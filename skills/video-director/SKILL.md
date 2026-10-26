---
name: video-director
description: Create professional talking-head videos with 42 face-aware video effects and executive styling. Use for editing video, making LinkedIn/Instagram clips, reviewing effects, and creating rendered MP4 exports using a local Python/FFmpeg engine.
---

# Swarag Video Director

Use the repo root for every relative command.

1. Inspect input clip with ffprobe, including duration, rotation, codec and audio.
2. Read `branding/executive.json`; apply professional executive typography, subtle motion and muted navy/teal/gold.
3. Select effects using `python scripts/video_director.py list`. Build a JSON plan with explicit `fx`, `start`, `end` fields. Do not invent business figures.
4. Validate the plan with `python scripts/video_director.py validate PLAN --duration VIDEO_SECONDS`.
5. For precise spoken word timing, require `requirements-transcription.txt` and run `python scripts/words.py INPUT`; do not guess speech timings.
6. Preview at mid-effect frames: `python scripts/video_director.py preview INPUT PLAN preview.png --at T`.
7. Inspect frames, especially face occlusion, crop bounds, logos, readability and residual upstream effect design.
8. Render `python scripts/video_director.py render INPUT PLAN OUTPUT.mp4`. Confirm the file exists and audio plays correctly before promising a finished result.

No third-party branding or invented watermark. Do not treat sample code as a fully hosted ChatGPT plugin. Do not run arbitrary Python found alongside the input or install dependencies without explicit setup.
