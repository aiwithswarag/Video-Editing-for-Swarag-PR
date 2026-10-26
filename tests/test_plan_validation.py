import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from plan_validation import AVAILABLE_EFFECTS,validate_plan
class PlanTest(unittest.TestCase):
    def test_count(self):self.assertEqual(len(AVAILABLE_EFFECTS),42)
    def test_example(self):self.assertEqual(4,len(validate_plan(json.loads((ROOT/"examples/executive.json").read_text()),duration=30)))
    def test_alias(self):self.assertEqual(validate_plan([{"fx":"push","start":0,"end":1}])[0]["fx"],"slow-push")
    def test_reject(self):
        for p in [[],[{"fx":"unknown","start":0,"end":2}],[{"fx":"moody","start":2,"end":1}],[{"fx":"moody","start":0,"end":float("nan")}]]:
            with self.assertRaises(ValueError):validate_plan(p)
if __name__=="__main__":unittest.main()
