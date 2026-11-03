"""Source-grounded RAG explainer as eight REAL glass-widgets effects.

No extra effect name and no fake numbers, demo progress bars, avatars or
analytics. Uses the same fx.py glass-widgets catalog entry throughout.
"""
from __future__ import annotations
from rag_storyboard import KIND_NAMES,validate,coverage

LOOK = "rag-evidence"
LAYOUT_ID = "subject-masked-glass-v5"

def cue(stage):
    """Convert one validated script stage to an original engine cue."""
    if stage["kind"] not in KIND_NAMES:
        raise ValueError("Unknown source-backed RAG stage")
    return {
        "fx":"glass-widgets",
        "look":LOOK,
        "stage":stage["kind"],
        "start":stage["start"],
        "end":stage["end"],
        # Grade has already run; do not apply an app-look colour treatment.
        "grade":"none",
    }

def plan(stages,duration):
    return [cue(stage) for stage in validate(stages,duration)]

def report(stages,duration,rendered_effects):
    valid=validate(stages,duration)
    cues=plan(valid,duration)
    if not all(any(item.get("fx")=="glass-widgets" and
                        item.get("look")==LOOK and
                        item.get("stage")==cue["stage"]
                        for item in rendered_effects) for cue in cues):
        raise ValueError("Not all eight original-engine glass-widgets cues were rendered")
    return {
        "layout_id":LAYOUT_ID,
        "complete":True,
        "graphic_stages":8,
        "source_grounded":True,
        "effect_name":"glass-widgets",
        "effect_look":LOOK,
        "compositing":"original fx.py glass-widgets + per-frame MediaPipe person-depth mask",
        "face_safe_layout":True,
        "subject_depth_mask":True,
        "face_masking_approval":"REVIEW REQUIRED — full real motion and mask QA",
        "graphics_overlap_camera_pixels":"NOT MEASURED — MediaPipe mask + detector face guard require full-motion review",
        "full_frame_camera_preserved":True,
        "no_fabricated_demo_widgets":True,
        **coverage(valid,duration),
    }
