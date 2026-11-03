#!/usr/bin/env python3
"""Measure dialogue loudness and true peak with FFmpeg, without changing audio."""
import argparse
import json
import math
import re
import subprocess
from pathlib import Path

MEASUREMENT=re.compile(r'\{\s*"input_i"\s*:.*?\}',re.DOTALL)

def parse_loudnorm_log(log):
    matches=MEASUREMENT.findall(log)
    if not matches:raise ValueError("FFmpeg did not emit loudness measurements")
    obj=json.loads(matches[-1])
    fields={"integrated_lufs":"input_i","true_peak_dbtp":"input_tp",
            "loudness_range_lu":"input_lra","measured_threshold_lufs":"input_thresh"}
    out={}
    for new,key in fields.items():
        x=float(obj[key])
        if not math.isfinite(x):raise ValueError("Nonfinite audio measurement")
        out[new]=round(x,2)
    return out

def analyze(video,target=-16.,ceiling=-1.5):
    if not video.is_file():raise FileNotFoundError(video)
    if not -30<=target<=-10 or not -6<=ceiling<=-0.5:
        raise ValueError("Unsupported review targets")
    filt=f"loudnorm=I={target}:TP={ceiling}:LRA=11:print_format=json"
    p=subprocess.run(["ffmpeg","-hide_banner","-nostats","-i",str(video),
                      "-vn","-af",filt,"-f","null","-"],
                     capture_output=True,text=True,check=True)
    data=parse_loudnorm_log(p.stderr)
    need=round(target-data["integrated_lufs"],2)
    return {"schema_version":1,"kind":"dialogue_audio_qa","source_media":video.name,
            **data,"reference_target_lufs":target,"reference_true_peak_ceiling_dbtp":ceiling,
            "gain_change_to_target_db":need,
            "safe_to_apply_gain_only":bool(need<=0 or data["true_peak_dbtp"]+need<=ceiling),
            "source_preserved":True,
            "note":"Measurements only. No audio is changed. Integrated LUFS is not a measure of noise, EQ, intelligibility or clipping. Gain-only boosting may exceed true-peak ceiling; any normalization or dynamics require a listened-to render and user-approved master."}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("video",type=Path)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--target",type=float,default=-16)
    p.add_argument("--true-peak",type=float,default=-1.5)
    a=p.parse_args()
    result=analyze(a.video,a.target,a.true_peak)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print(f"Dialogue loudness {result['integrated_lufs']} LUFS, TP {result['true_peak_dbtp']} dBTP; no audio modified")
if __name__=="__main__":main()
