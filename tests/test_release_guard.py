"""Regression: reject the actual class of fallback QA that passed technical checks."""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from release_guard import ENGINE_ID,REVIEW_FIELDS,evaluate,sha256_file

class ReleaseGuardTests(unittest.TestCase):
    def setUp(self):
        self.dir=tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.path=Path(self.dir.name)/"master.mp4"
        self.path.write_bytes(b"source-footage-render"*400)
        self.sample={
            "technical_status":"PASS",
            "creative_status":"REVIEW REQUIRED",
            "renderer_provenance":{"engine_id":ENGINE_ID,"entrypoint":"scripts/fx.py"},
            "selected_effects":["slow-push","backdrop-word"],
            "preview":False,
            "master_sha256":sha256_file(self.path),
            "visual_review":{"review_points":[{"time_s":1.0,"label":"motion check"}]}
        }
    def test_rejects_open_cv_ffmpeg_fallback_despite_stream_pass(self):
        real_world_fallback={
            "release_status":"TECHNICAL PASS; CREATIVE REVIEW REQUIRED",
            "export_type":"Real source-footage local OpenCV/FFmpeg fallback; not the original repository production engine",
            "checks":{"complete_video_decode":"PASS","frame_count":"PASS (1797)"},
            "content":{"new_effects":[{"name":"slow-push"},{"name":"backdrop-word"}]}
        }
        report=evaluate(real_world_fallback,self.path,["slow-push","backdrop-word"])
        self.assertEqual("BLOCKED",report["release_status"])
        self.assertTrue(any("fallback" in s.lower() for s in report["blocking_errors"]))
    def test_correct_engine_is_still_unapproved_without_full_review(self):
        report=evaluate(self.sample,self.path,["slow-push","backdrop-word"])
        self.assertEqual("CREATIVE_REVIEW_REQUIRED",report["release_status"])
    def test_rejects_missing_requested_effect_and_changed_output(self):
        self.path.write_bytes(b"tampered"*2000)
        report=evaluate(self.sample,self.path,["orbit"])
        self.assertEqual("BLOCKED",report["release_status"])
        self.assertTrue(any("SHA-256" in e for e in report["blocking_errors"]))
        self.assertTrue(any("orbit" in e for e in report["blocking_errors"]))
    def test_unverified_human_attestation_cannot_approve(self):
        review={"reviewer":"Editor","master_sha256":self.sample["master_sha256"]}
        report=evaluate(self.sample,self.path,["slow-push"],review)
        self.assertEqual("CREATIVE_REVIEW_REQUIRED",report["release_status"])
        self.assertEqual(len(REVIEW_FIELDS),len(report["review_requirements"]))
    def test_complete_attestation_approves_only_matching_bytes(self):
        review={"reviewer":"Designated producer",
                "master_sha256":self.sample["master_sha256"],
                **{k:True for k in REVIEW_FIELDS}}
        report=evaluate(self.sample,self.path,["slow-push","backdrop-word"],review)
        self.assertEqual("CREATIVE_APPROVED",report["release_status"])
        self.path.write_bytes(b"changed"*2500)
        report=evaluate(self.sample,self.path,["slow-push"],review)
        self.assertEqual("BLOCKED",report["release_status"])
    def test_preview_is_not_final(self):
        bad={**self.sample,"preview":True}
        self.assertEqual("BLOCKED",evaluate(bad,self.path)["release_status"])

if __name__=="__main__":
    unittest.main()
