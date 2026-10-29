"""Make brand choices effective at execution time (not just in documentation)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXECUTIVE = ROOT / "branding" / "executive.json"

def apply_brand(plan, name="executive"):
    if name == "none":
        return [dict(d) for d in plan]
    if name != "executive":
        raise ValueError(f"Unknown brand profile: {name}")
    brand = json.loads(EXECUTIVE.read_text(encoding="utf8"))
    defaults = brand.get("effect_defaults", {})
    output = []
    for item in plan:
        effect = item["fx"]
        # User-specified options always win over brand defaults.
        output.append({**defaults.get(effect, {}), **item})
    return output
