# Swarag Video Director: FREE local edition (no cloud rendering bill)

**This replaces a paid Render service with your own computer.** It runs the
exact same `scripts/fx.py` 42-effect Python/MediaPipe/FFmpeg engine through
`scripts/produce_video.py` with the same natural grade and technical QA.

**NOT the same user interface as uploading only to a ChatGPT Project.** A
regular ChatGPT Project cannot automatically push uploaded media into the
web browser running on your local computer. This local edition uses a
one-click launcher and a local web page instead. There is no recurring
hosting fee, no public network endpoint, and no automatic external upload.
Free compute is supplied by your own computer. Electricity and any hardware
costs remain yours. You still need technical/creative review of the output.

## One-time setup (no terminal commands per video)

1. Install Docker Desktop once (or Docker Engine on Linux).
   Docker Desktop is free only under its applicable license terms; see
   https://www.docker.com/pricing/ for personal/small-business eligibility.
   Use an adequate computer and enough free disk space; long 1080p effects
   can require substantial CPU/RAM and storage.
2. Download your Swarag repository branch as a ZIP from GitHub and extract
   it to a private folder. Or use your existing checkout.
   Repo: https://github.com/aiwithswarag/Video-Editing-for-Swarag-PR
   Branch: `feat/executive-editorial-v2` (draft PR #5; update the branch
   only after reviewing repository changes).
3. Start Docker Desktop and open the extracted folder.
4. **Windows:** double-click `START_FREE_EDITOR_WINDOWS.bat`.
   **Mac/Linux:** open `START_FREE_EDITOR_MAC_LINUX.sh` with your shell
   (on Mac, the first run may require opening it via Terminal; afterwards
   you can add a shortcut). These launchers build the Docker image before
   starting the app. The first build downloads *licensed public dependencies*
   and fonts/models once; subsequent builds use Docker layer caching.
5. Open http://127.0.0.1:8765/ on **the same computer**.
   This is a local/private browser interface, not a public Render URL.

## Update an existing Windows installation after the RAG Reel fix

If you already rendered your 50.4-second AI-citation Reel and saw only
`"selected_effects": ["slow-push"]`, that MP4 is technically valid but
editorially incomplete. **Do not simply re-render using the old ZIP**.

1. Keep a safe local copy of the original camera video, script and first render.
2. Close the old local-editor command window and stop the `swarag-local-editor`
   container in Docker Desktop. The old port `8765` must be free.
3. Download the **latest ZIP of branch `feat/executive-editorial-v2`** from
   GitHub, extract it into a NEW private folder, and ensure Docker Desktop is
   running. Do not overwrite the old `PRIVATE` media files.
4. Double-click `START_FREE_EDITOR_WINDOWS.bat`. Docker rebuilds the
   changed code, reusing downloaded dependency layers where possible.
5. At http://127.0.0.1:8765/ choose your original clean recording and the
   matching script with all six time-labelled sections (0–3, 3–12, 12–20,
   20–33, 33–49, 49–55). Describe the intended premium RAG explainer.
6. **Create edit draft** now recognizes the supported fictional policy
   script and displays a separate **six-section explainer** with eight stages:
   hook, fictional comparison, outdated citation, document-to-answer RAG
   explanation, three progressively appearing verification checks, and
   closing. The script's 55-second headings are scaled to the 50.4-second
   source *only as a draft*; manually review/adjust actual speech timing.
7. Confirm clean original footage and verified audio/timing. Then render.
   The canonical 42-effect engine runs first; an additional original
   source-grounded graphic overlay renders second. The final QA must report
   `requires_six_section_explainer: true`,
   `rag_graphics_pass.graphic_stages: 8`, and six
   `editorial_sections_covered`. A lone slow-push without those graphics
   is now blocked as incomplete for this recognized script.

**Boundary:** This template is specific to the six-section citation/RAG script.
For unrelated scripts, effects still require actual speech timing verification
and may not have a six-beat automated explainer. “DRAFT” never means
full transcription, frame-aware art-direction approval or final publishing
permission.

## For every video (simple browser workflow)

1. Upload the **clean original MP4** and the matching **TXT, MD or DOCX**
   script (PDF scripts must first be saved as text or DOCX).
