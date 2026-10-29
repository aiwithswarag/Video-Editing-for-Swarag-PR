import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import cinematic_finish as c
INFO={"width":1080,"height":1920,"duration":60.7,"fps":"59/2","color":"bt709"}
class ProductionTests(unittest.TestCase):
    def test_original_resolution_not_upscaled(self):
        self.assertNotIn("scale=",c.video_filter(INFO,"clean-studio"))
    def test_original_audio(self):
        a=c.command("a.mp4","b.mp4",INFO,"clean-studio","instagram")
        self.assertEqual("copy",a[a.index("-c:a")+1])
    def test_preview_audio_timestamps(self):
        a=c.command("a.mp4","b.mp4",INFO,"clean-studio","instagram",start=2,seconds=2)
        self.assertEqual("aac",a[a.index("-c:a")+1])
    def test_rejects_horizontal(self):
        with self.assertRaises(ValueError):c.video_filter({**INFO,"width":1920,"height":1080},"clean-studio")
    def test_rejects_hdr_relabeling(self):
        with self.assertRaises(ValueError):c.video_filter({**INFO,"color":"bt2020"},"clean-studio")
    def test_platforms(self):
        for name in c.PLATFORMS:self.assertIn("bt709",c.command("a","b",INFO,"neutral",name))
