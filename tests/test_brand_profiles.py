import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from brand_presets import apply_brand
class TestExecutiveBrand(unittest.TestCase):
    def test_brand_applies(self):
        out=apply_brand([{"fx":"backdrop-word","start":0,"end":1,"text":"Outcome"}])
        self.assertEqual("#C5A46D",out[0]["color"])
    def test_explicit_preference_wins(self):
        plan=[{"fx":"backdrop-word","start":0,"end":1,"color":"#FFFFFF"}]
        self.assertEqual("#FFFFFF",apply_brand(plan)[0]["color"])
    def test_original_style_opt_out(self):
        plan=[{"fx":"glass-widgets","start":0,"end":1}]
        self.assertNotIn("look",apply_brand(plan,"none")[0])
        self.assertEqual("simple",apply_brand(plan)[0]["look"])
    def test_brand_name_validation(self):
        with self.assertRaises(ValueError):
            apply_brand([{"fx":"slow-push","start":0,"end":1}],"unknown")
    def test_no_inherited_creator_defaults(self):
        s=(ROOT/"scripts/fx.py").read_text(encoding="utf8")
        for forbidden in ["'CLAUDE'","'VIBE'","@vibha.in.progress","22 effects"]:
            self.assertNotIn(forbidden,s)
