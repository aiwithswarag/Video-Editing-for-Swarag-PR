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

## Independently verify all 42 original effects (private, local)

The 42 registered effects and five named looks are available through the
original Swarag engine. Registered does NOT mean production-certified.

**Automated GitHub effect matrix:** Each original effect and named variant
renders on short synthetic 360x640/8fps footage. Tests now validate decoded
preview PNGs, expected image dimensions, full FFmpeg motion/audio decoding,
frame counts, and single-frame pixel-change evidence. These remain BASIC
TECHNICAL SMOKE TESTS, not face-masking or cinematic quality signoff.

**Optional one-click real-camera check on Windows:** Open the updated local
editor and select your clean original MP4. Click the new
**Test all 42 effects on my camera footage** button. It privately extracts
a 2.25-second camera sample and independently renders all 42 original
effects plus five named looks in the real Docker engine. The app displays
progress, then a contact sheet and a downloadable per-effect JSON report.
Missing or failed effects are named explicitly, including incomplete
video/audio decoding. The user media, sample and outputs stay in the
private local jobs folder; do not commit them to GitHub.

The diagnostic is intentionally NOT a second full Reel export. Passing
on 2.25 seconds of original footage cannot certify 1080p typography,
different gestures, accurate captions, stable masking throughout the
whole video, or brand-level artistic professionalism. Human review of
the final full MP4 is still mandatory.

---

## Latest RAG Reel design — ORIGINAL subject-masked glass-widgets (v5)

**The previous opaque policy cards and the subsequent tiny-text dark split
panel were rejected in the user's real-video review.** Do not render with
the legacy `face-safe-editorial-split-v3` compositor. It is intentionally
not in the current production chain.

**Current design:** `subject-masked-glass-v5`, using the *actual*
`glass-widgets` effect registered in `scripts/fx.py`, plus its original
glass blur, gentle pop motion and MediaPipe person-depth compositing.
The full authentic 9:16 video stays visible throughout, with frosted
glass floating in the background while the speaker's silhouette stays in
front. Script-verified cards present ONLY the two fictional 2024/$100 and
2026/$150 policies, outdated cited answer, RAG search/retrieve/generate
flow, one verification question at a time, and the closing thought.
No generic views charts, fake render progress, cloned face avatars,
made-up social UI or irrelevant widgets.

**Do not approve a full render based on a simulated image.** The browser's
three-frame preview now runs the actual `scripts/fx.py --still` engine
on short private excerpts from the uploaded source at the reviewed policy,
RAG and final-check timestamps. This uses real person segmentation.
Only accept the preview if those panels genuinely look professional,
are readable at phone size and do not cover hair, eyes or expressions.
Technical smoke tests are not artistic signoff.

1. Stop the existing Docker Desktop `swarag-local-editor` container.
2. Download latest `feat/executive-editorial-v2` ZIP and extract into a new
   folder; keep old PRIVATE media out of the repository.
3. Double-click `START_FREE_EDITOR_WINDOWS.bat`. In
   http://127.0.0.1:8765/local/version verify:
   `"face_safe_layout_id": "subject-masked-glass-v5"`.
4. Select clean MP4 + full RAG script; create the eight-stage draft.
5. Click **Render 3 genuine glass-widget preview frames**. The source
   video is processed locally only; the result is a preview JPEG.
6. Inspect it; **STOP without full render if design is still basic or
   the original face is obstructed**. When approved, verify spoken-word
   timing, check the relevant confirmations, and then render.
7. Final QA must report eight original `glass-widgets` instances,
   `rag_graphics_pass.layout_id=subject-masked-glass-v5`,
   `subject_depth_mask=true`, and full source frame/audio preservation.
   Human review of the full MP4 remains mandatory.

**Note:** This visual style is an original evidence-specific variant
inside the 42-effect `glass-widgets` catalog entry, not a 43rd effect.

---

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

## Verify the installed build and avoid the one-effect silent failure

The editor header must display the build marker
`RAG-SIX-SECTION-GUARD-2026-11-02` and the localhost
`/local/version` endpoint must return `"rag_six_section_guard": true`.
If the marker is absent, Windows is still using a cached/older application;
stop the previous `swarag-local-editor` container, download the updated
branch ZIP into a **new** folder and double-click the new launcher.

