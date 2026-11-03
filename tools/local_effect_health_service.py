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
from render_effect_gallery import NAMED_VARIANTS

ROOT=Path(__file__).resolve().parents[1]
ROUTE=re.compile(r"^/local/effect-diagnostic/([0-9a-f]{32})(?:/(report|contact-sheet|motion-sheet|motion-clips))?$")
CLIP_ROUTE=re.compile(r"^/local/effect-diagnostic/([0-9a-f]{32})/clip/([a-z0-9-]{1,60})$")
# A clip is selectable only if the exact label is in the original registry.
# Never turn user input into an arbitrary file path.
def safe_clip_labels():
    names,_,_=read_registry()
    return [*names,*[label for label,_,_ in NAMED_VARIANTS]]


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
    returned["effect_labels"]=safe_clip_labels()
    report=folder/"diagnostic"/"effect-health-report.json"
    if report.is_file():
        r=json.loads(report.read_text(encoding="utf8"))
        returned["technical_status"]=r.get("technical_status")
        returned["technically_passed_effects"]=r.get("technically_passed_effects")
        returned["technically_failed_or_unverified_effects"]=r.get(
            "technically_failed_or_unverified_effects",[])
        returned["creative_status"]=r.get("creative_status")
        returned["review_artifact_status"]=r.get("review_artifact_status")
        returned["review_artifact_error_type"]=r.get("review_artifact_error_type")
        returned["recovered_without_rerender"]=bool(r.get("recovered_without_rerender"))
        returned["motion_review_status"]=(r.get("motion_review") or {}).get("status")
        returned["motion_clips_packaged"]=(r.get("motion_review") or {}).get("clips_packaged",0)
    return returned


def process_diagnostic(job_id, *, recover=False):
    folder=api.jobdir(job_id)
    try:
        dest=folder/"diagnostic"
        dest.mkdir(exist_ok=True)
        command=[
            sys.executable,str(ROOT/"tools"/"local_effect_diagnostic.py"),
            "--video",str(folder/"source.mp4"),
            "--output-dir",str(dest)]
        if recover:
            command.append("--recover-existing")
        with (folder/"effect-health.log").open("a" if recover else "w",encoding="utf8") as log:
            # Each clip is strictly short; full suite still requires real CPU.
            # The user can close the browser and later poll this private job.
            proc=subprocess.run(command,cwd=ROOT,stdout=log,
                                stderr=subprocess.STDOUT,timeout=2*60*60)
        state=api.metadata(job_id)
        report=dest/"effect-health-report.json"
        if not report.is_file():
            raise RuntimeError("No health report exists. The individual render step may have succeeded; use local recovery if retained results.json exists.")
        data=json.loads(report.read_text(encoding="utf8"))
        state["status"]=(
            "REVIEW_REQUIRED" if proc.returncode==0 and
            data.get("technical_status")=="ALL_42_SHORT_SAMPLE_DECODE_PASS" and
            (data.get("motion_review") or {}).get("status")=="MOTION_SAMPLES_AVAILABLE"
            else "FAILED"
        )
        if state["status"]=="FAILED":
            stage=data.get("review_artifact_status","UNVERIFIED")
            state["error"]=("Diagnostic finished with incomplete evidence. Technical report is available. "
                "Review artifact state: "+str(stage)+". "
                "Failure class: "+str(data.get("review_artifact_error_type","none"))+".")
        else:
            state["error"]=None
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



def recover_latest(handler):
    """Rebuild latest FAILED diagnostic from retained local clips only.

    User-initiated, authenticated, localhost-only. No upload, no FX rerender
    and no remote data transfer. The original 47-entry manifest is mandatory.
    """
    if not handler.authorized():
        return
    with api.LIVE:
        if api.ACTIVE.get("id") is not None:
            handler.answer(409,{"error":"A diagnostic or render is already active"})
            return
        candidates=[]
        for folder in api.JOB_DIR.iterdir():
            if not folder.is_dir() or not api.ID_RE.fullmatch(folder.name):
                continue
            try:
                state=api.metadata(folder.name)
            except (ValueError,OSError,KeyError,json.JSONDecodeError):
                continue
            if (state.get("type")=="effect_diagnostic" and
                state.get("status")=="FAILED" and
                (folder/"source.mp4").is_file() and
                (folder/"diagnostic"/"effect-gallery"/"results.json").is_file()):
                candidates.append((float(state.get("created_at",0)),folder.name,state))
        if not candidates:
            handler.answer(409,{"error":"No retained completed effect gallery was found. Your previous local job may have been cleaned up; no rerender was started."})
            return
        _,job_id,state=max(candidates,key=lambda item:(item[0],item[1]))
        api.ACTIVE["id"]=job_id
        try:
            state["status"]="RUNNING"
            state["error"]=None
            state["recovery_requested"]=True
            api.save(job_id,state)
        except (ValueError,OSError) as exc:
            api.ACTIVE["id"]=None
            handler.answer(422,{"error":"Could not start local recovery: "+type(exc).__name__})
            return
    threading.Thread(target=process_diagnostic,kwargs={"job_id":job_id,"recover":True},daemon=True).start()
    handler.answer(202,{"id":job_id,"status":"RUNNING",
                   "message":"Recovering private 47-effect report and motion review from stored clips; no effect rerender or upload"})


def get(handler,path):
    if not handler.authorized():return
    selected=CLIP_ROUTE.fullmatch(path)
    if selected:
        job_id,label=selected.groups()
        if label not in safe_clip_labels():
            handler.answer(404,{"error":"Unknown original effect label"})
            return
        try:
            safe_health_state(job_id)
        except (FileNotFoundError,ValueError,KeyError,OSError):
            handler.answer(404,{"error":"Unknown local diagnostic"})
            return
        clip=api.jobdir(job_id)/"diagnostic"/"effect-gallery"/(label+".mp4")
        if not clip.is_file() or clip.stat().st_size<2000:
            handler.answer(409,{"error":"This effect's motion clip is unavailable; inspect the diagnostic report"})
            return
        # Downloading one short PRIVATE MP4 on demand is less cumbersome than
        # transferring the full 47-clip ZIP for every individual playback.
        blob=clip.read_bytes()
        handler.send_response(200)
        handler.send_header("Content-Type","video/mp4")
        handler.send_header("Cache-Control","private, no-store")
        handler.send_header("X-Content-Type-Options","nosniff")
        handler.send_header("Content-Length",str(len(blob)))
        handler.end_headers()
        handler.wfile.write(blob)
        return
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
    targets={
        "report":folder/"effect-health-report.json",
        "contact-sheet":folder/"review"/"all-47-effects.jpg",
        "motion-sheet":folder/"review"/"all-47-motion-review.jpg",
        "motion-clips":folder/"review"/"all-47-motion-clips.zip",
    }
    target=targets[kind]
    if not target.is_file():
        handler.answer(409,{"error":"Diagnostic artifact not ready; see status and effect-health.log"})
        return
    blob=target.read_bytes()
    handler.send_response(200)
    handler.send_header("Content-Type",
        "application/json" if kind=="report" else
        "application/zip" if kind=="motion-clips" else "image/jpeg")
    if kind=="motion-clips":
        handler.send_header("Content-Disposition",'attachment; filename="Swarag_47_Motion_Clips.zip"')
    handler.send_header("Cache-Control","private, no-store")
    handler.send_header("X-Content-Type-Options","nosniff")
    handler.send_header("Content-Length",str(len(blob)))
    handler.end_headers()
    handler.wfile.write(blob)
