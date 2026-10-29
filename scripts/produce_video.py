#!/usr/bin/env python3
"""Swarag production entry point: all 42 effects, native-rate grade-first editing, and QA.

No model invents dialogue, graphics or evidence. A natural-language brief is a human
direction reference; effect choices/timings must be represented in a validated plan.
"""
from __future__ import annotations
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
sys.path.insert(0,str(ROOT/'scripts'))
from plan_validation import AVAILABLE_EFFECTS,validate_plan
from effect_catalog import read_registry
from resumable_cinematic_master import process as grade_master,stream
from cinematic_finish import probe,audio_md5
from master_quality_check import evaluate as check_master


def run(args):
    subprocess.run(args,check=True)


def media(path):
    if not path.is_file():raise FileNotFoundError(path)
    data=probe(path)
    video=stream(path)
    return {**data,'video_codec':video['codec_name'],
            'frames':int(video['nb_frames']) if str(video.get('nb_frames','')).isdigit() else None}


def parse_directives(path):
    """Plain-text director cues: FX name START END [text=...] [title=...] etc."""
    lines=Path(path).read_text(encoding='utf-8').splitlines()
    effects=[]
    for n,raw in enumerate(lines,1):
        line=raw.strip()
        if not line or line.startswith('#'):continue
        import shlex
        tokens=shlex.split(line)
        if len(tokens)<4 or tokens[0].upper()!='FX':
            raise ValueError(f'Line {n}: expected FX <name> <start> <end> [key=value ...]')
        item={'fx':tokens[1],'start':float(tokens[2]),'end':float(tokens[3])}
        for token in tokens[4:]:
            if '=' not in token:raise ValueError(f'Line {n}: expected key=value, got {token!r}')
            k,v=token.split('=',1)
            if k in ('fx','start','end'):raise ValueError(f'Line {n}: reserved key {k}')
            item[k]=v
        effects.append(item)
    return validate_plan(effects)


def prepare(video,instructions,output,script=None,brief=None,verified=False):
    video=Path(video).resolve();output=Path(output).resolve()
    meta=media(video)
    plan=parse_directives(instructions)
    validate_plan(plan,meta['duration'])
    if script and not Path(script).is_file():raise FileNotFoundError(script)
    if brief and not Path(brief).is_file():raise FileNotFoundError(brief)
    output.parent.mkdir(parents=True,exist_ok=True)
    data={'schema_version':1,'status':'DRAFT — manual creative verification required',
          'transcript_verified':bool(verified),
          'requires_transcript':bool(script),'effects':plan,
          'source_media':{'duration':meta['duration'],'fps':meta['fps'],'width':meta['width'],'height':meta['height']},
          'source_script_name':Path(script).name if script else None,
          'brief_name':Path(brief).name if brief else None,
          'instructions_name':Path(instructions).name}
    output.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    return {'plan':str(output),'effects':len(plan),'catalog_available':len(AVAILABLE_EFFECTS),
            'spoken_words_verified':bool(verified)}


def build_preview(video,plan,start,seconds,tmp):
    # Extract only the requested review section and shift effects to clip-local seconds.
    length=media(video)['duration']
    if start<0 or seconds<=0 or start+seconds>length+0.03:
        raise ValueError('Preview range outside source')
    subset=[]
    for e in plan:
        lo=max(e['start'],start);hi=min(e['end'],start+seconds)
        if hi-lo>.06:
            local={**e,'start':round(lo-start,6),'end':round(hi-start,6)}
            subset.append(local)
    if not subset:raise ValueError('Selected preview has no effect; choose a different window')
    clip=tmp/'preview_source.mp4'
    run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y',
         '-ss',str(start),'-i',str(video),'-t',str(seconds),'-map','0:v:0',
         '-map','0:a:0','-c:v','libx264','-preset','veryfast','-crf','19',
         '-c:a','aac','-b:a','160k','-movflags','+faststart',str(clip)])
    return clip,subset


