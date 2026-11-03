"""Creative focus labels supplement technical QA; never certify visual quality."""
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from effect_catalog import read_registry
from effect_creative_review import review_focus,report_for

class CreativeFocusTests(unittest.TestCase):
    def test_every_registered_effect_has_a_human_review_prompt(self):
        names,_,_=read_registry()
        self.assertEqual(42,len(names))
        all_focus=report_for(names)
        self.assertEqual(42,len(all_focus))
        self.assertTrue(all(isinstance(v,list) and v for v in all_focus.values()))

    def test_known_camera_visual_risks_are_explicit(self):
        cases={
            "broll-split": ("FACE_CLEARANCE","SOURCE_ASSETS","CLAIM_PROVENANCE"),
            "profile-wall": ("SOURCE_ASSETS","CLAIM_PROVENANCE"),
            "the-bill": ("MOBILE_TYPE",),
            "match-cut": ("MOBILE_TYPE","CLAIM_PROVENANCE"),
            "cover-star-editorial": ("FACE_CLEARANCE","MOBILE_TYPE"),
            "glass-widgets-simple": ("MOBILE_TYPE","CLAIM_PROVENANCE"),
            "uninstall": ("MOTION_RESTRAINT",),
        }
        for effect,labels in cases.items():
            with self.subTest(effect=effect):
                result="|".join(review_focus(effect))
                for label in labels:self.assertIn(label,result)

    def test_no_machine_generated_creative_approval(self):
        for effect in ("slow-push","orbit","glitter-spotlight"):
            result="|".join(review_focus(effect)).lower()
            self.assertNotIn("creative pass",result)
            self.assertNotIn("approved",result)

if __name__=="__main__":
    unittest.main()
