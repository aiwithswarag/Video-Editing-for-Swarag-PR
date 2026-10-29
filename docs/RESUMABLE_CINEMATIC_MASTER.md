# Resumable full-length cinematic master (9:16)

## Why

A previous 60.7-second, 1080×1920 graded render exceeded the available CPU time. The regular cinematic finishing command re-encodes each platform variant separately. This **opt-in** path divides the reviewed portrait edit into frame-counted H.264 chunks, can resume after interruption, concatenates video without a second full transcode, and remuxes the original audio bitstream.

**This is a finishing/export tool, not an automatic editor.** It does not select 42-effects, correct transcription, generate B-roll, evaluate skin tone, or certify research claims. First verify the script and complete a content-led reviewed edit using the existing tools.

## Run on your private video workstation

Requires Python, FFmpeg, ffprobe and the repo scripts. The input must be a constant-frame-rate 9:16 MP4 with a single video track and audio, with readable exact frame count. HDR sources must be properly tone-mapped separately (not relabeled). Keep private video files and the exported deliverables **outside the public GitHub repository**.

Preview the look first using the regular `scripts/cinematic_finish.py --start ... --seconds ...` workflow.

```bash
# Full render in resumable ~6-second sections at 29.5fps:
python scripts/resumable_cinematic_master.py PRIVATE/world_models_reviewed.mp4 \
  --output-dir PRIVATE/world_models_release \
  --look editorial-cinema --preset veryfast --crf 18 --chunk-frames 180

# On slow/interrupted systems, render at most one chunk per invocation.
# Repeat this exact command to continue where the last run stopped:
python scripts/resumable_cinematic_master.py PRIVATE/world_models_reviewed.mp4 \
  --output-dir PRIVATE/world_models_release \
  --look editorial-cinema --preset veryfast --crf 18 --chunk-frames 180 --next-chunk

# Assemble and run full technical verification only after all chunks exist:
python scripts/resumable_cinematic_master.py PRIVATE/world_models_reviewed.mp4 \
  --output-dir PRIVATE/world_models_release \
  --look editorial-cinema --preset veryfast --crf 18 --chunk-frames 180 --final-only
```

The output directory contains a source/settings fingerprint manifest. Never mix chunks from different files or settings; changing CRF, source mtime, or look requires a **different output directory**. Each chunk must match its expected video frame count, resolution, and FPS. Full assembly checks total frame count, duration (±130ms), audio-stream MD5 identity and a complete decode. A failed check returns non-zero.

## Deliverables

- `cinematic_master.mp4`: single H.264/yuv420p/BT.709 9:16 video with unchanged source audio.
- `cinematic_master_instagram.mp4`, `cinematic_master_linkedin.mp4` and `cinematic_master_youtube-shorts.mp4`: **bit-identical copies** of the shared cross-platform master, not separately tuned encodes. The common conservative H.264 bitrate ceiling is 16 Mbps. If platform-specific compression or aspect ratios are required, use the regular finishing tool.
- `cinematic_qa.json`: machine-verifiable technical results and an explicit creative review status.
- `render_manifest.json` and temporary numbered chunks for repeatability/resuming.

Neither a PASS nor identical audio hashes certify professional-grade appearance or intelligibility. **Listen to the full video; inspect every graphic, cutaway, transition, research source, on-screen quotation, skin tone and mobile safe area before posting.** The `--approved` flag is only for manually recording a human signoff; do not use it automatically. No source-media upload is performed by the script.

The segmented workflow was tested on a short synthetic source at 59/2 fps with an interrupted/resumed render and an audio-bitstream checksum match. It has **not yet been benchmarked or creatively approved on the private 1080p World Models footage**.
