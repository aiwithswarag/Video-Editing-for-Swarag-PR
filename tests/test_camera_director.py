"""Conservative virtual-camera edit-decision tests; synthetic and audio-safe."""
import importlib.util,unittest
from fractions import Fraction
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('camera',ROOT/'scripts/render_directors_cut.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

class CameraDirectorTests(unittest.TestCase):
    def test_valid_plan(self):
        plan={'reframes':[{'start':1,'end':2.5,'zoom':1.07},{'start':4,'end':6,'zoom':1.09}]}
        self.assertEqual(2,len(mod.validate_plan(plan,7)))
    def test_reject_excessive_zoom(self):
        with self.assertRaises(ValueError):
            mod.validate_plan({'reframes':[{'start':1,'end':3,'zoom':1.30}]},7)
    def test_reject_overlap(self):
        with self.assertRaises(ValueError):
            mod.validate_plan({'reframes':[{'start':1,'end':3,'zoom':1.08},{'start':3.1,'end':5,'zoom':1.08}]},7)
    def test_same_audio_packets(self):
        cmd=mod.make_command('in.mp4','out.mp4',[],10,540,960,Fraction(59,2))
        self.assertIn('copy',cmd)
        self.assertIn('0:a:0?',cmd)
        self.assertIn('59/2',cmd[cmd.index('-vf')+1])
    def test_empty_reframe_plan(self):
        self.assertEqual('1',mod.zoom_expression([]))
    def test_reject_nan(self):
        with self.assertRaises(ValueError):
            mod.validate_plan({'reframes':[{'start':1,'end':3,'zoom':float('nan')}]},7)
