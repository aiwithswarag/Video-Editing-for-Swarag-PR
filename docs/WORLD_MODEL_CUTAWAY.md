# Original World Model conceptual cutaway

An **original vector-style animation** of a robot considering different outcomes when reaching for a cup. It is a conceptual explanation, **not** robot-benchmark footage or evidence of a measured success rate. The animation itself includes this notice.

Colours follow Swarag Executive Editorial: navy/ink, muted teal, ivory and restrained gold. It has three phases: OBSERVE / SIMULATE / CHOOSE. Deliberate restraint makes the animation readable on a phone.

Install FFmpeg, Pillow and the repo's licensed fonts using `python tools/download_assets.py`. Then render an exact number of source-rate frames:

```bash
python scripts/world_model_cutaway.py PRIVATE/prediction_cutaway.mp4 --width 1080 --fps 29.5 --frames 192
python scripts/insert_cutaway.py PRIVATE/base_edit.mp4 PRIVATE/prediction_cutaway.mp4 PRIVATE/new_edit.mp4 --at-frame 385
python tools/master_quality_check.py PRIVATE/base_edit.mp4 PRIVATE/new_edit.mp4 --output PRIVATE/technical.json
```

The 385/192 numbers are a private example for a particular 60.7-second video; they are **not** general defaults. This graphic is video-only. The compositor preserves the real, original speech audio.

Use source transcript and visual context to select actual edit points. Confirm the final edit on mobile and review any claims independently before publication. No private footage, transcripts, timeline or screenshots are included in source control.