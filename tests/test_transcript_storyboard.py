import importlib.util
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("transcript_storyboard",ROOT/"tools/transcript_storyboard.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class SpeechStoryTests(unittest.TestCase):
    def test_exact_words_not_invented(self):
        words=[{"w":"Strategy","s":0.5,"e":0.8},
               {"w":"meets","s":0.9,"e":1.1},
               {"w":"delivery.","s":1.2,"e":1.55},
               {"w":"Measured","s":9.0,"e":9.35},
               {"w":"outcomes.","s":9.4,"e":9.8}]
        result=module.create_story(words,12,6,6)
        self.assertEqual(["Strategy meets delivery.","Measured outcomes."],
                         [b["headline"] for b in result["beats"]])
        self.assertEqual("word_timestamps",result["source"])
        self.assertIn("MANUAL",result["status"])
        self.assertTrue(all(b["start"]>=0 for b in result["beats"]))
    def test_punctuation(self):
        x=[{"w":"Great","s":0,"e":.2},{"w":"idea","s":.2,"e":.4},{"w":",","s":.4,"e":.5},{"w":"right?","s":.6,"e":.8}]
        self.assertEqual("Great idea, right?",module.text_from_words(x))
    def test_reject_unordered(self):
        words=[{"w":"First","s":2,"e":3},{"w":"Second","s":1,"e":2}]
        with self.assertRaises(ValueError):module.parse_words(words,10)
    def test_reject_unknown_duration(self):
        with self.assertRaises(ValueError):module.parse_words([{"w":"Yes","s":0,"e":1}],float("nan"))
    def test_accept_faster_whisper_schema(self):
        words={"words":[{"w":"Think","s":1,"e":1.4},{"w":"clearly.","s":1.4,"e":1.9}]}
        result=module.create_story(words,5)
        self.assertEqual("Think clearly.",result["beats"][0]["headline"])
    def test_reject_fabricated_word(self):
        with self.assertRaises(ValueError):
            module.parse_words([{"w":"","s":0,"e":.2}],10)
