"""Original corrected single-axis MDS; full-profile fit/score, matched randomized tails."""
from pathlib import Path
from collections import Counter
import sys,json,csv,time,hashlib,platform,warnings
import numpy as np, scipy, sklearn
from og_axis import FitConfig,fit_axis,summarize,matched_null,seed_for,dissimilarity
ROOT=Path(__file__).resolve().parent
from ranking_rules import interpret_tokens
ORIGINAL_CORE_SHA256='b4ef0b5f1a152e655a114570e71d88791831241994c0a04d095f37363a4d001a'
IDS=[524,525,526,527]
NAMES=['Heikes, Gerald L.','Peltola, Mary','Sullivan, Daniel J. Jr.','Sullivan, Dan S.']
CONFIG=FitConfig(n_runs=20,n_init=8,max_iter=1000,eps=1e-6)
B=49
BASE=20261112

INPUT=ROOT.parent/'inputs/Alaska_20261103_US_Senate_11_11.csv'

def load_profile():
    """Every model ballot is constructed from Rachel's named rank columns."""
    profile=Counter();tokens=Counter();stops=Counter();ids=set();rows=0
    with INPUT.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        if not all(f'rank{i}' in reader.fieldnames for i in range(1,6)):
            raise ValueError('Rachel Senate CSV is missing rank columns')
        for row in reader:
            if row['ballotID'] in ids:raise ValueError('Duplicate Rachel ballotID')
            ids.add(row['ballotID']);rows+=1
            ranks=[row[f'rank{i}'] for i in range(1,6)]
            tokens.update(ranks)
            pref,reason,stop=interpret_tokens(ranks);stops[reason]+=1
            named=tuple(IDS.index(x) for x in pref if x!=373)
            profile[named]+=1
    if sum(profile.values())!=rows:raise AssertionError('Profile does not conserve Rachel rows')
    source=dict(filename=INPUT.name,sha256=hashlib.sha256(INPUT.read_bytes()).hexdigest(),rows=rows,unique_ballot_ids=len(ids),rank_token_counts=dict(tokens),prefix_stop_reasons=dict(stops),sole_ballot_source='Rachel CSV only; no official CVR-derived ballots, profiles, axes or randomized results read',candidate_id_note='Internal lookup labels assigned to candidate-name tokens; not CSV source IDs')
    (ROOT/'rachel_profile_provenance.json').write_text(json.dumps(source,indent=2))
    return dict(profile)

def margins(ballots):
    c=Counter()
    for b,w in ballots.items():c[(b[0] if b else None,len(b))]+=w
    return c

def serializable_summary(s):
    return {k:v for k,v in s.items() if k in ['ballots','empty_ballots','informative_ballots','gamma','gamma_informative','by_length']}

