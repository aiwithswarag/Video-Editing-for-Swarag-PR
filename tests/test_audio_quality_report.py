import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("audio_quality_report",ROOT/"tools/audio_quality_report.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

SAMPLE='''[Parsed_loudnorm_0] {
 "input_i" : "-20.68", "input_tp" : "-2.02",
 "input_lra" : "4.30", "input_thresh" : "-31.30",
 "output_i": "-17.05"
}'''

class AudioTests(unittest.TestCase):
    def test_measurement(self):
        data=module.parse_loudnorm_log(SAMPLE)
        self.assertAlmostEqual(-20.68,data["integrated_lufs"])
        self.assertAlmostEqual(-2.02,data["true_peak_dbtp"])
        self.assertAlmostEqual(4.3,data["loudness_range_lu"])
    def test_missing_measurement(self):
        with self.assertRaises(ValueError):
            module.parse_loudnorm_log("missing")
    def test_reject_nan(self):
        with self.assertRaises(ValueError):
            module.parse_loudnorm_log(SAMPLE.replace('-20.68','NaN'))