**Confirmed root cause of repeated old-editor confusion:** prior Windows
launchers opened the browser on port 8765 before proving the NEW container
was listening. If the old container was still bound to that port, the
browser displayed the old editor. The updated launcher explicitly refuses
to open when a stale `swarag-local-editor` container or any 8765 listener
is detected; it does **not** kill an active private render.

For the RAG Reel choose **RAG citation / fictional policy explainer —
all six sections REQUIRED** in **Editing mode** (it is selected by
default in this build). After uploading the six-section script, the draft
must display all eight graphics stages. You cannot enable Render full
MP4 in that mode without them. For unrelated videos switch explicitly
to **Other video — original Swarag effect catalog**.
The resulting `production_qa.json` now records `video_mode` and
`editorial_guard_build` alongside `requires_six_section_explainer`,
`editorial_sections_covered` and `rag_graphics_pass`.


A RAG/citation/policy script that is incomplete or lacks six recognizable
time headings now produces an **explicit error** instead of silently
rendering `["slow-push"]`. Use a complete six-heading TXT or DOCX script,
including the fictional 2024/$100 versus 2026/$150 comparison, outdated
citation, retrieval-augmented generation explanation, three checks and closing.
Do not upload a speech-only excerpt and assume the six-section animator will
infer unspoken policy years. The end-user should see exactly eight editable
graphic stages before ticking audio verification or starting a render.

After a successful export, confirm that the JSON technical QA contains
`rag_graphics_pass` with `graphic_stages: 8`,
`requires_six_section_explainer: true`, and six named
`editorial_sections_covered`. A null graphics pass is a **creative failure**
regardless of technical PASS. Send both the real MP4 and the QA here for
full-motion and audio review; technical checks do not certify visual quality.

## Superseded layout v3 — historical notes only, DO NOT USE

The older dedicated RAG graphics compositor used fixed opaque cards across
approximately 60–85% of the image, obscuring the actual speaker's beard,
face, hands or torso. **That was a creative failure despite technical PASS**
and did not match the face-first policy of the original 42-effect engine
or `branding/editorial-v2.json`. Do not publish that render.

**Face-safe layout ID:** `face-safe-editorial-split-v3`.

The corrected version uses the original 42-effect engine first, followed by
a restrained source-backed Executive Editorial V2 split composition.
The real camera lives entirely in the upper 64% of the portrait, while the
fictional policy comparison, outdated citation, retrieval flow and three
checks sit in their own lower ink/ivory/gold typography region. There is
**zero alpha overlay in the live camera region**. When the repository YuNet
face detector sees the source face reliably, the editor selects a static,
non-distorting crop that keeps the face clear. If detection is uncertain,
it fits the ENTIRE original portrait into the top camera region rather
than risk cutting off the speaker. The frame is not stretched or replaced
by a fake person; the original audio remains bit-identical.

**The local editor now requires a three-frame visual preview before a
full RAG export:**

1. Confirm the updated build: open
   `http://127.0.0.1:8765/local/version`. It must contain
   `"face_safe_layout_id": "face-safe-editorial-split-v3"` and
   `"layout_preview_required": true`.
2. Select your original clean MP4 and full six-section script; create
   the draft, and review all eight editable effect/graphic stages.
3. Click **Generate 3-frame face-safe preview**. It makes a local contact
   sheet using actual frames from the same recording and the same
   graphic geometry for policy cards, RAG flow and checks.
   This does not render or replace the full film; the preview is pre-grade
   and pre-effects and is not a substitute for watching actual motion.
4. Inspect the three preview frames. If the design is wrong or clips
   your head, **DO NOT approve or render**; report it. Only tick
   **I inspected the three actual layout frames and the graphics do NOT
   cover the speaker** when true, after checking clean source and audio.
5. Render the full MP4. The final QA's `rag_graphics_pass` must report
   `layout_id: face-safe-editorial-split-v3`,
   `face_safe_layout: true` and
   `graphics_overlap_camera_pixels: false` in addition to all
   eight stages and all six story sections.
6. Upload the real output MP4 and QA to the ChatGPT conversation for
   normal-motion/phone-size/skin/speech review. Automated bounds checks
   are not equivalent to human creative approval.

**Windows:** stop any previous `swarag-local-editor` container and
leave old `PRIVATE` media untouched. Download the latest branch ZIP to
a NEW extracted folder and double-click `START_FREE_EDITOR_WINDOWS.bat`;
Docker recompiles the code. This preserves zero monthly hosting fees.

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
