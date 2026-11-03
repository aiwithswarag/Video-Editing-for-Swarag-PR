"""Test the private real-camera effect verifier without uploading source media.

A fast subset exercises the actual renderer/FFmpeg workflow; CI's separate
47-clip matrix is responsible for complete catalog coverage.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from local_effect_diagnostic import sample_window,report_from_gallery,run
from effect_catalog import read_registry
from render_effect_gallery import NAMED_VARIANTS


class DiagnosticReporting(unittest.TestCase):
    def test_representative_clip_window(self):
        self.assertEqual((15.624,2.25),sample_window(50.4))
        s,t=sample_window(2.6)
        self.assertGreaterEqual(s,0)
        self.assertLessEqual(s+t,2.6)
        with self.assertRaises(ValueError):sample_window(2.2)

    def test_honest_42_pass_or_missing_with_47_manifest_entries(self):
        names,_,_=read_registry()
        labels=names+[x[0] for x in NAMED_VARIANTS]
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            entries=[{"effect":name,"ok":True,
                      "media_qc":{"full_video_and_audio_decode":True,
                                  "decoded_frames":16,"audio_streams":1},
                      "preview_qc":{"visible_change_detected_in_sample":True}}
                     for name in labels]
            (folder/"results.json").write_text(json.dumps(entries))
            report=report_from_gallery(folder,50.4,15.624,{"width":1080,"height":1920})
            self.assertEqual(42,report["technically_passed_effects"])
            self.assertEqual("ALL_42_SHORT_SAMPLE_DECODE_PASS",report["technical_status"])
            self.assertIn("REVIEW REQUIRED",report["creative_status"])
            entries.pop(9)
            (folder/"results.json").write_text(json.dumps(entries))
            report=report_from_gallery(folder,50.4,15.624,{"width":1080,"height":1920})
            self.assertEqual(41,report["technically_passed_effects"])
            self.assertNotEqual("ALL_42_SHORT_SAMPLE_DECODE_PASS",report["technical_status"])
            self.assertIn(names[9],report["technically_failed_or_unverified_effects"])


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe") and
                     (ROOT/"models"/"selfie_segmenter.tflite").is_file(),
                     "Full original-effect Docker runtime required")
class RealRendererDiagnosticSubset(unittest.TestCase):
    def test_small_private_source_excerpt_and_original_effects(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            movie=root/"private_synthetic.mp4"
            subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
              "-f","lavfi","-i","testsrc2=size=360x640:rate=8:duration=3",
              "-f","lavfi","-i","sine=frequency=440:sample_rate=16000:duration=3",
              "-c:v","libx264","-preset","ultrafast","-pix_fmt","yuv420p",
              "-c:a","aac","-shortest",str(movie)],check=True,timeout=30)
            health=run(movie,root/"private-health",only=["slow-push","glass-widgets"])
            self.assertEqual("INCOMPLETE_SUBSET",health["technical_status"])
            self.assertEqual(2,health["technically_passed_effects"])
            self.assertTrue((root/"private-health"/"effect-health-report.json").is_file())
            self.assertTrue((root/"private-health"/"private_source_excerpt.mp4").is_file())
            self.assertFalse((root/"private-health"/"review"/"all-47-effects.jpg").exists())
            for label in ("slow-push","glass-widgets"):
                self.assertTrue((root/"private-health"/"effect-gallery"/(label+".mp4")).is_file())


if __name__=="__main__":unittest.main()
