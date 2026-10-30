#!/usr/bin/env python3
"""Combine multiple B-roll videos at integer frame windows, copying original audio."""
import argparse,json,subprocess
from fractions import Fraction
from pathlib import Path

def probe(video):
    r=subprocess.run(["ffprobe","-v","error","-show_entries",
        "format=duration:stream=codec_type,width,height,nb_frames,avg_frame_rate",
        "-of","json",str(video)],capture_output=True,text=True,check=True)
    data=json.loads(r.stdout)
    videos=[s for s in data["streams"] if s.get("codec_type")=="video"]
    if len(videos)!=1 or not str(videos[0].get("nb_frames","")).isdigit():
        raise ValueError("One video with known frame count required")
    s=videos[0]
    return {"width":int(s["width"]),"height":int(s["height"]),
        "fps":Fraction(s["avg_frame_rate"]),"frames":int(s["nb_frames"]),
        "duration":float(data["format"]["duration"]),
        "audio":any(x.get("codec_type")=="audio" for x in data["streams"])}

def validate(source,windows):
    if not source["audio"]:raise ValueError("Original audio track required")
    if not isinstance(windows,list) or not 1<=len(windows)<=12:
        raise ValueError("Expected 1-12 B-roll windows")
    last=0
    for i,(item,clip) in enumerate(windows):
        start=item.get("start_frame")
        if not isinstance(start,int) or isinstance(start,bool) or start<1 or start<last:
            raise ValueError("Cutaway windows must be sorted, integer and nonoverlapping")
        if (source["width"],source["height"])!=(clip["width"],clip["height"]):
            raise ValueError(f"Resolution mismatch on window {i}")
        if source["fps"]!=clip["fps"]:
            raise ValueError(f"FPS mismatch on window {i}")
        last=start+clip["frames"]
        if clip["frames"]<=0 or last>=source["frames"]:
            raise ValueError(f"Window {i} exceeds available video")
    return last

def build_filter(total,windows):
    n=len(windows)
    split="".join(f"[s{i}]" for i in range(n+1))
    filters=[f"[0:v]split={n+1}{split}"]
    parts=[];cursor=0
    for i,(item,clip) in enumerate(windows):
        start=item["start_frame"];end=start+clip["frames"]
        filters.append(f"[s{i}]trim=start_frame={cursor}:end_frame={start},setpts=PTS-STARTPTS,setsar=1[g{i}]")
        filters.append(f"[{i+1}:v]trim=start_frame=0:end_frame={clip['frames']},setpts=PTS-STARTPTS,setsar=1[c{i}]")
        parts.extend([f"[g{i}]",f"[c{i}]"])
        cursor=end
    filters.append(f"[s{n}]trim=start_frame={cursor}:end_frame={total},setpts=PTS-STARTPTS,setsar=1[tail]")
    parts.append("[tail]")
    filters.append("".join(parts)+f"concat=n={2*n+1}:v=1:a=0,format=yuv420p[v]")
    return ";".join(filters)

def insert(source,plan,output,crf=19):
    source=Path(source).resolve();output=Path(output).resolve()
    if not source.is_file() or source==output or output.suffix.lower()!=".mp4" or not 0<=crf<=35:
        raise ValueError("Invalid source/output/CRF")
    data=json.loads(Path(plan).read_text("utf8"))
    items=data.get("windows") if isinstance(data,dict) else None
    if not isinstance(items,list):raise ValueError("Missing windows")
    files=[];windows=[]
    for item in items:
        if not isinstance(item,dict) or "clip" not in item:raise ValueError("Missing clip name")
        clip=Path(item["clip"])
        if not clip.is_absolute():clip=Path(plan).resolve().parent/clip
        clip=clip.resolve()
        if not clip.is_file() or clip in (source,output):raise ValueError("Invalid clip")
        files.append(clip);windows.append((item,probe(clip)))
    original=probe(source)
    validate(original,windows)
    fps=f'{original["fps"].numerator}/{original["fps"].denominator}'
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(source)]
    for clip in files:cmd.extend(["-i",str(clip)])
    cmd+=["-filter_complex",build_filter(original["frames"],windows),"-map","[v]",
          "-map","0:a:0","-c:v","libx264","-preset","ultrafast","-crf",str(crf),
          "-r",fps,"-frames:v",str(original["frames"]),
          "-c:a","copy","-movflags","+faststart",str(output)]
    output.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(cmd,check=True)
    result=probe(output)
    if result["frames"]!=original["frames"] or abs(result["duration"]-original["duration"])>.05:
        raise RuntimeError("Frame or duration QA failed")
    return {"frames":result["frames"],"cutaways":len(windows),
            "audio_policy":"source bitstream copied",
            "creative_status":"DRAFT — human source and timeline approval required"}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("plan",type=Path);p.add_argument("output",type=Path)
    p.add_argument("--crf",type=int,default=19)
    a=p.parse_args()
    print(json.dumps(insert(a.source,a.plan,a.output,a.crf),indent=2))
if __name__=="__main__":main()
