#!/usr/bin/env python3
"""Free localhost-only UI for the authentic Swarag 42-effect renderer.

Host port is loopback-only; Docker listens internally and maps to host localhost.
One-time Docker build prepares FFmpeg/MediaPipe/fonts/models; no external hosted
service or media uploads. Script and effect timing remain human-verified.
"""
import base64
import binascii
import html
import json
import os
import secrets
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import render_job_api as api
from effect_catalog import read_registry
from local_director import document_text,draft
from rag_glass_preview import preview_contact_sheet,LAYOUT_ID
import local_effect_health_service as effect_health
from local_runtime_health import runtime_diagnostics

BUILD_ID="RAG-SIX-SECTION-GUARD-2026-11-02"
RENDER_BUTTON_FIX_ID="RAG-RENDER-BUTTON-FIX-2026-11-02"
API_START_FIX_ID="RAG-API-START-FIX-2026-11-02"
GLASS_LEGIBILITY_FIX_ID="GLASS-MOBILE-LEGIBILITY-2026-11-03"
EFFECT_QA_BUILD_ID="ORIGINAL-42-EFFECT-QA-2026-11-03"
MOTION_REVIEW_BUILD_ID="ORIGINAL-42-MOTION-REVIEW-2026-11-03"

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
<div class="warning"><b>Editor build:</b> __LOCAL_BUILD_ID__ · <b>UI fix:</b> __RENDER_BUTTON_FIX_ID__ · <b>API fix:</b> __API_START_FIX_ID__ · <b>Creative layout:</b> __FACE_SAFE_LAYOUT_ID__ · <b>Typography:</b> __GLASS_LEGIBILITY_FIX_ID__ · <b>42-effect QA:</b> __EFFECT_QA_BUILD_ID__ · <b>Motion review:</b> __MOTION_REVIEW_BUILD_ID__ · Six-section RAG explainer detection and incomplete-plan protection enabled. If you do not see this build marker, stop and update your Windows ZIP/Docker image.</div>
<div class="warning">Uses your actual footage and the same FFmpeg/MediaPipe engine. It does not fake subtitles, voice, or statistics. Script-based timings must be checked before export.</div></header>
<section><h2>1. Upload and describe</h2>
<label>Clean original video (.mp4)</label><input type="file" accept=".mp4" id="video">
<div class="warning" style="margin-top:12px">
<h3>Check all 42 original effects — before another full render</h3>
<p>Optional private diagnostic. Tests all 42 effects and five named looks on a short sample of your ACTUAL selected camera video. Reports decode errors, missing audio/frames, observable visual changes, and a 3-frame motion review of each effect. The full 47 short MP4 clips can be played individually. This is not a finished MP4 or artistic certification. No footage goes to GitHub or a hosted service.</p>
<button id="checkEngine" type="button">Check my local 42-effect engine first (no rendering)</button>
<pre id="engineHealth" aria-live="polite" style="display:none"></pre>
<button id="check42" type="button">Test all 42 effects on my camera footage</button>
<pre id="check42Status" aria-live="polite" style="display:none"></pre>
<img id="check42Sheet" alt="Private 42-effect preview contact sheet from your actual original camera video" style="width:100%;height:auto;display:none;border:1px solid #587283;border-radius:8px">
<button id="download42" style="display:none" type="button">Download effect-by-effect diagnostic JSON</button>
<button id="download42Motion" style="display:none" type="button">Download all 47 playable effect previews (ZIP)</button>
<img id="check42MotionSheet" alt="Three sequential frames from each actual original-effect motion clip" style="width:100%;height:auto;display:none;border:1px solid #587283;border-radius:8px">
</div>
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
<p>Eight stages use the ORIGINAL glass-widgets effect with per-frame MediaPipe subject-depth masking, not a flat overlay. Check timings against real speech; each verification question appears separately.</p>
<div id="ragStages"></div>
</div>
<div id="layoutReview" style="display:none">
<h3>Original glass-widgets effect — real video preview</h3>
<p>Three frames are rendered by the REAL fx.py/MediaPipe engine: policy evidence, RAG retrieval and access check. Glass floats BEHIND your silhouette on full-frame source footage. This is not a completed video or creative approval.</p>
<button id="preview" type="button">Render 3 genuine glass-widget preview frames</button>
<img id="previewImage" alt="Three actual depth-masked glass-widget RAG frames" style="display:none;width:100%;height:auto;border:1px solid #587283;border-radius:8px">
<label><input type="checkbox" id="layoutApproved" disabled> I inspected the genuine glass-widget frames; the design is professional and does NOT obscure my face.</label>
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
let duration=0,jobId=null,previewReady=false,healthJobId=null;
function status(v){el("output").style.display="block";el("status").textContent=v;}
async function call(path,method="GET",body=null,blob=false,extraHeaders={}){
 const hdr={"Authorization":"Bearer "+TOKEN,...extraHeaders};
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
 start[1].addEventListener("input",()=>{invalidatePreview();check();});
 end[1].addEventListener("input",()=>{invalidatePreview();check();});
 el("ragStages").append(block);
}
function invalidatePreview(){
 previewReady=false;
 el("layoutApproved").checked=false;
 el("layoutApproved").disabled=true;
 el("previewImage").style.display="none";
}
function check(){
 let reason="";
 if(!el("clean").checked)reason="Confirm that your video is clean, original camera footage.";
 else if(!el("verified").checked)reason="Check the script/timestamps against the spoken audio, then confirm.";
 else if(el("editMode").value==="rag"&&(!previewReady||!el("layoutApproved").checked))
   reason="Render and inspect the three authentic glass-widget frames before full video production.";
 try{
   effects();
   const stages=collectRag();
   if(el("editMode").value==="rag"&&stages.length!==8)
     reason="RAG mode requires all eight visual stages. Recreate the edit draft with the complete six-section script.";
 }catch(e){reason=e.message||String(e);}
 el("render").disabled=Boolean(reason);
 el("renderReason").textContent=reason||"Ready to render. Original 42-effect pass and six-section graphics are selected.";
}
["clean","verified","layoutApproved"].forEach(x=>el(x).onchange=check);
el("editMode").onchange=()=>{invalidatePreview();check();};
el("script").addEventListener("change",()=>{invalidatePreview();check();});
el("video").addEventListener("change",()=>{
 previewReady=false;
 el("layoutApproved").checked=false;
 el("layoutApproved").disabled=true;
 el("previewImage").style.display="none";
 check();
});
el("checkEngine").onclick=async()=>{
 const output=el("engineHealth");output.style.display="block";
 try{
  const data=await call("/local/diagnostics");
  output.textContent="Renderer: "+data.status+"; original effects: "+data.effect_registry_count+"/42\\n"+
    "Dependencies: "+JSON.stringify(data.python_dependencies_installed)+"\\n"+
    "FFmpeg/ffprobe: "+JSON.stringify(data.runtime_executables)+"\\n"+
    "Model/fonts: "+JSON.stringify(data.required_assets_present)+"\\n"+
    "Private workspace free MB: "+data.private_workspace_free_mb+
    "; container memory limit MB: "+(data.docker_container_memory_limit_mb??"not set")+
    "\\nIssues: "+(data.issues.length?data.issues.join("; "):"none detected")+
    "\\nRuntime READY does not certify visual quality.";
 }catch(err){output.textContent="Cannot verify local renderer: "+String(err?.message||err);}
};
el("check42").onclick=async()=>{
 const button=el("check42"),file=el("video").files[0];
 if(!file){el("check42Status").style.display="block";el("check42Status").textContent="Select your clean original MP4 above first.";return;}
 button.disabled=true;
 const output=el("check42Status");output.style.display="block";
 output.textContent="Uploading a private camera sample for the original 42-effect diagnostic...";
 el("check42Sheet").style.display="none";el("download42").style.display="none";
 el("check42MotionSheet").style.display="none";el("download42Motion").style.display="none";
 try{
   const started=await call("/local/effect-diagnostic","POST",file);
   healthJobId=started.id;
   while(true){
     await new Promise(done=>setTimeout(done,3500));
     const state=await call("/local/effect-diagnostic/"+healthJobId);
     output.textContent="Real-camera effect checks: "+state.effect_checks_completed+"/47 (42 original + 5 named looks). Status: "+state.status+"\\n"+
        "Tech PASS does not prove professional look or mask safety.";
     if(state.status==="RUNNING")continue;
     if(state.technical_status){
       output.textContent+="\\n"+state.technical_status+"; original effects passed "+state.technically_passed_effects+"/42."+
          "\\nCreative status: "+state.creative_status;
       el("download42").style.display="inline-block";
       output.textContent+="\nMotion evidence: "+(state.motion_review_status||"not ready")+
          "; playable clips: "+(state.motion_clips_packaged||0)+"/47.";
       if(state.motion_review_status==="MOTION_SAMPLES_AVAILABLE"){
         el("download42Motion").style.display="inline-block";
         try{
           const motionSheet=await call("/local/effect-diagnostic/"+healthJobId+"/motion-sheet","GET",null,true);
           const motionImage=el("check42MotionSheet");
           if(motionImage.src?.startsWith("blob:"))URL.revokeObjectURL(motionImage.src);
           motionImage.src=URL.createObjectURL(motionSheet);
           motionImage.style.display="block";
         }catch(err){output.textContent+="\nMotion review sheet unavailable: "+String(err?.message||err);}
       }
       // Show evidence even when some tests fail: failed/missing slots
       // are explicitly labeled in the private contact sheet.
       try{
         const jpg=await call("/local/effect-diagnostic/"+healthJobId+"/contact-sheet","GET",null,true);
         const image=el("check42Sheet");
         if(image.src?.startsWith("blob:"))URL.revokeObjectURL(image.src);
         image.src=URL.createObjectURL(jpg);
         image.style.display="block";
       }catch(previewError){
         output.textContent+="\\nReview sheet unavailable: "+String(previewError?.message||previewError);
       }
     }else if(state.error)output.textContent+="\\n"+state.error;
     break;
   }
 }catch(err){
   output.textContent="Diagnostic could not be verified: "+String(err?.message||err)+
     "\\nIf Docker stopped, inspect Docker Desktop > Containers > swarag-local-editor > Logs. No 42/42 result was certified.";
 }finally{button.disabled=false;}
};
el("download42").onclick=async()=>{
 if(!healthJobId)return;
 try{
 const data=await call("/local/effect-diagnostic/"+healthJobId+"/report","GET",null,true);
 const url=URL.createObjectURL(data),a=document.createElement("a");
 a.href=url;a.download="Swarag_42_Effect_Health_Report.json";a.click();
 setTimeout(()=>URL.revokeObjectURL(url),30000);
 }catch(err){el("check42Status").textContent=String(err?.message||err);}
};
el("download42Motion").onclick=async()=>{
 if(!healthJobId)return;
 try{
   const data=await call("/local/effect-diagnostic/"+healthJobId+"/motion-clips","GET",null,true);
   const url=URL.createObjectURL(data),a=document.createElement("a");
   a.href=url;a.download="Swarag_47_Motion_Clips.zip";a.click();
   setTimeout(()=>URL.revokeObjectURL(url),30000);
 }catch(err){el("check42Status").textContent=String(err?.message||err);}
};
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
 el("layoutReview").style.display=(result.rag_storyboard||[]).length?"block":"none";
 previewReady=false;
 el("layoutApproved").checked=false;
 el("layoutApproved").disabled=true;
 el("previewImage").style.display="none";
 el("clean").checked=false;el("verified").checked=false;check();
 }catch(e){status(e.message);}};
