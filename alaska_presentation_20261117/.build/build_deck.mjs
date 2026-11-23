import fs from 'node:fs/promises';
import path from 'node:path';
import {Presentation, PresentationFile} from '@oai/artifact-tool';

const ROOT='/Users/pejmonshariati/.codex/.chatgpt-projects/g-p-6a7f49ff7aec8191b1e23d45a2922c23';
const W=path.join(ROOT,'alaska_presentation_20261117');
const BUILD=path.join(W,'.build');
const SOURCE=path.join(ROOT,'alaska_2026_sam_followup_20261116');
const SKILL='/Users/pejmonshariati/.codex/plugins/cache/openai-primary-runtime/presentations/26.1112.11011/skills/presentations';
process.env.RUNTIME_NODE_MODULES='/Users/pejmonshariati/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const {finalizePresentation}=await import(path.join(SKILL,'container_tools/artifact_tool_utils.mjs'));
const FONT='Arial';
const C={navy:'#24384F',text:'#26384D',muted:'#526A80',line:'#CBD6DF',blue:'#347CB1',red:'#BA5054',yellow:'#DBA429',green:'#609C8C',purple:'#8B65B1',pale:'#F3F6F9'};
const p=Presentation.create({slideSize:{width:1280,height:720}});
const manifest=[];
const tableOwners=new Set();
const plotData=JSON.parse(await fs.readFile(path.join(W,'assets/asset_manifest.json'),'utf8'));
function text(s,t,x,y,w,h,size=26,color=C.text,bold=false,align='left'){
  const a=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
  a.text=t;a.text.style={typeface:FONT,fontFamily:FONT,fontSize:size,color,bold,alignment:align,verticalAlignment:'top',insets:0,autoFit:'none'};return a;
}
function line(s,x,y,w,color=C.line){s.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:2},fill:color,line:{fill:'none',width:0}});}
function slide(title,section='Findings',subtitle='',notes=''){
 const s=p.slides.add();s.background.fill='#FFFFFF';
 text(s,section.toUpperCase(),64,29,1140,24,15,C.muted,true);
 text(s,title,64,65,1152,66,42,C.navy,true);
 if(subtitle)text(s,subtitle,64,137,1150,62,23,C.muted);
 line(s,64,669,1152);text(s,'Rachel / FairVote · November 11, 2026 snapshot',64,681,1040,22,14,C.muted);
 text(s,String(p.slides.items.length),1155,679,60,24,16,C.muted,false,'right');
 s.speakerNotes.text=notes+'\n\nAll ballot analysis uses Rachel’s unmodified November 11 CSV snapshot. Transfers are hypothetical Alaska-rule replays, not official final statewide results.';
 manifest.push({number:p.slides.items.length,title,section,subtitle,notes});return s;
}
function paras(s,items,x=64,y=214,w=1152,size=28,gap=105){items.forEach((v,i)=>text(s,v,x,y+i*gap,w,gap-18,size));}
function table(s,values,x,y,w,h,widths,size=25){
 tableOwners.add(p.slides.items.indexOf(s)+1);
 const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,values,columnWidths:widths});
 values.forEach((_,i)=>{t.rows[i].height=h/values.length;});
 t.borders.assign({fill:'#FFFFFF',width:0.5,style:'solid'});
 t.cells.block({row:0,column:0,rowCount:values.length,columnCount:values[0].length}).assign({textStyle:{fontFamily:FONT,typeface:FONT,fontSize:size,color:C.text},margins:{top:3,bottom:3,left:14,right:12},anchor:'center'});
 for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){
  const cell=t.getCell(r,c);cell.fill=r===0?C.navy:(r%2?'#FFFFFF':C.pale);
  cell.text.style={typeface:FONT,fontFamily:FONT,fontSize:size,color:r===0?'#FFFFFF':C.text,bold:r===0,verticalAlignment:'middle'};
 }
 return t;
}
async function img(s,name,x,y,w,h,alt=''){
 const b=await fs.readFile(path.isAbsolute(name)?name:path.join(W,name));
 s.images.add({blob:b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),contentType:'image/png',alt:alt||name,fit:'contain',position:{left:x,top:y,width:w,height:h}});
}
function note(s,t,y=607){text(s,t,64,y,1152,52,21,C.muted);}
function rect(s,x,y,w,h,fill){return s.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:h},fill,line:{fill:'none',width:0}});}
function dot(s,x,y,color){s.shapes.add({geometry:'ellipse',position:{left:x-7,top:y-7,width:14,height:14},fill:color,line:{fill:'#FFFFFF',width:1.5}});}
function bars(s,race){
 const groups=race==='governor'?['Democrat/Nonpartisan','Republican','Other / blank / overvote']:['Democrat','Nonpartisan','Libertarian','Republican','Other / blank / overvote'];
 const colors={'Democrat/Nonpartisan':'#3A7EAF',Democrat:'#3A7EAF',Nonpartisan:'#609C8C',Libertarian:'#C69B35',Republican:'#BA5054','Other / blank / overvote':'#BDCAD5'};
 const ids=[525,526,524,527],labels=['Mary Peltola','Dan J.','Gerald Heikes','Daniel S.'],centers=[298,545,792,1039];
 text(s,'Senate candidate order',64,227,215,27,18,C.muted);
 line(s,centers[0],241,centers[3]-centers[0]);
 centers.forEach((x,i)=>{dot(s,x,241,[C.blue,C.yellow,C.red,C.red][i]);text(s,labels[i],x-105,205,210,28,22,C.navy,true,'center');});
 for(const v of [0,25,50,75,100]){const y=546-v*2.65;rect(s,172,y,984,1,'#E5EBF0');text(s,v+'%',95,y-13,65,29,21,C.muted,false,'right');}
 ids.forEach((id,i)=>{let total=0;groups.forEach(g=>{const row=plotData.affiliation_values.find(v=>v.contest===race&&v.senate_candidate_id===id&&v.group===g);const h=row.percent*2.65;rect(s,centers[i]-63,546-total*2.65-h,126,h,colors[g]);if(row.percent>=10)text(s,row.percent.toFixed(1)+'%',centers[i]-65,546-total*2.65-h/2-16,130,34,24,'#FFFFFF',true,'center');total+=row.percent;});if(Math.abs(total-100)>1e-8)throw Error('Stack not100');text(s,labels[i],centers[i]-110,560,220,35,23,C.muted,false,'center');});
 text(s,'Senate 1st choice:',64,563,190,29,18,C.muted);
 const positions=race==='governor'?[190,520,760]:[145,340,555,770,955];
 groups.forEach((g,i)=>{rect(s,positions[i],616,22,14,colors[g]);text(s,g,positions[i]+30,610,i===groups.length-1?230:330,31,race==='governor'?20:18,C.navy);});
}
function axes(s){
 const partyColor={Democrat:C.blue,Republican:C.red,'Independent / Nonpartisan':C.yellow,Libertarian:C.purple};
 for(const [k,label,y] of [['us_senate','Senate',283],['governor','Governor',433],['us_house','House',583]]){
  text(s,label,64,y-17,145,37,25,C.navy,true);line(s,255,y,850);
  plotData.candidate_axes[k].forEach((a,i)=>{const x=255+850*a.coordinate;dot(s,x,y,partyColor[a.party]);const above=i%2===0;const yy=above?y-61:y+17;const label=a.public_label.replace('Mary Peltola','Peltola').replace('Gerald Heikes','Heikes');text(s,label+'\n'+a.coordinate.toFixed(3),x-125,yy,250,58,20,C.navy,true,'center');});
 }
}

