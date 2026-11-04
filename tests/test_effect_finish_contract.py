"""Every Swarag original FX has a human-readable finishing contract.

Regression tests use only synthetic metadata, not personal camera recordings.
"""
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from effect_catalog import read_registry
from effect_finish_contract import FINISH_SPEC,NAMED_LOOKS,risk_for
from production_lint import audit

class EffectFinishContractTests(unittest.TestCase):
    def test_exact_42_originals_and_all_five_names(self):
        names,_,_=read_registry()
        self.assertEqual(set(names),set(FINISH_SPEC))
        self.assertEqual(len(FINISH_SPEC),42)
        self.assertEqual(len(NAMED_LOOKS),5)
        p=json.loads((ROOT/"branding"/"executive.json").read_text())
        self.assertEqual(set(p["effect_defaults"]),set(FINISH_SPEC))
        for name in [*names,*NAMED_LOOKS]:
            result=risk_for(name)
            self.assertIn(result["preferred_placement"],
                          ("above","below","tracked","none"))
            self.assertTrue(result["must_review"])
            self.assertTrue(result["required_content"])
            self.assertEqual("REVIEW REQUIRED — full real moving video",
                             result["creative_status"])

    def test_all_variants_map_to_original_registry(self):
        names,_,_=read_registry()
        for look,original in NAMED_LOOKS.items():
            with self.subTest(look=look):
                self.assertIn(original,names)
                self.assertEqual(original,risk_for(look)["original_effect"])
        self.assertEqual("below",risk_for("apple-toggles-below")["preferred_placement"])

    def test_premium_rejects_unsourced_storyboard_ui_copy(self):
        for name in ("lineup","check-pills","apple-toggles",
                     "comment-box","pause-point","scribble","tier-list"):
            with self.subTest(effect=name):
                item={"fx":name,"start":0,"end":1.8}
                report=audit([item],3)
                self.assertIn("SCRIPT_COPY_REQUIRED",
                              [v["code"] for v in report["blocking_errors"]])
                self.assertFalse(audit([item],3,"showcase")["blocking_errors"])

    def test_phone_rows_are_validated_per_effect(self):
        cases={"lineup":"ONE|TWO|THREE|FOUR|FIVE",
               "apple-toggles":"BRAND PROTECTION AND PRIVACY POLICY",
               "todo":"ONE|TWO|THREE|FOUR|FIVE",
               "checklist":"ONE::brief|TWO::brief|THREE::brief|FOUR::brief|FIVE::brief",
               "cover-star":"ONE|TWO|THREE|FOUR",
               "red-collage":"ONE|TWO|THREE|FOUR"}
        for name,rows in cases.items():
            with self.subTest(effect=name):
                item={"fx":name,"start":0,"end":1.8,"text":rows,
                      "item":"APPROVED","lines":rows}
                codes=[v["code"] for v in audit([item],3)["blocking_errors"]]
                self.assertIn("MOBILE_COPY_OVERFLOW",codes)

    def test_reel_frame_counts_must_be_verified(self):
        item={"fx":"reel-frame","start":0,"end":1.8,"likes":26900}
        self.assertIn("UNVERIFIED_SOCIAL_METRICS",
            [x["code"] for x in audit([item],3)["blocking_errors"]])
        verified={**item,"metrics_verified":True,"metric_source":"Approved analytics export"}
        self.assertNotIn("UNVERIFIED_SOCIAL_METRICS",
            [x["code"] for x in audit([verified],3)["blocking_errors"]])

    def test_executive_card_count_limits(self):
        for name in ("noise","orbit","carousel-spin","shortcut-rain","headline-wall"):
            with self.subTest(effect=name):
                item={"fx":name,"start":0,"end":1.8,"count":50}
                self.assertIn("EXCESSIVE_CARD_DENSITY",
                    [x["code"] for x in audit([item],3)["blocking_errors"]])
        carousel={"fx":"carousel-spin","start":0,"end":1.8,
                  "turns":3,"count":4}
        self.assertIn("AGGRESSIVE_CAROUSEL",
                    [x["code"] for x in audit([carousel],3)["blocking_errors"]])


if __name__=="__main__":
    unittest.main()