el("add").onclick=()=>row({fx:"slow-push",start:Math.min(3,duration*.2),
 end:Math.min(duration,Math.min(3,duration*.2)+2),zoom:1.05,blur:0});
el("preview").onclick=async()=>{
 const button=el("preview");button.disabled=true;
 previewReady=false;
 el("layoutApproved").checked=false;
 el("layoutApproved").disabled=true;check();
 status("Generating three local real-footage composition previews (no full render)...");
 try{
  const stages=collectRag();
  if(stages.length!==8)throw Error("All eight script-backed RAG stages are required for original glass preview.");
  const picture=await call("/local/layout-preview","POST",el("video").files[0],true,
    {"X-Swarag-Storyboard":btoa(JSON.stringify(stages))});
  const image=el("previewImage");
  if(image.src&&image.src.startsWith("blob:"))URL.revokeObjectURL(image.src);
  image.src=URL.createObjectURL(picture);
  image.style.display="block";
  previewReady=true;
  el("layoutApproved").disabled=false;
  status("Real Swarag glass-widgets preview ready. Inspect readability, subtle motion direction and whether the original person remains in front. Reject if the design feels wrong.");
 }catch(e){status("Layout preview failed: "+String(e?.message||e));}
 finally{button.disabled=false;check();}
};
async function download(path,name){let data=await call("/v1/jobs/"+jobId+"/"+path,"GET",null,true);
 let url=URL.createObjectURL(data),a=document.createElement("a");a.href=url;a.download=name;a.click();
 setTimeout(()=>URL.revokeObjectURL(url),30000);}
