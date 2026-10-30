#!/usr/bin/env python3
"""Objective visual red flags from ACTUAL finished MP4 (not aesthetic certification).

Detects blown-out blank/fade frames at opening and abrupt luminance collapses.
These warnings require real video review and cannot prove good composition.
"""
from __future__ import annotations
import argparse
import json
import math
import subprocess
from pathlib import Path
import numpy as np

def inspect_luma(path,seconds=2.5,sample_fps=8):
    if not Path(path).is_file():raise FileNotFoundError(path)
    if not 0<seconds<=10:raise ValueError("Sample only the opening 0..10 seconds")
    if not 1<=sample_fps<=30:raise ValueError("Sampling rate out of range")
    w,h=72,128
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-nostdin",
         "-i",str(path),"-t",str(seconds),"-an",
         "-vf",f"fps={sample_fps},scale={w}:{h}:flags=area,format=gray",
         "-f","rawvideo","-pix_fmt","gray","-"]
    raw=subprocess.run(cmd,check=True,capture_output=True).stdout
    if len(raw)<w*h or len(raw)%(w*h):
        raise RuntimeError("No complete review frames returned by FFmpeg")
    frames=np.frombuffer(raw,dtype=np.uint8).reshape(-1,h,w)
    mean=frames.mean(axis=(1,2))
    white=(frames>=245).mean(axis=(1,2))
    return [{"time_s":round(i/sample_fps,3),
             "mean_luma":round(float(mean[i]),2),
             "near_white_fraction":round(float(white[i]),3)}
            for i in range(len(frames))]


def find_issues(samples):
    if not samples:return ["Unable to sample actual rendered opening"]
    issues=[]
    first=samples[0]
    after=[p for p in samples if 1.0<=p["time_s"]<=2.2]
    if after:
        base=min(p["mean_luma"] for p in after)
        if first["mean_luma"]>225 and first["mean_luma"]-base>55:
            issues.append({
                "code":"POSSIBLE_WASHED_OUT_OPENING",
                "severity":"REQUIRES_CREATIVE_REVIEW",
                "description":"Opening image is dramatically brighter than the steady shot; inspect for white/washed-out intro frames",
                "opening_luma":first["mean_luma"],
                "later_luma_min":base,
                "note":"May be deliberate fade; cannot certify fault without watching the footage"
            })
    return issues


def analyze(path):
    samples=inspect_luma(path)
    return {"source":Path(path).name,"analysis":"objective opening-frame sample only",
            "samples":samples,"flags":find_issues(samples),
            "status":"REVIEW_REQUIRED" if find_issues(samples) else "NO_AUTOMATIC_OPENING_FLAG",
            "caveat":"No automated brightness score establishes visual professionalism; full motion and human approval required"}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("video",type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    result=analyze(args.video)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf8")
    print(result["status"],*([x["code"] for x in result["flags"]] or ["no detected opening warnings"]))

if __name__=="__main__":main()
