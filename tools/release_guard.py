#!/usr/bin/env python3
"""Fail-closed Swarag release gate: technical PASS is not creative APPROVAL.

This gate is advisory to the release workflow; it cannot cryptographically prove
a process ran from a self-reported JSON. The producer writes a master SHA-256,
and a human reviewer must sign off on that exact digest after full playback.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ENGINE_ID = "swarag-repository-42-effect-engine"
REVIEW_FIELDS = (
    "source_confirmed_clean",
    "full_motion_watched",
    "full_audio_listened",
    "requested_effects_verified",
    "face_hair_hands_masking_checked",
    "typography_readable_on_phone",
    "captions_and_claims_verified",
    "visual_style_approved",
)
def sha256_file(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(2*1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def evaluate(qa,master,required_effects=(),review=None):
    master=Path(master)
    faults=[]
    evidence=[]
    if not master.is_file() or master.stat().st_size<4096:
        faults.append("The completed original-footage MP4 is missing or invalid")
        hashval=None
    else:
        hashval=sha256_file(master)

    if qa.get("technical_status")!="PASS":
        faults.append("Production QA technical_status is not PASS")
    provenance=qa.get("renderer_provenance",{})
    if provenance.get("engine_id")!=ENGINE_ID:
        faults.append("Original Swarag 42-effect engine provenance absent; fallback not authorized")
    if provenance.get("entrypoint")!="scripts/fx.py":
        faults.append("Rendering entrypoint not identified as original scripts/fx.py")
    if qa.get("creative_status","").upper().startswith("APPROVED"):
        faults.append("Technical renderer must not self-certify creative approval")
    effects=qa.get("selected_effects",[])
    absent=sorted(set(required_effects)-set(effects))
    if absent:
        faults.append("Requested effect names not recorded: "+", ".join(absent))
    if not effects:
        faults.append("No rendered effect identifiers recorded")
    if hashval and hashval!=qa.get("master_sha256"):
        faults.append("Master SHA-256 does not match the real MP4 bytes")
    if qa.get("preview") is True:
        faults.append("Preview output cannot be published as a complete master")
    if not qa.get("visual_review",{}).get("review_points"):
        faults.append("Actual exported frame-review samples absent")
    if faults:
        status="BLOCKED"
    else:
        status="CREATIVE_REVIEW_REQUIRED"
        if review is not None:
            if review.get("master_sha256")!=hashval:
                evidence.append("Reviewer attestation does not bind to the delivered MP4")
            if not str(review.get("reviewer","")).strip():
                evidence.append("Reviewer identity/name required")
            for k in REVIEW_FIELDS:
                if review.get(k) is not True:
                    evidence.append("Missing or incomplete human review: "+k)
            if not evidence:
                status="CREATIVE_APPROVED"
    return {
        "release_status":status,"technical_status":qa.get("technical_status"),
        "master_sha256":hashval,"canonical_renderer_required":ENGINE_ID,
        "requested_effects":list(required_effects),
        "renderer_effects":effects,
        "blocking_errors":faults,"review_requirements":evidence,
        "reviewer":review.get("reviewer") if review and status=="CREATIVE_APPROVED" else None,
        "note":"Only full playback by an actual reviewer can approve natural-looking face masking, sound, factual graphics and typography. An unsigned QA JSON is not proof."
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("production_qa",type=Path)
    p.add_argument("master",type=Path)
    p.add_argument("--required-effect",action="append",default=[])
    p.add_argument("--review",type=Path,help="Private completed human approval form bound to MP4 SHA-256")
    p.add_argument("--report",type=Path,required=True)
    args=p.parse_args()
    qa=json.loads(args.production_qa.read_text(encoding="utf8"))
    review=json.loads(args.review.read_text(encoding="utf8")) if args.review else None
    result=evaluate(qa,args.master,args.required_effect,review)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print(result["release_status"])
    if result["blocking_errors"]:
        for item in result["blocking_errors"]:
            print("RELEASE BLOCKER:",item)
        raise SystemExit(3)
    if result["release_status"]!="CREATIVE_APPROVED":
        raise SystemExit(2)

if __name__=="__main__":
    main()
