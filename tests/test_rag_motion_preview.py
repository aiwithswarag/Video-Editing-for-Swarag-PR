"""Validate native RAG glass motion preview on synthetic private-only media."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from rag_glass_preview import preview_motion_clip
from rag_storyboard import KIND_NAMES,KIND_TO_SECTION


def sample_stages():
    return [
        {"kind":kind, "section":KIND_TO_SECTION[kind],
         "start":round(i*1.2,3), "end":round((i+1)*1.2,3)}
        for i,kind in enumerate(KIND_NAMES)
    ]


class MotionPreviewContractTests(unittest.TestCase):
    def test_missing_video_cannot_generate_approval_preview(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(FileNotFoundError):
                preview_motion_clip(Path(temp)/"missing.mp4",sample_stages(),
                                    Path(temp)/"preview.mp4")


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe") and
                     (ROOT/"fonts"/"Inter.ttf").is_file() and
                     (ROOT/"models"/"selfie_segmenter.tflite").is_file(),
                     "Offline FFmpeg, fonts and original MediaPipe model needed")
class NativeGlassMotionTest(unittest.TestCase):
    def test_three_real_fx_glass_samples_have_audio(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)
            source=folder/"synthetic-private.mp4"
            target=folder/"rag-preview.mp4"
            subprocess.run([
                "ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
                "-f","lavfi","-i","testsrc2=size=360x640:rate=8:duration=9.6",
                "-f","lavfi","-i","sine=frequency=440:sample_rate=16000:duration=9.6",
                "-c:v","libx264","-preset","ultrafast","-pix_fmt","yuv420p",
                "-c:a","aac","-shortest",str(source),
            ],check=True,timeout=45)
            report=preview_motion_clip(source,sample_stages(),target,width=360,fps=8)
            self.assertTrue(target.is_file())
            self.assertEqual(["policies","rag-flow","check-3"],report["stage_kinds"])
            self.assertEqual("glass-widgets",report["original_effect"])
            self.assertIn("REVIEW REQUIRED",report["creative_status"])
            probe=subprocess.run([
                "ffprobe","-v","error","-show_entries",
                "stream=codec_type,width,height:format=duration",
                "-of","json",str(target),
            ],capture_output=True,text=True,check=True,timeout=30)
            info=json.loads(probe.stdout)
            self.assertGreater(float(info["format"]["duration"]),2.5)
            self.assertTrue(any(x["codec_type"]=="audio" for x in info["streams"]))
            video=next(x for x in info["streams"] if x["codec_type"]=="video")
            self.assertEqual((360,640),(int(video["width"]),int(video["height"])))


if __name__=="__main__":
    unittest.main()
