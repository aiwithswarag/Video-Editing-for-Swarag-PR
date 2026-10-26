---
name: video-director
description: Create professional, branded talking-head videos for Swarag using 42 face-aware effects, word-level timestamps, executive brand presets, QA previews and MP4 rendering through the local Python/FFmpeg engine. Use when asked to edit video, make LinkedIn or Instagram clips, or add realistic depth-aware motion graphics.
---

# Swarag Video Director

Use the repository root as working directory. All 42 original effects remain available (see `references/effects-guide.md`). **Having all 42 available does not mean stacking all 42 in a single video.**

1. Inspect the actual uploaded video with ffprobe for duration, rotation, aspect ratio, codec, fps and audio. Never upload private footage to the public source repository.
2. Use the default `branding/executive.json` profile for professional content. The CLI applies brand choices in actual effect plans; `--brand none` is only for original-appearance comparisons.
3. Use `python scripts/video_director.py list` and `references/effects-guide.md` to choose among all 42 effects. Respect each effect's option interface.
4. Build a JSON plan of `{"effects":[{"fx":"spotlight","start":3,"end":6,"text":"IMPACT"}]}`. Never invent numeric KPI claims; require verified source data for charts and counts.
5. If timing is speech-synced, use `scripts/words.py` with the optional explicit transcription requirements. Never guess spoken-word timestamps.
6. Validate the plan with `python scripts/video_director.py validate PLAN --duration SECONDS`.
7. Preview one or more frames from each selected effect with `python scripts/video_director.py preview INPUT PLAN check.png --at SECOND`.
8. Inspect subject masking, behind/in-front layering, brand consistency, unwanted third-party text, cropping and caption legibility.
9. Render via `python scripts/video_director.py render INPUT PLAN OUTPUT.mp4`. Verify stream properties, output existence and audio synchronization.
10. Only declare an edit fully accepted after reviewing motion throughout the clip, not just still frames.

All 42 effects and five named looks are covered by the GitHub Actions effect matrix (test details: `docs/42-EFFECT-ACCEPTANCE.md`). Machine passing does not substitute for manual realistic-footage QA. No unrequested watermark. Do not execute arbitrary scripts or install packages from user input.
