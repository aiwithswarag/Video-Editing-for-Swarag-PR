#!/usr/bin/env python3
"""Authenticated single-instance Render API for PRIVATE Swarag 42-effect renders.

This API is a transport/execution bridge, NOT a transcript aligner or creative
director. The caller must inspect the real speech and provide a validated plan.
The resulting MP4 is always REVIEW REQUIRED until actual full creative signoff.

Protected endpoints:
 POST   /v1/jobs                  JSON effects, script verification + clean-source flags
 PUT    /v1/jobs/<id>/video       application/octet-stream (original MP4 bytes)
 PUT    /v1/jobs/<id>/script      application/octet-stream (private script bytes)
 POST   /v1/jobs/<id>/start      starts rendering in a background thread
 GET    /v1/jobs/<id>            status
 GET    /v1/jobs/<id>/master     private MP4 retrieval
 GET    /v1/jobs/<id>/qa         technical QA report
 GET    /v1/jobs/<id>/release    release-gate JSON
 DELETE /v1/jobs/<id>            delete source + intermediates (not when running)
 GET    /health                  no personal data; unauthenticated
"""
from __future__ import annotations
import hashlib
import hmac
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from plan_validation import validate_plan
from rag_storyboard import (validate as validate_rag_beats, recognizable as recognizable_rag,
                            rag_intent, explain_unrecognized)
from local_director import document_text

JOB_DIR = Path(os.getenv("SWARAG_JOB_DIR", "/workspace/jobs")).resolve()
MAX_UPLOAD = int(os.getenv("SWARAG_MAX_UPLOAD_MB", "512")) * 1024 * 1024
MAX_JSON = 64 * 1024
TOKEN = os.getenv("SWARAG_API_TOKEN", "")
LIVE = threading.Lock()
ACTIVE = {"id": None}
ID_RE = re.compile(r"^[0-9a-f]{32}$")
PARTS_RE = re.compile(r"^/v1/jobs/([0-9a-f]{32})(?:/(video|script|start|master|qa|release))?$")
RENDER_TIMEOUT = 4 * 60 * 60


def jobdir(job_id):
    if not ID_RE.fullmatch(job_id):
        raise ValueError("Invalid job identifier")
    return JOB_DIR / job_id


def metadata(job_id):
    path = jobdir(job_id) / "state.json"
    if not path.is_file():
        raise FileNotFoundError("Unknown job")
    return json.loads(path.read_text(encoding="utf-8"))


def save(job_id, state):
    file = jobdir(job_id) / "state.json"
    temp = file.with_suffix(".tmp")
    temp.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, file)


def erase_old_jobs(now=None, max_age=24 * 3600):
    now = time.time() if now is None else now
    if not JOB_DIR.is_dir():
        return
    for folder in JOB_DIR.iterdir():
        if not folder.is_dir() or not ID_RE.fullmatch(folder.name):
            continue
        try:
            state = metadata(folder.name)
            if state.get("status") == "RUNNING":
                continue
            if now - float(state["created_at"]) > max_age:
                shutil.rmtree(folder)
        except (ValueError, KeyError, FileNotFoundError, OSError):
            continue


