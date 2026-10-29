"""Production-facing CLI tests: 42-effect coverage, explicit director cues, guardrails."""
import importlib.util,json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(ROOT/'tools'))
spec=importlib.util.spec_from_file_location('produce_video',ROOT/'scripts/produce_video.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
from plan_validation import AVAILABLE_EFFECTS

class PlanDirectivesTests(unittest.TestCase):
    def test_catalog_has_every_registered_effect(self):
        names,_,_=mod.read_registry()
        self.assertEqual(42,len(names))
        self.assertEqual(set(names),set(AVAILABLE_EFFECTS))
    def test_every_effect_accepted_by_directive_parser(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'cues.txt'
            p.write_text('\n'.join(f'FX {name} {i/4} {(i+1)/4}' for i,name in enumerate(sorted(AVAILABLE_EFFECTS))))
            parsed=mod.parse_directives(p)
            self.assertEqual(42,len(parsed))
            self.assertEqual(set(AVAILABLE_EFFECTS),{x['fx'] for x in parsed})
    def test_text_and_options_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'cues.txt'
            p.write_text('FX headline-box 1.0 3.5 text="Human production values" color=#F2EFE9\n')
            got=mod.parse_directives(p)
            self.assertEqual('Human production values',got[0]['text'])
            self.assertEqual('#F2EFE9',got[0]['color'])
    def test_rejects_invalid_unknown_and_shell_tokens(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'cues.txt'
            for line in ('FX invented 0 2','FX slow-push x 2','FX orbit 0 2 invalid',
                         'FX slow-push 2 1','FX slow-push 0 1 start=0'):
                p.write_text(line)
                with self.assertRaises(ValueError,msg=line):mod.parse_directives(p)

@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'FFmpeg runtime required')
class ProductionPipelineSmoke(unittest.TestCase):
    def test_grade_first_effect_edit_with_original_audio(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);src=root/'original.mp4'
            subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',
                '-f','lavfi','-i','testsrc2=size=240x426:rate=8:duration=2',
                '-f','lavfi','-i','sine=frequency=330:sample_rate=48000:duration=2',
                '-c:v','libx264','-preset','ultrafast','-pix_fmt','yuv420p',
                '-c:a','aac','-shortest',str(src)],check=True)
            # 240x426 differs from exact 9:16; use exact 240x? frame shape 360x640.
            native=root/'native.mp4'
            subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',
                '-i',str(src),'-vf','scale=360:640','-c:v','libx264',
                '-preset','ultrafast','-c:a','copy',str(native)],check=True)
            cues=root/'instructions.txt'
            cues.write_text('FX slow-push 0.2 1.5 zoom=1.04\n')
            plan=root/'plan.json'
            found=mod.prepare(native,cues,plan)
            self.assertEqual(1,found['effects'])
            final=mod.release(native,plan,root/'deliver',look='clean-studio',width=360,
                              crf=20,frames_per_chunk=30)
            self.assertEqual('PASS',final['technical_status'])
            self.assertEqual(42,final['catalog_total'])
            self.assertEqual('REVIEW REQUIRED — not certified natural/cinematic',final['creative_status'])
            self.assertEqual(final['original_audio_md5'],final['master_audio_md5'])
            self.assertEqual(3,len(final['platform_copies']))
            self.assertTrue(Path(final['visual_review']['contact_sheet']).is_file())
            self.assertGreaterEqual(final['visual_review']['frames'],4)
            for path in final['platform_copies'].values():
                self.assertTrue(Path(path).is_file())
    def test_fractional_fps_59_over_2_end_to_end(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);source=root/'fractional.mp4'
            subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',
                '-f','lavfi','-i','testsrc2=size=360x640:rate=59/2:duration=2.1',
                '-f','lavfi','-i','sine=frequency=440:sample_rate=48000:duration=2.1',
                '-c:v','libx264','-preset','ultrafast','-pix_fmt','yuv420p',
                '-c:a','aac','-shortest',str(source)],check=True)
            self.assertEqual('59/2',mod.media(source)['fps'])
            cues=root/'cues.txt';cues.write_text('FX slow-push 0.3 1.2 zoom=1.05'+chr(10))
            plan=root/'plan.json';mod.prepare(source,cues,plan)
            final=mod.release(source,plan,root/'out',look='neutral',crf=20,
                              width=360,frames_per_chunk=90)
            self.assertEqual('PASS',final['technical_status'])
            self.assertAlmostEqual(final['output_fps'],29.5,places=2)
            self.assertEqual(final['qa']['output_media']['frames'],
                             final['qa']['source_media']['frames'])
            self.assertEqual(final['original_audio_md5'],final['master_audio_md5'])

    def test_refuses_unverified_speech_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            dummy=root/'video.mp4';dummy.write_bytes(b'not video')
            plan=root/'plan.json'
            plan.write_text(json.dumps({'requires_transcript':True,'transcript_verified':False,
                'effects':[{'fx':'slow-push','start':0,'end':1}]}))
            with self.assertRaises(ValueError):
                mod.release(dummy,plan,root/'out')

if __name__=='__main__':unittest.main()
