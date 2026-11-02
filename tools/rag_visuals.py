#!/usr/bin/env python3
"""Swarag RAG explainer graphics, used AFTER original 42-effect engine.

Only draws labels/evidence explicitly supported by a matching verified script.
Original footage and AAC remain in the master. No fabricated screenshots,
fake business metrics, cartoon B-roll, computer-generated narrator or stock art.
The visual layer is a supplementary editorial graphic pass, NOT a new "43rd effect".
"""
from __future__ import annotations
import json
import math
import subprocess
import tempfile
from fractions import Fraction
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from rag_storyboard import COPY,validate,coverage

ROOT=Path(__file__).resolve().parents[1]
INK=(15,28,40,241)
WHITE=(244,245,241,252)
MUTED=(200,212,217,244)
GOLD=(207,177,117,255)
TEAL=(80,198,180,255)
CORAL=(223,133,114,255)

def media(path):
    r=subprocess.run(["ffprobe","-v","error","-select_streams","v:0",
        "-show_entries","stream=width,height,avg_frame_rate,nb_frames:format=duration",
        "-of","json",str(path)],capture_output=True,text=True,check=True)
    d=json.loads(r.stdout);v=d["streams"][0]
    return {"width":int(v["width"]),"height":int(v["height"]),
            "fps":Fraction(v["avg_frame_rate"]),
            "frames":int(v["nb_frames"]),
            "duration":float(d["format"]["duration"])}

def _font(fontdir,pixels,serif=False):
    name="InstrumentSerif-Italic.ttf" if serif else "Inter.ttf"
    path=fontdir/name
    if not path.is_file():
        raise FileNotFoundError("Swarag font assets missing; run tools/download_assets.py")
    return ImageFont.truetype(str(path),max(8,int(pixels)))

def _fitted(draw,words,available,size,fontdir,serif=False,minimum=None):
    # Font size has already been scaled from 1080p to output width.
    # A fixed 20px floor accidentally rejected every 360px preview headline.
    minimum=max(8,round(size*.48)) if minimum is None else minimum
    while size>=minimum:
        f=_font(fontdir,size,serif)
        if draw.textlength(words,font=f)<=available:return f
        size-=2
    raise ValueError("Editorial copy exceeds phone-safe width; do not clip titles")

def _label(draw,xy,string,font,fill):
    draw.text(xy,string,font=font,fill=fill,stroke_width=0)

