"""Dependency-free validation synchronized to the actual 42-effect renderer."""
import math
from effect_catalog import read_registry

_NAMES, ALIASES, LOOKS = read_registry()
AVAILABLE_EFFECTS = frozenset(_NAMES)

def validate_plan(plan, duration=None):
    if isinstance(plan, dict):
        plan = plan.get("effects")
    if not isinstance(plan, list) or not 1 <= len(plan) <= 150:
        raise ValueError("Plan requires 1 to 150 effects")
    if duration is not None and (isinstance(duration, bool) or not isinstance(duration,(int,float))
                                 or not math.isfinite(duration) or duration <= 0):
        raise ValueError("Duration must be positive and finite")
    result = []
    for i, item in enumerate(plan):
        if not isinstance(item, dict):
            raise ValueError(f"Effect {i}: expected object")
        d = dict(item)
        name = d.get("fx")
        if not isinstance(name, str):
            raise ValueError(f"Effect {i}: fx must be a string")
        name = name.lower().lstrip("/")
        if name in LOOKS:
            name, look = LOOKS[name]
            d.setdefault("look",look)
        name = ALIASES.get(name,name)
        if name not in AVAILABLE_EFFECTS:
            raise ValueError(f"Effect {i}: unknown effect {name}")
        s, e = d.get("start"), d.get("end")
        for label, value in (("start",s),("end",e)):
            if isinstance(value, bool) or not isinstance(value, (int,float)) or not math.isfinite(value):
                raise ValueError(f"Effect {i}: {label} must be finite numeric seconds")
        if s < 0 or e <= s or (duration is not None and e > duration + 1e-6):
            raise ValueError(f"Effect {i}: invalid time window")
        for key, val in d.items():
            if not isinstance(key,str) or len(key)>80:
                raise ValueError(f"Effect {i}: invalid option name")
            if isinstance(val, (dict,list)) or isinstance(val,str) and len(val)>3000:
                raise ValueError(f"Effect {i}: unsupported or oversized option {key}")
            if isinstance(val,float) and not math.isfinite(val):
                raise ValueError(f"Effect {i}: option {key} is not finite")
        d["fx"] = name
        result.append(d)
    return result
