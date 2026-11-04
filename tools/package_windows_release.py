#!/usr/bin/env python3
"""Package the tracked Swarag Windows/Docker editor without any private media.

This builds a source-based, one-click Windows bootstrap ZIP, not an .exe.
Docker Desktop builds the executable rendering environment on the user's PC.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = {
    "START_FREE_EDITOR_WINDOWS.bat", "START_FREE_EDITOR_MAC_LINUX.sh",
    "Dockerfile", ".dockerignore", "requirements.txt", "README.md",
    "LICENSE", "LICENSE.md", "LICENSE.txt", "NOTICE", "NOTICE.md",
}
ROOT_DIRS = {"tools", "scripts", "branding", "docs", "fonts", "models", "examples"}
PRIVATE_NAMES = {
    "private", "private_media", "outputs", "renders", "final_release",
    "sessions", "uploads", "jobs", ".env", ".venv", "__pycache__",
}
PRIVATE_EXTENSIONS = {
    ".mp4", ".mov", ".m4v", ".webm", ".mp3", ".m4a", ".wav",
    ".aac", ".zip", ".7z", ".tar", ".gz", ".key", ".pem", ".p12",
}
REQUIRED = {
    "START_FREE_EDITOR_WINDOWS.bat", "Dockerfile", "requirements.txt",
    "tools/local_editor.py", "tools/download_assets.py",
    "scripts/fx.py", "scripts/produce_video.py",
}


def git(*parts):
    return subprocess.check_output(["git", *parts], cwd=ROOT)


def build(out_dir):
    included = []
    for token in git("ls-files", "-z").split(b"\0"):
        if not token:
            continue
        name = token.decode("utf-8")
        path = Path(name)
        parts = [part.lower() for part in path.parts]
        if any(part in PRIVATE_NAMES for part in parts):
            continue
        if path.suffix.lower() in PRIVATE_EXTENSIONS:
            continue
        if name not in ROOT_FILES and parts[0] not in ROOT_DIRS:
            continue
        source = ROOT / path
        if source.is_file() and not source.is_symlink():
            included.append((name, source))
    missing = REQUIRED - {name for name, _ in included}
    if missing:
        raise RuntimeError("Editor package lacks: " + ", ".join(sorted(missing)))

    renderer_bytes = (ROOT / "scripts/fx.py").read_bytes()
    effects = len(re.findall(rb"@effect\(\s*['\"][^'\"]+['\"]", renderer_bytes))
    if effects != 42:
        raise RuntimeError(f"Expected 42 original effects, found {effects}")

    revision = git("rev-parse", "HEAD").decode().strip()
    short = revision[:12]
    fingerprint = hashlib.sha256(renderer_bytes).hexdigest()
    manifest = {
        "product": "Swarag Video Director — Windows local Docker editor",
        "revision": revision,
        "renderer_sha256": fingerprint,
        "renderer_fingerprint_sha256_16": fingerprint[:16],
        "registered_original_effects": effects,
        "named_looks": 5,
        "artifact_kind": "Complete tracked application source; Docker build required",
        "private_media_included": False,
        "certification_limit": "Short effect clips are not full-video creative approval",
    }
    quickstart = f"""SWARAG VIDEO DIRECTOR — WINDOWS EDITOR ({short})

1. Install and start Docker Desktop (subject to its applicable license).
2. Extract this ZIP to a NEW local folder, separate from private media.
3. Double-click START_FREE_EDITOR_WINDOWS.bat and allow Docker to build.
4. Open http://127.0.0.1:8765/ (only on your own computer).
5. At http://127.0.0.1:8765/local/version compare the renderer
   fingerprint_sha256_16 with: {fingerprint[:16]}
6. Select clean original MP4 and matching script.
   For ordinary videos select 'Other video — original Swarag effect catalog'.
   RAG mode requires its specific six-section fictional policy script.
7. Review timestamps/text against actual speech. Confirm only after checking.
8. Render the complete MP4; download technical QA; watch and listen to the
   ENTIRE exported video and approve creative quality before publication.

The first Docker image build needs internet and substantial free disk/RAM.
All source footage, scripts and output stay in the local PRIVATE workspace.
The 42+5 diagnostics do not certify any full-res master or its captions.
"""
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    archive = dest / f"Swarag_Video_Editor_Windows_{short}.zip"
    prefix = "Swarag-Video-Editor/"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=8) as z:
        for name, path in sorted(included):
            z.write(path, prefix + name)
        z.writestr(prefix + "RELEASE_BUILD_INFO.json",
                   json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        z.writestr(prefix + "START_HERE_WINDOWS.txt", quickstart)
    with zipfile.ZipFile(archive) as z:
        corrupted = z.testzip()
        if corrupted:
            raise RuntimeError("Corrupt ZIP entry: " + corrupted)

    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    (dest / (archive.name + ".sha256")).write_text(
        checksum + "  " + archive.name + "\n", encoding="utf-8")
    (dest / "RELEASE_BUILD_INFO.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"archive": str(archive), "file_count": len(included),
                      "sha256": checksum, "manifest": manifest}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="dist")
    build(parser.parse_args().out_dir)
