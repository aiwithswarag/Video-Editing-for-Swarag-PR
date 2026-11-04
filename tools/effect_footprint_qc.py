"""Private source-relative motion-footprint audit for all 47 Swarag clips.

Adds deterministic visual evidence to media decode success. It does not
identify a person, read captions, certify masking, or imply artistic approval.
All inputs stay on the local Windows/Docker worker; never transmit footage.
"""
from __future__ import annotations
from pathlib import Path

# These are intrinsically camera transforms, not infographic panels.
CAMERA_LOOKS=frozenset({
    "locked-on","lean-in","spotlight","moody","uninstall","rabbit-hole",
    "dot-reveal","led-sign","slow-push","glitter-spotlight",
    "pastel-word","broll-split","split-headline","swipe","match-cut",
    "reel-frame",
})
SMALL_INTENTIONAL=frozenset({"tap","reject-stamp","pause-point","scribble"})
ALL_LABELS_TO_REVIEW=47


def _samples(video,indices,shape=None):
    import cv2
    cap=cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise ValueError("INPUT_VIDEO_UNREADABLE")
    frames=[]
    try:
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES,idx)
            ok,frame=cap.read()
            if not ok or frame is None:
                raise ValueError("INPUT_VIDEO_MISSING_FRAME")
            if shape and frame.shape[:2]!=shape:
                frame=cv2.resize(frame,(shape[1],shape[0]),
                                 interpolation=cv2.INTER_AREA)
            frames.append(frame)
    finally:
        cap.release()
    return frames


def effect_footprint(source,clip,*,label):
    """Compare actual aligned frames, including multiple animation phases.

    Image difference is a conservative visibility heuristic. Camera motion,
    foreground masks, and compression can produce false positives; preserve
    numeric evidence and require a human for all final decisions.
    """
    import numpy as np
    indices=(4,8,12)
    output=_samples(clip,indices)
    native=_samples(source,indices,output[0].shape[:2])
    H,W=output[0].shape[:2]
    observations=[]
    for original,altered in zip(native,output):
        delta=np.max(np.abs(original.astype(np.int16)-
                            altered.astype(np.int16)),axis=2)
        changed=delta>=26
        # Area around the usual caption lanes, excluding the central face.
        lanes=np.zeros((H,W),np.bool_)
        lanes[:int(H*.38),:]=True
        lanes[int(H*.74):,:]=True
        changed_pct=float(changed.mean())
        lane_pct=float((changed & lanes).sum())/float(H*W)
        observations.append({
            "changed_percent":round(changed_pct*100,2),
            "safe_lane_changed_percent":round(lane_pct*100,2)})
    peak=max(x["safe_lane_changed_percent"] for x in observations)
    flags=[]
    if label not in CAMERA_LOOKS:
        threshold=.50 if label in SMALL_INTENTIONAL else 2.0
        if peak<threshold:
            flags.append("VISUAL_FOOTPRINT_TOO_SMALL_FOR_PHONE_REVIEW")
    if max(x["changed_percent"] for x in observations)<.30:
        flags.append("LITTLE_OBSERVABLE_EFFECT_MOTION_OR_VISUAL_CHANGE")
    return {"frames_checked":len(indices),
            "input_dimensions":[W,H],
            "observations":observations,
            "max_safe_lane_changed_percent":peak,
            "review_flags":flags,
            "creative_approval":"NOT_CERTIFIED"}


def audit_gallery(source,gallery,labels):
    gallery=Path(gallery)
    details={}
    for label in labels:
        p=gallery/(label+".mp4")
        if not p.is_file():
            details[label]={"review_flags":["MISSING_MOTION_CLIP"],
                            "creative_approval":"NOT_CERTIFIED"}
            continue
        try:
            details[label]=effect_footprint(source,p,label=label)
        except (ValueError,OSError,ImportError) as exc:
            details[label]={"review_flags":["FOOTPRINT_AUDIT_UNAVAILABLE"],
                            "error_type":type(exc).__name__,
                            "creative_approval":"NOT_CERTIFIED"}
    warnings={label:item["review_flags"] for label,item in details.items()
              if item["review_flags"]}
    return {"effects_checked":len(details),
            "warnings_by_effect":warnings,
            "effects_with_visual_warnings":len(warnings),
            "per_effect":details,
            "creative_status":"NOT_APPROVED_BY_METRICS"}