el("mp4").onclick=()=>download("master","swarag_master.mp4").catch(e=>status(e.message));
el("qa").onclick=()=>download("qa","swarag_qa.json").catch(e=>status(e.message));
el("render").onclick=async()=>{
 el("render").disabled=true;
 let phase="creating the job";
 try{
 status("Creating verified local render job...");
 let plannedRag=collectRag();
 if(el("editMode").value==="rag" && plannedRag.length!==8)
   throw Error("RAG Reel render blocked: all six sections and eight graphic stages must be present.");
 if(el("editMode").value==="rag" && (!previewReady||!el("layoutApproved").checked))
   throw Error("RAG Reel render blocked: generate, inspect and approve the actual face-safe layout preview.");
 let created=await call("/v1/jobs","POST",{
  effects:effects(),requires_transcript:true,transcript_verified:true,source_clean_confirmed:true,
  rag_storyboard:plannedRag,requires_six_section_explainer:el("editMode").value==="rag" || plannedRag.length>0,
  video_mode:el("editMode").value,source_duration:duration,script_filename:el("script").files[0].name
 });
 jobId=created.id;
 phase="uploading the original MP4";
 status("Copying your MP4 privately to the local rendering workspace...");
 await call("/v1/jobs/"+jobId+"/video","PUT",el("video").files[0]);
 phase="uploading the script";
 status("Copying your script privately to the local rendering workspace...");
 await call("/v1/jobs/"+jobId+"/script","PUT",el("script").files[0]);
 phase="starting the RAG render";
 status("Validating the six-section edit plan and starting the original renderer...");
 await call("/v1/jobs/"+jobId+"/start","POST",{});
 phase="checking render progress";
 status("Swarag 42-effect renderer is working. Keep this window open.");
 while(true){await new Promise(done=>setTimeout(done,2500));
 let state=await call("/v1/jobs/"+jobId);
 if(state.status==="RUNNING")continue;
 if(state.status!=="REVIEW_REQUIRED")throw Error(state.error||state.status);
 break;}
 status("Technical MP4 PASS. Review the complete result before publishing.");
 el("mp4").style.display="inline-block";el("qa").style.display="inline-block";
 }catch(e){
   const message=String(e?.message||e);
   if(/Failed to fetch|NetworkError|Load failed/i.test(message)){
     status("Local editor connection was lost while "+phase+".\n"+
       "The video MAY still be processing; do not launch another render blindly.\n"+
       "Open http://127.0.0.1:8765/local/version on this PC.\n"+
       "If it does not open: check Docker Desktop > Containers > swarag-local-editor "+
       "for stopped/exited/OOM status and read the Logs.\n"+
       "If it does open: keep this container running and check the job folder "+
       "under PRIVATE\\jobs for state.json / render.log.\n"+
       "The original footage stays private on your machine. No MP4 is certified yet.");
   }else status("Render was not confirmed at stage '"+phase+"': "+message);
 }finally{check();}
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
        if urlsplit(self.path).path.startswith("/local/effect-diagnostic/"):
            effect_health.get(self,urlsplit(self.path).path)
            return
        if urlsplit(self.path).path=="/local/diagnostics":
            if not self.authorized():return
            self.answer(200,runtime_diagnostics())
            return
        if urlsplit(self.path).path=="/local/version":
            self.answer(200,{"build_id":BUILD_ID,
                             "rag_six_section_guard":True,
                             "render_button_fixed":True,
                             "render_button_fix_id":RENDER_BUTTON_FIX_ID,
                             "rag_api_start_fixed":True,
                             "rag_api_start_fix_id":API_START_FIX_ID,
                             "face_safe_layout_id":LAYOUT_ID,
                             "glass_legibility_fix_id":GLASS_LEGIBILITY_FIX_ID,
                             "layout_preview_required":True,
                             "original_effect_catalog":len(read_registry()[0]),
                             "private_real_camera_42_effect_diagnostic":True,
                             "effect_qa_build_id":EFFECT_QA_BUILD_ID})
            return
        if urlsplit(self.path).path=="/":
            data=PAGE.replace("__LOCAL_BEARER_TOKEN__",html.escape(api.TOKEN,quote=True))
            data=data.replace("__LOCAL_BUILD_ID__",BUILD_ID)
            data=data.replace("__RENDER_BUTTON_FIX_ID__",RENDER_BUTTON_FIX_ID)
            data=data.replace("__API_START_FIX_ID__",API_START_FIX_ID)
            data=data.replace("__FACE_SAFE_LAYOUT_ID__",LAYOUT_ID)
            data=data.replace("__GLASS_LEGIBILITY_FIX_ID__",GLASS_LEGIBILITY_FIX_ID)
            data=data.replace("__EFFECT_QA_BUILD_ID__",EFFECT_QA_BUILD_ID)
        data=data.replace("__MOTION_REVIEW_BUILD_ID__",MOTION_REVIEW_BUILD_ID)
            data=data.replace("__ORIGINAL_EFFECT_NAMES__",json.dumps(sorted(read_registry()[0])))
            blob=data.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Security-Policy","default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src blob:; media-src blob:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
            self.send_header("Cache-Control","no-store")
            self.send_header("X-Content-Type-Options","nosniff")
            self.send_header("Content-Length",str(len(blob)))
            self.end_headers();self.wfile.write(blob);return
        super().do_GET()
    def do_POST(self):
        if not self.local_request():return
        if urlsplit(self.path).path=="/local/effect-diagnostic":
            effect_health.begin(self)
            return
        if urlsplit(self.path).path=="/local/layout-preview":
            if not self.authorized():return
            import io
            import tempfile
            try:
                n=self.body(api.MAX_UPLOAD)
                with tempfile.TemporaryDirectory(prefix="swarag_private_layout_") as d:
                    source=Path(d)/"preview_source.mp4"
                    with source.open("wb") as file:
                        remaining=n
                        while remaining:
                            chunk=self.rfile.read(min(1024*1024,remaining))
                            if not chunk:raise ValueError("Incomplete local preview upload")
                            file.write(chunk);remaining-=len(chunk)
                    with source.open("rb") as file:header=file.read(12)
                    if len(header)<12 or header[4:8]!=b"ftyp":
                        raise ValueError("Preview requires original MP4 bytes")
                    header_data=self.headers.get("X-Swarag-Storyboard","")
                    if not (40<len(header_data)<8000):
                        raise ValueError("Eight edited RAG stages must be supplied for true-effect preview")
                    stages=json.loads(base64.b64decode(header_data,validate=True).decode("utf-8"))
                    image,report=preview_contact_sheet(source,stages)
                    data=io.BytesIO()
                    image.save(data,format="JPEG",quality=86)
                    content=data.getvalue()
                self.send_response(200)
                self.send_header("Content-Type","image/jpeg")
                self.send_header("Cache-Control","private, no-store")
                self.send_header("X-Content-Type-Options","nosniff")
                self.send_header("Content-Length",str(len(content)))
                self.end_headers();self.wfile.write(content)
            except (ValueError,OSError,RuntimeError,ImportError,binascii.Error,
                    subprocess.SubprocessError) as exc:
                self.answer(422,{"error":"Local glass-widget preview failed: "+str(exc)[:180]})
            return
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
    # Docker restarts must not leave private jobs permanently RUNNING:
    # that would also prevent the 24-hour local cleanup policy.
    import time
    for folder in api.JOB_DIR.iterdir():
        if not folder.is_dir() or not api.ID_RE.fullmatch(folder.name):continue
        try:
            state=api.metadata(folder.name)
            if state.get("status")=="RUNNING":
                state["status"]="INTERRUPTED"
                state["finished_at"]=time.time()
                state["error"]="The previous local Docker session stopped during rendering or diagnostics; no output was certified."
                api.save(folder.name,state)
        except (OSError,ValueError,KeyError):continue
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
