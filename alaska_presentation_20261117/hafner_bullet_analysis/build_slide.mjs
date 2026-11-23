import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Presentation,PresentationFile} from '@oai/artifact-tool';
const base=path.dirname(fileURLToPath(import.meta.url));
const r=JSON.parse(await fs.readFile(path.join(base,'results.json'),'utf8'));
const audit=JSON.parse(await fs.readFile(path.join(base,'independent_verification.json'),'utf8'));
if(!audit.passed || r.cohort_n!==7707)throw new Error('Cohort audit not passed');
const N=r.cohort_n;
const p=Presentation.create({slideSize:{width:1280,height:720}});
const s=p.slides.add();s.background.fill='#FFFFFF';
const navy='#24384F',muted='#526A80',blue='#347CB1';
function text(str,x,y,w,h,size=24,bold=false,color=navy){
 const q=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 q.text=str;q.text.style={typeface:'Arial',fontFamily:'Arial',fontSize:size,bold,color,insets:0};return q;
}
text('HAFNER BULLET BALLOTS',64,25,1152,25,15,true,muted);
text('Hafner’s bullet voters: Senate and governor',64,64,1152,55,36,true);
text('7,707 ballots: Hafner first for House; ranks 2–5 all blank',64,127,1152,38,23,false,muted);
text('87.73% selected both Peltola and Kreiss-Tomkins/Johnson first',64,181,1152,36,25,true,blue);
text('Senate first choice',64,235,552,32,25,true);
text('Governor first choice',664,235,552,32,25,true);
const labels={
 'Peltola, Mary':'Mary Peltola','Sullivan, Dan S.':'Daniel S. (incumbent)',
 'Sullivan, Daniel J. Jr.':'Dan J. (outsider)','Heikes, Gerald L.':'Gerald Heikes',
 'Kreiss-Tomkins/Johnson':'Kreiss-Tomkins / Johnson','Wilson/Shower':'Wilson / Shower',
 'Bronson/Church':'Bronson / Church','Taylor/English':'Taylor / English',
 'skipped':'Blank first rank','overvote':'First-rank overvote','Write-in':'Write-in',
 'Missing contest record':'Missing contest record'
};
const records=[];
for(const [race,x] of [['us_senate',64],['governor',664]]){
 const entries=Object.entries(r.counts[race]).sort((a,b)=>b[1]-a[1] || a[0].localeCompare(b[0]));
 const values=[['Candidate / category','Ballots','Share'],...entries.map(([name,n])=>[labels[name],n.toLocaleString('en-US'),(100*n/N).toFixed(2)+'%'])];
 const table=s.tables.add({rows:values.length,columns:3,left:x,top:279,width:552,height:values.length*34,
                          columnWidths:[340,108,104],values});
 table.borders.assign({style:'solid',fill:'#FFFFFF',width:0.8});
 for(let i=0;i<values.length;i++){
  table.rows[i].height=34;
  for(let j=0;j<3;j++){
   const cell=table.getCell(i,j);
   cell.fill=i===0?navy:i===1?'#DCEFF8':i%2===0?'#F2F5F8':'#FFFFFF';
   cell.text.style={fontFamily:'Arial',typeface:'Arial',fontSize:i===0?17.5:19,
                    bold:i<=1,color:i===0?'#FFFFFF':navy,alignment:j===0?'left':'right'};
  }
 }
 records.push({race,values,rows:values.length});
}
text('First choices are recorded rank 1. All percentages use the full 7,707-ballot cohort.',64,615,1152,29,18,false,muted);
text('41 governor records are missing; these are separate from blank first ranks.',64,647,1152,28,18,false,muted);
text('Rachel / FairVote · November 11, 2026 snapshot',64,688,1152,22,15,false,muted);
s.speakerNotes.text=`Strict bullet definition: Hafner appears at literal House rank1 and ranks2–5 are all skipped (blank). This is 7,707 ballots, 43.01% of the 17,918 Hafner-first ballots; it excludes repeated Hafner selections, later overvotes and later write-ins. Senate and governor choices here are literal recorded rank1, not promoted preferences or transfer destinations. Each percentage uses all7,707 ballots, including missing governor records. All7,707 Senate records match by normalized ballot ID;7,666 governor records match and41 are missing. Peltola is first on7,262 (94.23%); Kreiss-Tomkins/Johnson on6,975 (90.50%); both on6,761 (87.73%). These describe recorded choices and do not identify voter knowledge or motivation. Sources: Rachel/FairVote November11 CSVs (${Object.values(r.source_files).map(v=>path.basename(v.path)).join('; ')}). Independent selection and one-to-one joins reproduced all counts. Full source hashes are in results.json.`;
const candidate=path.join(base,'Hafner_Bullet_Voters_draft.pptx');
await(await PresentationFile.exportPptx(p)).save(candidate);
const preview=await p.export({slide:s,format:'png',scale:2});
await fs.writeFile(path.join(base,'Hafner_Bullet_Voters_Preview.png'),new Uint8Array(await preview.arrayBuffer()));
await fs.writeFile(path.join(base,'slide_table_values.json'),JSON.stringify(records,null,2));
process.env.RUNTIME_NODE_MODULES='/Users/pejmonshariati/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const skill='/Users/pejmonshariati/.codex/plugins/cache/openai-primary-runtime/presentations/26.1116.12010/skills/presentations';
const {finalizePresentation}=await import(path.join(skill,'container_tools/artifact_tool_utils.mjs'));
await fs.mkdir(path.join(base,'output'),{recursive:true});
await finalizePresentation({workspaceDir:base,candidatePath:candidate,
 finalPath:path.join(base,'output/Hafner_Bullet_Voters.pptx'),
 pythonExecutable:'/Users/pejmonshariati/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3',
 integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit'],
 explicitTotalSlideCount:1,fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,
 receiptPath:path.join(base,'slide_validation.json')});
console.log('Editable slide ready.');
