"""Executive Editorial v2 safety, motion and layout tests."""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("editorial_director",ROOT/"scripts"/"editorial_director.py")
editorial=importlib.util.module_from_spec(spec)
spec.loader.exec_module(editorial)

class EditorialTests(unittest.TestCase):
    def test_fade(self):
        self.assertEqual(0,editorial.opacity_for(0,0,3))
        self.assertAlmostEqual(1,editorial.opacity_for(1,0,3),places=3)
        self.assertEqual(0,editorial.opacity_for(3,0,3))
    def test_valid_story(self):
        story=json.loads((ROOT/"examples/editorial-storyboard.json").read_text(encoding="utf8"))
        self.assertEqual(3,len(editorial.check_story(story,60.71)))
    def test_reject_overlapping_beats(self):
        bad={"beats":[{"kind":"chapter","start":1,"end":3},
                      {"kind":"chapter","start":2,"end":4}]}
        with self.assertRaises(ValueError):editorial.check_story(bad,6)
    def test_reject_oversized_copy(self):
        bad={"beats":[{"kind":"chapter","start":0,"end":1,"headline":"x"*300}]}
        with self.assertRaises(ValueError):editorial.check_story(bad,2)
    def test_keep_graphics_off_center_face(self):
        fonts=ROOT/"fonts"
        if not fonts.is_dir():self.skipTest("Licensed fonts not installed")
        beat={"kind":"opener","start":0,"end":2,
              "eyebrow":"TEST","headline":"Thoughtful direction.",
              "name":"SWARAG","subline":"EXECUTIVE EDITORIAL"}
        alpha=editorial.layout(540,960,beat,fonts).getchannel("A")
        self.assertIsNone(alpha.crop((190,330,350,690)).getbbox())
if __name__=="__main__":unittest.main()
