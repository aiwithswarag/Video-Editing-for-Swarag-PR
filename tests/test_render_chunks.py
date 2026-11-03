"""Tests for 42-effect segmented composition boundaries and layer ordering."""
import importlib.util
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
spec=importlib.util.spec_from_file_location("render_chunks",ROOT/"scripts/render_chunks.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SegmentedRenderTests(unittest.TestCase):
    def test_overlaps_preserve_order(self):
        plan=[{"fx":"moody","start":0.4,"end":2},
              {"fx":"spotlight","start":1.5,"end":3},
              {"fx":"slow-push","start":4,"end":5}]
        spans=module.intervals(plan,6)
        self.assertEqual(5,len(spans))
        self.assertEqual((0.,.4,[]),spans[0])
        self.assertEqual([e["fx"] for e in spans[1][2]],["moody","spotlight"])
        self.assertAlmostEqual(spans[1][2][1]["start"],1.1)
        self.assertEqual((5,6,[]),spans[-1])

    def test_gap_only_after_last_effect(self):
        p=[{"fx":"locked-on","start":0,"end":1}]
        r=module.intervals(p,5)
        self.assertEqual(2,len(r))
        self.assertEqual((1,5,[]),r[1])

    def test_full_effect(self):
        p=[{"fx":"locked-on","start":0,"end":5}]
        r=module.intervals(p,5)
        self.assertEqual(1,len(r))
        self.assertEqual(1,len(r[0][2]))

    def test_fractional_frame_grid_exact_coverage(self):
        from fractions import Fraction
        plan=[{"fx":"slow-push","start":.3,"end":1.2,"zoom":1.05}]
        spans=module.frame_segments(plan,61,Fraction(59,2))
        self.assertEqual(61,sum(n for _,n,_ in spans))
        self.assertEqual([0,9,35],[start for start,_,_ in spans])
        self.assertEqual([9,26,26],[n for _,n,_ in spans])
        self.assertEqual("59/2",module.resolve_fps("29.5","unused.mp4"))
        self.assertEqual("30000/1001",module.resolve_fps("30000/1001","unused.mp4"))

    def test_no_effects(self):
        self.assertEqual([(0.,5,[])],module.intervals([],5))


if __name__=="__main__":
    unittest.main()
