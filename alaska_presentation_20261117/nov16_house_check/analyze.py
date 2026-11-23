"""Independent November 16 House replay; standard library only.

No Rachel CSVs or previous analytical outputs are inputs. Benchmark values are
used only after raw extraction and tabulation. The original ZIP is never edited.
"""
from pathlib import Path
from collections import Counter, defaultdict
import csv, gzip, hashlib, json, zipfile, datetime

BASE=Path(__file__).resolve().parent
SOURCE=BASE.parent/'new_data_review/public_cvr_retrieved_20261117/CVR_Export.zip'
SHA='1db9e9279e163c4051d85e6db2e69ad3b66d810839102b5079d158df1d84312a'
SOURCE_URL='https://www.elections.alaska.gov/enr/26GENR/results/CVR_Export.zip'
BENCHMARK_URL='https://rcvis.com/ve/alaska-us-house-preliminary-results-as-of-11-16?vistype=tabular-candidate-by-round'
RULES_URL='https://www.elections.alaska.gov/election-results/e/?id=26genr'
WRITEIN_RULE_URL='https://www.akleg.gov/statutesPDF/aac%20Title%206.pdf'

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def prepare(ranks):
    last=max((i+1 for i,x in enumerate(ranks) if x),default=0)
    if not last:return (), 'blank'
    pref=[];skips=0
    for cell in ranks[:last]:
        if not cell:
            skips+=1
            if skips==2:return tuple(pref),'two_consecutive_skips'
            continue
        skips=0
        if len(cell)>1:return tuple(pref),'overvote'
        c=cell[0]
        if c not in pref:pref.append(c)
    return tuple(pref),'end_of_ranks'

def direct_choice(ranks,continuing):
    # Independent per-round scan of original rank cells; no prepared prefix.
    previous_blank=False
    for cell in ranks:
        if len(cell)>1:return None
        if not cell:
            if previous_blank:return None
            previous_blank=True
        else:
            previous_blank=False
            if cell[0] in continuing:return cell[0]
    return None

def tally(profile,continuing):
    counts=Counter({c:0 for c in continuing})
    for pref,n in profile.items():counts[next((c for c in pref if c in continuing),None)]+=n
    return counts

def replay(profile,rank_patterns,candidates,total):
    cont=set(candidates);rounds=[];losers=[]
    while True:
        counts=tally(profile,cont)
        direct=Counter({c:0 for c in cont})
        for ranks,n in rank_patterns.items():direct[direct_choice(ranks,cont)]+=n
        assert counts==direct,'Prepared-prefix and raw-rank-scan tallies disagree'
        assert sum(counts.values())==total,'Ballot conservation failed'
        active=total-counts[None]
        rounds.append({'continuing':sorted(cont),'counts':dict(counts),'active':active})
        first_majority=len(rounds)==1 and max(counts[c] for c in cont)>active/2
        if len(cont)==2 or first_majority:break
        minimum=min(counts[c] for c in cont)
        tied=[c for c in cont if counts[c]==minimum]
        assert len(tied)==1,'Tie requires Alaska lot decision; do not invent it'
        loser=tied[0];losers.append(loser);cont.remove(loser)
    return rounds,losers

