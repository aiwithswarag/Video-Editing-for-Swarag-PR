"""Strict objective media checks for Swarag's 42 independent effect renders.

A technical pass proves decode/stream integrity, NOT realistic person masking,
safe typography, accurate speech timing, or aesthetic approval.
"""
from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageChops, ImageStat


def preview_evidence(path, width, expected_height=None, baseline=None):
    """Verify an actual decoded PNG, report approximate visible pixel change."""
    source=Path(path)
    if not source.is_file() or source.stat().st_size<1000:
        raise ValueError("Missing or tiny preview PNG")
    try:
        with Image.open(source) as opened:
            opened.verify()
        with Image.open(source) as opened:
            img=opened.convert("RGB")
    except (OSError,ValueError) as exc:
        raise ValueError("Preview PNG does not decode: "+str(exc)) from exc
    if img.width!=width or (expected_height is not None and img.height!=expected_height):
        raise ValueError(f"Wrong preview dimensions: {img.width}x{img.height}")
    if img.height<120 or img.width<120:
        raise ValueError("Preview has implausibly small dimensions")
    gray=img.convert("L")
    stat=ImageStat.Stat(gray)
    luma=float(stat.mean[0])
    deviation=float(stat.stddev[0])
    if not all(math.isfinite(v) for v in (luma,deviation)):
        raise ValueError("Invalid brightness statistics")
    # Some effects intentionally fade through white/black; use a review flag
    # rather than silently certifying that every image is beautiful.
    warnings=[]
    if deviation<1.25:warnings.append("LOW_VARIANCE_PREVIEW — inspect actual frame")
    result={"width":img.width,"height":img.height,
            "mean_luma":round(luma,3),"luma_stdev":round(deviation,3),
            "warnings":warnings}
    if baseline is not None:
        with Image.open(baseline) as frame:
            if frame.size!=img.size:
                raise ValueError("Baseline and rendered image dimensions differ")
            delta=ImageChops.difference(img,frame.convert("RGB"))
            change=float(sum(ImageStat.Stat(delta).mean)/3)
            result["mean_abs_change_vs_source_rgb"]=round(change,3)
            result["visible_change_detected_in_sample"]=change>1.0
            if change<=1.0:
                warnings.append("NO_CLEAR_VISIBLE_CHANGE_IN_SAMPLE — effect may be subtle or require a real person; review manually")
    return result


def motion_evidence(path, width, expected_height, *, min_frames=10):
    """Use FFmpeg to decode every frame/audio packet, not just read container metadata."""
    path=Path(path)
    if not path.is_file() or path.stat().st_size<2000:
        raise ValueError("Missing or tiny MP4 output")
    probe=subprocess.run(
        ["ffprobe","-v","error","-count_frames",
         "-show_entries","stream=codec_type,codec_name,width,height,nb_read_frames,avg_frame_rate:"
                         "format=duration",
         "-of","json",str(path)],
        capture_output=True,text=True,check=True,timeout=60)
    data=json.loads(probe.stdout)
    videos=[s for s in data.get("streams",[]) if s.get("codec_type")=="video"]
    audios=[s for s in data.get("streams",[]) if s.get("codec_type")=="audio"]
    if len(videos)!=1 or not audios:
        raise ValueError("Clip must have one video track and at least one audio track")
    v=videos[0]
    if (int(v.get("width",0))!=width or int(v.get("height",0))!=expected_height):
        raise ValueError(f"Wrong motion dimensions: {v.get('width')}x{v.get('height')}")
    frames=int(v.get("nb_read_frames","0") or "0")
    if frames<min_frames:
        raise ValueError(f"Too few decodable frames: {frames} vs required {min_frames}")
    dur=float(data.get("format",{}).get("duration",0))
    if not math.isfinite(dur) or dur<1.3:
        raise ValueError(f"Motion duration too short or invalid: {dur}")
    # ffprobe can successfully read headers on a corrupt file. Decode the
    # complete MP4 including audio and fail on FFmpeg decoding errors.
    decoded=subprocess.run(
        ["ffmpeg","-hide_banner","-loglevel","error","-xerror",
         "-i",str(path),"-map","0:v:0","-map","0:a:0",
         "-f","null","-"],
        capture_output=True,text=True,timeout=120)
    if decoded.returncode!=0:
        raise ValueError("Full motion/audio decode failed: "+decoded.stderr[-400:])
    return {
        "decoded_frames":frames,"duration_seconds":round(dur,3),
        "width":int(v["width"]),"height":int(v["height"]),
        "video_codec":v.get("codec_name"),"audio_streams":len(audios),
        "audio_codec":audios[0].get("codec_name"),
        "full_video_and_audio_decode":True,
    }
