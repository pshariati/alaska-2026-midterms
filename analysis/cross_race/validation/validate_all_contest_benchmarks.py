"""Validate all 54 published FairVote numerical cells using only Rachel's CSVs.

This is a reference replay, not a model fit. Published non-eliminated candidate
sets identify which stage is being compared. Counts are always derived from each
Rachel CSV's rank1-rank5. All source ballots remain in each stage's denominator;
published inactive values are compared after subtracting initial inactivity.
No original CVR, prior cleaned dataset, old ranking patterns, or old result-count
files are read. The only external inputs are frozen published HTML benchmarks.
"""
from pathlib import Path
from analysis.shared.paths import REPO_ROOT, INPUTS_ROOT, REFERENCES_ROOT, SHARED_ROOT, race_dir, model_dir, cross_race_dir, resolve_recorded_path
from collections import Counter
import csv, hashlib, html, json, re
ROOT=REPO_ROOT
CONTESTS={
    'governor': 'Alaska_20261103_US_Governor_11_11.csv',
    'us_house': 'Alaska_20261103_US_House_11_11.csv',
    'us_senate': 'Alaska_20261103_US_Senate_11_11.csv',
}

def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
    return h.hexdigest()

def parse_reference(path):
    body=path.read_text(encoding='utf-8').split('<tbody>',1)[1].split('</tbody>',1)[0]
    clean=lambda value:' '.join(html.unescape(re.sub('<[^>]+>',' ',value)).split())
    result={}
    for tr in re.findall(r'<tr\b[^>]*>(.*?)</tr>',body,re.S):
        th=re.search(r'<th\b[^>]*>(.*?)</th>',tr,re.S)
        if not th:continue
        values=[]
        for td in re.findall(r'<td\b[^>]*>(.*?)</td>',tr,re.S):
            value=re.search(r'([\d,]+)\s+(?:votes|ballots)',clean(td))
            values.append(int(value[1].replace(',','')) if value else None)
        if values:result[clean(th[1])]=values
    if len(result)!=6 or 'Inactive Ballots' not in result or any(len(v)!=4 for v in result.values()):
        raise ValueError(f'Unexpected frozen reference schema: {path}')
    return result

def structural_prefix(tokens):
    # Stop at a generic overvote or two consecutive internal skips. Preserve
    # write-in occupancy and keep only the first occurrence of a candidate.
    last=max((i for i,token in enumerate(tokens,1) if token!='skipped'),default=0)
    result=[];skips=0
    for token in tokens[:last]:
        if token=='skipped':
            skips+=1
            if skips==2:break
            continue
        skips=0
        if token=='overvote':break
        if token not in result:result.append(token)
    return tuple(result)

def write_csv(path,rows):
    with path.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)

def main():
    checks=[];records={}
    for slug,filename in CONTESTS.items():
        source=INPUTS_ROOT/filename
        benchmark=REFERENCES_ROOT/f'fairvote_{slug}.html'
        reference=parse_reference(benchmark)
        candidates=set(reference)-{'Inactive Ballots'}
        prefixes=Counter();seen=set();source_rows=0
        with source.open(encoding='utf-8-sig',newline='') as f:
            reader=csv.DictReader(f)
            if not all(f'rank{i}' in reader.fieldnames for i in range(1,6)):
                raise ValueError(f'Missing original rank columns: {source}')
            for row in reader:
                uid=row['ballotID']
                if uid in seen:raise ValueError(f'Duplicate source ballot ID: {uid}')
                seen.add(uid);source_rows+=1
                tokens=tuple(row[f'rank{i}'].strip() for i in range(1,6))
                unknown=set(tokens)-candidates-{'skipped','overvote'}
                if unknown:raise ValueError(f'Unmapped source token(s) in {filename}: {unknown}')
                prefixes[structural_prefix(tokens)]+=1
        if sum(prefixes.values())!=source_rows:raise AssertionError('Pattern aggregation changed ballot count')
        initially_inactive=prefixes.get((),0)
        round_counts=[]
        for stage in range(4):
            continuing={name for name,values in reference.items() if name!='Inactive Ballots' and values[stage] is not None}
            counts=Counter()
            for pref,n in prefixes.items():counts[next((x for x in pref if x in continuing),None)]+=n
            if sum(counts.values())!=source_rows:raise AssertionError('Ballot mass lost in replay')
            round_counts.append({'Inactive Ballots' if k is None else k:v for k,v in counts.items()})
            for candidate,values in reference.items():
                expected=values[stage]
                if expected is None:continue
                observed=counts[None]-initially_inactive if candidate=='Inactive Ballots' else counts[candidate]
                checks.append(dict(contest=slug,stage=stage+1,candidate=candidate,rachel_replay=observed,published_benchmark=expected,difference=observed-expected,match=observed==expected,source_ballots=source_rows,initially_inactive=initially_inactive,comparison_basis='Newly inactive since initial allocation' if candidate=='Inactive Ballots' else 'Candidate count on full source cohort'))
        records[slug]=dict(source_file=str(source.relative_to(REPO_ROOT)),source_sha256=sha256(source),source_ballots=source_rows,unique_ballot_ids=len(seen),initially_inactive=initially_inactive,pattern_count=len(prefixes),reference_file=str(benchmark.relative_to(REPO_ROOT)),reference_sha256=sha256(benchmark),stage_candidate_sets_role='Published non-eliminated sets align reference stages only; not model-fitting inputs',round_counts=round_counts,mass_conservation_passed=True)
    assert len(checks)==54,'Unexpected number of published numerical cells'
    reference_dir=REFERENCES_ROOT
    write_csv(reference_dir/'all_contests_benchmark_comparison.csv',checks)
    matches=sum(row['match'] for row in checks)
    record=dict(source_only='All counts recomputed from the three Rachel CSV rank1-rank5 columns only.',benchmark_role='Frozen published FairVote HTML tables are external reference values, never analysis data or fitting inputs.',cells=len(checks),matches=matches,mismatches=[row for row in checks if not row['match']],all_mass_conservation_passed=True,initial_inactive_handling='Every source ballot remains in each round. The initially inactive count is subtracted only when matching the published newly-inactive series.',contests=records)
    (reference_dir/'benchmark_validation.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(dict(cells=len(checks),matches=matches,mismatches=len(record['mismatches']),source_ballots={slug:v['source_ballots'] for slug,v in records.items()}),indent=2))
    if matches!=len(checks):raise AssertionError('Rachel replay differs from published benchmark; discrepancies retained in outputs')
    return record

if __name__=='__main__':main()
