import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('normalizer',ROOT/'tools/two_pass_dialogue_master.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

LOG='''[Parsed_loudnorm_0] {
"input_i" : "-20.68","input_tp" : "-2.02","input_lra" : "4.30",
"input_thresh" : "-31.30","output_i" : "-18.86",
"target_offset" : "0.86"
}'''
class DialogueMasterTests(unittest.TestCase):
    def test_parse_report(self):
        r=m.parse_report(LOG)
        self.assertEqual('-20.68',r['input_i'])
        self.assertEqual('0.86',r['target_offset'])
    def test_filter(self):
        f=m.normalizer_filter(m.parse_report(LOG))
        self.assertIn('measured_I=-20.68',f)
        self.assertIn('TP=-1.9',f)
        self.assertIn('linear=true',f)
    def test_reject_missing_json(self):
        with self.assertRaises(ValueError):m.parse_report('No audio filter output')
    def test_reject_nonfinite(self):
        with self.assertRaises(ValueError):m.parse_report(LOG.replace('-20.68','NaN'))
