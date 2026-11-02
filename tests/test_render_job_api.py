"""Authenticated Render API transport tests; no private footage or server deployment."""
import http.client
import importlib.util
import json
import shutil
import subprocess
import time
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
spec=importlib.util.spec_from_file_location("render_job_api",ROOT/"tools"/"render_job_api.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class RenderAPITransportTests(unittest.TestCase):
    def setUp(self):
        self.dir=tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.old_path=mod.JOB_DIR
        self.old_token=mod.TOKEN
        mod.JOB_DIR=Path(self.dir.name)
        mod.TOKEN="x"*48
        self.server=mod.ThreadingHTTPServer(("127.0.0.1",0),mod.Handler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.addCleanup(self._close)
    def _close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(5)
        mod.JOB_DIR=self.old_path
        mod.TOKEN=self.old_token
    def request(self,method,path,body=None,auth=True):
        con=http.client.HTTPConnection("127.0.0.1",self.server.server_port,timeout=6)
        headers={"Content-Type":"application/json" if isinstance(body,dict) else "application/octet-stream"}
        if auth:headers["Authorization"]="Bearer "+mod.TOKEN
        if isinstance(body,dict):
            body=json.dumps(body).encode()
        con.request(method,path,body=body,headers=headers)
        res=con.getresponse()
        raw=res.read()
        code=res.status
        con.close()
        return code,json.loads(raw.decode())
    def job(self,verified=False):
        code,response=self.request("POST","/v1/jobs",{
            "effects":[{"fx":"backdrop-word","start":5.2,"end":7.3,
                        "text":"WORLD MODELS"}],
            "requires_transcript":True,
            "transcript_verified":verified,
            "source_clean_confirmed":True})
        self.assertEqual(201,code,response)
        return response["id"]
    def test_authentication_hides_job_and_media(self):
        self.assertEqual(401,self.request("POST","/v1/jobs",{},auth=False)[0])
        self.assertEqual(401,self.request("GET","/v1/jobs/"+"0"*32,auth=False)[0])
        self.assertEqual(404,self.request("GET","/v1/jobs/"+"0"*32)[0])
    def test_script_cannot_start_without_verified_spoken_words(self):
        id=self.job(False)
        movie=b"\x00\x00\x00\x18ftypisom"+b"\x00"*45
        self.assertEqual(201,self.request("PUT",f"/v1/jobs/{id}/video",movie)[0])
        self.assertEqual(201,self.request("PUT",f"/v1/jobs/{id}/script",b'Actual script')[0])
        code,payload=self.request("POST",f"/v1/jobs/{id}/start",{})
        self.assertEqual(409,code)
        self.assertIn("Verified",payload["error"])
        self.assertEqual("AWAITING_INPUT",self.request("GET",f"/v1/jobs/{id}")[1]["status"])
        self.assertEqual(409,self.request("GET",f"/v1/jobs/{id}/master")[0])
        self.assertEqual(200,self.request("DELETE",f"/v1/jobs/{id}")[0])
        self.assertEqual(404,self.request("GET",f"/v1/jobs/{id}")[0])
    def test_full_citation_rag_script_cannot_render_only_slow_push(self):
        code,info=self.request("POST","/v1/jobs",{
            "effects":[{"fx":"slow-push","start":0,"end":1,"zoom":1.05}],
            "requires_transcript":True,"transcript_verified":True,
            "source_clean_confirmed":True})
        self.assertEqual(201,code,info)
        job=info["id"]
        source=b"\x00\x00\x00\x18ftypisom"+b"\x00"*64
        self.assertEqual(201,self.request("PUT",f"/v1/jobs/{job}/video",source)[0])
        words=b"AI cited a citation. Fictional policies $100 and $150. RAG retrieval documents and the answer may not be current."
        self.assertEqual(201,self.request("PUT",f"/v1/jobs/{job}/script",words)[0])
        code,out=self.request("POST",f"/v1/jobs/{job}/start",{})
        self.assertEqual(409,code,out)
        self.assertIn("Incomplete RAG explainer",out["error"])
        self.assertEqual("AWAITING_INPUT",self.request("GET",f"/v1/jobs/{job}")[1]["status"])

    def test_explicit_rag_mode_cannot_fall_back_to_slow_push(self):
        status,data=self.request("POST","/v1/jobs",{
            "video_mode":"rag",
            "effects":[{"fx":"slow-push","start":0.5,"end":2.0,"zoom":1.04}],
            "requires_transcript":True,"transcript_verified":True,
            "source_clean_confirmed":True,
            "requires_six_section_explainer":False,
            "rag_storyboard":[]})
        self.assertEqual(422,status,data)
        self.assertIn("Six-section explainer required",data["error"])

    def test_invalid_mp4_is_rejected_before_processing(self):
        id=self.job()
        code,_=self.request("PUT",f"/v1/jobs/{id}/video",b"NOT AN MP4")
        self.assertEqual(422,code)
        self.assertFalse((mod.jobdir(id)/"source.mp4").exists())
    def test_no_absolute_external_effect_asset_paths(self):
        code,payload=self.request("POST","/v1/jobs",{"effects":[{
            "fx":"orbit","start":0,"end":1,"images":"/etc/private"
        }]})
        self.assertEqual(422,code,payload)
    def test_old_jobs_are_purged_not_running_jobs(self):
        id=self.job()
        state=mod.metadata(id)
        state["created_at"]=2
        mod.save(id,state)
        mod.erase_old_jobs(now=100_000,max_age=100)
        self.assertFalse(mod.jobdir(id).exists())
        id2=self.job()
        state=mod.metadata(id2)
        state["created_at"]=2
        state["status"]="RUNNING"
        mod.save(id2,state)
        mod.erase_old_jobs(now=100_000,max_age=100)
        self.assertTrue(mod.jobdir(id2).exists())
    @unittest.skipUnless(shutil.which("ffmpeg") and (ROOT/"models"/"selfie_segmenter.tflite").is_file(),
                         "Full FFmpeg/MediaPipe model assets required")
    def test_private_api_can_render_real_synthetic_mp4(self):
        source=Path(self.dir.name)/"synthetic.mp4"
        subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
            "-f","lavfi","-i","testsrc2=size=360x640:rate=8:duration=2",
            "-f","lavfi","-i","sine=frequency=400:sample_rate=48000:duration=2",
            "-c:v","libx264","-preset","ultrafast","-pix_fmt","yuv420p",
            "-c:a","aac","-shortest",str(source)],check=True)
        code,info=self.request("POST","/v1/jobs",{
            "effects":[{"fx":"slow-push","start":0.2,"end":1.5,"zoom":1.05}],
            "source_clean_confirmed":True,
            "transcript_verified":True,
            "requires_transcript":True})
        self.assertEqual(201,code,info)
        job=info["id"]
        self.assertEqual(201,self.request("PUT",f"/v1/jobs/{job}/video",source.read_bytes())[0])
        self.assertEqual(201,self.request("PUT",f"/v1/jobs/{job}/script",b"Verified spoken dialogue")[0])
        self.assertEqual(202,self.request("POST",f"/v1/jobs/{job}/start",{})[0])
        deadline=time.monotonic()+180
        status=None
        while time.monotonic()<deadline:
            code,status=self.request("GET",f"/v1/jobs/{job}")
            if status["status"]!="RUNNING":break
            time.sleep(.5)
        self.assertIsNotNone(status)
        self.assertEqual("REVIEW_REQUIRED",status["status"],status)
        code,body=self.request("GET",f"/v1/jobs/{job}/qa")
        self.assertEqual(200,code,body)
        self.assertEqual("PASS",body["technical_status"])
        code,release=self.request("GET",f"/v1/jobs/{job}/release")
        self.assertEqual(200,code)
        self.assertEqual("CREATIVE_REVIEW_REQUIRED",release["release_status"])
        # Test token-protected MP4 bytes can be returned to an agent.
        con=http.client.HTTPConnection("127.0.0.1",self.server.server_port,timeout=60)
        con.request("GET",f"/v1/jobs/{job}/master",headers={"Authorization":"Bearer "+mod.TOKEN})
        res=con.getresponse();payload=res.read();con.close()
        self.assertEqual(200,res.status)
        self.assertEqual(b"ftyp",payload[4:8])
        self.assertGreater(len(payload),8000)

    def test_no_script_or_video_leak_in_status(self):
        id=self.job()
        code,body=self.request("GET",f"/v1/jobs/{id}")
        self.assertEqual(200,code)
        self.assertEqual({"id","status","created_at","finished_at","error",
                          "master_sha256","effect_names"},set(body))
        self.assertNotIn("transcript_verified",json.dumps(body))

if __name__=="__main__":
    unittest.main()
