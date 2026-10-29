#!/usr/bin/env python3
"""Segmented renderer for the 42-effect engine: composite active windows only.

Unaffected sections are fast FFmpeg encodes. All final audio comes directly
from the original input. This avoids the memory and CPU overhead of sending
untouched frames through the face tracking and effects pipeline.
"""
import argparse
import hashlib
from contextlib import nullcontext
from fractions import Fraction
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from plan_validation import validate_plan


def intervals(plan, duration):
    """Cover a video with contiguous intervals; merge overlapping effect windows."""
    windows = []
    for item in sorted(plan, key=lambda e: e["start"]):
        start, end = item["start"], min(item["end"], duration)
        if start >= duration:
            continue
        if windows and start <= windows[-1][1] + 1e-7:
            windows[-1] = (windows[-1][0], max(windows[-1][1], end))
        else:
            windows.append((start, end))
    pieces, cursor = [], 0.0
    for start, end in windows:
        if start > cursor + 1e-7:
            pieces.append((cursor, start, []))
        subset = []
        for item in plan:  # maintain the user's effect/layer order
            if item["start"] < end and item["end"] > start:
                clip = dict(item)
                clip["start"] = round(max(item["start"], start) - start, 6)
                clip["end"] = round(min(item["end"], end) - start, 6)
                subset.append(clip)
        pieces.append((start, end, subset))
        cursor = end
    if cursor < duration - 1e-7:
        pieces.append((cursor, duration, []))
    return pieces


def run(command):
    subprocess.run(command, check=True)


def probe(path):
    raw = subprocess.run([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height:format=duration",
        "-of", "json", str(path)], capture_output=True, text=True, check=True).stdout
    media = json.loads(raw)
    stream = media["streams"][0]
    return float(media["format"]["duration"]), int(stream["width"]), int(stream["height"])


def resolve_fps(value, source):
    """Choose the actual source frame rate, retaining fractional values (e.g. 59/2)."""
    if value == "auto":
        record = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=avg_frame_rate", "-of", "default=nw=1:nk=1",
            str(source)], capture_output=True, text=True, check=True)
        value = record.stdout.strip()
    try:
        rate = Fraction(value).limit_denominator(1001000)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError(f"Unsupported FPS value: {value}") from exc
    if not 8 <= float(rate) <= 30.5:
        raise ValueError("This 42-effect engine supports 8–30.5 fps for full-quality effect rendering. Normalize higher-FPS footage explicitly before editing.")
    return f"{rate.numerator}/{rate.denominator}"


def frame_count(path):
    raw = subprocess.run(["ffprobe","-v","error","-select_streams","v:0",
        "-show_entries","stream=nb_frames","-of","default=nw=1:nk=1",str(path)],
        capture_output=True,text=True,check=True).stdout.strip()
    if not raw.isdigit() or int(raw)<1:
        raise ValueError("Exact source-frame metadata required; normalize to CFR MP4 first")
    return int(raw)


def frame_segments(plan, total_frames, rate):
    """Snap every edit boundary to the source frame grid, with complete frame coverage."""
    duration=float(Fraction(total_frames,1)/rate)
    legacy=intervals(plan,duration)
    parts=[];cursor=0
    for _,end,_ in legacy:
        stop=min(total_frames,max(cursor,round(Fraction(str(end))*rate)))
        if stop<=cursor:continue
        edits=[]
        for item in plan:
            fx_start=round(Fraction(str(item["start"]))*rate)
            fx_end=round(Fraction(str(item["end"]))*rate)
            lo=max(cursor,fx_start);hi=min(stop,fx_end)
            if hi>lo:
                edit={**item,
                      "start":round(float(Fraction(lo-cursor,1)/rate),6),
                      "end":round(float(Fraction(hi-cursor,1)/rate),6)}
                edits.append(edit)
        parts.append((cursor,stop-cursor,edits))
        cursor=stop
    if cursor<total_frames:
        parts.append((cursor,total_frames-cursor,[]))
    if sum(part[1] for part in parts)!=total_frames:
        raise RuntimeError("Frame grid did not cover entire source video")
    return parts


