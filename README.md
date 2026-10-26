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
```

## Executive design system
Use navy #17283E, ink #101923, ivory #F5F2EC, restrained teal #2C9A90 and gold #C5A46D. Prefer legible Inter typography, subtle zooms, minimal charts and verified metrics. Avoid unnecessary stickers, flashing animations, or brand logos. Individual legacy effects have their own graphics; visually review output before publishing.

See `skills/video-director/SKILL.md` for agent instructions, `branding/executive.json` for palette, and `docs/MIGRATION.md` for release gates.

## Legal
Original effects renderer copyright (c) 2026 Vibha Ramprakash, MIT; see `LICENSE-THIRD-PARTY`. Optional fonts and models retain their upstream licences, documented in `THIRD_PARTY.md`.
