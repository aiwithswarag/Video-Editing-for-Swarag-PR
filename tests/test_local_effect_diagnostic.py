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
from types import SimpleNamespace
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from local_effect_diagnostic import sample_window,report_from_gallery,run,recover_existing
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


    def test_failed_effect_includes_exact_reason_and_renderer_fingerprint(self):
        names,_,_=read_registry()
        labels=names+[x[0] for x in NAMED_VARIANTS]
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)
            items=[]
            for label in labels:
                broken=label=="tier-list"
                items.append({
                    "effect":label,"ok":not broken,
                    "preview":None if broken else label+".png",
                    "motion":None if broken else label+".mp4",
                    "log":("Traceback (most recent call last):\\n"
                           "ValueError: PANEL_DOES_NOT_FIT_BELOW" if broken else ""),
                    "media_qc":{"full_video_and_audio_decode":not broken},
                    "preview_qc":{"visible_change_detected_in_sample":not broken}})
            (folder/"results.json").write_text(json.dumps(items))
            report=report_from_gallery(folder,50.4,15.624,
                                        {"width":1080,"height":1920})
            self.assertEqual(2,report["schema_version"])
            self.assertEqual(41,report["technically_passed_effects"])
            self.assertEqual("PANEL_DOES_NOT_FIT_BELOW",
                  report["per_effect_runtime"]["tier-list"]["error_code"])
            self.assertFalse(
                report["per_effect_runtime"]["tier-list"]["preview_rendered"])
            self.assertRegex(report["renderer_fingerprint_sha256_16"],
                             r"^[0-9a-f]{16}$")

    def _complete_manifest(self, directory):
        names,_,_=read_registry()
        labels=names+[name for name,_,_ in NAMED_VARIANTS]
        gallery=directory/"effect-gallery"
        gallery.mkdir(parents=True,exist_ok=True)
        gallery.joinpath("results.json").write_text(json.dumps([
            {"effect":name,"ok":True,
             "media_qc":{"full_video_and_audio_decode":True},
             "preview_qc":{"visible_change_detected_in_sample":True}}
            for name in labels
        ]),encoding="utf8")
        return gallery

    def test_full_gallery_postprocess_uses_real_registry_names(self):
        """Regression: undefined 'names' used to crash after 47 PASS lines."""
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            source=folder/"video.mp4"
            source.write_bytes(b"private-source")
            output=folder/"diagnostic"
            self._complete_manifest(output)
            with mock.patch("local_effect_diagnostic.probe",
                            return_value=(50.4,{"width":1080,"height":1920})), \
                 mock.patch("local_effect_diagnostic.subprocess.run",
                            return_value=SimpleNamespace(returncode=0)), \
                 mock.patch("local_effect_diagnostic.make_review_sheet") as sheet, \
                 mock.patch("local_effect_diagnostic.create_motion_review",
                            return_value={"status":"MOTION_SAMPLES_AVAILABLE",
                                          "clips_packaged":47}):
                report=run(source,output)
            self.assertTrue(sheet.called)
            self.assertEqual(42,report["technically_passed_effects"])
            self.assertEqual("READY",report["review_artifact_status"])
            self.assertEqual("ALL_42_SHORT_SAMPLE_DECODE_PASS",report["technical_status"])
            self.assertTrue((output/"effect-health-report.json").is_file())

    def test_secondary_sheet_crash_preserves_full_technical_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            source=folder/"video.mp4"
            source.write_bytes(b"private-source")
            output=folder/"diagnostic"
            self._complete_manifest(output)
            with mock.patch("local_effect_diagnostic.probe",
                            return_value=(50.4,{"width":1080,"height":1920})), \
                 mock.patch("local_effect_diagnostic.subprocess.run",
                            return_value=SimpleNamespace(returncode=0)), \
                 mock.patch("local_effect_diagnostic.make_review_sheet",
                            side_effect=RuntimeError("mock art failure")):
                report=run(source,output)
            saved=json.loads((output/"effect-health-report.json").read_text(encoding="utf8"))
            self.assertEqual(42,saved["technically_passed_effects"])
            self.assertEqual("FAILED",saved["review_artifact_status"])
            self.assertEqual("RuntimeError",saved["review_artifact_error_type"])
            self.assertIn("REVIEW REQUIRED",saved["creative_status"])

    def test_recover_completed_gallery_without_any_new_render(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            source=folder/"video.mp4"
            source.write_bytes(b"private-source")
            output=folder/"diagnostic"
            self._complete_manifest(output)
            with mock.patch("local_effect_diagnostic.probe",
                            return_value=(50.4,{"width":1080,"height":1920})), \
                 mock.patch("local_effect_diagnostic.subprocess.run") as render, \
                 mock.patch("local_effect_diagnostic.make_review_sheet"), \
                 mock.patch("local_effect_diagnostic.create_motion_review",
                            return_value={"status":"MOTION_SAMPLES_AVAILABLE",
                                          "clips_packaged":47}):
                report=recover_existing(source,output)
            render.assert_not_called()
            self.assertTrue(report["recovered_without_rerender"])
            self.assertEqual("READY",report["review_artifact_status"])
            self.assertEqual(42,report["technically_passed_effects"])
            self.assertTrue((output/"effect-health-report.json").is_file())

    def test_recovery_refuses_missing_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/"video.mp4"
            source.write_bytes(b"private-source")
            with self.assertRaises(ValueError):
                recover_existing(source,Path(tmp)/"diagnostic")


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