// 1 — cover
{
 const s=slide('Alaska’s ranked ballots','Research presentation','','Source: Alaska_2026_Sam_Followup.ipynb, opening summary and methods. Prepared for discussion with Sam. These are three separate elections: governor, one US House seat, and one US Senate seat.');
 text(s,'Preferences, transfers and voter structure',64,198,1100,80,43,C.navy);
 text(s,'Senate · Governor · U.S. House',64,302,1100,48,30,C.muted);
 text(s,'Pejmon Shariati',64,451,1000,45,29,C.navy,true);
 text(s,'November 2026 · Rachel’s November 11 data',64,504,1100,48,26,C.muted);
}
// 2 — scope and aliases
{
 const s=slide('The data and the candidates','Data','Three separate races linked by anonymous ballot identifiers',`Source: inputs/ and completed/descriptive/descriptive_results.json. Senate and House IDs match exactly. Governor is missing 130 of those records. Original names are preserved in source CSVs. Dan J. = Sullivan, Daniel J. Jr. (526), outsider. Daniel S. = Sullivan, Dan S. (527), incumbent. The aliases are for readability only. DOE CVR coverage does not include ballots counted only by hand: https://www.elections.alaska.gov/election-results/e/?id=26genr`);
 table(s,[['Race','Recorded ballots'],['U.S. Senate','244,705'],['Governor','244,575'],['U.S. House','244,705']],64,218,510,287,[290,220],26);
 text(s,'Senate candidates',660,215,545,40,30,C.navy,true);
 paras(s,['Mary Peltola — Democrat','Dan J. — outsider; no party affiliation','Gerald Heikes — Republican','Daniel S. — Republican incumbent'],660,272,550,25,65);
 note(s,'A dated snapshot: these records are not the final statewide vote.');
}
// 3 — RCV plain English
{
 const s=slide('Ranked-choice voting (RCV)','How the count works','If no first-choice majority, the candidate with the fewest votes is eliminated',`Official rule: AS 15.15.350(d), https://www.akleg.gov/statutesPDF/Title-15.pdf ; DOE explanation https://www.elections.alaska.gov/election-information/ . In the first round, a majority ends the count. Otherwise, the lowest candidate is eliminated and votes go to the next-highest-ranked continuing candidate. Subsequent rounds continue until two candidates remain. This example assumes Dan J. and then Heikes are eliminated; it is illustrative, not an official result.`);
 text(s,'Each ballot counts for one continuing candidate at a time.',64,210,1150,40,27,C.navy);
 text(s,'Example ranking',64,260,1140,38,25,C.muted,true);
 text(s,'Dan J.  →  Heikes  →  Daniel S.',64,308,1150,62,44,C.navy,true);
 paras(s,['1. The vote starts with Dan J.','2. If Dan J. is eliminated, it moves to Heikes.','3. If Heikes is then eliminated, it moves to Daniel S.'],64,384,1152,28,70);
 note(s,'No remaining valid ranking for a continuing candidate → inactive ballot.');
}
// 4 — ranking interpretation
{
 const s=slide('Valid rankings and inactive ballots','Definitions','Ranking eligibility and later ballot status are different concepts',`Sources: AS15.15.350(d), https://www.akleg.gov/statutesPDF/Title-15.pdf ; official agency English phrase “valid rankings” in B19-NC glossary p10 https://www.elections.alaska.gov/doc/forms/B19-NC.pdf . The phrase is agency wording, not a separately defined statutory ballot category. Production prefix parser preserves raw rank cells and stops at the first overvote, permits one internal skipped rank, stops at two consecutive skipped ranks, and collapses repeated candidate names without treating duplicate ranks as blank. Generic write-ins occupy recorded cells while barriers are applied; the generic category is excluded before the named candidate replay. Hidden candidate names inside generic overvote cells cannot be recovered.`);
 paras(s,['Valid rankings: preferences eligible to be followed under Alaska’s rules.','Overvote: more than one choice at one rank. Our replay stops at that rank.','One skipped rank can be crossed; two consecutive skipped ranks stop the sequence.','Inactive ballot: no remaining valid ranking for a continuing candidate.'],64,215,1152,27,88);
 note(s,'A ballot may have valid earlier rankings and become inactive in a later round.');
}
// 5,6 — preferred thick bars, one per readable slide
for(const [title,file,what] of [['Governor first choice','governor_first_choice.png','governor tickets'],['House first choice','house_first_choice.png','House candidates']]){
 const s=slide(title,'Cross-race preferences','Within each Senate first-choice group',`Source: completed/descriptive/first_choice_party_crosstabs.csv. Denominator is the complete literal-rank-1 Senate cohort: Peltola117437, DanJ3940, Heikes5054, DanielS115849. Cross-race labels are candidate/ticket affiliations, not voter registration. Percentages include blank/overvote/other and missing governor records in the cohort denominator. The top strip shows candidate order only; equally spaced bar centers are not numeric MDS distances. Original percentages and House stacking order preserved.`);
 bars(s,title.startsWith('Governor')?'governor':'us_house');
 // note(s,`Each bar totals 100%. Colors describe first-choice ${what}; the top strip marks Senate candidate order.`);
}
// 7 — exhaustive five-category table
{
 const s=slide('Dan J.-first rankings of the assumed finalists','Senate preferences','3,940 ballots with Dan J. literally marked first',`Source: confusion/confusion_results.json and daniel_first_usable_permutations.csv. Legal-prefix comparison after barriers, not visible names anywhere. 568+423=991 ballots have both valid finalists:568/991=57.32% Peltola earlier,423/991=42.68% DanielS earlier. All-cohort proportions differ:568/3940=14.42%,423/3940=10.74%. 765 is Peltola-valid-only, distinct from568 both-valid Peltola-earlier. Names after barriers are excluded.`);
 table(s,[['Valid finalist preferences','Ballots','Share of 3,940'],['Peltola before Daniel S.','568','14.42%'],['Daniel S. before Peltola','423','10.74%'],['Peltola only','765','19.42%'],['Daniel S. only','481','12.21%'],['Neither finalist','1,703','43.22%']],64,214,1152,348,[660,200,292],25);
 note(s,'Among the 991 ranking both finalists, 57.32% place Peltola ahead of Daniel S.');
}
// 8 — literal cohort routes
{
 const s=slide('Where Dan J.-first ballots would go','Hypothetical Senate replay','Assume Dan J. and Heikes are eliminated, leaving Peltola and Daniel S.',`Source: confusion/dan_j_first_finalist_routes.csv and confusion_results.json. Fixed literal-first cohort3940. After DanJ elimination:P1147,S638,H708,inactive1447; Heikes onward:P186,S266,inactive256. FinalP1333=1147+186;S904=638+266;inactive1703=1447+256. Source strict raw bullet count1363 differs named-prefix singleton1447. 1333/3940=33.83%;904/3940=22.94%;1703/3940=43.22%.`);
 await img(s,'flow_assets/dan_j_first_flow_slide.png',64,202,1152,390);
 note(s,'Final destinations in this replay: Peltola 1,333 (33.83%) · Daniel S. 904 (22.94%) · inactive 1,703 (43.22%)',595);
}
// 9 — fullsource Sankey
{
 const s=slide('The Senate transfer flow','Hypothetical Senate replay','All 244,705 Senate records; wider ribbons represent more ballots',`Source: completed/flows/ saved Senate stage allocations and links. Generic write-ins excluded first, then DanJ, then Heikes. This sequence is a dated replay, not a statement about official ongoing elimination. The DanJ node4055 includes incoming votes, so it differs from the3940 literal-first cohort. Stage totals remain244705. Initial valid allocation:P117505,S115917,H5155,J3992,WI773,inactive1363. AfterWI:P117656,S116023,H5272,J4055,I1699. AfterJ:P118830,S116678,H6014,I3183. Final:P119933,S119223,I5549.`);
 await img(s,'flow_assets/senate_full_sankey_slide.png',64,195,1152,410);
 note(s,'The Dan J. node contains 4,055 ballots after incoming transfers; it is not the 3,940 literal-first group.');
}
// 10 — confusion
{
 const s=slide('Rankings compatible with several explanations','Interpreting the patterns','Ballot order shows preferences; it does not identify voter confusion',`Source: confusion/daniel_first_usable_permutations.csv, incumbent_omission_by_Peltola.csv, conditional_upper_bound_scenarios.csv. Examples are observable patterns, not classified psychological states. No identified link to Sam’s ballot#34 was available; do not substitute row34. A DanJ-Heikes-DanielS ordering demonstrates an indirect route to incumbent support. Some ballots mention both finalists but Peltola is preferred. No confusion prevalence is estimated.`);
 paras(s,['Dan J. → Daniel S. can preserve a later preference for the incumbent.','Dan J. → Heikes → Daniel S. can preserve it through another candidate.','2,468 Dan J.-first ballots have no valid ranking for Daniel S.; 765 of these have a valid Peltola ranking.','These patterns can reflect sincere preferences or mistakes. Rankings alone cannot tell us which.'],64,211,1152,28,93);
}
// 11 — introduce MDS
{
 const s=slide('Multidimensional scaling (MDS)','Candidate positions','Here, MDS summarizes ranking relationships on a single line',`Source: axis_models/*/mds_results.json and axis_models/run_axes.py. OG method computes ranking adjacency/co-ranked frequencies, converts these to inverse-square-root dissimilarities, and fits1D nonmetric MDS. Mirrored runs are aligned, modal order averaged and normalized0–1. Model setup20outer×8starts; stronger100×16 sensitivity preserves candidate order and gamma. Unranked candidates add no comparison constraints. MDS does not perform vote tabulation.`);
 paras(s,['Candidates with more similar relationships in the rankings are placed closer together.','The model fits candidate positions. We then ask whether a voter could prefer candidates in the recorded order by distance along that line.','Each race has its own 0–1 axis. Direction is arbitrary; distances are not calibrated measures of ideology.'],64,216,1152,29,116);
 note(s,'MDS summarizes ballot structure. It does not determine who wins the RCV count.');
}
// 12 — exact candidate axes
{
 const s=slide('The fitted candidate axes','One-dimensional MDS','Party colors annotate the candidates; the fitted positions come from rankings',`Source: axis_models/us_senate/candidate_axis.csv, governor/candidate_axis.csv, us_house/candidate_axis.csv. Exact Senate positionsP0,J.436306,H.751166,S1. GovernorKreiss0,Taylor.507917,Bronson.633023,Wilson1. House displayed reflection:Hafner0,Hill.254147,McDermott.745856,Begich1. Independent axes cannot be treated as a common measured ideology scale. Party sources preserved in candidate metadata. Kreiss/Johnson ticket is Democrat/Nonpartisan.`);
 axes(s);
 text(s,'Blue: Democrat · Red: Republican · Yellow: Independent / Nonpartisan / no party · Purple: Libertarian',64,184,1152,30,18,C.muted);
}
// 13 — consistency
{
 const s=slide('How often does the single line fit?','Consistency (gamma)','Gamma = the share of the stated group compatible with some voter position on the line',`Source: axis_models/*/mds_results.json. Three/four valid named rankings only. SenateN45743,61.54real,41.57random;GovernorN88693,57.23,50.51;HouseN43003,65.27,41.26.49 randomized runs per race. Randomize tails preserving first choice×valid-prefix length; fit and score a new axis for each randomized run. This is a structured reference baseline, not simply all permutations equally weighted. One/two-name prefixes automatically pass this compatibility criterion and therefore make all-nonempty gamma higher. Not a causal or intention measure.`);
 table(s,[['Race','Ballots with 3–4 names','Observed gamma','Random mean'],['Senate','45,743','61.54%','41.57%'],['Governor','88,693','57.23%','50.51%'],['House','43,003','65.27%','41.26%']],64,231,1152,259,[210,350,300,292],25);
 text(s,'49 randomized runs per race, preserving first choice and ranking length',64,526,1152,46,26,C.navy,true);
 note(s,'One- and two-name rankings pass automatically, so the 3–4-name group is more informative.');
}
// 14 — positions vs candidates
{
 const s=slide('Estimating voter positions','Voter distributions','A ranking can allow a range of locations on the fitted candidate axis',`Source: voter_distributions/results.json, density_grid.csv and voter_distributions/run_distributions.py. Mahshad allocation convention places n observations evenly within each compatible interval with np.linspace(lo,hi,n); singleton rankings pinned to chosen candidate. The intervals are defined by pairwise distance inequalities. Spatially inconsistent rankings receive no estimated position; they can still contain valid Alaska rankings. Kernel density is boundary-reflected, with within-axis common bandwidth. These are estimated allocations, not uniquely recovered voter locations, and cannot be individually paired across races. Sensitivity to uniform allocation of singleton intervals is saved in singleton_allocation_sensitivity.png. Bullet vote means one recorded named candidate with no further selections; strict raw and valid-prefix singleton counts differ.`);
 paras(s,['Candidate positions are the fitted points from MDS.','Estimated voter positions are assigned within the locations compatible with each ranking, using Mahshad’s convention.','A single-name ranking is placed at that candidate. This choice strongly shapes peaks near candidates.','The curves summarize this allocation; they do not directly measure voters’ ideology.'],64,215,1152,28,91);
}
// 15 — all densities
for(const [race,raceLabel] of [['senate','Senate'],['governor','Governor'],['house','House']]){
 const s=slide(raceLabel+' estimated voter distribution','Mahshad’s allocation convention','Curve height shows concentration; area is normalized within each plotted distribution',`Source: voter_distributions/density_grid.csv; exact saved density arrays reused without refitting. Located:Senate225411/244705;Governor202646/244575;House227393/244705. Unplaced spatially inconsistent/empty/missing records are not silently removed from the source totals. Plotted distributions are conditional on located records. Note strong dependence of endpoint peaks on singleton allocation convention. Each election normalized separately.`);
 await img(s,'assets/'+race+'_voter_density.png',115,184,1050,464);
}
// 16 — focal comparison
for(const [race,raceLabel] of [['senate','Senate'],['governor','Governor'],['house','House']]){
 const s=slide(raceLabel+': Peltola-first and Dan J.-first voters','Estimated voter distributions','The same Senate first-choice groups, located separately using each race’s rankings',`Source: voter_distributions/density_grid.csv, saved focal comparison. Plot groups defined by literal Senate rank1. Conditional densities integrate1 for plotted records; curves are not cohort size comparisons. LocatedPeltola90.5%Senate86.5%Governor93.5%House;DanJ86.6%,75.1%,85.7%. Different elections have separate normalized axes; do not read an equal numerical coordinate as the same ideology across races. This is the two-group focal figure, not either excluded four-group overlay or coverage chart.`);
 await img(s,'assets/'+race+'_peltola_dan_j_density.png',115,184,1050,464);
 // Plot caption carries this convention and plotted percentages.
}
// 17 — Hafner crossrace
{
 const s=slide('Eric Hafner’s first-choice voters','House focus','17,918 ballots mark Hafner first: 7.32% of all recorded House ballots',`Source: hafner/results.json and hafner_cross_election_first_choices.csv. Hafner literal-first cohort17918,SenateP16866=94.1288%,GovernorKreiss16385=91.4444%. Full cohort denominator includes blanks, overvotes, write-ins and74missing governor rows. Bill Hill cohort98286:93.31%Peltola and93.07%Kreiss. These choices are consistent with party-label voting but do not establish voter knowledge, motivation or awareness of Hafner’s background. Background: DOJ sentenced Hafner20years onDec7,2023 https://www.justice.gov/usao-nj/pr/monmouth-county-man-sentenced-20-years-prison-making-threatening-communications-and ; KTUU June2026 reports he had never visited Alaska https://www.alaskasnewssource.com/2026/06/06/prisoner-his-mom-how-are-candidates-whove-never-visited-alaska-able-run-states-federal-seats/ . Background is context, not a ballot inference.`);
 table(s,[['Hafner-first ballots also mark…','Ballots','Share of 17,918'],['Peltola first for Senate','16,866','94.13%'],['Kreiss-Tomkins / Johnson first for governor','16,385','91.44%']],64,232,1152,225,[742,160,250],26);
 text(s,'Both Hafner- and Hill-first groups strongly favor Peltola and the Democrat/Nonpartisan governor ticket.',64,500,1152,80,29,C.navy,true);
 note(s,'This is consistent with a party-label explanation; it does not establish who was informed.');
}
// 18 — Hafner next vs final
{
 const s=slide('Hafner’s backup rankings and replay destinations','Hypothetical House replay','A next named preference is different from the candidate who finally receives the vote',`Source: hafner/results.json. LiteralHafner-first17918. NextnamedHill6745,McDermott2181,Begich882,none8110. FinalHill8131,Begich1142,inactive8645. McDermott eliminated before Hafner; whenHafner is removed, McDermott preferences are bypassed. Strict rawbullets7707=43.01%,namedprefixsingleton8110=45.26%. Inactive8645=48.25% includes more than strict bullets.`);
 table(s,[['Next valid named preference','Ballots'],['Bill Hill','6,745'],['Jim McDermott','2,181'],['Nick Begich','882'],['No further named preference','8,110']],64,221,556,310,[396,160],24);
 table(s,[['Final replay destination','Ballots / share'],['Bill Hill','8,131 / 45.38%'],['Nick Begich','1,142 / 6.37%'],['Inactive','8,645 / 48.25%']],660,221,556,249,[315,241],24);
 note(s,'McDermott is eliminated before Hafner in this replay, so those rankings are bypassed.');
}
// 19 — geography
{
 const s=slide('Where Hafner received support','Geography','The largest vote count and the largest share are different measures',`Source: hafner/geography/results.json and districts_all_voting_modes.csv / precincts_and_administrative_batches.csv. House districts derived from precinct prefix, not judicial district field. Allmethods district comparisons; physicalprecinct comparisons hereElectionDayonly. HD21EAnchorage653/6686=9.77%;HD18GovernmentHill/JBER/NMuldoon304/2035=14.94% highest geographicdistrictshare excludingadmin99. HD22NEAnch558/3922=14.23%. At least8216/17918=45.85% identifiableAnchoragearea, conservative duepooledHD9EV/absentee184Hafner votes sharedWhittier/Anchorage. LargestprecinctcountEAnchNo3 129/1032=12.50%;highestprecinctshareN>=100 Skagway68/368=18.48%. Chefornak8/30=26.67%higherunfiltered. Geographic metadata https://www.elections.alaska.gov/research/district-maps/ . Do not infer residentialcity forpooledmethodbatches.`);
 table(s,[['Measure','Location','Hafner first'],['Most votes in a House district','HD 21 · East Anchorage','653 / 6,686 (9.77%)'],['Highest district share','HD 18 · Government Hill / JBER / North Muldoon','304 / 2,035 (14.94%)'],['Highest precinct share, ≥100 records','Skagway · Election Day only','68 / 368 (18.48%)']],64,222,1152,286,[350,502,300],23);
 text(s,'At least 8,216 Hafner-first ballots (45.85%) are identifiable as Anchorage-area records.',64,544,1152,70,29,C.navy,true);
}
// 20 — takeaways
{
 const s=slide('What the rankings establish','Research findings','Behavior is observable; confusion and political motivation remain unmeasured',`Summary of the dated dataset findings. The3,940DanJ cohort is a fixed literal-first group. These values are hypothetical transfer outcomes following the recorded valid preferences. Gamma result concerns3/4-name rankings; density estimates depend on allocation convention. No causal interpretation of name confusion, party labels, candidate knowledge, or district context.`);
 paras(s,['Dan J.-first ballots follow several routes: 1,333 reach Peltola, 904 reach Daniel S., and 1,703 become inactive in this replay.','A single candidate axis fits more observed 3–4-name rankings than the randomized reference in all three races.','Hafner-first voters overwhelmingly favor Peltola and the Democrat/Nonpartisan governor ticket in the other races.','These records describe ranking patterns; they do not reveal voters’ intentions.'],64,211,1152,28,96);
}
// 21 — all16J patterns
{
 const s=slide('All 16 valid named orders beginning with Dan J.','Appendix','Intervening generic write-ins omitted after ranking barriers are applied',`Source: confusion/daniel_first_usable_permutations.csv. All16orders add3940. “Dan J. only” means the valid named prefix contains onlyDanJ, not necessarily a strict raw bullet. Strictrawbullets1363. Abbreviations P=Peltola,H=Heikes,S=DanielS. Full original ranks remain in source files. Final destinations assumeDanJthenHeikes eliminated. No row is proof of confusion.`);
 const a=[['Order after Dan J.','Ballots'],['No further name','1,447'],['Peltola','624'],['Heikes','256'],['Daniel S.','214'],['Peltola → Heikes → Daniel S.','211'],['Daniel S. → Heikes','161'],['Heikes → Daniel S. → Peltola','160'],['Daniel S. → Heikes → Peltola','149']];
 const b=[['Order after Dan J.','Ballots'],['Peltola → Daniel S. → Heikes','147'],['Heikes → Peltola → Daniel S.','133'],['Heikes → Daniel S.','106'],['Peltola → Heikes','88'],['Peltola → Daniel S.','77'],['Daniel S. → Peltola → Heikes','69'],['Heikes → Peltola','53'],['Daniel S. → Peltola','45']];
 table(s,a,64,216,558,360,[438,120],21);table(s,b,658,216,558,360,[438,120],21);
 note(s,'Strict bullet ballot: only Dan J. selected, all later ranks blank (1,363 ballots).');
}
// 22 — all lengths gamma
{
 const s=slide('Consistency including short rankings','Appendix','One- and two-name rankings automatically fit the compatibility test',`Source: axis_models/*/mds_results.json. Allnonemptyvalidnamedprefixes:Senate243006,92.76real89.00random;Governor240576,84.23,81.75;House242328,93.84,89.58. Three/fourlengthN45743,88693,43003respectively.49matched-tailrandomizations preserve observedfirstchoice×prefixlength distribution; eachhas independentlyfittedaxis. DifferenceppSenate3.76,Governor2.48,House4.26;3/4differences19.97,6.73,24.01. Not allsourceballots arenonempty: rawrowsarelarger.`);
 table(s,[['Race','All nonempty rankings','Observed gamma','Random mean'],['Senate','243,006','92.76%','89.00%'],['Governor','240,576','84.23%','81.75%'],['House','242,328','93.84%','89.58%']],64,226,1152,258,[215,345,300,292],25);
 paras(s,['The higher percentages reflect the inclusion of many short rankings.','The 3–4-name comparison in the main results places a stronger demand on the fitted line.'],64,524,1152,25,62);
}
// 23 — conditional ceilings
{
 const s=slide('Conditional ceilings on possible lost support','Appendix','These are scenario bounds, not estimates of how many voters were confused',`Source: confusion/conditional_upper_bound_scenarios.csv. Each scenario makes an explicit reassignment assumption. No-validDanielS subset2468:765currentlyP+1703inactive, maxadditionalS2468,marginchange2*765+1703=3233. AllDanJfirst3940:904alreadyS so maxadditional3036,marginchange2*1333+1703=4369. BothSvalid1472:904alreadyS568P, maxadditional568,marginchange1136. Sets overlapandmustnotbeadded. Lowerboundzero iscompatiblewith observeddata. Keep focusonresearchquestion, no politicalcounterargument.`);
 table(s,[['Assume every ballot in this group intended Daniel S.','Group size','Maximum extra Daniel S. votes'],['Dan J.-first with no valid Daniel S. ranking','2,468','2,468'],['All Dan J.-first ballots','3,940','3,036'],['Dan J.-first ranking both Sullivans validly','1,472','568']],64,222,1152,281,[650,180,322],23);
 note(s,'Reassign the selected ballots to Daniel S.; hold all others fixed. Groups overlap. Zero confusion remains possible.');
}
// 24 — provenance/validation
{
 const s=slide('Data preservation and validation','Appendix','Original records, interpreted rankings and hypothetical counts remain separate',`Source: validation/DELIVERY_CHECKS.json, completed/descriptive/source_provenance.json, analysis_checks/terminology_20261117/audit_results.json, validation/verify_completed.py and completed/flows/fairvote_benchmark_comparison.csv and preserved archived FairVote tables. All54 numericroundcells match archivedNov11FairVote values checked, not currentlivearticle. Thevisible-name subgroup reproduction is distinctfromAlaska-rule transfers and cannotserveas alegal-rulevalidation. Original RachelCSV hashes recorded, rawrankstringspreserved, normalizedballotIDswithoutcollisions,Senate/HousesameIDs,130Governorrowsmissingretained. No hiddenovervotememberships reconstructed. SameversionofficialCVR excludeshandcount-onlyrecords. MDSsavedprofiles/denominators independentlychecked; laterinactiveballotswithvalidprefixesremaininthespati alanalysis.`);
 paras(s,['Unmodified Rachel CSVs and original rank cells are preserved, with file hashes.','Anonymous ballot identifiers link races; 130 missing governor records remain explicit.','All 54 round-count values checked match the archived November 11 FairVote tables.','This validates the same-version replay comparison, not completeness or final statewide certification.'],64,213,1152,28,94);
}
// 25 — source reference
{
 const s=slide('Sources and supporting material','Appendix','Full methods, ranking tables and reproducibility files are in the research notebook',`Notebook: Alaska_2026_Sam_Followup.ipynb and Alaska_2026_Sam_Followup_Readable.html. Analytic ballot inputs only Rachel November11 CSVs. Sourcehashes Senate3f0a1a946f23d2d1195f98c5ee5f123916d5f91ede334397465692d5e7f2d972;Governor3d76cd612870025d9c470f78a60d0bde0cd274aeb9a4e57d575704b588f4b8b3;Houseb57fad2ef5a8845ba5b3da1eeb3c5e7cfb036c1c174af640b3acee65e45f8b48. Official terminology and rule references below. Hafner background and geographic references cited in corresponding speaker notes.`);
 const rows=[['Alaska counting rules','https://www.akleg.gov/statutesPDF/Title-15.pdf'],['Alaska election explanation','https://www.elections.alaska.gov/election-information/'],['Official “valid rankings” wording','https://www.elections.alaska.gov/doc/forms/B19-NC.pdf'],['CVR coverage / official results','https://www.elections.alaska.gov/election-results/e/?id=26genr'],['House district geography','https://www.elections.alaska.gov/research/district-maps/']];
 rows.forEach(([label,url],i)=>{text(s,label,64,212+i*76,1152,31,25,C.navy,true);const a=text(s,url,64,247+i*76,1152,32,22,C.muted);a.text.get(url).link={uri:url,isExternal:true};});
}


