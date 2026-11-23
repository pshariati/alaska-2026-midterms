"""Independent source-level reconstruction of confusion/conditional-bound outputs.

Does not import the producer or shared counting parser.
"""
from pathlib import Path
from collections import Counter,defaultdict
import csv,gzip,json,hashlib

from analysis.shared.paths import INPUTS_ROOT, race_dir
OUT=race_dir('us_senate')/'rankings'
SOURCE=INPUTS_ROOT/'Alaska_20261103_US_Senate_11_11.csv'
J='Sullivan, Daniel J. Jr.';D='Sullivan, Dan S.';P='Peltola, Mary';H='Heikes, Gerald L.';W='Write-in'
DEST={P:'Peltola',D:'Dan S. Sullivan',None:'Inactive'}
COHORTS=['literal_rank1_daniel','structural_first_daniel','daniel_node_after_writein_exclusion']
SHORT={P:'Mary Peltola',D:'Dan S. Sullivan',J:'Daniel J. Sullivan Jr.',H:'Gerald Heikes',W:'Write-in',None:'Inactive'}

def prefix(tokens):
    end=len(tokens)
    for i in range(len(tokens)):
        if tokens[i]=='overvote' or (i and tokens[i-1]==tokens[i]=='skipped'):
            end=i;break
    seen=set();out=[]
    for token in tokens[:end]:
        if token!='skipped' and token not in seen:out.append(token);seen.add(token)
    return tuple(out)

def first(pref,continuing):return next((x for x in pref if x in continuing),None)

def named_rcv(profile):
    """Fresh full-source IRV after unresolved-WI exclusion; derive losers anew."""
    continuing={H,P,J,D};rounds=[];order=[];first_majority=None
    while True:
        current=Counter()
        for pref,n in profile.items():
            if n:current[first(pref,continuing)]+=n
        active=sum(n for candidate,n in current.items() if candidate is not None)
        if not rounds:
            first_majority=next((candidate for candidate in continuing if current[candidate]>active/2),None)
        rounds.append(current)
        if len(continuing)==2 or (len(rounds)==1 and first_majority is not None):break
        loser=min(continuing,key=lambda x:(current[x],x));order.append(loser);continuing.remove(loser)
    return rounds,order,first_majority

