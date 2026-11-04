"""Conservative editorial guardrails for 42-effect plans.

This static lint cannot verify realistic compositing, skin, speech, factual
accuracy or whether any motion looks 'AI generated'; human review remains required.
"""
from __future__ import annotations
import math
import re

COPY_REQUIRED=frozenset({'headline-box','backdrop-word','led-sign','reject-stamp',
                         'split-headline','headline-wall','pastel-word','the-bill'})
CARD_EFFECTS=frozenset({'noise','orbit','phone-fan','carousel-spin','red-collage',
                       'broll-split','reel-frame','cover-star'})
TEMPLATE_UI=frozenset({'glass-widgets','liquid-glass-graph','apple-toggles',
                       'comment-box','tap','checklist','todo','timeline'})
# Effects using the source's ten stills as substitute 'B-roll' look repetitive.
# Real business production needs approved assets or explicitly authored Swarag
# vector cards. The technical showcase remains fully available.
ASSET_CARD_EFFECTS=frozenset({'noise','orbit','carousel-spin','check-pills',
                              'profile-wall','phone-fan','broll-split'})
SAFE_BRAND_CARD_EFFECTS=ASSET_CARD_EFFECTS-{'broll-split'}
# Source-specific words must be supplied at real spoken moments. A demo label
# silently carried through the 42-effect gallery is not verified film copy.
SPEECH_COPY_EFFECTS=frozenset({
    'lineup','check-pills','apple-toggles','comment-box',
    'pause-point','scribble','phone-fan','tier-list'
})
# Full panels must fit at 9:16 phone size before the renderer animates them.
ROW_RULES={
    'lineup':(4,20),'apple-toggles':(4,19),'todo':(4,27),
    'checklist':(4,44),'the-bill':(4,24),
    'cover-star':(3,32),'red-collage':(3,36)
}


