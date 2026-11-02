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
        result=d.draft('Subtle slow-push and backdrop-word, text="RAG"',script,50.4)
        self.assertEqual(42,result["effect_catalog_size"])
        self.assertEqual({"slow-push","backdrop-word"},{x["fx"] for x in result["effects"]})
        self.assertTrue(any("scaled proportionally" in w for w in result["warnings"]))
        self.assertEqual("RAG",next(x for x in result["effects"] if x["fx"]=="backdrop-word")["text"])
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

    def test_txt_and_docx_scripts(self):
        self.assertEqual("RAG explained",d.document_text("script.txt",b"RAG explained"))
        out=io.BytesIO()
        with zipfile.ZipFile(out,"w") as z:
            z.writestr("word/document.xml",
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                '<w:body><w:p><w:r><w:t>Correct script</w:t></w:r></w:p></w:body></w:document>')
        self.assertEqual("Correct script",d.document_text("script.docx",out.getvalue()))
        with self.assertRaises(ValueError):d.document_text("script.pdf",b"%PDF-1.7")


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
    def request(self,method,path,body=None,host="127.0.0.1:8765",origin=None,token=True):
        c=http.client.HTTPConnection("127.0.0.1",self.server.server_port,timeout=5)
        hdr={"Host":host,"Content-Type":"application/json"}
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
        code,version=self.request("GET","/local/version",token=False)
        self.assertEqual(200,code)
        self.assertTrue(json.loads(version)["rag_six_section_guard"])
        self.assertEqual(403,self.request("GET","/",host="evil.example")[0])
        self.assertEqual(403,self.request("POST","/local/draft",{},origin="https://evil.example")[0])
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
