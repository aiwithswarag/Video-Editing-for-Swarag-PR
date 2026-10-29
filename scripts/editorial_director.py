#!/usr/bin/env python3
"""Swarag Executive Editorial V2: restrained art direction over talking-head video.

Complementary to the existing 42-effect renderer; can post-process its output.
No fabricated subtitles, fake statistics, social widgets, or mandatory watermark.
"""
from __future__ import annotations
import argparse
import json
import math
import subprocess
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
INK=(18,27,38)
GOLD=(183,150,96)
IVORY=(242,239,233)
LIGHT=(232,233,224)

def eased(t):
    t=max(0.,min(1.,t))
    return t*t*(3-2*t)

def opacity_for(t,begin,end,fade=.45):
    return eased((t-begin)/fade)*eased((end-t)/fade)

def check_story(story,duration):
    if not isinstance(story,dict) or not isinstance(story.get('beats'),list):
        raise ValueError('Story needs a beats array')
    out=[]
    last_end=0.
    for index,beat in enumerate(story['beats']):
        if not isinstance(beat,dict):raise ValueError(f'Beat {index} must be an object')
        start,end=beat.get('start'),beat.get('end')
        for value in (start,end):
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
                raise ValueError(f'Beat {index} times must be finite numeric seconds')
        if start<0 or end<=start or end>duration+.01 or start<last_end:
            raise ValueError(f'Beat {index} overlaps or exceeds media duration')
        if beat.get('kind') not in ('opener','chapter','closing'):
            raise ValueError(f'Beat {index} has unknown kind')
        for key in ('eyebrow','headline','subline'):
            value=beat.get(key,'')
            if not isinstance(value,str) or len(value)>95 or '\n' in value:
                raise ValueError(f'Beat {index} invalid {key}')
        out.append(dict(beat))
        last_end=end
    return out

def fonts(width,font_dir):
    paths={'sans':font_dir/'Inter.ttf','serif':font_dir/'InstrumentSerif-Italic.ttf'}
    if not all(path.is_file() for path in paths.values()):
        raise FileNotFoundError('Install font assets using python tools/download_assets.py')
    def load(kind,sz):
        f=ImageFont.truetype(str(paths[kind]),max(8,int(sz)))
        if kind=='sans':
            try:f.set_variation_by_axes([24,600])
            except (ValueError,OSError,AttributeError):pass
        return f
    return dict(headline=load('serif',width*.083),name=load('sans',width*.062),
                small=load('sans',width*.023),micro=load('sans',width*.018))

def letterspaced(draw,xy,value,font,fill,tracking):
    x,y=xy
    for c in value:
        draw.text((round(x),y),c,font=font,fill=fill)
        x+=draw.textlength(c,font=font)+tracking

def layout(width,height,beat,font_dir):
    """Place text in the wall's upper negative space and the shirt's lower third."""
    if not 1.65<=height/width<=1.9:
        raise ValueError('Executive Editorial V2 is designed for 9:16 portrait clips')
    f=fonts(width,font_dir)
    im=Image.new('RGBA',(width,height),(0,0,0,0))
    draw=ImageDraw.Draw(im)
    left=int(width*.079)
    upper=int(height*.081)
    eyebrow=beat.get('eyebrow','').upper().strip()
    headline=beat.get('headline','').strip()
    sub=beat.get('subline','').strip()
    if eyebrow:
        letterspaced(draw,(left,upper),eyebrow,f['micro'],INK+(240,),width*.0035)
    if headline:
        size=int(width*.083)
        headfont=f['headline']
        available=width-2*left
        while draw.textlength(headline,font=headfont)>available and size>=25:
            size-=2
            headfont=ImageFont.truetype(str(font_dir/'InstrumentSerif-Italic.ttf'),size)
        if draw.textlength(headline,font=headfont)>available:
            raise ValueError('Headline exceeds safe area')
        draw.text((left,upper+int(height*.024)),headline,font=headfont,fill=INK+(255,))
    rule_y=upper+int(height*.102)
    draw.line([(left,rule_y),(left+int(width*.078),rule_y)],fill=GOLD+(235,),width=max(2,int(width*.004)))
    if beat['kind'] in ('opener','closing'):
        y=int(height*.790)
        draw.line([(left,y-16),(left,y+48)],fill=GOLD+(235,),width=max(2,int(width*.005)))
        draw.text((left+int(width*.026),y-22),beat.get('name','SWARAG'),font=f['name'],fill=IVORY+(255,))
        letterspaced(draw,(left+int(width*.027),y+23),
                     (sub or 'STRATEGY  /  DELIVERY').upper(),
                     f['small'],LIGHT+(220,),width*.0015)
    elif sub:
        y=int(height*.790)
        draw.line([(left,y-9),(left+int(width*.11),y-9)],fill=GOLD+(240,),width=max(2,int(width*.004)))
        letterspaced(draw,(left,y+9),sub.upper(),f['small'],IVORY+(240,),width*.001)
    return im

