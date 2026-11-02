"""Six-section RAG/citation visual direction, grounded in uploaded script only.

Specialized editorial layer; does NOT add/rename any of the original 42 effects.
Never treats script time headings as actual spoken-word timestamps.
"""
from __future__ import annotations
import math
import re
from local_director import BEAT_RE,seconds

SECTION_NAMES=("hook","policies","outdated-answer","rag-flow","verification-checks","closing")
KIND_NAMES=("hook","policies","outdated-answer","rag-flow",
            "check-1","check-2","check-3","closing")
KIND_TO_SECTION={"hook":"hook","policies":"policies",
                 "outdated-answer":"outdated-answer","rag-flow":"rag-flow",
                 "check-1":"verification-checks","check-2":"verification-checks",
                 "check-3":"verification-checks","closing":"closing"}
# These are labelled instructional figures, not real company policies or KPI data.
COPY={
    "hook":("YOUR AI CITED A SOURCE","CAN IT STILL BE WRONG?"),
    "policies":("FICTIONAL POLICIES","2024","$100 / NIGHT","2026","$150 / NIGHT"),
    "outdated-answer":("AI ANSWER","$100","CITATION: 2024 POLICY","OUTDATED DOCUMENT"),
    "rag-flow":("HOW RAG WORKS","SEARCH DOCUMENTS","RETRIEVE TEXT","GENERATE ANSWER",
                "RELEVANT IS NOT ALWAYS CURRENT"),
    "check-1":("VERIFY THE CITATION","RIGHT VERSION?"),
    "check-2":("VERIFY THE CITATION","RIGHT VERSION?","ANSWER MATCHES SOURCE?"),
    "check-3":("VERIFY THE CITATION","RIGHT VERSION?","ANSWER MATCHES SOURCE?","AUTHORIZED ACCESS?"),
    "closing":("A CITATION","IS WHERE VERIFICATION STARTS"),
}

def _chapters(script):
    matches=list(BEAT_RE.finditer(script))
    if len(matches)!=6:return None
    out=[]
    for index,match in enumerate(matches):
        start=seconds(match.group(1));end=seconds(match.group(2))
        next_begin=matches[index+1].start() if index+1<len(matches) else len(script)
        text=script[match.end():next_begin]
        if end<=start or (out and start<out[-1][1]):return None
        out.append((start,end,match.group(0)+" "+text))
    return out

def recognizable(script):
    """Require the actual six chapter texts to support every specific graphic."""
    chapters=_chapters(script)
    if not chapters:return False
    checks=(
        lambda t:"cited" in t or "citation" in t,
        lambda t:all(x in t for x in ("2024","2026","$100","$150","fictional")),
        lambda t:all(x in t for x in ("2024","$100","citat","outdated")),
        lambda t:all(x in t for x in ("rag","retriev","document","answer")),
        lambda t:all(x in t for x in ("version","answer","source","access")),
        lambda t:"citation" in t and "verification" in t,
    )
    return all(check(chapters[i][2].casefold()) for i,check in enumerate(checks))

def rag_intent(script):
    """Identify a likely citation/policy/RAG video before accepting an effect-only plan.

    This check is deliberately broader than the six-section storyboard template:
    if a user supplies a relevant-but-incomplete script, fail with a useful error
    instead of silently rendering a lone slow-push as a completed explainer.
    """
    if not isinstance(script,str):
        return False
    t=script.casefold()
    return (("rag" in t or "retriev" in t) and
            ("citation" in t or "cited" in t) and
            ("polic" in t or ("$100" in t and "$150" in t)))


