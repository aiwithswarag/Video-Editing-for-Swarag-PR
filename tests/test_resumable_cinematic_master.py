"""Actual FFmpeg integration test for resumable cinematic masters."""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import resumable_cinematic_master as r

@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'FFmpeg required')
class ResumableMasterSmoke(unittest.TestCase):
    def test_resume_and_shared_exports(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            source=root/'source.mp4'
            out=root/'outputs'
            subprocess.run([
                'ffmpeg','-hide_banner','-loglevel','error','-y',
                '-f','lavfi','-i','testsrc2=size=180x320:rate=59/2:duration=1.5',
                '-f','lavfi','-i','sine=frequency=420:sample_rate=48000:duration=1.5',
                '-c:v','libx264','-preset','ultrafast','-pix_fmt','yuv420p',
                '-c:a','aac','-b:a','96k','-shortest',str(source)],check=True)
            first=r.process(source,out,preset='ultrafast',crf=20,frames_per_chunk=30,next_chunk=True)
            self.assertEqual('INCOMPLETE',first['technical_status'])
            self.assertEqual(1,first['chunks_complete'])
            final=r.process(source,out,preset='ultrafast',crf=20,frames_per_chunk=30)
            self.assertEqual('PASS',final['technical_status'])
            self.assertEqual('REVIEW REQUIRED',final['creative_status'])
            self.assertEqual(r.count_frames(r.stream(source)),final['source_frames'])
            self.assertEqual(r.audio_md5(source),r.audio_md5(out/'cinematic_master.mp4'))
            for platform in r.PLATFORMS:
                target=out/f'cinematic_master_{platform}.mp4'
                self.assertTrue(target.exists())
                self.assertEqual(target.read_bytes(),(out/'cinematic_master.mp4').read_bytes())
            before=(out/'cinematic_master.mp4').stat().st_mtime_ns
            again=r.process(source,out,preset='ultrafast',crf=20,frames_per_chunk=30,final_only=True)
            self.assertEqual('PASS',again['technical_status'])
            self.assertEqual(before,(out/'cinematic_master.mp4').stat().st_mtime_ns)
            self.assertEqual(again['master_file_sha256'],r.file_sha256(out/'cinematic_master.mp4'))
            with self.assertRaises(ValueError):
                r.process(source,out,preset='ultrafast',crf=18,frames_per_chunk=30)


    def test_one_frame_final_chunk_keeps_source_fps(self):
        # This is a regression for x264 B-frame DTS reordering at a 1-frame tail.
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            source=folder/'one-frame-tail.mp4'
            subprocess.run([
                'ffmpeg','-hide_banner','-loglevel','error','-y',
                '-f','lavfi','-i','testsrc2=size=180x320:rate=59/2:duration=2.1',
                '-f','lavfi','-i','sine=frequency=420:sample_rate=48000:duration=2.1',
                '-c:v','libx264','-preset','ultrafast','-pix_fmt','yuv420p',
                '-c:a','aac','-shortest',str(source)],check=True)
            self.assertEqual(61,r.count_frames(r.stream(source)))
            output=folder/'result'
            report=r.process(source,output,preset='veryfast',crf=20,frames_per_chunk=30)
            self.assertEqual('PASS',report['technical_status'])
            self.assertEqual('59/2',r.stream(output/'cinematic_master.mp4')['avg_frame_rate'])
            self.assertEqual(61,r.count_frames(r.stream(output/'cinematic_master.mp4')))
            self.assertEqual(r.audio_md5(source),r.audio_md5(output/'cinematic_master.mp4'))

if __name__=='__main__':
    unittest.main()
