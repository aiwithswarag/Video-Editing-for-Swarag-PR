# Dialogue mastering (opt-in, fully reviewed)

The `tools/audio_quality_report.py` utility *only measures* the recording. For a separate A/B **review variant**, use `tools/two_pass_dialogue_master.py` to normalize the voice with EBU R128 loudness targeting. It uses two passes (first measure, then apply) and measures the output again. **Original audio and original video remain untouched.**

```bash
python tools/two_pass_dialogue_master.py PRIVATE/director_cut.mp4 PRIVATE/director_cut_mastered_review.mp4 --lufs -18 --true-peak -1.9 --report PRIVATE/mastered-audio-qa.json
python tools/master_quality_check.py PRIVATE/director_cut.mp4 PRIVATE/director_cut_mastered_review.mp4 --allow-audio-remaster --output PRIVATE/technical-qa.json
```

Audio alone is re-encoded at AAC 160kbps/48kHz; video is stream-copied unchanged. Defaults are conservative **review targets**, not universally mandated platform requirements. FFmpeg's final measured true peak may differ slightly after AAC encoding; the script permits ≤0.12 dBTP measurement tolerance around the requested target and ±0.65 LUFS.

On a private spoken-word sample, the 60.71-second source measured **-20.68 LUFS / -2.02 dBTP**. A separate two-pass test rendered approximately **-18.13 LUFS / -1.83 dBTP**, with identical source video frames. These measurements do not certify sound quality, noise management, EQ, de-essing, intelligibility or musicality. The original-audio cut is retained for A/B comparison.

**Mandatory creative QA:** listen to voice breaths, sibilance and consonants on headphones and speakers; use independent reviews, not only numerical loudness measures. Never overwrite the source. Never silently apply mastering to user media. Keep private edits outside the public repository.
