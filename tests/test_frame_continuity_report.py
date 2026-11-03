"""Regression checks for source-aligned sample frames at resumable video joins."""
import shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'scripts')]
from frame_continuity_report import evaluate,score
from resumable_cinematic_master import process

class FrameContinuityUnitTests(unittest.TestCase):
    def test_shift_detector(self):
        ids=[30]
        good=score({-1:{30:21.},0:{30:44.},1:{30:22.}},ids)
        bad=score({-1:{30:21.},0:{30:26.},1:{30:45.}},ids)
        self.assertEqual('PASS',good['technical_status'])
        self.assertEqual('FAIL',bad['technical_status'])
        self.assertTrue(bad['samples'][0]['suspected_shift'])

@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'FFmpeg unavailable')
class FrameContinuityIntegrationTests(unittest.TestCase):
    def test_real_motion_clean_then_deliberately_shifted(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);source=root/'source.mp4';out=root/'out'
            subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',
                '-f','lavfi','-i','testsrc2=size=180x320:rate=59/2:duration=2.5',
                '-f','lavfi','-i','sine=frequency=440:sample_rate=48000:duration=2.5',
                '-c:v','libx264','-preset','ultrafast','-pix_fmt','yuv420p',
                '-c:a','aac','-shortest',str(source)],check=True)
            master=process(source,out,preset='ultrafast',crf=20,frames_per_chunk=30)['master']
            good=evaluate(source,master,30,'editorial-cinema')
            self.assertEqual('PASS',good['technical_status'])
            self.assertGreater(good['tested_frames'],0)
            self.assertEqual(0,good['suspect_frames'])
            bad=root/'shifted.mp4'
            subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',
                '-i',master,'-map','0:v:0','-map','0:a:0',
                '-vf','trim=start_frame=1,setpts=N/(29.5*TB),tpad=stop_mode=clone:stop=1',
                '-frames:v',str(good['render_frames']),'-r','59/2','-fps_mode','cfr',
                '-c:v','libx264','-preset','ultrafast','-crf','20','-c:a','copy',
                str(bad)],check=True)
            faulty=evaluate(source,bad,30,'editorial-cinema')
            self.assertEqual('FAIL',faulty['technical_status'])
            self.assertGreater(faulty['suspect_frames'],0)

if __name__=='__main__':unittest.main()
