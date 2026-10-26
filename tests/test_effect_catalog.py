"""Prevent regression from 42 effects, aliases or named looks."""
import json
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
from effect_catalog import read_registry
from plan_validation import validate_plan, AVAILABLE_EFFECTS, ALIASES, LOOKS

class EffectsCatalogue(unittest.TestCase):
    def test_all_42_registered(self):
        expected = json.loads((ROOT/"skills/video-director/references/effects-manifest.json").read_text())
        actual, aliases, looks = read_registry()
        self.assertEqual(expected["names"], actual)
        self.assertEqual(42, len(actual))
        self.assertEqual(set(actual), AVAILABLE_EFFECTS)
        self.assertEqual(aliases, ALIASES)
        self.assertEqual(looks, LOOKS)

    def test_all_42_validate(self):
        names, _, _ = read_registry()
        plan = [{"fx": name, "start": 0, "end": 1.5} for name in names]
        self.assertEqual(42, len(validate_plan({"effects":plan},duration=2)))

    def test_every_alias_resolves(self):
        _, aliases, looks = read_registry()
        for name, expected in aliases.items():
            with self.subTest(name=name):
                self.assertEqual(expected, validate_plan([{"fx":name,"start":0,"end":1}])[0]["fx"])
        for name, (effect, look) in looks.items():
            with self.subTest(look=name):
                actual = validate_plan([{"fx":name,"start":0,"end":1}])[0]
                self.assertEqual(effect, actual["fx"])
                self.assertEqual(look, actual["look"])

    def test_reject_nonfinite_optional_number(self):
        with self.assertRaises(ValueError):
            validate_plan([{"fx":"orbit","start":0,"end":1,"speed":float("nan")}])
