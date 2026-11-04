"""Swarag original 42-effect per-effect finishing contract.

Source of truth for the effect names remains scripts/fx.py. This is an
editorial QA policy for the real 9:16 camera film, not an alternative
renderer or a claim that synthetic tests prove creative quality.

The 47 camera diagnostic MP4 clips are private and must not be committed.
Every production text/value is tied to spoken words or approved evidence.
"""
from __future__ import annotations

# Format: exact original name: (placement, content rule, visual inspection).
# Placement "none" means the effect transforms camera footage; "tracked"
# means it is intended to draw on/around the subject rather than hide it.
FINISH_SPEC = {
    "noise": ("above", "approved visual cards", "avoid repeated speaker clones; count <= 8"),
    "lineup": ("above", "spoken numbered steps", "at most four large, readable tiles"),
    "locked-on": ("tracked", "short optional label", "keep face brackets outside eyes; zoom <= 1.15"),
    "orbit": ("below", "approved relevant visual cards", "depth sort, hair/hand edges and card readability"),
    "lean-in": ("none", "spoken emphasis", "subtle real-camera zoom; preserve skin texture"),
    "backdrop-word": ("above", "exact approved headline", "no disappearing letter segments over head"),
    "spotlight": ("above", "short sourced headline if shown", "preserve facial exposure and skin hue"),
    "the-bill": ("above", "four or fewer verified short lines", "readable paper/receipt with no clipped baseline"),
    "moody": ("none", "no new text", "preserve skin hue; avoid double grading"),
    "swipe": ("tracked", "verified before/after comparison", "visible separator, big labels and no fake results"),
    "todo": ("above", "one to four approved tasks", "complete readable checklist; ticks match speech"),
    "comment-box": ("above", "approved quote or mock labeled demo", "no fake comments or reply events as facts"),
    "tap": ("below", "illustrative social UI only", "button does not assert actual account engagement"),
    "pause-point": ("tracked", "approved annotation", "arrow stays on topic, not eyes or mouth"),
    "uninstall": ("none", "illustrative uninstall metaphor", "explicit experimental style; glitch is intentional"),
    "reel-frame": ("below", "approved handle; verified social metrics only", "no invented likes or comments"),
    "shortcut-rain": ("above", "approved shortcut keys", "limited key count and controlled falling motion"),
    "reject-stamp": ("below", "approved short judgment text", "visible contrast and time on screen"),
    "countdown-flip": ("above", "real count if spoken", "clear digits and unobstructed flip animation"),
    "rabbit-hole": ("none", "intentional recursive-frame metaphor", "no accidental face cloning or extreme spin"),
    "cover-star": ("above", "verified masthead and cover lines", "no tiny editorial side labels near face"),
    "scribble": ("tracked", "relevant approved callout", "visible, stable strokes and legible arrow"),
    "glass-widgets": ("above", "script-specific verified widget facts", "depth, blur contrast, complete labels"),
    "red-collage": ("above", "verified single headline and short lines", "no lost characters in hair silhouette"),
    "split-headline": ("above", "approved words and pill", "top card stays fully readable and face remains below"),
    "pastel-word": ("above", "short actual thematic word", "word and profile bar do not interrupt expression"),
    "check-pills": ("above", "approved choices and relevant cards", "no generic fake project screenshots"),
    "headline-box": ("above", "approved two-part headline", "label and box remain a single readable unit"),
    "profile-wall": ("below", "approved source media, sourced metric only", "no invented count, cloned gallery or oval hole"),
    "tier-list": ("below", "approved comparative tiers", "max four readable rows unless explicitly requested"),
    "broll-split": ("below", "real approved B-roll and verified tag", "upper visual and lower speaker are cleanly separated"),
    "phone-fan": ("below", "real approved supporting reels or labeled concepts", "no unrelated videos covering mouth"),
    "dot-reveal": ("none", "intentional dot-grid visual transition", "full reveal returns intact real face"),
    "headline-wall": ("above", "verified source-backed headlines", "no tiny dense wall or implied fabricated publications"),
    "checklist": ("below", "one to four verified steps", "full frosted panel moves as a unit, no face cutout"),
    "liquid-glass-graph": ("below", "verified figure or conspicuous hypothetical sample", "readable axes, label, units"),
    "carousel-spin": ("below", "approved relevant cards", "speed restrained; rear cards do not obscure eyes"),
    "match-cut": ("above", "approved short verified article excerpt", "not a duplicated wallpaper of source prose"),
    "apple-toggles": ("above", "one to four approved complete rows", "all toggles and text visible; no chopped rows"),
    "led-sign": ("above", "one concise approved phrase", "complete letters outside head and enough contrast"),
    "slow-push": ("none", "no new copy", "subtle reframing without artificial blur")
}

NAMED_LOOKS = {
    "glitter-spotlight": "spotlight",
    "cover-star-editorial": "cover-star",
    "liquid-glass-graph-bento": "liquid-glass-graph",
    "glass-widgets-simple": "glass-widgets",
    "apple-toggles-below": "apple-toggles",
}

def risk_for(effect):
    """A specific review brief. No visual approval is inferred."""
    base=NAMED_LOOKS.get(effect,effect)
    placement,content,check=FINISH_SPEC[base]
    if effect=="apple-toggles-below": placement="below"
    return {"original_effect":base,"look":effect if effect!=base else None,
            "preferred_placement":placement,
            "required_content":content,
            "must_review":check,
            "creative_status":"REVIEW REQUIRED — full real moving video"}
