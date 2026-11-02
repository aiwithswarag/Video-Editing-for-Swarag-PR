"""Six-chapter RAG visual direction and real synthetic render acceptance.

No private media, genuine personal transcript, or user-provided voice in CI.
"""
from __future__ import annotations
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
sys.path.insert(0,str(ROOT/"scripts"))
from local_director import draft
from rag_storyboard import compose,recognizable,validate,coverage,rag_intent,explain_unrecognized
from rag_visuals import draw_overlay,geometry,sample_face_crop,LAYOUT_ID
from release_guard import evaluate as gate
from PIL import Image

# Synthetic script preserving only user-authorized fictional policy concepts.
SAMPLE=(
"# 0–3 sec | Citation question\n"
"Your AI cited a source. Can it be wrong?\n"
"# 3–12 sec | Fictional comparison\n"
"These fictional policies: 2024 $100 per night and 2026 $150 per night.\n"
"# 12–20 sec | Outdated answer\n"
"AI answers $100 with a 2024 citation, but it is outdated.\n"
"# 20–33 sec | Explain RAG\n"
"RAG retrieval augmented generation retrieves a document and generates an answer.\n"
"# 33–49 sec | Three checks\n"
"Right version? Does the answer match the source? Authorized access to source?\n"
"# 49–55 sec | Closing\n"
"A citation is where verification starts, not where it ends.\n"
)

class StoryboardTests(unittest.TestCase):
    def test_incomplete_six_section_plan_must_not_silently_fallback(self):
        self.assertTrue(rag_intent(SAMPLE))
        no_headings = __import__("re").sub(
            r"(?m)^# \d+[–-]\d+ sec \|.*$", "", SAMPLE)
        self.assertTrue(rag_intent(no_headings))
        self.assertFalse(recognizable(no_headings))
        self.assertIn("six numbered time headings",explain_unrecognized(no_headings))
        with self.assertRaisesRegex(ValueError,"six numbered time headings"):
            draft("subtle slow-push",no_headings,50.4)
    def test_markdown_bold_script_headings_are_recognized(self):
        bold = __import__("re").sub(
            r"(?m)^# (\d+[–-]\d+ sec \|.*)$",r"**\1**",SAMPLE)
        self.assertTrue(recognizable(bold))
        self.assertEqual(8,len(compose(bold,50.4)))

    def test_rag_detection_is_grounded(self):
        self.assertTrue(recognizable(SAMPLE))
        plan=draft("premium executive reel with a subtle slow-push",SAMPLE,50.4)
        self.assertTrue(plan["requires_six_section_explainer"])
        self.assertEqual(8,len(plan["rag_storyboard"]))
        self.assertEqual(6,len(plan["semantic_sections"]))
        self.assertEqual(["slow-push"],[x["fx"] for x in plan["effects"]])
        self.assertEqual("DRAFT — NOT SPEECH VERIFIED",plan["status"])
        self.assertEqual(42,plan["effect_catalog_size"])
    def test_real_2024_2026_evidence_is_required(self):
        altered=SAMPLE.replace("Fictional comparison","Policy comparison").replace("fictional policies","real company policies")
        self.assertFalse(recognizable(altered))
        self.assertEqual([],compose(altered,50.4))
        altered=SAMPLE.replace("$150","$500")
        self.assertFalse(recognizable(altered))
        self.assertEqual([],compose(altered,50.4))
    def test_reject_missing_graphics_even_with_single_effect_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake=Path(tmp)/"final_master.mp4"
            fake.write_bytes(b"not an actual mp4"*1000)
            report={"technical_status":"PASS","renderer_provenance":{
                "engine_id":"swarag-repository-42-effect-engine","entrypoint":"scripts/fx.py"},
                "selected_effects":["slow-push"],
                "master_sha256":"bad","preview":False,
                "visual_review":{"review_points":[{"time_s":1.0}]},
                "requires_six_section_explainer":True}
            result=gate(report,fake,["slow-push"])
            self.assertEqual("BLOCKED",result["release_status"])
            self.assertTrue(any("RAG narrative" in x for x in result["blocking_errors"]))
    def test_eight_graphics_spread_over_six_sections(self):
        beats=compose(SAMPLE,50.4)
        self.assertEqual(["hook","policies","outdated-answer","rag-flow",
                "verification-checks","closing"],coverage(beats,50.4)["actual_sections"])
        self.assertAlmostEqual(50.4,beats[-1]["end"])
        self.assertAlmostEqual(30.24,beats[4]["start"],places=1)
        self.assertTrue(all(b["end"]>b["start"] for b in beats))
        corrupted=beats[:-1]
        with self.assertRaises(ValueError):validate(corrupted,50.4)
        corrupted=[dict(x) for x in beats];corrupted[2]["kind"]="hook"
        with self.assertRaises(ValueError):validate(corrupted,50.4)
    @unittest.skipUnless((ROOT/"fonts"/"Inter.ttf").is_file(),"Licensed fonts must be installed to draw graphics")
    def test_entire_camera_is_pixel_transparent_all_eight_graphics(self):
        top=geometry(360,640)["camera_bottom"]
        for item in compose(SAMPLE,50.4):
            image=draw_overlay(item["kind"],360,640,ROOT/"fonts")
            self.assertEqual("RGBA",image.mode)
            self.assertEqual((360,640),image.size)
            # Strong contract: NO overlays touch any portion of camera tile,
            # regardless of actor face position or segmentation accuracy.
            self.assertIsNone(image.crop((0,0,360,top)).getchannel("A").getbbox(),
                "Graphics have invaded the real-camera region")
            self.assertEqual(255,image.getpixel((180,600))[3])
    def test_face_safe_split_layout_metadata(self):
        geo=geometry(1080,1920)
        self.assertEqual(1228,geo["camera_bottom"])
        self.assertEqual(1670,geo["text_bottom"])
        self.assertEqual("face-safe-editorial-split-v3",LAYOUT_ID)
    def test_missing_face_detection_always_preserves_original_full_frame(self):
        with tempfile.TemporaryDirectory() as tmp:
            absent=Path(tmp)/"no_detector.onnx"
            # No need for actual face pixels: without verified model we MUST
            # fit the full original camera, not guess a risky crop.
            result=sample_face_crop(Path(tmp)/"source.mp4",360,640,
                                    geometry(360,640)["camera_bottom"],
                                    model=absent)
            self.assertEqual("contain-full-source",result["camera_mode"])
            self.assertIsNone(result["crop_y"])

