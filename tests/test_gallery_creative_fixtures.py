"""Protect original registry coverage and source-neutral executive gallery content."""
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from effect_catalog import read_registry
from render_effect_gallery import (DIAGNOSTIC_CARD_FX, SAFE_EXAMPLE_TEXT,
                                   NAMED_VARIANTS,diagnostic_options)

class OriginalCatalogCreativeFixtures(unittest.TestCase):
    def test_all_42_original_implementations_and_five_looks_are_preserved(self):
        names,_,_=read_registry()
        self.assertEqual(42,len(names))
        self.assertEqual(5,len(NAMED_VARIANTS))
        self.assertEqual(47,len(names)+len(NAMED_VARIANTS))
        for label in names:
            with self.subTest(effect=label):
                options=diagnostic_options(label,label)
                self.assertIsInstance(options,dict)
        for label,actual,look in NAMED_VARIANTS:
            with self.subTest(look=label):
                self.assertEqual(look, {
                    k:v for k,v in diagnostic_options(label,actual,look).items()
                    if k in look
                })

    def test_no_duplicated_camera_thumbnails_in_card_fixtures(self):
        for label in DIAGNOSTIC_CARD_FX:
            with self.subTest(effect=label):
                params=diagnostic_options(label,label)
                self.assertTrue(params["brand_cards"])
                self.assertGreaterEqual(len(params["labels"].split("|")),4)
                self.assertFalse(params.get("images"))

    def test_unverified_values_are_explicitly_demo_not_business_facts(self):
        self.assertEqual("ILLUSTRATIVE DEMO",
                         diagnostic_options("broll-split","broll-split")["text"])
        self.assertTrue(diagnostic_options("liquid-glass-graph",
                         "liquid-glass-graph")["hypothetical_example"])
        self.assertNotIn("count",diagnostic_options("profile-wall","profile-wall"))
        self.assertIn("EXAMPLE",
                      diagnostic_options("match-cut","match-cut")["text"])
        self.assertNotIn("197000",repr(SAFE_EXAMPLE_TEXT))
        self.assertNotIn("4 hrs",repr(SAFE_EXAMPLE_TEXT))

    def test_original_cover_and_simple_variants_are_separately_exercised(self):
        self.assertEqual("standard",diagnostic_options("cover-star",
                         "cover-star")["look"])
        self.assertEqual("editorial",diagnostic_options("cover-star-editorial",
                         "cover-star",{"look":"editorial"})["look"])
        self.assertEqual("standard",diagnostic_options("glass-widgets",
                         "glass-widgets")["look"])
        self.assertEqual("simple",diagnostic_options("glass-widgets-simple",
                         "glass-widgets",{"look":"simple"})["look"])

if __name__=="__main__":
    unittest.main()
