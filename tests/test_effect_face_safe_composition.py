"""Face-safe composition regressions for actual original effects.

Synthetic context only: no user video, voice, screenshots or other private media.
Motion and mobile typography still require human playback approval.
"""
import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
HAS_CV2=importlib.util.find_spec("cv2") is not None
HAS_NUMPY=importlib.util.find_spec("numpy") is not None
FONTS=(ROOT/"fonts"/"Inter.ttf").exists()

@unittest.skipUnless(HAS_CV2 and HAS_NUMPY and FONTS,
                     "Original OpenCV engine and Swarag fonts required")
class FaceSafeEffectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import numpy as np
        from PIL import Image
        sys.path.insert(0,str(ROOT/"scripts"))
        import fx
        cls.np=np
        cls.Image=Image
        cls.fx=fx

    def canvas(self):
        return SimpleNamespace(
            W=360,H=640,fx=180.0,fy=215.0,fw=48.0,lt=.95,
            img=self.np.zeros((640,360,3),dtype=self.np.float32),
            m=self.np.zeros((640,360),dtype=self.np.float32)
        )

    def test_behind_keeps_real_face_even_on_empty_person_mask(self):
        c=self.canvas()
        panel=self.Image.new("RGBA",(220,280),(255,0,0,255))
        self.fx.comp(c,panel,70,100,behind=True)
        self.assertLess(float(c.img[215,180,0]),.03)
        self.assertGreater(float(c.img[115,85,0]),.9)

    def test_guard_keeps_face_even_on_empty_person_mask(self):
        c=self.canvas()
        panel=self.Image.new("RGBA",(220,280),(255,0,0,255))
        self.fx.comp(c,panel,70,100,guard=True)
        self.assertLess(float(c.img[215,180,0]),.03)
        self.assertGreater(float(c.img[115,85,0]),.9)

    def test_broll_label_stays_in_upper_broll_pane(self):
        c=self.canvas()
        c.img[:]=.35
        e=SimpleNamespace(o={},cards=[self.Image.new("RGB",(360,640),(90,110,120))],
                          state={},d=1.7,start=0.0)
        with patch.object(self.fx,"place") as place:
            self.fx.fx_broll_split(c,e)
            self.assertTrue(place.called)
            args=place.call_args.args
            cy=float(args[3])
            self.assertLess(cy,c.H*.31)
            self.assertGreater(c.fy,c.H*.55)
            self.assertGreater(c.fy-cy,c.fw*2.5)

    def test_invalid_approved_media_never_falls_back_to_selfies(self):
        missing=ROOT/"PRIVATE"/"this-media-directory-must-not-exist"
        with self.assertRaises(ValueError):
            self.fx.load_cards(str(missing),[self.Image.new("RGB",(10,10))])

    def test_swarag_concept_cards_are_distinct(self):
        cards=self.fx.executive_cards("STRATEGY|DELIVERY|GOVERNANCE")
        self.assertEqual(3,len(cards))
        self.assertEqual(3,len(set(img.tobytes()[:3000] for img in cards)))

if __name__=="__main__":
    unittest.main()
