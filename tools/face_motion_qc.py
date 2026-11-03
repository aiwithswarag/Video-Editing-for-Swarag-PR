"""Conservative face-region change warnings for private RAG motion previews.

Compares exactly corresponding decoded frames BEFORE and AFTER the original
subject-masked glass effect. Flags large face changes; does NOT establish
professional masking quality, identity protection, or caption legibility.
The YuNet detector runs locally. No user pixels or identifiers are exported.
"""
from __future__ import annotations

from pathlib import Path

SAMPLE_RATIOS = (0.18, 0.50, 0.82)


def inspect_face_change(source, rendered, model=None, sample_ratios=SAMPLE_RATIOS):
    import cv2
    import numpy as np

    source, rendered = Path(source), Path(rendered)
    model = Path(model or Path(__file__).resolve().parents[1] / "models" / "yunet.onnx")
    if not source.is_file() or not rendered.is_file():
        raise FileNotFoundError("Both before/after motion clips are required")
    if not model.is_file():
        return {"status": "UNVERIFIED_FACE_MODEL_MISSING", "sampled_frames": 0,
                "face_detections": 0, "possible_overlays": 0}
    before = cv2.VideoCapture(str(source))
    after = cv2.VideoCapture(str(rendered))
    if not before.isOpened() or not after.isOpened():
        before.release()
        after.release()
        raise ValueError("Source/rendered motion clips could not be opened")
    measurements = []
    try:
        width = int(before.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(before.get(cv2.CAP_PROP_FRAME_HEIGHT))
        rw = int(after.get(cv2.CAP_PROP_FRAME_WIDTH))
        rh = int(after.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if width != rw or height != rh or width < 120 or height < 120:
            raise ValueError("Before/after frame dimensions do not match")
        total_before = int(before.get(cv2.CAP_PROP_FRAME_COUNT))
        total_after = int(after.get(cv2.CAP_PROP_FRAME_COUNT))
        if min(total_before, total_after) < 4 or abs(total_before-total_after) > 1:
            raise ValueError("Before/after motion frame counts differ")
        detector = cv2.FaceDetectorYN.create(str(model), "", (width, height), 0.68, 0.3, 20)
        for fraction in sample_ratios:
            idx = min(total_before-1, total_after-1,
                      max(0, round((min(total_before, total_after)-1) * fraction)))
            before.set(cv2.CAP_PROP_POS_FRAMES, idx)
            after.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok_before, frame_before = before.read()
            ok_after, frame_after = after.read()
            if not ok_before or not ok_after:
                raise ValueError("Could not decode corresponding before/after frames")
            _, faces = detector.detect(frame_before)
            if faces is None or not len(faces):
                measurements.append({"sample_ratio": fraction, "face_found": False})
                continue
            face = max(faces, key=lambda item: float(item[2]*item[3]*item[14]))
            x, y, w, h = [float(v) for v in face[:4]]
            # Inset excludes hair/background because the goal is detecting a
            # foreground glass card on the visible eyes/nose/mouth region.
            x0, y0 = max(0, int(x + w * .15)), max(0, int(y + h * .12))
            x1, y1 = min(width, int(x + w * .85)), min(height, int(y + h * .88))
            if x1 <= x0 + 3 or y1 <= y0 + 3:
                measurements.append({"sample_ratio": fraction, "face_found": False})
                continue
            difference = np.abs(
                frame_before[y0:y1,x0:x1].astype(np.int16) -
                frame_after[y0:y1,x0:x1].astype(np.int16)
            )
            mean_delta = float(difference.mean())
            changed_fraction = float((difference.max(axis=2) > 42).mean())
            flagged = mean_delta > 22.0 or changed_fraction > .32
            measurements.append({
                "sample_ratio": fraction,
                "face_found": True,
                "mean_face_rgb_change": round(mean_delta, 2),
                "fraction_face_pixels_changed_gt_42": round(changed_fraction, 3),
                "possible_overlay": flagged,
            })
    finally:
        before.release()
        after.release()
    detected = [m for m in measurements if m.get("face_found")]
    warnings = sum(bool(m.get("possible_overlay")) for m in detected)
    if warnings:
        status = "POSSIBLE_FACE_OVERLAY_REVIEW_REQUIRED"
    elif not detected:
        status = "UNVERIFIED_FACE_NOT_DETECTED"
    else:
        status = "NO_MAJOR_FACE_CHANGE_IN_SAMPLED_FRAMES"
    return {
        "status": status,
        "sampled_frames": len(measurements),
        "face_detections": len(detected),
        "possible_overlays": warnings,
        "samples": measurements,
        "limitation": "Objective face-region differences are warnings only; no hair/hand, creative or full-duration approval",
    }
