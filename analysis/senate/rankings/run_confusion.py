"""Operational transfer/permutation counts and conditional name-confusion ceilings.

FairVote's Senate CSV is the sole ballot input. No ranking establishes voter intent.
"""
from pathlib import Path
from collections import Counter,defaultdict
import csv,gzip,hashlib,json,sys,datetime

from analysis.shared.paths import SHARED_ROOT, race_dir
OUT=race_dir('us_senate')/'rankings'
from analysis.shared.data import read_rows,countable_tokens,normalized_id,RACES,source_path,sha256

J='Sullivan, Daniel J. Jr.';D='Sullivan, Dan S.';P='Peltola, Mary';H='Heikes, Gerald L.';W='Write-in'
SHORT={J:'Daniel J. Sullivan Jr.',D:'Dan S. Sullivan',P:'Mary Peltola',H:'Gerald Heikes',W:'Write-in',None:'Inactive'}
DEST={P:'Peltola',D:'Dan S. Sullivan',None:'Inactive'}
ID={H:524,P:525,J:526,D:527,W:373}
STAGES=[{H,P,J,D,W},{H,P,J,D},{H,P,D},{P,D}]
COHORTS=['literal_rank1_daniel','structural_first_daniel','daniel_node_after_writein_exclusion']

def oracle(tokens):
    """Independent earliest-barrier selection; producer uses a sequential scan."""
    last=max((i for i,x in enumerate(tokens) if x!='skipped'),default=-1)
    barriers=[i for i,x in enumerate(tokens) if x=='overvote']
    barriers += [i for i in range(len(tokens)-1)
                 if tokens[i]==tokens[i+1]=='skipped' and i+1<last]
    stop=min(barriers,default=len(tokens))
    return tuple(dict.fromkeys(x for x in tokens[:stop] if x not in ['skipped','overvote']))

def allocations(pref):return tuple(next((x for x in pref if x in continuing),None) for continuing in STAGES)
def pattern_text(pref):return ' > '.join(SHORT[x] for x in pref) or '(empty)'
def flags(tokens,pref):
    named=tuple(x for x in pref if x!=W)
    return {
        'incumbent_named_anywhere_in_rank_cells':D in tokens,
        'peltola_named_anywhere_in_rank_cells':P in tokens,
        'incumbent_in_countable_prefix':D in pref,
        'peltola_in_countable_prefix':P in pref,
        'lower_overvote_token': 'overvote' in tokens[1:],
        'any_overvote_token':'overvote' in tokens,
        'both_sullivans_countable':J in pref and D in pref,
        'adjacent_sullivans_in_named_prefix':any(a==J and b==D for a,b in zip(named,named[1:])),
        'literal_rank2_incumbent':tokens[1]==D,
        'peltola_before_incumbent_countable':P in pref and D in pref and pref.index(P)<pref.index(D),
        'incumbent_before_peltola_countable':P in pref and D in pref and pref.index(D)<pref.index(P),
    }

def absent_status(tokens,pref):
    if D in pref:return 'incumbent_countable'
    if D in tokens:return 'incumbent_visible_only_beyond_counting_barrier'
    if 'overvote' in tokens:return 'incumbent_not_visible_hidden_overvote_membership_unknown'
    return 'incumbent_not_named_in_coded_cells_no_overvote'

