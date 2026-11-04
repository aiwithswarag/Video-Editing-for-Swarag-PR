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
rem FAIL CLOSED: Never open the old 8765 server when the user thinks they launched
rem an updated editor. Do not interrupt any active/private render automatically.
docker ps --format "{{.Names}}" | findstr /i /x /c:"swarag-local-editor" >nul
if not errorlevel 1 (
  echo.
  echo ERROR: The OLD Swarag editor is still running.
  echo Open Docker Desktop, go to Containers, STOP swarag-local-editor,
  echo then double-click this NEW launcher again.
  echo No new browser window was opened and no paid resource was used.
  pause
  exit /b 1
)
netstat -ano | findstr /i /c:":8765 " | findstr /i /c:"LISTENING" >nul
if not errorlevel 1 (
  echo.
  echo ERROR: Port 8765 is already occupied by a running application.
  echo Stop the previous editor/container before launching this version.
  echo No new browser window will open until port 8765 is free.
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
echo Required build marker: 47-CAMERA-RENDER-FAIL-CLOSED-2026-11-04-R2
echo Check the installed renderer fingerprint at http://127.0.0.1:8765/local/version
echo All 47 short camera samples must pass before rendering a final master.
echo Your media stays in the PRIVATE folder on this computer.
echo Close this command window or press Ctrl+C when finished.
start "" /min powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 6; Start-Process 'http://127.0.0.1:8765/'"
docker run --rm --name swarag-local-editor --network bridge -p 127.0.0.1:8765:8765 -e SWARAG_LOCAL_DOCKER=1 -e PORT=8765 -e SWARAG_JOB_DIR=/workspace/jobs -v "%CD%\PRIVATE:/workspace" swarag-free-editor:local python tools/local_editor.py
if errorlevel 1 (
  echo The local editor stopped unexpectedly. Check the message above.
  pause
)
endlocal
