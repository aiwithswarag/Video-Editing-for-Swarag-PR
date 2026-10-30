import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import world_model_cutaway as wm
class CutawayArtTests(unittest.TestCase):
    def test_frame_and_copy(self):
        if not (ROOT/"fonts/Inter.ttf").exists():self.skipTest("Fonts not installed")
        im=wm.draw_frame(1.,width=360,fps=12,frames=18)
        self.assertEqual((360,640),im.size)
        self.assertEqual("RGB",im.mode)
    def test_reject_dimensions(self):
        with self.assertRaises(ValueError):wm.draw_frame(1.,width=361)
    def test_reject_count(self):
        with self.assertRaises(ValueError):wm.render("/tmp/no.mp4",frames=1)
