@echo off
setlocal
cd /d "%~dp0"
echo SWARAG VIDEO DIRECTOR - FREE LOCAL EDITOR
echo.
where docker >nul 2>&1
if errorlevel 1 (
  echo Docker Desktop is required for the free local renderer.
  echo Install Docker Desktop for personal use, start it, then double-click this file again.
  pause
  exit /b 1
)
docker info >nul 2>&1
if errorlevel 1 (
  echo Docker Desktop is not running. Please start Docker Desktop.
  pause
  exit /b 1
)
if not exist PRIVATE mkdir PRIVATE
echo Preparing the original 42-effect engine. First setup requires internet.
docker build -t swarag-free-editor:local .
if errorlevel 1 (
  echo Docker engine build failed. No fallback editor will be used.
  pause
  exit /b 1
)
echo.
echo This is your local-only editor: http://127.0.0.1:8765/
echo Your media stays in the PRIVATE folder on this computer.
echo Close this command window or press Ctrl+C when finished.
start "" /min powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 6; Start-Process 'http://127.0.0.1:8765/'"
docker run --rm --name swarag-local-editor --network bridge -p 127.0.0.1:8765:8765 -e SWARAG_LOCAL_DOCKER=1 -e PORT=8765 -e SWARAG_JOB_DIR=/workspace/jobs -v "%CD%\PRIVATE:/workspace" swarag-free-editor:local python tools/local_editor.py
if errorlevel 1 (
  echo The local editor stopped unexpectedly. Check the message above.
  pause
)
endlocal
