#!/usr/bin/env python3
"""Build *draft* timed editorial headlines from a verified word-timestamp list.

Never generates a sentence, statistic or quotation absent from the source.
Supports scripts/words.py's [{"w":"word","s":1.2,"e":1.5}] format.
"""
import argparse
import json
import math
import re
from pathlib import Path

def parse_words(source,duration):
    words=source.get("words") if isinstance(source,dict) else source
    if not isinstance(words,list) or not words:
        raise ValueError("Expected a nonempty word-timestamp list")
    if not isinstance(duration,(int,float)) or isinstance(duration,bool) or not math.isfinite(duration) or duration<=0:
        raise ValueError("Duration must be finite and positive")
    out=[]
    previous=0.
    for i,item in enumerate(words):
        if not isinstance(item,dict):raise ValueError(f"Word {i}: expected object")
        w=item.get("w",item.get("word"))
        s=item.get("s",item.get("start"))
        e=item.get("e",item.get("end"))
        if not isinstance(w,str) or not w.strip() or len(w)>80 or "\n" in w:
            raise ValueError(f"Word {i}: invalid text")
        for label,v in (("start",s),("end",e)):
            if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v):
                raise ValueError(f"Word {i}: invalid {label}")
        if s<0 or e<=s or e>duration+.02 or s<previous-.03:
            raise ValueError(f"Word {i}: nonmonotonic or out-of-bounds timestamps")
        previous=e
        out.append({"w":w.strip(),"s":float(s),"e":float(e)})
    return out

def text_from_words(words):
    text=" ".join(x["w"] for x in words)
    return re.sub(r"\s+([,.;:!?])",r"\1",text).strip()

def clauses(words,gap=.60,max_duration=6.0):
    out=[]; current=[]
    for word in words:
        if current and (word["s"]-current[-1]["e"]>=gap or
                        word["e"]-current[0]["s"]>max_duration):
            out.append(current);current=[]
        current.append(word)
        if re.search(r"[.!?]\s*$",word["w"]):
            out.append(current);current=[]
    if current:out.append(current)
    return out

def headline_excerpt(words,max_chars=37,max_words=6):
    """Choose only a contiguous prefix of real source words; no paraphrases."""
    picked=[]
    for word in words:
        if len(picked)>=max_words:break
        proposal=text_from_words(picked+[word])
        if len(proposal)>max_chars:
            break
        picked.append(word)
    if len(picked)<2:return None
    return text_from_words(picked)

def create_story(words_source,duration,max_beats=6,min_spacing=6.5):
    if not 1<=max_beats<=12:raise ValueError("max_beats must be 1-12")
    if not 2<=min_spacing<=30:raise ValueError("min_spacing must be 2-30s")
    words=parse_words(words_source,duration)
    grouped=clauses(words)
    candidates=[]
    for group in grouped:
        headline=headline_excerpt(group)
        if not headline:continue
        start=max(0.,group[0]["s"]-.16)
        end=min(duration,start+max(2.4,min(4.,group[-1]["e"]-group[0]["s"]+.55)))
        if end<=start+.5:continue
        count=0
        for token in group:
            if count>=6 or len(text_from_words(group[:count+1]))>37:
                break
            count+=1
        candidates.append({"s":start,"e":end,"headline":headline,
                           "word_span":[group[0]["s"],group[count-1]["e"]]})
    beats=[]
    for candidate in candidates:
        if beats and candidate["s"]-beats[-1]["start"]<min_spacing:continue
        if beats and candidate["s"]<beats[-1]["end"]+.2:continue
        if len(beats)>=max_beats:break
        beats.append({"kind":"chapter","start":round(candidate["s"],2),
                      "end":round(candidate["e"],2),
                      "eyebrow":f"EXCERPT  /  {len(beats)+1:02d}",
                      "headline":candidate["headline"],"subline":"",
                      "transcript_word_span":candidate["word_span"]})
    if not beats:
        raise ValueError("No usable phrase with two or more timestamped words")
    return {"schema_version":1,"duration":duration,"source":"word_timestamps",
            "status":"DRAFT - MANUAL TRANSCRIPT AND LAYOUT REVIEW REQUIRED",
            "notice":"Every headline is a contiguous excerpt of supplied word-timing data. It is not a verified quotation until the transcription is checked against the actual audio. No inferred metrics, topic labels or paraphrases are added.",
            "beats":beats}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("words",type=Path)
    p.add_argument("--duration",type=float,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--max-beats",type=int,default=6)
    p.add_argument("--min-spacing",type=float,default=6.5)
    a=p.parse_args()
    data=json.loads(a.words.read_text(encoding="utf8"))
    result=create_story(data,a.duration,a.max_beats,a.min_spacing)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print(f"Created {len(result['beats'])} speech-timed draft beats: {a.output}. Manual review required.")
if __name__=="__main__":main()
