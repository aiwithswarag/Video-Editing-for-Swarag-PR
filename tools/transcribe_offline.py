#!/usr/bin/env python3
"""Offline private English transcription with experimental word timestamps (whisper.cpp).

Model, CLI and user video stay on the local machine. ASR output requires manual review.
"""
import argparse
import json
import math
import re
import subprocess
import tempfile
from pathlib import Path

TIME=re.compile(r"(?:(\d+):)?(\d+):(\d+)[.,](\d+)$")
SPECIAL=re.compile(r"^(<\|[^>]+\|>|\[_.*_\]|\[SPEAKER_TURN\])$")

def timestamp(text):
    m=TIME.fullmatch(str(text).strip())
    if not m:raise ValueError("Invalid time string")
    h,mi,s,f=m.groups()
    return int(h or 0)*3600+int(mi)*60+int(s)+int(f)/10**len(f)

def span(data):
    off=data.get("offsets")
    if isinstance(off,dict) and "from" in off and "to" in off:
        return float(off["from"])/1000.,float(off["to"])/1000.
    stamp=data.get("timestamps")
    if isinstance(stamp,dict) and "from" in stamp and "to" in stamp:
        return timestamp(stamp["from"]),timestamp(stamp["to"])
    raise ValueError("No source time offsets")

def normalize(raw,duration):
    if not math.isfinite(duration) or duration<=0:raise ValueError("Invalid duration")
    segments=raw.get("transcription") if isinstance(raw,dict) else None
    if not isinstance(segments,list):raise ValueError("Whisper full JSON has no transcription")
    words=[];flags=[];last=0.
    for i,seg in enumerate(segments):
        if not isinstance(seg,dict):continue
        text=str(seg.get("text","")).strip()
        if not text or SPECIAL.fullmatch(text):continue
        candidates=[seg]
        if len(text.split())>1:
            candidates=seg.get("tokens",[])
            if not isinstance(candidates,list) or not candidates:
                flags.append({"segment":i,"reason":"No independent word boundaries"})
                continue
        for item in candidates:
            t=str(item.get("text","")).strip()
            if not t or SPECIAL.fullmatch(t):continue
            if len(t.split())>1:
                flags.append({"segment":i,"reason":"Multiword token not word-aligned"})
                continue
            try:s,e=span(item)
            except (TypeError,ValueError):
                flags.append({"segment":i,"reason":"Missing timestamps"})
                continue
            if not math.isfinite(s) or not math.isfinite(e) or s<0 or e<s or e>duration+.05:
                flags.append({"segment":i,"reason":"Invalid timestamps"})
                continue
            # A few Whisper word tokens have zero duration. Use the enclosing
            # segment span when valid; never estimate from a sentence.
            if e==s and item is not seg:
                try:s,e=span(seg)
                except (ValueError,TypeError):pass
            if e<=s:
                flags.append({"segment":i,"reason":"Zero-duration token"})
                continue
            if words and s<last-.10:
                flags.append({"segment":i,"reason":"Nonmonotonic word"})
                continue
            if words and re.fullmatch(r"[,.;:!?]+",t):
                words[-1]["w"]+=t
                words[-1]["e"]=round(e,3)
            else:
                words.append({"w":t,"s":round(max(s,last-.03),3),"e":round(e,3)})
            last=max(last,e)
    if len(words)<4:raise ValueError("No trustworthy word-aligned transcript")
    return {"schema_version":1,"kind":"private_asr_word_draft",
            "transcript_verified":False,"word_timestamps_experimental":True,
            "engine":"whisper.cpp base.en CPU","language":"en",
            "word_count":len(words),"words":words,"review_flags":flags,
            "status":"DRAFT — manually check transcript and word timings before publication"}

def probe_duration(path):
    r=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                      "-of","default=nw=1:nk=1",str(path)],text=True,
                     capture_output=True,check=True)
    return float(r.stdout.strip())

def transcribe(video,binary,model,output,threads=4):
    video=Path(video).resolve();binary=Path(binary).resolve()
    model=Path(model).resolve();output=Path(output).resolve()
    if not all(x.is_file() for x in (video,binary,model)):
        raise FileNotFoundError("Missing video, offline whisper-cli or model")
    if output==video or output.suffix.lower()!=".json" or not 1<=threads<=16:
        raise ValueError("Invalid output or thread count")
    duration=probe_duration(video)
    with tempfile.TemporaryDirectory(prefix="private_whisper_") as tmp:
        wav=Path(tmp)/"audio.wav"
        stem=Path(tmp)/"asr"
        subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",
                        "-i",str(video),"-map","0:a:0","-ac","1","-ar","16000",
                        "-c:a","pcm_s16le",str(wav)],check=True)
        subprocess.run([str(binary),"-m",str(model),"-f",str(wav),"-l","en",
                        "-t",str(threads),"-ml","1","-sow","-ojf",
                        "-of",str(stem)],check=True)
        raw=json.loads(Path(str(stem)+".json").read_text(encoding="utf8"))
        report=normalize(raw,duration)
    report["duration"]=round(duration,6)
    report["source_filename"]=video.name
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("video",type=Path)
    p.add_argument("--binary",type=Path,required=True)
    p.add_argument("--model",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--threads",type=int,default=4)
    a=p.parse_args()
    result=transcribe(a.video,a.binary,a.model,a.output,a.threads)
    print(f"Generated {result['word_count']} word-timestamp drafts. MANUAL REVIEW REQUIRED.")
if __name__=="__main__":main()
