"""The free local UI uses the original registered effects and never uploads media."""
import base64
import http.client
import io
import json
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import local_director as d
import local_editor as ui


class LocalDraftTests(unittest.TestCase):
    def test_rag_script_time_windows_marked_unverified(self):
        script="# 0–3 sec | Hook\nYour AI cited a source.\n# 3–12 sec | Two policies\nThe old one says $100; the current one says $150.\n# 12–20 sec | Answer\n"
        result=d.draft('Subtle slow-push and backdrop-word, text="POLICIES"',script,50.4)
        self.assertEqual(42,result["effect_catalog_size"])
        self.assertEqual({"slow-push","backdrop-word"},{x["fx"] for x in result["effects"]})
        self.assertTrue(any("scaled proportionally" in w for w in result["warnings"]))
        self.assertEqual("POLICIES",next(x for x in result["effects"] if x["fx"]=="backdrop-word")["text"])
        self.assertIn("NOT SPEECH VERIFIED",result["status"])
    def test_named_42_options_are_never_faked(self):
        result=d.draft("orbit and glass-widgets with slow-push", "Hello.", 20)
        self.assertEqual({"orbit","glass-widgets","slow-push"},{x["fx"] for x in result["effects"]})
        self.assertTrue(all(x["end"]>x["start"] for x in result["effects"]))
    def test_never_invents_on_screen_text(self):
        result=d.draft("Put backdrop-word behind me", "The answer is different", 8)
        self.assertEqual("",result["effects"][0]["text"])
        self.assertTrue(any("supply intentional on-screen copy" in w for w in result["warnings"]))
    @unittest.skipUnless(shutil.which("node"),"Node.js required to lint embedded browser JavaScript")
    def test_local_browser_javascript_syntax(self):
        source=ui.PAGE.split("<script>",1)[1].split("</script>",1)[0]
        source=source.replace("__ORIGINAL_EFFECT_NAMES__",'["slow-push"]')
        source=source.replace("__LOCAL_BEARER_TOKEN__","test-token")
        result=subprocess.run(["node","--check","-"],input=source,
                              text=True,capture_output=True)
        self.assertEqual(0,result.returncode,result.stderr)

    @unittest.skipUnless(shutil.which("node"), "Node.js required to execute browser validation logic")
    def test_rag_render_button_enables_for_eight_valid_stages(self):
        """Regression: undefined ragStages variable previously disabled Render forever."""
        source=ui.PAGE.split("<script>",1)[1].split("</script>",1)[0]
        source=source.replace("__ORIGINAL_EFFECT_NAMES__",'["slow-push"]')
        source=source.replace("__LOCAL_BEARER_TOKEN__","test-token")
        starts=[0,2.749,10.996,18.327,30.24,35.127,40.015,44.902]
        ends=[2.749,10.996,18.327,30.24,35.127,40.015,44.902,50.4]
        node_source=r"""
const vm=require("node:vm");
const assert=require("node:assert/strict");
const stageRows=JSON.parse(process.env.STAGES);
const elements={};
function elem(id){
  if(!elements[id])elements[id]={checked:false,disabled:true,value:"",
    textContent:"",style:{},children:[],files:[],addEventListener:()=>{}};
  return elements[id];
}
elem("clean").checked=true;
elem("verified").checked=true;
elem("layoutApproved").checked=true;
elem("editMode").value="rag";
elem("effects").children=[{data:{
  fx:{fx:"slow-push",start:0.25,end:3.45,zoom:1.055,blur:0},
  sel:{value:"slow-push"},from:{value:"0.25"},to:{value:"3.45"},title:{value:""}
}}];
elem("ragStages").children=stageRows.map(v=>({stage:{
  kind:v.kind,section:v.section,
  start:{value:String(v.start)},end:{value:String(v.end)}
}}));
const ctx=vm.createContext({
  document:{getElementById:elem},
  URL:{createObjectURL:()=>""},
  fetch:async()=>{throw Error("Unexpected network request")},
  setTimeout:()=>{},
});
vm.runInContext(JSON.parse(process.env.BROWSER_JS),ctx);
vm.runInContext("duration=50.4;previewReady=true;check();",ctx);
assert.equal(elem("render").disabled,false,elem("renderReason").textContent);
assert.match(elem("renderReason").textContent,/Ready to render/);
vm.runInContext("previewReady=false;check();",ctx);
assert.equal(elem("render").disabled,true);
assert.match(elem("renderReason").textContent,/glass-widget/);
vm.runInContext("previewReady=true;check();",ctx);
assert.equal(elem("render").disabled,false);
elem("verified").checked=false;
vm.runInContext("check();",ctx);
assert.equal(elem("render").disabled,true);
assert.match(elem("renderReason").textContent,/Check the script/);
elem("verified").checked=true;
elem("layoutApproved").checked=false;
vm.runInContext("check();",ctx);
assert.equal(elem("render").disabled,true);
assert.match(elem("renderReason").textContent,/glass-widget/);
elem("layoutApproved").checked=true;
elem("ragStages").children[7].stage.end.value="51";
vm.runInContext("check();",ctx);
assert.equal(elem("render").disabled,true);
assert.match(elem("renderReason").textContent,/time window/);
console.log("RAG render button enabled with eight valid stages; disabled for unchecked/invalid input");
"""
        import os
        kinds=["hook","policies","outdated-answer","rag-flow",
               "check-1","check-2","check-3","closing"]
        sections=["hook","policies","outdated-answer","rag-flow",
                  "verification-checks","verification-checks","verification-checks","closing"]
        env=os.environ.copy()
        env["BROWSER_JS"]=json.dumps(source)
        env["STAGES"]=json.dumps([{
            "kind":kind,"section":section,"start":a,"end":b
        } for kind,section,a,b in zip(kinds,sections,starts,ends)])
        result=subprocess.run(["node","-e",node_source],env=env,
                              capture_output=True,text=True)
        self.assertEqual(0,result.returncode,result.stderr)
        self.assertIn("RAG render button enabled",result.stdout)

    def test_txt_and_docx_scripts(self):
        self.assertEqual("RAG explained",d.document_text("script.txt",b"RAG explained"))
        out=io.BytesIO()
        with zipfile.ZipFile(out,"w") as z:
            z.writestr("word/document.xml",
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                '<w:body><w:p><w:r><w:t>Correct script</w:t></w:r></w:p></w:body></w:document>')
        self.assertEqual("Correct script",d.document_text("script.docx",out.getvalue()))
        with self.assertRaises(ValueError):d.document_text("script.pdf",b"%PDF-1.7")


