"""Fresh full-profile OG1D fits for Governor and House, with matched null fits."""
from pathlib import Path
from collections import Counter
from itertools import permutations
import argparse,csv,datetime,hashlib,json,platform,sys,time
import numpy as np
import scipy,sklearn

ROOT=Path(__file__).resolve().parents[1]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'common'))
from data import RACES,profile,sha256
from og_axis import FitConfig,fit_axis,summarize,matched_null,seed_for,pair_matrices,dissimilarity,prefix_flags

BASE=20261112
CONFIG=FitConfig(n_runs=20,n_init=8,max_iter=1000,eps=1e-6)
STRONG=FitConfig(n_runs=100,n_init=16,max_iter=1000,eps=1e-6)
B=49
CORE_SHA='b4ef0b5f1a152e655a114570e71d88791831241994c0a04d095f37363a4d001a'
ANCHORS={'governor':(538,539),'us_house':(530,528)}

def write_json(path,value):
    path.write_text(json.dumps(value,indent=2,allow_nan=False))

def write_csv(path,rows):
    with path.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def margins(ballots):
    result=Counter()
    for ballot,weight in ballots.items():result[(ballot[0] if ballot else None,len(ballot))]+=weight
    return result

def trimmed(summary):
    return {key:summary[key] for key in ['ballots','empty_ballots','informative_ballots','gamma','gamma_informative','by_length']}

def oracle(ranking,axis):
    """Independent distance-order sweep over all open midpoint cells."""
    if len(ranking)<2:return True
    cuts=sorted({0.,1.}|{(float(axis[a])+float(axis[b]))/2 for a in range(len(axis)) for b in range(a)})
    for left,right in zip(cuts,cuts[1:]):
        if right-left<=1e-12:continue
        voter=(left+right)/2
        distances=[abs(voter-float(axis[c])) for c in ranking]
        if all(a<b for a,b in zip(distances,distances[1:])):return True
    return False

def independent_score(ballots,axis):
    counts={'ballots':0,'consistent':0,'informative_ballots':0,'informative_consistent':0}
    for ballot,weight in ballots.items():
        if not ballot:continue
        passed=oracle(ballot,axis)
        counts['ballots']+=weight;counts['consistent']+=weight*passed
        if len(ballot)>=3:
            counts['informative_ballots']+=weight;counts['informative_consistent']+=weight*passed
    counts['gamma']=counts['consistent']/counts['ballots']
    counts['gamma_informative']=counts['informative_consistent']/counts['informative_ballots']
    return counts

def display_coords(slug,axis):
    ids=RACES[slug]['ids'];left,right=ANCHORS[slug]
    reflected=bool(axis[ids.index(left)]>axis[ids.index(right)])
    return (1-axis if reflected else axis.copy()),reflected

