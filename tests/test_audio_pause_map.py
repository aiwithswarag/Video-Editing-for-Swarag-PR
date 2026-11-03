import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("audio_pause_map",ROOT/"tools/audio_pause_map.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class PauseTests(unittest.TestCase):
    def test_parse_and_filter(self):
        log="[silencedetect] silence_start: 3.00\n[silencedetect] silence_end: 3.80 | silence_duration: .8\n[silencedetect] silence_start: 7.00\n[silencedetect] silence_end: 7.12"
        data=module.read_pauses(log,12,.3)
        self.assertEqual(1,len(data))
        self.assertAlmostEqual(3.4,data[0]["cut_at"])
        self.assertEqual(1,len(module.select_boundaries(data,12,min_strength=.5)))
    def test_spacing_prefers_longer_pause(self):
        pauses=[{"start":5.,"end":5.6,"duration":.6,"cut_at":5.3},
                {"start":7.,"end":7.9,"duration":.9,"cut_at":7.45},
                {"start":15.,"end":15.8,"duration":.8,"cut_at":15.4}]
        out=module.select_boundaries(pauses,19,4,.5)
        self.assertEqual([7.45,15.4],[x["cut_at"] for x in out])
    def test_trailing_pause(self):
        out=module.read_pauses("silence_start: 8.7",10,.3)
        self.assertEqual(10.,out[0]["end"])
    def test_invalid_duration(self):
        with self.assertRaises(ValueError):module.read_pauses("",float("nan"))
