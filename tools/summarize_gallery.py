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
    missing=sorted(expected-set(png_by_stem))
    unexpected=sorted(set(png_by_stem)-expected)
    runs=list(root.rglob("results.json"))
    results=[r for path in runs for r in json.loads(path.read_text(encoding="utf8"))]
    failed=[r["effect"] for r in results if not r["ok"]]
    if missing or unexpected or failed or len(results)!=len(expected):
        raise SystemExit(f"Coverage error: missing={missing}, extra={unexpected}, failed={failed}, results={len(results)} expected={len(expected)}")
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
    report={"registered_effects":42,"named_looks":5,"rendered_previews":len(results),
            "missing":[],"duplicates":[],"failed":[],"visual_review":"NOT YET APPROVED"}
    (output/"coverage-report.json").write_text(json.dumps(report,indent=2),encoding="utf8")
    print(json.dumps(report))
if __name__=="__main__":main()
