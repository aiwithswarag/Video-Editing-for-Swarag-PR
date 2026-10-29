# Executive Editorial V2 — Art direction

**Purpose.** Replace conspicuous template effects with a coherent visual language based on one carefully composed frame, not 42 effects stacked together. Built as an optional finishing pass: all 42 legacy engine effects remain untouched.

## Design rules
- One idea per shot. Preserve facial expression, hand gestures and the natural background as the focal point.
- Use the wall's clean top 8–21% for editorial titles and the dark shirt's 78–87% zone for concise lower-thirds; never cover the eyes.
- Instrument Serif Italic for a single editorial headline; Inter for chapter markers, names and detail. Strong hierarchy, consistent baseline and approximately 8% safe margins.
- Palette is ink #121B26, warm ivory #F2EFE9, antique gold #B79660. No neon, glow, gimmicky app widgets or fake analytics.
- Use restrained 0.45-second fades and eight-pixel movement at 540×960; no bounce, spin or unmotivated movement.
- Light neutral grade that preserves skin tone. Original dialogue and duration are retained in the preview.
- Words in `examples/editorial-storyboard.json` are **example editorial labels, not spoken quotes**. Before final publication, review the actual transcript and adapt copy to the speaker's topic.

## Run
Install FFmpeg, Pillow, and the original fonts via `python tools/download_assets.py`.
```bash
python scripts/editorial_director.py input.mp4 examples/editorial-storyboard.json style-preview.mp4 --seconds 12 --width 540 --fps 15
```
For a native-resolution test: `--width 1080 --fps 30 --seconds 3`. Keep the original input private.

## 42-effect integration
Render the selected advanced effects using `scripts/render_chunks.py`, then pass that MP4 into `scripts/editorial_director.py` to apply typography and editorial branding. Do not reapply a brand label if the advanced timeline already creates one. Distinguish tested preview settings from final production settings.

## Approval gates
- Review a contact sheet at the start, peak and fade of each graphic. Check no overlap with head or safe-area UI.
- Confirm exact frame rate, H.264/AAC output, speech synchronization and readability on a mobile device.
- Review manual selections of the 42 effects separately. The 47/47 synthetic passing test only establishes functional completeness.
- Do not assert that the demonstration headings match the transcript, or that a synthetic preview is a production master.