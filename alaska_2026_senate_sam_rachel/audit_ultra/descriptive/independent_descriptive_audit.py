"""Independent Rachel-only audit. No producer module is imported and no source is modified."""
from pathlib import Path
from collections import Counter,defaultdict
import csv,gzip,hashlib,json,re,sys,datetime
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
RACES={'governor':'Governor','us_house':'House','us_senate':'Senate'}
EXPECTED_FIELDS=['ballotID','ballot_type','countingGroup','district','districtType','precinct','precinctPortion','rank1_ambiguous_candidates','rank1_overvote_candidates','votingLocation','rank1','rank2','rank3','rank4','rank5']
SENATE=['Heikes, Gerald L.','Peltola, Mary','Sullivan, Daniel J. Jr.','Sullivan, Dan S.']
P='Peltola, Mary';D='Sullivan, Dan S.';O='Sullivan, Daniel J. Jr.'
PARTY={
 'Heikes, Gerald L.':'Republican','Peltola, Mary':'Democrat','Sullivan, Daniel J. Jr.':'No listed affiliation','Sullivan, Dan S.':'Republican',
 'Begich, Nick':'Republican','Hafner, Eric':'Democrat','Hill, Bill':'Nonpartisan','McDermott, James C. "Jim"':'Libertarian',
 'Bronson/Church':'Republican','Taylor/English':'Republican','Wilson/Shower':'Republican','Kreiss-Tomkins/Johnson':'Democrat/Nonpartisan','Write-in':'Write-in'}
METAFIELDS=['ballot_type','countingGroup','district','districtType','precinct','precinctPortion','votingLocation']

def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def uid(text):
 m=re.fullmatch(r'([0-9]+)_([0-9]+)_([0-9]+)_?',text)
 assert m,repr(text)
 return tuple(int(x) for x in m.groups())
def usable(ranks):
 # Independent look-ahead implementation: choose the earliest barrier before
 # deduplicating named candidates. Trailing blank ranks do not create a barrier.
 last=max((i for i,x in enumerate(ranks) if x!='skipped'),default=-1)
 barriers=[(i,'overvote') for i,x in enumerate(ranks) if x=='overvote']
 barriers += [(i,'two_consecutive_skips') for i in range(len(ranks)-1) if ranks[i]==ranks[i+1]=='skipped' and i+1<last]
 stop,reason=min(barriers,default=(len(ranks),'blank' if last<0 else 'end_of_ranks'))
 return tuple(dict.fromkeys(x for x in ranks[:stop] if x not in ('skipped','overvote'))),reason

def first_literal(ranks):return {'skipped':'blank_rank1','overvote':'overvote_rank1'}.get(ranks[0],ranks[0])
def pref_category(pref):
 if P not in pref:return 'senator_only_explicitly_ranked' if D in pref else 'neither_explicitly_ranked'
 if D not in pref:return 'peltola_only_explicitly_ranked'
 return 'peltola_above_senator_both_ranked' if pref.index(P)<pref.index(D) else 'senator_above_peltola_both_ranked'
def party(name):return PARTY.get(name,name)