def write_csv(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    assert digest(SOURCE)==SHA,'Unexpected source version'
    stats=Counter();state_counts=Counter();stop_counts=Counter();profile=Counter();patterns=Counter();seen=set();inventory=[]
    with zipfile.ZipFile(SOURCE) as z:
        assert len(z.namelist())==len(set(z.namelist()))
        manifests={n:json.loads(z.read(n)) for n in z.namelist() if n.endswith('Manifest.json')}
        (BASE/'manifests.json').write_text(json.dumps(manifests,indent=2))
        contests={c['Id']:c for c in manifests['ContestManifest.json']['List']}
        cid=next(i for i,c in contests.items() if c['Description']=='U.S. Representative')
        assert contests[cid]['NumOfRanks']==5
        candidates={c['Id']:c for c in manifests['CandidateManifest.json']['List'] if c['ContestId']==cid}
        assert len(candidates)==5
        writeins={i for i,c in candidates.items() if c['Type']=='WriteIn'}
        assert len(writeins)==1
        wi=next(iter(writeins));regular=set(candidates)-writeins
        names={i:c['Description'] for i,c in candidates.items()}
        eligible=defaultdict(set)
        for r in manifests['BallotTypeContestManifest.json']['List']:eligible[r['BallotTypeId']].add(r['ContestId'])
        fields=['ballot_uid','source_file','session_index','selected_state','ballot_type_id','precinct_portion_id',
                *[f'rank{i}_ids_json' for i in range(1,6)],'valid_prefix_ids_json','stop_reason','raw_current_house_contests_json']
        with gzip.open(BASE/'house_ballots.csv.gz','wt',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
            files=sorted((n for n in z.namelist() if n.startswith('CvrExport_') and n.endswith('.json')),
                         key=lambda n:int(n.removeprefix('CvrExport_').removesuffix('.json')))
            for name in files:
                raw=z.read(name);doc=json.loads(raw)
                assert doc['Version']=='5.17.18.1' and doc['ElectionId']=='2026 General Election'
                inventory.append({'member':name,'sha256':hashlib.sha256(raw).hexdigest(),'sessions':len(doc['Sessions'])})
                for index,s in enumerate(doc['Sessions']):
                    stats['sessions']+=1
                    uid=':'.join(str(s[k]) for k in ['TabulatorId','BatchId','RecordId'])
                    assert uid not in seen, f'Duplicate ballot session {uid}'
                    seen.add(uid)
                    states=[(k,v) for k,v in s.items() if isinstance(v,dict) and 'Cards' in v]
                    for k,v in states:state_counts[k+':'+str(v.get('IsCurrent'))]+=1
                    current=[(k,v) for k,v in states if v.get('IsCurrent') is True]
                    assert len(current)==1,f'Unresolved current state {uid}'
                    sk,st=current[0];stats['selected_'+sk]+=1
                    bt=st['BallotTypeId'];assert bt in eligible
                    cs=[c for card in st['Cards'] for c in card.get('Contests',[]) if c['Id']==cid]
                    if cid not in eligible[bt]:
                        assert not cs;stats['house_ineligible']+=1;continue
                    stats['house_ballots']+=1
                    if not cs:stats['eligible_missing_house_contest']+=1
                    if len(cs)>1:stats['multiple_house_contest_instances']+=1
                    marks=[m for c in cs for m in c.get('Marks',[])]
                    ranks=[set() for _ in range(5)]
                    for m in marks:
                        assert type(m['IsVote']) is bool and type(m['IsAmbiguous']) is bool
                        assert type(m['Rank']) is int and 1<=m['Rank']<=5 and m['CandidateId'] in candidates
                        stats['recorded_marks']+=1
                        stats['accepted_marks' if m['IsVote'] else 'nonvote_marks']+=1
                        if m['IsAmbiguous']:stats['ambiguous_accepted_marks' if m['IsVote'] else 'ambiguous_nonvote_marks']+=1
                        if m['IsVote']:
                            cell=ranks[m['Rank']-1]
                            if m['CandidateId'] in cell:stats['duplicate_same_candidate_same_rank_records']+=1
                            cell.add(m['CandidateId'])
                    ranks=tuple(tuple(sorted(cell)) for cell in ranks)
                    pref,reason=prepare(ranks);stop_counts[reason]+=1
                    patterns[ranks]+=1;profile[pref]+=1
                    stats['overvote_ballots']+=any(len(cell)>1 for cell in ranks)
                    ids=[c for cell in ranks for c in cell]
                    stats['repeated_candidate_ballots']+=len(ids)!=len(set(ids))
                    writer.writerow({'ballot_uid':uid,'source_file':name,'session_index':index,'selected_state':sk,
                        'ballot_type_id':bt,'precinct_portion_id':st['PrecinctPortionId'],
                        **{f'rank{i}_ids_json':json.dumps(ranks[i-1]) for i in range(1,6)},
                        'valid_prefix_ids_json':json.dumps(pref),'stop_reason':reason,
                        'raw_current_house_contests_json':json.dumps(cs,separators=(',',':'))})
                if len(inventory)%400==0:print(f'Processed {len(inventory)}/{len(files)} CVR files',flush=True)
    total=stats['house_ballots'];assert sum(profile.values())==total
    display,display_losers=replay(profile,patterns,candidates,total)
    initial=display[0]['counts'];leader=max(initial[c] for c in regular);w=initial[wi]
    # 6 AAC 25.071: defeat all write-ins if W<L and L-W >= .005*(L+W).
    # Exact integer arithmetic avoids rounding at the legal boundary.
    defeat_writeins=w<leader and 200*(leader-w)>=leader+w
    assert defeat_writeins,'Write-ins require individual resolution; public CVR lacks written names'
    official,official_losers=replay(profile,patterns,regular,total)
    assert display[-1]['counts']==official[-1]['counts']
    assert display_losers[0]==wi
    assert [r['counts'] for r in display[1:]]==[r['counts'] for r in official]
    # Benchmark numbers transcribed from Sam's screenshot / its exact RCVis table.
    benchmark={528:[134732,134771,136814,138417],530:[117843,117929,120011,130450],
               529:[22258,22282,23208,None],531:[7503,7537,None,None],374:[435,None,None,None]}
    pct={528:[47.65,47.70,48.86,51.48],530:[41.67,41.74,42.86,48.52],
         529:[7.87,7.89,8.29,None],531:[2.65,2.67,None,None],374:[.15,None,None,None]}
    inactive_ref=[0,252,2738,13904]
    assert set(benchmark)==set(candidates) and len(display)==4
    initially_inactive=initial.get(None,0);comparison=[];rows=[]
    for number,r in enumerate(display,1):
        for candidate in sorted(r['continuing']):
            observed=r['counts'][candidate];expected=benchmark[candidate][number-1]
            percent=100*observed/r['active'];expected_pct=pct[candidate][number-1]
            comparison.append({'round':number,'candidate':names[candidate],'recomputed_votes':observed,
                'screenshot_votes':expected,'difference':observed-expected,'votes_match':observed==expected,
                'recomputed_percent':round(percent,2),'screenshot_percent':expected_pct,
                'percent_match':round(percent,2)==expected_pct})
            rows.append({'display_round':number,'candidate':names[candidate],'votes':observed,
                         'percent_of_continuing':percent,'active_ballots':r['active'],
                         'inactive_total':r['counts'].get(None,0),
                         'newly_inactive_since_display_round1':r['counts'].get(None,0)-initially_inactive})
    inactive_comparison=[{'round':i+1,'recomputed_newly_inactive':r['counts'].get(None,0)-initially_inactive,
                         'published_newly_inactive':inactive_ref[i],
                         'match':r['counts'].get(None,0)-initially_inactive==inactive_ref[i]} for i,r in enumerate(display)]
    write_csv(BASE/'comparison_to_sam.csv',comparison)
    write_csv(BASE/'house_rounds.csv',rows)
    write_csv(BASE/'inactive_comparison.csv',inactive_comparison)
    (BASE/'rank_patterns.json').write_text(json.dumps([{'rank_ids':ranks,'ballots':n} for ranks,n in patterns.items()]))
    def round_json(rounds):
        return [{'continuing':[names[c] for c in r['continuing']],
                 'counts':{names.get(c,'Inactive'):n for c,n in r['counts'].items()},'active_ballots':r['active']} for r in rounds]
    result={'status':'computed','source_sha256':SHA,'source_url':SOURCE_URL,'benchmark_url':BENCHMARK_URL,
        'rules_url':RULES_URL,'writein_regulation_url':WRITEIN_RULE_URL,
        'snapshot':'November 16, 2026','generated_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'stats':dict(stats),'state_counts':dict(state_counts),'stop_reasons':dict(stop_counts),
        'source_CVR_files':len(inventory),'initially_inactive':initially_inactive,
        'display_eliminations':[names[c] for c in display_losers],
        'official_settings_eliminations':[names[c] for c in official_losers],
        'writein_test':{'leading_regular_initial_votes':leader,'combined_writein_initial_votes':w,
                       'all_writeins_defeated_under_6_AAC_25_071':defeat_writeins},
        'display_rounds':round_json(display),'official_settings_rounds':round_json(official),
        'candidate_vote_cells':len(comparison),'candidate_vote_matches':sum(r['votes_match'] for r in comparison),
        'candidate_percentage_matches':sum(r['percent_match'] for r in comparison),
        'inactive_cells':len(inactive_comparison),'inactive_matches':sum(r['match'] for r in inactive_comparison),
        'all_rounds_ballot_conservation':True,'independent_raw_rank_scan_matches_all_rounds':True,
        'writein_exclusion_gives_identical_subsequent_rounds':True,
        'mismatches':[r for r in comparison if not r['votes_match'] or not r['percent_match']],
        'scope':'Separate raw-state-CVR House check; does not modify Rachel inputs, the notebook or slides; unofficial snapshot replay, not certified results.'}
    result['status']='exact_match' if not result['mismatches'] and result['inactive_matches']==4 else 'discrepancies_retained'
    (BASE/'results.json').write_text(json.dumps(result,indent=2))
    (BASE/'source_members.json').write_text(json.dumps(inventory,indent=2))
    print(json.dumps({k:result[k] for k in ['status','stats','initially_inactive','display_rounds','candidate_vote_matches','candidate_percentage_matches','inactive_matches','mismatches']},indent=2))
    return result

if __name__=='__main__':main()