def main():
    started=time.monotonic();profile=load_profile()
    (ROOT/'senate_profile.json').write_text(json.dumps({'candidate_ids':IDS,'candidates':NAMES,'ballots':[dict(ranking=list(b),count=w) for b,w in sorted(profile.items())],'source_filename':INPUT.name,'source_sha256':hashlib.sha256(INPUT.read_bytes()).hexdigest(),'source_rows':sum(profile.values()),'candidate_ids_are_internal_lookup_labels':True,'cohort':'All Rachel Senate CSV rows, Alaska-interpretable prefix; generic unresolved write-in excluded only after barriers; empty prefixes retained separately'},indent=2))
    axis,diag=fit_axis(profile,4,seed_for(BASE,'alaska_senate','observed'),CONFIG)
    obs=serializable_summary(summarize(profile,axis));draws=[]
    result={'status':'running','candidate_ids':IDS,'candidates':NAMES,'axis':list(map(float,axis)),'observed':obs,'fit_diagnostics':diag,'null':draws,'base_seed':BASE,'null_draws':B,'settings':diag['settings'],'original_core_sha256':ORIGINAL_CORE_SHA256,'copied_core_sha256':hashlib.sha256((ROOT/'og_axis.py').read_bytes()).hexdigest(),'environment':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'sklearn':sklearn.__version__},'method_source':'rcv-analysis/src/rcv_core.py; copied unchanged; fullfit default in rcv-analysis/AGENTS.md','source_filename':INPUT.name,'source_sha256':hashlib.sha256(INPUT.read_bytes()).hexdigest(),'source_rows':sum(profile.values()),'candidate_ids_are_internal_lookup_labels':True,'sole_ballot_source':'Rachel Senate CSV; no previous profile, fitted axis or randomized result read','ranking_interpreter_sha256':hashlib.sha256((ROOT/'ranking_rules.py').read_bytes()).hexdigest(),'cohort':'All nonempty Alaska unresolved-writein prefix ballots; empties retained and reported; ranked-only distances, no constraints on omitted candidates.'}
    print('Observed:',obs,'axis',axis,flush=True)
    for draw in range(B):
        randomized=matched_null(profile,4,seed_for(BASE,'alaska_senate','null',draw))
        assert margins(randomized)==margins(profile)
        a,d=fit_axis(randomized,4,seed_for(BASE,'alaska_senate','null_fit',draw),CONFIG)
        s=serializable_summary(summarize(randomized,a));s['fit_diagnostics']=d;s['axis']=list(map(float,a));s['draw']=draw;draws.append(s)
        (ROOT/'mds_results.json').write_text(json.dumps(result,indent=2,allow_nan=False))
        print(f'Fresh Rachel null {draw+1}/{B}; elapsed {time.monotonic()-started:.1f} s',flush=True)
    summary=[]
    for label,field,n in [('All nonempty','gamma',obs['ballots']),('Three or four named ranks','gamma_informative',obs['informative_ballots'])]:
        values=np.array([x[field] for x in draws]);observed=obs[field]
        summary.append(dict(group=label,ballots=n,observed_consistency=observed,random_mean=float(values.mean()),excess_percentage_points=100*(observed-values.mean()),random_sd=float(values.std(ddof=1)),random_mcse=float(values.std(ddof=1)/np.sqrt(B)),random_2_5pct=float(np.quantile(values,.025)),random_97_5pct=float(np.quantile(values,.975)),simulation_tail_fraction=(1+int((values>=observed).sum()))/(B+1),random_draws=B))
    for length in obs['by_length']:
        m=length['length'];vals=np.array([next(y['gamma'] for y in x['by_length'] if y['length']==m) for x in draws])
        summary.append(dict(group=f'Exactly {m} named ranks',ballots=length['ballots'],observed_consistency=length['gamma'],random_mean=float(vals.mean()),excess_percentage_points=100*(length['gamma']-vals.mean()),random_sd=float(vals.std(ddof=1)),random_mcse=float(vals.std(ddof=1)/np.sqrt(B)),random_2_5pct=float(np.quantile(vals,.025)),random_97_5pct=float(np.quantile(vals,.975)),simulation_tail_fraction=(1+int((vals>=length['gamma']).sum()))/(B+1),random_draws=B))
    with (ROOT/'consistency_summary.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
    with (ROOT/'candidate_axis.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['candidate_id','candidate','axis_position']);w.writeheader();w.writerows(dict(candidate_id=i,candidate=n,axis_position=float(a)) for i,n,a in zip(IDS,NAMES,axis))
    with (ROOT/'dissimilarity_matrix.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['candidate']+NAMES)
        for name,row in zip(NAMES,dissimilarity(profile,4)):w.writerow([name]+list(map(float,row)))
    result['summary']=summary;result['status']='complete';result['seconds']=time.monotonic()-started
    (ROOT/'mds_results.json').write_text(json.dumps(result,indent=2,allow_nan=False));print(json.dumps(summary,indent=2),flush=True)
    return result
if __name__=='__main__':main()
