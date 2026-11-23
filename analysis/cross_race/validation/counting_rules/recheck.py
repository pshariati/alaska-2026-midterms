"""Read-only reconstruction from FairVote's November 11 files.

Audit output is separate from the notebook and its existing results.
Checks independent lowest-tally eliminations, original-rank barriers,
and exclusion of unresolved write-ins before the named-candidate count.
"""
from pathlib import Path
from analysis.shared.paths import REPO_ROOT, INPUTS_ROOT, REFERENCES_ROOT, SHARED_ROOT, race_dir, model_dir, cross_race_dir, resolve_recorded_path
from collections import Counter
import csv, hashlib, json, importlib.util

BASE=Path(__file__).resolve().parent
ROOT=REPO_ROOT
from analysis.cross_race.validation import validate_archived_benchmarks as mod
expected=json.loads((REFERENCES_ROOT/'benchmark_validation.json').read_text())

def prepare(t):
    # Find barriers in original rank cells, before discarding duplicates/write-ins.
    stop=next((i for i,v in enumerate(t) if v=='overvote' or
               (i>0 and v==t[i-1]=='skipped')),len(t))
    return tuple(dict.fromkeys(v for v in t[:stop] if v!='skipped'))

def count(profile,cont):
    c=Counter({name:0 for name in cont})
    for p,w in profile.items():c[next((v for v in p if v in cont),None)]+=w
    return c

results={};matches=0
for race,old in expected['contests'].items():
    path=resolve_recorded_path(old['source_file'])
    assert hashlib.sha256(path.read_bytes()).hexdigest()==old['source_sha256']
    profile=Counter();n=0;ids=set();literal=Counter();rank1_notes=Counter()
    with path.open(encoding='utf-8-sig',newline='') as f:
        for row in csv.DictReader(f):
            t=tuple(row[f'rank{i}'] for i in range(1,6))
            assert row['ballotID'] not in ids
            ids.add(row['ballotID']);n+=1;literal[t[0]]+=1;profile[prepare(t)]+=1
            for col in ['rank1_ambiguous_candidates','rank1_overvote_candidates']:
                if row.get(col):rank1_notes[col]+=1
    assert n==old['source_ballots']
    ref=mod.parse_reference(resolve_recorded_path(old['reference_file']))
    for stage in range(4):
        cont={name for name,values in ref.items() if name!='Inactive Ballots' and values[stage] is not None}
        c=count(profile,cont)
        assert sum(c.values())==n
        assert {('Inactive Ballots' if k is None else k):v for k,v in c.items()}==old['round_counts'][stage]
        for name,values in ref.items():
            if values[stage] is None:continue
            value=c[None]-old['initially_inactive'] if name=='Inactive Ballots' else c[name]
            assert value==values[stage]
            matches+=1
    # Derive elimination order, without using published stage candidate sets.
    cont=set(ref)-{'Inactive Ballots','Write-in'};rounds=[];losers=[]
    while True:
        c=count(profile,cont);assert sum(c.values())==n
        rounds.append({('Inactive' if k is None else k):v for k,v in c.items()})
        active=sum(v for k,v in c.items() if k is not None)
        if len(cont)==2 or (len(rounds)==1 and max(c[v] for v in cont)>active/2):break
        loser=min(cont,key=lambda v:(c[v],v));losers.append(loser);cont.remove(loser)
    assert {('Inactive Ballots' if k=='Inactive' else k):v for k,v in rounds[-1].items()}==old['round_counts'][-1]
    results[race]={'rows':n,'source_sha256':old['source_sha256'],
        'literal_rank1':dict(literal),'rank1_annotation_nonempty':dict(rank1_notes),
        'exclusion_of_unresolved_writeins':True,'independently_derived_eliminations':losers,
        'named_candidate_rounds':rounds,'final_tallies_match_existing_results':True}

result={'archived_cells_rechecked':matches,'mismatches':0,'fairvote_snapshot_only':True,
        'races':results,
        'limitation':'Coded rank cells checked; cannot independently adjudicate original paper marks or hidden overvote membership from these CSVs.'}
assert matches==54
(BASE/'recheck.json').write_text(json.dumps(result,indent=2))
print(json.dumps({'archived_cells':matches,'mismatches':0,
                  'House_Nov11_final':results['us_house']['named_candidate_rounds'][-1]},indent=2))
