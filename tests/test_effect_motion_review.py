"""The private 47-clip motion review must remain evidence, never approval."""
import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

from PIL import Image

from tools.effect_motion_review import create_motion_review


def fake_samples(_):
    return [Image.new("RGB", (240, 426), color)
            for color in ("#121b26", "#2c9a90", "#b79660")]


class MotionReviewTests(unittest.TestCase):
    def test_all_clips_packaged_with_three_separated_frames(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            gallery = root / "gallery"
            gallery.mkdir()
            for label in ("slow-push", "glass-widgets"):
                (gallery / (label + ".mp4")).write_bytes(b"x" * 3000)
            with patch("tools.effect_motion_review.sampled_frames", side_effect=fake_samples):
                outcome = create_motion_review(gallery, root / "review",
                                                ["slow-push", "glass-widgets"])
            self.assertEqual("MOTION_SAMPLES_AVAILABLE", outcome["status"])
            self.assertEqual(2, outcome["clips_packaged"])
            self.assertEqual(3, outcome["frames_per_clip"])
            self.assertTrue((root / "review" / "all-47-motion-review.jpg").is_file())
            with ZipFile(root / "review" / "all-47-motion-clips.zip") as archive:
                self.assertIn("clips/slow-push.mp4", archive.namelist())
                self.assertIn("clips/glass-widgets.mp4", archive.namelist())
                manifest = json.loads(archive.read("review-manifest.json"))
                self.assertEqual(2, len(manifest["effects"]))
                self.assertIn("NOT CREATIVE APPROVAL", manifest["purpose"])

    def test_missing_or_unreadable_clips_are_not_passed(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            gallery = root / "gallery"
            gallery.mkdir()
            (gallery / "slow-push.mp4").write_bytes(b"x" * 3000)
            with patch("tools.effect_motion_review.sampled_frames",
                       side_effect=ValueError("bad video")):
                outcome = create_motion_review(gallery, root / "review",
                                                ["slow-push", "orbit"])
            self.assertEqual("INCOMPLETE_MOTION_SAMPLES", outcome["status"])
            self.assertEqual(0, outcome["clips_packaged"])
            self.assertEqual(["slow-push", "orbit"],
                             outcome["missing_or_unreadable_clips"])
            with ZipFile(root / "review" / "all-47-motion-clips.zip") as archive:
                self.assertNotIn("clips/slow-push.mp4", archive.namelist())
                self.assertNotIn("clips/orbit.mp4", archive.namelist())


@unittest.skipUnless(shutil.which("ffmpeg") and
                     importlib.util.find_spec("cv2") is not None,
                     "Real FFmpeg/OpenCV decode runtime required")
class ActualMotionDecodeTests(unittest.TestCase):
    def test_ffmpeg_mp4_is_sampled_at_three_distinct_times(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            gallery = root / "gallery"
            gallery.mkdir()
            clip = gallery / "slow-push.mp4"
            subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
                "-y", "-f", "lavfi",
                "-i", "testsrc2=size=240x426:rate=8:duration=2",
                "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                str(clip),
            ], check=True, timeout=30)
            result = create_motion_review(gallery, root / "review", ["slow-push"])
            self.assertEqual("MOTION_SAMPLES_AVAILABLE", result["status"])
            with Image.open(root / "review" / "all-47-motion-review.jpg") as img:
                self.assertGreater(img.width, 300)


if __name__ == "__main__":
    unittest.main()
