"""Regression for objective washed-out opening warnings."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from visual_quality_gate import find_issues

class OpeningQC(unittest.TestCase):
    def test_flags_first_frame_burned_to_white(self):
        samples=[
            {"time_s":0,"mean_luma":247.29,"near_white_fraction":.923},
            {"time_s":1.5,"mean_luma":137.11,"near_white_fraction":.009},
            {"time_s":2.0,"mean_luma":137.95,"near_white_fraction":.008},
        ]
        flags=find_issues(samples)
        self.assertEqual("POSSIBLE_WASHED_OUT_OPENING",flags[0]["code"])
    def test_normal_stable_opening_has_no_flag(self):
        samples=[{"time_s":i/8,"mean_luma":135+i*.1,
                  "near_white_fraction":.01} for i in range(21)]
        self.assertEqual([],find_issues(samples))
    def test_normal_white_background_static_is_not_false_positive(self):
        samples=[{"time_s":0,"mean_luma":241,"near_white_fraction":.5},
                 {"time_s":1.5,"mean_luma":232,"near_white_fraction":.4}]
        self.assertEqual([],find_issues(samples))
    def test_empty_is_explicit_warning(self):
        self.assertTrue(find_issues([]))

if __name__=="__main__":
    unittest.main()
