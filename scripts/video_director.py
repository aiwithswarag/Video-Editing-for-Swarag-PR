#!/usr/bin/env python3
"""Swarag Video Director: 42 original effects, brand-aware plan validation and rendering."""
import argparse,json,math,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from plan_validation import validate_plan, AVAILABLE_EFFECTS
from brand_presets import apply_brand

def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest="cmd",required=True)
    sub.add_parser("list")
    check=sub.add_parser("validate")
    check.add_argument("plan");check.add_argument("--duration",type=float)
    for cmd in ("preview","render"):
        x=sub.add_parser(cmd)
        x.add_argument("input");x.add_argument("plan");x.add_argument("output")
        x.add_argument("--width",type=int,default=1080)
        x.add_argument("--brand",choices=["executive","none"],default="executive",help="Apply Swarag Executive styles or original raw effect styling")
        if cmd=="preview":x.add_argument("--at",type=float,required=True)
    a=p.parse_args()
    if a.cmd=="list":print("\n".join(sorted(AVAILABLE_EFFECTS)));return
    plan=validate_plan(json.loads(Path(a.plan).read_text(encoding="utf8")),a.duration if a.cmd=="validate" else None)
    if a.cmd=="validate":print(f"Valid plan: {len(plan)} effect(s)");return
    inp=Path(a.input).resolve();out=Path(a.output).resolve()
    if not inp.is_file():p.error(f"Input missing: {inp}")
    if inp==out:p.error("Refusing to overwrite input")
    if not 240<=a.width<=2160 or a.width%2:p.error("Width must be even and between 240 and 2160")
    if a.cmd=="render" and out.suffix.lower()!=".mp4":p.error("Use .mp4 output")
    if a.cmd=="preview" and out.suffix.lower()!=".png":p.error("Use .png output")
    if a.cmd=="preview" and (a.at<0 or not math.isfinite(a.at)):p.error("Invalid preview time")
    plan=apply_brand(plan,name=a.brand)
    with tempfile.TemporaryDirectory() as t:
        plan_path=Path(t)/"plan.json"
        plan_path.write_text(json.dumps({"effects":plan}),encoding="utf8")
        args=[sys.executable,str(ROOT/"scripts"/"fx.py"),"--plan",str(plan_path),str(inp),str(out),"--width",str(a.width)]
        if a.cmd=="preview":args.extend(["--still",str(a.at)])
        subprocess.run(args,check=True)
    if not out.is_file() or out.stat().st_size==0:raise SystemExit("Renderer did not produce output")
    print(f"Output: {out}")
if __name__=="__main__":main()
