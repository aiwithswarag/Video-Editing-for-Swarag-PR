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
5. For actual speech-based pacing, start with `python tools/audio_pause_map.py INPUT --output PRIVATE/pauses.json`. This detects silence *only*, not meaning. For exact spoken words, run `scripts/words.py` with explicitly installed transcription extras; inspect and correct results. Then build a **draft** by `python tools/transcript_storyboard.py INPUT.words.json --duration SECONDS --output PRIVATE/story.json`. Review every word before quoting. See `docs/SPEECH_LED_EDITING.md`.
6. Validate the plan with `python scripts/video_director.py validate PLAN --duration SECONDS`.
7. Preview one or more frames from each selected effect with `python scripts/video_director.py preview INPUT PLAN check.png --at SECOND`.
8. Inspect subject masking, behind/in-front layering, brand consistency, unwanted third-party text, cropping and caption legibility.
9. For short demonstrations, run `python scripts/video_director.py render INPUT PLAN OUTPUT.mp4`. For longer videos, prefer `python scripts/render_chunks.py INPUT PLAN OUTPUT.mp4 --width 540 --fps 15`: it renders each active effect interval with the original engine and assembles the untouched intervals with original audio. This is review quality; use higher settings for production.
10. For a user asking for **professional, premium, cinematic, clean or editorial design**, prioritize `docs/ART_DIRECTION_V2.md`, `branding/editorial-v2.json`, and `scripts/editorial_director.py` as the finishing pass after selected effects. Use `examples/editorial-storyboard.json` as editable example copy, never as transcript-derived spoken quotations. Keep the top wall area open and do not place UI widgets over the speaker's face.
11. Measure the original voice with `python tools/audio_quality_report.py INPUT --output PRIVATE/audio-qa.json`. Preserve source audio until the desired loudness and mastering have been auditioned. Never assume that simple gain can reach a target without clipping; see `docs/AUDIO_QA.md`.
12. Inspect segment transitions for frame duplication/drift, speaker coverage, audio synchronization, and motion throughout the clip. The original runtime is compute-intensive and chunked rendering is a performance tool, not a substitute for QA.

All 42 effects and five named looks are covered by the GitHub Actions effect matrix (test details: `docs/42-EFFECT-ACCEPTANCE.md`). Machine passing does not substitute for manual realistic-footage QA. No unrequested watermark. Do not execute arbitrary scripts or install packages from user input.
