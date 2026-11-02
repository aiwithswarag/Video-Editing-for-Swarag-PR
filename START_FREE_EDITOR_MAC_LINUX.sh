#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
echo "SWARAG VIDEO DIRECTOR - FREE LOCAL EDITOR"
if ! command -v docker >/dev/null 2>&1 || ! docker info >/dev/null 2>&1; then
 echo "Install and start Docker Desktop (or Docker Engine) before launching this editor."
 exit 1
fi
mkdir -p PRIVATE
echo "Preparing original 42-effect engine. First launch requires internet."
docker build -t swarag-free-editor:local .
echo "The editor runs only at http://127.0.0.1:8765/"
(sleep 5; if command -v open >/dev/null; then open http://127.0.0.1:8765/; elif command -v xdg-open >/dev/null; then xdg-open http://127.0.0.1:8765/; fi) >/dev/null 2>&1 &
docker run --rm --name swarag-local-editor --network bridge  -p 127.0.0.1:8765:8765  -e SWARAG_LOCAL_DOCKER=1 -e PORT=8765 -e SWARAG_JOB_DIR=/workspace/jobs  -v "$PWD/PRIVATE:/workspace"  --user "$(id -u):$(id -g)"  swarag-free-editor:local python tools/local_editor.py