def draw_overlay(kind,width,height,fontdir):
    if width<360 or not 1.7<=height/width<=1.9:
        raise ValueError("RAG graphics require portrait 9:16 at least 360 px wide")
    if kind not in COPY:
        raise ValueError("Unknown source-backed RAG editorial graphic")
    im=Image.new("RGBA",(width,height),(0,0,0,0))
    d=ImageDraw.Draw(im)
    scale=width/1080
    def px(x):return round(x*scale)
    x=px(68);r=width-x
    title_font=_font(fontdir,px(35))
    eyebrow=_font(fontdir,px(26))
    micro=_font(fontdir,px(22))
    body=_font(fontdir,px(35))
    bold=_font(fontdir,px(44))
    hero=_font(fontdir,px(71),True)

    # Top identity strip. Nothing is burned into the face by the top strip.
    d.rounded_rectangle([x,px(105),r,px(175)],radius=px(13),fill=(20,36,49,195))
    _label(d,(x+px(24),px(121)),"SWARAG  /  AI VERIFICATION",eyebrow,WHITE)
    d.line([(x,px(194)),(x+px(100),px(194))],fill=GOLD,width=max(2,px(5)))

    # Restrained lower-card system. Intentional spacing: sits above platform UI.
    y=round(height*.596)
    bottom=min(round(height*.847),height-px(225))
    d.rounded_rectangle([x,y,r,bottom],radius=px(24),fill=(15,29,41,223),
                        outline=(104,135,147,150),width=max(1,px(2)))
    ix=x+px(33);maxw=r-ix-px(23)
    def headline(value,offset=42):
        ff=_fitted(d,value,maxw,px(46),fontdir)
        _label(d,(ix,y+px(offset)),value,ff,WHITE)
    def small_tag(value,dy=18):
        _label(d,(ix,y+px(dy)),value,eyebrow,GOLD)
    if kind=="hook":
        small_tag("SOURCE CHECK / 01")
        headline("YOUR AI CITED A SOURCE",75)
        _label(d,(ix,y+px(170)),COPY[kind][1],hero,GOLD)
    elif kind=="policies":
        small_tag("FICTIONAL EXAMPLE · NOT REAL POLICY")
        gap=px(17);half=(maxw-gap)//2
        ty=y+px(76)
        for index,(year,amount,status,tint) in enumerate([
            ("2024","$100 / NIGHT","OLD POLICY",CORAL),
            ("2026","$150 / NIGHT","CURRENT POLICY",TEAL)]):
            cx=ix+index*(half+gap)
            d.rounded_rectangle([cx,ty,cx+half,ty+px(275)],radius=px(15),
                                fill=(35,54,67,230),outline=tint,width=max(2,px(3)))
            _label(d,(cx+px(17),ty+px(18)),year,bold,WHITE)
            ff=_fitted(d,amount,half-px(30),px(35),fontdir)
            _label(d,(cx+px(17),ty+px(99)),amount,ff,tint)
            _label(d,(cx+px(17),ty+px(208)),status,micro,MUTED)
    elif kind=="outdated-answer":
        small_tag("FICTIONAL AI RESPONSE / 2024 CITATION")
        _label(d,(ix,y+px(87)),"AI ANSWER:  $100",hero,WHITE)
        d.line([(ix,y+px(191)),(r-px(33),y+px(191))],fill=(132,156,162,175),width=px(2))
        _label(d,(ix,y+px(219)),"CITATION: 2024 POLICY",body,MUTED)
        _label(d,(ix,y+px(282)),"OUTDATED SOURCE",bold,CORAL)
    elif kind=="rag-flow":
        small_tag("RAG / RETRIEVAL-AUGMENTED GENERATION")
        stages=("SEARCH DOCUMENTS","RETRIEVE TEXT","GENERATE ANSWER")
        for index,line in enumerate(stages):
            by=y+px(77)+index*px(78)
            d.rounded_rectangle([ix,by,r-px(33),by+px(63)],radius=px(10),fill=(42,65,75,227))
            _label(d,(ix+px(21),by+px(12)),str(index+1).zfill(2)+"  "+line,body,WHITE)
        _label(d,(ix,y+px(337)),"RELEVANT IS NOT ALWAYS CURRENT",eyebrow,GOLD)
    elif kind.startswith("check-"):
        small_tag("THREE VERIFICATION CHECKS")
        n=int(kind[-1])
        for index,line in enumerate(COPY[kind][1:],1):
            yy=y+px(78)+(index-1)*px(88)
            accent=TEAL if index<n else GOLD
            d.ellipse([ix,yy,ix+px(47),yy+px(47)],fill=accent)
            _label(d,(ix+px(17),yy+px(7)),str(index),micro,INK)
            f=_fitted(d,line,maxw-px(74),px(33),fontdir)
            _label(d,(ix+px(65),yy+px(7)),line,f,WHITE)
    elif kind=="closing":
        small_tag("THE TAKEAWAY")
        _label(d,(ix,y+px(101)),"A CITATION",hero,WHITE)
        f=_fitted(d,"IS WHERE VERIFICATION STARTS",maxw,px(47),fontdir)
        _label(d,(ix,y+px(220)),"IS WHERE VERIFICATION STARTS",f,GOLD)
    return im

def apply(source,output,beats,script=None,crf=18):
    source=Path(source);output=Path(output)
    if source.resolve()==output.resolve():
        raise ValueError("Graphics output must not overwrite an input video")
    if not source.is_file():
        raise FileNotFoundError(source)
    info=media(source)
    valid=validate(beats,info["duration"],script)
    if not 8<=float(info["fps"])<=30.5 or info["frames"]<1:
        raise ValueError("Supported source requires CFR 8–30.5 fps")
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="swarag_rag_graphics_") as work:
        assets=Path(work)
        inputs=["-i",str(source)]
        filters=["[0:v]setpts=PTS-STARTPTS,format=yuv420p[v0]"]
        prior="v0"
        for index,beat in enumerate(valid,1):
            img=assets/f"editorial_{index:02d}.png"
            draw_overlay(beat["kind"],info["width"],info["height"],ROOT/"fonts").save(img)
            inputs+=["-loop","1","-framerate",str(info["fps"]),"-i",str(img)]
            a,b=beat["start"],beat["end"]
            fade=min(.20,(b-a)/4)
            filters.append(f"[{index}:v]format=rgba,"
                           f"fade=t=in:st={a:.3f}:d={fade:.3f}:alpha=1,"
                           f"fade=t=out:st={b-fade:.3f}:d={fade:.3f}:alpha=1[a{index}]")
            filters.append(f"[{prior}][a{index}]overlay=0:0:format=auto:"
                           f"enable='between(t,{a:.3f},{b:.3f})':shortest=1[v{index}]")
            prior=f"v{index}"
        command=["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
                 *inputs,"-filter_complex",";".join(filters),
                 "-map",f"[{prior}]","-map","0:a:0","-c:v","libx264",
                 "-preset","veryfast","-crf",str(crf),"-pix_fmt","yuv420p",
                 "-r",str(info["fps"]),"-frames:v",str(info["frames"]),
                 "-c:a","copy","-movflags","+faststart",str(output)]
        subprocess.run(command,check=True)
    if not output.is_file() or output.stat().st_size<4096:
        raise RuntimeError("RAG graphics MP4 output not created")
    return {"compositing":"source-backed Swarag RAG graphics after original 42-effect renderer",
            **coverage(valid,info["duration"],script),"output":str(output),
            "source_fps":str(info["fps"]),"source_frames":info["frames"]}
