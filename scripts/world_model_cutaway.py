#!/usr/bin/env python3
"""Original editorial World Models schematic, not a robot-performance demonstration."""
import argparse
import subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
INK=(19,29,39); PANEL=(28,43,53); IVORY=(240,238,231)
MUTED=(168,185,186); TEAL=(91,171,162); GOLD=(207,173,110)
BORDER=(65,82,91); DIM=(98,122,125)

def ease(x):
    x=max(0.,min(1.,x))
    return x*x*(3-2*x)

def draw_frame(time,width=540,fps=15,frames=90,font_dir=None):
    if width%2 or not 360<=width<=1080 or not 8<=fps<=60 or frames<2:
        raise ValueError("Invalid rendering parameters")
    height=round(width*16/9/2)*2
    k=width/1080.
    xy=lambda x,y:(round(x*k),round(y*k))
    rect=lambda *v:tuple(round(x*k) for x in v)
    px=lambda v:max(1,round(v*k))
    fonts=Path(font_dir) if font_dir else ROOT/"fonts"
    serif,sans=fonts/"InstrumentSerif-Italic.ttf",fonts/"Inter.ttf"
    if not serif.is_file() or not sans.is_file():
        raise FileNotFoundError("Run python tools/download_assets.py to install licensed fonts")
    font=lambda path,size:ImageFont.truetype(str(path),px(size))
    head=font(serif,112);label=font(sans,26);small=font(sans,21);step=font(sans,36)
    im=Image.new("RGB",(width,height),INK);d=ImageDraw.Draw(im)
    d.line([xy(85,92),xy(995,92)],fill=BORDER,width=px(2))
    d.text(xy(90,123),"SWARAG  /  AI FIELD NOTES",font=label,fill=TEAL)
    d.text(xy(90,220),"Before it acts,",font=head,fill=IVORY)
    d.text(xy(90,340),"it predicts.",font=head,fill=IVORY)
    d.line([xy(90,494),xy(179,494)],fill=GOLD,width=px(5))
    d.text(xy(206,479),"WORLD MODELS  /  ROBOTICS",font=small,fill=MUTED)
    d.rounded_rectangle(rect(74,573,1006,1435),radius=px(25),fill=PANEL,outline=BORDER,width=px(2))
    d.text(xy(121,612),"A SINGLE ACTION. MULTIPLE POSSIBLE FUTURES.",font=small,fill=MUTED)
    d.line([xy(120,662),xy(953,662)],fill=BORDER,width=px(2))
    d.line([xy(118,1250),xy(949,1250)],fill=DIM,width=px(2))
    d.line([xy(616,1092),xy(934,1092)],fill=DIM,width=px(4))
    for a,b in [((670,1093),(646,1240)),((901,1093),(915,1240))]:
        d.line([xy(*a),xy(*b)],fill=BORDER,width=px(9))
    d.rounded_rectangle(rect(166,1152,278,1238),radius=px(20),fill=(54,71,81),outline=(118,137,143),width=px(3))
    joints=[(223,1150),(330,967),(506,890)]
    for a,b in zip(joints,joints[1:]):
        d.line([xy(*a),xy(*b)],fill=(130,150,150),width=px(34))
        d.line([xy(*a),xy(*b)],fill=(208,217,209),width=px(9))
    d.line([xy(506,890),xy(616,901)],fill=(140,162,164),width=px(26))
    for x,y in joints:
        d.ellipse(rect(x-24,y-24,x+24,y+24),fill=PANEL,outline=(194,209,209),width=px(6))
        d.ellipse(rect(x-6,y-6,x+6,y+6),fill=TEAL)
    for a,b in [((616,901),(650,943)),((616,901),(656,872))]:
        d.line([xy(*a),xy(*b)],fill=IVORY,width=px(11))
    d.text(xy(134,1303),"ROBOT ARM",font=small,fill=MUTED)
    d.rounded_rectangle(rect(726,937,833,1091),radius=px(16),fill=(50,71,79),outline=IVORY,width=px(5))
    d.ellipse(rect(725,925,834,958),outline=IVORY,width=px(5))
    d.arc(rect(825,971,893,1055),start=-83,end=95,fill=IVORY,width=px(6))
    d.line([xy(740,1037),xy(818,1037)],fill=TEAL,width=px(5))
    d.text(xy(751,1130),"CUP",font=small,fill=IVORY)
    observation=ease((time-.4)/1.25)
    simulation=ease((time-1.7)/2.5)
    selection=ease((time-4.2)/1.65)
    if observation>.01:
        d.arc(rect(476,769,868,1148),start=214,end=214+175*observation,fill=TEAL,width=px(5))
    if simulation>.01:
        coords=[]
        for n in range(100):
            t=n/99
            if t>simulation:break
            x=(1-t)**2*631+2*(1-t)*t*820+t*t*845
            y=(1-t)**2*902+2*(1-t)*t*796+t*t*900
            coords.append((x,y))
        for n in range(len(coords)-1):
            if n%9<5:d.line([xy(*coords[n]),xy(*coords[n+1])],fill=GOLD,width=px(6))
        if simulation>.28:
            amount=ease((simulation-.28)/.4)
            color=tuple(round(PANEL[n]*(1-amount)+GOLD[n]*amount) for n in range(3))
            ghost=Image.new("RGBA",(px(125),px(165)),(0,0,0,0))
            gd=ImageDraw.Draw(ghost)
            gd.rounded_rectangle((px(15),px(10),px(103),px(147)),radius=px(14),outline=color,width=px(4))
            ghost=ghost.rotate(-24,resample=Image.Resampling.BICUBIC,expand=True)
            im.paste(ghost,xy(842,829),ghost);d=ImageDraw.Draw(im)
            d.text(xy(783,744),"IF IT SLIPS",font=small,fill=GOLD)
    if selection>.01:
        d.rounded_rectangle(rect(661,851,931,1182),radius=px(15),outline=TEAL,width=px(3))
    for n,(number,word) in enumerate([("01","OBSERVE"),("02","SIMULATE"),("03","CHOOSE")]):
        x=85+n*307
        active=n==(0 if time<1.7 else 1 if time<4.25 else 2)
        d.rounded_rectangle(rect(x,1510,x+285,1635),radius=px(12),
             fill=(29,55,58) if active else PANEL,outline=TEAL if active else BORDER,
             width=px(3 if active else 2))
        d.text(xy(x+17,1528),number,font=small,fill=GOLD if active else DIM)
        d.text(xy(x+17,1575),word,font=step,fill=IVORY if active else MUTED)
    d.line([xy(86,1708),xy(995,1708)],fill=BORDER,width=px(2))
    d.text(xy(87,1739),"CONCEPTUAL SCHEMATIC / NOT ROBOT TEST FOOTAGE",font=small,fill=MUTED)
    d.text(xy(88,1807),"Prediction is not proof of reliability.",font=font(serif,45),fill=IVORY)
    fade=min(1.,time/.35,(frames/fps-time)/.38)
    if fade<1:im=Image.blend(Image.new("RGB",(width,height),INK),im,max(0,fade))
    return im

