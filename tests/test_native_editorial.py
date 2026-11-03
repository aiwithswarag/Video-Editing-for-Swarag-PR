"""Regression tests for complete portrait timeline with only edited windows encoded as effects."""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from render_editorial_master import parts
from editorial_director import layout

class NativeEditorialTests(unittest.TestCase):
    def test_segment_boundaries(self):
        beats=[{"kind":"opener","start":.5,"end":1.5,"name":"SWARAG"},
               {"kind":"closing","start":3.5,"end":4.5,"name":"SWARAG"}]
        out=parts(beats,5)
        self.assertEqual(5,len(out))
        self.assertEqual((0.,.5,None),out[0])
        self.assertEqual((1.5,3.5,None),out[2])
        self.assertEqual((4.5,5,None),out[-1])
    def test_full_coverage_without_art(self):
        self.assertEqual([(0.,5,None)],parts([],5))
    def test_safe_approved_style(self):
        fonts=ROOT/"fonts"
        if not fonts.is_dir():self.skipTest("Licensed fonts are not installed")
        result=layout(540,960,{"kind":"opener","name":"SWARAG","subline":"EDITORIAL NOTES"},fonts)
        alpha=result.getchannel("A")
        # The identity-only slate must not paint an unexplained upper gold bar.
        self.assertIsNone(alpha.crop((15,120,190,250)).getbbox())
        # The upper face region is protected.
        self.assertIsNone(alpha.crop((180,310,350,600)).getbbox())

if __name__=="__main__":unittest.main()
