#!/usr/bin/env python3
"""Resume an original-resolution 9:16 cinematic grade in frame-checked chunks.

The input is an already REVIEWED edit, not raw footage or an unverified transcript.
A technical PASS cannot certify script truth, art direction, or sound quality.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import shutil
import subprocess
from fractions import Fraction
from pathlib import Path
from cinematic_finish import PLATFORMS, probe, video_filter, audio_md5


def run(args, capture=False):
    return subprocess.run(args, check=True, text=True, capture_output=capture)


def stream(path):
    data = json.loads(run(['ffprobe','-v','error','-select_streams','v:0',
      '-show_entries','stream=codec_name,width,height,nb_frames,avg_frame_rate',
      '-of','json',str(path)], True).stdout)
    if len(data.get('streams', [])) != 1:
        raise ValueError(f'No video stream in {path}')
    return data['streams'][0]


def count_frames(meta):
    try:
        frames = int(meta['nb_frames'])
        if frames <= 0:
            raise ValueError
        return frames
    except (KeyError, TypeError, ValueError):
        raise ValueError('Source must have exact nb_frames metadata; remux to CFR MP4 before chunking')


def make_plan(source, frames_per_chunk, look, preset, crf):
    source = Path(source).resolve()
    info = probe(source)
    video_filter(info, look)
    meta = stream(source)
    fps = Fraction(meta['avg_frame_rate'])
    if fps <= 0 or fps > 60:
        raise ValueError('Source video frame rate out of 0–60fps range')
    total = count_frames(meta)
    if abs(float(total / fps) - info['duration']) > 0.13:
        raise ValueError('Source is not reliably constant-frame-rate; normalize before chunking')
    if not 30 <= frames_per_chunk <= 1200:
        raise ValueError('Chunk length must be 30..1200 frames')
    if preset not in ('ultrafast','superfast','veryfast','fast','medium','slow'):
        raise ValueError('Unsupported x264 preset')
    if not 12 <= crf <= 25:
        raise ValueError('CRF must be 12..25')
    stat = source.stat()
    config = {'source_path':str(source),'size':stat.st_size,'mtime_ns':stat.st_mtime_ns,
              'look':look,'preset':preset,'crf':crf,'fps':str(fps),
              'width':info['width'],'height':info['height'],
              'total_frames':total,'frames_per_chunk':frames_per_chunk}
    ident = hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()
    chunks = [(i, start, min(frames_per_chunk,total-start))
              for i,start in enumerate(range(0,total,frames_per_chunk))]
    return info, fps, chunks, config, ident


def check_chunk(path, frames, size, fps):
    if not path.is_file() or path.stat().st_size < 1024:
        return False
    try:
        s=stream(path)
        return (s.get('codec_name')=='h264' and count_frames(s)==frames
                and (int(s['width']),int(s['height']))==size
                and Fraction(s['avg_frame_rate'])==fps)
    except (ValueError,KeyError,subprocess.CalledProcessError):
        return False


def encode_chunk(source, target, start, frames, fps, info, look, preset, crf):
    target.parent.mkdir(parents=True,exist_ok=True)
    tmp=target.with_name(target.stem+'.tmp.mp4')
    expected=(min(info['width'],1080),min(info['height'],1920))
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y',
         '-ss',f'{float(start/fps):.9f}','-i',str(source),'-map','0:v:0','-an',
         '-vf',video_filter(info,look),'-frames:v',str(frames),
         '-fps_mode','cfr','-r',str(fps),'-c:v','libx264','-preset',preset,
         '-crf',str(crf),'-maxrate','16M','-bufsize','24M',
         '-pix_fmt','yuv420p','-color_primaries','bt709','-color_trc','bt709',
         '-colorspace','bt709','-movflags','+faststart',str(tmp)]
    try:
        run(cmd)
        if not check_chunk(tmp, frames, expected, fps):
            raise RuntimeError(f'Chunk {target.name} failed exact frame/resolution/FPS QA')
        tmp.replace(target)
    finally:
        tmp.unlink(missing_ok=True)


def finalize(source, outdir, chunks, fps, info, ident, approved, report_path):
    playlist=outdir/'chunks.txt'
    playlist.write_text(''.join("file '"+str((outdir/f'chunk_{i:04d}.mp4').resolve()).replace("'","'\\''")+"'\n"
                     for i,_,_ in chunks),encoding='utf8')
    master=outdir/'cinematic_master.mp4'
    temp=outdir/'cinematic_master.tmp.mp4'
    duration=sum(n for _,_,n in chunks)/fps
    try:
        run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y',
             '-f','concat','-safe','0','-i',str(playlist),'-i',str(source),
             '-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','copy',
             '-movflags','+faststart',str(temp)])
        meta=stream(temp)
        expected=(min(info['width'],1080),min(info['height'],1920))
        video_errors=[]
        if not check_chunk(temp,sum(n for _,_,n in chunks),expected,fps):
            video_errors.append('Total frame count, dimensions, fps or H264 codec incorrect')
        exported=probe(temp)
        if abs(exported['duration']-info['duration'])>.13:
            video_errors.append('Output duration differs from input by over 130ms')
        if audio_md5(source)!=audio_md5(temp):
            video_errors.append('Original audio bitstream changed')
        decode=run(['ffmpeg','-v','error','-xerror','-i',str(temp),'-map','0:v:0',
                    '-f','null','-'],True)
        if decode.stderr.strip():
            video_errors.append('Decoder reported errors')
        if video_errors:
            raise RuntimeError('; '.join(video_errors))
        temp.replace(master)
    finally:
        temp.unlink(missing_ok=True)
    platforms={}
    for platform in PLATFORMS:
        destination=outdir/f'cinematic_master_{platform}.mp4'
        shutil.copyfile(master,destination)
        platforms[platform]=str(destination)
    # File names differ, but the deliberately shared upload-quality H264/AAC master is identical.
    report={'schema_version':1,'technical_status':'PASS',
            'creative_status':'APPROVED' if approved else 'REVIEW REQUIRED',
            'note':'Technical gate only. Human approval requires viewing the entire video, captions, research and listening to audio.',
            'render_config_sha256':ident,'source':source.name,'source_frames':sum(n for _,_,n in chunks),
            'source_fps':str(fps),'source_audio_md5':audio_md5(source),
            'output_audio_md5':audio_md5(master),'duration_s':exported['duration'],
            'dimensions':expected,'decode':'PASS','shared_encode':True,
            'master':str(master),'platform_exports':platforms}
    report_path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    return report


def process(source,outdir,look='editorial-cinema',preset='veryfast',crf=18,
            frames_per_chunk=180,next_chunk=False,final_only=False,approved=False):
    source=Path(source).resolve();outdir=Path(outdir).resolve()
    if not source.is_file():raise FileNotFoundError(source)
    if outdir==source.parent and source.name.startswith('cinematic_master'):
        raise ValueError('Output would collide with input')
    info,fps,chunks,config,ident=make_plan(source,frames_per_chunk,look,preset,crf)
    outdir.mkdir(parents=True,exist_ok=True)
    manifest=outdir/'render_manifest.json'
    if manifest.is_file():
        if json.loads(manifest.read_text())['config_sha256']!=ident:
            raise ValueError('Existing chunks belong to a different source/settings; use an empty output folder')
    else:
        if any(outdir.glob('chunk_*.mp4')):
            raise ValueError('Found unmanaged chunks; use an empty output folder')
        manifest.write_text(json.dumps({'config_sha256':ident,'config':config},indent=2)+'\n')
    expected=(min(info['width'],1080),min(info['height'],1920))
    pending=[(i,start,n) for i,start,n in chunks if not check_chunk(outdir/f'chunk_{i:04d}.mp4',n,expected,fps)]
    if not final_only:
        for i,start,n in pending[:1] if next_chunk else pending:
            target=outdir/f'chunk_{i:04d}.mp4'
            encode_chunk(source,target,start,n,fps,info,look,preset,crf)
            print(f'Encoded {i+1}/{len(chunks)}: {n} frames',flush=True)
    remaining=[i for i,_,n in chunks if not check_chunk(outdir/f'chunk_{i:04d}.mp4',n,expected,fps)]
    if remaining:
        result={'technical_status':'INCOMPLETE','chunks_complete':len(chunks)-len(remaining),
                'chunks_total':len(chunks),'next_chunk':remaining[0],
                'instruction':'Run the same command again with --next-chunk, or without it to finish all chunks'}
        print(json.dumps(result,indent=2));return result
    return finalize(source,outdir,chunks,fps,info,ident,approved,outdir/'cinematic_qa.json')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('reviewed_edit',type=Path)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--look',choices=('editorial-cinema','clean-studio','neutral','restoration'),default='editorial-cinema')
    p.add_argument('--preset',choices=('ultrafast','superfast','veryfast','fast','medium','slow'),default='veryfast')
    p.add_argument('--crf',type=int,default=18)
    p.add_argument('--chunk-frames',type=int,default=180)
    mode=p.add_mutually_exclusive_group()
    mode.add_argument('--next-chunk',action='store_true')
    mode.add_argument('--final-only',action='store_true')
    p.add_argument('--approved',action='store_true',help='Mark human creative review signoff, NOT automatic approval')
    a=p.parse_args()
    result=process(a.reviewed_edit,a.output_dir,a.look,a.preset,a.crf,a.chunk_frames,
                   a.next_chunk,a.final_only,a.approved)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
