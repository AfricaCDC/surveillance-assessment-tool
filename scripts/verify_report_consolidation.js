// Run: node scripts/verify_report_consolidation.js [optional pasted report]
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync('static/app.js','utf8');
const context=vm.createContext({});
for(const name of ['cleanReportLines','consolidatedReportOutput']){
  const start=source.indexOf(`function ${name}(`);
  const end=source.indexOf('\nfunction ',start+1);
  vm.runInContext(source.slice(start,end),context);
}
const run=sections=>context.consolidatedReportOutput(sections,true);
const result=run({'Summary of Findings':['Surveillance Profile Report','-','Lack of airtime for verification calls.','Poor network coverage.','Knowledge gap should be closed through training.','Unusual workflow needs investigation.'],Recommendations:['Provision of airtime.','-','No other recommendation since transition is in progress']});
assert(!result.includes('Surveillance Profile Report'));
assert(!result.split('Original recommendation coverage check')[0].includes(': -'));
assert.equal((result.match(/Infrastructure and reporting continuity\n/g)||[]).length,1);
assert(result.includes('Supporting findings: F1, F2'));
assert(result.includes('Findings requiring individual review: F3'));
assert(result.includes('Recorded suggestions — for review'));
assert(!result.includes('F4'));
assert(!run({Recommendations:['Digitalisation.']}).includes('Proposed action:'));
assert.equal(run({Overview:['-','Surveillance Profile Report']}),'No substantive findings or respondent suggestions are available to consolidate.');
assert(!run({Findings:['A rare operational concern.']}).includes('Proposed action:'));
if(process.argv[2]){
  const text=fs.readFileSync(process.argv[2],'utf8');
  const [findings,recommendations]=text.split('Consolidated recommendations');
  const output=run({Findings:findings.replace('Consolidated findings','').split('\n'),Recommendations:(recommendations||'').split('\n')});
  assert(!output.includes('Surveillance Profile Report'));
  assert(!output.split('Original recommendation coverage check')[0].includes(': -'));
  assert.equal((output.match(/^R\d+ \[Recommendations\]:/gm)||[]).length,43);
  assert(output.includes('Recorded suggestions — for review'));
  fs.mkdirSync('outputs/report-consolidation',{recursive:true});
  fs.writeFileSync('outputs/report-consolidation/coverage-check.txt',output);
  fs.writeFileSync('outputs/report-consolidation/review-example.txt',context.consolidatedReportOutput({Findings:findings.replace('Consolidated findings','').split('\n'),Recommendations:(recommendations||'').split('\n')}));
  console.log('Pasted example checked; preview written to outputs/report-consolidation/review-example.txt');
}
console.log('PASS: grouped evidence, source links, placeholders, suggestions, unmatched and absent evidence');
