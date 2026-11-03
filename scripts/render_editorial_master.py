#!/usr/bin/env python3
"""Full-resolution editorial export: render title windows only, preserve original audio.

Requires FFmpeg and the licensed source fonts. Complements all 42 original effects.
The editor does not invent speech captions or approve creative work by itself.
"""
from __future__ import annotations
import argparse
import json
import subprocess
import tempfile
from pathlib import Path
from editorial_director import layout,check_story,media_info

ROOT=Path(__file__).resolve().parents[1]

def parts(beats,duration):
    result=[];pos=0.
    for beat in beats:
        s,e=beat['start'],beat['end']
        if s>pos+1e-6:result.append((pos,s,None))
        result.append((s,e,beat));pos=e
    if pos<duration-1e-6:result.append((pos,duration,None))
    return result or [(0.,duration,None)]

def run(cmd):subprocess.run(cmd,check=True)

def render(video,story,output,width=1080,fps=29.5,preset='ultrafast',crf=21,fontdir=None):
    video,output=Path(video).resolve(),Path(output).resolve()
    if not video.is_file() or output==video or output.suffix.lower()!='.mp4':
        raise ValueError('Input missing, invalid output, or same input/output')
    duration,sw,sh=media_info(video)
    data=json.loads(Path(story).read_text(encoding='utf8'))
    beats=check_story(data,duration)
    if data.get('requires_transcript') and not data.get('transcript_verified'):
        raise ValueError('Transcript-led copy must be verified')
    if width%2 or not 360<=width<=2160 or not 8<=fps<=60 or not 0<=crf<=35:
        raise ValueError('Invalid output settings')
    if preset not in ('ultrafast','superfast','veryfast','fast','medium'):
        raise ValueError('Invalid encoder preset')
    height=round(width*sh/sw/2)*2
    fonts=Path(fontdir) if fontdir else ROOT/'fonts'
    windows=parts(beats,duration)
    with tempfile.TemporaryDirectory(prefix='editorial_master_') as temporary:
        folder=Path(temporary)
        clips=[]
        for index,(start,end,beat) in enumerate(windows):
            outfile=folder/f'part_{index:02d}.mp4'
            cmd=['ffmpeg','-hide_banner','-loglevel','error','-y',
                 '-ss',f'{start:.6f}','-i',str(video)]
            base=f'fps={fps:.6f},scale={width}:{height}:flags=bicubic,setsar=1,eq=contrast=1.028:saturation=0.97'
            if beat is not None:
                png=folder/f'art_{index:02d}.png'
                layout(width,height,beat,fonts).save(png)
                cmd+=['-loop','1','-framerate',str(fps),'-i',str(png)]
                fade=min(.4,(end-start)/2)
                graph=(f'[0:v]{base},format=yuv420p[base];'
                       f'[1:v]format=rgba,fade=t=in:st=0:d={fade:.4f}:alpha=1,'
                       f'fade=t=out:st={end-start-fade:.4f}:d={fade:.4f}:alpha=1[art];'
                       f'[base][art]overlay=shortest=1:format=auto,format=yuv420p[v]')
                cmd+=['-filter_complex',graph,'-map','[v]']
            else:
                cmd+=['-vf',base,'-map','0:v:0']
            cmd+=['-t',f'{end-start:.6f}','-an','-c:v','libx264','-preset',preset,
                  '-crf',str(crf),'-pix_fmt','yuv420p','-r',str(fps),
                  '-video_track_timescale','30000',str(outfile)]
            run(cmd)
            if not outfile.exists() or outfile.stat().st_size<1000:
                raise RuntimeError(f'Segment {index} is empty')
            clips.append(outfile)
            print(f'Rendered {index+1}/{len(windows)} | {start:.2f}-{end:.2f}s | art={beat is not None}',flush=True)
        playlist=folder/'list.txt'
        playlist.write_text(''.join(f"file '{file.as_posix()}'\n" for file in clips),encoding='utf8')
        output.parent.mkdir(parents=True,exist_ok=True)
        run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(playlist),
             '-i',str(video),'-map','0:v:0','-map','1:a:0?',
             '-c:v','copy','-c:a','copy','-movflags','+faststart','-t',str(duration),str(output)])
    d,ow,oh=media_info(output)
    if (ow,oh)!=(width,height) or abs(d-duration)>.13:
        raise RuntimeError(f'Export failed dimension/duration QA: {(ow,oh,d)}')
    return {'source_duration':duration,'output_duration':d,'dimensions':[ow,oh],
            'effects_windows':len(beats),'audio':'source stream copied, no master applied',
            'approval':'DRAFT: manually verify edits and source speech'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('input',type=Path);p.add_argument('story',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--width',type=int,default=1080);p.add_argument('--fps',type=float,default=29.5)
    p.add_argument('--font-dir',type=Path);p.add_argument('--preset',default='ultrafast')
    p.add_argument('--crf',type=int,default=21)
    a=p.parse_args()
    print(json.dumps(render(a.input,a.story,a.output,a.width,a.fps,a.preset,a.crf,a.font_dir),indent=2))
if __name__=='__main__':main()
