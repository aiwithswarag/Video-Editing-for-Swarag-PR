# Automated master technical QC

Run after any native-resolution export:

```bash
python tools/master_quality_check.py original.mp4 export.mp4 --output private/technical-qa.json
```

Checks H.264 output, original aspect ratio and resolution, video-frame count, average frame rate (±0.05 fps), duration (±120 ms), audio codec and **bit-identical audio stream MD5** by default. A failed check returns non-zero. For a deliberate lower-resolution or changed-frame-rate preview use `--expected-width 540 --allow-fps-change`. When audio was intentionally mastered, `--allow-audio-remaster` disables identical-audio checks; audition the master separately.

This is **technical** QA, not visual, caption, sound-quality or human editorial approval. The JSON report explicitly marks creative approval as outstanding.

A private 60.711856-second, 1080×1920 source was exported as a 60.711900-second 1080×1920, 1791-frame H.264 master review, with identical source AAC stream MD5. Technical QA passed and complete video decoding produced no errors. This is an **identity-only review**, not the ten-effects content-led final. No private media or QA data is committed.