@unittest.skipUnless(shutil.which("ffmpeg") and (ROOT/"models"/"selfie_segmenter.tflite").is_file(),
                     "Full offline MediaPipe/FFmpeg/fonts are required")
class FullPipelineTest(unittest.TestCase):
    def test_8_graphics_through_original_42_engine_keep_audio_and_frames(self):
        import produce_video as production
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp)
            source=base/"synthetic.mp4"
            subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",
                "-f","lavfi","-i","testsrc2=size=360x640:rate=8:duration=6",
                "-f","lavfi","-i","sine=frequency=420:sample_rate=48000:duration=6",
                "-c:v","libx264","-preset","ultrafast","-pix_fmt","yuv420p",
                "-c:a","aac","-shortest",str(source)],check=True)
            plan=base/"plan.json"
            plan.write_text(json.dumps({"requires_transcript":True,
                "transcript_verified":True,"requires_six_section_explainer":True,
                "effects":[{"fx":"slow-push","start":0,"end":.6,"zoom":1.04}],
                "rag_storyboard":compose(SAMPLE,6)}),encoding="utf-8")
            report=production.release(source,plan,base/"out",
                 look="neutral",width=360,crf=21,frames_per_chunk=48)
            self.assertEqual("PASS",report["technical_status"])
            self.assertEqual("CREATIVE_REVIEW_REQUIRED",report["release_gate_status"])
            self.assertEqual(8,report["rag_graphics_pass"]["graphic_stages"])
            self.assertTrue(report["rag_graphics_pass"]["face_safe_layout"])
            self.assertFalse(report["rag_graphics_pass"]["graphics_overlap_camera_pixels"])
            self.assertEqual(LAYOUT_ID,report["rag_graphics_pass"]["layout_id"])
            self.assertEqual("contain-full-source",report["rag_graphics_pass"]["camera"]["camera_mode"])
            self.assertEqual(6,len(report["editorial_sections_covered"]))
            self.assertEqual(48,report["qa"]["output_media"]["frames"])
            self.assertTrue(report["qa"]["audio_bitstream_identical"])
            self.assertEqual(report["original_audio_md5"],report["master_audio_md5"])
            self.assertGreater(len(report["visual_review"]["review_points"]),8)
            self.assertTrue((base/"out"/"final_master.mp4").stat().st_size>4000)

if __name__=="__main__":
    unittest.main()
