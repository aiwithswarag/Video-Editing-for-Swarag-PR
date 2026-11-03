#!/usr/bin/env python3
"""Render every effect individually and generate machine-readable QA artifacts."""
import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / "tools"))
from effect_catalog import read_registry
from effect_media_qc import preview_evidence, motion_evidence

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
    ap.add_argument("--only",action="append",default=[],
       help="LIMITED developer test subset only. Omit this option for 42-effect certification.")
    args=ap.parse_args()
    if args.shards<1 or not 0<=args.shard<args.shards:
        ap.error("Invalid shard or shard count")
    out=Path(args.output_dir);out.mkdir(parents=True,exist_ok=True)
    stream_probe=subprocess.run(["ffprobe","-v","error","-select_streams","v:0",
          "-show_entries","stream=width,height","-of","json",args.video],
          capture_output=True,text=True,check=True,timeout=40)
    streams=json.loads(stream_probe.stdout).get("streams",[])
    if len(streams)!=1:
        raise ValueError("Source must contain one readable video stream")
    sw,sh=int(streams[0]["width"]),int(streams[0]["height"])
    if sw<=0 or sh<=0 or sw>sh:
        raise ValueError("Effect verification requires portrait source video")
    expected_preview_h=round(args.width*sh/sw/2)*2
    expected_motion_h=round(240*sh/sw/2)*2
    # A real decoded source-frame baseline allows us to distinguish "the
    # renderer returned a PNG" from "there was any observable change".
    # Low differences are evidence for manual review, never fabricated PASS.
    baseline_tmp=tempfile.TemporaryDirectory(prefix="swarag_effect_baseline_")
    baseline=Path(baseline_tmp.name)/"unedited_source_baseline.png"
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin",
           "-y","-ss",str(args.at),"-i",args.video,
           "-vf",f"scale={args.width}:{expected_preview_h}",
           "-frames:v","1",str(baseline)],check=True,timeout=60)
    names, _, _=read_registry()
    tasks=[(name,name,{}) for name in names]
    if args.include_variants: tasks+=NAMED_VARIANTS
    if args.only:
        selected=set(args.only)
        if not selected<=set(label for label,_,_ in tasks):
            ap.error("Unknown effect label in --only; cannot claim catalog coverage")
        tasks=[task for task in tasks if task[0] in selected]
        print("LIMITED TEST SUBSET ONLY — NOT a 42/42 certification",flush=True)
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
        preview_qc=None
        motion_qc=None
        try:
            p=subprocess.run(command,capture_output=True,text=True,timeout=args.timeout)
            ok=p.returncode==0 and image.exists() and image.stat().st_size>1000
            message=(p.stdout+"\n"+p.stderr)[-5000:]
            if ok:
                preview_qc=preview_evidence(image,args.width,expected_preview_h,baseline)
            if ok and args.render_motion:
                motion=out/(label+".mp4")
                video_command=[sys.executable,str(ROOT/"scripts/video_director.py"),"render",
                               args.video,str(plan),str(motion),"--width","240","--brand",str(args.brand)]
                q=subprocess.run(video_command,capture_output=True,text=True,timeout=args.timeout)
                ok=q.returncode==0 and motion.exists() and motion.stat().st_size>1000
                if ok:
                    motion_qc=motion_evidence(motion,240,expected_motion_h,min_frames=10)
                if not ok:
                    message=(q.stdout+"\n"+q.stderr)[-5000:]+"\nMotion render failed"
        except (subprocess.TimeoutExpired,subprocess.CalledProcessError,
                ValueError,OSError,KeyError) as exc:
            ok=False;message=type(exc).__name__+": "+str(exc)[-3500:]
        statuses.append({"effect":label,"ok":ok,"preview":image.name if ok else None,
                         "motion":motion.name if args.render_motion and ok else None,
                         "elapsed_seconds":round(time.monotonic()-start,2),
                         "media_qc":motion_qc,
                         "preview_qc":preview_qc,
                         "creative_status":"REVIEW REQUIRED — technical smoke is not professional approval",
                         "log":message if not ok else ""})
        print(f"{'PASS' if ok else 'FAIL'} {label} ({statuses[-1]['elapsed_seconds']}s)",flush=True)
    (out/"results.json").write_text(json.dumps(statuses,indent=2),encoding="utf8")
    failed=[s for s in statuses if not s["ok"]]
    baseline_tmp.cleanup()
    print(f"Results: {len(statuses)-len(failed)}/{len(statuses)} passed")
    if failed:
        for f in failed: print("ERROR",f["effect"],f["log"][-1200:],file=sys.stderr)
        sys.exit(1)
if __name__=="__main__":
    main()
