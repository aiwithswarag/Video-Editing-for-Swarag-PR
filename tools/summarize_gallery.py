#!/usr/bin/env python3
"""Validate 42/42 + five named looks and create a single preview contact sheet."""
import json
import sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from effect_catalog import read_registry
from render_effect_gallery import NAMED_VARIANTS

def main():
    root=Path(sys.argv[1]);output=Path(sys.argv[2])
    output.mkdir(parents=True,exist_ok=True)
    names,_,_=read_registry()
    expected=set(names) | {label for label,_,_ in NAMED_VARIANTS}
    images=list(root.rglob("*.png"))
    png_by_stem={}
    for image in images:
        if image.stem in png_by_stem:
            raise SystemExit(f"Duplicate gallery preview: {image.stem}")
        png_by_stem[image.stem]=image
    motion=list(root.rglob("*.mp4"))
    clips_by_stem={}
    for clip in motion:
        if clip.stem in clips_by_stem:
            raise SystemExit(f"Duplicate motion clip: {clip.stem}")
        clips_by_stem[clip.stem]=clip
    missing_motion=sorted(expected-set(clips_by_stem))
    missing=sorted(expected-set(png_by_stem))
    unexpected=sorted(set(png_by_stem)-expected)
    runs=list(root.rglob("results.json"))
    results=[r for path in runs for r in json.loads(path.read_text(encoding="utf8"))]
    failed=[r["effect"] for r in results if not r["ok"]]
    incomplete_qc=[r["effect"] for r in results if not (
        isinstance(r.get("preview_qc"),dict) and
        isinstance(r.get("media_qc"),dict) and
        r["media_qc"].get("full_video_and_audio_decode") is True and
        int(r["media_qc"].get("decoded_frames",0))>=10 and
        r["media_qc"].get("audio_streams",0)>=1)]
    duplicate_results=sorted(x for x in {r["effect"] for r in results}
                             if sum(v["effect"]==x for v in results)>1)
    if missing or missing_motion or unexpected or failed or incomplete_qc or duplicate_results or len(results)!=len(expected):
        raise SystemExit(f"Coverage error: previews={missing}, motions={missing_motion}, extra={unexpected}, failed={failed}, incomplete_qc={incomplete_qc}, duplicate_results={duplicate_results}, results={len(results)} expected={len(expected)}")
    ordered=list(names)+[label for label,_,_ in NAMED_VARIANTS]
    cols=6;cellw=205;cellh=390;rows=(len(ordered)+cols-1)//cols
    sheet=Image.new("RGB",(cols*cellw,rows*cellh),(239,240,242))
    dr=ImageDraw.Draw(sheet)
    for i,name in enumerate(ordered):
        original=Image.open(png_by_stem[name]).convert("RGB")
        original.thumbnail((cellw-12,cellh-34))
        x=(i%cols)*cellw+(cellw-original.width)//2
        y=(i//cols)*cellh+27
        sheet.paste(original,(x,y))
        dr.text(((i%cols)*cellw+6,(i//cols)*cellh+5),name,fill=(18,25,33))
    sheet.save(output/"all-47-effects.jpg",quality=86)
    observable=[r["effect"] for r in results if
                r["preview_qc"].get("visible_change_detected_in_sample") is True]
    low_change=[r["effect"] for r in results if
                r["preview_qc"].get("visible_change_detected_in_sample") is False]
    report={"registered_effects":len(names),"named_looks":len(NAMED_VARIANTS),
            "rendered_previews":len(results),"rendered_motion_clips":len(clips_by_stem),
            "decoded_motion_clips":len(results),
            "all_video_and_audio_fully_decoded":True,
            "missing":[],"duplicates":[],"failed":[],
            "visible_change_detected_in_single_synthetic_frame":observable,
            "no_clear_change_in_single_synthetic_frame":low_change,
            "test_scope":"2-second 360x640 8fps SYNTHETIC fixture; 240px motion outputs",
            "technical_status":"BASIC_EFFECT_SMOKE_PASS",
            "person_masking_status":"NOT VERIFIED ON REAL MOVING SUBJECT",
            "phone_typography_status":"NOT VERIFIED",
            "creative_status":"NOT APPROVED — full-motion 1080x1920 real footage review required"}
    (output/"coverage-report.json").write_text(json.dumps(report,indent=2),encoding="utf8")
    (output/"effect-by-effect.json").write_text(
        json.dumps(sorted(results,key=lambda x:x["effect"]),indent=2),encoding="utf8")
    print(json.dumps({k:v for k,v in report.items() if k not in
          ("visible_change_detected_in_single_synthetic_frame",
           "no_clear_change_in_single_synthetic_frame")}))
if __name__=="__main__":main()
