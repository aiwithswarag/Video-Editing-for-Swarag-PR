# Migration audit and release gates

Source repo: Vibha-Ramprakash/claude-video-effects (MIT), revision d675cff93cb3719a5728348566f80ba44073c9e0.

- Original 42 Python effects adapted and included in scripts/fx.py.
- Claude-branded sample text removed from copied default labels.
- Private local module auto-execution intentionally disabled.
- CLI validates plans and prevents accidental source overwrite.
- Transcription is optional and does not install packages at runtime.
- Executive brand profile and skill workflow added.
- Test plan schema and Python syntax via GitHub Actions.

## Limits before production
- Integration render test still required with FFmpeg, fonts, models, NumPy, OpenCV, Pillow and MediaPipe.
- The original renderer encodes audio to AAC rather than bitwise copy.
- Some effects implement social-platform interface motifs; adjust or avoid them to meet a strict executive aesthetic.
- Fonts and model notices need licence compliance review before distribution.
- No cloud job runner or remote MCP endpoint implemented.
- Rendering quality and speech sync must be checked on representative user footage.