2. Describe effects in plain language, e.g.:
   `Subtle slow-push at opening; backdrop-word, text="RAG"; natural skin and executive style`.
   All 42 registered effect names are available in the dropdown.
3. Click **Create edit draft**. The app reads **time headings inside the
   script** if present (e.g. `0–3 sec | Hook`). It scales those approximate
   windows when script and recording durations differ and warns you.
   It does **not** transcribe audio or pretend that script time headings are
   confirmed word-level timings.
4. Inspect the actual video and adjust effect start/end and on-screen copy.
   Explicitly confirm that the uploaded source is clean and script/edit
   timing matches what is actually spoken.
5. Click **Render full MP4**. The application runs the original 42-effect
   engine with the current full source-rate `clean-studio` finish, grade-
   before-effects production and technical release gates. No substitute
   renderer is allowed; missing dependencies result in a real error.
6. Download the actual `swarag_master.mp4` and `swarag_qa.json`.
   Watch the *entire* MP4 with sound before publishing. A technical PASS
   does not mean visual art direction or research facts were approved.

The private source and outputs are also saved under `PRIVATE/local-jobs`
in the extracted folder, with job-specific directories. Local file cleanup
runs every hour for jobs older than 24 hours and on next launch; make a copy
of any master you intend to keep. Stopping the container does not send
media anywhere. Do not commit `PRIVATE` to a public Git repository.

## What the free edition genuinely provides

- No Render subscription, storage bill or dedicated hosted service.
- Source-unchanged 42 effect definitions and the existing cinematic finish.
- 9:16 H.264/AAC master; original AAC preserved by default.
- Natural-language **effect selection**, editable timeline, verified-script
  acceptance and real original-media rendering.
- Bitstream/frame/audio technical QA, plus explicit creative review state.
- Offline rendering after one-time Docker image build.
- Uploads/downloads remain on `127.0.0.1`; no public network port or
  external video handling.

## What it does NOT yet provide

- Automatic speech-to-script alignment, cinematic art-direction decisions,
  or a human-quality final visual review just by uploading files.
- Invisible, direct attachment transfer from ChatGPT Project files to
  the local machine. The current UI requires you to select the files in
  the **local browser page** even if they were previously uploaded in ChatGPT.
- A promise that every original effect looks photorealistic on every shot:
  42-effect availability does not imply all effects are appropriate.
- Free compute if your computer is off, unable to run Docker, or too slow
  for this workload.
- Automatically differentiated Instagram/LinkedIn framing. The existing
  production tool delivers bit-identical portrait copies.

## Privacy and internet boundary

Docker initially downloads only the project's public code dependencies
and licensed fonts/segmentation models during local build. The running
rendering process needs no network connection for its built-in effects.
The `-p 127.0.0.1:8765:8765` launcher exposes the UI **only on your
computer**, not the LAN or internet. The browser requests use a randomized
bearer token generated at startup and reject non-local HTTP Host/Origin.

If you later want true "upload to ChatGPT Project and get finished MP4
back into that exact chat automatically", we must add a **separate,
authorized file-transfer connector** between ChatGPT and a continuously
available private renderer. GitHub Plugins and Project Source documents
alone are not that connector. A free Google Drive sync bridge is a
possible later integration, but it involves storage/permission/privacy
tradeoffs and is **not implemented** by the local edition.

### Helpful troubleshooting

- `docker` missing: install and start Docker Desktop.
- Build cannot download MediaPipe/models: first build needs working internet.
  Retry after networking is available; the render itself is local.
- Port 8765 busy: stop another Swarag local editor process.
- Missing video audio/script mismatch: correct source, timings and transcript.
- Long 1080p render fails: inspect the private render job and container log.
  The original engine and its cache resume where possible; don't silently
  replace the renderer with generic OpenCV.
- To rebuild updated code: download the updated branch and double-click
  the launcher again; it rebuilds using Docker's cache.

**Status:** free local edition implemented; verify the complete user-facing
workflow on the specific Windows/Mac hardware before treating it as
one-click production-ready. The real user RAG Reel has NOT been rendered by
this new interface.