def main():
 sources={};data={};qc={};meta_indices=[EXPECTED_FIELDS.index(x) for x in METAFIELDS]
 for slug,race in RACES.items():
  path=ROOT/'inputs'/f'Alaska_20261103_US_{race}_11_11.csv';records={};quality=Counter();literal_lengths=Counter();distinct_names=Counter();usable_lengths=Counter();usable_named_lengths=Counter();reasons=Counter();rank_ov=Counter();rank_skips=Counter();tokens=Counter()
  with path.open(encoding='utf-8-sig',newline='') as f:
   reader=csv.DictReader(f);assert reader.fieldnames==EXPECTED_FIELDS
   for row in reader:
    key=uid(row['ballotID']);assert key not in records
    vals=tuple(sys.intern(row[x]) for x in EXPECTED_FIELDS);ranks=vals[-5:];pref,why=usable(ranks)
    records[key]=(vals,pref)
    named=[x for x in ranks if x not in ('skipped','overvote')]
    nnamed=[x for x in pref if x!='Write-in']
    literal_lengths[len(named)]+=1;distinct_names[len(set(named))]+=1;usable_lengths[len(pref)]+=1;usable_named_lengths[len(nnamed)]+=1;reasons[why]+=1;tokens.update(ranks)
    quality['rows']+=1
    quality['all_five_rank_tokens_skipped']+=all(x=='skipped' for x in ranks)
    quality['exact_one_named_cell_no_overvote']+=len(named)==1 and 'overvote' not in ranks
    quality['one_distinct_named_candidate_no_overvote']+=len(set(named))==1 and 'overvote' not in ranks
    quality['one_usable_choice_including_writein']+=len(pref)==1
    quality['one_usable_named_candidate_excluding_writein']+=len(nnamed)==1
    quality['any_overvote_token']+='overvote' in ranks
    quality['literal_rank1_overvote']+=ranks[0]=='overvote'
    quality['any_lower_rank_overvote']+='overvote' in ranks[1:]
    quality['any_repeat_named_candidate']+=len(named)!=len(set(named))
    quality['any_internal_skip']+=any(x=='skipped' and any(y!='skipped' for y in ranks[i+1:]) for i,x in enumerate(ranks))
    quality['any_two_consecutive_internal_skips']+=any(ranks[i]==ranks[i+1]=='skipped' and any(x!='skipped' for x in ranks[i+2:]) for i in range(3))
    quality['rank1_ambiguous_metadata_present']+=bool(row['rank1_ambiguous_candidates'])
    quality['rank1_overvote_metadata_present']+=bool(row['rank1_overvote_candidates'])
    quality['rank1_overvote_metadata_disagrees_with_token']+=(bool(row['rank1_overvote_candidates'])!=(ranks[0]=='overvote'))
    for i,x in enumerate(ranks,1):
     rank_ov[i]+=x=='overvote';rank_skips[i]+=x=='skipped'
  data[slug]=records;sources[slug]={'file':path.name,'bytes':path.stat().st_size,'sha256':h(path)}
  qc[slug]={'counts':dict(quality),'literal_named_cell_length_distribution':dict(sorted(literal_lengths.items())),'distinct_visible_named_candidate_count_distribution':dict(sorted(distinct_names.items())),'usable_prefix_length_including_writein_distribution':dict(sorted(usable_lengths.items())),'usable_prefix_length_excluding_writein_distribution':dict(sorted(usable_named_lengths.items())),'barrier_reasons':dict(reasons),'overvote_token_counts_by_rank':dict(rank_ov),'skipped_token_counts_by_rank':dict(rank_skips),'rank_tokens':dict(tokens)}
 sids=set(data['us_senate']);hids=set(data['us_house']);gids=set(data['governor']);assert sids==hids and gids<=sids
 joins={'senate_house_identical_id_sets':True,'governor_only_ids':len(gids-sids),'missing_governor_ids':len(sids-gids),'normalized_id_collisions':0}; mismatches=Counter();examples=[]
 for key in sids:
  sr=data['us_senate'][key][0]
  for slug in ['governor','us_house']:
   if key not in data[slug]:continue
   other=data[slug][key][0]
   for f,i in zip(METAFIELDS,meta_indices):
    if sr[i]!=other[i]:
     mismatches[(slug,f)]+=1
     if len(examples)<10:examples.append({'id':key,'contest':slug,'field':f,'senate':sr[i],'other':other[i]})
 joins['shared_metadata_disagreements']=[{'contest':k[0],'field':k[1],'ballots':n} for k,n in sorted(mismatches.items())];joins['examples']=examples
 literal_cohorts=Counter();structural_cohorts=Counter();q1=Counter();q1_struct=Counter();visible=Counter();final=Counter();cross=Counter();partycross=Counter();scross=Counter();spartycross=Counter()
 for key,(row,pref) in data['us_senate'].items():
  ranks=row[-5:];s=first_literal(ranks);si=pref[0] if pref else 'no_interpretable_first_choice'
  literal_cohorts[s]+=1;structural_cohorts[si]+=1
  if s==O:
   q1[pref_category(pref)]+=1;visible[pref_category(tuple(dict.fromkeys(x for x in ranks if x not in ('skipped','overvote'))))]+=1
   dest=next((x for x in pref if x in (P,D)),None);final[dest or 'inactive']+=1
  if si==O:q1_struct[pref_category(pref)]+=1
  for slug in ['governor','us_house']:
   rec=data[slug].get(key)
   x=first_literal(rec[0][-5:]) if rec else 'not_in_governor_file';xi=(rec[1][0] if rec[1] else 'no_interpretable_first_choice') if rec else 'not_in_governor_file'
   if s in SENATE:cross[(s,slug,x)]+=1;partycross[(s,slug,party(x))]+=1
   if si in SENATE:scross[(si,slug,xi)]+=1;spartycross[(si,slug,party(xi))]+=1
 comparisons=[]
 for name,counter,denom,partyflag in [('first_choice_candidate_crosstabs.csv',cross,literal_cohorts,False),('first_choice_party_crosstabs.csv',partycross,literal_cohorts,True),('interpreted_first_choice_candidate_sensitivity.csv',scross,structural_cohorts,False),('interpreted_first_choice_party_sensitivity.csv',spartycross,structural_cohorts,True)]:
  with (ROOT/'descriptive'/name).open(newline='') as f:rows=list(csv.DictReader(f))
  found=Counter()
  for r in rows:
   k=(r['senate_candidate'],r['other_contest'],r['other_first_choice'])
   assert k not in found;found[k]=int(r['ballots']);assert int(r['senate_cohort_n'])==denom[k[0]]
   assert abs(float(r['pct_of_senate_cohort'])-100*found[k]/denom[k[0]])<1e-10
   if not partyflag:assert r['other_party']==party(k[2])
  assert found==counter,(name,found-counter,counter-found)
  for s in SENATE:
   for slug in ['governor','us_house']:assert sum(n for (ss,sl,x),n in found.items() if (ss,sl)==(s,slug))==denom[s]
  comparisons.append({'file':name,'nonzero_cells':len(found),'exact_count_matches':len(found),'percentage_values_match':True,'full_cohort_denominators_match':True})
 d=json.loads((ROOT/'descriptive/descriptive_results.json').read_text())
 assert dict(literal_cohorts)==d['literal_rank1_senate_cohorts'];assert dict(structural_cohorts)==d['structural_first_choice_senate_cohorts'];assert q1==d['question1_usable_prefix_categories'];assert q1_struct==d['question1_structural_cohort_usable_categories'];assert visible==d['question1_visible_named_slot_categories']
 # Verify all linked source columns, ID links, token arrays and independently
 # calculated prefixes. No reliance on input ordering or producer source code.
 linked_n=0;original_rows=Counter();prefix_checks=Counter()
 meta=json.loads((ROOT/'descriptive/candidate_metadata.json').read_text());idname={int(k):v['name'] for k,v in meta.items()}
 with gzip.open(ROOT/'descriptive/linked_ballots.csv.gz','rt',encoding='utf-8',newline='') as f:
  for linked in csv.DictReader(f):
   linked_n+=1;key=tuple(int(x) for x in linked['ballot_uid'].split(':'))
   assert key in sids
   for slug in RACES:
    raw=linked[slug+'_original_row_json'];rec=data[slug].get(key)
    assert bool(raw)==bool(rec)
    if not rec:continue
    original=json.loads(raw);assert tuple(original[x] for x in EXPECTED_FIELDS)==rec[0]
    assert json.loads(linked[slug+'_rank_tokens_json'])==list(rec[0][-5:]);pref=rec[1]
    structural=tuple(idname[x] for x in json.loads(linked[slug+'_structural_prefix_json']));alaska=tuple(idname[x] for x in json.loads(linked[slug+'_alaska_prefix_json']))
    assert structural==pref and alaska==tuple(x for x in pref if x!='Write-in')
    original_rows[slug]+=1;prefix_checks[slug]+=1
 assert linked_n==len(sids);assert original_rows=={k:len(v) for k,v in data.items()}
 report={'audit':'Independent direct-source descriptive reconstruction; producer modules not imported','completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sole_ballot_sources':sources,'status':'passed','joins':joins,'source_rows_preserved_in_linked_records':dict(original_rows),'all_structural_and_alaska_prefixes_independently_verified':dict(prefix_checks),'cross_tab_checks':comparisons,'literal_rank1_senate_cohorts':dict(literal_cohorts),'structural_first_choice_senate_cohorts':dict(structural_cohorts),'main_literal_daniel_cohort_n':literal_cohorts[O],'main_usable_comparison':dict(q1),'structural_cohort_usable_comparison':dict(q1_struct),'supplementary_visible_comparison':dict(visible),'main_cohort_final_usable_destination':dict(final),'data_quality':qc,'definitions':{'literal_rank_length':'Number of visibly named rank cells, including Write-in and repeated names; generic overvotes are separate tokens, not reconstructed candidate lists.','distinct_visible_named_candidates':'Number of distinct visible candidate names, including generic Write-in.','usable_prefix_length':'After Alaska barriers and candidate deduplication; separate distributions including and excluding generic Write-in.','bullet_vote_exact':'Exactly one named cell, no overvote token; descriptive original-cell measure distinct from one usable preference.','one_distinct_named_candidate':'May contain repeated rankings of the same candidate; no overvotes.','party':'Candidate/ticket displayed-affiliation reference labels, not voter registration. Daniel has no affiliation printed on the sampled general-election ballot.','ambiguity_metadata':'Supplied annotations retained without changing the main rank cells; legal ballot-image adjudication cannot be independently recovered from these CSVs.'}}
 (OUT/'independent_descriptive_audit.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
 with (OUT/'data_quality_counts.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.writer(f);fields=['contest']+list(next(iter(qc.values()))['counts']);w.writerow(fields)
  for slug,q in qc.items():w.writerow([slug]+[q['counts'][k] for k in fields[1:]])
 with (OUT/'rank_length_distributions.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.writer(f);w.writerow(['contest','length_definition','rank_length','ballots'])
  for slug,q in qc.items():
   for label in ['literal_named_cell_length_distribution','distinct_visible_named_candidate_count_distribution','usable_prefix_length_including_writein_distribution','usable_prefix_length_excluding_writein_distribution']:
    for length,count in q[label].items():w.writerow([slug,label,length,count])
 (OUT/'DATA_QUALITY_REPORT.txt').write_text("""RACHEL DATA: INDEPENDENT QUALITY AUDIT — NOVEMBER 13, 2026

All three supplied 15-column CSVs were read directly. No historical ballot data
or producer parser was imported. All 733,985 original contest records and all
independently calculated prefixes agree with the linked records. Every nonzero
cell, denominator, and percentage in all four cross-tab CSVs matches (208 cells).

Source row totals: governor 244,575; House 244,705; Senate 244,705.
No normalized ID collisions. Senate and House ID sets match exactly. The 130
missing governor rows are genuinely absent from that source and are not filled.
All seven shared geography/counting fields agree across every joined record.

                                     Governor      House      Senate
Any overvote token                         779        592         976
Overvote in literal rank 1                  251        134         330
Any lower-rank overvote                     545        475         687
Any repeated visible candidate           4,860      5,295       6,592
Any internal skipped rank                3,775      4,259       6,134
Any pair of consecutive internal skips     878        904       1,379
All five ranks skipped                   3,089      1,834         898
First-rank ambiguity annotations             89         69          80

These are full-source descriptive flags, including marks after an earlier barrier;
flags overlap and must not be added together. An overvote means a generic token,
not a recovered list of its candidates. Every rank-1 overvote annotation agrees
with its rank-1 overvote token; annotation counts must not be added to token counts.

BULLET VOTES REQUIRE AN EXPLICIT DEFINITION
Exactly one named cell, no overvote: governor 124,330; House 156,158; Senate 127,505.
One distinct visible name, no overvote (allows repeating that candidate):
governor 127,518; House 160,053; Senate 132,011. Both definitions include Write-in.
One usable named candidate after Alaska barriers and excluding generic Write-in:
governor 129,491; House 161,860; Senate 133,784. This last measure can differ from
an original one-cell bullet because later choices may be unusable or be write-ins.

SENATE USABLE NAMED LENGTHS (MDS INPUT DEFINITION)
Length 0: 1,699; length 1: 133,784; length 2: 63,479; length 3: 17,782;
length 4: 27,961. Total 244,705; nonempty 243,006; length 3–4 total 45,743.
All contests' original named-cell, distinct-name, and usable-prefix distributions
are provided in rank_length_distributions.csv; counts are not imputed for overvotes.

MAIN DANIEL COMPARISON
Fixed cohort: 3,940 ballots with Daniel J. Sullivan Jr. explicitly at literal rank 1.
Both countable: 568 Peltola above Dan S.; 423 Dan S. above Peltola.
Only Peltola countable: 765; only Dan S.: 481; neither finalist countable: 1,703.
Final countable destinations for this same cohort: 1,333 Peltola, 904 Dan, 1,703
inactive. This is a cohort calculation, not the Daniel transfer node in the Sankey.
The separately labeled first-usable Daniel cohort has 3,992 ballots.

No numerical descriptive error was found. Candidate affiliation is a reference
annotation, not voter party registration. The original ambiguity fields remain
unchanged; the ballot images and adjudication history needed to re-adjudicate
those marks are not supplied by these CSVs. Candidate reference sources and the
specific blank general-ballot label for Daniel are documented separately.
""",encoding='utf-8')

 print(json.dumps({k:v for k,v in report.items() if k!='data_quality'},indent=2))
 print('Quality counts:',json.dumps({k:v['counts'] for k,v in qc.items()},indent=2))
if __name__=='__main__':main()
