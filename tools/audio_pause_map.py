#!/usr/bin/env python3
"""Audio-only pause detection for precise edit timing; no transcript claims."""
import argparse
import json
import math
import re
import subprocess
from pathlib import Path

START=re.compile(r"silence_start:\s*([0-9.]+)")
END=re.compile(r"silence_end:\s*([0-9.]+)")

def read_pauses(log, duration, min_pause=0.30):
    """Parse FFmpeg silencedetect output, including an unfinished trailing silence."""
    if not math.isfinite(duration) or duration<=0:raise ValueError("Invalid media duration")
    items=[]
    begin=None
    for line in log.splitlines():
        s=START.search(line)
        e=END.search(line)
        if s:begin=float(s.group(1))
        if e and begin is not None:
            stop=min(float(e.group(1)),duration)
            if 0<=begin<stop and stop-begin>=min_pause-1e-5:
                items.append({"start":round(begin,3),"end":round(stop,3),
                              "duration":round(stop-begin,3),"cut_at":round((begin+stop)/2,3)})
            begin=None
    if begin is not None and begin<duration and duration-begin>=min_pause-1e-5:
        items.append({"start":round(begin,3),"end":round(duration,3),
                      "duration":round(duration-begin,3),"cut_at":round((begin+duration)/2,3)})
    return items

def select_boundaries(pauses,duration,minimum_gap=4.0,min_strength=0.50):
    """Select strong, spaced pauses; never confuse a pause with a semantic cut."""
    proposed=[p for p in pauses if p["duration"]>=min_strength
              and p["start"]>=1.0 and p["end"]<=duration-1.0]
    chosen=[]
    for pause in sorted(proposed,key=lambda p:(-p["duration"],p["start"])):
        if all(abs(pause["cut_at"]-q["cut_at"])>=minimum_gap for q in chosen):
            chosen.append(pause)
    return sorted(chosen,key=lambda p:p["cut_at"])

def probe_duration(video):
    result=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                           "-of","default=noprint_wrappers=1:nokey=1",str(video)],
                           capture_output=True,text=True,check=True)
    return float(result.stdout.strip())

def analyze(video,threshold_db=-34,min_pause=.30,minimum_gap=4.0):
    if not video.is_file():raise FileNotFoundError(video)
    if not (-90<=threshold_db<=-10):raise ValueError("Threshold must be -90 to -10 dB")
    if not (.1<=min_pause<=3):raise ValueError("Minimum pause must be 0.1 to 3 seconds")
    if minimum_gap<1:raise ValueError("Minimum edit spacing must exceed one second")
    duration=probe_duration(video)
    cmd=["ffmpeg","-hide_banner","-nostats","-i",str(video),"-vn",
         "-af",f"silencedetect=noise={threshold_db}dB:d={min_pause}","-f","null","-"]
    result=subprocess.run(cmd,text=True,capture_output=True,check=True)
    silences=read_pauses(result.stderr,duration,min_pause)
    transitions=select_boundaries(silences,duration,minimum_gap)
    return {"schema_version":1,"kind":"audio_pause_map","source_media":video.name,
            "duration":round(duration,3),"threshold_db":threshold_db,
            "minimum_pause_s":min_pause,"pauses":silences,
            "suggested_transitions":[{"at":p["cut_at"],"pause":p,"type":"timing_candidate"} for p in transitions],
            "warning":"Pauses indicate potential edit points only. They do NOT identify spoken words, scene changes, or semantic chapter boundaries. Manual review required."}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("video",type=Path)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--noise-db",type=float,default=-34)
    p.add_argument("--min-pause",type=float,default=.30)
    p.add_argument("--min-gap",type=float,default=4.)
    a=p.parse_args()
    report=analyze(a.video,a.noise_db,a.min_pause,a.min_gap)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print(f"Detected {len(report['pauses'])} pauses; proposed {len(report['suggested_transitions'])} timing candidates: {a.output}")
if __name__=="__main__":main()
