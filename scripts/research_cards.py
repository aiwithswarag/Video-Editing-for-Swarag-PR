#!/usr/bin/env python3
"""Source-led portrait research graphics. Never infer or invent metrics."""
import argparse
import json
import math
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
INK=(16,26,35); IVORY=(240,236,227); TEAL=(91,173,162)
GOLD=(198,163,103); MUTED=(153,170,174); RULE=(56,74,80)

def validate(item):
    if not isinstance(item,dict) or item.get("kind") not in ("benchmark","coverage"):
        raise ValueError("Expected benchmark or coverage card")
    for field in ("title","scope","citation","source_url","caveat"):
        x=item.get(field)
        if not isinstance(x,str) or not x.strip() or len(x)>130:
            raise ValueError("Invalid source-backed field: "+field)
    if not re.fullmatch(r"https://arxiv\.org/abs/\d{4}\.\d{4,5}",item["source_url"]):
        raise ValueError("A primary arXiv paper URL is required")
    if item["kind"]=="benchmark":
        for side in ("before","after"):
            x=item.get(side)
            if not isinstance(x,dict) or not isinstance(x.get("label"),str) or not x["label"]:
                raise ValueError("Every numerical bar needs its scope label")
            value=x.get("value")
            if isinstance(value,bool) or not isinstance(value,(float,int)) or not math.isfinite(value) or not 0<=value<=100:
                raise ValueError("Task-success percentage must be 0-100")
    else:
        n,total=item.get("matched"),item.get("total")
        if any(isinstance(x,bool) or not isinstance(x,int) for x in (n,total)) or not 0<=n<=total<=200:
            raise ValueError("Expected audited integer counts, 0<=matched<=total<=200")
        if not isinstance(item.get("contrast"),str) or not item["contrast"]:
            raise ValueError("Name the specific comparison")
    return item

def render(item,font_dir,width=1080):
    validate(item)
    if not isinstance(width,int) or width%2 or not 360<=width<=1080:
        raise ValueError("Output width must be even, 360-1080")
    font_dir=Path(font_dir)
    sans=font_dir/"Inter.ttf"; serif=font_dir/"InstrumentSerif-Italic.ttf"
    if not sans.is_file() or not serif.is_file():
        raise FileNotFoundError("Use tools/download_assets.py to install licensed fonts")
    def font(sz,kind="sans",heavy=False):
        f=ImageFont.truetype(str(serif if kind=="serif" else sans),sz)
        if kind=="sans":
            try:f.set_variation_by_axes([24,650 if heavy else 430])
            except (OSError,ValueError,AttributeError):pass
        return f
    def fit(d,words,size,max_width,kind="sans",heavy=False):
        for z in range(size,19,-2):
            f=font(z,kind,heavy)
            if d.textlength(words,font=f)<=max_width:return f
        raise ValueError("Text exceeds typography safe area")
    image=Image.new("RGB",(1080,1920),INK); d=ImageDraw.Draw(image)
    d.line((89,115,991,115),fill=RULE,width=2)
    d.text((92,146),"SWARAG / AI FIELD NOTES",font=font(24,heavy=True),fill=TEAL)
    d.text((92,210),item["scope"].upper(),font=fit(d,item["scope"].upper(),24,900,heavy=True),fill=MUTED)
    title=item["title"]
    d.text((90,315),title,font=fit(d,title,100,900,"serif"),fill=IVORY)
    d.line((92,486,198,486),fill=GOLD,width=5)
    if item["kind"]=="benchmark":
        before,after=item["before"],item["after"]
        d.text((88,673),f'{before["value"]:g}',font=font(169,heavy=True),fill=IVORY)
        d.text((540,729),"→",font=font(94),fill=GOLD)
        d.text((658,691),f'{after["value"]:g}',font=font(155,heavy=True),fill=TEAL)
        d.text((94,882),"%",font=font(47,heavy=True),fill=MUTED)
        d.text((675,886),"%",font=font(47,heavy=True),fill=MUTED)
        for index,(number,color) in enumerate(((before,MUTED),(after,TEAL))):
            y=1045+150*index
            d.line((98,y,982,y),fill=RULE,width=14)
            d.line((98,y,98+round(884*number["value"]/100),y),fill=color,width=14)
            desc=number["label"].upper()
            d.text((98,y+34),desc,font=fit(d,desc,25,880,heavy=True),fill=color)
    else:
        matched,total=item["matched"],item["total"]
        d.text((87,613),str(matched),font=font(292,heavy=True),fill=TEAL)
        d.text((413,734),"of",font=font(77,"serif"),fill=MUTED)
        d.text((558,643),str(total),font=fit(d,str(total),210,430,heavy=True),fill=IVORY)
        line=item["contrast"]
        d.text((96,980),line,font=fit(d,line,37,895),fill=IVORY)
        for n in range(total):
            x=99+43*(n%20);y=1110+43*(n//20)
            d.ellipse((x-6,y-6,x+6,y+6),fill=TEAL if n<matched else RULE)
    d.line((96,1520,983,1520),fill=RULE,width=2)
    caveat=item["caveat"]
    d.text((93,1584),caveat,font=fit(d,caveat,54,894,"serif"),fill=IVORY)
    d.text((94,1670),item["citation"],font=fit(d,item["citation"],27,890,heavy=True),fill=GOLD)
    d.line((88,1767,991,1767),fill=RULE,width=2)
    d.text((92,1798),"RESEARCH REFERENCE / CREATIVE REVIEW",font=font(21,heavy=True),fill=MUTED)
    if width!=1080:image=image.resize((width,round(width*16/9)),Image.Resampling.LANCZOS)
    return image

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("data",type=Path)
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--font-dir",type=Path,default=ROOT/"fonts")
    p.add_argument("--width",type=int,default=1080)
    args=p.parse_args()
    obj=json.loads(args.data.read_text("utf8"))
    cards=obj.get("cards") if isinstance(obj,dict) else None
    if not isinstance(cards,list) or not 1<=len(cards)<=12:
        raise ValueError("Expected one to twelve cards")
    args.output_dir.mkdir(parents=True,exist_ok=True)
    for i,card in enumerate(cards,1):
        path=args.output_dir/f'evidence_{i:02d}.png'
        render(card,args.font_dir,args.width).save(path)
        print(path)
if __name__=="__main__":main()