const scripts=[
"This presentation examines three Alaska races using Rachel’s November 11 snapshot. We will look at recorded preferences, hypothetical transfers under Alaska’s rules, and the structure of rankings. These are dated research results, not final statewide election results.",
"The files describe three different elections. Anonymous ballot identifiers let us connect their choices across races. Senate and House contain the same 244,705 ballot identifiers; governor has 130 fewer records. Dan J. means the outsider, and Daniel S. means the incumbent; original names remain unchanged in the data.",
"Ranked-choice voting lets someone list candidates in preference order. Each ballot counts for one continuing candidate at a time. If nobody has a first-round majority, the lowest candidate is eliminated and each affected ballot moves to its next-highest-ranked continuing candidate. Alaska’s later rounds continue until two candidates remain. The example assumes Dan J. is eliminated before Heikes.",
"Valid rankings describe preferences that the counting rules allow us to follow. Inactive describes what happens in a round when a ballot has no remaining qualifying choice. Those are different concepts: a ballot can have valid early rankings and become inactive later. We preserve every original rank cell and apply overvote, skip and repeated-name rules separately.",
"Each bar is everyone who literally marked the named Senate candidate first. The colors show those voters’ first-choice governor ticket affiliations. Each bar totals 100%, including other choices and missing or blank records. The top strip gives Senate candidate order, with party colors; the equal spacing is not fitted MDS distance.",
"This is the same Senate grouping, now showing House first-choice candidate affiliations. The stack runs Democrat, Nonpartisan, Libertarian, Republican and other from bottom to top. Candidate affiliation is not voter registration. The cohort denominator includes every ballot in the Senate first-choice group.",
"Among the 3,940 Dan J.-first ballots, 991 have valid rankings for both assumed finalists. Of these, 568 place Peltola earlier and 423 place Daniel S. earlier. That is 57.32% versus 42.68% among the 991, rather than among all 3,940. Another 765 rank Peltola validly without a valid Daniel S. ranking; that is a separate group.",
"Read the diagram from left to right. It follows the same fixed set of 3,940 literal Dan J.-first ballots. Wider ribbons mean more ballots. If Dan J. and then Heikes are eliminated, 1,333 reach Peltola, 904 reach Daniel S., and 1,703 become inactive. The Peltola total includes 1,147 direct transfers and 186 through Heikes; Daniel S. includes 638 direct and 266 through Heikes.",
"This diagram follows all 244,705 Senate records. Most votes stay with Peltola or Daniel S.; smaller ribbons show the hypothetical transfers. Every stage preserves the total, including inactive ballots. The Dan J. node after write-in exclusion contains 4,055 votes because it has received incoming transfers. It is different from the 3,940 literal-first group used in the preceding results.",
"We can identify ranking patterns that preserve a later preference for Daniel S., and patterns that omit him. We cannot identify a voter’s intentions from those patterns alone. The same order could be sincere or mistaken. The 2,468 figure is the group with no valid Daniel S. ranking; 765 of those have a valid Peltola ranking.",
"Multidimensional scaling is a way to summarize relationships among candidates. Our original method builds dissimilarities from ranking adjacency and co-ranking information, then fits a one-dimensional nonmetric MDS model. Mirrored solutions are aligned and positions normalized to zero through one. Each election has a separate line. This model summarizes rankings and plays no role in counting the election.",
"Dots mark fitted candidate positions, and colors identify candidate party affiliation. The Senate ordering is Peltola, Dan J., Heikes and Daniel S. Governor and House have their own independently fitted axes. A position of one-half in one race is not the same measured ideology as one-half in another. Reversing an axis would not change the substantive ordering relationships.",
"Gamma is the share of the stated ranking group that can be explained by some voter position on the fitted line, using distance to candidates. Here we focus on three- and four-name rankings, because one- and two-name rankings automatically pass this test. For the random comparison, we preserve first choice and ranking length, randomize the later choices, and independently fit and score 49 new datasets per race. The random mean is a reference, not a measure of voter intent.",
"The fitted candidate points do not uniquely identify each voter’s location. For a compatible ranking, we find the interval of possible locations and assign observations across it under Mahshad’s convention. A single-name ranking is placed at that candidate. Spatially inconsistent rankings receive no estimated position, even though they may contain valid Alaska rankings. The curves are therefore model-dependent estimates, not direct observations of ideology.",
"This Senate curve uses the saved estimated positions without refitting. It includes 225,411 located ballots out of 244,705 source records. The horizontal coordinate is the Senate candidate axis and the curve height shows concentration. Endpoint peaks depend strongly on the convention placing single-name rankings at candidates. The displayed density is conditional on the ballots that can be located.",
"The governor curve uses 202,646 located ballots out of 244,575 source records. Its axis was fitted separately from the Senate axis. The distribution is conditional on compatible rankings and depends on the same allocation convention; it is not an independently observed ideology distribution.",
"The House curve uses 227,393 located ballots out of 244,705 source records. Candidate markers help read where the estimated concentration falls. As with the other races, the shape depends on the allocation convention and the set of rankings that can be located.",
"The groups are defined by literal Senate first choice: Peltola or Dan J. We then use their Senate rankings to estimate positions on the Senate axis. Each curve integrates to one among that group’s plotted ballots, so curve height does not compare group size. The legend gives the share of the full group that is plotted.",
"These are still the Peltola-first and Dan J.-first Senate groups, but their governor rankings now locate them on the governor axis. The legend reports coverage separately for each group. We are comparing ranking structure across elections, not tracking a uniquely observed individual ideology coordinate.",
"Here the same two Senate groups are located from their House rankings. The House axis is independent of the other two axes. The shapes are conditional on the records that can be located under the convention, and each group’s curve integrates to one.",
"There are 17,918 literal Hafner-first House ballots. Of those, 94.13% also mark Peltola first for Senate and 91.44% mark the Democrat/Nonpartisan governor ticket first. Hill-first voters also overwhelmingly favor those choices. These patterns are consistent with a party-label explanation, but they do not show what voters knew about either candidate. Hafner’s criminal sentence and reported lack of visits to Alaska are background context, not inferences from ballots.",
"The next named preference and the final replay destination are different questions. McDermott is eliminated before Hafner in this replay, so a Hafner ballot listing McDermott next bypasses him when Hafner leaves. Of the fixed 17,918 Hafner-first ballots, 8,131 finish with Hill, 1,142 with Begich and 8,645 become inactive. The 8,110 with no further valid named preference are broader than the 7,707 strict raw bullet ballots.",
"The district with the largest number of Hafner-first votes is not the district with the largest percentage. District comparisons include all voting modes in this snapshot; the geographic precinct comparisons here are Election Day records only. The Skagway result is restricted to precincts with at least 100 records, because very small places can have higher but unstable shares. The Anchorage-area count is a conservative minimum because pooled batches cannot always be assigned to one city.",
"The findings describe recorded preferences and their consequences under explicit assumptions. The Dan J. group has several different replay destinations, and a single candidate axis fits the observed long rankings more often than the randomized reference. Hafner’s cross-race pattern is strongly aligned with Peltola and the Democrat/Nonpartisan governor ticket. None of those findings establishes individual confusion or motivation.",
"Each row is a distinct valid named candidate order beginning with Dan J. The two tables together sum to 3,940. Generic write-ins are omitted only after applying ranking barriers; original rank cells remain preserved. The 1,447 with no further valid named preference are not all strict bullet ballots. A strict bullet ballot selects only Dan J. and leaves all later ranks blank; there are 1,363 of those.",
"These gamma results include every nonempty valid named ranking, including short rankings. Their percentages are higher because one- and two-name rankings automatically satisfy the compatibility test. That is why the three- and four-name results are more demanding. Each random mean comes from the same 49 matched randomizations described in the main results.",
"These are conditional ceilings, not estimated confusion rates. Each row assumes every selected ballot is reassigned to Daniel S. while all other ballots stay fixed. Votes already reaching him add nothing. The groups overlap and cannot be added. The observed data are also compatible with no voter confusion.",
"We preserve Rachel’s original CSVs and rank strings with recorded file hashes. We keep raw rankings, Alaska-rule interpretations and replay allocations separate. All 54 checked numeric round-count values match the archived November 11 FairVote tables. This is a same-version validation, not proof of final statewide completeness. Later inactive ballots with valid prefixes remain in the spatial analysis.",
"The research notebook contains the full methods, raw and interpreted ranking tables, sensitivity results and reproducibility files. Official Alaska references explain the counting rules and terminology. The sources on this slide are clickable; background and geographic sources are cited in the relevant notes."
];
if(scripts.length!==manifest.length)throw Error('Speaker-note count mismatch');
for(let i=0;i<manifest.length;i++){
 const urls=[...new Set((manifest[i].notes.match(/https:\/\/[^\s;]+/g)||[]).map(u=>u.replace(/[.,]$/,'')))];
 p.slides.items[i].speakerNotes.text=scripts[i]+'\n\nSources: Alaska_2026_Sam_Followup.ipynb; Rachel’s November 11 CSVs and saved analysis outputs.\n'+urls.join('\n');
}

