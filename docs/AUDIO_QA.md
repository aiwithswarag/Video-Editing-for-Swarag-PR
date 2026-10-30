# Dialogue sound quality assessment

Professional editing includes sound. Use source audio as ground truth and **do not alter it by default**.

Run: `python tools/audio_quality_report.py INPUT.mp4 --output private/audio-qa.json`

The report uses FFmpeg `loudnorm` analysis to measure **integrated LUFS**, **true peak (dBTP)** and **loudness range**. It only measures; it does not normalize, limit, compress, enhance or remix. The -16 LUFS / -1.5 dBTP reference is a conversational starting point, **not a universal platform requirement**.

If gain-only boosting exceeds the true-peak ceiling, the proposed gain is flagged as unsafe. Apply EQ, noise reduction or gentle dynamics only after listening on headphones and mobile speakers; remeasure the final master.

Check intelligibility, natural pauses, clipped endings, and any music against the speaker's voice. Keep private audio reports and media outside the public source repository.