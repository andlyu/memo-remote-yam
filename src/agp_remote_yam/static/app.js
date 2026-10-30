"use strict";
const $ = id => document.getElementById(id);
let stopCameras=null;
let config, activeRun = null, selected = null, cursor = -1, rows = [], polling = false, fileListKey = "", terminalHistoryKey = "";
const terminal = new Set(["completed", "succeeded", "stopped", "timed_out", "failed", "disconnected", "safety_aborted", "interrupted", "resetting"]);
async function api(path, value) {
  const response = await fetch(path, value === undefined ? {} : {method:"POST", headers:{"Content-Type":"application/json", "X-CSRF-Token":config.csrf}, body:JSON.stringify(value)});
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || "Request failed");
  return result;
}
function error(message) { $("error").textContent = message || ""; $("error").hidden = !message; }
function displayStatus(run){return run.error?"Failed":terminal.has(run.status)&&!run.active&&run.outcome?.status==="done"?"Agent finished":run.status.replaceAll("_"," ");}
function timingLabel(run){
 if(run.mode==="offline_mock")return "Mock robot · no physical execution";
 const timing=run.timing||{};
 if(timing.run_to_motion_s!=null)return "Measured movement completed "+timing.run_to_motion_s.toFixed(1)+" s after Run. Visual onset timing is unverified.";
 if(terminal.has(run.status)&&!run.active)return "Ended with no verified method-driven movement.";
 const elapsed=Math.max(0,Date.now()/1000-(timing.run_clicked_at||run.created_at));
 return "Waiting for measured method-driven movement · "+Math.floor(elapsed)+" s since Run. Queue and agent work appear below.";
}
function clearRun(id) { selected=id; cursor=-1; rows=[]; fileListKey=""; terminalHistoryKey=""; $("events").replaceChildren(); $("outcome").hidden=true; $("code").hidden=true; $("replay-panel").hidden=true; $("run-replay").pause(); $("run-replay").removeAttribute("src"); delete $("run-replay").dataset.run; error(""); }
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
  const result=await api("/api/runs"); activeRun=result.runs.find(x=>x.active||!terminal.has(x.status))?.id||null; const old=$("experience").value;
  $("history").replaceChildren();$("experience").replaceChildren(new Option("Fresh start",""));
  for (const run of result.runs) { const button=document.createElement("button");button.className="history-item";const title=document.createElement("strong"),meta=document.createElement("small");title.textContent=run.task;meta.textContent=(run.approach||"Agent as Policy")+" · "+(run.runner?.name||"Legacy")+" · "+displayStatus(run)+" · "+new Date(run.created_at*1000).toLocaleString();button.append(title,meta);button.onclick=()=>{clearRun(run.id);poll();};$("history").append(button);if(terminal.has(run.status))$("experience").add(new Option(run.task.slice(0,35),run.id)); }
  if ([...$("experience").options].some(x=>x.value===old))$("experience").value=old;
}
async function poll() {
  if (!selected || polling) return; polling=true;
  try {
    const identity=selected, run=await api("/api/runs/"+identity+"?after="+cursor);
    if(identity!==selected)return;
    $("phase").textContent=displayStatus(run);$("run-title").textContent=run.task;
    const finished=terminal.has(run.status)&&!run.active;
    const controlled=activeRun&&activeRun!==identity?await api("/api/runs/"+activeRun+"?after=99999999"):run;
    if(controlled.active)activeRun=controlled.id;
    else if(terminal.has(controlled.status)&&activeRun===controlled.id)activeRun=null;

    $("run-attribution").textContent=(run.approach||"Agent as Policy")+" · "+(run.runner?.name||"Unattributed legacy run")+" · "+(run.robot_id||config.robot_id)+" · "+displayStatus(run);
    $("run-timing").textContent=timingLabel(run);
    renderReplay(run);
    $("run").disabled=!!activeRun;$("stop").disabled=!activeRun;$("stop").textContent=activeRun&&activeRun!==identity?"Stop active run":"Stop run";$("robot-select").disabled=!!activeRun;
    const nearBottom=$("events").scrollTop+$("events").clientHeight>=$("events").scrollHeight-60;
    for(const event of run.events){rows.push(event);$("events").append(eventRow(event));cursor=event.id;}
    if(nearBottom)$("events").scrollTop=$("events").scrollHeight;
    $("event-count").textContent=rows.length+" events";renderFiles(run.files);
    if(run.error)error(run.error);
    if(run.outcome){$("outcome").replaceChildren();const message=document.createElement("div"),scope=document.createElement("small");message.textContent=run.outcome.summary;scope.textContent=config.mode==="offline_mock"?(config.agent==="scripted"?"Mock transport verification only. No model inference or physical robot.":"Real model, mock robot. No physical task validation."):"Agent-declared outcome. Review captures and evidence before judging task success.";$("outcome").append(message,scope);$("outcome").hidden=false;}
    const historyKey=selected+run.status+"|"+(activeRun||"");if(finished&&terminalHistoryKey!==historyKey){terminalHistoryKey=historyKey;await history();}
  } catch(exc){error(exc.message);}finally{polling=false;}
}
$("task-form").addEventListener("submit",async event=>{
  event.preventDefault();error("");$("run").disabled=true;
  try{let goal=null;const file=$("goal").files[0];if(file)goal=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.onerror=reject;reader.readAsDataURL(file);});
    const run=await api("/api/runs",{task:$("task").value,duration_s:Number($("duration").value),experience_run:$("experience").value||null,goal_image:goal,robot_id:config.robot_id,runner:runner(),timing:{page_entered_at:performance.timeOrigin/1000,run_clicked_at:Date.now()/1000}});saveIdentity();clearRun(run.id);await history();await poll();
  }catch(exc){error(exc.message);$("run").disabled=false;}
});
$("stop").onclick=async()=>{if(!activeRun)return;const target=activeRun;$("stop").disabled=true;try{await api("/api/runs/"+target+"/stop",{});await poll();}catch(exc){error(exc.message);}};
$("refresh").onclick=()=>history().catch(exc=>error(exc.message));
$("goal").onchange=()=>{const file=$("goal").files[0];$("goal-preview").hidden=!file;if(file)$("goal-preview").src=URL.createObjectURL(file);};
async function init(){try{const requestedRobot=new URLSearchParams(location.search).get("robot_id");config=await api("/api/config"+(requestedRobot?"?robot_id="+encodeURIComponent(requestedRobot):""));$("robot-select").replaceChildren(...config.robots.map(x=>new Option(x.name,x.id)));$("robot-select").value=config.robot_id;$("mode").textContent=config.camera_source==="synthetic"?"Synthetic cameras":config.mode==="offline_mock"?"Live cameras · mock robot":"Live cameras · API robot";$("mode").classList.toggle("mock",config.mode==="offline_mock");$("robot").textContent=config.robot_id;$("model").textContent=config.agent==="scripted"?"Scripted agent · no model usage":config.model+" · Agent as Policy";if(config.mode==="offline_mock")$("task").value="Demonstrate the offline agent → API controller loop.";await history();const active=await api("/api/runs");const current=active.runs.find(x=>x.active||!terminal.has(x.status));activeRun=current?.id||null;const requestedRun=new URLSearchParams(location.search).get("run");if(current||requestedRun){clearRun(current?.id||requestedRun);await poll();}setInterval(poll,800);station();setInterval(station,10000);stopCameras=AgPCameras.start(config);}catch(exc){error(exc.message);}}
$("robot-select").onchange=async()=>{
 try{config=await api("/api/config?robot_id="+encodeURIComponent($("robot-select").value));$("robot").textContent=config.robot_id;stopCameras?.();stopCameras=AgPCameras.start(config);station();}
 catch(exc){error(exc.message);}
};
let checkingStation=false;
async function station(){
 if(checkingStation)return;checkingStation=true;
 try{const status=await api("/api/station?robot_id="+encodeURIComponent(config.robot_id));$("station-state").textContent=status.message;$("station-dot").style.background=status.connected?"#547766":"#9b6b37";}
 catch{$("station-state").textContent="Robot connection could not be checked";}finally{checkingStation=false;}
}
const automated=new URLSearchParams(location.search).get("automated")==="1";
function runner(){return automated?{kind:"automated",name:"Automated"}:{kind:"human",name:$("runner-name").value.trim(),email:$("runner-email").value.trim()};}
function saveIdentity(){if(!automated)try{localStorage.setItem("agp-runner",JSON.stringify(runner()));}catch{}}
function initIdentity(){
 $("runner-fields").hidden=automated;$("automated-runner").hidden=!automated;
 for(const id of ["runner-name","runner-email"])$(id).required=!automated;
 if(!automated)try{const prior=JSON.parse(localStorage.getItem("agp-runner")||"null");if(prior){$("runner-name").value=prior.name||"";$("runner-email").value=prior.email||"";}}catch{}
}
function renderReplay(run){
 const replay=run.replay;$("replay-panel").hidden=!replay;
 if(!replay)return;
 $("replay-state").textContent=replay.status.replaceAll("_"," ");
 $("replay-note").textContent=replay.note||"Retained footage is associated with this method, runner and run. It is not an independent task-success verdict.";
 const video=$("run-replay");if(replay.url&&video.dataset.run!==run.id){video.src=replay.url;video.dataset.run=run.id;}
 video.hidden=!replay.url;
}
initIdentity();
init();
