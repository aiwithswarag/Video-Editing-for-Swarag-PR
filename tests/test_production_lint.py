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
    def test_premium_rejects_demo_ui_and_unsourced_business_metrics(self):
        risky=[
            ({'fx':'glass-widgets','start':0,'end':1.7},'STOCK_GLASS_DEMO'),
            ({'fx':'glass-widgets','start':0,'end':1.7,'look':'simple'},'STOCK_GLASS_DEMO'),
            ({'fx':'liquid-glass-graph','start':0,'end':1.7},'UNVERIFIED_CHART_METRIC'),
            ({'fx':'liquid-glass-graph','start':0,'end':1.7,'look':'bento',
              'text':'Revenue','from':0,'to':100},'UNVERIFIED_CHART_METRIC'),
            ({'fx':'profile-wall','start':0,'end':1.7},'FAKE_ENGAGEMENT_COUNT'),
            ({'fx':'match-cut','start':0,'end':1.7},'DEMO_ARTICLE_COPY'),
            ({'fx':'checklist','start':0,'end':1.7},'UNVERIFIED_CHECKLIST_COPY'),
            ({'fx':'todo','start':0,'end':1.7},'UNVERIFIED_CHECKLIST_COPY'),
        ]
        for item,expected in risky:
            with self.subTest(fx=item['fx'],look=item.get('look')):
                report=audit([item],3,'premium')
                codes=[p['code'] for p in report['blocking_errors']]
                self.assertIn(expected,codes)
                self.assertEqual('BLOCKED',report['technical_status'])
                showcase=audit([item],3,'showcase')
                self.assertEqual([],showcase['blocking_errors'])
    def test_source_backed_rag_glass_is_allowed_but_still_review_required(self):
        item={'fx':'glass-widgets','look':'rag-evidence','stage':'policies',
              'start':0,'end':1.7}
        report=audit([item],3,'premium')
        self.assertEqual([],report['blocking_errors'])
        self.assertTrue(report['requires_manual_creative_review'])
    def test_explicit_sourced_non_bento_chart_is_allowed_with_review(self):
        item={'fx':'liquid-glass-graph','text':'Hypothetical example',
              'from':100,'to':150,'start':0,'end':1.7,'metric_source':'Verified fictional example in supplied script'}
        report=audit([item],3,'premium')
        self.assertNotIn('UNVERIFIED_CHART_METRIC',
                         [e['code'] for e in report['blocking_errors']])

    def test_unsafe_card_recycling_blocks_premium_not_gallery(self):
        for name in ('noise','orbit','carousel-spin','check-pills',
                     'profile-wall','phone-fan','broll-split'):
            with self.subTest(effect=name):
                item={'fx':name,'start':0,'end':1.7}
                result=audit([item],3,'premium')
                self.assertIn('UNAPPROVED_REPEATED_MEDIA',
                              [x['code'] for x in result['blocking_errors']])
                showcase=audit([item],3,'showcase')
                self.assertFalse(showcase['blocking_errors'])

    def test_branded_source_cards_allowed_for_supported_effects(self):
        for name in ('noise','orbit','carousel-spin','check-pills','phone-fan'):
            with self.subTest(effect=name):
                item={'fx':name,'start':0,'end':1.7,'brand_cards':True,
                      'labels':'STRATEGY|DELIVERY'}
                report=audit([item],3,'premium')
                self.assertNotIn('UNAPPROVED_REPEATED_MEDIA',
                                 [x['code'] for x in report['blocking_errors']])

    def test_broll_needs_real_media_and_sourced_label(self):
        sample={'fx':'broll-split','start':0,'end':1.7,'images':'private-approved',
                'text':'CONFIRMED PROCESS'}
        report=audit([sample],3,'premium')
        self.assertEqual([],report['blocking_errors'])
        no_copy=audit([{k:v for k,v in sample.items() if k!='text'}],3)
        self.assertIn('UNVERIFIED_BROLL_TAG',
                      [x['code'] for x in no_copy['blocking_errors']])
        fake_cards=audit([{**sample,'images':'','brand_cards':True,
                           'labels':'EXAMPLE'}],3)
        self.assertIn('UNAPPROVED_REPEATED_MEDIA',
                      [x['code'] for x in fake_cards['blocking_errors']])

    def test_numeric_claims_require_provenance(self):
        item={'fx':'broll-split','start':0,'end':1.7,
              'images':'private-approved','text':'4 hours to 4 minutes'}
        report=audit([item],3)
        self.assertIn('UNVERIFIED_BROLL_METRIC',
                      [x['code'] for x in report['blocking_errors']])
        sourced=audit([{**item,'metric_source':'Original timing study'}],3)
        self.assertNotIn('UNVERIFIED_BROLL_METRIC',
                         [x['code'] for x in sourced['blocking_errors']])
        chart={'fx':'liquid-glass-graph','start':0,'end':1.7,
               'text':'Retention','from':0,'to':59}
        report=audit([chart],3)
        self.assertIn('UNVERIFIED_CHART_PROVENANCE',
                      [x['code'] for x in report['blocking_errors']])
        explicitly_hypothetical=audit([{**chart,'hypothetical_example':True}],3)
        self.assertNotIn('UNVERIFIED_CHART_PROVENANCE',
                         [x['code'] for x in explicitly_hypothetical['blocking_errors']])

    def test_ticket_mobile_copy_and_cover_headlines_are_checked(self):
        ticket={'fx':'the-bill','start':0,'end':1.7,'text':'ONE|TWO|THREE'}
        self.assertEqual([],audit([ticket],3,'premium')['blocking_errors'])
        overflow=audit([{**ticket,'text':'ONE|TWO|THREE|FOUR|FIVE'}],3)
        self.assertIn('MOBILE_TICKET_OVERFLOW',
                      [x['code'] for x in overflow['blocking_errors']])
        for name in ('cover-star','red-collage'):
            self.assertIn('EDITORIAL_DEMO_COPY',
                          [x['code'] for x in audit([
                          {'fx':name,'start':0,'end':1.7,'text':'STRATEGY'}
                          ],3)['blocking_errors']])
            approved=audit([{'fx':name,'start':0,'end':1.7,
                             'text':'STRATEGY','lines':'Delivery|Outcomes'}],3)
            self.assertNotIn('EDITORIAL_DEMO_COPY',
                             [x['code'] for x in approved['blocking_errors']])

    def test_verified_custom_article_can_render_premium_match_cut(self):
        plan=[{'fx':'match-cut','start':0,'end':1.7,
               'article_text':'Source backed summary provided and checked by editor.',
               'source_verified':True,'text':'POLICY'}]
        self.assertNotIn('DEMO_ARTICLE_COPY',
                         [x['code'] for x in audit(plan,3)['blocking_errors']])

    def test_brand_defaults_supply_explicit_source_neutral_cards(self):
        from brand_presets import apply_brand
        result=apply_brand([{'fx':'phone-fan','start':0,'end':1.7}])
        self.assertTrue(result[0]['brand_cards'])
        self.assertIn('GOVERNANCE',result[0]['labels'])
        self.assertNotIn('UNAPPROVED_REPEATED_MEDIA',
                         [x['code'] for x in audit(result,3)['blocking_errors']])

    def test_42_effect_gallery_is_possible_with_manual_override(self):
        from plan_validation import AVAILABLE_EFFECTS
        plan=[{'fx':fx,'start':i*2,'end':i*2+1,'text':'Reviewed'} for i,fx in enumerate(sorted(AVAILABLE_EFFECTS))]
        result=audit(plan,90,'showcase')
        self.assertEqual([],result['blocking_errors'])

if __name__=='__main__':unittest.main()
