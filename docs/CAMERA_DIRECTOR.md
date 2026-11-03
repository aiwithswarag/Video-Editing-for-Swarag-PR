# Camera Director: pause-led editorial reframes

This is an intentionally subtle virtual-camera tool for fixed-camera portrait talking-head content. Instead of flashing UI elements or inventing on-screen quotes, it uses **reviewed pause points** to switch between wide and modestly tighter crops. It does not delete any speech, skip frames, change duration, or add titles.

## Recommended sequence

1. Obtain audio-only timing hints from `python tools/audio_pause_map.py INPUT --output PRIVATE/pauses.json`.
2. Listen and review each proposed cut. Confirm that the framing and gesture remain comfortable at the edit point; never treat silence detection as a transcript.
3. Make a **private** JSON plan with `{"reframes":[{"start":8.1,"end":14.7,"zoom":1.075}]}`, based on a reviewed video. This example is illustrative; the demo in `examples/camera-reframes-demo.json` is wholly synthetic.
4. Apply it after the editorial titles have been created, or use it directly on original footage:

```bash
python scripts/render_directors_cut.py input.mp4 PRIVATE/camera-reframes.json PRIVATE/director_cut.mp4 --crf 22
python tools/master_quality_check.py input.mp4 PRIVATE/director_cut.mp4 --output PRIVATE/qa.json
```

The renderer uses FFmpeg `zoompan` with 1.01–1.14× reframes, requires at least 1.25 seconds per reframe, disallows overlap, and is limited to 12 reframes to avoid frantic cut patterns. Input audio is copied bit-for-bit; there is no speech-based claim. Use the original frame rate, preserving the 9:16 portrait frame. The clean editorial finishing pass can be combined with the 42-effect renderer, but avoid competing type treatments.

## QA evidence and boundaries

A private full 60.71-second 1080×1920, 29.5fps source was exported with **three audio-pause-aligned reframes** at 1.075–1.09×. Technical checks passed: 1,791 frames, an 8-microsecond duration delta and identical source/output AAC MD5. Video decoding returned no errors. A smaller full-length playback copy and 10-frame comparison were created privately.

**Creative status: draft.** These reframes were positioned near *pauses*, not verified semantic chapter changes. The actual transcript was unavailable, and manual frame-by-frame cut approval remains outstanding. This does not constitute a final premium professional sound mix or content-led master. No user's footage or private per-video edit-plan JSON is committed to the public source repository.