def frame_at(t,width,height,beats,font_dir,cache):
    canvas=Image.new('RGBA',(width,height),(0,0,0,0))
    for i,beat in enumerate(beats):
        alpha=opacity_for(t,beat['start'],beat['end'])
        if alpha<.001:continue
        if i not in cache:cache[i]=layout(width,height,beat,font_dir)
        layer=cache[i].copy()
        layer.putalpha(layer.getchannel('A').point(lambda v:round(v*alpha)))
        slide=round((1-eased((t-beat['start'])/.6))*height*.008)
        canvas.alpha_composite(layer,(0,slide))
    return canvas

def media_info(path):
    res=subprocess.run(['ffprobe','-v','error','-show_entries',
                        'format=duration:stream=width,height,codec_type',
                        '-of','json',str(path)],capture_output=True,text=True,check=True)
    data=json.loads(res.stdout)
    video=next((s for s in data['streams'] if s['codec_type']=='video'),None)
    if video is None:raise ValueError('Input has no video stream')
    return float(data['format']['duration']),video['width'],video['height']

def generate_frames(story,out,width,height,fps,start,seconds,font_dir):
    beats=check_story(story,max(start+seconds,story.get('duration',start+seconds)))
    out.mkdir(parents=True,exist_ok=True)
    cache={}
    frames=math.ceil(seconds*fps)
    for i in range(frames):
        frame_at(start+i/fps,width,height,beats,font_dir,cache).save(
            out/f'{i:05d}.png',compress_level=4)
    return frames

def render(video,out,story,width,fps,start,seconds,root=ROOT,crf=19):
    duration,sw,sh=media_info(video)
    if seconds<=0 or start<0 or start+seconds>duration+.05:
        raise ValueError('Invalid source time range')
    height=round(width*sh/sw/2)*2
    check_story(story,duration)
    with tempfile.TemporaryDirectory(prefix='swarag_editorial_') as folder:
        frames=Path(folder)
        generate_frames(story,frames,width,height,fps,start,seconds,root/'fonts')
        command=['ffmpeg','-hide_banner','-loglevel','error','-y',
                 '-ss',str(start),'-t',str(seconds),'-i',str(video),
                 '-framerate',str(fps),'-start_number','0','-i',str(frames/'%05d.png'),
                 '-filter_complex',
                 f'[0:v]fps={fps},scale={width}:{height}:flags=lanczos,eq=contrast=1.035:saturation=0.93[base];[base][1:v]overlay=0:0:format=auto,format=yuv420p[v]',
                 '-map','[v]','-map','0:a:0?','-c:v','libx264','-preset','veryfast',
                 '-crf',str(crf),'-c:a','aac','-b:a','160k',
                 '-movflags','+faststart','-shortest',str(out)]
        subprocess.run(command,check=True)
    if not out.is_file() or out.stat().st_size<1024:
        raise RuntimeError('No MP4 produced')
    return out

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('video',type=Path)
    p.add_argument('story',type=Path)
    p.add_argument('output',type=Path)
    p.add_argument('--width',type=int,default=540)
    p.add_argument('--fps',type=int,default=15)
    p.add_argument('--start',type=float,default=0.)
    p.add_argument('--seconds',type=float,default=12.)
    p.add_argument('--crf',type=int,default=19)
    a=p.parse_args()
    if not a.video.is_file():p.error('Missing video')
    if a.output.resolve()==a.video.resolve():p.error('Output cannot overwrite input')
    if a.output.suffix.lower()!='.mp4':p.error('Output must be MP4')
    if a.width%2 or not 360<=a.width<=1080:p.error('Width must be even, 360-1080')
    if not 12<=a.fps<=30:p.error('FPS must be 12-30')
    if not 0<=a.crf<=35:p.error('CRF out of range')
    story=json.loads(a.story.read_text(encoding='utf8'))
    render(a.video,a.output,story,a.width,a.fps,a.start,a.seconds,ROOT,a.crf)
    print('Exported',a.output)

if __name__=='__main__':main()
