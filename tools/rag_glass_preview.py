"""Private pre-render sample using EXACT original Swarag glass-widgets effect.

Unlike the retired Pillow split preview, this calls scripts/fx.py --still on
short excerpts of the actual uploaded MP4. The resulting person-aware
compositing matches the same MediaPipe implementation as final production.
No full edit or artificial fallback is created.
"""
from __future__ import annotations
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from PIL import Image

from rag_glass_plan import LAYOUT_ID,cue
from rag_storyboard import validate

ROOT=Path(__file__).resolve().parents[1]

def _probe(source):
    x=subprocess.run(["ffprobe","-v","error","-show_entries",
        "format=duration:stream=width,height,avg_frame_rate",
        "-select_streams","v:0","-of","json",str(source)],
        capture_output=True,text=True,check=True)
    record=json.loads(x.stdout)
    video=record["streams"][0]
    return {"duration":float(record["format"]["duration"]),
            "width":int(video["width"]),"height":int(video["height"])}

def preview_contact_sheet(source,storyboard,thumb_width=360):
    """Render three authentic glass-widgets stills from source at edited times."""
    source=Path(source)
    if not source.is_file():raise FileNotFoundError(source)
    if not 240<=thumb_width<=720 or thumb_width%2:
        raise ValueError("Preview width must be even, between 240 and 720")
    info=_probe(source)
    if info["width"]*16 !=info["height"]*9:
        raise ValueError("Original input must be portrait 9:16")
    valid=validate(storyboard,info["duration"])
    chosen=[]
    for kind in ("policies","rag-flow","check-3"):
        stage=next((v for v in valid if v["kind"]==kind),None)
        if stage is None:raise ValueError(f"Missing RAG preview stage: {kind}")
        chosen.append(stage)
    images=[]
    with tempfile.TemporaryDirectory(prefix="swarag_private_glass_preview_") as d:
        work=Path(d)
        for i,beat in enumerate(chosen):
            # Source data is extracted locally; no network upload and no user
            # content is passed to GitHub. Use a short moment so real depth
            # detection can inspect frames without tracking all 1512 frames.
            midpoint=(beat["start"]+beat["end"])/2
            begin=max(0.,min(info["duration"]-1.15,midpoint-.58))
            duration=min(1.15,info["duration"]-begin)
            clip=work/f"part_{i}.mp4"
            still=work/f"scene_{i}.png"
            plan_path=work/f"plan_{i}.json"
            fx=cue(beat)
            fx["start"]=0.
            fx["end"]=duration
            plan_path.write_text(json.dumps({"effects":[fx]}),encoding="utf8")
            subprocess.run(["ffmpeg","-hide_banner","-loglevel","error",
                "-nostdin","-y","-ss",f"{begin:.3f}","-i",str(source),
                "-t",f"{duration:.3f}","-map","0:v:0","-an",
                "-c:v","libx264","-preset","ultrafast","-crf","21",
                "-pix_fmt","yuv420p",str(clip)],check=True)
            # This is the original engine, *not* a lookalike Pillow drawing.
            subprocess.run([sys.executable,str(ROOT/"scripts"/"fx.py"),
                "--plan",str(plan_path),str(clip),str(still),
                "--width",str(thumb_width),"--still","0.6"],
                cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
            img=Image.open(still).convert("RGB")
            out_h=round(thumb_width*16/9)
            if img.size!=(thumb_width,out_h):
                raise RuntimeError("Authentic glass preview has unexpected dimensions")
            images.append(img.copy())
    sheet=Image.new("RGB",(thumb_width*len(images),images[0].height),(18,27,38))
    for i,img in enumerate(images):
        sheet.paste(img,(i*thumb_width,0))
    return sheet,{
        "layout_id":LAYOUT_ID,
        "preview_engine":"scripts/fx.py",
        "original_effect":"glass-widgets",
        "look":"rag-evidence",
        "frame_kinds":[stage["kind"] for stage in chosen],
        "source_fidelity":"real original-camera footage with original MediaPipe person-depth protection",
        "full_motion_status":"NOT REVIEWED — three true-effect stills only",
        "creative_status":"PREVIEW ONLY — approval and full MP4 review required",
    }


def preview_motion_clip(source, storyboard, output, *, width=540, fps=15):
    """Three short REAL moving RAG glass samples, with original spoken audio.

    This is a motion/subject-mask approval aid, not the 50-second film, and
    540-pixel / 15fps previews never certify native 1080p detail or final FPS.
    All extracts and rendered media remain under the caller's private folder.
    """
    source, output = Path(source), Path(output)
    if not source.is_file():
        raise FileNotFoundError(source)
    if not 360 <= width <= 720 or width % 2:
        raise ValueError("Motion preview width must be even, 360..720")
    if not 8 <= fps <= 30:
        raise ValueError("Motion preview FPS must be 8..30")
    if source.resolve() == output.resolve():
        raise ValueError("Refusing to overwrite original footage")
    info = _probe(source)
    if info["width"] * 16 != info["height"] * 9:
        raise ValueError("Motion preview source must be portrait 9:16")
    stages = validate(storyboard, info["duration"])
    selected = [next(beat for beat in stages if beat["kind"] == kind)
                for kind in ("policies", "rag-flow", "check-3")]
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="swarag_private_rag_motion_") as tmp:
        work = Path(tmp)
        rendered = []
        for index, beat in enumerate(selected):
            span = beat["end"] - beat["start"]
            if span < 0.80:
                raise ValueError("RAG stage too short for a meaningful moving preview")
            length = min(1.50, span - 0.02)
            begin = round(beat["start"] + (span - length) / 2, 3)
            source_clip = work / ("camera_%d.mp4" % index)
            output_clip = work / ("glass_%d.mp4" % index)
            plan_file = work / ("plan_%d.json" % index)
            effect = cue(beat)
            effect["start"], effect["end"] = 0.0, length
            plan_file.write_text(json.dumps({"effects": [effect]}), encoding="utf8")
            subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
                "-y", "-ss", str(begin), "-i", str(source), "-t", str(length),
                "-map", "0:v:0", "-map", "0:a:0",
                "-vf", f"fps={fps},scale={width}:{round(width * 16 / 9)}:flags=lanczos,format=yuv420p",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
                "-c:a", "aac", "-b:a", "128k", str(source_clip),
            ], check=True, timeout=180)
            subprocess.run([
                sys.executable, str(ROOT / "scripts" / "video_director.py"),
                "render", str(source_clip), str(plan_file), str(output_clip),
                "--width", str(width), "--brand", "none",
            ], cwd=ROOT, check=True, timeout=240)
            if not output_clip.is_file() or output_clip.stat().st_size < 4096:
                raise RuntimeError("Original RAG glass renderer produced no motion clip")
            rendered.append(output_clip)
        concatenation = work / "preview-list.txt"
        concatenation.write_text(
            "".join("file '" + clip.name + "'\n" for clip in rendered),
            encoding="utf8",
        )
        subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
            "-y", "-f", "concat", "-safe", "0", "-i", str(concatenation),
            "-c", "copy", "-movflags", "+faststart", str(output),
        ], cwd=work, check=True, timeout=120)
    if not output.is_file() or output.stat().st_size < 4096:
        raise RuntimeError("No playable RAG motion preview was produced")
    return {
        "preview_engine": "original scripts/fx.py via scripts/video_director.py",
        "original_effect": "glass-widgets",
        "look": "rag-evidence",
        "stage_kinds": [stage["kind"] for stage in selected],
        "preview_resolution": f"{width}x{round(width * 16 / 9)}",
        "preview_fps": fps,
        "original_speech_audio": True,
        "creative_status": "REVIEW REQUIRED — this is three short moving samples, not final motion approval",
    }
