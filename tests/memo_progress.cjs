const fs=require('node:fs'), vm=require('node:vm'), assert=require('node:assert/strict');
const nodes=new Map(),handlers=new Map(),calls=[];
function node(id){if(!nodes.has(id))nodes.set(id,{value:'',textContent:'',hidden:false,disabled:false,
 files:[],options:[],scrollTop:0,scrollHeight:0,clientHeight:0,dataset:{},style:{},
 addEventListener:(event,fn)=>handlers.set(id+':'+event,fn),append(){},replaceChildren(){},
 removeAttribute(){},pause(){}});return nodes.get(id);}
const context={console,URLSearchParams,location:{search:'?verification=1'},Date,performance:{timeOrigin:Date.now()-2000},
 document:{getElementById:node,createElement:()=>node('generated'),createDocumentFragment:()=>node('fragment')},
 localStorage:{setItem(){}},Option:function(text,value){this.text=text;this.value=value;},
 setInterval(){},fetch:async(path,options)=>{calls.push({path,options});return {ok:false,json:async()=>({error:'Unavailable fixture'})};}};
vm.createContext(context);
vm.runInContext(fs.readFileSync(process.argv[2],'utf8').replace('initIdentity();\ninit();',''),context);
vm.runInContext(`config={csrf:'fixture',mode:'offline_mock',robot_id:'yam-1'};
renderProgress({status:'failed',active:false,error:'Coding worker unavailable'});`,context);
assert.match(node('run-progress').textContent,/Coding worker unavailable/);
assert.match(node('run-progress').textContent,/new Run/);
vm.runInContext(`rows=[];renderProgress({status:'running',active:true,timing:{home_completed_at:Date.now()/1000-20}});`,context);
assert.match(node('run-progress').textContent,/Home complete/);
assert.match(node('run-progress').textContent,/More than 15 s/);
assert.match(node('run-progress').textContent,/Stop is available/);
assert.equal(calls.length,0); // Displaying stalled/failed state never replays a request.
assert.match(vm.runInContext(`timingLabel({id:'unreviewed',mode:'physical_api',timing:{run_to_motion_s:20,home_to_measured_completion_s:9}})`,context),/unverified/);
vm.runInContext(`verificationReport={physical_reviews:[{run_id:'reviewed',status:'passed',run_clicked_at:100,home_completed_at:112,run_to_visible_upper_s:21.4,home_to_visible_upper_s:9.8}]};`,context);
assert.match(vm.runInContext(`timingLabel({id:'reviewed',timing:{run_clicked_at:100,home_completed_at:112}})`,context),/Both timing targets met/);
assert.doesNotMatch(vm.runInContext(`timingLabel({id:'different',timing:{run_clicked_at:100,home_completed_at:112}})`,context),/Both timing targets met/);
assert.doesNotMatch(vm.runInContext(`timingLabel({id:'reviewed',timing:{run_clicked_at:101,home_completed_at:112}})`,context),/Both timing targets met/);
vm.runInContext(`verificationReport={task_reviews:[{run_id:'failed-task',created_at:123,status:'failed',summary:'Object remained on its support.'}]};
var reviewedRun={id:'failed-task',created_at:123,status:'stopped',active:false,mode:'physical_api',outcome:{status:'done',summary:'Model claimed done'}};
renderProgress(reviewedRun);`,context);
assert.equal(vm.runInContext('displayStatus(reviewedRun)',context),'Task not passed');
assert.match(node('run-progress').textContent,/Object remained on its support/);
assert.equal(vm.runInContext('reviewedRun.outcome.status',context),'done'); // Original model declaration is retained.
assert.equal(vm.runInContext('displayStatus({...reviewedRun,created_at:124})',context),'Agent finished');
assert.equal(vm.runInContext('taskReview({...reviewedRun,active:true})',context),null);
assert.equal(calls.length,0); // Review display never causes a control request.
node('task').value='Offline fixture';node('duration').value='60';
node('runner-name').value='Fixture';node('runner-email').value='fixture@example.test';
(async()=>{
 await handlers.get('task-form:submit')({preventDefault(){}});
 assert.match(node('run-progress').textContent,/submission failed/);
 assert.equal(node('run').disabled,false);
 assert.equal(calls.filter(c=>c.path==='/api/runs').length,1);
 context.fetch=async(path,options)=>{calls.push({path,options});throw Error('fixture read unavailable');};
 vm.runInContext(`activeRun='active-fixture';selected='historical-fixture';`,context);
 await node('stop').onclick();
 assert.equal(calls.at(-1).path,'/api/runs/active-fixture/stop');
 assert.equal(node('stop').disabled,false);
 assert.match(node('run-progress').textContent,/Stop could not be confirmed/);
 vm.runInContext(`renderProgress({status:'running',active:true,timing:{}});`,context);
 assert.match(node('run-progress').textContent,/Stop could not be confirmed/);
 console.log(JSON.stringify({failure:'passed',stall:'passed',submissionRecovery:'passed',
   historicalSelectionStop:'passed',motionRequests:0,physical:false}));
})().catch(e=>{console.error(e);process.exitCode=1;});
