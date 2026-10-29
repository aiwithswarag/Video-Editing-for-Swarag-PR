"""Static premium-art-direction checks; all effects remain available in showcase mode."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from production_lint import audit

class EditorialGuardTests(unittest.TestCase):
    def test_rejects_unverified_placeholder(self):
        report=audit([{'fx':'headline-box','start':0,'end':2}],6)
        self.assertEqual('BLOCKED',report['technical_status'])
        self.assertEqual('PLACEHOLDER_COPY',report['blocking_errors'][0]['code'])
    def test_avoids_overlapping_graphics(self):
        plan=[{'fx':k,'start':0,'end':2,'text':'Approved'} for k in ('headline-box','spotlight','slow-push')]
        result=audit(plan,5)
        self.assertIn('EFFECT_OVERLAP',[x['code'] for x in result['blocking_errors']])
        demo=audit(plan,5,'showcase')
        self.assertEqual([],demo['blocking_errors'])
        self.assertTrue(any(x['code']=='SHOWCASE_OVERRIDE' for x in demo['warnings']))
    def test_reasonable_slow_push_passes(self):
        report=audit([{'fx':'slow-push','start':.2,'end':2,'zoom':1.06}],3)
        self.assertNotIn('AGGRESSIVE_ZOOM',[x['code'] for x in report['blocking_errors']])
        self.assertEqual('REVIEW',report['technical_status'])
    def test_rejects_hard_zoom(self):
        report=audit([{'fx':'slow-push','start':.2,'end':2,'zoom':1.6}],3)
        self.assertEqual('AGGRESSIVE_ZOOM',report['blocking_errors'][0]['code'])
    def test_42_effect_gallery_is_possible_with_manual_override(self):
        from plan_validation import AVAILABLE_EFFECTS
        plan=[{'fx':fx,'start':i*2,'end':i*2+1,'text':'Reviewed'} for i,fx in enumerate(sorted(AVAILABLE_EFFECTS))]
        result=audit(plan,90,'showcase')
        self.assertEqual([],result['blocking_errors'])

if __name__=='__main__':unittest.main()