def run_production(job_id):
    folder = jobdir(job_id)
    try:
        state = metadata(job_id)
        source = folder / "source.mp4"
        plan = folder / "plan.json"
        out = folder / "output"
        out.mkdir(exist_ok=True)
        cmd = [
            sys.executable, str(ROOT / "scripts" / "produce_video.py"),
            "render", str(source), "--plan", str(plan),
            "--output-dir", str(out), "--look", "clean-studio",
            "--style", "premium", "--crf", "18",
        ]
        with (folder / "render.log").open("w", encoding="utf-8") as log:
            subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                           check=True, timeout=RENDER_TIMEOUT)
        qa_path = out / "production_qa.json"
        release_path = out / "release_gate.json"
        master = out / "final_master.mp4"
        qa = json.loads(qa_path.read_text(encoding="utf-8"))
        release = json.loads(release_path.read_text(encoding="utf-8"))
        if qa.get("technical_status") != "PASS" or not master.is_file() or not master.stat().st_size:
            raise RuntimeError("Final video technical checks did not pass")
        if release.get("release_status") != "CREATIVE_REVIEW_REQUIRED":
            raise RuntimeError("Unexpected release gate status; review the report")
        state = metadata(job_id)
        state["status"] = "REVIEW_REQUIRED"
        state["finished_at"] = time.time()
        state["master_sha256"] = release.get("master_sha256")
        save(job_id, state)
    except (OSError, ValueError, subprocess.SubprocessError, RuntimeError, KeyError) as exc:
        state = metadata(job_id)
        state["status"] = "FAILED"
        state["finished_at"] = time.time()
        state["error"] = type(exc).__name__ + ": " + str(exc)[:240]
        save(job_id, state)
    finally:
        with LIVE:
            ACTIVE["id"] = None