def write_csv(file,rows):
    if not rows:raise ValueError('No output rows for '+file)
    with (OUT/file).open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def summarize(records):
    n=len(records);finals=Counter();visibility=Counter();missing=Counter();routes=Counter();tag_counts=Counter()
    raw_omission=Counter();raw_omission_to=Counter();comparison=Counter();barriers=Counter()
    for r in records:
        tokens=r['tokens'];pref=r['pref'];path=r['path'];f=r['flags'];dest=path[-1]
        finals[DEST[dest]]+=1;barriers[r['reason']]+=1
        for key,value in f.items():tag_counts[key]+=value
        visibility[absent_status(tokens,pref)]+=1
        if D not in pref:
            missing['total']+=1;missing['Peltola_countable' if P in pref else 'Peltola_not_countable']+=1
            missing['visible_incumbent_beyond_barrier' if D in tokens else 'no_visible_incumbent_with_overvote' if 'overvote' in tokens else 'no_visible_incumbent_no_overvote']+=1
        if D not in tokens:
            key='hidden_membership_unknown' if 'overvote' in tokens else 'coded_absence_no_overvote'
            raw_omission[key]+=1
            raw_omission_to[key+'__'+DEST[dest]]+=1
            raw_omission['Peltola_visibly_named' if P in tokens else 'Peltola_not_visibly_named']+=1
            raw_omission['Peltola_countable' if P in pref else 'Peltola_not_countable']+=1
        if dest==D:
            routes['after_Daniel_to_Heikes_then_incumbent' if path[2]==H else 'after_Daniel_direct_to_incumbent']+=1
        comparison['Peltola_above_Dan_both_countable' if f['peltola_before_incumbent_countable'] else
                   'Dan_above_Peltola_both_countable' if f['incumbent_before_peltola_countable'] else
                   'Peltola_only_countable' if P in pref else 'Dan_only_countable' if D in pref else 'Neither_finalist_countable']+=1
    assert sum(finals.values())==n
    assert sum(routes.values())==finals['Dan S. Sullivan']
    assert sum(comparison.values())==n
    return {'ballots':n,'final_destinations':dict(finals),'countable_finalist_comparison':dict(comparison),
        'incumbent_visibility_status':dict(visibility),'no_incumbent_in_countable_prefix':dict(missing),
        'no_incumbent_visibly_named_in_five_cells':{'ballots':raw_omission['coded_absence_no_overvote']+raw_omission['hidden_membership_unknown'],
            'source_visibility_partition':{'coded_absence_no_overvote':raw_omission['coded_absence_no_overvote'],'hidden_membership_unknown':raw_omission['hidden_membership_unknown']},
            'Peltola_visibly_named':raw_omission['Peltola_visibly_named'],'Peltola_not_visibly_named':raw_omission['Peltola_not_visibly_named'],
            'Peltola_countable':raw_omission['Peltola_countable'],'Peltola_not_countable':raw_omission['Peltola_not_countable'],
            'split_by_current_destination':dict(raw_omission_to),
            'interpretation':'No visible name is a coded-data property. Generic overvotes may hide that candidate; no identities are imputed.'},
        'actual_reach_incumbent_routes':dict(routes),'operational_pattern_flags':dict(tag_counts),
        'first_barrier_reasons':dict(barriers),
        'rank1_ambiguous_annotation_nonempty':sum(bool(r['row']['rank1_ambiguous_candidates']) for r in records),
        'rank1_overvote_annotation_nonempty':sum(bool(r['row']['rank1_overvote_candidates']) for r in records)}

def scenario(name,description,subset,full_final):
    current=Counter(DEST[r['path'][-1]] for r in subset)
    n=len(subset);from_p=current['Peltola'];from_inactive=current['Inactive'];already=current['Dan S. Sullivan']
    gain=from_p+from_inactive;margin=2*from_p+from_inactive
    after={'Peltola':full_final['Peltola']-from_p,'Dan S. Sullivan':full_final['Dan S. Sullivan']+gain,
           'Inactive':full_final['Inactive']-from_inactive}
    assert sum(after.values())==sum(full_final.values())
    return {'scenario':name,'designated_subset':description,'subset_ballots':n,
        'already_reaches_incumbent':already,'currently_Peltola':from_p,'currently_inactive':from_inactive,
        'maximum_additional_incumbent_votes_in_this_scenario':gain,
        'maximum_Dan_minus_Peltola_margin_increase':margin,
        'assumption_dependent_additional_Dan_vote_range_json':json.dumps([0,gain]),
        'assumption_dependent_margin_increase_range_json':json.dumps([0,margin]),
        'hypothetical_final_Dan':after['Dan S. Sullivan'],'hypothetical_final_Peltola':after['Peltola'],
        'hypothetical_final_inactive':after['Inactive'],'hypothetical_Dan_minus_Peltola_margin':after['Dan S. Sullivan']-after['Peltola'],
        'assumption':'Ceiling: every designated ballot intended incumbent Dan first and would be reassigned to him, with outsider removed and incumbent deduplicated; all other ballots and ranking behavior fixed. Zero remains compatible with no confusion.',
        'scope':'Conditional ceiling for this specified source cohort, not an identified number of confused voters or a universal causal bound.'}

