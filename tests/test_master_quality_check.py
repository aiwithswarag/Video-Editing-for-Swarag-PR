import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('quality',ROOT/'tools/master_quality_check.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
S={'duration':60.711856,'width':1080,'height':1920,'fps':29.50,'frames':1791,
   'video_codec':'h264','video_sar':'1:1','audio_codec':'aac','audio_streams':1}
class MasterQATests(unittest.TestCase):
    def test_clean(self):
        self.assertEqual([],mod.assess(S,{**S,'duration':60.7119}))
    def test_frames(self):
        self.assertIn('Frame count differs by more than one frame',
                      mod.assess(S,{**S,'frames':1760}))
    def test_audio(self):
        self.assertIn('Missing original/output audio',
                      mod.assess(S,{**S,'audio_streams':0,'audio_codec':None}))
    def test_width(self):
        self.assertIn('Unexpected output width',
                      mod.assess(S,{**S,'width':540,'height':960}))
    def test_preview(self):
        out={**S,'width':540,'height':960,'fps':15,'frames':911}
        self.assertEqual([],mod.assess(S,out,540,True,False))
    def test_duration(self):
        self.assertIn('Duration drift exceeds 120 milliseconds',
                      mod.assess(S,{**S,'duration':60.43}))
