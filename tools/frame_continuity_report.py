#!/usr/bin/env python3
"""Check frame alignment around cinematic chunk joins using FFmpeg PSNR.

Image similarity cannot prove temporal perfection on static footage.
Human review of every join, caption and sound remains mandatory.
"""
from __future__ import annotations
import argparse,json,re,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from cinematic_finish import probe,video_filter

def frame_count(path):
    p=subprocess.run(['ffprobe','-v','error','-select_streams','v:0',
      '-show_entries','stream=nb_frames','-of','json',str(path)],
      check=True,text=True,capture_output=True)
    tracks=json.loads(p.stdout)['streams']
    if len(tracks)!=1 or not str(tracks[0].get('nb_frames','')).isdigit():
        raise ValueError('Source/output must expose exact video frame counts')
    return int(tracks[0]['nb_frames'])

def selection(ids,shift=0):
    return '+'.join(f'eq(n\\,{n+shift})' for n in ids)

def compare(source,master,ids,look,fps):
    grade=video_filter(probe(source),look)
    with tempfile.TemporaryDirectory(prefix='join_qa_') as directory:
        graph=['[0:v]split=3[rp][r0][rn]','[1:v]split=3[op][o0][on]']
        for delta,key in [(-1,'p'),(0,'0'),(1,'n')]:
            graph.extend([
                f'[r{key}]select={selection(ids,delta)},setpts=N/({fps}*TB),{grade}[src{key}]',
                f'[o{key}]select={selection(ids)},setpts=N/({fps}*TB)[out{key}]',
                f'[src{key}][out{key}]psnr=stats_file={directory}/{key}.txt[ps{key}]'])
        cmd=['ffmpeg','-hide_banner','-loglevel','error','-nostdin',
             '-filter_complex_threads','2','-i',str(source),'-i',str(master),
             '-filter_complex',';'.join(graph),
             '-map','[psp]','-map','[ps0]','-map','[psn]','-f','null','-']
        subprocess.run(cmd,check=True,capture_output=True,text=True)
        data={}
        for delta,key in [(-1,'p'),(0,'0'),(1,'n')]:
            lines=(Path(directory)/f'{key}.txt').read_text().strip().splitlines()
            if len(lines)!=len(ids):
                raise RuntimeError(f'PSNR comparison expected {len(ids)} samples; got {len(lines)}')
            values=[]
            for line in lines:
                m=re.search(r'\bpsnr_avg:(inf|[0-9.]+)\b',line)
                if not m:raise ValueError(f'Invalid FFmpeg PSNR line: {line}')
                values.append(float(m.group(1)))
            data[delta]=dict(zip(ids,values))
        return data

def score(measurements,ids,min_psnr=29.,shift_margin_db=2.):
    samples=[]
    for n in ids:
        expected=measurements[0][n]
        prior=measurements[-1][n]
        following=measurements[1][n]
        samples.append({'frame':n,'psnr_expected_db':round(expected,2),
          'psnr_source_previous_db':round(prior,2),
          'psnr_source_next_db':round(following,2),
          'suspected_shift':max(prior,following)>expected+shift_margin_db,
          'poor_image_match':expected<min_psnr})
    suspects=sum(x['suspected_shift'] or x['poor_image_match'] for x in samples)
    return {'technical_status':'FAIL' if suspects else 'PASS',
      'tested_frames':len(samples),'suspect_frames':suspects,
      'minimum_psnr_db':min_psnr,'shift_margin_db':shift_margin_db,
      'samples':samples,
      'limitations':'Stationary scenes and subtle repeats may escape PSNR detection; manually inspect every join.'}

def evaluate(source,master,chunk_frames=180,look='editorial-cinema',
             min_psnr=29.,shift_margin_db=2.):
    source,master=Path(source).resolve(),Path(master).resolve()
    if source==master or not source.is_file() or not master.is_file():
        raise ValueError('Specify distinct existing source and master files')
    a,b=frame_count(source),frame_count(master)
    if a!=b:raise ValueError(f'Frame-count mismatch: {a} vs {b}')
    info,finished=probe(source),probe(master)
    if info['fps']!=finished['fps']:
        raise ValueError(f'FPS mismatch: {info["fps"]} vs {finished["fps"]}')
    if not 30<=chunk_frames<=1200:
        raise ValueError('Chunk length must be 30..1200 frames')
    if look not in ('editorial-cinema','clean-studio','neutral'):
        raise ValueError('Temporal restoration and unknown grades are unsupported for spot checking')
    boundaries=list(range(chunk_frames,a,chunk_frames))
    ids=sorted({i for b in boundaries for i in (b-2,b-1,b,b+1,b+2) if 1<=i<a-1})
    if not ids:raise ValueError('No full chunk join to inspect')
    report=score(compare(source,master,ids,look,info['fps']),ids,min_psnr,shift_margin_db)
    report.update({'source':source.name,'render':master.name,
      'source_frames':a,'render_frames':b,'boundaries':boundaries,
      'look':look,'creative_review':'REQUIRED: inspect video cuts, subtitles, research and sound'})
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path);p.add_argument('master',type=Path)
    p.add_argument('--chunk-frames',type=int,default=180)
    p.add_argument('--look',choices=('editorial-cinema','clean-studio','neutral'),
                   default='editorial-cinema')
    p.add_argument('--minimum-psnr',type=float,default=29.)
    p.add_argument('--shift-margin-db',type=float,default=2.)
    p.add_argument('--output',required=True,type=Path)
    args=p.parse_args()
    if not 20<=args.minimum_psnr<=50 or not 1<=args.shift_margin_db<=6:
        p.error('PSNR threshold must be 20..50 dB and shift margin 1..6 dB')
    report=evaluate(args.source,args.master,args.chunk_frames,args.look,
                    args.minimum_psnr,args.shift_margin_db)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(f"{report['technical_status']}: {report['tested_frames']} frames checked, {report['suspect_frames']} suspects")
    if report['technical_status']!='PASS':raise SystemExit(1)

if __name__=='__main__':main()
