#!/usr/bin/env python3
"""Opt-in, two-pass EBU R128 dialogue normalization with independent verification.

Never overwrites the source, never changes video frames, and never claims the
result has been listened to or creatively approved. Use sparingly on spoken voice.
"""
from __future__ import annotations
import argparse,json,math,re,subprocess
from pathlib import Path

MATCH=re.compile(r'\{\s*"input_i"\s*:.*?\}',re.DOTALL)

def parse_report(text):
    parts=MATCH.findall(text)
    if not parts:raise ValueError('No FFmpeg loudnorm measurement JSON found')
    d=json.loads(parts[-1])
    for field in ('input_i','input_tp','input_lra','input_thresh','target_offset'):
        if field not in d or not math.isfinite(float(d[field])):
            raise ValueError(f'Invalid loudness measurement: {field}')
    return d

def run_measure(video,integrated=-18.,true_peak=-1.9,lra=8.):
    filt=f'loudnorm=I={integrated}:TP={true_peak}:LRA={lra}:print_format=json'
    args=['ffmpeg','-hide_banner','-nostats','-i',str(video),'-vn',
          '-af',filt,'-f','null','-']
    result=subprocess.run(args,capture_output=True,text=True,check=True)
    return parse_report(result.stderr)

def normalizer_filter(d,integrated=-18.,true_peak=-1.9,lra=8.):
    return (f'loudnorm=I={integrated}:TP={true_peak}:LRA={lra}:'
            f'measured_I={d["input_i"]}:measured_TP={d["input_tp"]}:'
            f'measured_LRA={d["input_lra"]}:measured_thresh={d["input_thresh"]}:'
            f'offset={d["target_offset"]}:linear=true:print_format=summary')

def master(source,output,integrated=-18.,true_peak=-1.9,bitrate='160k'):
    source=Path(source).resolve();output=Path(output).resolve()
    if not source.is_file() or source==output or output.suffix.lower()!='.mp4':
        raise ValueError('Invalid source/output')
    if not -24<=integrated<=-14 or not -3.0<=true_peak<=-1.0:
        raise ValueError('Targets outside conservative spoken-word range')
    if bitrate not in ('128k','160k','192k'):raise ValueError('Unsupported audio bitrate')
    measurements=run_measure(source,integrated,true_peak)
    output.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(source),
                    '-map','0:v:0','-map','0:a:0','-c:v','copy',
                    '-af',normalizer_filter(measurements,integrated,true_peak),
                    '-c:a','aac','-b:a',bitrate,'-ar','48000',
                    '-movflags','+faststart',str(output)],check=True)
    verification=run_measure(output,integrated,true_peak)
    measured_i=float(verification['input_i']);measured_tp=float(verification['input_tp'])
    passed=(abs(measured_i-integrated)<=.65 and measured_tp<=true_peak+.12)
    return {'source':source.name,'render':output.name,'target_lufs':integrated,
            'target_true_peak_dbtp':true_peak,
            'measured_lufs':measured_i,'measured_true_peak_dbtp':measured_tp,
            'source_video':'stream-copied without re-encoding',
            'source_audio':'re-encoded in a separate, reversible review variant',
            'technical_loudness_status':'PASS' if passed else 'REVIEW REQUIRED',
            'creative_status':'NOT APPROVED — listen on headphones and mobile speaker'}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--lufs',type=float,default=-18)
    p.add_argument('--true-peak',type=float,default=-1.9)
    p.add_argument('--bitrate',choices=['128k','160k','192k'],default='160k')
    p.add_argument('--report',type=Path)
    a=p.parse_args()
    report=master(a.source,a.output,a.lufs,a.true_peak,a.bitrate)
    if a.report:
        a.report.parent.mkdir(parents=True,exist_ok=True)
        a.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2))
    if report['technical_loudness_status']!='PASS':raise SystemExit(1)
if __name__=='__main__':main()
