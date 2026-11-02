#!/usr/bin/env python3
"""Free localhost-only UI for the authentic Swarag 42-effect renderer.

Host port is loopback-only; Docker listens internally and maps to host localhost.
One-time Docker build prepares FFmpeg/MediaPipe/fonts/models; no external hosted
service or media uploads. Script and effect timing remain human-verified.
"""
import base64
import html
import json
import os
import secrets
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import render_job_api as api
from effect_catalog import read_registry
from local_director import document_text,draft

BUILD_ID="RAG-SIX-SECTION-GUARD-2026-11-02"
RENDER_BUTTON_FIX_ID="RAG-RENDER-BUTTON-FIX-2026-11-02"

PAGE = r'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Swarag / Free Local Video Editor</title>
<style>
*{box-sizing:border-box}body{background:#111f2c;color:#f5f2ec;font-family:system-ui,sans-serif;max-width:930px;margin:35px auto;padding:0 18px}
header{padding:12px 0 24px}h1{margin:0}p{color:#bfccd4;line-height:1.55}
section{background:#1a2f41;padding:20px;border:1px solid #456071;border-radius:12px;margin:18px 0}
label{display:block;margin:12px 0 6px;font-size:14px}
input,select,textarea{background:#132535;border:1px solid #587283;border-radius:6px;color:white;padding:10px;width:100%;font:inherit}
input[type=checkbox]{width:auto}textarea{height:100px}button{background:#2c9a90;color:#071e21;border:0;border-radius:8px;padding:12px 15px;font-weight:700;cursor:pointer;margin:10px 7px 10px 0}
button:disabled{opacity:.45}video{display:block;max-height:400px;max-width:100%;margin:auto}
pre{white-space:pre-wrap;font-size:13px;color:#dcd4ba;background:#0c1b26;padding:14px;border-radius:6px}
.effect{display:grid;grid-template-columns:1.2fr .7fr .7fr 1.5fr auto;gap:8px;padding:8px 0;border-bottom:1px solid #3e5669}
.effect label{font-size:12px}@media(max-width:700px){.effect{grid-template-columns:1fr 1fr}}
.warning{padding:12px;border-left:3px solid #c5a46d;background:#273744}
</style></head><body>
<header><h1>SWARAG / Free Video Director</h1>
<p>Private on-device rendering · Original 42 effects · No monthly hosting</p>
<div class="warning"><b>Editor build:</b> __LOCAL_BUILD_ID__ · <b>UI fix:</b> __RENDER_BUTTON_FIX_ID__ · Six-section RAG explainer detection and incomplete-plan protection enabled. If you do not see this build marker, stop and update your Windows ZIP/Docker image.</div>
<div class="warning">Uses your actual footage and the same FFmpeg/MediaPipe engine. It does not fake subtitles, voice, or statistics. Script-based timings must be checked before export.</div></header>
<section><h2>1. Upload and describe</h2>
<label>Clean original video (.mp4)</label><input type="file" accept=".mp4" id="video">
<label>Script (.txt / .md / .docx)</label><input type="file" accept=".txt,.md,.docx" id="script">
<video id="player" controls playsinline style="display:none"></video>
<label>Editing mode (required)</label>
<select id="editMode"><option value="rag" selected>RAG citation / fictional policy explainer — all six sections REQUIRED</option>
<option value="general">Other video — original Swarag effect catalog</option></select>
<label>What effects do you want?</label><textarea id="direction" placeholder='Example: cinematic slow-push and backdrop-word, text="RAG". Keep natural skin and restrained typography.'></textarea>
<button id="draft">Create edit draft</button></section>
<section id="review" style="display:none"><h2>2. Check timing and titles</h2>
<p>The plan is a draft based on your written time headings, NOT verified speech transcription. Review the actual video and correct timings below.</p>
<pre id="warnings"></pre><div id="effects"></div><button id="add">Add another effect</button>
<div id="ragPanel" style="display:none">
<h3>Six-section script-aware explainer · fictional policy example</h3>
<p>These graphics are separate from the original 42 effects. Check actual word timing against the uploaded video and adjust every start/end point. The three checks are revealed sequentially.</p>
<div id="ragStages"></div>
</div>
<label><input type="checkbox" id="clean"> I confirm this is unedited camera footage, with no burned-in graphics.</label>
<label><input type="checkbox" id="verified"> I checked effect timestamps/text and script words against the actual video audio.</label>
<button id="render" disabled>Render full MP4</button>
<p id="renderReason" role="status" style="color:#e7ca92">Confirm the clean source and exact spoken-word timings to enable rendering.</p></section>
<section id="output" style="display:none"><h2>3. Download</h2><pre id="status"></pre>
<button style="display:none" id="mp4">Download complete MP4</button>
<button style="display:none" id="qa">Download technical QA</button>
<p>Technical PASS is not creative approval. Watch the entire MP4, inspect face/hand masks, typography and speech, and listen to all audio before publishing.</p></section>
<script>
"use strict";
const TOKEN="__LOCAL_BEARER_TOKEN__";
const EFFECTS=__ORIGINAL_EFFECT_NAMES__;
const el=(id)=>document.getElementById(id);
let duration=0,jobId=null;
function status(v){el("output").style.display="block";el("status").textContent=v;}
async function call(path,method="GET",body=null,blob=false){
 const hdr={"Authorization":"Bearer "+TOKEN};
 if(body instanceof Blob)hdr["Content-Type"]="application/octet-stream";
 else if(body!==null){hdr["Content-Type"]="application/json";body=JSON.stringify(body);}
 const response=await fetch(path,{method:method,headers:hdr,body:body,cache:"no-store"});
 if(!response.ok){let err=await response.text();try{err=JSON.parse(err).error||err;}catch(e){}throw Error("HTTP "+response.status+" "+err);}
 return blob?response.blob():response.json();
}
el("video").onchange=async()=>{
 let file=el("video").files[0];if(!file)return;
 let video=el("player");video.src=URL.createObjectURL(file);video.style.display="block";
 await new Promise((ok,fail)=>{video.onloadedmetadata=ok;video.onerror=()=>fail(Error("Video cannot be read"));});
 duration=video.duration;
};
function b64(bytes){let s="";for(let i=0;i<bytes.length;i+=30000)s+=String.fromCharCode(...bytes.subarray(i,i+30000));return btoa(s);}
function field(label,value,type){
 let wrap=document.createElement("label"),inp=document.createElement("input");
 wrap.append(document.createTextNode(label));inp.type=type||"text";inp.value=value===undefined?"":value;
 if(type==="number")inp.step=".01";
 wrap.append(inp);return [wrap,inp];
}
function row(fx){
 let node=document.createElement("div");node.className="effect";
 let sel=document.createElement("select");
 EFFECTS.forEach(name=>{let option=document.createElement("option");option.value=name;option.textContent=name;sel.add(option);});
 sel.value=fx.fx;let name=document.createElement("label");name.textContent="Real 42-effect";name.append(sel);
 let from=field("Start sec",fx.start,"number"),to=field("End sec",fx.end,"number");
 let title=field("On-screen text",fx.text||"");
 let del=document.createElement("button");del.textContent="Remove";del.onclick=()=>{node.remove();check();};
 [name,from[0],to[0],title[0],del].forEach(x=>node.append(x));
 node.data={sel,from:from[1],to:to[1],title:title[1],fx};
 [sel,from[1],to[1],title[1]].forEach(x=>x.oninput=check);
 el("effects").append(node);check();
}
function effects(){
 let result=[];
 for(const n of el("effects").children){
   let d=n.data,x={...d.fx,fx:d.sel.value,start:Number(d.from.value),end:Number(d.to.value)};
   if(d.title.value.trim())x.text=d.title.value.trim();else delete x.text;
   if(["backdrop-word","headline-box","led-sign","reject-stamp","split-headline","headline-wall","pastel-word"].includes(x.fx) && !x.text)
     throw Error("Add verified on-screen text for "+x.fx);
   if(!Number.isFinite(x.start)||!Number.isFinite(x.end)||x.start<0||x.end<=x.start||x.end>duration+.01)throw Error("Invalid effect time window");
   result.push(x);
 }
 if(!result.length)throw Error("Add at least one effect");
 return result;
}
function collectRag(){
 // This must read the DOM, not a missing global JavaScript variable.
 // The prior "ragStages.length" threw ReferenceError; check() swallowed it
 // and permanently disabled Render even after valid user confirmations.
 if(!el("ragStages").children.length)return [];
 const rows=[];
 for(const block of el("ragStages").children){
   const meta=block.stage;
   const a=Number(meta.start.value),b=Number(meta.end.value);
   if(!Number.isFinite(a)||!Number.isFinite(b)||a<0||b<=a+.15||b>duration+.02)
     throw Error("Please fix one RAG graphic time window.");
   rows.push({kind:meta.kind,section:meta.section,start:a,end:b});
 }
 if(rows.length!==8||rows[0].start>.2||duration-rows[7].end>.2||
    rows.some((x,i)=>i>0&&x.start<rows[i-1].end-.0001))
     throw Error("RAG storyboard must cover all six script sections in their proper order.");
 return rows;
}
function createStage(item){
 const block=document.createElement("div");block.className="effect";
 const label=document.createElement("label");label.textContent=item.section+" · "+item.kind;
 const start=field("Start sec",item.start,"number"),end=field("End sec",item.end,"number");
 const note=document.createElement("label");note.textContent="Graphic content is derived from matching script text";
 [label,start[0],end[0],note].forEach(x=>block.append(x));
 block.stage={kind:item.kind,section:item.section,start:start[1],end:end[1]};
 start[1].addEventListener("input",check);end[1].addEventListener("input",check);
 el("ragStages").append(block);
}
function check(){
 let reason="";
 if(!el("clean").checked)reason="Confirm that your video is clean, original camera footage.";
 else if(!el("verified").checked)reason="Check the script/timestamps against the spoken audio, then confirm.";
 try{
   effects();
   const stages=collectRag();
   if(el("editMode").value==="rag"&&stages.length!==8)
     reason="RAG mode requires all eight visual stages. Recreate the edit draft with the complete six-section script.";
 }catch(e){reason=e.message||String(e);}
 el("render").disabled=Boolean(reason);
 el("renderReason").textContent=reason||"Ready to render. Original 42-effect pass and six-section graphics are selected.";
}
["clean","verified","editMode"].forEach(x=>el(x).onchange=check);
el("draft").onclick=async()=>{try{
 if(!duration||!el("video").files[0]||!el("script").files[0])throw Error("Select an MP4 and matching script first");
 let sc=el("script").files[0];
 let result=await call("/local/draft","POST",{duration:duration,direction:el("direction").value,
   script_filename:sc.name,script_b64:b64(new Uint8Array(await sc.arrayBuffer()))});
 el("review").style.display="block";el("effects").replaceChildren();
 if(el("editMode").value==="rag" && (result.rag_storyboard||[]).length!==8)
   throw Error("Six-section RAG mode requires all eight graphic stages. Upload the full six-part citation/policy script, not an excerpt. Rendering is blocked.");
 result.effects.forEach(row);el("warnings").textContent=result.warnings.join("\n");
 el("ragStages").replaceChildren();
 (result.rag_storyboard||[]).forEach(createStage);
 el("ragPanel").style.display=(result.rag_storyboard||[]).length?"block":"none";
 el("clean").checked=false;el("verified").checked=false;check();
 }catch(e){status(e.message);}};
el("add").onclick=()=>row({fx:"slow-push",start:Math.min(3,duration*.2),
 end:Math.min(duration,Math.min(3,duration*.2)+2),zoom:1.05,blur:0});
async function download(path,name){let data=await call("/v1/jobs/"+jobId+"/"+path,"GET",null,true);
 let url=URL.createObjectURL(data),a=document.createElement("a");a.href=url;a.download=name;a.click();
 setTimeout(()=>URL.revokeObjectURL(url),30000);}
el("mp4").onclick=()=>download("master","swarag_master.mp4").catch(e=>status(e.message));
el("qa").onclick=()=>download("qa","swarag_qa.json").catch(e=>status(e.message));
el("render").onclick=async()=>{
 el("render").disabled=true;try{
 status("Creating verified local render job...");
 let plannedRag=collectRag();
 if(el("editMode").value==="rag" && plannedRag.length!==8)
   throw Error("RAG Reel render blocked: all six sections and eight graphic stages must be present.");
 let created=await call("/v1/jobs","POST",{
  effects:effects(),requires_transcript:true,transcript_verified:true,source_clean_confirmed:true,
  rag_storyboard:plannedRag,requires_six_section_explainer:el("editMode").value==="rag" || plannedRag.length>0,
  video_mode:el("editMode").value,source_duration:duration,script_filename:el("script").files[0].name
 });
 jobId=created.id;
 status("Copying your MP4 and script to the local rendering workspace...");
 await call("/v1/jobs/"+jobId+"/video","PUT",el("video").files[0]);
 await call("/v1/jobs/"+jobId+"/script","PUT",el("script").files[0]);
 await call("/v1/jobs/"+jobId+"/start","POST",{});
 status("Swarag 42-effect renderer is working. Keep this window open.");
 while(true){await new Promise(done=>setTimeout(done,2500));
 let state=await call("/v1/jobs/"+jobId);
 if(state.status==="RUNNING")continue;
 if(state.status!=="REVIEW_REQUIRED")throw Error(state.error||state.status);
 break;}
 status("Technical MP4 PASS. Review the complete result before publishing.");
 el("mp4").style.display="inline-block";el("qa").style.display="inline-block";
 }catch(e){status("Not completed: "+e.message);}finally{check();}
};
</script></body></html>'''

class LocalHandler(api.Handler):
    def local_request(self):
        port=int(os.getenv("PORT","8765"))
        hosts={"localhost:"+str(port),"127.0.0.1:"+str(port)}
        origin=self.headers.get("Origin")
        if self.headers.get("Host") not in hosts or (
            origin and origin not in {"http://"+h for h in hosts}
        ):
            self.answer(403,{"error":"Localhost-only editor; external requests rejected"})
            return False
        return True
    def do_GET(self):
        if not self.local_request():return
        if urlsplit(self.path).path=="/local/version":
            self.answer(200,{"build_id":BUILD_ID,
                             "rag_six_section_guard":True,
                             "render_button_fixed":True,
                             "render_button_fix_id":RENDER_BUTTON_FIX_ID,
                             "original_effect_catalog":len(read_registry()[0])})
            return
        if urlsplit(self.path).path=="/":
            data=PAGE.replace("__LOCAL_BEARER_TOKEN__",html.escape(api.TOKEN,quote=True))
            data=data.replace("__LOCAL_BUILD_ID__",BUILD_ID)
            data=data.replace("__RENDER_BUTTON_FIX_ID__",RENDER_BUTTON_FIX_ID)
            data=data.replace("__ORIGINAL_EFFECT_NAMES__",json.dumps(sorted(read_registry()[0])))
            blob=data.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Security-Policy","default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; media-src blob:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
            self.send_header("Cache-Control","no-store")
            self.send_header("X-Content-Type-Options","nosniff")
            self.send_header("Content-Length",str(len(blob)))
            self.end_headers();self.wfile.write(blob);return
        super().do_GET()
    def do_POST(self):
        if not self.local_request():return
        if urlsplit(self.path).path=="/local/draft":
            if not self.authorized():return
            try:
                n=self.body(3*1024*1024)
                body=self.rfile.read(n)
                if len(body)!=n:raise ValueError("Incomplete script upload")
                payload=json.loads(body)
                content=base64.b64decode(payload["script_b64"],validate=True)
                script=document_text(payload["script_filename"],content)
                result=draft(payload.get("direction",""),script,float(payload["duration"]))
                self.answer(200,result)
            except Exception as exc:
                self.answer(422,{"error":str(exc)[:180]})
            return
        super().do_POST()
    def do_PUT(self):
        if self.local_request():super().do_PUT()
    def do_DELETE(self):
        if self.local_request():super().do_DELETE()

def main():
    import webbrowser
    api.TOKEN=secrets.token_urlsafe(48)
    api.JOB_DIR=Path(os.getenv("SWARAG_JOB_DIR",str(ROOT/"PRIVATE"/"local-jobs"))).resolve()
    api.JOB_DIR.mkdir(parents=True,exist_ok=True)
    api.erase_old_jobs()
    import threading
    import time
    def purge_expired_local_jobs():
        while True:
            time.sleep(3600)
            with api.LIVE:
                api.erase_old_jobs()
    threading.Thread(target=purge_expired_local_jobs,daemon=True).start()
    port=int(os.getenv("PORT","8765"))
    bind="0.0.0.0" if os.getenv("SWARAG_LOCAL_DOCKER")=="1" else "127.0.0.1"
    print("Swarag Free Local Editor: http://127.0.0.1:"+str(port),flush=True)
    if bind=="127.0.0.1":webbrowser.open("http://127.0.0.1:"+str(port))
    with api.ThreadingHTTPServer((bind,port),LocalHandler) as srv:srv.serve_forever()

if __name__=="__main__":main()
