"use strict";
let pendingCorrection=null, memoryJob=null, memoryJobActive=false, stopFailure="";
const $ = id => document.getElementById(id);
let stopCameras=null;
let config, verificationReport=null, activeRun = null, selected = null, cursor = -1, rows = [], polling = false, fileListKey = "", terminalHistoryKey = "";
const terminal = new Set(["completed", "succeeded", "stopped", "timed_out", "failed", "disconnected", "safety_aborted", "interrupted", "resetting"]);
async function api(path, value) {
  const response = await fetch(path, value === undefined ? {} : {method:"POST", headers:{"Content-Type":"application/json", "X-CSRF-Token":config.csrf}, body:JSON.stringify(value)});
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || "Request failed");
  return result;
}
function error(message) { $("error").textContent = message || ""; $("error").hidden = !message; }
function displayStatus(run){return run.error?"Failed":terminal.has(run.status)&&!run.active&&run.outcome?.status==="give_up"?"Could not complete":terminal.has(run.status)&&!run.active&&run.outcome?.status==="done"?"Agent finished":run.status.replaceAll("_"," ");}
function timingLabel(run){
 if(run.mode==="offline_mock")return "Mock robot · no physical execution";
 const timing=run.timing||{};
 const review=verificationReport?.physical_reviews?.find(r=>r.run_id===run.id&&r.status==="passed"&&r.run_clicked_at===timing.run_clicked_at&&r.home_completed_at===timing.home_completed_at);
 if(review)return "Visual review: method motion observed by "+review.run_to_visible_upper_s.toFixed(1)+" s after Run and "+review.home_to_visible_upper_s.toFixed(1)+" s after Home. Both timing targets met.";
 if(timing.run_to_motion_s!=null)return "Measured completion: "+timing.run_to_motion_s.toFixed(1)+" s after Run"+(timing.home_to_measured_completion_s!=null?", "+timing.home_to_measured_completion_s.toFixed(1)+" s after Home":"")+". Targets: 30 s after Run and 15 s after Home. Visual onset timing is unverified.";
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
  const result=await api("/api/runs"); activeRun=result.runs.find(x=>x.owned!==false&&(x.active||!terminal.has(x.status)))?.id||null; const old=$("experience").value;
  $("history").replaceChildren();$("experience").replaceChildren(new Option("Fresh start",""));
  for (const run of result.runs) { const button=document.createElement("button");button.className="history-item";const title=document.createElement("strong"),meta=document.createElement("small");title.textContent=run.task;meta.textContent=(run.approach||"MEMO")+" · "+(run.runner?.name||"Legacy")+" · "+displayStatus(run)+" · "+new Date(run.created_at*1000).toLocaleString();button.append(title,meta);button.onclick=()=>{clearRun(run.id);poll();};$("history").append(button);if(run.owned!==false&&terminal.has(run.status))$("experience").add(new Option(run.task.slice(0,35),run.id)); }
  if ([...$("experience").options].some(x=>x.value===old))$("experience").value=old;
  return result.runs;
}
async function poll() {
  if (!selected || polling) return; polling=true;
  try {
    const identity=selected, run=await api("/api/runs/"+identity+"?after="+cursor);
    if(identity!==selected)return;
    $("phase").textContent=displayStatus(run);$("run-title").textContent=run.task;
    const finished=terminal.has(run.status)&&!run.active;
    const controlled=activeRun&&activeRun!==identity?await api("/api/runs/"+activeRun+"?after=99999999"):run;
    if(controlled.active&&controlled.owned!==false)activeRun=controlled.id;
    else if(terminal.has(controlled.status)&&activeRun===controlled.id){activeRun=null;stopFailure="";}

    $("run-attribution").textContent=(run.approach||"MEMO")+" · "+(run.runner?.name||"Unattributed legacy run")+" · "+(run.robot_id||config.robot_id)+" · "+(run.execution_mode||"interactive").replaceAll("_"," ")+" · "+displayStatus(run);
    $("run-timing").textContent=timingLabel(run);
    renderReplay(run);
    renderMemoryContext(run, finished);
    $("run").disabled=!!activeRun||memoryJobActive;$("stop").disabled=!activeRun;$("stop").textContent=activeRun&&activeRun!==identity?"Stop active run":"Stop run";$("robot-select").disabled=!!activeRun;
    const nearBottom=$("events").scrollTop+$("events").clientHeight>=$("events").scrollHeight-60;
    for(const event of run.events){rows.push(event);$("events").append(eventRow(event));cursor=event.id;}
    if(nearBottom)$("events").scrollTop=$("events").scrollHeight;
    renderProgress(run);$("event-count").textContent=rows.length+" events";renderFiles(run.files);
    if(run.error)error(run.error);
    if(run.outcome){$("outcome").replaceChildren();const message=document.createElement("div"),scope=document.createElement("small");message.textContent=run.outcome.summary;scope.textContent=config.mode==="offline_mock"?(config.agent==="scripted"?"Mock transport verification only. No model inference or physical robot.":"Real model, mock robot. No physical task validation."):"Agent-declared outcome. Review captures and evidence before judging task success.";$("outcome").append(message,scope);$("outcome").hidden=false;}
    const historyKey=selected+run.status+"|"+(activeRun||"");if(finished&&terminalHistoryKey!==historyKey){terminalHistoryKey=historyKey;await history();await memory();}
  } catch(exc){error(exc.message);}finally{polling=false;}
}
$("task-form").addEventListener("submit",async event=>{
  event.preventDefault();error("");$("run").disabled=true;$("phase").textContent="Submitting";$("run-progress").hidden=false;$("run-progress").textContent="Submitting your task · joining the robot queue and preparing the coding agent.";
  try{let goal=null;const file=$("goal").files[0];if(file)goal=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.onerror=reject;reader.readAsDataURL(file);});
    const run=await api("/api/runs",{task:$("task").value,duration_s:Number($("duration").value),experience_run:$("experience").value||null,goal_image:goal,memo:true,robot_id:config.robot_id,runner:runner(),execution_mode:verification?"automated_test":automated?"unattended_test":"interactive",timing:{page_entered_at:performance.timeOrigin/1000,run_clicked_at:Date.now()/1000}});saveIdentity();activeRun=run.id;clearRun(run.id);$("stop").disabled=false;$("robot-select").disabled=true;await poll();history().catch(exc=>error(exc.message));
  }catch(exc){error(exc.message);$("run-progress").textContent="Task submission failed · correct the error below and try Run again.";$("run").disabled=!!activeRun||memoryJobActive;}
});
$("stop").onclick=async()=>{if(!activeRun)return;const target=activeRun;$("stop").disabled=true;try{await api("/api/runs/"+target+"/stop",{});stopFailure="";error("");await poll();}catch(exc){stopFailure=exc.message;error(exc.message);$("stop").disabled=!activeRun;$("run-progress").hidden=false;$("run-progress").textContent="Stop could not be confirmed · "+exc.message+". Use Stop again; watch the live arms.";}};
$("refresh").onclick=()=>history().catch(exc=>error(exc.message));
$("goal").onchange=()=>{const file=$("goal").files[0];$("goal-preview").hidden=!file;if(file)$("goal-preview").src=URL.createObjectURL(file);};
async function init(){try{api("/api/acceptance").then(v=>{verificationReport=v;$("verification-status").textContent="Verification: "+v.passed+"/"+v.total+" ("+v.percentage+"%)";}).catch(()=>{$("verification-status").textContent="Verification status unavailable";});const requestedRobot=new URLSearchParams(location.search).get("robot_id");config=document.getElementById("initial-config")?JSON.parse(document.getElementById("initial-config").textContent):await api("/api/config"+(requestedRobot?"?robot_id="+encodeURIComponent(requestedRobot):""));$("robot-select").replaceChildren(...config.robots.map(x=>new Option(x.name,x.id)));$("robot-select").value=config.robot_id;$("mode").textContent=config.camera_source==="synthetic"?"Synthetic cameras":config.mode==="offline_mock"?"Live cameras · mock robot":"Live cameras · API robot";$("mode").classList.toggle("mock",config.mode==="offline_mock");$("robot").textContent=config.robot_id;$("model").textContent=config.agent==="scripted"?"Scripted agent · no model usage":"Model: MEMO · "+(config.foundation_model||"scripted fixture");if(config.mode==="offline_mock")$("task").value="Demonstrate the offline agent → API controller loop.";stopCameras=AgPCameras.start(config);station();setInterval(station,10000);const runs=await history();const current=runs.find(x=>x.owned!==false&&(x.active||!terminal.has(x.status)));activeRun=current?.id||null;const requestedRun=new URLSearchParams(location.search).get("run");if(current||requestedRun){clearRun(current?.id||requestedRun);await poll();}$("run").disabled=!!activeRun||memoryJobActive;memory().catch(exc=>error(exc.message));restoreMemoryJob().catch(exc=>error(exc.message));setInterval(()=>{poll();pollMemoryJob();},800);}catch(exc){error(exc.message);}}
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
const verification=new URLSearchParams(location.search).get("verification")==="1";
function runner(){return automated?{kind:"automated",name:"Automated"}:{kind:"human",name:$("runner-name").value.trim(),email:$("runner-email").value.trim()};}
function saveIdentity(){if(!automated)try{localStorage.setItem("memo-runner",JSON.stringify(runner()));}catch{}}
function initIdentity(){
 $("runner-fields").hidden=automated;$("verification-note").hidden=!verification;$("automated-runner").hidden=!automated;
 for(const id of ["runner-name","runner-email"])$(id).required=!automated;
 if(!automated)try{const prior=JSON.parse(localStorage.getItem("memo-runner")||"null");if(prior){$("runner-name").value=prior.name||"";$("runner-email").value=prior.email||"";}}catch{}
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

function renderMemoryContext(run, finished){
 const writable=run.id===activeRun&&!finished;
 $("correction").disabled=!writable;$("send-correction").disabled=!writable;
 const latest=run.corrections?.at(-1);
 $("correction-state").textContent=latest?(latest.delivered?"Latest correction delivered to the agent.":finished?"Run ended before delivery.":"Correction queued for the next observation."):writable?"Corrections guide the next decision. Use Stop to halt motion.":"Select the active run to send a correction.";
 $("memory-scope").textContent="This run uses skillbook v"+run.memory_version+". New lessons are available to later runs; skills remain agent-authored and unverified.";
}
async function memory(){
 const data=await api("/api/memories");$("memory-version").textContent="v"+data.version+" · "+data.memories.length+" entries";
 const fragment=document.createDocumentFragment();
 for(const row of data.memories){const item=document.createElement("details"),title=document.createElement("summary"),pre=document.createElement("pre"),note=document.createElement("p");title.textContent=row.action+" · "+row.kind+" · v"+row.version;pre.textContent=row.content;note.textContent="Agent-authored, unverified · "+row.encoder;item.append(title,note,pre);fragment.append(item);}
 if(!data.memories.length){const p=document.createElement("p");p.textContent="No lessons yet. Run a task and provide a correction to build your skillbook.";fragment.append(p);}
 $("memories").replaceChildren(fragment);$("refine-memory").disabled=memoryJobActive||!!activeRun||data.memories.length<2;
}
$("correction-form").addEventListener("submit",async event=>{
 event.preventDefault();if(!selected||selected!==activeRun)return;error("");$("send-correction").disabled=true;
 const content=$("correction").value.trim();
 if(!pendingCorrection||pendingCorrection.text!==content||pendingCorrection.run!==selected)pendingCorrection={text:content,request_id:crypto.randomUUID(),run:selected};
 try{await api("/api/runs/"+selected+"/corrections",pendingCorrection);$("correction").value="";pendingCorrection=null;await poll();}
 catch(exc){error(exc.message);}finally{$("send-correction").disabled=$("correction").disabled;}
});
$("refine-memory").onclick=async()=>{
 try{const job=await api("/api/skillbook/jobs",{runner:runner()});memoryJob=job.id;memoryJobActive=true;$("run").disabled=true;$("refine-memory").disabled=true;$("cancel-refinement").hidden=false;await pollMemoryJob();}
 catch(exc){error(exc.message);}
};
let checkingMemoryJob=false;
async function pollMemoryJob(){
 if(!memoryJob||checkingMemoryJob)return;checkingMemoryJob=true;
 try{const job=await api("/api/skillbook/jobs/"+memoryJob);memoryJobActive=job.active;
 $("refinement-state").textContent=job.active?"Refining related lessons · offline, no robot control":job.outcome?.summary||job.error||"Refinement ended";
 $("cancel-refinement").hidden=!job.active;$("run").disabled=!!activeRun||job.active;
 if(!job.active){memoryJob=null;await memory();}}
 catch(exc){error(exc.message);}finally{checkingMemoryJob=false;}
}
$("cancel-refinement").onclick=async()=>{try{if(memoryJob)await api("/api/skillbook/jobs/"+memoryJob+"/stop",{});}catch(exc){error(exc.message);}};

async function restoreMemoryJob(){const data=await api("/api/skillbook/jobs");const active=data.jobs.find(job=>job.owned!==false&&job.active);if(active){memoryJob=active.id;memoryJobActive=true;await pollMemoryJob();}}

function renderProgress(run){
 const progress=$("run-progress");progress.hidden=false;
 if(stopFailure&&activeRun){progress.textContent="Stop could not be confirmed · "+stopFailure+". Use Stop again; watch the live arms.";return;}
 if(terminal.has(run.status)&&run.active){progress.textContent="Session "+run.status.replaceAll("_"," ")+" · finishing cleanup before a new Run can start.";return;}
 if(!run.active&&terminal.has(run.status)){progress.textContent=run.error?"Run ended · "+run.error+". Review the error; start a new Run when ready. Movement will not be replayed.":run.outcome?.summary||"Run ended · review activity and retained evidence.";return;}
 const lastCall=rows.filter(e=>e.kind==="tool_call").at(-1);
 if(lastCall?.message==="frames"&&!rows.some(e=>e.id>lastCall.id&&e.kind==="tool_result"&&e.message==="frames")){
  progress.textContent=lastCall.arguments?.depth?"Reading fresh overhead/wrist RGB-D · waiting for measured depth and camera calibration before choosing a target.":"Reading fresh camera views before the next decision.";return;
 }
 const home=run.timing?.home_completed_at;
 const elapsed=home?Date.now()/1000-home:null;
 const admitted=rows.some(e=>e.kind==="lifecycle"&&e.message==="Robot session running");
 const ready=rows.some(e=>e.kind==="worker_profile"&&e.profile?.stage==="thread_ready");
 const images=rows.some(e=>e.kind==="leased_images_reviewed");
 const motion=rows.some(e=>e.kind==="physical_motion_measured");
 progress.textContent=(home?"Home complete · ":"")+(elapsed>15&&!motion?"More than 15 s since Home; motion is not yet confirmed. Stop is available. ":"")+(motion?"Measured movement confirmed · the agent is checking observations and finishing the task.":images?"Queue complete · scene received · the coding agent is choosing and executing its next step.":admitted?"Queue complete · "+(ready?"coding agent ready · supplying the settled camera views.":"preparing the coding agent before motion can begin."):"Waiting for robot admission · the coding environment prepares while the queue and robot readiness checks finish.");
}
