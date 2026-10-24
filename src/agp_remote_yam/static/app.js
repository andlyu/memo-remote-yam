"use strict";
const $ = id => document.getElementById(id);
let config, selected = null, cursor = -1, rows = [], polling = false, fileListKey = "", terminalHistoryKey = "";
const terminal = new Set(["stopped", "timed_out", "failed", "disconnected", "safety_aborted", "interrupted", "resetting"]);
async function api(path, value) {
  const response = await fetch(path, value === undefined ? {} : {method:"POST", headers:{"Content-Type":"application/json", "X-CSRF-Token":config.csrf}, body:JSON.stringify(value)});
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || "Request failed");
  return result;
}
function error(message) { $("error").textContent = message || ""; $("error").hidden = !message; }
function clearRun(id) { selected=id; cursor=-1; rows=[]; fileListKey=""; terminalHistoryKey=""; $("events").replaceChildren(); $("outcome").hidden=true; $("code").hidden=true; }
function eventRow(event) {
  const node = document.createElement("article"); node.className="event " + (event.kind==="error"?"error":"");
  const label=document.createElement("div");label.className="event-label";label.textContent=event.kind.replaceAll("_"," ").toUpperCase();
  const text=document.createElement("p");text.textContent=event.message;node.append(label,text);
  if (event.arguments || event.response || event.result) { const details=document.createElement("details"), summary=document.createElement("summary"), pre=document.createElement("pre");summary.textContent="Inspect details";pre.textContent=JSON.stringify(event.arguments||event.response||event.result,null,2);details.append(summary,pre);node.append(details); }
  return node;
}
function fileURL(name) { return "/api/runs/"+selected+"/files/"+name.split("/").map(encodeURIComponent).join("/"); }
function renderFiles(names) {
  const key=selected+JSON.stringify(names);if(key===fileListKey)return;fileListKey=key;
  $("file-count").textContent=names.length+" files";
  const fragment=document.createDocumentFragment();
  for (const name of names) { const button=document.createElement("button");button.className="file";button.textContent=name;button.type="button";button.onclick=async()=>{if(/\.(py|md|json)$/.test(name)){const response=await fetch(fileURL(name));if(!response.ok){error("Cannot read workspace file");return;}$("code").textContent=await response.text();$("code").hidden=false;}else window.open(fileURL(name),"_blank","noopener");};fragment.append(button); }
  $("files").replaceChildren(fragment);
}
async function history() {
  const result=await api("/api/runs"); const old=$("experience").value;
  $("history").replaceChildren();$("experience").replaceChildren(new Option("Fresh start",""));
  for (const run of result.runs) { const button=document.createElement("button");button.className="history-item";const title=document.createElement("strong"),meta=document.createElement("small");title.textContent=run.task;meta.textContent=run.status+" · "+new Date(run.created_at*1000).toLocaleString();button.append(title,meta);button.onclick=()=>{clearRun(run.id);poll();};$("history").append(button);if(terminal.has(run.status))$("experience").add(new Option(run.task.slice(0,35),run.id)); }
  if ([...$("experience").options].some(x=>x.value===old))$("experience").value=old;
}
async function poll() {
  if (!selected || polling) return; polling=true;
  try {
    const identity=selected, run=await api("/api/runs/"+identity+"?after="+cursor);
    if(identity!==selected)return;
    $("phase").textContent=run.status.replaceAll("_"," ");$("run-title").textContent=run.task;
    const finished=terminal.has(run.status);$("run").disabled=!finished;$("stop").disabled=finished;
    const nearBottom=$("events").scrollTop+$("events").clientHeight>=$("events").scrollHeight-60;
    for(const event of run.events){rows.push(event);$("events").append(eventRow(event));cursor=event.id;}
    if(nearBottom)$("events").scrollTop=$("events").scrollHeight;
    $("event-count").textContent=rows.length+" events";renderFiles(run.files);
    if(run.error)error(run.error);
    if(run.outcome){$("outcome").replaceChildren();const message=document.createElement("div"),scope=document.createElement("small");message.textContent=run.outcome.summary;scope.textContent=config.mode==="offline_mock"?(config.agent==="scripted"?"Mock transport verification only. No model inference or physical robot.":"Real model, mock robot. No physical task validation."):"Agent-declared outcome. Review captures and evidence before judging task success.";$("outcome").append(message,scope);$("outcome").hidden=false;}
    const historyKey=selected+run.status;if(finished&&terminalHistoryKey!==historyKey){terminalHistoryKey=historyKey;await history();}
  } catch(exc){error(exc.message);}finally{polling=false;}
}
$("task-form").addEventListener("submit",async event=>{
  event.preventDefault();error("");$("run").disabled=true;
  try{let goal=null;const file=$("goal").files[0];if(file)goal=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.onerror=reject;reader.readAsDataURL(file);});
    const run=await api("/api/runs",{task:$("task").value,duration_s:Number($("duration").value),experience_run:$("experience").value||null,goal_image:goal});clearRun(run.id);await history();await poll();
  }catch(exc){error(exc.message);$("run").disabled=false;}
});
$("stop").onclick=async()=>{if(!selected)return;$("stop").disabled=true;try{await api("/api/runs/"+selected+"/stop",{});await poll();}catch(exc){error(exc.message);}};
$("refresh").onclick=()=>history().catch(exc=>error(exc.message));
$("goal").onchange=()=>{const file=$("goal").files[0];$("goal-preview").hidden=!file;if(file)$("goal-preview").src=URL.createObjectURL(file);};
for(const role of ["top","left","right"]){const image=$("camera-"+role);image.onerror=()=>{image.hidden=true;image.parentElement.querySelector("figcaption").hidden=false;};image.onload=()=>{image.hidden=false;image.parentElement.querySelector("figcaption").hidden=true;};}
async function init(){try{config=await api("/api/config");$("mode").textContent=config.mode==="offline_mock"?"Offline mock":"Physical robot · API";$("mode").classList.toggle("mock",config.mode==="offline_mock");$("robot").textContent=config.robot_id;$("model").textContent=config.agent==="scripted"?"Scripted agent · no model usage":config.model+" · Agent as Policy";if(config.mode==="offline_mock")$("task").value="Demonstrate the offline agent → API controller loop.";await history();setInterval(poll,800);setInterval(()=>{for(const role of ["top","left","right"])$("camera-"+role).src="/api/cameras/"+role+".jpg?t="+Date.now();},4000);}catch(exc){error(exc.message);}}
init();
