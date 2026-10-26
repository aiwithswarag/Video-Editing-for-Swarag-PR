#!/usr/bin/env python3
"""Word-level timestamps with explicitly installed faster-whisper."""
import argparse,json
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("--model",default="base")
    a=p.parse_args()
    try: from faster_whisper import WhisperModel
    except ImportError as exc: raise SystemExit("Run pip install -r requirements-transcription.txt first") from exc
    engine=WhisperModel(a.model,device="cpu",compute_type="int8")
    segments,_=engine.transcribe(a.video,word_timestamps=True,vad_filter=True)
    words=[{"w":word.word.strip(),"s":round(word.start,2),"e":round(word.end,2)} for segment in segments for word in (segment.words or [])]
    output=Path(a.video).with_suffix(".words.json")
    output.write_text(json.dumps(words,indent=2),encoding="utf8")
    print(f"Saved {len(words)} words to {output}")
if __name__=="__main__":main()