class WindowsLauncherGuards(unittest.TestCase):
    def test_old_container_refused_before_browser_open(self):
        bat=(ROOT/"START_FREE_EDITOR_WINDOWS.bat").read_text(encoding="utf-8")
        self.assertIn('docker ps --format "{{.Names}}"',bat)
        self.assertIn('netstat -ano',bat)
        self.assertIn('Stop the previous editor/container',bat)
        self.assertLess(bat.index('docker ps --format'),bat.index("docker build"))
        self.assertLess(bat.index("netstat -ano"),bat.index("Start-Process"))
        self.assertLess(bat.index("docker build"),bat.index("docker run --rm"))


class LocalHostHTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.old_token=ui.api.TOKEN
        self.old_path=ui.api.JOB_DIR
        self.old_port=__import__("os").environ.get("PORT")
        ui.api.TOKEN="local-test-token-"+"x"*48
        ui.api.JOB_DIR=Path(self.temp.name)
        __import__("os").environ["PORT"]="8765"
        self.server=ui.api.ThreadingHTTPServer(("127.0.0.1",0),ui.LocalHandler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.addCleanup(self.stop)
    def stop(self):
        self.server.shutdown();self.server.server_close();self.thread.join(timeout=6)
        ui.api.TOKEN=self.old_token;ui.api.JOB_DIR=self.old_path
        if self.old_port is None:__import__("os").environ.pop("PORT",None)
        else:__import__("os").environ["PORT"]=self.old_port
    def request(self,method,path,body=None,host="127.0.0.1:8765",origin=None,token=True,extra_headers=None,timeout=5):
        c=http.client.HTTPConnection("127.0.0.1",self.server.server_port,timeout=timeout)
        hdr={"Host":host,"Content-Type":"application/json",**(extra_headers or {})}
        if token:hdr["Authorization"]="Bearer "+ui.api.TOKEN
        if origin:hdr["Origin"]=origin
        c.request(method,path,json.dumps(body).encode() if isinstance(body,dict) else body,headers=hdr)
        r=c.getresponse();code=r.status;data=r.read();c.close()
        return code,data
    def test_opening_screen_is_local_only_and_has_real_42_names(self):
        code,data=self.request("GET","/",token=False)
        self.assertEqual(200,code)
        self.assertIn(b"SWARAG / Free Video Director",data)
        self.assertIn(b"slow-push",data)
        self.assertIn(b"backdrop-word",data)
        self.assertIn(b"RAG-SIX-SECTION-GUARD-2026-11-02",data)
        self.assertIn(b"RAG-RENDER-BUTTON-FIX-2026-11-02",data)
        self.assertIn(b"RAG-API-START-FIX-2026-11-02",data)
        self.assertIn(b'id="editMode"',data)
        self.assertIn(b'value="rag" selected',data)
        code,version=self.request("GET","/local/version",token=False)
        self.assertEqual(200,code)
        self.assertTrue(json.loads(version)["rag_six_section_guard"])
        self.assertTrue(json.loads(version)["render_button_fixed"])
        self.assertTrue(json.loads(version)["rag_api_start_fixed"])
        self.assertEqual("subject-masked-glass-v5",
                         json.loads(version)["face_safe_layout_id"])
        self.assertTrue(json.loads(version)["layout_preview_required"])
        self.assertIn(b"subject-masked-glass-v5",data)
        self.assertIn(b"GLASS-MOBILE-LEGIBILITY-2026-11-03",data)
        self.assertIn(b'id="check42"',data)
        self.assertIn(b'id="checkEngine"',data)
        self.assertIn(b'id="check42Status"',data)
        self.assertIn(b'id="download42"',data)
        self.assertIn(b"Test all 42 effects on my camera footage",data)
        self.assertTrue(json.loads(version)["private_real_camera_42_effect_diagnostic"])
        self.assertEqual("ORIGINAL-42-EFFECT-QA-2026-11-03",
                         json.loads(version)["effect_qa_build_id"])
        self.assertIn(b"ORIGINAL-42-EFFECT-QA-2026-11-03",data)
        self.assertEqual("GLASS-MOBILE-LEGIBILITY-2026-11-03",
                         json.loads(version)["glass_legibility_fix_id"])
        self.assertIn(b"Original glass-widgets",data)
        self.assertIn(b'id="previewImage"',data)
        self.assertIn(b'id="layoutApproved"',data)
        self.assertIn(b"layout-preview",data)
        self.assertEqual("RAG-API-START-FIX-2026-11-02",
                         json.loads(version)["rag_api_start_fix_id"])
        self.assertEqual(403,self.request("GET","/",host="evil.example")[0])
        self.assertEqual(403,self.request("POST","/local/draft",{},origin="https://evil.example")[0])
    def test_layout_preview_rejects_unauthenticated_or_fake_media(self):
        self.assertEqual(401,self.request("POST","/local/layout-preview",
                                          b"not a video",token=False)[0])
        from rag_storyboard import KIND_NAMES,KIND_TO_SECTION
        stages=[{"kind":kind,"section":KIND_TO_SECTION[kind],
                 "start":round(i*3/8,3),"end":round((i+1)*3/8,3)}
                for i,kind in enumerate(KIND_NAMES)]
        header=base64.b64encode(json.dumps(stages).encode()).decode()
        status,body=self.request("POST","/local/layout-preview",b"not a real MP4",
                    extra_headers={"X-Swarag-Storyboard":header})
        self.assertEqual(422,status)
        self.assertIn(b"MP4",body)

    @unittest.skipUnless(shutil.which("ffmpeg") and
                         (ROOT/"fonts"/"Inter.ttf").is_file(),
                         "Actual video/fonts required for local preview test")
    def test_local_preview_renders_three_real_source_stills(self):
        with tempfile.TemporaryDirectory() as tmp:
            movie=Path(tmp)/"synthetic.mp4"
            subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
               "-f","lavfi","-i","testsrc2=size=360x640:rate=8:duration=3",
               "-f","lavfi","-i","sine=frequency=400:sample_rate=48000:duration=3",
               "-c:v","libx264","-preset","ultrafast","-pix_fmt","yuv420p",
               "-c:a","aac","-shortest",str(movie)],check=True)
            from rag_storyboard import KIND_NAMES,KIND_TO_SECTION
            stages=[{"kind":kind,"section":KIND_TO_SECTION[kind],
                "start":round(i*3/8,3),"end":round((i+1)*3/8,3)}
                for i,kind in enumerate(KIND_NAMES)]
            header=base64.b64encode(json.dumps(stages).encode()).decode()
            status,body=self.request("POST","/local/layout-preview",movie.read_bytes(),
                        extra_headers={"X-Swarag-Storyboard":header},timeout=180)
            self.assertEqual(200,status,body[:220])
            self.assertTrue(body.startswith(b"\xff\xd8"))
            from PIL import Image
            im=Image.open(io.BytesIO(body))
            self.assertEqual((1080,640),im.size)

    def test_local_runtime_status_is_private_and_redacted(self):
        self.assertEqual(401,self.request("GET","/local/diagnostics",token=False)[0])
        status,blob=self.request("GET","/local/diagnostics")
        self.assertEqual(200,status)
        report=json.loads(blob)
        self.assertEqual(42,report["effect_registry_count"])
        self.assertIn(report["status"],("READY_FOR_PRIVATE_TEST","NEEDS_ATTENTION"))
        self.assertIn("ffmpeg",report["runtime_executables"])
        self.assertIn("selfie_segmenter.tflite",str(report["required_assets_present"]))
        self.assertEqual(42,len(report["effect_names"]))
        self.assertNotIn("Bearer ",blob.decode())
        self.assertNotIn("source.mp4",blob.decode())
        self.assertNotIn("PRIVATE/local-jobs",blob.decode())

    def test_private_diagnostic_refuses_unauthorized_and_malformed_video(self):
        self.assertEqual(401,self.request("POST","/local/effect-diagnostic",
                                          b"not a video",token=False)[0])
        code,data=self.request("POST","/local/effect-diagnostic",b"not a real MP4")
        self.assertEqual(422,code,data)
        self.assertIn(b"MP4",data)
        self.assertEqual(401,self.request("GET","/local/effect-diagnostic/"+"0"*32,
                                          token=False)[0])
        self.assertEqual(404,self.request("GET","/local/effect-diagnostic/"+"0"*32)[0])

    def test_draft_endpoint_requires_token_and_returns_review_not_certification(self):
        body={"duration":50.4,"direction":'slow-push and backdrop-word, text="RAG"',
              "script_filename":"rag.txt",
              "script_b64":base64.b64encode(b"# 0-3 sec | Hook\nA citation can be wrong").decode()}
        self.assertEqual(401,self.request("POST","/local/draft",body,token=False)[0])
        code,data=self.request("POST","/local/draft",body,origin="http://127.0.0.1:8765")
        self.assertEqual(200,code,data[:200])
        parsed=json.loads(data)
        self.assertEqual("DRAFT — NOT SPEECH VERIFIED",parsed["status"])
        self.assertEqual(2,len(parsed["effects"]))


if __name__=="__main__":
    unittest.main()