def render(out,width=540,fps=15.,frames=90,font_dir=None):
    if not 2<=frames<=1800:raise ValueError("Invalid frame count")
    height=round(width*16/9/2)*2
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-y",
         "-f","rawvideo","-pix_fmt","rgb24","-s",f"{width}x{height}",
         "-r",str(fps),"-i","pipe:0","-an","-c:v","libx264","-preset","ultrafast",
         "-crf","19","-pix_fmt","yuv420p","-movflags","+faststart",str(out)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        for i in range(frames):
            proc.stdin.write(draw_frame(i/fps,width,fps,frames,font_dir).tobytes())
        proc.stdin.close()
        error=proc.stderr.read().decode("utf8",errors="replace")
        if proc.wait():raise RuntimeError(error[-900:])
    except Exception:
        proc.kill()
        raise
    return {"width":width,"height":height,"frames":frames,"fps":fps,
            "disclaimer":"Conceptual illustration, not actual robot-test footage."}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("output",type=Path);p.add_argument("--width",type=int,default=540)
    p.add_argument("--fps",type=float,default=15)
    p.add_argument("--frames",type=int,default=90);p.add_argument("--font-dir",type=Path)
    a=p.parse_args()
    print(render(a.output,a.width,a.fps,a.frames,a.font_dir))
if __name__=="__main__":main()
