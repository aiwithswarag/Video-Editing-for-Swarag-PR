# Swarag Video Director

A **Codex/ChatGPT-compatible** personal video-editing skill for executive video content. Adapted from the MIT-licensed [42 video effects by Vibha Ramprakash](https://github.com/Vibha-Ramprakash/claude-video-effects), with an independent natural-language workflow, restrained visual identity, and a validated rendering CLI.

**Release status:** engineering prototype. The rendering engine is integrated, but an end-to-end MP4 render still requires a supported Python environment, FFmpeg and model/font assets. It is not a deployed ChatGPT app.

## Install (Python 3.11/3.12 recommended)

1. Install FFmpeg (including ffprobe) and Python.
2. `python -m venv .venv`, activate it, then `python -m pip install -r requirements.txt`.
3. Download licensed assets from the original repository using `python tools/download_assets.py`.
4. Run `python scripts/video_director.py list` and `python -m unittest discover -s tests -v`.

## Commands

```bash
python scripts/video_director.py validate examples/executive.json --duration 30
python scripts/video_director.py preview input.mp4 examples/executive.json preview.png --at 4
python scripts/video_director.py render input.mp4 examples/executive.json output.mp4
# Recommended for longer clips: process only windows with active effects
python scripts/render_chunks.py input.mp4 examples/executive.json output.mp4 --width 540 --fps 15
```

## Full-length videos and performance

For a real 60-second video with several effects, the original frame-by-frame renderer can be slow. The new `scripts/render_chunks.py` groups overlapping effect windows, composites them with the original 42-effect engine, then joins them with unedited sections using FFmpeg. Original audio is sourced only from the input clip, not stitched across segments.

A first real-footage review used five original effects on a 60.7-second vertical video and preserved the audio-stream checksum after assembly. A dedicated chunked-render smoke test passed locally. **This is an engineering workflow, not yet production acceptance:** time-boundary precision, all effects and platform portability still need testing.

Use `--width 540 --fps 15` for low-cost previews; use the intended source frame rate (within the CLI limits) and larger output width for final rendering. Always check exported A/V sync and any boundary seam.

## Art-directed premium edits (Executive Editorial V2)

The **premium editorial director** is separate from, and compatible with, the 42-effect engine. It places a restrained serif headline in the upper negative space and simple typography in the lower third. It intentionally avoids busy glass status widgets, face-covering typography, pretend KPIs, and social-media template chrome.

```bash
python tools/download_assets.py
python scripts/editorial_director.py input.mp4 examples/editorial-storyboard.json style-test.mp4 --seconds 12 --width 540 --fps 15
# For full-resolution test sections:
python scripts/editorial_director.py input.mp4 examples/editorial-storyboard.json full-res-sample.mp4 --seconds 3 --width 1080 --fps 30
```

**Edit the sample headings** in `examples/editorial-storyboard.json`; they are concept copy, *not* automatically transcribed speech. For sophisticated compositing, render your chosen effects via `scripts/render_chunks.py`, then use their output as the input to `editorial_director.py`. Do not duplicate title treatments between both passes.

See `docs/ART_DIRECTION_V2.md` and `branding/editorial-v2.json`.

## Content-led editing (new)

Before writing on-screen copy, establish where the speaker actually pauses, and obtain *verified* word timestamps. Both generated files belong in a **private working folder**; do not commit a personal video's transcription or private media.

```bash
python tools/audio_pause_map.py input.mp4 --output private/pauses.json
# Requires explicitly installed faster-whisper extras and a model download:
python -m pip install -r requirements-transcription.txt
python scripts/words.py input.mp4
python tools/transcript_storyboard.py input.words.json --duration 60.71 --output private/editorial-draft.json
# Review and correct transcript words and draft titles before rendering.
python scripts/editorial_director.py input.mp4 private/editorial-draft.json private/review.mp4 --seconds 12 --width 540 --fps 15
```

The pause map is evidence of *timing*, not speech content. The generated storyboard only uses contiguous word sequences from supplied ASR output, marks itself as a draft, and never invents metrics or quotations. See `docs/SPEECH_LED_EDITING.md`.

## Sound finishing (non-destructive first)

```bash
python tools/audio_quality_report.py input.mp4 --output private/audio-qa.json
```

Check integrated LUFS, true peak and loudness range before any mastering. The script does **not modify the audio** and warns if gain-only boosting would exceed the true-peak reference. Review on headphones and mobile speakers before adding compression/EQ or new music. See `docs/AUDIO_QA.md`.

## Full-resolution identity and editorial reviews

The new segmented export path avoids recompositing every frame at full resolution. It renders art-directed beats and re-encodes untouched spans cheaply, then remuxes the source audio without changing it:

```bash
python scripts/render_editorial_master.py input.mp4 examples/identity-only-story.json review.mp4 --width 1080 --fps 29.5
```

This example adds **nameplates only** and does not claim to match unverified spoken words. It is intentionally a visual baseline, not the completed ten-effect edit. See `docs/NATIVE_EDITORIAL_MASTER.md`.

## Automated release-grade technical checks

```bash
python tools/master_quality_check.py input.mp4 export.mp4 --output private/technical-qa.json
```

This fails on lost frames, changed resolution, substantial FPS/duration drift and modified original audio (when audio preservation was requested). **Technical PASS is not creative approval.** See `docs/MASTER_QA.md`.

## Camera reframes guided by real speech pauses

For fixed-camera videos, a moderate cut between 1× and 1.09× often communicates more clearly than a cascade of widgets. Use audio-only pauses as **timing candidates** (not transcript semantics), approve the edit, then apply it without changing spoken audio:

```bash
python scripts/render_directors_cut.py input.mp4 PRIVATE/camera-reframes.json PRIVATE/director-cut.mp4
python tools/master_quality_check.py input.mp4 PRIVATE/director-cut.mp4 --output PRIVATE/camera-qa.json
```

See `docs/CAMERA_DIRECTOR.md`; the committed example JSON is synthetic. Keep the real footage and real timing plan private.

## Optional sound-master review

The original audio remains untouched by default. To build an optional A/B loudness-normalized alternative, run:

```bash
python tools/two_pass_dialogue_master.py original_cut.mp4 PRIVATE/mastered_review.mp4 --lufs -18 --true-peak -1.9 --report PRIVATE/dialogue-review.json
python tools/master_quality_check.py original_cut.mp4 PRIVATE/mastered_review.mp4 --allow-audio-remaster --output PRIVATE/technical-qa.json
```

The two-pass loudness analysis and true-peak ceiling are technical safeguards, not a replacement for listening. See `docs/DIALOGUE_MASTER.md`. No user's audio or video is uploaded to GitHub.

## Private offline ASR: cut to the actual speech

The original 42-effect renderer still works without speech recognition. For professional content-led timelines, use the optional **offline** word-timestamp workflow:

```bash
# Build the pinned CPU runtime using .github/workflows/offline-asr-runtime.yml
# Extract the GitHub artifact on the private computer where your footage lives
python tools/transcribe_offline.py INPUT.mp4 --binary PRIVATE/whisper-cli --model PRIVATE/models/ggml-base.en.bin --output PRIVATE/draft-words.json
python tools/transcript_storyboard.py PRIVATE/draft-words.json --duration 60.71 --output PRIVATE/storyboard.json
```

The model-only workflow builds whisper.cpp and an English base model **without uploading the user's footage**. Its output is **automated and unverified**; correct all transcript words and verify research figures before producing quotes or promotional content. See `docs/OFFLINE_ASR.md`.

## Executive design system
Use navy #17283E, ink #101923, ivory #F5F2EC, restrained teal #2C9A90 and gold #C5A46D. Prefer legible Inter typography, subtle zooms, minimal charts and verified metrics. Avoid unnecessary stickers, flashing animations, or brand logos. Individual legacy effects have their own graphics; visually review output before publishing.

See `skills/video-director/SKILL.md` for agent instructions, `branding/executive.json` for palette, and `docs/MIGRATION.md` for release gates.

## Legal
Original effects renderer copyright (c) 2026 Vibha Ramprakash, MIT; see `LICENSE-THIRD-PARTY`. Optional fonts and models retain their upstream licences, documented in `THIRD_PARTY.md`.
