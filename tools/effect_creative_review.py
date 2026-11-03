"""Swarag effect-specific creative-review priorities, not automated approval.

These labels are reasoned from each original effect's presentation mechanism and
the user's recent camera contact sheets. They are NOT detections of a defect in
any individual MP4, or a substitute for full playback at final output size.
"""
from __future__ import annotations

FACE_CLEARANCE = frozenset({
    "broll-split", "cover-star", "red-collage", "headline-box",
    "headline-wall", "profile-wall", "match-cut", "led-sign",
    "backdrop-word", "phone-fan", "comment-box",
})
MOBILE_TYPE = frozenset({
    "the-bill", "todo", "checklist", "glass-widgets",
    "liquid-glass-graph", "match-cut", "headline-wall",
    "cover-star", "profile-wall", "tier-list", "apple-toggles",
    "check-pills", "split-headline", "headline-box",
})
SOURCE_ASSETS = frozenset({
    "noise", "orbit", "carousel-spin", "check-pills",
    "profile-wall", "phone-fan", "broll-split",
})
CLAIM_PROVENANCE = frozenset({
    "profile-wall", "broll-split", "glass-widgets",
    "liquid-glass-graph", "match-cut", "timeline",
    "checklist", "todo", "headline-wall",
})
INTENTIONAL_DISTORTION = frozenset({
    "uninstall", "rabbit-hole", "dot-reveal", "red-collage",
    "shortcut-rain", "glitter-spotlight", "spotlight",
    "countdown-flip", "swipe", "match-cut",
})
PER_FRAME_MOTION = frozenset({
    "locked-on", "orbit", "carousel-spin", "noise", "scribble",
    "pause-point", "lean-in", "slow-push", "rabbit-hole",
    "reel-frame", "glitter-spotlight", "cover-star",
})

def review_focus(effect):
    """Specific human review questions, including all named variants."""
    name = str(effect)
    if name in ("cover-star-editorial",):
        name = "cover-star"
    elif name in ("liquid-glass-graph-bento",):
        name = "liquid-glass-graph"
    elif name in ("glass-widgets-simple",):
        name = "glass-widgets"
    elif name in ("apple-toggles-below",):
        name = "apple-toggles"
    elif name in ("glitter-spotlight",):
        name = "spotlight"
    focus = []
    if name in FACE_CLEARANCE:
        focus.append("FACE_CLEARANCE — check eyes, mouth, hair and foreground overlap throughout")
    if name in MOBILE_TYPE:
        focus.append("MOBILE_TYPE — inspect every line at actual phone playback size")
    if name in SOURCE_ASSETS:
        focus.append("SOURCE_ASSETS — verify approved imagery, not repeated camera thumbnails")
    if name in CLAIM_PROVENANCE:
        focus.append("CLAIM_PROVENANCE — verify examples, figures and UI copy against the script/source")
    if name in INTENTIONAL_DISTORTION:
        focus.append("MOTION_RESTRAINT — ensure the intended stylization does not reduce credibility")
    if name in PER_FRAME_MOTION:
        focus.append("TRACKING_STABILITY — inspect temporal mask, camera movement and transitions")
    if not focus:
        focus.append("GENERAL_MOTION — review face, audio and overall visual polish")
    return focus

def report_for(labels):
    return {label:review_focus(label) for label in labels}
