"""Localhost-only private real-footage 42-effect diagnostic background worker.

Uses the SAME original repository renderer, independently testing all 42
effects + five catalogue looks. The user's media stays under PRIVATE/jobs.
No request to a remote service and no effect substitutions.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

import render_job_api as api
from effect_catalog import read_registry

ROOT=Path(__file__).resolve().parents[1]
ROUTE=re.compile(r"^/local/effect-diagnostic/([0-9a-f]{32})(?:/(report|contact-sheet))?$")


def safe_health_state(job_id):
    state=api.metadata(job_id)
    if state.get("type")!="effect_diagnostic":
        raise FileNotFoundError("Unknown diagnostic")
    folder=api.jobdir(job_id)
    completed=0
    log=folder/"effect-health.log"
    if log.is_file():
        try:
            tail=log.read_text(encoding="utf8",errors="replace")
            completed=sum(1 for line in tail.splitlines()
                          if line.startswith(("PASS ","FAIL ")))
        except (OSError,UnicodeError):
            completed=0
    returned={key:state.get(key) for key in
              ("id","status","error","finished_at","created_at")}
    returned["effect_checks_completed"]=min(47,completed)
    returned["expected_effect_checks"]=47
    report=folder/"diagnostic"/"effect-health-report.json"
    if report.is_file():
        r=json.loads(report.read_text(encoding="utf8"))
        returned["technical_status"]=r.get("technical_status")
        returned["technically_passed_effects"]=r.get("technically_passed_effects")
        returned["technically_failed_or_unverified_effects"]=r.get(
            "technically_failed_or_unverified_effects",[])
        returned["creative_status"]=r.get("creative_status")
    return returned


def process_diagnostic(job_id):
    folder=api.jobdir(job_id)
    try:
        dest=folder/"diagnostic"
        dest.mkdir(exist_ok=True)
        command=[
            sys.executable,str(ROOT/"tools"/"local_effect_diagnostic.py"),
            "--video",str(folder/"source.mp4"),
            "--output-dir",str(dest)]
        with (folder/"effect-health.log").open("w",encoding="utf8") as log:
            # Each clip is strictly short; full suite still requires real CPU.
            # The user can close the browser and later poll this private job.
            proc=subprocess.run(command,cwd=ROOT,stdout=log,
                                stderr=subprocess.STDOUT,timeout=2*60*60)
        state=api.metadata(job_id)
        report=dest/"effect-health-report.json"
        if not report.is_file():
            raise RuntimeError("No effect-by-effect health report was produced; check private diagnostic log")
        data=json.loads(report.read_text(encoding="utf8"))
        state["status"]=(
            "REVIEW_REQUIRED" if proc.returncode==0 and
            data.get("technical_status")=="ALL_42_SHORT_SAMPLE_DECODE_PASS"
            else "FAILED"
        )
        if state["status"]=="FAILED":
            state["error"]="At least one effect or named variant failed short real-camera testing. Review the per-effect report."
        state["finished_at"]=time.time()
        api.save(job_id,state)
    except (subprocess.TimeoutExpired,ValueError,KeyError,OSError,RuntimeError,
            json.JSONDecodeError) as exc:
        try:
            state=api.metadata(job_id)
            state["status"]="FAILED"
            state["finished_at"]=time.time()
            # Avoid external leaks: only show bounded local exception string.
            state["error"]=type(exc).__name__+": "+str(exc)[-200:]
            api.save(job_id,state)
        except (OSError,FileNotFoundError):pass
    finally:
        with api.LIVE:
            if api.ACTIVE.get("id")==job_id:
                api.ACTIVE["id"]=None


def begin(handler):
    if not handler.authorized():return
    with api.LIVE:
        if api.ACTIVE.get("id") is not None:
            handler.answer(409,{"error":"Another render or 42-effect diagnostic is active on this computer"})
            return
        job_id=uuid.uuid4().hex
        api.ACTIVE["id"]=job_id
    folder=api.jobdir(job_id)
    try:
        n=handler.body(api.MAX_UPLOAD)
        folder.mkdir(parents=True,exist_ok=False)
        original=folder/"source.mp4"
        incoming=folder/"source.incoming"
        with incoming.open("wb") as file:
            left=n
            while left:
                chunk=handler.rfile.read(min(1024*1024,left))
                if not chunk:
                    raise ValueError("Incomplete private video upload")
                file.write(chunk)
                left-=len(chunk)
        with incoming.open("rb") as file:
            head=file.read(12)
        if len(head)<12 or head[4:8]!=b"ftyp":
            raise ValueError("Diagnostic requires actual MP4 bytes, not a script or renamed file")
        incoming.replace(original)
        api.save(job_id,{"id":job_id,"type":"effect_diagnostic",
                 "created_at":time.time(),"status":"RUNNING"})
        threading.Thread(target=process_diagnostic,args=(job_id,),daemon=True).start()
        handler.answer(202,{"id":job_id,"status":"RUNNING",
                       "message":"Testing 42 original effects + five catalogue looks privately on a short excerpt; creative approval still required"})
    except (ValueError,OSError) as exc:
        if folder.exists():
            import shutil
            shutil.rmtree(folder,ignore_errors=True)
        with api.LIVE:
            if api.ACTIVE.get("id")==job_id:
                api.ACTIVE["id"]=None
        handler.answer(422,{"error":"Diagnostic could not start: "+str(exc)[-190:]})


def get(handler,path):
    if not handler.authorized():return
    match=ROUTE.fullmatch(path)
    if not match:
        handler.answer(404,{"error":"Unknown local diagnostic"})
        return
    job_id,kind=match.groups()
    try:
        info=safe_health_state(job_id)
    except (FileNotFoundError,ValueError,KeyError,OSError):
        handler.answer(404,{"error":"Unknown local diagnostic"})
        return
    if kind is None:
        handler.answer(200,info)
        return
    folder=api.jobdir(job_id)/"diagnostic"
    target=(folder/"effect-health-report.json" if kind=="report" else
            folder/"review"/"all-47-effects.jpg")
    if not target.is_file():
        handler.answer(409,{"error":"Diagnostic artifact not ready; see status and effect-health.log"})
        return
    blob=target.read_bytes()
    handler.send_response(200)
    handler.send_header("Content-Type",("application/json" if kind=="report" else "image/jpeg"))
    handler.send_header("Cache-Control","private, no-store")
    handler.send_header("X-Content-Type-Options","nosniff")
    handler.send_header("Content-Length",str(len(blob)))
    handler.end_headers()
    handler.wfile.write(blob)
