"""Offline, conservative draft editing decisions for the free local Swarag app.

Not speech recognition. Exact timestamps and words must be verified against
recorded audio before the user can start a production render.
"""
from __future__ import annotations
import io
import math
import re
import zipfile
from xml.etree import ElementTree as ET

from effect_catalog import read_registry
from plan_validation import validate_plan

BEAT_RE = re.compile(r"(?m)^[ \t#*]*(\d{1,3}(?::\d{2})?)\s*[–—-]\s*(\d{1,3}(?::\d{2})?)\s*(?:sec(?:onds?)?)?\s*(?:\||\*|$)")
_TEXTFX = {"backdrop-word", "headline-box", "split-headline", "led-sign",
           "reject-stamp", "pastel-word", "headline-wall"}
_SYNONYMS = {
    "slow-push": ("cinematic push", "subtle push", "push in", "slow zoom"),
    "backdrop-word": ("text behind", "behind my head", "text behind me"),
    "spotlight": ("spotlight effect",),
    "headline-box": ("animated title", "animated headline"),
}
_PRESET_HINTS = {
    "slow-push": {"zoom": 1.055, "blur": 0},
}

def document_text(filename, body):
    """Read uploaded TXT/MD/DOCX locally. PDF requires an explicit converter."""
    name = filename.casefold()
    if len(body) > 2 * 1024 * 1024:
        raise ValueError("Script is too large (maximum 2MB)")
    if name.endswith((".txt", ".md")):
        return body.decode("utf-8-sig")
    if name.endswith(".docx"):
        with zipfile.ZipFile(io.BytesIO(body)) as archive:
            info = archive.getinfo("word/document.xml")
            if info.file_size > 2 * 1024 * 1024:
                raise ValueError("Expanded DOCX script is too large")
            blob = archive.read("word/document.xml")
        root = ET.fromstring(blob)
        ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        paragraphs = []
        for paragraph in root.iter(ns+"p"):
            phrase = "".join(e.text or "" for e in paragraph.iter(ns+"t"))
            if phrase.strip():
                paragraphs.append(phrase)
        return "\n".join(paragraphs)
    raise ValueError("Upload a TXT, Markdown or DOCX script; PDFs need conversion first")

def seconds(value):
    if ":" in value:
        mins,secs=value.split(":",1)
        return int(mins)*60+int(secs)
    return int(value)

def beats(script,duration):
    matches=list(BEAT_RE.finditer(script))
    if not matches:
        return [], None
    out=[]
    for i,m in enumerate(matches):
        start,end=seconds(m[1]),seconds(m[2])
        if end<=start or (i and start<out[-1]["end"]):
            raise ValueError("Script time ranges overlap or are invalid")
        out.append({"start":start,"end":end})
    max_time=out[-1]["end"]
    if max_time <= 0:
        raise ValueError("Invalid scripted duration")
    factor=duration/max_time
    return [{"start":round(item["start"]*factor,3),"end":round(min(duration,item["end"]*factor),3)}
            for item in out], round(max_time,3)

def requested_names(direction):
    names,aliases,_ = read_registry()
    found=set()
    lower=direction.casefold()
    for name in sorted(names,key=len,reverse=True):
        if re.search(r"(?<!\w)"+re.escape(name).replace(r"\-",r"[\s-]")+"(?!\w)",lower):
            found.add(name)
    for alias,canonical in aliases.items():
        if re.search(r"(?<!\w)"+re.escape(alias).replace(r"\-",r"[\s-]")+"(?!\w)",lower):
            found.add(canonical)
    for name,patterns in _SYNONYMS.items():
        if any(p in lower for p in patterns):
            found.add(name)
    return sorted(found)

def draft(direction,script,duration):
    if not isinstance(duration,(int,float)) or not math.isfinite(duration) or not 1<=duration<=7200:
        raise ValueError("Invalid source-video duration")
    if not isinstance(direction,str) or len(direction)>3000:
        raise ValueError("Direction must be ordinary text, under 3,000 characters")
    if not isinstance(script,str) or len(script)>100000:
        raise ValueError("Script is too long")
    windows,script_total=beats(script,duration)
    found=requested_names(direction)
    if not found:
        found=["slow-push"]
    warnings=[
        "DRAFT ONLY: on-screen timestamps were NOT matched to actual spoken words.",
        "Review/edit each effect's timing and text against the actual video before rendering.",
        "Technical PASS never proves polished masks, cinematography or accurate research claims.",
    ]
    if script_total is None:
        warnings.append("No timestamp headings found in script; effect windows are approximate suggestions.")
    elif abs(script_total-duration)>.30:
        warnings.append(f"Script ends at {script_total:g}s but video is {duration:.2f}s; chapter windows were scaled proportionally, NOT verified.")
    title = re.search(r"(?:text|title)\s*[:=]\s*['\"]([^'\"\n]{1,100})['\"]", direction, flags=re.I)
    explicit_title = title.group(1).strip() if title else None
    entries=[]
    n=len(found)
    for i,name in enumerate(found):
        # Assign unique chapter windows when possible so simultaneous effects
        # do not overwhelm the speaker. Timings are never represented as verified.
        if name=="slow-push":
            start=min(.25,max(0,duration-.65))
            end=min(duration,start+min(3.2,max(.7,duration*.11)))
        else:
            if windows:
                idx=min(i+1,len(windows)-1)
                window=windows[idx]
                start=window["start"]+.18
                end=min(window["end"]-.14,start+2.5)
            else:
                start=duration*(i+1)/(n+1)
                end=min(duration,start+min(2.5,duration*.16))
            if end-start<.58:
                start=max(0,start-.3)
                end=min(duration,start+.65)
        entry={"fx":name,"start":round(start,3),"end":round(end,3)}
        entry.update(_PRESET_HINTS.get(name,{}))
        if name in _TEXTFX:
            entry["text"]=explicit_title or ""
            if not entry["text"]:
                warnings.append(f"{name}: supply intentional on-screen copy from the verified script. No placeholder was invented.")
        entries.append(entry)
    validated=validate_plan(entries,duration)
    # Specialized source-grounded graphic direction complements the original
    # catalog. Other scripts stay on the conservative original-effect path.
    from rag_storyboard import compose as compose_rag_storyboard
    semantic_beats=compose_rag_storyboard(script,duration)
    from rag_storyboard import explain_unrecognized,rag_intent
    if rag_intent(script) and not semantic_beats:
        # Crucial: never "succeed" with just slow-push when a complete
        # six-section source-backed explainer is obviously requested.
        raise ValueError(explain_unrecognized(script) or
                         "RAG explainer requested but source-backed visual stages are missing")
    if semantic_beats:
        warnings.append("Recognized all six RAG/citation story sections and prepared eight reviewable graphic stages (the three checks enter sequentially).")
        warnings.append("The fictional 2024/$100 and 2026/$150 figures are copied from YOUR script, not asserted to be real policies.")
        warnings.append("Script-time scaling is provisional. Check each panel against the actual spoken video BEFORE approving the render.")
    return {
        "status":"DRAFT — NOT SPEECH VERIFIED",
        "rag_storyboard":semantic_beats,
        "requires_six_section_explainer":bool(semantic_beats),
        "semantic_sections":list(dict.fromkeys(x['section'] for x in semantic_beats)),
        "effects":validated,"script_duration":script_total,
        "source_duration":round(duration,3),
        "effect_catalog_size":len(read_registry()[0]),
        "warnings":warnings
    }
