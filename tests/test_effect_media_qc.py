"""Objective coverage tests for Swarag's 42 independently rendered effect clips."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from effect_media_qc import preview_evidence,motion_evidence


class PreviewQC(unittest.TestCase):
    def test_real_png_and_visible_change_evidence(self):
        with tempfile.TemporaryDirectory() as t:
            t=Path(t)
            original=t/"baseline.png"
            changed=t/"effect.png"
            Image.new("RGB",(360,640),(45,53,68)).save(original)
            Image.new("RGB",(360,640),(156,78,26)).save(changed)
            result=preview_evidence(changed,360,640,original)
            self.assertTrue(result["visible_change_detected_in_sample"])
            self.assertGreater(result["mean_abs_change_vs_source_rgb"],5)
            same=preview_evidence(original,360,640,original)
            self.assertFalse(same["visible_change_detected_in_sample"])
            self.assertIn("LOW_VARIANCE_PREVIEW",same["warnings"][0])
            self.assertTrue(any("NO_CLEAR_VISIBLE_CHANGE" in w for w in same["warnings"]))
    def test_wrong_size_or_corrupt_preview_is_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"a.png"
            Image.new("RGB",(360,640),(0,0,0)).save(p)
            with self.assertRaisesRegex(ValueError,"Wrong preview dimensions"):
                preview_evidence(p,240,426)
            p.write_bytes(b"not a valid PNG"*100)
            with self.assertRaisesRegex(ValueError,"does not decode"):
                preview_evidence(p,360,640)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),"FFmpeg required")
class MotionQC(unittest.TestCase):
    def movie(self,target,with_audio=True):
        cmd=["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
             "-f","lavfi","-i","testsrc2=size=360x640:rate=8:duration=2"]
        if with_audio:
            cmd+=["-f","lavfi","-i","sine=frequency=440:sample_rate=16000:duration=2"]
        cmd+=["-c:v","libx264","-preset","ultrafast","-pix_fmt","yuv420p"]
        if with_audio:cmd+=["-c:a","aac","-shortest"]
        cmd+=[str(target)]
        subprocess.run(cmd,check=True,timeout=30)
    def test_complete_aac_and_frame_decode_required(self):
        with tempfile.TemporaryDirectory() as t:
            file=Path(t)/"valid.mp4"
            self.movie(file)
            result=motion_evidence(file,360,640,min_frames=10)
            self.assertTrue(result["full_video_and_audio_decode"])
            self.assertGreaterEqual(result["decoded_frames"],10)
            self.assertGreaterEqual(result["audio_streams"],1)
            with self.assertRaisesRegex(ValueError,"Wrong motion dimensions"):
                motion_evidence(file,240,426)
            with self.assertRaisesRegex(ValueError,"Too few decodable frames"):
                motion_evidence(file,360,640,min_frames=1000)
    def test_video_without_audio_must_fail(self):
        with tempfile.TemporaryDirectory() as t:
            file=Path(t)/"silent.mp4"
            self.movie(file,with_audio=False)
            with self.assertRaisesRegex(ValueError,"audio track"):
                motion_evidence(file,360,640,min_frames=10)


if __name__=="__main__":unittest.main()
