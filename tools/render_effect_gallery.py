#!/usr/bin/env python3
"""Render every effect individually and generate machine-readable QA artifacts."""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / "tools"))
from effect_catalog import read_registry

NAMED_VARIANTS = [
    ("glitter-spotlight", "glitter-spotlight", {}),
    ("cover-star-editorial", "cover-star", {"look":"editorial"}),
    ("liquid-glass-graph-bento", "liquid-glass-graph", {"look":"bento"}),
    ("glass-widgets-simple", "glass-widgets", {"look":"simple"}),
    ("apple-toggles-below", "apple-toggles", {"pos":"below"})
]

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--video",required=True)
    ap.add_argument("--output-dir",default="gallery")
    ap.add_argument("--shard",type=int,default=0)
    ap.add_argument("--shards",type=int,default=1)
    ap.add_argument("--width",type=int,default=360)
    ap.add_argument("--at",type=float,default=0.95)
    ap.add_argument("--timeout",type=int,default=180)
    ap.add_argument("--brand",choices=["none","executive"],default="none")
    ap.add_argument("--include-variants",action="store_true")
    ap.add_argument("--render-motion",action="store_true",help="Also render MP4 clips")
    args=ap.parse_args()
    if args.shards<1 or not 0<=args.shard<args.shards:
        ap.error("Invalid shard or shard count")
    out=Path(args.output_dir);out.mkdir(parents=True,exist_ok=True)
    names, _, _=read_registry()
    tasks=[(name,name,{}) for name in names]
    if args.include_variants: tasks+=NAMED_VARIANTS
    assigned=[task for idx,task in enumerate(tasks) if idx % args.shards==args.shard]
    statuses=[]
    for label,fx,options in assigned:
        plan=out / (label+".json")
        image=out / (label+".png")
        plan.write_text(json.dumps({"effects":[{"fx":fx,"start":0.0,"end":1.7,**options}]}),encoding="utf8")
        command=[sys.executable,str(ROOT/"scripts/video_director.py"),"preview",
                 args.video,str(plan),str(image),"--at",str(args.at),"--width",str(args.width),"--brand",str(args.brand)]
        start=time.monotonic()
        motion=None
        try:
            p=subprocess.run(command,capture_output=True,text=True,timeout=args.timeout)
            ok=p.returncode==0 and image.exists() and image.stat().st_size>1000
            message=(p.stdout+"\n"+p.stderr)[-5000:]
            if ok and args.render_motion:
                motion=out/(label+".mp4")
                video_command=[sys.executable,str(ROOT/"scripts/video_director.py"),"render",
                               args.video,str(plan),str(motion),"--width","240","--brand",str(args.brand)]
                q=subprocess.run(video_command,capture_output=True,text=True,timeout=args.timeout)
                ok=q.returncode==0 and motion.exists() and motion.stat().st_size>1000
                if ok:
                    probe=subprocess.run(["ffprobe","-v","error","-show_entries","stream=codec_type",
                                          "-of","csv=p=0",str(motion)],capture_output=True,text=True)
                    ok=probe.returncode==0 and "video" in probe.stdout and "audio" in probe.stdout
                if not ok:
                    message=(q.stdout+"\n"+q.stderr)[-5000:]+"\nMotion render or A/V verification failed"
        except subprocess.TimeoutExpired:
            ok=False;message="Timed out"
        statuses.append({"effect":label,"ok":ok,"preview":image.name if ok else None,
                         "motion":motion.name if args.render_motion and ok else None,
                         "elapsed_seconds":round(time.monotonic()-start,2),
                         "log":message if not ok else ""})
        print(f"{'PASS' if ok else 'FAIL'} {label} ({statuses[-1]['elapsed_seconds']}s)",flush=True)
    (out/"results.json").write_text(json.dumps(statuses,indent=2),encoding="utf8")
    failed=[s for s in statuses if not s["ok"]]
    print(f"Results: {len(statuses)-len(failed)}/{len(statuses)} passed")
    if failed:
        for f in failed: print("ERROR",f["effect"],f["log"][-1200:],file=sys.stderr)
        sys.exit(1)
if __name__=="__main__":
    main()
