# Speech-led Executive Editing — real wording, actual pauses

**Why:** A professional edit follows the message and speaker's breathing. It does not add invented quotations, empty business slogans, or decorative UI dashboards.

## 1. Find natural timing breaks from the original recording

\`\`\`bash
python tools/audio_pause_map.py input.mp4 --output private/pauses.json --noise-db -34 --min-pause .3
\`\`\`

This runs FFmpeg in **audio-only mode** (no expensive video-frame decoding) and records all silence windows plus proposed cut points. The results are *timing suggestions only*, not a transcript. It never rewrites the source audio and must not be used to claim semantic chapters.

## 2. Make word-level timing available

Install transcription extras explicitly (the default renderer does not silently download ASR models):
\`\`\`bash
python -m pip install -r requirements-transcription.txt
python scripts/words.py input.mp4
\`\`\`

Output schema: \`[{"w":"Spoken", "s":1.23, "e":1.58}, ...]\`. Word timestamps and recognition accuracy need confirmation with the actual audio. Models can download on the first use; the computer needs access to the intended model.

## 3. Produce transcript-grounded draft titles

\`\`\`bash
python tools/transcript_storyboard.py input.words.json --duration 60.71 --output private/editorial-draft.json
python scripts/editorial_director.py input.mp4 private/editorial-draft.json private/review.mp4 --width 540 --fps 15 --seconds 12
\`\`\`

- Every draft headline uses a **contiguous group of actual transcript tokens**. No translation, rewriting, random KPIs, automatic branded claims, or invented paraphrases.
- The output explicitly says **DRAFT / MANUAL REVIEW REQUIRED**. If ASR makes a transcription error, the headline can still be wrong; correct the words/timings first.
- One thought per graphic, moderate spacing (default ≥6.5s), 37-character maximum text length, and short appearance windows. Edit decisions are intentionally conservative.
- Add a user-approved opening or closing identity card only when wanted; keep voice and original performance.

## Creative review, mandatory before publication

Listen to the source and align each excerpt against the speech. Check word accuracy, timing, readability, facial occlusion, breathing space, clean motion endings and loudness. Use only a few face-aware original effects where the underlying statement earns them. Final distribution should include an approved edit-decision list and a reproducible timeline; never publish a raw auto-generated transcript as a verified quotation.

## Privacy

Do not commit personal footage, transcriptions, word-timestamp JSON, silence maps or renders to this **public** GitHub repository. Private outputs belong in a restricted local/output folder. The original media is not uploaded by either analysis tool.
