"""Visual regression contracts for the 11 observed P0 camera-preview defects.

These use generated canvas pixels only. They exercise the actual FX engine
and explicit semantic placement evidence, not private media or invented
creative approval.
"""
import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
HAS_DEPS=all(importlib.util.find_spec(m) is not None
             for m in ('numpy','cv2','PIL')) and (ROOT/'fonts'/'Inter.ttf').is_file()

@unittest.skipUnless(HAS_DEPS,'Requires original OpenCV renderer and fonts')
class CriticalFrameVisibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import numpy as np
        sys.path.insert(0,str(ROOT/'scripts'))
        import fx
        from PIL import Image
        cls.fx=fx
        cls.np=np
        cls.Image=Image

    def canvas(self,effect):
        import numpy as np
        a=np.empty((426,240,3),dtype=np.float32)
        a[:]=(.48,.43,.37)
        return SimpleNamespace(W=240,H=426,fx=120.,fy=198.,fw=34.,
            t=1.,lt=1.,fps=8.,img=a,m=np.zeros((426,240),dtype=np.float32),
            face_priority=True,current_fx=effect,graphic_region=None,
            layout_conflicts=0,visible_safe_panels=0)

    def effect(self,name,**opts):
        return SimpleNamespace(o=opts,d=2.25,start=0.,state={},cards=[
            self.Image.new('RGB',(200,300),(40+30*i,70+20*i,90+15*i))
            for i in range(4)])

    def assert_safe(self,c,region=None):
        self.assertGreater(c.visible_safe_panels,0,
                           'Visible panel disappeared from a technically valid MP4')
        self.assertEqual(0,c.layout_conflicts)
        self.assertEqual(c.img.shape,(426,240,3))
        self.assertTrue(self.np.isfinite(c.img).all())

    def test_checklist_is_visible_in_safe_region(self):
        c=self.canvas('checklist')
        self.fx.fx_checklist(c,self.effect('checklist'))
        self.assert_safe(c)

    def test_standard_graph_is_visible_in_safe_region(self):
        c=self.canvas('liquid-glass-graph')
        self.fx.fx_liquid_glass_graph(c,self.effect(
            'liquid-glass-graph',hypothetical_example=True,
            text='ILLUSTRATIVE',color='#2C9A90'))
        self.assert_safe(c)

    def test_full_phone_fan_is_one_safe_composite(self):
        c=self.canvas('phone-fan')
        self.fx.fx_phone_fan(c,self.effect('phone-fan'))
        self.assert_safe(c)
        self.assertGreater(float(self.np.abs(c.img-.45).sum()),1000)

    def test_tier_rows_not_hidden_by_guard(self):
        c=self.canvas('tier-list')
        self.fx.fx_tier_list(c,self.effect('tier-list'))
        self.assert_safe(c)

    def test_profile_wall_avoids_head_cutout(self):
        c=self.canvas('profile-wall')
        self.fx.fx_profile_wall(c,self.effect('profile-wall'))
        self.assertGreaterEqual(c.visible_safe_panels,2)
        self.assertEqual(0,c.layout_conflicts)

    def test_swipe_has_no_bright_diagonal_crossing_real_face(self):
        c=self.canvas('swipe')
        self.fx.fx_swipe(c,self.effect('swipe'))
        self.assert_safe(c)
        # The original swipe line was solid white at the centre of the face.
        patch=c.img[164:235,94:145]
        self.assertLess(float(patch.max()),.99)

    def test_cover_star_title_group_is_complete(self):
        c=self.canvas('cover-star')
        self.fx.fx_cover_star(c,self.effect('cover-star'))
        self.assert_safe(c)

    def test_editorial_cover_has_no_cut_through_speaker(self):
        c=self.canvas('cover-star')
        self.fx.cover_editorial(c,self.effect('cover-star'))
        self.assert_safe(c)

    def test_timeline_preserves_original_skin_and_shows_edit_ui(self):
        c=self.canvas('timeline')
        original=c.img.copy()
        self.fx.fx_timeline(c,self.effect('timeline',look='studio'))
        self.assert_safe(c)
        self.np.testing.assert_allclose(c.img[198,120],original[198,120],
                                        atol=.04)

    def test_below_toggle_remains_below_actual_face(self):
        c=self.canvas('apple-toggles')
        captured=[]
        original=self.fx.place
        def spy(ctx,im,cx,cy,*args,**kwargs):
            captured.append((cy,im.height*kwargs.get('scale',1.0)))
            return original(ctx,im,cx,cy,*args,**kwargs)
        with patch.object(self.fx,'place',side_effect=spy):
            self.fx.fx_apple_toggles(c,self.effect('apple-toggles',
                          pos='below',text='CLARITY|GOVERNANCE|OUTCOMES'))
        self.assert_safe(c)
        self.assertTrue(captured)
        face_bottom=self.fx.face_protection_rect(c)[3]
        self.assertGreater(captured[-1][0]-captured[-1][1]/2,face_bottom)

    def test_no_safe_region_fails_explicitly_instead_of_silently(self):
        c=self.canvas('checklist')
        c.fw=110.
        with self.assertRaisesRegex(ValueError,
                                    'NO_SAFE_REGION|PANEL_DOES_NOT_FIT'):
            self.fx.safe_panel_layout(c,200,160,'below',min_scale=.6)

    def test_unbranded_original_guard_still_available(self):
        c=self.canvas('swipe')
        c.face_priority=False
        self.fx.fx_swipe(c,self.effect('swipe'))
        self.assertTrue(self.np.isfinite(c.img).all())


    def test_reported_missing_and_unverified_effects_across_realistic_portrait_geometry(self):
        """The known 37/42 local regression must not recur on portrait frames.

        Six generic speaker bounding boxes at the two diagnostic resolutions
        cover different face positions; this does not replace real-video QA.
        """
        for W,H in ((240,426),(360,640)):
            for center_frac,fw_frac in ((.45,.14),(.53,.17),(.58,.19)):
                for label in ('tier-list','phone-fan','checklist','timeline',
                              'liquid-glass-graph','liquid-glass-graph-bento',
                              'apple-toggles-below'):
                    with self.subTest(frame=(W,H),center=center_frac,
                                      effect=label):
                        c=self.canvas(label)
                        c.W=W;c.H=H;c.fx=W*.5;c.fy=H*center_frac
                        c.fw=W*fw_frac;c.t=1.0;c.lt=1.0
                        c.img=self.np.full((H,W,3),
                          (.48,.43,.37),dtype=self.np.float32)
                        c.m=self.np.zeros((H,W),dtype=self.np.float32)
                        opts={'hypothetical_example':True} if label.startswith(
                              'liquid-glass-graph') else {}
                        if label=='liquid-glass-graph-bento':
                            opts.update(look='bento')
                        if label=='apple-toggles-below':
                            opts.update(pos='below',
                                text='CLARITY|GOVERNANCE|OUTCOMES')
                        e=self.effect(label,**opts)
                        if label=='tier-list':
                            self.fx.fx_tier_list(c,e)
                        elif label=='phone-fan':
                            self.fx.fx_phone_fan(c,e)
                        elif label=='checklist':
                            self.fx.fx_checklist(c,e)
                        elif label=='timeline':
                            self.fx.fx_timeline(c,e)
                        elif label.startswith('liquid-glass-graph'):
                            self.fx.fx_liquid_glass_graph(c,e)
                        elif label=='apple-toggles-below':
                            self.fx.fx_apple_toggles(c,e)
                        self.assertGreaterEqual(
                            c.visible_safe_panels,1,'Entire panel disappeared')
                        self.assertEqual(getattr(c,'layout_conflicts',0),0)
                        self.assertTrue(self.np.isfinite(c.img).all())
                        # A drawn panel must change pixels, not merely set an
                        # internal counter without compositing any image.
                        self.assertGreater(
                            float(self.np.abs(c.img-
                               self.np.float32((.48,.43,.37))).sum()),30)

    def test_visibility_counter_only_increases_after_pixels_are_drawn(self):
        c=self.canvas('checklist')
        blank=self.Image.new('RGBA',(90,35),(0,0,0,0))
        with self.assertRaisesRegex(ValueError,
                                    'SAFE_PANEL_NOT_COMPOSITED_ABOVE'):
            self.fx.place_safe_panel(c,blank,'above',alpha=1,
                                      min_scale=.2)
        self.assertEqual(c.visible_safe_panels,0)



if __name__=='__main__':
    unittest.main()
