"""Redacted localhost runtime diagnostics for the free Swarag Windows editor.

No media filenames, script text, tokens, private paths or personal metadata
are returned. Runtime readiness is NOT a promise of creative quality.
"""
from __future__ import annotations
import importlib.util
import shutil
import subprocess
from pathlib import Path

from effect_catalog import read_registry
import render_job_api as api

ROOT=Path(__file__).resolve().parents[1]


def _memory_limit_mb():
    file=Path("/sys/fs/cgroup/memory.max")
    try:
        v=file.read_text(encoding="ascii").strip()
        if v=="max":return None
        size=int(v)
        if size<=0 or size>1<<54:return None
        return round(size/1048576)
    except (OSError,ValueError):
        return None


def runtime_diagnostics():
    names,aliases,looks=read_registry()
    required=[
        "models/yunet.onnx","models/selfie_segmenter.tflite",
        "fonts/Inter.ttf","fonts/InstrumentSerif-Italic.ttf"]
    assets={name:((ROOT/name).is_file() and
                  (ROOT/name).stat().st_size>0) for name in required}
    binaries={name:bool(shutil.which(name)) for name in ("ffmpeg","ffprobe")}
    imports={name:importlib.util.find_spec(name) is not None
             for name in ("cv2","mediapipe","PIL","numpy")}
    try:
        disk=shutil.disk_usage(api.JOB_DIR if api.JOB_DIR.is_dir() else ROOT)
        free_mb=round(disk.free/1048576)
    except OSError:
        free_mb=None
    failures=[]
    if len(names)!=42:failures.append("Original effect registry is not 42")
    failures.extend("Missing asset: "+x for x,available in assets.items() if not available)
    failures.extend("Missing binary: "+x for x,available in binaries.items() if not available)
    failures.extend("Missing Python package: "+x for x,available in imports.items() if not available)
    if free_mb is not None and free_mb<2048:
        failures.append("Less than 2 GB free private workspace; video render may fail")
    return {
        "status":"READY_FOR_PRIVATE_TEST" if not failures else "NEEDS_ATTENTION",
        "effect_registry_count":len(names),
        "effect_names":names,
        "registered_alias_count":len(aliases),
        "registered_look_count":len(looks),
        "required_assets_present":assets,
        "runtime_executables":binaries,
        "python_dependencies_installed":imports,
        "private_workspace_free_mb":free_mb,
        "docker_container_memory_limit_mb":_memory_limit_mb(),
        "render_or_diagnostic_active":api.ACTIVE.get("id") is not None,
        "issues":failures,
        "creative_certification":"NOT APPROVED — 42 effects still need real footage visual QA",
        "privacy":"No source video, script content, tokens, file names, paths or logs included"
    }