def release(video,plan_path,outdir,look='clean-studio',width=None,brand='executive',
            crf=18,frames_per_chunk=180,preview_start=None,preview_seconds=None):
    video=Path(video).resolve();plan_path=Path(plan_path).resolve()
    outdir=Path(outdir).resolve()
    if not plan_path.is_file():raise FileNotFoundError(plan_path)
    raw=json.loads(plan_path.read_text(encoding='utf8'))
    if isinstance(raw,dict) and raw.get('requires_transcript') and not raw.get('transcript_verified'):
        raise ValueError('Transcript-based plan must be explicitly verified before export')
    original=media(video)
    plan=validate_plan(raw,original['duration'])
    if original['frames'] is None:
        raise ValueError('Frame count missing; normalize video to CFR H264/AAC first')
    if original['width']*16!=original['height']*9:
        raise ValueError('Production pipeline currently requires exact portrait 9:16 source; review reframe externally')
    if float(__import__('fractions').Fraction(original['fps']))>30.5:
        raise ValueError('42-effect engine does not preserve above-30.5 fps. Normalize footage before editing.')
    if width is None:width=min(original['width'],1080)
    if width<240 or width>original['width'] or width%2:
        raise ValueError('Width must be even, at least 240, and not exceed source width')
    if outdir==video.parent:
        raise ValueError('Choose a separate output folder, not the source folder')
    if (outdir/'final_master.mp4').resolve()==video:raise ValueError('Cannot overwrite original')
    outdir.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='swarag_production_') as dirname:
        temp=Path(dirname)
        source,workplan=video,plan
        if preview_seconds is not None:
            source,workplan=build_preview(video,plan,preview_start or 0.,preview_seconds,temp)
        workplan_path=temp/'validated-effects.json'
        workplan_path.write_text(json.dumps({'effects':workplan}),encoding='utf8')
        # Grade CAMERA footage before effects/typography. Do not tint the titles a second time.
        graded_dir=outdir/'graded_intermediate'
        grade=grade_master(source,graded_dir,look=look,crf=crf,
                           frames_per_chunk=frames_per_chunk)
        if grade['technical_status']!='PASS':
            raise RuntimeError('Grading did not complete')
        graded=Path(grade['master'])
        master=outdir/'final_master.mp4'
        cmd=[sys.executable,str(ROOT/'scripts'/'render_chunks.py'),str(graded),
             str(workplan_path),str(master),'--width',str(width),
             '--fps','auto','--brand',brand,'--crf',str(crf)]
        run(cmd)
        report=check_master(graded,master,expected_width=width)
        if report['technical_status']!='PASS':
            raise RuntimeError('Final QA FAIL: '+', '.join(report['errors']))
        run(['ffmpeg','-hide_banner','-loglevel','error','-xerror',
             '-i',str(master),'-map','0:v:0','-f','null','-'])
        outputs={}
        for name in ('instagram','linkedin','youtube-shorts'):
            dest=outdir/f'final_{name}.mp4'
            shutil.copyfile(master,dest)
            outputs[name]=str(dest)
        result={'schema_version':1,'technical_status':'PASS',
                'creative_status':'REVIEW REQUIRED — not certified natural/cinematic',
                'catalog_total':len(AVAILABLE_EFFECTS),
                'selected_effects':[x['fx'] for x in workplan],
                'grade_before_graphics':look,'source':video.name,
                'preview':preview_seconds is not None,
                'source_fps':original['fps'],'output_fps':report['output_media']['fps'],
                'qa':report,'original_audio_md5':audio_md5(source),
                'master_audio_md5':audio_md5(master),
                'output':str(master),'platform_copies':outputs,
                'platform_note':'Same portrait H264/AAC master, no platform-specific video layout or bitrate.',
                'creative_review':'Inspect motion, keyframes, masking, exact speech, exposure, skin, titles and music; do not publish solely on technical PASS.'}
        (outdir/'production_qa.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
        return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='action',required=True)
    sub.add_parser('catalog')
    plan=sub.add_parser('plan',help='Turn explicit FX edit cues into validated JSON')
    plan.add_argument('video',type=Path)
    plan.add_argument('--instructions',required=True,type=Path)
    plan.add_argument('--output',required=True,type=Path)
    plan.add_argument('--script',type=Path)
    plan.add_argument('--brief',type=Path)
    plan.add_argument('--transcript-verified',action='store_true')
    export=sub.add_parser('render',help='Grade source, apply 42-effect plan, QA and package MP4')
    export.add_argument('video',type=Path);export.add_argument('--plan',required=True,type=Path)
    export.add_argument('--output-dir',required=True,type=Path)
    export.add_argument('--look',choices=('clean-studio','editorial-cinema','neutral','restoration'),default='clean-studio')
    export.add_argument('--brand',choices=('executive','none'),default='executive')
    export.add_argument('--width',type=int)
    export.add_argument('--crf',type=int,default=18)
    export.add_argument('--chunk-frames',type=int,default=180)
    export.add_argument('--preview-start',type=float)
    export.add_argument('--preview-seconds',type=float)
    args=p.parse_args()
    if args.action=='catalog':
        names,aliases,looks=read_registry()
        print(json.dumps({'count':len(names),'effects':names,'aliases':aliases,'named_looks':looks},indent=2))
        return
    try:
        if args.action=='plan':
            result=prepare(args.video,args.instructions,args.output,args.script,args.brief,args.transcript_verified)
        else:
            if not 12<=args.crf<=25:p.error('--crf must be 12–25')
            if args.preview_start is not None and args.preview_seconds is None:
                p.error('--preview-start requires --preview-seconds')
            result=release(args.video,args.plan,args.output_dir,args.look,args.width,args.brand,
                           args.crf,args.chunk_frames,args.preview_start,args.preview_seconds)
        print(json.dumps(result,indent=2,ensure_ascii=False))
    except (ValueError,RuntimeError,FileNotFoundError,subprocess.CalledProcessError) as exc:
        p.exit(1,f'Production pipeline failed: {exc}\n')

if __name__=='__main__':main()
