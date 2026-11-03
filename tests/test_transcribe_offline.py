import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('asr',ROOT/'tools/transcribe_offline.py')
asr=importlib.util.module_from_spec(spec);spec.loader.exec_module(asr)
class OfflineASRTests(unittest.TestCase):
    def test_time_conversion(self):
        self.assertAlmostEqual(75.25,asr.timestamp('00:01:15.250'))
    def test_words_and_punctuation(self):
        segments=[{"text":w,"offsets":{"from":i*250,"to":(i+1)*250}}
                  for i,w in enumerate(['Most','AI','describes','the','world','.'])]
        result=asr.normalize({"transcription":segments},3)
        self.assertEqual(['Most','AI','describes','the','world.'],[x['w'] for x in result['words']])
        self.assertFalse(result["transcript_verified"])
    def test_reject_fake_word_timings(self):
        with self.assertRaises(ValueError):
            asr.normalize({"transcription":[{"text":"multiple words here","offsets":{"from":0,"to":500}}]},3)
    def test_full_json_tokens(self):
        segments=[{"text":"hello world","tokens":[
                  {"text":"hello","offsets":{"from":0,"to":250}},
                  {"text":"world","offsets":{"from":250,"to":500}}]}]
        segments.extend({"text":w,"offsets":{"from":i*250,"to":(i+1)*250}}
                       for i,w in enumerate(['works','very','well'],start=2))
        r=asr.normalize({"transcription":segments},3)
        self.assertEqual(5,len(r['words']))
    def test_reject_nonmonotonic(self):
        entries=[{"text":str(i),"offsets":{"from":i*300,"to":i*300+140}} for i in range(5)]
        entries.append({"text":"bad","offsets":{"from":1,"to":110}})
        r=asr.normalize({"transcription":entries},3)
        self.assertEqual(5,len(r["words"]))
        self.assertTrue(r["review_flags"])
