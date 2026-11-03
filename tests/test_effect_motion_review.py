"""The private 47-clip motion review must remain evidence, never approval."""
import json
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


if __name__ == "__main__":
    unittest.main()
