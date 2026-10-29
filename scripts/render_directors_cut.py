#!/usr/bin/env python3
"""Conservative camera reframes, preserving the original dialogue and timing.

Use an explicitly reviewed plan; never infer spoken words from silence. The
stream-copied audio is unmodified. Supports portrait 9:16 recordings.
"""
from __future__ import annotations
import argparse,json,math,subprocess
from fractions import Fraction
from pathlib import Path

def validate_plan(data,duration):
    if not isinstance(data,dict) or not isinstance(data.get('reframes'),list):
        raise ValueError("Plan must contain a 'reframes' list")
    if not math.isfinite(duration) or duration<=0:raise ValueError('Invalid duration')
    cuts=[]
    for i,c in enumerate(data['reframes']):
        if not isinstance(c,dict):raise ValueError(f'Reframe {i}: expected object')
        s,e,z=c.get('start'),c.get('end'),c.get('zoom')
        if any(isinstance(x,bool) or not isinstance(x,(float,int)) or not math.isfinite(x) for x in (s,e,z)):
            raise ValueError(f'Reframe {i}: finite start/end/zoom required')
        if s<0 or e-s<1.25 or e>duration+.02 or not 1.01<=z<=1.14:
            raise ValueError(f'Reframe {i}: invalid range or excessive crop')
        if cuts and s<cuts[-1]['end']+.25:
            raise ValueError('Reframes must be sorted and spaced at least 0.25 seconds apart')
        cuts.append({'start':float(s),'end':float(e),'zoom':float(z)})
    if len(cuts)>12:raise ValueError('Excessive reframe frequency')
    return cuts

def zoom_expression(cuts):
    expr='1'
    for p in reversed(cuts):
        expr=(f"if(between(in_time,{p['start']:.3f},{p['end']:.3f}),"
              f"{p['zoom']:.4f},{expr})")
    return expr

def probe(path):
    r=subprocess.run(['ffprobe','-v','error','-select_streams','v:0',
                      '-show_entries','stream=width,height,avg_frame_rate:format=duration',
                      '-of','json',str(path)],capture_output=True,text=True,check=True)
    d=json.loads(r.stdout)
    v=d['streams'][0]
    return float(d['format']['duration']),int(v['width']),int(v['height']),Fraction(v['avg_frame_rate']).limit_denominator(1000)

def make_command(source,out,cuts,duration,width,height,fps,crf=22,preset='ultrafast'):
    if preset not in ('ultrafast','superfast','veryfast','fast','medium'):
        raise ValueError('Unsupported encoder preset')
    if not 16<=crf<=34 or width<360 or width%2 or height%2:raise ValueError('Invalid quality/dimensions')
    fpsarg=f'{fps.numerator}/{fps.denominator}'
    vf=(f"fps={fpsarg},zoompan=z='{zoom_expression(cuts)}':"
        f"x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':"
        f"d=1:s={width}x{height}:fps={fpsarg},format=yuv420p")
    return ['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(source),
            '-vf',vf,'-map','0:v:0','-map','0:a:0?',
            '-c:v','libx264','-preset',preset,'-crf',str(crf),
            '-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',str(out)]

def render(source,plan_path,output,width=None,crf=22,preset='ultrafast'):
    source=Path(source).resolve();output=Path(output).resolve()
    if not source.is_file():raise FileNotFoundError(source)
    if source==output or output.suffix.lower()!='.mp4':raise ValueError('Invalid output')
    duration,sw,sh,fps=probe(source)
    if abs(sh/sw-16/9)>.025:raise ValueError('Current camera director supports portrait 9:16 only')
    width=width or sw
    height=round(width*sh/sw/2)*2
    cuts=validate_plan(json.loads(Path(plan_path).read_text('utf8')),duration)
    output.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(make_command(source,output,cuts,duration,width,height,fps,crf,preset),check=True)
    if not output.is_file() or output.stat().st_size<1024:raise RuntimeError('No output video')
    return {'source_duration':duration,'reframes':cuts,'fps':str(fps),
            'output_width':width,'output_height':height,
            'source_audio':'stream-copied unchanged',
            'creative_approval':'PENDING — transcript and visual review required'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('input',type=Path);p.add_argument('plan',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--width',type=int);p.add_argument('--crf',type=int,default=22)
    p.add_argument('--preset',default='ultrafast')
    a=p.parse_args()
    print(json.dumps(render(a.input,a.plan,a.output,a.width,a.crf,a.preset),indent=2))
if __name__=='__main__':main()
