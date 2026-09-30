// Regression check for the actual NDJSON reader and separate coverage output.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync('static/app.js','utf8');
const start=source.indexOf('async function streamAssistantAnswer(');
const end=source.indexOf('\nasync function ',start+1);
const payload=JSON.stringify({delta:'Draft theme\n'})+'\n'+JSON.stringify({coverage_check:'F69: backup evidence retained',done:true});
const bytes=new TextEncoder().encode(payload);
const context=vm.createContext({state:{},TextDecoder,fetch:async()=>({ok:true,body:new ReadableStream({start(controller){controller.enqueue(bytes.slice(0,17));controller.enqueue(bytes.slice(17));controller.close()}})})});
vm.runInContext(source.slice(start,end),context);
(async()=>{
  const text=await context.streamAssistantAnswer({},()=>{});
  assert.equal(text,'Draft theme');
  assert.equal(context.state.recommendationAudit,'F69: backup evidence retained');
  console.log('PASS: streamed answer and separate coverage check survive split packets and final line without newline');
})().catch(error=>{console.error(error);process.exitCode=1});
