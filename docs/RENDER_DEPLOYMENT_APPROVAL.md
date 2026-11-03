# Swarag Render pilot — deployment approval and security checklist

**Status:** Prepared on GitHub branch `feat/executive-editorial-v2`. **NOT DEPLOYED. NOT BILLING.** This is an operator/developer deployment specification, not a guarantee of a ChatGPT-native upload-and-edit workflow.

## Customer's goal

Upload a clean original video and matching script to the existing Swarag ChatGPT Project, request effects in ordinary language, and receive a real professionally finished MP4 using the original 42-effect engine. The existing Project has Sources and an authorized GitHub integration; neither turns GitHub code into live rendering.

## Verified building blocks

- Dockerfile includes FFmpeg, MediaPipe, verified subject-segmentation models, licensed fonts, and the original 42 registered effects. GitHub CI previously passed the synthetic MP4 test without network access during rendering.
- `scripts/produce_video.py` is the correct grade-first editing/export path. It records `renderer_provenance`, requires validated effects, tests output frame count and audio, and creates `production_qa.json`, `release_gate.json`, `final_master.mp4`.
- `tools/render_job_api.py` is the proposed single-instance HTTPS API. It does not accept untrusted shell commands or any user-designated filesystem paths. Its private endpoints require `SWARAG_API_TOKEN` (a strong bearer secret).
- `render.yaml` declares one manually deployed Docker web service. It is **publicly addressable over HTTPS** but media ingress/egress requires token authentication; it is not a Render internal-only private service. A truly private Render service would not be directly reachable from ChatGPT outside the Render network.

## Draft deployment choices — review BEFORE charges

| Item | Proposed | Why |
|---|---|---|
| Workspace | The Video Editors | User-connected Render workspace |
| Branch | `feat/executive-editorial-v2` (draft PR #5) | Contains newest editor and safe release guards; do not merge casually |
| Region | Singapore | Nearby supported region; get explicit privacy/residency approval |
| Type | Web service with Docker runtime | Authenticated HTTP endpoint that an authorized ChatGPT/Work bridge can reach |
| Compute plan | `2c-4g` (2 vCPU / 4GB) | Proposed starting benchmark for 1080p MediaPipe/FFmpeg, NOT performance-certified |
| Storage | 20 GB Render persistent disk mounted at `/workspace` | Resumable private jobs and MP4 exports; cannot scale this instance horizontally |
| Automatic deploy | Off | Prevents PR code pushes from restarting active private renders |
| Render previews | Off | Avoid duplicate paid preview workers |
| Render secret | `SWARAG_API_TOKEN` (manual, never stored in Git) | Required >=32-character randomly generated secret; distribute only through secure channels |
| Media lifetime | API deletes completed/failed jobs after 24 hours; sweeps hourly | Retention applies to LIVE disk files only |
| Snapshot caveat | Render automatically snapshots persistent disks daily and retains snapshots at least 7 days | **Deletion from the running disk does not immediately delete snapshots.** Ask user to authorize this or choose an ephemeral-storage/no-snapshot design |
| Cost when continuously active | **~$85/month compute + ~$5/month for 20 GB SSD = ~$90/month** before bandwidth, taxes and any workspace subscription | Subject to current Render Dashboard price; compute prorated by runtime |
| Billing status | Zero resources created by this plan | GitHub YAML and tests do not charge the Render account |

If only occasional videos are needed, compare on-demand Render Workflows or a manually started/stopped service before accepting persistent monthly cost. On-demand requires a separate job orchestration/storage design and is **not** implemented by this Blueprint.

## Supported internal API workflow

All endpoints except `GET /health` require `Authorization: Bearer <private token>`. Do NOT paste the token into a ChatGPT conversation, Project Source, GitHub file, code example, PR comment or public link.

1. The authorized agent inspects the original video's speech and script and creates a script-accurate JSON `effects` plan from the true 42-effect catalog. The API does NOT perform transcription, natural-language interpretation or script alignment by itself.
2. POST `/v1/jobs` with JSON `{"effects":[{"fx":"slow-push","start":0.5,"end":2.5,"zoom":1.05}],"requires_transcript":true,"transcript_verified":true,"source_clean_confirmed":true}`. The flags must reflect actual verification; do not forge them.
3. PUT raw original MP4 bytes to `/v1/jobs/<job-id>/video`. Upload matching private TXT/DOCX/PDF script bytes to `/v1/jobs/<job-id>/script`. Maximum default MP4 upload size 512 MB. No GitHub media uploads.
4. POST `/v1/jobs/<job-id>/start`. One render at a time; the video is processed asynchronously within the running server and full logs stay on private storage. A service restart marks in-progress jobs INTERRUPTED; the caller may restart after checking conditions.
5. Poll GET `/v1/jobs/<job-id>`. A successful technical render returns status `REVIEW_REQUIRED`, never automatic creative approval.
6. Download authenticated `/v1/jobs/<job-id>/master`, `/qa`, and `/release`. Actual full-motion and audio review is still mandatory. Download the verified master and attach it to the authorized ChatGPT conversation through a supported file-capable workflow.
7. DELETE `/v1/jobs/<job-id>` after acceptance, or wait for the 24-hour active-disk cleanup. Remember the snapshot retention caveat.

No public endpoint exposes a media file without the bearer token. Output filenames do not indicate Instagram/LinkedIn-specific crops; the current production engine makes bit-identical portrait copies.

## Required acceptance gates before calling it operational

- Validate `render.yaml` with current Render CLI, and review the active plan, disk, bandwidth and workspace fees in Dashboard before applying.
- Confirm Render's GitHub integration is authorized to read the draft branch. Blueprints normally read the linked repo and might require merging `render.yaml` into the default branch; do not merge PR #5 just to deploy without separate code review.
- Run a real user-authorized upload through the authenticated HTTP API on the deployed service. Confirm 1080x1920 source, 30 fps / exact frame count, grade-before-effects, MediaPipe rendering, AAC preservation, visual quality and output download.
- **Do not use simplified OpenCV/GrabCut/Pillow/FFmpeg substitutes** as if they were the original 42-effect engine. Fail the release gate on unknown provenance.
- Confirm Render disk mount is writable by the container's non-root user (UID 10001); if not, fix mount ownership/permissions before accepting uploads.
- Perform manual 100% MP4 motion/speech verification and full audio listening. The server enforces a technical release gate, but cannot approve human art direction.
- Complete the **ChatGPT-to-API media-transfer integration**. The connected Render management plugin can create/manage services but does not automatically upload arbitrary chat attachments or read the private bearer token. A secure authorized Work or custom connector workflow is still required.

## Change-control and privacy

- Keep personal video/script/transcripts/outputs out of GitHub repo, PR, Docker image, test fixtures and CI artifacts.
- Do not apply the Blueprint or create paid service resources until the user explicitly approves the compute region, expected cost and live-disk/snapshot retention.
- No external or public product reference should be displayed in exported research cards unless factually verified. Captions must reflect the actual audio.
- Do not call technical QA a complete creative sign-off. If the original media or rendering engine cannot run, report BLOCKED.

**Repo:** https://github.com/aiwithswarag/Video-Editing-for-Swarag-PR
