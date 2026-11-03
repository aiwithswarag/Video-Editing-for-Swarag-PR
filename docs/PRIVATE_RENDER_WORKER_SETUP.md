# Swarag: eliminate Work's dependency-installation blocker

**Status (30 Oct 2026):** The repository has a Dockerfile for a pre-provisioned environment, and the container build/test has passed in GitHub Actions. This is **not** a deployed production service and does not automatically connect a ChatGPT Project to a renderer.

## Why the user's Work test failed

The Project/Work environment could inspect the uploaded MP4 (1080x1920, 30 fps, about 60s) and GitHub source files, but its runtime had no GitHub clone/package network and lacked MediaPipe, fonts and segmentation assets.

**Do not retry pip/GitHub installs in the same restricted runtime** expecting a different result. The appropriate solution is to build once in trusted CI and run on an authorized machine that already has the dependencies.

## Prepared environment

- `Dockerfile`: Python 3.12, FFmpeg, native OpenCV runtime libraries, pinned-compatible Python requirements, real MediaPipe, Git-hash-verified original licensed fonts and face/segmentation models. Includes all repository code.
- `.dockerignore`: excludes local videos, audio, transcripts, export directories, secrets and model/font outputs from build context; approved public assets are fetched/verified during build.
- `.github/workflows/renderer-container.yml`: builds the image using GitHub CI networking, checks 42-effect registry, dependencies, assets, and performs *real synthetic MP4 editing with Docker networking disabled*, proving there is no dependency/download requirement during execution. No real/private media goes to CI.

The pre-built image is **a dependency solution**, not a queue, web upload portal, video transcript matcher, or ChatGPT plugin. Its default command lists effects; an authorized compute operator or deployed worker must run the production CLI with private input files.

## Remaining single-Project experience: private rendering service

For the desired 'upload video + script + creative request in ChatGPT -> receive finished MP4', implement and connect this architecture:

1. **ChatGPT Project/Work**: User uploads video and script. An authorized workflow checks the actual spoken words, creates the timed editing plan and supplies approved effects/options. The Project Sources govern branding but cannot execute code.
2. **Secure ingestion**: The Project/agent transfers original video, approved script and timed edit plan over an authenticated private interface to worker-owned encrypted temporary storage. A GitHub plugin is **not** an input-media transport.
3. **Containerized rendering worker**: A private hosted service runs the prebuilt Docker image on sufficient CPU/RAM/disk resources, executes `scripts/produce_video.py render` and captures bounded logs, status, completion and failures. Do not run user-supplied shell commands; validate effect data with `tools/plan_validation.py`.
4. **Private result delivery**: The worker emits `final_master.mp4`, QA JSON and optional copies. Results are made available using authenticated retrieval / short-lived signed URLs, not GitHub Actions public artifacts. The agent attaches the verified MP4 to the chat. Delete source footage and temporary artifacts according to an explicit retention policy.
5. **Creative QA**: Automated stream tests are necessary but insufficient for a promise of realistic speaker masking; review the *real finished video* and correct rejected effects before approval.

## One-time deployment decisions

- **Hosting:** Choose an authorized Docker-capable environment with a persistent/temporary private data volume, enough resources for a 60-second 1080p render, and external access for the agent or approved file bridge. A managed deployment provider such as Render or Railway is an option, but no deployment has yet occurred.
- **Credentials:** GitHub repository access for building source; a separate private token or OAuth authorization for media upload/results. Never put private tokens or uploaded video in Project Sources, public repo, CI logs or container build context.
- **User approval:** The user must connect/authorize the hosting account and consent to the selected region, costs and retention policy before actual deployment.

## What is verified vs not verified

**Verified in CI:** Docker build, dependency/asset loading, all 42 effect registry entries, and end-to-end synthetic MP4 generation without runtime networking.

**Not yet verified:** private worker hosting, authenticated job API, connection from *this specific ChatGPT Project*, real video byte transfer, transcript matching, 1080p 60-second creative rendering, user-visible final MP4 delivery, and human visual approval.

Do not call the Project 'one-click fully working' before a real uploaded video passes all of those acceptance gates.
