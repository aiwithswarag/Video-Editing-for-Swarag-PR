# High-resolution editorial export

The original editorial finishing pass created overlays on **every frame** and exceeded CPU limits for long 1080p videos. `scripts/render_editorial_master.py` now renders only the short title windows, uses inexpensive video processing for the remaining spans, concatenates all sections, then **stream-copies the untouched source audio**.

It uses the exact editorial visual language in `scripts/editorial_director.py`; all 42 original effects are unchanged. The renderer automatically checks the video duration and dimensions and refuses to overwrite the source.

## Example

Install FFmpeg/ffprobe, Pillow and the licensed fonts using `python tools/download_assets.py`.

```bash
python scripts/render_editorial_master.py input.mp4 examples/identity-only-story.json review.mp4 --width 1080 --fps 29.5 --crf 21
```

The identity-only example has 2 brief nameplates, with no invented spoken words. **It is a layout example**, not a content-led finished edit. For editorial chapter text, first obtain an accurate word transcript and manually approve it; see `docs/SPEECH_LED_EDITING.md`.

## Acceptance and tests

- Unit tests enforce contiguous segment coverage, unobstructed face zones and layout correctness.
- Video smoke test renders a synthetic 3-second clip with one window at 360×640 and checks for both video and audio streams.
- Compare source and rendered audio-stream hashes; audio is remuxed, not processed.
- Verify every segment join visually at source frame rate, and check frame-accurate lip synchronization.
- Real-footage 60.71-second 1080×1920, 29.5fps identity-only version rendered in the local test workspace with duration drift below 0.01s and matching audio MD5. That **does not** constitute visual signoff or verify a 10-effect native-resolution master.

**Do not commit private media, transcripts or review masters to this public GitHub repository.**