def ballot_record(r):
    out={'source_ballotID':r['row']['ballotID'],'normalized_ballot_id':normalized_id(r['row']['ballotID']),
        'source_row_index_zero_based':r['index'],'source_csv_line_one_based_including_header':r['index']+2,
        **{f'rank{i+1}':token for i,token in enumerate(r['tokens'])},
        'countable_prefix_json':json.dumps(r['pref']),'named_four_candidate_prefix_json':json.dumps([x for x in r['pref'] if x!=W]),
        'first_barrier_reason':r['reason'],'barrier_rank':r['barrier_rank'],
        'initial_with_generic_writein':SHORT[r['path'][0]],'after_writein_exclusion':SHORT[r['path'][1]],
        'after_Daniel_elimination':SHORT[r['path'][2]],'after_Heikes_elimination':SHORT[r['path'][3]],
        'incumbent_visibility_status':absent_status(r['tokens'],r['pref']),
        **r['flags'],'rank1_ambiguous_candidates':r['row']['rank1_ambiguous_candidates'],
        'rank1_overvote_candidates':r['row']['rank1_overvote_candidates'],
        'original_source_row_json':json.dumps(r['row'],ensure_ascii=False,separators=(',',':'))}
    return out

def main():
    start=datetime.datetime.now(datetime.timezone.utc).isoformat()
    cohorts={c:[] for c in COHORTS};all_patterns=Counter();full_final=Counter();all_allocations=[Counter() for _ in STAGES]
    source_n=0;ids=set();prefix_checked=0;raw_patterns=Counter();records=[]
    for index,row,tokens in read_rows('us_senate'):
        uid=normalized_id(row['ballotID']);assert uid not in ids;ids.add(uid);source_n+=1
        pref,reason,barrier_rank=countable_tokens(tokens)
        assert pref==oracle(tokens),(row['ballotID'],pref,oracle(tokens));prefix_checked+=1
        path=allocations(pref)
        for i,a in enumerate(path):all_allocations[i][SHORT[a]]+=1
        full_final[DEST[path[-1]]]+=1
        named=tuple(x for x in pref if x!=W);all_patterns[named]+=1
        member=[tokens[0]==J,bool(pref) and pref[0]==J,path[1]==J]
        if any(member):
            record={'index':index,'row':row,'tokens':tokens,'pref':pref,'path':path,'reason':reason,
                    'barrier_rank':barrier_rank,'flags':flags(tokens,pref)}
            records.append(record)
            for c,yes in zip(COHORTS,member):
                if yes:cohorts[c].append(record)
            if member[0]:raw_patterns[tokens,pref,reason,barrier_rank]+=1
    assert source_n==244705 and len(ids)==source_n
    assert [len(cohorts[c]) for c in COHORTS]==[3940,3992,4055]
    assert full_final=={'Peltola':119933,'Dan S. Sullivan':119223,'Inactive':5549}
    summaries={name:summarize(subset) for name,subset in cohorts.items()}
    literal=cohorts[COHORTS[0]];lit=summaries[COHORTS[0]]
    assert lit['final_destinations']=={'Peltola':1333,'Dan S. Sullivan':904,'Inactive':1703}
    assert lit['no_incumbent_in_countable_prefix']['total']==2468
    assert lit['countable_finalist_comparison']=={'Peltola_above_Dan_both_countable':568,
        'Dan_above_Peltola_both_countable':423,'Peltola_only_countable':765,
        'Dan_only_countable':481,'Neither_finalist_countable':1703}

    # Exhaustive observed named-prefix permutations, with every cohort represented.
    named_counts={c:Counter(tuple(x for x in r['pref'] if x!=W) for r in subset) for c,subset in cohorts.items()}
    permutation_rows=[]
    for pref,n in sorted(all_patterns.items(),key=lambda z:(len(z[0]),z[0])):
        a=allocations(pref)
        row={'named_usable_permutation':pattern_text(pref),'candidate_ids_json':json.dumps([ID[x] for x in pref]),
            'named_length':len(pref),'all_Senate_source_ballots':n,
            **{c+'_ballots':named_counts[c][pref] for c in COHORTS},
            'after_Daniel_elimination':SHORT[a[2]],'final_destination':SHORT[a[3]],
            'both_sullivans_usable':J in pref and D in pref,
            'adjacent_sullivans_in_named_prefix':any(x==J and y==D for x,y in zip(pref,pref[1:]))}
        permutation_rows.append(row)
    write_csv('all_senate_usable_permutations.csv',permutation_rows)
    daniel_rows=[row for row in permutation_rows if row[COHORTS[0]+'_ballots']]
    write_csv('daniel_first_usable_permutations.csv',daniel_rows)
    assert sum(row[COHORTS[0]+'_ballots'] for row in daniel_rows)==3940
    write_csv('daniel_first_raw_rank_patterns.csv',[{
        **{f'rank{i+1}':x for i,x in enumerate(tokens)},'ballots':n,
        'countable_prefix_json':json.dumps(pref),'first_barrier_reason':reason,'barrier_rank':rank,
        'final_destination':SHORT[allocations(pref)[-1]]}
        for (tokens,pref,reason,rank),n in sorted(raw_patterns.items(),key=lambda z:z[0][0])])

    omission_rows=[]
    for c,subset in cohorts.items():
        cross=Counter((absent_status(r['tokens'],r['pref']),P in r['pref'],P in r['tokens'],DEST[r['path'][-1]]) for r in subset)
        for (status,p_countable,p_visible,dest),n in sorted(cross.items()):
            omission_rows.append({'cohort':c,'cohort_n':len(subset),'incumbent_status':status,
                'Peltola_countable':p_countable,'Peltola_visibly_named':p_visible,'current_final_destination':dest,
                'ballots':n,'percent_of_cohort':100*n/len(subset)})
    write_csv('incumbent_omission_by_Peltola.csv',omission_rows)

    # Clearly designated overlapping scenario sets; no inference of actual confusion.
    scenario_sets=[
        ('no_countable_incumbent','Literal-rank1 Daniel; incumbent absent from Alaska-countable prefix',[r for r in literal if D not in r['pref']]),
        ('no_visible_incumbent','Literal-rank1 Daniel; no explicit incumbent name in any of five coded rank cells',[r for r in literal if D not in r['tokens']]),
        ('no_visible_incumbent_no_overvote','Literal-rank1 Daniel; no incumbent name and no overvote token',[r for r in literal if D not in r['tokens'] and 'overvote' not in r['tokens']]),
        ('no_visible_incumbent_with_overvote_unknown','Literal-rank1 Daniel; no visible incumbent name but generic overvote may hide it',[r for r in literal if D not in r['tokens'] and 'overvote' in r['tokens']]),
        ('both_sullivans_countable','Literal-rank1 Daniel; incumbent also in countable prefix',[r for r in literal if D in r['pref']]),
        ('adjacent_sullivans_countable','Literal-rank1 Daniel; incumbent immediately follows outsider in named prefix',[r for r in literal if r['flags']['adjacent_sullivans_in_named_prefix']]),
        ('all_literal_Daniel_first','Every literal-rank1 Daniel ballot',literal),
    ]
    scenario_rows=[scenario(name,description,subset,full_final) for name,description,subset in scenario_sets]
    write_csv('conditional_upper_bound_scenarios.csv',scenario_rows)
    assert scenario_rows[0]['maximum_additional_incumbent_votes_in_this_scenario']==2468
    assert scenario_rows[0]['maximum_Dan_minus_Peltola_margin_increase']==3233
    assert scenario_rows[-1]['maximum_additional_incumbent_votes_in_this_scenario']==3036
    assert scenario_rows[-1]['maximum_Dan_minus_Peltola_margin_increase']==4369

    for c,filename in [(COHORTS[0],'daniel_literal_first_ballots.csv.gz'),(COHORTS[2],'daniel_actual_node_ballots.csv.gz')]:
        with gzip.open(OUT/filename,'wt',encoding='utf-8',newline='') as f:
            writer=None
            for r in cohorts[c]:
                out=ballot_record(r)
                if writer is None:writer=csv.DictWriter(f,fieldnames=list(out));writer.writeheader()
                writer.writerow(out)

    # Real, anonymous source examples, selected by pattern rather than row number.
    predicates=[
        ('direct_to_incumbent',lambda r:r['path'][2]==D and r['path'][3]==D),
        ('via_Heikes_to_incumbent',lambda r:r['path'][2]==H and r['path'][3]==D),
        ('Peltola_before_countable_incumbent',lambda r:P in r['pref'] and D in r['pref'] and r['path'][3]==P),
        ('Peltola_countable_incumbent_absent',lambda r:P in r['pref'] and D not in r['tokens'] and 'overvote' not in r['tokens']),
        ('neither_finalist_countable',lambda r:r['path'][3] is None and not r['flags']['any_overvote_token']),
        ('incumbent_visible_beyond_barrier',lambda r:D in r['tokens'] and D not in r['pref']),
        ('hidden_overvote_membership_unknown',lambda r:D not in r['tokens'] and r['flags']['any_overvote_token']),
    ]
    examples=[]
    for label,predicate in predicates:
        example=next((r for r in literal if predicate(r)),None)
        if example:
            row=ballot_record(example);row={'illustration':label,**row}
            examples.append(row)
    write_csv('anonymous_example_ballots.csv',examples)

    result={
        'status':'passed','source_filename':RACES['us_senate']['filename'],
        'source_sha256':RACES['us_senate']['sha256'],'source_rows':source_n,
        'source_policy':'Only the supplied FairVote Senate CSV; original source strings retained. No original CVR or earlier ballot extracts read.',
        'cohorts':summaries,'all_source_final_destinations':dict(full_final),
        'all_source_Dan_minus_Peltola_margin':full_final['Dan S. Sullivan']-full_final['Peltola'],
        'stage_totals_and_allocations':[dict(x) for x in all_allocations],
        'conditional_upper_bound_scenarios':scenario_rows,
        'ballot_34_status':'Not identified: Sam supplied no stable ballotID/source reference. The 34th CSV row is not assumed to be ballot #34. Anonymous examples are separately identified by source ballotID and explicit row index.',
        'example_ballots_csv':'anonymous_example_ballots.csv','named_permutation_rows':len(permutation_rows),
        'literal_Daniel_named_permutations':len(daniel_rows),
        'source_row_annotation_note':'Ancillary rank1 ambiguity/overvote annotations remain unchanged; coded rank tokens govern the main interpretation. No ballot-image adjudication is inferred.',
        'interpretation':[
            'Reaching incumbent Dan after an outsider-first choice is an observable RCV transfer; it is not proof the voter was confused.',
            'Adjacent or separated similarly named candidates, an omitted incumbent, or a Peltola preference may each be sincere. Operational categories are possible scenarios, not diagnoses.',
            'No incumbent in usable prefix differs from no incumbent explicitly named in original rank cells. A generic overvote can hide names and any excluded later preferences cannot transfer.',
            'The designated lost-support ceiling assumes every ballot in the stated subset intended incumbent Dan first. Actual confusion could be zero; this is not an identified causal effect.',
            'Under the fixed-ballot reassignment scenario, switching an existing Peltola destination to Dan improves his margin by 2; recovering an inactive ballot improves it by 1; votes already reaching Dan add 0.',
            'Scenario sets overlap and must not be added. The literal 3,940 cohort, structural 3,992 cohort and actual 4,055 Daniel node are distinct.',
        ],
        'verification':{'source_rows_independently_prefix_checked':prefix_checked,'unique_normalized_ids':len(ids),
            'all_stage_totals_conserved':all(sum(x.values())==source_n for x in all_allocations),
            'literal_cohort_partition_checked':True,'permutation_totals_checked':True,'all_scenario_total_ballots_conserved':True},
        'code_sha256':sha256(Path(__file__)),'shared_interpreter_sha256':sha256(SHARED_ROOT/'data.py'),
        'started_utc':start,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    (OUT/'confusion_results.json').write_text(json.dumps(result,indent=2))
    write_notes(result)
    print(json.dumps({'status':result['status'],'cohorts':summaries,'conditional_bounds':scenario_rows},indent=2))
    return result

def write_notes(result):
    literal=result['cohorts'][COHORTS[0]]
    lines=['CONFUSION QUESTIONS: WHAT THE RANKINGS CAN AND CANNOT ESTABLISH','',
        'Sources and cohorts','FairVote November 11 Senate CSV only; source SHA256 recorded. Earlier raw CVRs are not read.',
        'Main cohort: 3,940 literal-rank-1 Daniel J. Sullivan Jr. ballots. Separate first-structural-choice',
        'cohort: 3,992; after unresolved write-in exclusion, Daniel actual node: 4,055. The latter',
        'includes write-in transfers and is the relevant node for the replay Sankey.','',
        '1. What could be described as RCV preserving incumbent support?',
        f"Within 3,940 literal-outsider-first ballots, {literal['final_destinations']['Dan S. Sullivan']} actually reach incumbent Dan under Alaska rules.",
        'Routes: '+json.dumps(literal['actual_reach_incumbent_routes'])+'.',
        'These observed transfers preserve recorded lower-ranked incumbent support. We cannot say',
        'that every such voter confused the two Sullivans, or that this is a causal confusion count.',
        'Permutations with adjacent J>Dan or separated J>Heikes>Dan illustrate mechanisms.',
        'If Peltola appears before Dan in the usable prefix, Peltola retains the ballot when both',
        'finalists continue; a still-lower Dan ranking does not transfer past a continuing Peltola.','',
        '2. Which patterns might be consistent with confusion?',
        'A name-swap explanation is compatible with some J-first ballots naming Dan next, naming',
        'him after Heikes, or omitting him. All are also compatible with sincere preferences.',
        'No ranking permutation by itself proves confusion, protest, strategy or voter intent.',
        'The operational permutation and scenario sets are explicit and overlapping.','',
        '3. How to count possible lost support and Peltola preferences?',
        'No countable incumbent: 2,468, of which 765 have a countable Peltola preference and 1,703 have',
        'neither finalist countable. This is a rule-based availability category, not literal',
        'absence from every original mark. The detailed source-visibility split is in',
        'incumbent_omission_by_Peltola.csv. No visible incumbent with a generic overvote remains',
        'partially observed; names hidden inside overvotes are never reconstructed.','',
        'If ALL 2,468 designated ballots intended incumbent Dan first and every other ballot stayed',
        'fixed, he could gain at most 2,468 additional votes in that scenario. The margin improves',
        'by 3,233: 765 switches from Peltola count twice; 1,703 recoveries from inactive count once.',
        'This conditional ceiling is not an estimate or universal identified upper bound.',
        'Broader all-3,940 outsider-first reassignment: 904 already reach Dan; at most 3,036 additional',
        'votes and 4,369 margin improvement. The scenario would require assuming away all sincere',
        'outsider/Peltola/nontransfer choices in that cohort. Actual confusion could be zero.',
        'No claim is made about confusion originating in other first-choice cohorts.','',
        '4. Ballot #34 and reproducible examples',
        result['ballot_34_status'],
        'anonymous_example_ballots.csv supplies actual anonymous source IDs, zero-based source',
        'indices, original rank cells, metadata annotations, countable prefixes and stage paths.',
        'Those chosen examples are illustrations; they are not silently equated with Sam\'s ballot #34.','',
        'Files','daniel_first_usable_permutations.csv: every observed named-prefix pattern in the',
        'literal cohort; all_senate_usable_permutations.csv: every observed named prefix, all sources.',
        'daniel_first_raw_rank_patterns.csv: original token patterns, including irregularities.',
        'daniel_literal_first_ballots.csv.gz and daniel_actual_node_ballots.csv.gz preserve the',
        'entire original 15-column row plus separately derived interpretations and classifications.',
        'conditional_upper_bound_scenarios.csv: explicit, overlapping fixed-ballot hypotheticals.',
        'Run: python3 confusion/run_confusion.py. No file outside this delivered FairVote source',
        'and pure shared parser is required.','']
    (OUT/'NOTES.txt').write_text('\n'.join(lines))

if __name__=='__main__':main()