def observed(slug):
    folder=HERE/slug;folder.mkdir(exist_ok=True)
    ballots,source=profile(slug);names=RACES[slug]['names'];ids=RACES[slug]['ids']
    axis,diagnostics=fit_axis(ballots,4,seed_for(BASE,slug,'observed'),CONFIG)
    display,reflected=display_coords(slug,axis)
    score=trimmed(summarize(ballots,axis));independent=independent_score(ballots,axis)
    assert independent['gamma']==score['gamma'] and independent['gamma_informative']==score['gamma_informative']
    write_csv(folder/'candidate_axis.csv',[{'candidate_id':cid,'candidate':name,'axis_position':float(x),'display_axis_position':float(y),'display_reflected':reflected} for cid,name,x,y in zip(ids,names,axis,display)])
    write_json(folder/'profile.json',{'candidate_ids':ids,'candidates':names,'ballots':[{'ranking':list(b),'count':w} for b,w in sorted(ballots.items())],**source})
    adjacent,together=pair_matrices(ballots,4)
    for file,matrix in [('adjacency_matrix.csv',adjacent),('coranking_matrix.csv',together),('dissimilarity_matrix.csv',dissimilarity(ballots,4))]:
        with (folder/file).open('w',encoding='utf-8',newline='') as f:
            writer=csv.writer(f);writer.writerow(['candidate']+names)
            for name,row in zip(names,matrix):writer.writerow([name]+list(map(float,row)))
    result={'status':'observed_complete','candidate_ids':ids,'candidates':names,'axis':list(map(float,axis)),
        'display_axis':list(map(float,display)),'display_reflected':reflected,
        'display_orientation_rule':'Kreiss-Tomkins left of Wilson' if slug=='governor' else 'Hill left of Begich',
        'orientation_interpretation':'Reflection only; axes are separately fitted and not a common calibrated ideology metric.',
        'observed':score,'fit_diagnostics':diagnostics,'null':[],'base_seed':BASE,'null_draws':B,
        'settings':diagnostics['settings'],'original_core_sha256':CORE_SHA,
        'copied_core_sha256':sha256(ROOT/'common/og_axis.py'),
        'environment':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'sklearn':sklearn.__version__},
        'method_source':'Pure corrected OG method copied unchanged from prior audited code; no old ballot data or models used.',
        'source_filename':source['source_filename'],'source_sha256':source['source_sha256'],'source_rows':source['source_rows'],
        'candidate_ids_are_internal_lookup_labels':True,
        'sole_ballot_source':'Rachel November11 CSV for this contest; countable-prefix transformation from common/data.py',
        'ranking_interpreter_sha256':sha256(ROOT/'common/data.py'),
        'cohort':'All nonempty Alaska-countable named prefixes; generic write-in excluded only after barriers; empty prefixes retained separately.'}
    write_json(folder/'mds_results.json',result)
    print(slug,'OBSERVED AXIS READY',result['axis'],'display',result['display_axis'],'gamma',score['gamma'],'gamma3+',score['gamma_informative'],flush=True)
    return ballots,result

