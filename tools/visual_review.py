#!/usr/bin/env python3
"""Create a visual edit-review sheet from actual MP4 frames (not mock screenshots)."""
from __future__ import annotations
import argparse,json,math,subprocess,tempfile
from fractions import Fraction
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

def review_points(effects,duration,limit=24):
    """Representative real frames at start, body and exit of each effect."""
    if not 0<duration or not math.isfinite(duration):raise ValueError('Invalid duration')
    if not 4<=limit<=48:raise ValueError('Use 4..48 review frames')
    candidates=[(max(0,duration*.02),'Opening'),(duration*.5,'Midpoint'),
                (duration*.98,'Closing')]
    for i,fx in enumerate(effects):
        start=max(0,float(fx['start']));end=min(duration,float(fx['end']))
        if end<=start:continue
        label=f"{i+1}: {fx['fx']}"
        candidates.extend([
          (start+min(.12,(end-start)*.18),label+' / enter'),
          ((start+end)*.5,label+' / peak'),
          (end-min(.12,(end-start)*.18),label+' / exit')
        ])
    # Keep genuine timeline ordering; do not exceed the page budget.
    ordered=sorted(candidates,key=lambda x:x[0])
    unique=[]
    for t,label in ordered:
        if not unique or abs(t-unique[-1][0])>=.07:
            unique.append((t,label))
    if len(unique)>limit:
        # Uniformly cover the complete video even with a very dense showreel.
        take=sorted(set(round(i*(len(unique)-1)/(limit-1)) for i in range(limit)))
        unique=[unique[i] for i in take]
    return unique

def last_decodable_time(video):
    """Container duration often extends past the last video frame due to AAC padding."""
    raw=subprocess.run(['ffprobe','-v','error','-select_streams','v:0',
        '-show_entries','stream=nb_frames,avg_frame_rate','-of','json',str(video)],
        check=True,capture_output=True,text=True)
    track=json.loads(raw.stdout)['streams'][0]
    frames=int(track['nb_frames'])
    rate=Fraction(track['avg_frame_rate'])
    if frames<1 or rate<=0:
        raise ValueError('Invalid frame count / FPS for review frames')
    return max(0.,float(Fraction(frames-1,1)/rate)-.001)


def frame(video,at,path,width=240):
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y',
        '-ss',f'{at:.6f}','-i',str(video),'-map','0:v:0',
        '-vf',f'scale={width}:-2:flags=lanczos',
        '-frames:v','1','-update','1',str(path)],check=True)
    if not path.is_file() or path.stat().st_size<500:
        raise RuntimeError(f'No frame decoded at {at:.3f}s')
    return Image.open(path).convert('RGB')

def create(video,effects,duration,output,limit=24,width=240):
    video=Path(video);output=Path(output)
    if not video.is_file():raise FileNotFoundError(video)
    if width<160 or width>640:raise ValueError('Width must be 160..640')
    last=last_decodable_time(video)
    pts=[(min(t,last),label) for t,label in review_points(effects,duration,limit)]
    cols=4 if len(pts)>4 else len(pts);cols=max(cols,1)
    with tempfile.TemporaryDirectory(prefix='review_frames_') as temp:
        frames=[(frame(video,t,Path(temp)/f'frame_{i:03}.png',width),t,label)
                for i,(t,label) in enumerate(pts)]
        cellw=width+24;cellh=max(im.height for im,_,_ in frames)+55
        header=74;footer=55;rows=math.ceil(len(frames)/cols)
        image=Image.new('RGB',(cellw*cols+24,header+cellh*rows+footer),(242,241,237))
        pen=ImageDraw.Draw(image);font=ImageFont.load_default()
        pen.text((20,15),'SWARAG VIDEO DIRECTOR | REAL EXPORT REVIEW',fill=(15,26,36),font=font)
        pen.text((20,36),f'{len(frames)} actual frames | Creative approval required',fill=(95,103,112),font=font)
        for i,(im,t,label) in enumerate(frames):
            x=16+(i%cols)*cellw;y=header+(i//cols)*cellh
            image.paste(im,(x,y))
            pen.text((x,y+im.height+8),f'{t:.2f}s - {label[:31]}',fill=(25,38,46),font=font)
        pen.text((20,image.height-30),'Watch the COMPLETE MP4 for motion, face occlusion, cadence, joins and audio.',
                 fill=(95,103,112),font=font)
        output.parent.mkdir(parents=True,exist_ok=True)
        image.save(output,quality=90,optimize=True)
    return {'contact_sheet':str(output),'frames':len(frames),
            'review_points':[{'time_s':round(t,3),'label':label} for t,label in pts],
            'creative_status':'NOT APPROVED — real-motion human review still required'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('video',type=Path);p.add_argument('plan',type=Path)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--duration',type=float,required=True)
    p.add_argument('--max-frames',type=int,default=24)
    a=p.parse_args()
    raw=json.loads(a.plan.read_text(encoding='utf8'))
    fx=raw.get('effects',raw) if isinstance(raw,dict) else raw
    print(json.dumps(create(a.video,fx,a.duration,a.output,a.max_frames),indent=2))

if __name__=='__main__':main()
