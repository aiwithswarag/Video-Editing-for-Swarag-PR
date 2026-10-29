import sys,unittest
from pathlib import Path
from fractions import Fraction
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from insert_cutaway import validate
SRC={"width":1080,"height":1920,"fps":Fraction(59,2),"frames":1791,"audio":True}
BR={"width":1080,"height":1920,"fps":Fraction(59,2),"frames":192,"audio":False}
class EditCutTests(unittest.TestCase):
    def test_insert(self):self.assertEqual(577,validate(SRC,BR,385))
    def test_res(self):
        with self.assertRaises(ValueError):validate(SRC,{**BR,"width":720},385)
    def test_fps(self):
        with self.assertRaises(ValueError):validate(SRC,{**BR,"fps":Fraction(30,1)},385)
    def test_bounds(self):
        with self.assertRaises(ValueError):validate(SRC,BR,1700)
    def test_no_voice(self):
        with self.assertRaises(ValueError):validate({**SRC,"audio":False},BR,385)
