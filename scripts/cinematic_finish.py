#!/usr/bin/env python3
"""Camera-look finishing of a REVIEWED portrait edit: no fake optics or extra pixels."""
import argparse,json,subprocess
from pathlib import Path

LOOKS={
"clean-studio":"eq=contrast=1.055:brightness=-0.008:saturation=0.96:gamma=1.01,colorbalance=rs=-0.012:bs=0.018:rm=-0.012:bm=0.013:rh=0.006:bh=-0.003:pl=1,unsharp=5:5:0.28:5:5:0",
"editorial-cinema":"eq=contrast=1.075:brightness=-0.013:saturation=0.90:gamma=1.018,colorbalance=rs=-0.020:bs=0.032:rm=-0.013:bm=0.017:rh=0.006:bh=-0.004:pl=1,unsharp=5:5:0.22:5:5:0",
"neutral":"unsharp=5:5:0.16:5:5:0",
"restoration":"hqdn3d=1.1:0.8:1.3:1.0,eq=contrast=1.025:saturation=0.99,unsharp=5:5:0.2:5:5:0",
}
PLATFORMS={"instagram":("16M","24M","128k",18),
           "linkedin":("18M","30M","192k",18),
           "youtube-shorts":("22M","32M","192k",17)}

def execute(cmd,capture=False):
    return subprocess.run(cmd,check=True,text=True,capture_output=capture)
def probe(path):
    r=execute(["ffprobe","-v","error","-show_entries",
       "format=duration:stream=codec_type,width,height,avg_frame_rate,color_primaries",
       "-of","json",str(path)],True)
    d=json.loads(r.stdout)
    v=next((s for s in d.get("streams",[]) if s.get("codec_type")=="video"),None)
    a=next((s for s in d.get("streams",[]) if s.get("codec_type")=="audio"),None)
    if not v or not a:raise ValueError("Input must contain video and audio")
    return {"width":int(v["width"]),"height":int(v["height"]),
            "fps":v["avg_frame_rate"],"duration":float(d["format"]["duration"]),
            "color":v.get("color_primaries","unknown")}
def video_filter(info,look):
    if look not in LOOKS:raise ValueError("Unknown look")
    w,h=info["width"],info["height"]
    if w%2 or h%2 or not .548<=w/h<=.578:
        raise ValueError("9:16 portrait only; review reframe for other aspect ratios")
    if info["color"] not in ("bt709","unknown"):
        raise ValueError("HDR input needs genuine SDR conversion, not BT.709 relabeling")
    resize=",scale=1080:1920:flags=lanczos" if w>1080 or h>1920 else ""
    return LOOKS[look]+resize+",setsar=1,format=yuv420p"
def command(source,out,info,look,platform,preset="medium",audio="source",start=None,seconds=None):
    if platform not in PLATFORMS:raise ValueError("Unsupported platform")
    if preset not in ("ultrafast","veryfast","fast","medium","slow"):raise ValueError("Bad encoder preset")
    if audio not in ("source","aac"):raise ValueError("Bad audio mode")
    if seconds is not None and (start is None or start<0 or seconds<=0 or start+seconds>info["duration"]+.03):
        raise ValueError("Invalid preview range")
    maxrate,buf,abr,crf=PLATFORMS[platform]
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y"]
    if start is not None:cmd+=["-ss",str(start)]
    cmd+=["-i",str(source)]
    if seconds is not None:cmd+=["-t",str(seconds)]
    cmd+=["-map","0:v:0","-map","0:a:0","-vf",video_filter(info,look),
          "-c:v","libx264","-preset",preset,"-crf",str(crf),
          "-maxrate",maxrate,"-bufsize",buf,"-pix_fmt","yuv420p",
          "-fps_mode","passthrough","-color_primaries","bt709",
          "-color_trc","bt709","-colorspace","bt709"]
    if audio=="source" and seconds is None:cmd+=["-c:a","copy"]
    else:cmd+=["-c:a","aac","-b:a",abr,"-ar","48000"]
    return cmd+["-movflags","+faststart","-avoid_negative_ts","make_zero",str(out)]
def audio_md5(path):
    r=execute(["ffmpeg","-v","error","-i",str(path),"-map","0:a:0","-c","copy","-f","md5","-"],True)
    return r.stdout.strip().split("=")[-1]
def finish(video,folder,look="clean-studio",platform="all",preset="medium",audio="source",
           start=None,seconds=None,script=None):
    video=Path(video).resolve();folder=Path(folder).resolve()
    if not video.is_file():raise FileNotFoundError(video)
    if script is not None and not Path(script).is_file():raise FileNotFoundError(script)
    info=probe(video);video_filter(info,look);folder.mkdir(parents=True,exist_ok=True)
    profiles=list(PLATFORMS) if platform=="all" else [platform]
    digest=audio_md5(video) if audio=="source" and seconds is None else None
    outputs=[]
    for item in profiles:
        out=folder/f"{video.stem.replace(' ','_')}_{look}_{item}.mp4"
        if out==video:raise ValueError("Cannot overwrite source")
        execute(command(video,out,info,look,item,preset,audio,start,seconds))
        actual=probe(out)
        if abs(actual["duration"]-(seconds or info["duration"]))>.13:
            raise RuntimeError("Video export duration drift")
        expected=(min(info["width"],1080),min(info["height"],1920))
        if (actual["width"],actual["height"])!=expected:
            raise RuntimeError("Output dimensions do not match")
        if digest is not None and audio_md5(out)!=digest:
            raise RuntimeError("Source audio stream changed unexpectedly")
        outputs.append({"platform":item,"file":str(out),"duration":actual["duration"],
                        "dimensions":expected,"source_audio_unchanged":digest is not None})
    report={"technical_status":"PASS","source":video.name,"look":look,"exports":outputs,
            "script_reference":Path(script).name if script else None,
            "note":"Script is only a reference; generate and verify actual effect timeline BEFORE this finishing step.",
            "creative_approval":"PENDING — verify image, captions, facts, sound and effects"}
    (folder/"cinematic_qa.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf8")
    return report
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("video",type=Path);p.add_argument("--output-dir",required=True,type=Path)
    p.add_argument("--look",choices=LOOKS,default="clean-studio")
    p.add_argument("--platform",choices=[*PLATFORMS,"all"],default="all")
    p.add_argument("--audio",choices=["source","aac"],default="source")
    p.add_argument("--preset",choices=["ultrafast","veryfast","fast","medium","slow"],default="medium")
    p.add_argument("--start",type=float);p.add_argument("--seconds",type=float)
    p.add_argument("--script",type=Path)
    a=p.parse_args()
    if a.start is None and a.seconds is not None:a.start=0.
    if a.start is not None and a.seconds is None:p.error("--start requires --seconds")
    print(json.dumps(finish(a.video,a.output_dir,a.look,a.platform,a.preset,a.audio,a.start,a.seconds,a.script),indent=2))
if __name__=="__main__":main()
