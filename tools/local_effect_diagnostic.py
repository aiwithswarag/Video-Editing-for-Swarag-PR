"""Private 42-effect diagnostic using a SHORT SAMPLE OF ACTUAL camera footage.

This is not a finished edit. The 42 original effects and five named looks
run independently on a 2.25-second, 360x640/8fps clip of the user's authentic
source, so masking failures specific to a real person can at least be surfaced
for human review without rerendering 47 full videos.

Video, voice, gallery, stills and log remain under the local PRIVATE folder.
No external B-roll, cloud upload, invented metrics, or GitHub commit.
"""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from effect_catalog import read_registry
from render_effect_gallery import NAMED_VARIANTS
from effect_motion_review import create_motion_review
from effect_creative_review import report_for


def probe(source):
    p=subprocess.run(["ffprobe","-v","error","-show_entries",
       "format=duration:stream=codec_type,width,height",
       "-of","json",str(source)],capture_output=True,text=True,check=True,timeout=30)
    d=json.loads(p.stdout)
    streams=d.get("streams",[])
    v=[s for s in streams if s.get("codec_type")=="video"]
    a=[s for s in streams if s.get("codec_type")=="audio"]
    if len(v)!=1 or not a:
        raise ValueError("Diagnostic requires original MP4 with video and spoken audio")
    duration=float(d["format"]["duration"])
    if duration<2.5 or duration>7200:
        raise ValueError("Diagnostic needs at least 2.5 seconds of camera footage")
    if int(v[0]["height"])<=int(v[0]["width"]):
        raise ValueError("The Swarag 9:16 diagnostic requires portrait footage")
    return duration,v[0]


def sample_window(duration):
    """Pick real camera footage away from the intro/outro; always 2.25 sec."""
    if duration<2.5:
        raise ValueError("Source too short for proper audio/video sample")
    length=2.25
    return round(min(max(0.0,duration*.31),duration-length-.10),3),length


def report_from_gallery(folder,source_duration,source_start,original_dims):
    names,_,_=read_registry()
    expected=[*names,*[label for label,_,_ in NAMED_VARIANTS]]
    p=Path(folder)/"results.json"
    results=json.loads(p.read_text(encoding="utf8")) if p.is_file() else []
    by_name={r.get("effect"):r for r in results if isinstance(r,dict)}
    absent=[key for key in expected if key not in by_name]
    passed=[name for name in names if name in by_name and by_name[name].get("ok") and
            (by_name[name].get("media_qc") or {}).get("full_video_and_audio_decode")]
    failed=[name for name in names if name not in passed]
    variant_failed=[key for key in expected[42:] if key not in by_name or
                    not by_name[key].get("ok") or not
                    (by_name[key].get("media_qc") or {}).get("full_video_and_audio_decode")]
    low_change=[name for name in names if
                (by_name.get(name,{}).get("preview_qc") or {}).get("visible_change_detected_in_sample") is False]
    per_effect_review_flags = {
        label: list((by_name.get(label, {}).get('preview_qc') or {}).get('warnings') or [])
        for label in expected
        if (by_name.get(label, {}).get('preview_qc') or {}).get('warnings')
    }
    return {
        "schema_version":1,"purpose":"PRIVATE LOCAL DIAGNOSTIC — NOT A PUBLISHABLE EDIT",
        "presentation":"Swarag executive illustrative examples (not original effect default UI)",
        "original_effect_implementations_tested":True,
        "illustrative_fixture_content":True,
        "registered_effects":len(names),
        "tested_effects":len([n for n in names if n in by_name]),
        "technically_passed_effects":len(passed),
        "technically_failed_or_unverified_effects":failed,
        "named_looks":len(NAMED_VARIANTS),
        "named_looks_failed_or_unverified":variant_failed,
        "missing_results":absent,
        "source_duration_s":round(source_duration,3),
        "sample_start_s":source_start,
        "sample_length_s":2.25,
        "test_resolution":"360x640/8fps previews; 240px motion clips",
        "source_dimensions":{"width":int(original_dims["width"]),
                             "height":int(original_dims["height"])},
        "no_visible_change_in_one_sample_frame":low_change,
        "per_effect_review_flags":per_effect_review_flags,
        "human_creative_review_focus":report_for(expected),
        "technical_status":("ALL_42_SHORT_SAMPLE_DECODE_PASS" if
            len(passed)==42 and not variant_failed and not absent else
            "FAIL_OR_INCOMPLETE — SEE EFFECT-BY-EFFECT RESULTS"),
        "creative_status":"REVIEW REQUIRED — real moving face/hair, phone typography, content, hand masking and full 1080p still unapproved",
        "limitations":[
            "Only 2.25 seconds of real camera footage are sampled",
            "No automatic speech/caption alignment or cinematic artistic approval",
            "All on-screen numbers, charts and concepts are illustrative gallery fixtures, never production claims",
            "Executive palette and options are enabled; tests run all original effect FUNCTIONS but not every unstyled original default",
            "Technical decode/visual change on a small sample cannot certify a complete 1080p video"
        ]
    }