def audit(plan,duration,style='premium'):
    if style not in ('premium','showcase'):
        raise ValueError('Style must be premium or showcase')
    notes=[]
    def flag(severity,code,message):
        notes.append({'severity':severity,'code':code,'message':message})
    if len(plan)>max(5,math.ceil(duration/6.)):
        flag('warning','EFFECT_DENSITY','Dense effects may distract from the subject; review pacing')
    for i,item in enumerate(plan):
        name=item['fx'];label=f'Effect {i+1} ({name})'
        seconds=item['end']-item['start']
        if seconds<0.55:
            flag('warning','VERY_SHORT_FX',f'{label} lasts under 0.55s')
        if name in COPY_REQUIRED and not str(item.get('text','')).strip():
            flag('error','PLACEHOLDER_COPY',f'{label} requires verified, intentional text')
        if name in SPEECH_COPY_EFFECTS:
            key='item' if name=='tier-list' else 'text'
            if not str(item.get(key,'')).strip():
                flag('error','SCRIPT_COPY_REQUIRED',
                     f'{label} must receive actual verified spoken or source-backed {key}')
        if name in ROW_RULES:
            key='lines' if name in ('cover-star','red-collage') else 'text'
            if name=='checklist':
                rows=[x.strip().split('::')[0] for x in str(item.get(key,'')).split('|') if x.strip()]
            elif name=='cover-star' or name=='red-collage':
                rows=[x.strip() for x in str(item.get('lines','')).split('|') if x.strip()]
            else:
                rows=[x.strip() for x in str(item.get(key,'')).split('|') if x.strip()]
            limit,max_chars=ROW_RULES[name]
            if rows and (len(rows)>limit or any(len(t)>max_chars for t in rows)):
                flag('error','MOBILE_COPY_OVERFLOW',
                     f'{label} needs ≤{limit} rows of ≤{max_chars} characters each for phone-sized graphics')
        if name=='reel-frame':
            has_metrics=any(item.get(k) is not None for k in ('likes','comments'))
            if has_metrics and (item.get('metrics_verified') is not True
                                or not str(item.get('metric_source','')).strip()):
                flag('error','UNVERIFIED_SOCIAL_METRICS',
                     f'{label} cannot publish social engagement counts without verified provenance')
        if name in ('noise','orbit','carousel-spin','shortcut-rain','headline-wall'):
            max_count={'noise':8,'orbit':7,'carousel-spin':8,
                       'shortcut-rain':16,'headline-wall':8}[name]
            if 'count' in item:
                try: count=int(item['count'])
                except (ValueError,TypeError): count=-1
                if count<1 or count>max_count:
                    flag('error','EXCESSIVE_CARD_DENSITY',
                         f'{label} count must be 1–{max_count} in executive output')
        if name=='carousel-spin' and 'turns' in item:
            try: turns=float(item['turns'])
            except (TypeError,ValueError): turns=float('inf')
            if not math.isfinite(turns) or not 0<=turns<=1:
                flag('error','AGGRESSIVE_CAROUSEL',
                     f'{label} should remain below one turn for a restrained executive edit')

        if name in ASSET_CARD_EFFECTS:
            real_assets=bool(item.get('images'))
            brand_assets=(name in SAFE_BRAND_CARD_EFFECTS and
                          item.get('brand_cards') is True and
                          bool(str(item.get('labels','')).strip()))
            if not (real_assets or brand_assets):
                flag('error','UNAPPROVED_REPEATED_MEDIA',
                     f'{label} requires a private approved images directory or intentional labeled Swarag brand_cards; never duplicate camera thumbnails as evidence')
        elif name in CARD_EFFECTS and not any(item.get(k) for k in ('images','labels','brand_cards')):
            flag('warning','STOCK_LIKE_CARDS',f'{label} uses autogenerated/recirculated cards without selected assets')
        if name=='broll-split' and not str(item.get('text','')).strip():
            flag('error','UNVERIFIED_BROLL_TAG',
                 f'{label} cannot publish the demo time-savings sticker; provide an intentional sourced short label')
        if name=='broll-split' and re.search(r'\d',str(item.get('text',''))) and not str(item.get('metric_source','')).strip():
            flag('error','UNVERIFIED_BROLL_METRIC',
                 f'{label} shows numeric claims without metric_source evidence')
        if name in ('cover-star','red-collage'):
            if not str(item.get('text','')).strip() or not str(item.get('lines','')).strip():
                flag('error','EDITORIAL_DEMO_COPY',
                     f'{label} needs intentional title AND approved cover lines; generic demo typography is not a publishable claim')
        if name=='the-bill':
            chunks=[x.strip() for x in str(item.get('text','')).split('|') if x.strip()]
            if len(chunks)>4 or any(len(x)>24 for x in chunks):
                flag('error','MOBILE_TICKET_OVERFLOW',
                     f'{label} must use four or fewer concise approved lines (at most 24 characters) for phone readability')
        if name in TEMPLATE_UI:
            flag('warning','TEMPLATE_UI',f'{label} can look like an app-template overlay; inspect against real footage')
        # The catalog includes artist demo UIs with baked sample values,
        # example view counts, progress metrics and example article copy.
        # A renderer producing an MP4 does NOT establish these as facts.
        # In premium Swarag production, block unverified demos; the effects
        # remain technically available for explicitly labeled showcases.
        if name=='glass-widgets' and item.get('look')!='rag-evidence':
            flag('error','STOCK_GLASS_DEMO',
                 f'{label} uses fixed example charts/render stats; select a sourced content-specific glass look instead')
        if name=='liquid-glass-graph' and (
                item.get('look')=='bento' or
                any(k not in item or str(item[k]).strip()=='' for k in ('text','from','to'))):
            flag('error','UNVERIFIED_CHART_METRIC',
                 f'{label} needs sourced label/from/to values; its bento demo has built-in examples')
        if name=='liquid-glass-graph' and item.get('look')!='bento' and (
                all(str(item.get(k,'')).strip() for k in ('text','from','to')) and
                not item.get('hypothetical_example') and
                not str(item.get('metric_source','')).strip()):
            flag('error','UNVERIFIED_CHART_PROVENANCE',
                 f'{label} needs metric_source or explicit hypothetical_example=true')
        if name=='profile-wall' and (
                'count' not in item or not str(item.get('metric_source','')).strip()):
            flag('error','FAKE_ENGAGEMENT_COUNT',
                 f'{label} needs an actual count, documented metric_source and approved original/brand-card imagery; demo counts are not evidence')
        if name=='match-cut' and (
                not str(item.get('article_text','')).strip() or
                item.get('source_verified') is not True):
            flag('error','DEMO_ARTICLE_COPY',
                 f'{label} needs actual approved article_text plus source_verified=true; random demo prose cannot be published')
        if name in ('checklist','todo') and not str(item.get('text','')).strip():
            flag('error','UNVERIFIED_CHECKLIST_COPY',
                 f'{label} cannot publish default checklist/task claims without verified script text')
        zoom=item.get('zoom')
        if zoom is not None:
            try:
                z=float(zoom)
            except (TypeError,ValueError):
                flag('error','BAD_ZOOM',f'{label} has nonnumeric zoom')
            else:
                if not math.isfinite(z) or z>1.35 or z<1:
                    flag('error','AGGRESSIVE_ZOOM',f'{label} zoom {zoom} may reveal interpolation/soft detail')
        if name=='moody':
            flag('warning','DOUBLE_GRADE','Moody inside the effect layer may change skin colour after camera-grade pass')
    edges=sorted(set([v for p in plan for v in (p['start'],p['end'])]))
    for a,b in zip(edges,edges[1:]):
        if b<=a:continue
        active=[p['fx'] for p in plan if p['start']<b and p['end']>a]
        if len(active)>2:
            flag('error','EFFECT_OVERLAP',
                 f'{len(active)} concurrent effects at {a:.2f}-{b:.2f}s: {", ".join(active)}')
    warnings=[x for x in notes if x['severity']=='warning']
    errors=[x for x in notes if x['severity']=='error']
    return {'style':style,'requires_manual_creative_review':True,
            'technical_status':'BLOCKED' if (errors and style=='premium') else 'REVIEW',
            'blocking_errors':errors if style=='premium' else [],
            'warnings':warnings+[{'severity':'warning','code':'SHOWCASE_OVERRIDE',
                'message':x['message']} for x in errors] if style=='showcase' else warnings,
            'note':'An absence of static warnings does not prove natural footage, correct masking or professional design'}
