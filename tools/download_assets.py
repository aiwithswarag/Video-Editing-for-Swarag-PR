#!/usr/bin/env python3
"""Download pinned original models and fonts, verifying Git blob hashes."""
import hashlib
from pathlib import Path
from urllib.request import urlopen
ROOT=Path(__file__).resolve().parents[1]
REV="d675cff93cb3719a5728348566f80ba44073c9e0"
BASE=f"https://raw.githubusercontent.com/Vibha-Ramprakash/claude-video-effects/{REV}/"
ASSETS={
"models/yunet.onnx":"f9beb3044f3791affe1c2f0932af31927e2e4705",
"models/selfie_segmenter.tflite":"a4ebd4777ede40ba04abc8e5c28a73407cb7a1a0",
"models/NOTICE.md":"678dc0cf9a80bcc45da6ce1b0f21ff83512bfda6",
"fonts/ArchivoBlack-Regular.ttf":"82d07de3b84ed4428f6a302b70f4b555148dfeb0",
"fonts/InstrumentSerif-Italic.ttf":"192c3eda9864241ad280e9bcc84e258c80a4a588",
"fonts/SpaceMono-Bold.ttf":"2c4f2682f915d988e7314544ff7c9e38c8c733f5",
"fonts/PermanentMarker-Regular.ttf":"3218fc5b3d395c3a3fc207fdf17a27bb32af3242",
"fonts/Inter.ttf":"047c92f6e2212473dc436020afed689527076d44",
"fonts/Anton-Regular.ttf":"c7d74558de6454f0f5f095cbde5967aa9a7ac00d",
"fonts/Montserrat.ttf":"c97aca18592834d8706549c279cb8d5ac5d85f69",
"fonts/PlayfairDisplay.ttf":"7a09eb71f10622fd083134ac9ed46f59b21bee18",
"fonts/PlayfairDisplay-Italic.ttf":"94fae1f2853dd325b1a3602370780d154ffc8c89",
"fonts/OFL-Anton.txt":"fa985cd1ce56d84853180b96fca5add88696cbd1",
"fonts/OFL-ArchivoBlack.txt":"8894736938f94c6c7a81f27501f26151c412fcbc",
"fonts/OFL-InstrumentSerif.txt":"669ce7917bec662fcf7244d37f49c4277f6fbd73",
"fonts/OFL-Montserrat.txt":"0249f9ff1c3051079f565a0ad82184bc5c9524b0",
"fonts/OFL-PlayfairDisplay.txt":"13153890847ba9bde8a852596d1515261156e474",
"fonts/OFL-SpaceMono.txt":"a72b0a7845bec3214559673ffeba60c816a21841",
"fonts/LICENSE-PermanentMarker.txt":"d645695673349e3947e8e5ae42332d0ac3164cd7",
"fonts/OFL-Inter.txt":"21f6aff961064c2e429f570995e446bcdd555422"
}
def git_sha(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+bytes([0])+data).hexdigest()
def main():
    for name,expected in ASSETS.items():
        target=ROOT/name
        if target.is_file() and git_sha(target.read_bytes())==expected:print("OK",name);continue
        with urlopen(BASE+name,timeout=40) as response:data=response.read()
        if git_sha(data)!=expected:raise RuntimeError(f"Checksum mismatch {name}")
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        print("Downloaded",name)
if __name__=="__main__":main()