def make_review_sheet(gallery,destination):
    """Private original-camera contact sheet, including failed/missing effect slots."""
    names,_,_=read_registry()
    labels=names+[name for name,_,_ in NAMED_VARIANTS]
    gallery=Path(gallery)
    destination=Path(destination)
    destination.parent.mkdir(parents=True,exist_ok=True)
    columns=6
    cell_width=205
    cell_height=391
    rows=(len(labels)+columns-1)//columns
    canvas=Image.new("RGB",(columns*cell_width,rows*cell_height),(20,32,44))
    dr=ImageDraw.Draw(canvas)
    for i,name in enumerate(labels):
        x=(i%columns)*cell_width
        y=(i//columns)*cell_height
        image_path=gallery/(name+".png")
        if image_path.is_file():
            try:
                with Image.open(image_path) as file:
                    image=file.convert("RGB")
                image.thumbnail((cell_width-12,cell_height-40))
                canvas.paste(image,(x+(cell_width-image.width)//2,y+30))
            except (OSError,ValueError):
                dr.text((x+6,y+45),"FAILED TO DECODE",fill=(227,151,126))
        else:
            dr.text((x+6,y+45),"MISSING PREVIEW",fill=(227,151,126))
        dr.text((x+6,y+7),name[:27],fill=(242,239,233))
    canvas.save(destination,quality=88)
    return destination


def run(source,output,*,only=None):
    source=Path(source)
    if not source.is_file():raise FileNotFoundError(source)
    output=Path(output)
    output.mkdir(parents=True,exist_ok=True)
    duration,stream=probe(source)
    start,length=sample_window(duration)
    short=output/"private_source_excerpt.mp4"
    gallery=output/"effect-gallery"
    review=output/"review"
    # This is a PRIVATE ephemeral excerpt of the user's actual source.
    # Original full-resolution video and all outputs remain untouched.
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-nostdin",
         "-y","-ss",str(start),"-i",str(source),"-t",str(length),
         "-map","0:v:0","-map","0:a:0",
         "-vf","fps=8,scale=360:640:flags=lanczos,format=yuv420p",
         "-c:v","libx264","-preset","veryfast","-crf","20",
         "-c:a","aac","-b:a","128k","-movflags","+faststart",str(short)]
    subprocess.run(cmd,check=True,timeout=120)
    command=[sys.executable,str(ROOT/"tools"/"render_effect_gallery.py"),
        "--video",str(short),"--output-dir",str(gallery),"--width","360",
        "--at","0.95","--timeout","120","--brand","executive",
        "--illustrative-executive-examples",
        "--include-variants","--render-motion"]
    if only:
        for name in only:command+=["--only",name]
    proc=subprocess.run(command,check=False,cwd=ROOT)
    report=report_from_gallery(gallery,duration,start,stream)
    report_path=output/"effect-health-report.json"
    report["review_artifact_status"]="PENDING"
    # A gallery, ZIP or thumbnail failure must not erase 42-effect evidence.
    report_path.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    if not only:
        # Even if one original effect crashes, show a genuine partial review
        # sheet with explicit missing/failed slots. Don't hide failed visuals.
        try:
            make_review_sheet(gallery,review/"all-47-effects.jpg")
            effect_names,_,_=read_registry()
            labels=effect_names+[name for name,_,_ in NAMED_VARIANTS]
            report["motion_review"]=create_motion_review(gallery,review,labels)
            report["review_artifact_status"]=("READY" if
                report["motion_review"]["status"]=="MOTION_SAMPLES_AVAILABLE" else "INCOMPLETE")
        except Exception as exc:
            # Do not leak private file paths, user audio or traces via the UI.
            report["review_artifact_status"]="FAILED"
            report["review_artifact_error_type"]=type(exc).__name__
            report["motion_review"]={"status":"UNAVAILABLE","clips_packaged":0,
                                    "creative_status":"REVIEW REQUIRED"}
    if only:
        report["review_artifact_status"]="NOT_REQUESTED_SUBSET"
        report["purpose"]="LIMITED INTERNAL SUBSET TEST — NOT ALL 42 EFFECTS"
        report["technical_status"]="INCOMPLETE_SUBSET" if proc.returncode==0 else "FAIL_OR_INCOMPLETE"
    report_path.write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    if not only and proc.returncode==0:
        try:
            subprocess.run([sys.executable,str(ROOT/"tools"/"summarize_gallery.py"),
                            str(gallery),str(review)],check=True,timeout=80)
        except (subprocess.CalledProcessError,subprocess.TimeoutExpired,OSError) as exc:
            report["supplementary_gallery_status"]="FAILED"
            report["supplementary_gallery_error_type"]=type(exc).__name__
            report_path.write_text(
                json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    return report



def recover_existing(source, output):
    """Rebuild private review artifacts from a previous completed result manifest.

    Does not extract camera footage or execute any of the 47 effect renders.
    Fails closed when the manifest is absent; no fabricated PASS results.
    """
    source, output = Path(source), Path(output)
    if not source.is_file():
        raise FileNotFoundError("Original locally stored video unavailable")
    gallery=output/"effect-gallery"
    if not (gallery/"results.json").is_file():
        raise ValueError("No prior completed 47-effect results manifest exists")
    duration,stream=probe(source)
    start,_=sample_window(duration)
    report=report_from_gallery(gallery,duration,start,stream)
    report["recovered_without_rerender"]=True
    report["review_artifact_status"]="PENDING"
    target=output/"effect-health-report.json"
    output.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    try:
        review=output/"review"
        make_review_sheet(gallery,review/"all-47-effects.jpg")
        effect_names,_,_=read_registry()
        labels=effect_names+[label for label,_,_ in NAMED_VARIANTS]
        report["motion_review"]=create_motion_review(gallery,review,labels)
        report["review_artifact_status"]=(
            "READY" if report["motion_review"]["status"]=="MOTION_SAMPLES_AVAILABLE"
            else "INCOMPLETE"
        )
    except Exception as exc:
        report["review_artifact_status"]="FAILED"
        report["review_artifact_error_type"]=type(exc).__name__
        report["motion_review"]={"status":"UNAVAILABLE","clips_packaged":0,
                                 "creative_status":"REVIEW REQUIRED"}
    target.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    return report


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--video",required=True)
    ap.add_argument("--output-dir",required=True)
    ap.add_argument("--only",action="append",default=[])
    ap.add_argument("--recover-existing",action="store_true",
                    help="Reassemble only local saved effect results (no effect rendering)")
    args=ap.parse_args()
    report=(recover_existing(args.video,args.output_dir) if args.recover_existing
            else run(args.video,args.output_dir,only=args.only))
    print(json.dumps({
        "technical_status":report["technical_status"],
        "effects_passed":report["technically_passed_effects"],
        "effects_missing_or_failed":report["technically_failed_or_unverified_effects"],
        "creative_status":report["creative_status"]
    },ensure_ascii=False),flush=True)
    if report["technical_status"] not in ("ALL_42_SHORT_SAMPLE_DECODE_PASS","INCOMPLETE_SUBSET"):
        raise SystemExit(1)


if __name__=="__main__":main()
