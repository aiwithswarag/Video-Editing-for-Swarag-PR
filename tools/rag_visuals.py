#!/usr/bin/env python3
"""Face-safe, SOURCE-GROUNDED Swarag RAG explainer editorial pass.

After the ORIGINAL scripts/fx.py 42-effect engine, the authentic speaker
occupies a separate, clear camera region and the instructional graphics occupy
a separate lower editorial region. There is NEVER a graphic/card over the
speaker's video pixels. This replaces the earlier fixed opaque card overlay
that crossed Swarag's beard, face and gesture area.

Uses the repository's YuNet model to choose a static face-safe crop when
detected reliably. If detection is uncertain, conservatively fits the FULL
original camera frame in the unobstructed top area with ink side mattes,
rather than risk clipping the face. Never fabricates B-roll, people, audio,
metrics, quotations or policies. No new "43rd effect" claimed.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
from fractions import Fraction
from pathlib import Path
from statistics import median

from PIL import Image, ImageDraw, ImageFont

from rag_storyboard import COPY, validate, coverage

ROOT = Path(__file__).resolve().parents[1]
INK = (18,27,38,255)         # repository Executive Editorial V2 #121B26
IVORY = (242,239,233,255)    # #F2EFE9
GOLD = (183,150,96,255)      # #B79660
SLATE = (205,213,213,255)    # #CDD5D5
TEAL = (44,154,144,255)      # #2C9A90
CORAL = (208,144,119,255)    # only to mark outdated fictional content

LAYOUT_ID = "face-safe-editorial-split-v3"
CAMERA_HEIGHT_FRACTION = 0.64
LAST_TEXT_HEIGHT_FRACTION = 0.87


def video_info(path):
    run = subprocess.run(
        ["ffprobe","-v","error","-select_streams","v:0",
         "-show_entries","stream=width,height,avg_frame_rate,nb_frames:format=duration",
         "-of","json",str(path)],capture_output=True,text=True,check=True)
    data=json.loads(run.stdout); item=data["streams"][0]
    return {
        "width":int(item["width"]), "height":int(item["height"]),
        "fps":Fraction(item["avg_frame_rate"]),
        "frames":int(item["nb_frames"]),
        "duration":float(data["format"]["duration"]),
    }


def geometry(width,height):
    if width<360 or not 1.7<=height/width<=1.9:
        raise ValueError("Face-safe RAG editorial split needs 9:16 portrait >=360px")
    top=round(height*CAMERA_HEIGHT_FRACTION)
    if top%2: top-=1
    return {"camera_bottom":top, "text_bottom":round(height*LAST_TEXT_HEIGHT_FRACTION),
            "width":width,"height":height}


def _font(folder,size,serif=False):
    file=folder/("InstrumentSerif-Italic.ttf" if serif else "Inter.ttf")
    if not file.is_file():
        raise FileNotFoundError("Required Swarag Inter/Instrument Serif font is missing")
    f=ImageFont.truetype(str(file),max(8,int(size)))
    if not serif:
        try:f.set_variation_by_axes([24,600])
        except (ValueError,OSError,AttributeError):pass
    return f


def fitted(draw,text,font_folder,size,max_width,serif=False):
    size=max(8,int(size))
    while size>=8:
        f=_font(font_folder,size,serif=serif)
        if draw.textlength(text,font=f)<=max_width:return f
        size-=1
    raise ValueError("Editorial text does not fit; shorten source-backed copy")


def draw_overlay(kind,width,height,font_folder):
    """Transparent camera area; graphics and flat ink only BELOW camera.

    The top camera region is guaranteed alpha-zero (not merely mask-averaged).
    This is testable without a face-detection model or the user's private media.
    """
    if kind not in COPY:
        raise ValueError("Unsupported source-backed graphic kind")
    geo=geometry(width,height);top=geo["camera_bottom"]
    scale=width/1080.
    px=lambda v:round(v*scale)
    board=Image.new("RGBA",(width,height),(0,0,0,0))
    draw=ImageDraw.Draw(board)
    draw.rectangle([0,top,width,height],fill=INK)
    draw.line([(px(85),top+px(3)),(width-px(85),top+px(3))],
              fill=GOLD,width=max(1,px(3)))
    left=px(86);right=width-px(86);maxw=right-left
    y=top+px(34)
    def set_text(text,x,yy,size,color=IVORY,serif=False,max_width=None):
        fit=fitted(draw,text,font_folder,px(size),max_width or (right-x),serif)
        draw.text((x,yy),text,font=fit,fill=color)
    def upper(text):
        set_text(text,left,y,30,GOLD)
    def heading(text,dy=67,size=65):
        set_text(text,left,y+px(dy),size,IVORY,True)
    def sub(text,dy=165,size=31,color=SLATE):
        set_text(text,left,y+px(dy),size,color)
    if kind=="hook":
        upper("AI VERIFICATION / 01")
        heading("A citation is not proof",66,65)
        sub("Your AI can cite a source and still be wrong.",173,34)
    elif kind=="policies":
        upper("FICTIONAL POLICIES / EXAMPLE ONLY")
        half=maxw/2
        draw.line([(left+round(half),y+px(78)),
                   (left+round(half),y+px(306))],fill=SLATE,width=max(1,px(2)))
        for index,(year,amount,meta,color) in enumerate((
            ("2024","$100","OUTDATED / NIGHT",CORAL),
            ("2026","$150","CURRENT / NIGHT",TEAL))):
            sx=left+round(index*half)+px(18)
            cellw=int(half-px(42))
            set_text(year,sx,y+px(76),43,SLATE,max_width=cellw)
            set_text(amount,sx,y+px(135),95,color,True,max_width=cellw)
            set_text(meta,sx,y+px(258),26,SLATE,max_width=cellw)
    elif kind=="outdated-answer":
        upper("FICTIONAL AI ANSWER")
        heading("$100 per night",57,90)
        sub("CITED: 2024 POLICY  ·  OUTDATED",184,35,CORAL)
        sub("A citation can point to the wrong version.",241,30,SLATE)
    elif kind=="rag-flow":
        upper("RAG / RETRIEVAL-AUGMENTED GENERATION")
        labels=("01  SEARCH","02  RETRIEVE","03  GENERATE")
        gap=maxw/3
        for i,label in enumerate(labels):
            xx=left+round(i*gap)
            set_text(label,xx,y+px(90),38,IVORY,max_width=int(gap-px(13)))
            if i<2:
                draw.line([(xx+round(gap)-px(18),y+px(96)),
                           (xx+round(gap)-px(5),y+px(96))],
                          fill=GOLD,width=max(1,px(3)))
        sub("Relevant does not always mean current.",212,33,GOLD)
    elif kind.startswith("check-"):
        n=int(kind[-1])
        upper("THREE CHECKS / VERIFY THE CITATION")
        rows=("RIGHT VERSION?","ANSWER MATCHES THE SOURCE?","AUTHORIZED TO ACCESS?")
        for i in range(n):
            yy=y+px(74)+i*px(90)
            set_text(f"{i+1:02d}",left,yy,41,GOLD,max_width=px(65))
            set_text(rows[i],left+px(85),yy,37,IVORY,
                     max_width=maxw-px(90))
    elif kind=="closing":
        upper("THE TAKEAWAY")
        heading("A citation is where",70,67)
        set_text("verification starts.",left,y+px(162),75,GOLD,True)
        sub("Not where it ends.",264,35,SLATE)
    return board


def sample_face_crop(video,width,height,top,model=None,max_samples=14):
    """Use SAME YuNet model as the original 42-effect engine, else safe contain.

    The detector is only used to choose a STATIC camera crop; a detection
    failure never means "put cards over the face." The original video
    remains pixel-authentic and unretouched.
    """
    model=Path(model or (ROOT/"models"/"yunet.onnx"))
    fallback={"camera_mode":"contain-full-source","crop_y":None,
              "face_detections":0,"face_protection":"unobstructed-camera-band"}
    if not model.is_file():
        return fallback
    # A host-side plan/QA pass may not install OpenCV; the full original
    # Docker runtime does. Never fail media validation just to import a
    # detector when a conservative unobstructed-camera fallback is possible.
    try:
        import cv2
    except ImportError:
        return fallback
    capture=cv2.VideoCapture(str(video))
    if not capture.isOpened():
        return fallback
    try:
        detector=cv2.FaceDetectorYN.create(str(model),"",(width,height),0.60,0.3,20)
        centers=[]
        lefts=[];bottoms=[]
        duration=capture.get(cv2.CAP_PROP_FRAME_COUNT) / max(1.,capture.get(cv2.CAP_PROP_FPS))
        for i in range(max_samples):
            second=duration*(i+.5)/max_samples
            capture.set(cv2.CAP_PROP_POS_MSEC,second*1000)
            ok,frame=capture.read()
            if not ok:continue
            if frame.shape[1]!=width or frame.shape[0]!=height:
                frame=cv2.resize(frame,(width,height))
            detector.setInputSize((width,height))
            _,detected=detector.detect(frame)
            if detected is None or not len(detected):continue
            strongest=max(detected,key=lambda x:x[2]*x[3]*x[14])
            x,y,w,h=[float(v) for v in strongest[:4]]
            if not (0<=x<width and 0<=y<height and w>20 and h>20):
                continue
            centers.append(y+h*.5)
            lefts.append(y-h*.22)  # extra hair/speaker-motion margin
            bottoms.append(y+h*1.22) # extra beard/gesture margin
        # Require enough observations to make any crop decision. Otherwise
        # preserve the entire frame by fitting it into the camera band.
        if len(centers)<max(3,max_samples//3):
            return fallback
        desired=round(median(centers)-top*.48)
        desired=max(0,min(height-top,desired))
        margin=height*.025
        if min(lefts)-desired<margin or max(bottoms)-desired>top-margin:
            # Frame drift or unusually large head: do not risk cutting hair.
            return {**fallback,"face_detections":len(centers)}
        return {"camera_mode":"face-aware-crop","crop_y":desired,
                "face_detections":len(centers),
                "face_protection":"unobstructed-camera-band"}
    finally:
        capture.release()


def apply(source,output,beats,script=None,crf=18):
    source=Path(source);output=Path(output)
    if source.resolve()==output.resolve():
        raise ValueError("RAG output cannot overwrite the 42-effect video")
    info=video_info(source)
    valid=validate(beats,info["duration"],script)
    if not 8<=float(info["fps"])<=30.5 or info["frames"]<1:
        raise ValueError("Face-safe editorial pass requires CFR 8–30.5 fps")
    dims=geometry(info["width"],info["height"])
    top=dims["camera_bottom"]
    face=sample_face_crop(source,info["width"],info["height"],top)
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="swarag_face_safe_rag_") as temp:
        temp=Path(temp)
        inputs=["-i",str(source)]
        if face["camera_mode"]=="face-aware-crop":
            crop_y=face["crop_y"]
            # Source frame and new top camera area share the SAME width:
            # no stretching, artificial skin changes or lip sync alterations.
            transform=(f"crop={info['width']}:{top}:0:{crop_y},"
                       f"pad={info['width']}:{info['height']}:0:0:color=0x121B26")
        else:
            # Preserve all original camera pixels if face detection is
            # unavailable. Fit, NEVER warp the portrait into a short slot.
            transform=(f"scale=-2:{top}:flags=lanczos,"
                       f"pad={info['width']}:{info['height']}:(ow-iw)/2:0:color=0x121B26")
        graphs=["[0:v]setpts=PTS-STARTPTS,"+transform+",format=yuv420p[v0]"]
        previous="v0"
        for index,beat in enumerate(valid,1):
            png=temp/f"editorial_{index:02d}.png"
            draw_overlay(beat["kind"],info["width"],info["height"],ROOT/"fonts").save(png)
            inputs+=["-loop","1","-framerate",str(info["fps"]),"-i",str(png)]
            start,end=beat["start"],beat["end"]
            fade=min(.24,(end-start)/4.)
            graphs.append(f"[{index}:v]format=rgba,"
                          f"fade=t=in:st={start:.3f}:d={fade:.3f}:alpha=1,"
                          f"fade=t=out:st={end-fade:.3f}:d={fade:.3f}:alpha=1[a{index}]")
            graphs.append(f"[{previous}][a{index}]overlay=0:0:format=auto:"
                          f"enable='between(t,{start:.3f},{end:.3f})':shortest=1[v{index}]")
            previous=f"v{index}"
        cmd=["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",*inputs,
             "-filter_complex",";".join(graphs),"-map",f"[{previous}]",
             "-map","0:a:0","-c:v","libx264","-preset","veryfast",
             "-crf",str(crf),"-pix_fmt","yuv420p","-r",str(info["fps"]),
             "-frames:v",str(info["frames"]),"-c:a","copy",
             "-movflags","+faststart",str(output)]
        subprocess.run(cmd,check=True)
    if not output.is_file() or output.stat().st_size<4096:
        raise RuntimeError("Face-safe RAG video did not finish")
    return {
        "compositing":"original Swarag 42 effects + face-safe Executive Editorial V2 split",
        "layout_id":LAYOUT_ID,"face_safe_layout":True,
        "graphics_overlap_camera_pixels":False,
        "camera_region_y": [0,top],
        "graphics_region_y":[top,info["height"]],
        "camera":face,
        **coverage(valid,info["duration"],script),
        "output":str(output),"source_fps":str(info["fps"]),
        "source_frames":info["frames"],
        "creative_status":"REVIEW REQUIRED — full-motion face/crop and graphic QA mandatory",
    }
