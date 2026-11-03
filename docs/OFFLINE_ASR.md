# Private offline transcription — Swarag Video Director

This provides local English transcription with experimental word timestamps. **No personal video or audio is uploaded to GitHub Actions or external ASR services.** Only the public whisper.cpp executable and base.en model are built/downloaded via GitHub Actions; the resulting portable bundle is downloaded to the private computer where the source media lives.

## Prepare the model and CPU executable

Run the `Build private offline ASR runtime` GitHub workflow on a trusted branch. Download the `whisper-cpp-base-en-cpu` artifact and extract it into a private, restricted directory. It contains the pinned CPU binary, `models/ggml-base.en.bin`, SHA-256 checksum, and upstream licence notices. The binary is built from pinned whisper.cpp commit `284029c07012d2000941a08d38a31ffb71f4734e`. A Linux x86_64 build is supplied by this workflow; other platforms must build a compatible executable locally.

The model is English-only and the timestamps are **experimental**. Before trusting downloaded code or weights, inspect its origin, SHA-256 and licences. Do not place the user's video in the public repo or CI.

## Run privately

```bash
python tools/transcribe_offline.py INPUT.mp4 --binary PRIVATE/offline-asr/whisper-cli --model PRIVATE/offline-asr/models/ggml-base.en.bin --output PRIVATE/draft-words.json
python tools/transcript_storyboard.py PRIVATE/draft-words.json --duration 60.71 --output PRIVATE/draft-storyboard.json
```

Output contains *unverified* timestamped source phrases (`{"words":[{"w":"example","s":1.23,"e":1.55}]}`) and cannot automatically become approved quotes or research claims. Review the source audio word by word and correct omissions, hallucinations and ambiguous pronunciation. Verify any external research claims against primary sources.

## Actual private acceptance evidence

The model was built in GitHub Actions **without personal media**. On a private 60.71-second 1080x1920 English-language video, offline inference produced approximately 146 timed words and 13 draft sentences. The transcript revealed the subject as **AI world models and robotic task reliability**, allowing a six-cue content-led preview. Human word-level listening signoff remains outstanding; one opening phrase was flagged as potentially inaccurate.

Do not commit the private transcript, video, temporary WAV, model binary or generated review assets to this public repo. The model/runtime is obtained through its separate GitHub artifact, not stored in Git history.