class Handler(BaseHTTPRequestHandler):
    server_version = "SwaragPrivateEditor/0.1"

    def log_message(self, pattern, *args):
        # No Authorization headers, script contents, video names or media
        # are logged through HTTP request diagnostics.
        sys.stderr.write("HTTP " + pattern % args + "\n")

    def answer(self, code, obj):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def authorized(self):
        incoming = self.headers.get("Authorization", "")
        expected = "Bearer " + TOKEN
        if not TOKEN or not hmac.compare_digest(incoming, expected):
            self.answer(401, {"error": "Unauthorized"})
            return False
        return True

    def parts(self):
        return PARTS_RE.fullmatch(urlsplit(self.path).path)

    def body(self, limit):
        try:
            value = int(self.headers.get("Content-Length", ""))
        except ValueError:
            raise ValueError("Explicit Content-Length required")
        if value < 1 or value > limit:
            raise ValueError("Request body exceeds permitted limit or is empty")
        return value

    def json_body(self):
        n = self.body(MAX_JSON)
        raw = self.rfile.read(n)
        if len(raw) != n:
            raise ValueError("Truncated request")
        return json.loads(raw)

    def do_GET(self):
        if urlsplit(self.path).path == "/health":
            ok = bool(TOKEN and shutil.which("ffmpeg") and
                      (ROOT / "models" / "selfie_segmenter.tflite").is_file())
            self.answer(200 if ok else 503, {"status": "ready" if ok else "unconfigured",
                                              "engine": "swarag-original-42-effects"})
            return
        if not self.authorized():
            return
        match = self.parts()
        if not match:
            self.answer(404, {"error": "Not found"})
            return
        job_id, action = match.groups()
        try:
            state = metadata(job_id)
        except FileNotFoundError:
            self.answer(404, {"error": "Unknown job"})
            return
        if action is None:
            # Do not leak source script content or private file system paths.
            self.answer(200, {key: state.get(key) for key in
                        ("id", "status", "created_at", "finished_at",
                         "error", "master_sha256", "effect_names")})
            return
        file = {"master": jobdir(job_id) / "output" / "final_master.mp4",
                "qa": jobdir(job_id) / "output" / "production_qa.json",
                "release": jobdir(job_id) / "output" / "release_gate.json"}.get(action)
        if file is None:
            self.answer(404, {"error": "Not found"})
            return
        if state["status"] != "REVIEW_REQUIRED" or not file.is_file():
            self.answer(409, {"error": "Output is not ready"})
            return
        self.send_response(200)
        self.send_header("Content-Type", "video/mp4" if action == "master" else "application/json")
        self.send_header("Cache-Control", "private, no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(file.stat().st_size))
        self.end_headers()
        with file.open("rb") as fp:
            shutil.copyfileobj(fp, self.wfile, length=1024 * 1024)

    def do_POST(self):
        if not self.authorized():
            return
        url = urlsplit(self.path).path
        if url == "/v1/jobs":
            try:
                data = self.json_body()
                if not isinstance(data, dict):
                    raise ValueError("JSON object expected")
                effects = data.get("effects", [])
                if not isinstance(effects, list) or not 1 <= len(effects) <= 42:
                    raise ValueError("Supply one or more validated effect cues")
                effects = validate_plan(effects)
                rag= data.get("rag_storyboard",[])
                mode=data.get("video_mode","general")
                if mode not in ("rag","general"):
                    raise ValueError("Select RAG explainer or general video mode")
                requires= data.get("requires_six_section_explainer") is True or mode=="rag"
                if requires and not rag:
                    raise ValueError("Six-section explainer required but no visual storyboard supplied")
                if rag:
                    # Duration verified again by producer against actual MP4.
                    validate_rag_beats(rag,float(data.get("source_duration",0)))
                    requires=True
                script_filename=data.get("script_filename","script.txt")
                if not isinstance(script_filename,str) or not script_filename.casefold().endswith((".txt",".md",".docx")) or len(script_filename)>150:
                    raise ValueError("Script filename must be TXT, MD or DOCX")
                # Explicitly disable user-submitted local file paths; optional
                # image/B-roll uploads need a separate approved asset interface.
                if any("images" in e or "video" in e or "asset" in e for e in effects):
                    raise ValueError("External effect media requires a separately authorized asset upload")
                job_id = uuid.uuid4().hex
                folder = jobdir(job_id)
                folder.mkdir(parents=True)
                plan = {
                    "requires_transcript": bool(data.get("requires_transcript", True)),
                    "transcript_verified": data.get("transcript_verified") is True,
                    "requires_six_section_explainer":requires,
                    "rag_storyboard":rag,
                    "video_mode":mode,
                    "script_filename":script_filename,
                    "effects": effects,
                }
                (folder / "plan.json").write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
                save(job_id, {
                    "id": job_id, "created_at": time.time(), "status": "AWAITING_INPUT",
                    "source_clean_confirmed": data.get("source_clean_confirmed") is True,
                    "effect_names": [e["fx"] for e in effects]
                })
                erase_old_jobs()
                self.answer(201, {"id": job_id, "status": "AWAITING_INPUT"})
            except (ValueError, TypeError, json.JSONDecodeError) as exc:
                self.answer(422, {"error": str(exc)[:300]})
            return
        match = self.parts()
        if not match or match.group(2) != "start":
            self.answer(404, {"error": "Not found"})
            return
        job_id = match.group(1)
        try:
            state = metadata(job_id)
            folder = jobdir(job_id)
            plan = json.loads((folder / "plan.json").read_text(encoding="utf-8"))
        except (FileNotFoundError, ValueError):
            self.answer(404, {"error": "Unknown job"})
            return
        if not (folder / "source.mp4").is_file():
            self.answer(409, {"error": "Original video not uploaded"})
            return
        if plan.get("requires_transcript"):
            if not (folder / "script.bin").is_file() or not plan.get("transcript_verified"):
                self.answer(409, {"error": "Verified script and actual speech alignment required"})
                return
        if not state.get("source_clean_confirmed"):
            self.answer(409, {"error": "Clean original camera footage must be confirmed"})
            return
        # Read the actual private uploaded script (never copied to GitHub or
        # HTTP status) and detect RAG-explainer intent independently of UI flags.
        # A stale local browser may submit an effect-only plan with "requires"
        # false; it must never turn that into an accepted final MP4.
        try:
            script_path=folder/"script.bin"
            transcript=(document_text(plan.get("script_filename","script.txt"),
                                       script_path.read_bytes()) if script_path.is_file() else "")
            is_rag=rag_intent(transcript)
            if is_rag and not plan.get("requires_six_section_explainer"):
                self.answer(409,{"error":"Incomplete RAG explainer: server detected citation/policy/RAG script but no six-section graphics plan. Restart the UPDATED editor, upload the COMPLETE six-section script, and verify eight stages before rendering."})
                return
            if plan.get("requires_six_section_explainer"):
                if not recognizable_rag(transcript):
                    raise ValueError(explain_unrecognized(transcript) or
                                     "Script does not support required fictional policy figures")
                from rag_storyboard import coverage
                from cinematic_finish import probe
                duration=probe(folder/"source.mp4")["duration"]
                coverage(plan.get("rag_storyboard",[]),duration,transcript)
        except (ValueError,KeyError,OSError,FileNotFoundError) as exc:
            self.answer(409,{"error":"Complete script-verified explainer required: "+str(exc)[:200]})
            return
        with LIVE:
            if ACTIVE["id"] is not None or state["status"] not in ("AWAITING_INPUT", "FAILED", "INTERRUPTED"):
                self.answer(409, {"error": "Busy or already started"})
                return
            ACTIVE["id"] = job_id
            state["status"] = "RUNNING"
            state.pop("error", None)
            save(job_id, state)
            threading.Thread(target=run_production, args=(job_id,), daemon=True).start()
        self.answer(202, {"id": job_id, "status": "RUNNING"})

    def do_PUT(self):
        if not self.authorized():
            return
        match = self.parts()
        if not match or match.group(2) not in ("video", "script"):
            self.answer(404, {"error": "Not found"})
            return
        job_id, kind = match.groups()
        try:
            state = metadata(job_id)
            if state["status"] != "AWAITING_INPUT":
                self.answer(409, {"error": "Cannot replace job inputs after starting"})
                return
            count = self.body(MAX_UPLOAD if kind == "video" else 2 * 1024 * 1024)
            folder = jobdir(job_id)
            target = folder / ("source.mp4" if kind == "video" else "script.bin")
            incoming = target.with_suffix(".incoming")
            with incoming.open("wb") as handle:
                left = count
                while left:
                    data = self.rfile.read(min(1024 * 1024, left))
                    if not data:
                        raise ValueError("Incomplete upload")
                    handle.write(data)
                    left -= len(data)
            if kind == "video":
                with incoming.open("rb") as handle:
                    header = handle.read(12)
                if len(header) < 12 or header[4:8] != b"ftyp":
                    incoming.unlink(missing_ok=True)
                    raise ValueError("Upload must contain actual MP4 bytes")
            os.replace(incoming, target)
            self.answer(201, {"uploaded": kind, "bytes": count})
        except FileNotFoundError:
            self.answer(404, {"error": "Unknown job"})
        except (ValueError, OSError) as exc:
            self.answer(422, {"error": str(exc)[:220]})

    def do_DELETE(self):
        if not self.authorized():
            return
        match = self.parts()
        if not match or match.group(2) is not None:
            self.answer(404, {"error": "Not found"})
            return
        job_id = match.group(1)
        try:
            state = metadata(job_id)
            with LIVE:
                if state["status"] == "RUNNING" or ACTIVE["id"] == job_id:
                    self.answer(409, {"error": "Cannot delete active render"})
                    return
                shutil.rmtree(jobdir(job_id))
            self.answer(200, {"deleted": True})
        except FileNotFoundError:
            self.answer(404, {"error": "Unknown job"})

def main():
    if len(TOKEN) < 32:
        raise SystemExit("SWARAG_API_TOKEN must be a private random secret >=32 characters")
    JOB_DIR.mkdir(parents=True, exist_ok=True)
    for folder in JOB_DIR.iterdir():
        if folder.is_dir() and ID_RE.fullmatch(folder.name):
            try:
                state = metadata(folder.name)
                if state["status"] == "RUNNING":
                    state["status"] = "INTERRUPTED"
                    save(folder.name, state)
            except (ValueError, OSError, KeyError):
                continue
    erase_old_jobs()
    def janitor():
        while True:
            time.sleep(3600)
            with LIVE:
                erase_old_jobs()
    threading.Thread(target=janitor,daemon=True).start()
    port = int(os.getenv("PORT", "10000"))
    with ThreadingHTTPServer(("0.0.0.0", port), Handler) as app:
        print(f"Swarag Render API listening on port {port}", flush=True)
        app.serve_forever()

if __name__ == "__main__":
    main()
