"""Real 42-effect finish policy and geometry regressions.

No user image/video/audio is embedded in tests. These are engineering contracts,
not an artistic endorsement of the actual 50.4-second camera film.
"""
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
sys.path.insert(0,str(ROOT/"scripts"))
from effect_catalog import read_registry
from brand_presets import apply_brand

try:
    import fx
    import numpy as np
    from PIL import Image
    HAVE_RENDERER=True
except ImportError:
    HAVE_RENDERER=False


class EveryEffectFinishContract(unittest.TestCase):
    def test_42_effects_have_individual_production_options(self):
        names,_,_=read_registry()
        self.assertEqual(len(names),42)
        p=json.loads((ROOT/"branding"/"executive.json").read_text(encoding="utf8"))
        self.assertEqual(set(names),set(p["effect_defaults"]))
        self.assertEqual(42,p["finish_policy"]["effects_with_explicit_defaults"])
        self.assertEqual("SWARAG-42-EFFECT-FINISH-2026-11-04",
                         p["finish_policy"]["version"])
        resolved=apply_brand([{"fx":name,"start":0,"end":1.8} for name in names])
        self.assertEqual(42,len(resolved))
        self.assertTrue(all(e.get("face_priority") is True for e in resolved))
        self.assertTrue(all(e["end"]>e["start"] for e in resolved))

    def test_camera_zoom_and_spin_suitable_for_executive_context(self):
        names,_,_=read_registry()
        defaults=json.loads((ROOT/"branding"/"executive.json").read_text())["effect_defaults"]
        for name in names:
            with self.subTest(effect=name):
                options=defaults[name]
                if "zoom" in options:
                    self.assertTrue(1 <= float(options["zoom"]) <= 1.15)
                if "spin" in options:
                    self.assertLessEqual(abs(float(options["spin"])),2)
        self.assertLessEqual(defaults["slow-push"]["zoom"],1.10)
        self.assertEqual(0,defaults["slow-push"]["blur"])
        self.assertEqual("executive",defaults["match-cut"]["look"])

    def test_all_original_effect_names_are_still_registered(self):
        names,_,_=read_registry()
        from render_effect_gallery import NAMED_VARIANTS
        self.assertEqual(5,len(NAMED_VARIANTS))
        self.assertEqual(47,len(names)+len(NAMED_VARIANTS))


@unittest.skipUnless(HAVE_RENDERER, "Original OpenCV effects engine required")
class FinishedFrameGeometry(unittest.TestCase):
    def canvas(self, masked=False):
        c=SimpleNamespace(W=240,H=426,fx=120.,fy=215.,fw=38.,
            img=np.zeros((426,240,3),np.float32),
            m=np.zeros((426,240),np.float32),
            face_priority=True,current_fx="checklist",graphic_region="below",
            t=1.0,lt=.9,fps=8.)
        if masked:
            c.m[170:255,85:155]=1.
        return c

    def test_full_graphic_moves_instead_of_cutting_oval_hole(self):
        c=self.canvas()
        image=Image.new("RGBA",(120,68),(255,255,255,255))
        self.assertTrue(fx.overlaps_face(c,60,175,120,68))
        fx.comp(c,image,60,175,guard=True)
        self.assertEqual(float(c.img[215,120,0]),0.)
        self.assertGreater(float(c.img[355,120,0]),.90)
        self.assertGreater(float(c.img[377,120,0]),.90)
        self.assertEqual(getattr(c,"layout_conflicts",0),0)

    def test_behind_uses_real_mask_without_invented_oval_halo(self):
        c=self.canvas(masked=True)
        image=Image.new("RGBA",(240,426),(255,0,0,255))
        fx.comp(c,image,0,0,behind=True)
        self.assertEqual(float(c.img[220,120,0]),0.)
        # Geometric ellipse used to punch a hole here even though this pixel
        # is not in the real person segmentation.
        self.assertGreater(float(c.img[160,120,0]),.97)

    def test_unbranded_original_has_no_automatic_panel_relocation(self):
        c=self.canvas()
        c.face_priority=False
        image=Image.new("RGBA",(100,65),(255,0,0,255))
        fx.comp(c,image,80,180,guard=False)
        self.assertGreater(float(c.img[215,120,0]),.98)

    def test_exit_animation_not_clamped_onto_face(self):
        c=self.canvas()
        self.assertEqual((5,-120),fx.safe_graphic_xy(c,5,-120,120,70,"above"))

    def test_editorial_headline_is_placed_above_face(self):
        c=self.canvas()
        image=Image.new("RGBA",(210,42),(245,242,236,255))
        cy,scale=fx.editorial_headline_anchor(c,image)
        self.assertLess(cy+image.height*scale/2,
                        fx.face_protection_rect(c)[1])
        self.assertGreater(scale,0.5)

    def test_toggle_rows_must_fit_and_keep_whole_card(self):
        c=self.canvas()
        c.graphic_region="above"
        e=SimpleNamespace(o={"text":"CLARITY|GOVERNANCE|OUTCOMES",
                             "pos":"above","zoom":1.0},
                          state={},d=2.25,start=0.)
        fx.fx_apple_toggles(c,e)
        self.assertEqual(getattr(c,"layout_conflicts",0),0)
        self.assertEqual(float(c.img[215,120].max()),0.)
        over=SimpleNamespace(o={"text":"A UNVERIFIABLY LONG CLAIM THAT WILL NOT FIT"},
                             state={},d=2.25,start=0.)
        with self.assertRaises(ValueError):
            fx.fx_apple_toggles(self.canvas(),over)

    def test_executive_match_cut_uses_actual_short_article_without_wallpaper(self):
        c=self.canvas(masked=True)
        c.img[:]=.30
        e=SimpleNamespace(o={"look":"executive","text":"POLICY",
                             "article_text":"The checked document establishes the current version.",
                             "source_verified":True,"color":"#2C9A90"},
                          state={},d=2.25,start=0.)
        rendered=fx.match_page_editorial(c,e,0)
        self.assertEqual(rendered.shape,(426,240,3))
        self.assertAlmostEqual(float(rendered[400,120,0]),int(.3*255),delta=2)
        self.assertNotEqual(int(rendered[45,120,0]),int(.3*255))


if __name__=="__main__":
    unittest.main()
