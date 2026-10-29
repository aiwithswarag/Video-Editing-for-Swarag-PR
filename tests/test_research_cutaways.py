import unittest
from fractions import Fraction
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import research_cards as cards
import insert_cutaways as cut

S={"width":360,"height":640,"fps":Fraction(8,1),"frames":24,"audio":True}
C={"width":360,"height":640,"fps":Fraction(8,1),"frames":4,"audio":False}
URL="https://arxiv.org/abs/2610.10528"
class ResearchVisualTests(unittest.TestCase):
    def test_citation_required(self):
        b={"kind":"benchmark","title":"Evidence","scope":"Simulation",
           "citation":"Huang et al.","source_url":URL,"caveat":"Not real-world proof",
           "before":{"label":"0s","value":63.3},"after":{"label":"19.2s","value":78.7}}
        self.assertEqual(b,cards.validate(b))
        with self.assertRaises(ValueError):cards.validate({**b,"source_url":""})
        with self.assertRaises(ValueError):cards.validate({**b,"after":{"label":"19.2s","value":102}})
    def test_coverage(self):
        b={"kind":"coverage","title":"Comparisons","scope":"Survey","citation":"Jena et al.",
           "source_url":"https://arxiv.org/abs/2609.29669","caveat":"Not a verdict",
           "contrast":"World models vs VLA","matched":11,"total":160}
        self.assertEqual(11,cards.validate(b)["matched"])
        with self.assertRaises(ValueError):cards.validate({**b,"matched":161})
    def test_multi_insert_validation(self):
        windows=[({"start_frame":3},C),({"start_frame":13},C)]
        self.assertEqual(17,cut.validate(S,windows))
        self.assertIn("concat=n=5",cut.build_filter(24,windows))
        with self.assertRaises(ValueError):cut.validate(S,[windows[0],({"start_frame":5},C)])
        with self.assertRaises(ValueError):cut.validate(S,[({"start_frame":3},{**C,"fps":Fraction(30)})])
    def test_missing_audio(self):
        with self.assertRaises(ValueError):cut.validate({**S,"audio":False},[({"start_frame":3},C)])
