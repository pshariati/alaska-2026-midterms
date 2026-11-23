"""Recheck carried-forward descriptive tables and Sankey from Rachel CSVs."""
from pathlib import Path
from collections import Counter,defaultdict
import csv,json,sys,math
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'common'))
from data import RACES,read_rows,normalized_id,countable_tokens,sha256

def main():
 metadata=json.loads((ROOT/'common/candidate_metadata.json').read_text())
 party={x['name']:x['party_label'] for x in metadata.values()}
 sources={};firsts={};seen={}
 for slug in RACES:
  firsts[slug]={};seen[slug]=set()
  for _,row,tokens in read_rows(slug):
   uid=normalized_id(row['ballotID']);assert uid not in seen[slug];seen[slug].add(uid)
   firsts[slug][uid]={'skipped':'blank_rank1','overvote':'overvote_rank1'}.get(tokens[0],tokens[0])
  sources[slug]={'rows':len(seen[slug]),'sha256':RACES[slug]['sha256']}
 assert seen['us_senate']==seen['us_house'] and seen['governor']<=seen['us_senate']
 assert len(seen['us_senate']-seen['governor'])==130
 cohort=Counter();candidate_counts=Counter();party_counts=Counter();q1=Counter();stage_counts=[Counter() for _ in range(4)];links=Counter()
 senate=RACES['us_senate']['names'];P,J,D=senate[1],senate[2],senate[3]
 sets=[set(senate)|{'Write-in'},set(senate),{senate[0],P,D},{P,D}]
 lookup=dict(zip(senate,RACES['us_senate']['ids']))
 flowkeys={senate[0]:'heikes',P:'peltola',J:'daniel_sullivan',D:'dan_sullivan','Write-in':'writein',None:''}
 for _,row,tokens in read_rows('us_senate'):
  uid=normalized_id(row['ballotID']);first=firsts['us_senate'][uid]
  pref,_,_=countable_tokens(tokens)
  allocations=[next((x for x in pref if x in names),None) for names in sets]
  for stage,x in enumerate(allocations):stage_counts[stage][flowkeys[x]]+=1
  for stage,(a,b) in enumerate(zip(allocations,allocations[1:]),1):links[stage,flowkeys[a],flowkeys[b]]+=1
  if first in lookup:
   cid=lookup[first];cohort[cid]+=1
   for race in ['governor','us_house']:
    other=firsts[race].get(uid,'not_in_governor_file')
    candidate_counts[cid,race,other]+=1
    party_counts[cid,race,party.get(other,other)]+=1
  if first==J:
   p=pref.index(P) if P in pref else None;d=pref.index(D) if D in pref else None
   key='neither_explicitly_ranked' if p is None and d is None else 'senator_only_explicitly_ranked' if p is None else 'peltola_only_explicitly_ranked' if d is None else 'peltola_above_senator_both_ranked' if p<d else 'senator_above_peltola_both_ranked'
   q1[key]+=1
 d=json.loads((ROOT/'completed/descriptive/descriptive_results.json').read_text())
 assert dict(q1)==d['question1_usable_prefix_categories'] and cohort[526]==3940
 checked=0
 for file,expected in [('first_choice_candidate_crosstabs.csv',candidate_counts),('first_choice_party_crosstabs.csv',party_counts)]:
  actual={}
  with (ROOT/'completed/descriptive'/file).open(newline='') as f:
   for row in csv.DictReader(f):
    cid=int(row['senate_candidate_id']);key=(cid,row['other_contest'],row['other_first_choice'])
    actual[key]=int(row['ballots']);assert int(row['senate_cohort_n'])==cohort[cid]
    assert math.isclose(float(row['pct_of_senate_cohort']),100*actual[key]/cohort[cid],abs_tol=1e-10)
  assert actual==dict(expected),file
  checked+=len(actual)
 with (ROOT/'completed/flows/senate_flow_nodes.csv').open(newline='') as f:
  nodes=list(csv.DictReader(f))
 for row in nodes:assert int(row['ballots'])==stage_counts[int(row['stage'])-1][row['candidate_key']]
 with (ROOT/'completed/flows/senate_flow_links.csv').open(newline='') as f:
  actual={(int(row['stage_from']),row['source_candidate_key'],row['target_candidate_key']):int(row['ballots']) for row in csv.DictReader(f)}
 assert actual==dict(links)
 assert all(sum(counts.values())==244705 for counts in stage_counts)
 result={'status':'passed','source_policy':'Only three package Rachel CSVs; no previous ballot profiles used',
  'sources':sources,'literal_senate_cohorts':dict(cohort),'main_usable_comparison':dict(q1),
  'candidate_and_party_cross_tab_cells_verified':checked,'missing_governor_rows':130,
  'flow_nodes_verified':len(nodes),'flow_links_verified':len(actual),
  'all_stage_counts_conserved':True,'final_counts':dict(stage_counts[-1]),
  'role':'Revalidation of completed work, not a new interpretation or model fit.'}
 (ROOT/'validation/completed_results_revalidation.json').write_text(json.dumps(result,indent=2))
 print(json.dumps(result,indent=2));return result

if __name__=='__main__':main()