def main():
    refs=json.loads((OUT/'confusion_results.json').read_text())
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==refs['source_sha256']
    all_prefs=Counter();subset_prefs={c:Counter() for c in COHORTS};literal={};cohort_original={c:{} for c in COHORTS}
    summaries={c:{'final':Counter(),'routes':Counter(),'noD':0,'noD_P':0,'noD_noP':0,'noDvisible':0,
        'noDvisible_OV':0,'noDvisible_noOV':0} for c in COHORTS}
    raw_patterns=Counter();rows=0
    with SOURCE.open(encoding='utf-8-sig',newline='') as f:
        for index,row in enumerate(csv.DictReader(f)):
            rows+=1;t=tuple(row[f'rank{i}'] for i in range(1,6));pref=prefix(t)
            all_prefs[pref]+=1;named=tuple(x for x in pref if x!=W)
            membership=[t[0]==J,bool(pref) and pref[0]==J,bool(named) and named[0]==J]
            for cohort,yes in zip(COHORTS,membership):
                if not yes:continue
                subset_prefs[cohort][named]+=1;cohort_original[cohort][row['ballotID']]=row
                q=summaries[cohort];final=first(pref,{P,D});q['final'][DEST[final]]+=1
                if final==D:q['routes']['after_Daniel_to_Heikes_then_incumbent' if first(pref,{P,D,H})==H else 'after_Daniel_direct_to_incumbent']+=1
                if D not in pref:q['noD']+=1;q['noD_P' if P in pref else 'noD_noP']+=1
                if D not in t:
                    q['noDvisible']+=1;q['noDvisible_OV' if 'overvote' in t else 'noDvisible_noOV']+=1
            if membership[0]:
                literal[row['ballotID']]={'row':row,'pref':pref,'tokens':t,'index':index}
                raw_patterns[t]+=1
    assert rows==refs['source_rows']==244705
    for cohort,q in summaries.items():
        r=refs['cohorts'][cohort]
        assert r['ballots']==sum(subset_prefs[cohort].values())
        assert r['final_destinations']==q['final']
        assert r['actual_reach_incumbent_routes']==q['routes']
        assert r['no_incumbent_in_countable_prefix']['total']==q['noD']
        assert r['no_incumbent_in_countable_prefix']['Peltola_countable']==q['noD_P']
        assert r['no_incumbent_in_countable_prefix']['Peltola_not_countable']==q['noD_noP']
        omission=r['no_incumbent_visibly_named_in_five_cells']
        assert omission['ballots']==q['noDvisible']
        assert omission['source_visibility_partition']['coded_absence_no_overvote']==q['noDvisible_noOV']
        assert omission['source_visibility_partition']['hidden_membership_unknown']==q['noDvisible_OV']
    with (OUT/'daniel_first_raw_rank_patterns.csv').open(newline='') as f:
        for row in csv.DictReader(f):assert raw_patterns[tuple(row[f'rank{i}'] for i in range(1,6))]==int(row['ballots'])
    named_all=Counter()
    for pref,n in all_prefs.items():named_all[tuple(x for x in pref if x!=W)]+=n
    with (OUT/'all_senate_usable_permutations.csv').open(newline='') as f:
        for row in csv.DictReader(f):
            # Decode IDs from immutable local reference names, independently.
            ids={524:H,525:P,526:J,527:D}
            pref=tuple(ids[i] for i in json.loads(row['candidate_ids_json']))
            assert named_all[pref]==int(row['all_Senate_source_ballots'])
            for cohort in COHORTS:assert subset_prefs[cohort][pref]==int(row[cohort+'_ballots'])
    # Independently derive the actual replay order from each round's lowest tally.
    continuing={H,P,J,D,W};order=[];allocations=[]
    while True:
        current=Counter()
        for pref,n in all_prefs.items():current[first(pref,continuing)]+=n
        assert sum(current.values())==rows;allocations.append(current)
        if len(continuing)==2:break
        loser=min(continuing,key=lambda x:(current[x],x));order.append(loser);continuing.remove(loser)
    assert order==[W,J,H]
    for expected,observed in zip(refs['stage_totals_and_allocations'],allocations):
        assert expected=={SHORT[k]:v for k,v in observed.items()}
    full_final=Counter({DEST[k]:v for k,v in allocations[-1].items()})
    scenario_names=[];dynamic_counterfactuals=[]
    for scenario in refs['conditional_upper_bound_scenarios']:
        name=scenario['scenario']
        checks={
            'no_countable_incumbent':lambda r:D not in r['pref'],
            'no_visible_incumbent':lambda r:D not in r['tokens'],
            'no_visible_incumbent_no_overvote':lambda r:D not in r['tokens'] and 'overvote' not in r['tokens'],
            'no_visible_incumbent_with_overvote_unknown':lambda r:D not in r['tokens'] and 'overvote' in r['tokens'],
            'both_sullivans_countable':lambda r:D in r['pref'],
            'adjacent_sullivans_countable':lambda r:tuple(x for x in r['pref'] if x!=W)[:2]==(J,D),
            'all_literal_Daniel_first':lambda r:True}
        subset=[r for r in literal.values() if checks[name](r)]
        before=Counter(DEST[first(r['pref'],{P,D})] for r in subset)
        assert scenario['subset_ballots']==len(subset)
        # Counterfactual: incumbent goes first on each designated ballot.
        after=full_final.copy();counterfactual_profile=all_prefs.copy()
        for r in subset:
            old=DEST[first(r['pref'],{P,D})];modified=(D,)+tuple(x for x in r['pref'] if x not in (D,J))
            new=DEST[first(modified,{P,D})];after[old]-=1;after[new]+=1
            counterfactual_profile[r['pref']]-=1;counterfactual_profile[modified]+=1
        assert sum(after.values())==rows
        assert scenario['maximum_additional_incumbent_votes_in_this_scenario']==after['Dan S. Sullivan']-full_final['Dan S. Sullivan']
        assert scenario['maximum_Dan_minus_Peltola_margin_increase']==(after['Dan S. Sullivan']-after['Peltola'])-(full_final['Dan S. Sullivan']-full_final['Peltola'])
        assert scenario['hypothetical_final_Dan']==after['Dan S. Sullivan']
        assert scenario['hypothetical_final_Peltola']==after['Peltola']
        assert scenario['hypothetical_final_inactive']==after['Inactive']
        dynamic_rounds,dynamic_order,first_majority=named_rcv(counterfactual_profile)
        assert first_majority is None,'New first-round majority changes tally reporting'
        assert dynamic_order==[J,H]
        assert all(sum(round_counts.values())==rows for round_counts in dynamic_rounds)
        dynamic_final={DEST[k]:v for k,v in dynamic_rounds[-1].items()}
        assert dynamic_final==after
        dynamic_counterfactuals.append({'scenario':name,'all_source_rows_reallocated':rows,
            'modified_literal_Daniel_ballots':len(subset),
            'elimination_order_after_writein_exclusion':[SHORT[x] for x in dynamic_order],
            'first_round_majority':first_majority,'final_counts':dynamic_final,
            'all_rounds':[{'Inactive' if k is None else SHORT[k]:v for k,v in counts.items()} for counts in dynamic_rounds],
            'interpretation':'Conditional fixed-ballot D-first reassignment, not an estimated real-world outcome.'})
        scenario_names.append(name)
    verified_records={}
    for cohort,file in [(COHORTS[0],'daniel_literal_first_ballots.csv.gz'),(COHORTS[2],'daniel_actual_node_ballots.csv.gz')]:
        n=0;seen=set()
        with gzip.open(OUT/file,'rt',encoding='utf-8',newline='') as f:
            for row in csv.DictReader(f):
                uid=row['source_ballotID'];assert uid not in seen;seen.add(uid);n+=1
                original=cohort_original[cohort][uid]
                assert json.loads(row['original_source_row_json'])==original
                assert json.loads(row['countable_prefix_json'])==list(prefix(tuple(original[f'rank{i}'] for i in range(1,6))))
        assert n==len(cohort_original[cohort]);verified_records[file]=n
    with (OUT/'anonymous_example_ballots.csv').open(newline='') as f:
        for example in csv.DictReader(f):
            original=literal[example['source_ballotID']]
            assert int(example['source_row_index_zero_based'])==original['index']
            assert json.loads(example['original_source_row_json'])==original['row']
    result={'status':'passed','source_sha256':refs['source_sha256'],'source_rows':rows,
        'actual_elimination_order_independently_derived':[SHORT[x] for x in order],
        'all_observed_named_permutations_checked':len(named_all),'conditional_scenarios_independently_reassigned':scenario_names,
        'preserved_original_source_rows_verified':verified_records,'all_three_cohort_summaries_independently_reproduced':True,
        'full_source_dynamic_RCV_counterfactuals':dynamic_counterfactuals,
        'all_round_totals_conserved':True,'stable_source_examples_checked':True}
    (OUT/'confusion_verification.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2));return result

if __name__=='__main__':main()
