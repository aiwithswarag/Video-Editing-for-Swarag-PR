# CINEMATIC FINAL — Prompt commands and finishing CLI

**Prompt to paste with uploaded ORIGINAL video, script and approved reference media:**

> SWARAG CINEMATIC FINAL — EXECUTE THE WORKFLOW. Use the original video and supplied script. In a video-capable Work environment, verify the transcript against audio, build a word-timed story plan, choose relevant original effects from my 42-effect catalog, mask the person cleanly, choose only motivated B-roll and accurate research cards, and colour-finish the original camera footage before applying graphics wherever possible. Maintain believable natural skin, restrained Rec.709 contrast, white balance, highlights, detail-preserving sharpening and noise reduction only when needed. Do not invent 4K optics, bokeh, research evidence or speech. Finish clean audio with an optional A/B mastered mix. Export actual complete H.264/AAC 9:16 MP4 files for Instagram, LinkedIn and YouTube Shorts with video and audio technical QA. Deliver the finished files, captions, script-timeline, source list and QA—not just screenshots. If tools are missing, explain what could not be rendered.

**Shorter prompt:** `SWARAG CINEMATIC CLEAN` — keep original talking head and voice, reduce visual clutter, finish colour/sound, show a 4s A/B preview, then render full 9:16 exports.

**Story-editing prompt:** `SWARAG EFFECTS DIRECTOR` — use the attached verified script and video to select only the most relevant original 42-effect implementations, not all simultaneously; preview actual motion, check tracked foreground masks, and deliver a frame-verified final export.

**These are prompts, not built-in ChatGPT slash commands.** Actual rendering requires a connected repository and functioning Python/FFmpeg execution such as ChatGPT Work. Text-chat alone is not a guaranteed automatic renderer.

## Executable terminal commands

```bash
# First, edit and approve the STORY and effect timeline using existing repo tools.
# Then apply the filmic finish to a reviewed MP4 (do not apply it to only the overlays):
python scripts/cinematic_finish.py "reviewed_edit.mp4" --look clean-studio --platform all --audio source --output-dir exports

# Compare 4 seconds with a stronger, but still natural, look:
python scripts/cinematic_finish.py "raw_video.mp4" --look editorial-cinema --platform instagram --start 8 --seconds 4 --preset veryfast --audio aac --output-dir previews

# Optional sound A/B — not automatically enabled:
python tools/two_pass_dialogue_master.py "reviewed_edit.mp4" "mastered_review.mp4" --lufs -18 --true-peak -1.9 --report PRIVATE/audio.json
python scripts/cinematic_finish.py "mastered_review.mp4" --look clean-studio --platform all --audio aac --output-dir exports
```

Use `tools/master_quality_check.py` to check duration, dimensions and source audio; permit remastered audio explicitly when intentional. For genuine HDR footage, tone-map properly rather than just relabel BT.709. Do not crop vertical portraits into 16:9 long-form YouTube automatically.

## Output properties

All three presets produce 9:16 H.264, yuv420p, Rec.709, fast-start MP4 at SOURCE FPS; output pixels are at or below the original resolution, never inventing 4K detail. Instagram aims below its documented upload bitrate ceiling, LinkedIn below 30 Mbps, and YouTube Shorts at upload-quality H.264. Original audio is stream-copied in full-length `--audio source` mode; optional `--audio aac` re-encodes at 48 kHz, **not a loudness master**. Avoid strong noise reduction on clean footage: the optional `restoration` preset is much slower and can remove skin texture.

Full camera image processing is CPU/GPU intensive; ensure a capable renderer for minute-long 1080p, and run a short preview first. A technical PASS is not proof of professional artistic approval, script truthfulness or face-aware effect quality.

Never commit user footage, transcripts, font binaries, private EDLs or final film to the public repository.