def explain_unrecognized(script):
    """Diagnostic, no user content copied into public logs."""
    if not rag_intent(script):
        return None
    chapters=_chapters(script)
    if chapters is None:
        return ("RAG explainer detected, but six numbered time headings were not found. "
                "Upload the complete script with six separate headings, e.g. "
                "'0-3 sec | Hook' ... '49-55 sec | Close'; do not submit a spoken-text-only excerpt.")
    checks=(
        ("citation hook",lambda t:"cited" in t or "citation" in t),
        ("fictional 2024/$100 vs 2026/$150 comparison",lambda t:all(x in t for x in
          ("2024","2026","$100","$150","fictional"))),
        ("outdated 2024 citation",lambda t:all(x in t for x in ("2024","$100","citat","outdated"))),
        ("RAG retrieve-document-answer explanation",lambda t:all(x in t for x in
          ("rag","retriev","document","answer"))),
        ("three checks: version, source accuracy, access",lambda t:all(x in t for x in
          ("version","answer","source","access"))),
        ("verification closing",lambda t:"citation" in t and "verification" in t),
    )
    failures=[label for (_,_,seg),(label,check) in zip(chapters,checks) if not check(seg.casefold())]
    if failures:
        return ("RAG explainer detected but the uploaded script does not support: " +
                "; ".join(failures) +
                ". Supply the matching COMPLETE six-section script; no visuals or data will be invented.")
    return "RAG six-section recognition failed; check the script time headings and ordering."


def compose(script,duration):
    if not isinstance(duration,(int,float)) or not math.isfinite(duration) or duration<=0:
        raise ValueError("Actual source duration must be finite positive seconds")
    if not recognizable(script):
        return []
    chapters=_chapters(script)
    scripted_end=chapters[-1][1]
    ratio=duration/scripted_end
    beats=[]
    for i,(start,end,_) in enumerate(chapters):
        lo=round(start*ratio,3)
        hi=round(min(duration,end*ratio),3)
        if i==4:
            for j,kind in enumerate(("check-1","check-2","check-3")):
                a=round(lo+(hi-lo)*j/3,3)
                b=round(lo+(hi-lo)*(j+1)/3,3) if j<2 else hi
                beats.append({"section":"verification-checks","kind":kind,"start":a,"end":b})
        else:
            beats.append({"section":SECTION_NAMES[i],
                          "kind":("hook","policies","outdated-answer","rag-flow",None,"closing")[i],
                          "start":lo,"end":hi})
    return validate(beats,duration,script)

def validate(beats,duration,script=None):
    if not isinstance(beats,list) or len(beats)!=8:
        raise ValueError("RAG visual storyboard requires eight graphic stages spanning six sections")
    if script is not None and not recognizable(script):
        raise ValueError("Script does not support the fictional-policy RAG visual template")
    output=[]
    prev=0.
    for index,(item,kind) in enumerate(zip(beats,KIND_NAMES)):
        if not isinstance(item,dict) or set(item)!={"kind","section","start","end"}:
            raise ValueError("RAG beat contains unsupported fields")
        if item["kind"]!=kind or item["section"]!=KIND_TO_SECTION[kind]:
            raise ValueError("RAG storyboard sections must be complete and ordered")
        a,b=item["start"],item["end"]
        if any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) for x in (a,b)):
            raise ValueError("RAG visual times must be real numbers")
        if a<0 or b>a+240 or b<=a+.15 or b>duration+.02 or a<prev-.00001:
            raise ValueError("RAG visual time outside source or overlaps another visual")
        prev=b
        output.append({"kind":kind,"section":item["section"],
                       "start":round(a,3),"end":round(b,3)})
    if output[0]["start"]>.2 or duration-output[-1]["end"]>.2:
        raise ValueError("Six-chapter explainer must cover opening and closing; review timeline")
    return output

def coverage(beats,duration,script=None):
    valid=validate(beats,duration,script)
    return {"expected_sections":list(SECTION_NAMES),
            "actual_sections":list(dict.fromkeys(b["section"] for b in valid)),
            "graphic_stages":len(valid),"complete":True,
            "speech_timing":"DRAFT SCRIPT WINDOWS - manual audio alignment required"}
