#!/usr/bin/env python3
"""Technical master QA: codec, duration, FPS, frame count and bit-identical audio.
A PASS never means the edit's appearance or spoken content is approved.
"""
from __future__ import annotations
import argparse,json,math,re,subprocess
from pathlib import Path

def inspect(path):
    cmd=['ffprobe','-v','error','-show_entries',
         'format=duration:stream=codec_type,codec_name,width,height,avg_frame_rate,nb_frames,sample_aspect_ratio',
         '-of','json',str(path)]
    d=json.loads(subprocess.run(cmd,capture_output=True,text=True,check=True).stdout)
    tracks=d.get('streams',[])
    videos=[x for x in tracks if x.get('codec_type')=='video']
    audios=[x for x in tracks if x.get('codec_type')=='audio']
    if len(videos)!=1:raise ValueError('Expected exactly one video stream')
    v=videos[0]
    a,b=v.get('avg_frame_rate','0/1').split('/')
    fps=float(a)/float(b)
    if not math.isfinite(fps) or fps<=0:raise ValueError('Invalid FPS')
    return {'duration':float(d['format']['duration']),
            'width':int(v['width']),'height':int(v['height']),'fps':fps,
            'frames':int(v['nb_frames']) if v.get('nb_frames','N/A').isdigit() else None,
            'video_codec':v['codec_name'],'video_sar':v.get('sample_aspect_ratio'),
            'audio_codec':audios[0].get('codec_name') if audios else None,
            'audio_streams':len(audios)}

def audio_stream_md5(path):
    r=subprocess.run(['ffmpeg','-v','error','-i',str(path),'-map','0:a:0',
                      '-c','copy','-f','md5','-'],capture_output=True,text=True,check=True)
    m=re.search(r'MD5=([0-9a-f]{32})',r.stdout)
    if not m:raise ValueError('No stream MD5 from FFmpeg')
    return m.group(1)

def assess(source,output,expected_width=None,allow_fps_change=False,require_audio_copy=True):
    failure=[]
    if source['audio_streams']<1 or output['audio_streams']<1:
        failure.append('Missing original/output audio')
    if source['video_codec']!='h264' or output['video_codec']!='h264':
        failure.append('Expected H264 video')
    if abs(output['duration']-source['duration'])>.12:
        failure.append('Duration drift exceeds 120 milliseconds')
    if output['width']!=(expected_width or source['width']):
        failure.append('Unexpected output width')
    if abs(output['height']/output['width']-source['height']/source['width'])>.004:
        failure.append('Aspect ratio unexpectedly changed')
    if not allow_fps_change and abs(output['fps']-source['fps'])>.05:
        failure.append('Frame rate unexpectedly changed')
    if not allow_fps_change and source['frames'] is not None and output['frames'] is not None:
        if abs(output['frames']-source['frames'])>1:
            failure.append('Frame count differs by more than one frame')
    if require_audio_copy and source['audio_codec']!=output['audio_codec']:
        failure.append('Original audio codec changed')
    return failure

def evaluate(input_path,output_path,expected_width=None,allow_fps_change=False,require_audio_copy=True):
    source=inspect(input_path);out=inspect(output_path)
    errors=assess(source,out,expected_width,allow_fps_change,require_audio_copy)
    src_hash=out_hash=None
    if require_audio_copy and source['audio_streams'] and out['audio_streams']:
        src_hash=audio_stream_md5(input_path);out_hash=audio_stream_md5(output_path)
        if src_hash!=out_hash:errors.append('Source and output AAC bitstreams differ')
    return {'schema_version':1,'source':input_path.name,'render':output_path.name,
            'technical_status':'PASS' if not errors else 'FAIL',
            'creative_status':'NOT APPROVED - manual footage and transcript review required',
            'source_media':source,'output_media':out,
            'duration_delta_s':round(out['duration']-source['duration'],6),
            'source_audio_md5':src_hash,'output_audio_md5':out_hash,
            'audio_bitstream_identical':src_hash==out_hash if require_audio_copy else None,
            'errors':errors}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('input',type=Path);p.add_argument('render',type=Path)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--expected-width',type=int)
    p.add_argument('--allow-fps-change',action='store_true')
    p.add_argument('--allow-audio-remaster',action='store_true')
    a=p.parse_args()
    report=evaluate(a.input,a.render,a.expected_width,a.allow_fps_change,not a.allow_audio_remaster)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(report['technical_status'],':',','.join(report['errors']) or 'streams, timing and audio verified')
    if report['errors']:raise SystemExit(1)
if __name__=='__main__':main()