def complete(slug,ballots,result):
    started=time.monotonic();folder=HERE/slug;result['status']='running'
    draw_profiles=[]
    for draw in range(B):
        randomized=matched_null(ballots,4,seed_for(BASE,slug,'null',draw));assert margins(randomized)==margins(ballots)
        axis,diag=fit_axis(randomized,4,seed_for(BASE,slug,'null_fit',draw),CONFIG)
        summary=trimmed(summarize(randomized,axis));independent=independent_score(randomized,axis)
        assert summary['gamma']==independent['gamma'] and summary['gamma_informative']==independent['gamma_informative']
        result['null'].append({**summary,'fit_diagnostics':diag,'axis':list(map(float,axis)),'draw':draw})
        draw_profiles.append({'draw':draw,'rankings':[{'ranking':list(b),'count':w} for b,w in sorted(randomized.items())],
            'exact_first_choice_by_length_margins_preserved':True})
        write_json(folder/'mds_results.json',result)
        print(slug,f'fresh null {draw+1}/{B}; {time.monotonic()-started:.1f}s',flush=True)
    summary=[];obs=result['observed'];draws=result['null']
    for label,field,n in [('All nonempty','gamma',obs['ballots']),('Three or four named ranks','gamma_informative',obs['informative_ballots'])]:
        values=np.array([d[field] for d in draws]);observed_value=obs[field]
        summary.append({'group':label,'ballots':n,'observed_consistency':observed_value,'random_mean':float(values.mean()),
            'excess_percentage_points':100*(observed_value-values.mean()),'random_sd':float(values.std(ddof=1)),
            'random_mcse':float(values.std(ddof=1)/np.sqrt(B)),'random_2_5pct':float(np.quantile(values,.025)),
            'random_97_5pct':float(np.quantile(values,.975)),
            'simulation_tail_fraction':(1+int((values>=observed_value).sum()))/(B+1),'random_draws':B})
    for row in obs['by_length']:
        length=row['length'];values=np.array([next(y['gamma'] for y in d['by_length'] if y['length']==length) for d in draws])
        summary.append({'group':f'Exactly {length} named ranks','ballots':row['ballots'],'observed_consistency':row['gamma'],
            'random_mean':float(values.mean()),'excess_percentage_points':100*(row['gamma']-values.mean()),
            'random_sd':float(values.std(ddof=1)),'random_mcse':float(values.std(ddof=1)/np.sqrt(B)),
            'random_2_5pct':float(np.quantile(values,.025)),'random_97_5pct':float(np.quantile(values,.975)),
            'simulation_tail_fraction':(1+int((values>=row['gamma']).sum()))/(B+1),'random_draws':B})
    strong_axis,strong_diag=fit_axis(ballots,4,seed_for(BASE,slug,'observed'),STRONG)
    strong_score=trimmed(summarize(ballots,strong_axis));axes=[result['axis'],list(map(float,strong_axis))]+[d['axis'] for d in draws]
    checked=0
    for coords in axes:
        for length in range(1,5):
            rankings=np.array(list(permutations(range(4),length)),dtype=int)
            flags=prefix_flags(np.array(coords)[rankings])[:,-1]
            for ranking,flag in zip(rankings,flags):
                assert oracle(tuple(map(int,ranking)),coords)==bool(flag)
                checked+=1
    verification={'status':'passed','source_sha256':result['source_sha256'],'axes_checked':len(axes),
        'independent_feasibility_rankings_checked':checked,'all49_null_margins_exact':True,
        'all_observed_and_randomized_scores_independently_checked':True,
        'strong_fit_axis':list(map(float,strong_axis)),'strong_fit_diagnostics':strong_diag,
        'strong_fit_gamma':strong_score['gamma'],'strong_fit_gamma_informative':strong_score['gamma_informative'],
        'main_fit_gamma':obs['gamma'],'main_fit_gamma_informative':obs['gamma_informative'],
        'change_overall_percentage_points':100*(strong_score['gamma']-obs['gamma']),
        'change_three_plus_percentage_points':100*(strong_score['gamma_informative']-obs['gamma_informative']),
        'interpretation':'Stronger observed-only fit sensitivity; main real/null comparison uses identical20x8budgets.'}
    result.update(status='complete',summary=summary,seconds=time.monotonic()-started,
        completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    write_json(folder/'mds_results.json',result);write_csv(folder/'consistency_summary.csv',summary)
    write_json(folder/'null_profiles.json',{'source_sha256':result['source_sha256'],'base_seed':BASE,'draws':draw_profiles})
    write_json(folder/'mds_verification.json',verification)
    write_json(folder/'method_provenance.json',{'ballot_source_filename':result['source_filename'],
        'ballot_source_sha256':result['source_sha256'],'core_sha256':CORE_SHA,'core_copied_unchanged':True,
        'ranking_interpreter_sha256':result['ranking_interpreter_sha256'],'base_seed':BASE,
        'seed_rule':'seed_for(base_seed,contest_slug,observed/null/null_fit[,draw])',
        'settings':result['settings'],'null_draws':B,'strong_observed_settings':strong_diag['settings'],
        'cohort':'Full eligible contest profile fitted and scored; each randomized profile freshly fitted and scored.',
        'orientation':{'raw_coordinates_retained':True,'display_reflected':result['display_reflected'],
            'display_rule':result['display_orientation_rule']}})
    print(slug,'COMPLETE',json.dumps(summary[:2]),flush=True)
    return result

def main(only=None):
    assert sha256(ROOT/'common/og_axis.py')==CORE_SHA
    slugs=[only] if only else ['governor','us_house']
    pending={slug:observed(slug) for slug in slugs}
    return {slug:complete(slug,*pending[slug]) for slug in slugs}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--only',choices=['governor','us_house'])
    args=parser.parse_args();main(args.only)
