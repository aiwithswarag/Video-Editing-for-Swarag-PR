import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from brand_presets import apply_brand
class TestExecutiveBrand(unittest.TestCase):
    def test_brand_applies(self):
        out=apply_brand([{"fx":"backdrop-word","start":0,"end":1,"text":"Outcome"}])
        self.assertEqual("#B79660",out[0]["color"])
    def test_explicit_preference_wins(self):
        plan=[{"fx":"backdrop-word","start":0,"end":1,"color":"#FFFFFF"}]
        self.assertEqual("#FFFFFF",apply_brand(plan)[0]["color"])
    def test_original_style_opt_out(self):
        plan=[{"fx":"glass-widgets","start":0,"end":1}]
        self.assertNotIn("look",apply_brand(plan,"none")[0])
        self.assertEqual("standard",apply_brand(plan)[0]["look"])
    def test_face_priority_is_default_for_every_executive_effect(self):
        names=["slow-push","glass-widgets","broll-split","match-cut","red-collage"]
        result=apply_brand([{"fx":name,"start":0,"end":1} for name in names])
        self.assertTrue(all(x["face_priority"] is True for x in result))
        # User opt-out remains available for intentionally face-touching art
        edited=apply_brand([{"fx":"scribble","start":0,"end":1,
                             "face_priority":False}])
        self.assertIs(edited[0]["face_priority"],False)
        self.assertNotIn("face_priority",apply_brand(
            [{"fx":"slow-push","start":0,"end":1}],"none")[0])
    def test_brand_name_validation(self):
        with self.assertRaises(ValueError):
            apply_brand([{"fx":"slow-push","start":0,"end":1}],"unknown")
    def test_orbit_executive_cards_default(self):
        plan=[{"fx":"orbit","start":0,"end":2}]
        branded=apply_brand(plan)[0]
        self.assertTrue(branded["brand_cards"])
        self.assertIn("STRATEGY",branded["labels"])
        self.assertNotIn("brand_cards",apply_brand(plan,"none")[0])
    def test_orbit_user_images_take_priority(self):
        script=(ROOT/"scripts/fx.py").read_text(encoding="utf8")
        self.assertIn("if f.o.get('brand_cards') and not f.o.get('images')",script)
        self.assertIn("else load_cards(f.o.get('images'), thumbs)",script)
        self.assertIn("Approved card media directory does not exist",script)
    def test_no_inherited_creator_defaults(self):
        s=(ROOT/"scripts/fx.py").read_text(encoding="utf8")
        for forbidden in ["'CLAUDE'","'VIBE'","@vibha.in.progress","22 effects","the art of the|effortless edit"]:
            self.assertNotIn(forbidden,s)