await fs.mkdir(path.join(BUILD,'previews'),{recursive:true});
await fs.writeFile(path.join(BUILD,'slide_manifest.json'),JSON.stringify(manifest,null,2));
console.log('Built',p.slides.items.length,'slides');
const draft=path.join(BUILD,'candidate.pptx');
await(await PresentationFile.exportPptx(p)).save(draft);
console.log('Draft exported');
for(let i=0;i<p.slides.items.length;i++){
 const blob=await p.export({slide:p.slides.items[i],format:'png',scale:1});
 await fs.writeFile(path.join(BUILD,'previews',`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await blob.arrayBuffer()));
 console.log('Rendered',i+1);
}
await fs.writeFile(path.join(BUILD,'deck.proto.json'),JSON.stringify(p.toProto()));
const out=path.join(W,'output','Alaska_2026_Research_Presentation_Ready.pptx');
const result=await finalizePresentation({workspaceDir:W,candidatePath:draft,finalPath:out,pythonExecutable:'/Users/pejmonshariati/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3',integrityValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...[...tableOwners].flatMap(n=>['--require-native-table-slide',String(n)])],explicitTotalSlideCount:29,requiredNativeTableOwnerSlides:[...tableOwners],fontPolicy:{basis:'design',families:[FONT]},verifyArtifactToolImport:true,receiptPath:path.join(BUILD,'validation_ready.json')});
console.log(JSON.stringify(result));
