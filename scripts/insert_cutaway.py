#!/usr/bin/env python3
"""Frame-exact B-roll insertion while copying the original voice track unchanged."""
import argparse
import json
import subprocess
from fractions import Fraction
from pathlib import Path

def probe(path):
    r=subprocess.run(["ffprobe","-v","error","-show_entries",
                      "format=duration:stream=codec_type,width,height,avg_frame_rate,nb_frames",
                      "-of","json",str(path)],capture_output=True,text=True,check=True)
    data=json.loads(r.stdout)
    video=next((s for s in data["streams"] if s.get("codec_type")=="video"),None)
    if video is None or not str(video.get("nb_frames","")).isdigit():
        raise ValueError("Video needs a known frame count")
    return {"width":int(video["width"]),"height":int(video["height"]),
            "fps":Fraction(video["avg_frame_rate"]),"frames":int(video["nb_frames"]),
            "duration":float(data["format"]["duration"]),
            "audio":any(s.get("codec_type")=="audio" for s in data["streams"])}

def validate(source,cutaway,start_frame):
    if (source["width"],source["height"])!=(cutaway["width"],cutaway["height"]):
        raise ValueError("Cutaway dimensions must match source")
    if source["fps"]!=cutaway["fps"]:
        raise ValueError("Cutaway frame rate must match source exactly")
    if not isinstance(start_frame,int) or start_frame<1:
        raise ValueError("Invalid start frame")
    end=start_frame+cutaway["frames"]
    if end>=source["frames"]:
        raise ValueError("Cutaway exceeds input frame count")
    if not source["audio"]:
        raise ValueError("Original voice track required")
    return end

def insert(source,cutaway,output,start_frame,crf=19):
    source,cutaway,output=[Path(p).resolve() for p in (source,cutaway,output)]
    if not source.is_file() or not cutaway.is_file() or output in (source,cutaway):
        raise ValueError("Invalid input or output")
    if output.suffix.lower()!=".mp4" or not 0<=crf<=35:
        raise ValueError("Invalid output settings")
    a,b=probe(source),probe(cutaway)
    end=validate(a,b,start_frame)
    filt=(f"[0:v]split=2[x][y];"
          f"[x]trim=start_frame=0:end_frame={start_frame},setpts=PTS-STARTPTS,setsar=1[before];"
          f"[1:v]trim=start_frame=0:end_frame={b['frames']},setpts=PTS-STARTPTS,setsar=1[graphic];"
          f"[y]trim=start_frame={end}:end_frame={a['frames']},setpts=PTS-STARTPTS,setsar=1[after];"
          f"[before][graphic][after]concat=n=3:v=1:a=0,format=yuv420p[out]")
    output.parent.mkdir(parents=True,exist_ok=True)
    fps=f"{a['fps'].numerator}/{a['fps'].denominator}"
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(source),"-i",str(cutaway),
         "-filter_complex",filt,"-map","[out]","-map","0:a:0","-c:v","libx264",
         "-preset","ultrafast","-crf",str(crf),"-r",fps,
         "-frames:v",str(a["frames"]),"-c:a","copy","-movflags","+faststart",str(output)]
    subprocess.run(cmd,check=True)
    meta=probe(output)
    if meta["frames"]!=a["frames"] or abs(meta["duration"]-a["duration"])>.05:
        raise RuntimeError("Frame or duration regression")
    return {"source_frames":a["frames"],"output_frames":meta["frames"],
            "insert_start_frame":start_frame,"insert_end_frame_exclusive":end,
            "source_audio":"stream copied","creative_status":"DRAFT — check cutaway and story"}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("cutaway",type=Path)
    p.add_argument("output",type=Path);p.add_argument("--at-frame",type=int,required=True)
    p.add_argument("--crf",type=int,default=19)
    a=p.parse_args()
    print(json.dumps(insert(a.source,a.cutaway,a.output,a.at_frame,a.crf),indent=2))
if __name__=="__main__":main()
