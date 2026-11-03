"""Private motion-review artifacts for the 42 original effects and five looks.

Three separated frames per *actual rendered MP4* are placed in one contact
sheet, and the original short clips are bundled for real playback. Neither
artifact is a professional/face-mask certification. Never publish user media
or its previews to GitHub or cloud storage.
"""
from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZIP_STORED, ZipFile

from PIL import Image, ImageDraw

SAMPLE_RATIOS = (0.15, 0.50, 0.85)


def sampled_frames(path, ratios=SAMPLE_RATIOS):
    """Read several frames from the real rendered clip, not its PNG thumbnail."""
    import cv2
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise ValueError("Motion clip cannot be opened")
    frames = []
    try:
        total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        if total < 3:
            raise ValueError("Fewer than three frames in motion clip")
        for ratio in ratios:
            index = min(total - 1, max(0, round((total - 1) * ratio)))
            capture.set(cv2.CAP_PROP_POS_FRAMES, index)
            success, frame = capture.read()
            if not success or frame is None:
                raise ValueError("Motion clip has an unreadable sampled frame")
            frames.append(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
    finally:
        capture.release()
    return frames


def create_motion_review(gallery, destination, labels):
    """Build the private 3-frame/47-effect sheet and playable clips ZIP.

    Returns review evidence, not a creative PASS. Missing/unreadable clips are
    explicit failures rather than empty thumbnails treated as success.
    """
    gallery, destination = Path(gallery), Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    labels = list(labels)
    cols, tile_w, tile_h = 6, 382, 265
    rows = (len(labels) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tile_w, rows * tile_h), (18, 27, 38))
    draw = ImageDraw.Draw(sheet)
    results = []
    archive_path = destination / "all-47-motion-clips.zip"
    with ZipFile(archive_path, "w", compression=ZIP_STORED) as archive:
        for i, label in enumerate(labels):
            x, y = (i % cols) * tile_w, (i // cols) * tile_h
            draw.text((x + 7, y + 7), label[:40], fill=(242, 239, 233))
            clip = gallery / (label + ".mp4")
            if not clip.is_file() or clip.stat().st_size < 2000:
                results.append({"effect": label, "status": "MISSING_MOTION_CLIP"})
                draw.text((x + 7, y + 44), "MISSING MOTION CLIP", fill=(227, 151, 126))
                continue
            try:
                frames = sampled_frames(clip)
                archive.write(clip, arcname="clips/" + label + ".mp4")
                for j, frame in enumerate(frames):
                    frame.thumbnail((116, 214))
                    offset = x + 7 + 124 * j
                    sheet.paste(frame, (offset + (116 - frame.width) // 2, y + 32))
                results.append({"effect": label, "status": "FRAMES_SAMPLED",
                                "frame_samples": len(frames)})
            except (OSError, ValueError) as exc:
                results.append({"effect": label, "status": "UNREADABLE_MOTION_CLIP",
                                "error_type": type(exc).__name__})
                draw.text((x + 7, y + 44), "UNREADABLE MOTION", fill=(227, 151, 126))
        manifest = {
            "purpose": "PRIVATE MOTION REVIEW — NOT CREATIVE APPROVAL",
            "sampling": "Three separated actual MP4 frames per effect plus playable clips",
            "sample_ratios": list(SAMPLE_RATIOS),
            "effects": results,
        }
        archive.writestr("review-manifest.json",
                         json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    sheet_path = destination / "all-47-motion-review.jpg"
    sheet.save(sheet_path, quality=88)
    misses = [item["effect"] for item in results if item["status"] != "FRAMES_SAMPLED"]
    return {
        "status": "MOTION_SAMPLES_AVAILABLE" if not misses else "INCOMPLETE_MOTION_SAMPLES",
        "clips_packaged": len(results) - len(misses),
        "expected_clips": len(labels),
        "missing_or_unreadable_clips": misses,
        "frames_per_clip": 3,
        "review_sheet": sheet_path.name,
        "playable_clips_archive": archive_path.name,
        "creative_status": "REVIEW REQUIRED — play actual MP4 clips; inspect hair, face, hands, typography and motion",
    }