def usable_segment(path,frames,width,height,fps):
    try:
        if not path.is_file() or path.stat().st_size<1024 or frame_count(path)!=frames:
            return False
        _,w,h=probe(path)
        return (w,h)==(width,height) and resolve_fps("auto",path)==fps
    except (ValueError,FileNotFoundError,subprocess.CalledProcessError,KeyError):
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("plan", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--width", type=int, default=540,
                        help="Short side of output in even pixels")
    parser.add_argument("--fps", default="auto",
                        help="Output rate: auto (source rate), 30, 29.5 or 30000/1001; effect engine supports 8–30.5 fps")
    parser.add_argument("--brand", choices=["executive", "none"], default="executive")
    parser.add_argument("--crf", type=int, default=19)
    parser.add_argument("--cache-dir",type=Path,help="Optional reusable effect-segment directory; safe to rerun after interruption")
    args = parser.parse_args()
    if not args.input.is_file():
        parser.error("Input file is missing")
    if args.input.resolve() == args.output.resolve():
        parser.error("Refusing to overwrite the original video")
    if args.output.suffix.lower() != ".mp4":
        parser.error("Output must be MP4")
    if not 240 <= args.width <= 2160 or args.width % 2:
        parser.error("--width must be even, between 240 and 2160")
    try:
        fps = resolve_fps(args.fps, args.input)
    except (ValueError, subprocess.CalledProcessError) as exc:
        parser.error(str(exc))
    if not 0 <= args.crf <= 51:
        parser.error("--crf must be 0-51")

    duration, sw, sh = probe(args.input)
    plan = validate_plan(json.loads(args.plan.read_text(encoding="utf8")),
                         duration=duration)
    if sw <= sh:
        w, h = args.width, round(args.width * sh / sw / 2) * 2
    else:
        h, w = args.width, round(args.width * sw / sh / 2) * 2
    rate=Fraction(fps)
    total_frames=frame_count(args.input)
    video_seconds=float(Fraction(total_frames,1)/rate)
    if abs(video_seconds-duration)>.13:
        raise ValueError("Video and container duration disagree by >130ms; normalize to CFR source")
    segments=frame_segments(plan,total_frames,rate)
    print(f"Segments: {len(segments)}, active: {sum(bool(e) for _, _, e in segments)}, exact frames: {total_frames}", flush=True)
    if args.cache_dir:
        cache=args.cache_dir.resolve()
        if cache==args.input.resolve() or cache==args.output.resolve():
            raise ValueError("Cache directory must not replace source or destination")
        cache.mkdir(parents=True,exist_ok=True)
        stat=args.input.stat()
        context={"input":str(args.input.resolve()),"size":stat.st_size,"mtime_ns":stat.st_mtime_ns,
                 "plan":plan,"width":w,"height":h,"fps":fps,"crf":args.crf,"brand":args.brand}
        digest=hashlib.sha256(json.dumps(context,sort_keys=True).encode()).hexdigest()
        manifest=cache/"effect_cache_manifest.json"
        if manifest.exists():
            if json.loads(manifest.read_text())["sha256"]!=digest:
                raise ValueError("Cached effect sections belong to a different source/plan/settings")
        else:
            if any(cache.glob("input_*.mp4")) or any(cache.glob("edited_*.mp4")):
                raise ValueError("Unmanaged effect sections found; use an empty cache directory")
            manifest.write_text(json.dumps({"sha256":digest,"context":context},indent=2)+"\n")
        manager=nullcontext(str(cache))
    else:
        manager=tempfile.TemporaryDirectory(prefix="swarag_segments_")
    with manager as temp:
        folder = Path(temp)
        chunks = []
        for i, (start_frame, count, effects) in enumerate(segments):
            src = folder / f"input_{i:02d}.mp4"
            dst = folder / f"edited_{i:02d}.mp4"
            start_time=float(Fraction(start_frame,1)/rate)
            end_time=float(Fraction(start_frame+count,1)/rate)
            if not usable_segment(src,count,w,h,fps):
                run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                     "-ss", f"{start_time:.9f}", "-i", str(args.input),
                     "-vf", f"fps={fps},scale={w}:{h}:flags=lanczos",
                     "-frames:v",str(count),"-an",
                     "-c:v", "libx264", "-preset", "veryfast", "-crf", str(args.crf),
                     "-pix_fmt", "yuv420p", str(src)])
            if not usable_segment(src,count,w,h,fps):
                raise RuntimeError(f"Input segment {i} failed exact media QA")
            if effects:
                plan_path = folder / f"plan_{i:02d}.json"
                plan_path.write_text(json.dumps({"effects": effects}), encoding="utf8")
                if not usable_segment(dst,count,w,h,fps):
                    run([sys.executable, str(ROOT / "scripts/video_director.py"),
                         "render", str(src), str(plan_path), str(dst),
                         "--width", str(args.width), "--brand", args.brand])
                if not usable_segment(dst,count,w,h,fps):
                    raise RuntimeError(f"42-effect engine changed segment {i} frame count, FPS or dimensions")
                chunks.append(dst)
            else:
                chunks.append(src)
            print(f"{i+1}/{len(segments)}: {start_time:.2f}-{end_time:.2f}s; {count} frames; {len(effects)} effects", flush=True)

        sources = []
        for part in chunks:
            sources += ["-i", str(part)]
        sources += ["-i", str(args.input)]
        filter_head = "".join(f"[{i}:v]setsar=1,setpts=PTS-STARTPTS[v{i}];"
                              for i in range(len(chunks)))
        filter_tail = "".join(f"[v{i}]" for i in range(len(chunks)))
        filter_graph = (filter_head + filter_tail +
                        f"concat=n={len(chunks)}:v=1:a=0,format=yuv420p[v]")
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
             *sources, "-filter_complex", filter_graph,
             "-map", "[v]", "-map", f"{len(chunks)}:a:0?",
             "-c:v", "libx264", "-preset", "veryfast",
             "-crf", str(args.crf), "-r", fps, "-frames:v",str(total_frames),
             "-c:a", "copy", "-movflags", "+faststart",str(args.output)])
    if not args.output.is_file() or args.output.stat().st_size < 1024:
        raise RuntimeError("Renderer did not produce a valid output file")
    if frame_count(args.output)!=total_frames:
        raise RuntimeError("Final frame count differs from exact source frame count")
    print(f"Saved: {args.output}; verified {total_frames} frames at {fps} fps")


if __name__ == "__main__":
    main()
