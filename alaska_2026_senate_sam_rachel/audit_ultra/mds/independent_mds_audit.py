"""Independent Rachel-only model audit; never changes published model artifacts.

Source parsing, dissimilarities, geometric feasibility and null profiles are
implemented independently. Only the intended OG MDS fitting function is reused
for a genuine reproducibility rerun of all fifty fits.
"""
from pathlib import Path
from collections import Counter
from itertools import permutations, combinations
import csv, json, hashlib, sys, time
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
sys.path.insert(0,str(ROOT/'mds'))
from og_axis import fit_axis, FitConfig, dissimilarity, matched_null, summarize

NAMES=['Heikes, Gerald L.','Peltola, Mary','Sullivan, Daniel J. Jr.','Sullivan, Dan S.']
SOURCE=ROOT/'inputs/Alaska_20261103_US_Senate_11_11.csv'
CONFIG=FitConfig(n_runs=20,n_init=8,max_iter=1000,eps=1e-6)

def seed(*pieces):
    return int.from_bytes(hashlib.sha256('|'.join(map(str,pieces)).encode()).digest()[:4],'little')

def source_profile():
    profile=Counter(); total=0; ids=set(); tokens=set()
    with SOURCE.open(encoding='utf-8-sig',newline='') as f:
        for row in csv.DictReader(f):
            total+=1
            if row['ballotID'] in ids:raise AssertionError('Duplicate source ID')
            ids.add(row['ballotID'])
            ranks=[row['rank'+str(i)].strip() for i in range(1,6)]
            tokens.update(ranks)
            known=set(NAMES+['Write-in','skipped','overvote'])
            assert set(ranks)<=known
            # Locate all barriers at once rather than using the producer's scan.
            barriers=[i for i,t in enumerate(ranks) if t=='overvote']
            barriers += [i for i in range(4) if ranks[i:i+2]==['skipped','skipped']]
            stop=min(barriers,default=5)
            # A write-in remains occupied when finding barriers. It is removed
            # only when projecting the surviving prefix onto four named people.
            ordered=list(dict.fromkeys(t for t in ranks[:stop] if t in NAMES))
            profile[tuple(NAMES.index(t) for t in ordered)]+=1
    return profile,total,len(ids),sorted(tokens)

def independent_matrices(profile):
    adjacent=np.zeros((4,4)); together=np.zeros((4,4))
    for ranking,weight in profile.items():
        for left,right in zip(ranking,ranking[1:]):adjacent[left,right]+=weight
        for left in ranking:
            for right in ranking:together[left,right]+=weight
    similarity=np.zeros((4,4))
    for i,j in combinations(range(4),2):
        if together[i,j]:similarity[i,j]=similarity[j,i]=(adjacent[i,j]+adjacent[j,i])/(2*together[i,j])
    positive=similarity[similarity>0]
    distance=np.zeros((4,4))
    for i,j in combinations(range(4),2):distance[i,j]=distance[j,i]=1/np.sqrt(similarity[i,j]) if similarity[i,j] else 2/positive.min()
    return adjacent,together,similarity,distance

def feasible(ranking,axis):
    if len(ranking)<3:return True
    # Each open interval between all candidate-distance equality points has a
    # constant strict distance order. Include all pairs, including omitted people.
    points=sorted({0.,1.,*((float(axis[a])+float(axis[b]))/2 for a,b in combinations(range(4),2))})
    for left,right in zip(points,points[1:]):
        if right-left<=1e-12:continue
        x=(left+right)/2
        distances=[abs(x-float(axis[c])) for c in ranking]
        if all(a < b-1e-12 for a,b in zip(distances,distances[1:])):return True
    return False

def score(profile,axis):
    rows=[];total=good=informative=informative_good=0
    for length in range(1,5):
        n=sum(w for b,w in profile.items() if len(b)==length)
        g=sum(w for b,w in profile.items() if len(b)==length and feasible(b,axis))
        rows.append({'length':length,'ballots':n,'consistent':g,'gamma':g/n})
        total+=n;good+=g
        if length>=3:informative+=n;informative_good+=g
    return {'ballots':total,'empty_ballots':profile.get((),0),'informative_ballots':informative,'gamma':good/total,'gamma_informative':informative_good/informative,'by_length':rows}

def independent_null(profile,random_seed):
    # Independently enumerate each first-choice×length stratum's complete uniform
    # support and aggregate a multinomial sample. No old/null profile is an input.
    strata=Counter()
    for ranking,w in profile.items():
        if ranking:strata[(ranking[0],len(ranking))]+=w
    rng=np.random.default_rng(random_seed)
    result=Counter({():profile.get((),0)})
    for (first,length),weight in sorted(strata.items()):
        if length==1:result[(first,)]+=weight;continue
        support=list(permutations([c for c in range(4) if c!=first],length-1))
        draws=rng.multinomial(weight,[1/len(support)]*len(support))
        for tail,w in zip(support,draws):
            if w:result[(first,)+tail]+=int(w)
    return dict(result)

def validate_score(actual,saved):
    for k in ['ballots','empty_ballots','informative_ballots','gamma','gamma_informative']:
        assert actual[k]==saved[k],(k,actual[k],saved[k])
    for a,b in zip(actual['by_length'],saved['by_length']):
        for k in a:assert a[k]==b[k],(k,a,b)

def main():
    started=time.monotonic();profile,n,unique,tokens=source_profile()
    published=json.loads((ROOT/'mds/mds_results.json').read_text())
    p=json.loads((ROOT/'mds/senate_profile.json').read_text())
    assert dict(profile)=={tuple(x['ranking']):x['count'] for x in p['ballots']}
    assert n==unique==sum(profile.values())==244705
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==published['source_sha256']
    a,t,s,d=independent_matrices(profile)
    assert np.allclose(d,dissimilarity(profile,4),rtol=0,atol=1e-15)
    with (ROOT/'mds/dissimilarity_matrix.csv').open(newline='') as f:
        rows=list(csv.reader(f));assert np.allclose(d,np.array([list(map(float,x[1:])) for x in rows[1:]]),rtol=0,atol=1e-15)
    observed,diag=fit_axis(dict(profile),4,seed(20261112,'alaska_senate','observed'),CONFIG)
    assert np.allclose(observed,published['axis'],rtol=0,atol=1e-12)
    assert diag==published['fit_diagnostics']
    validate_score(score(profile,observed),published['observed'])
    audit=[];geometry_checks=0
    for draw,saved in enumerate(published['null']):
        random_seed=seed(20261112,'alaska_senate','null',draw)
        null=independent_null(profile,random_seed)
        assert null==matched_null(dict(profile),4,random_seed)
        def margins(q):return Counter({(first,length):sum(w for b,w in q.items() if b and b[0]==first and len(b)==length) for first in range(4) for length in range(1,5)})
        assert margins(null)==margins(profile)
        axis,diagnostics=fit_axis(null,4,seed(20261112,'alaska_senate','null_fit',draw),CONFIG)
        assert np.allclose(axis,saved['axis'],rtol=0,atol=1e-12)
        assert diagnostics==saved['fit_diagnostics']
        result=score(null,axis);validate_score(result,saved)
        for length in range(1,5):
            for ranking in permutations(range(4),length):
                one=summarize({ranking:1},axis)['gamma']==1
                assert one==feasible(ranking,axis)
                geometry_checks+=1
        audit.append({'draw':draw,'gamma':result['gamma'],'gamma_informative':result['gamma_informative'],'axis':list(map(float,axis)),'profile_sha256':hashlib.sha256(json.dumps([[list(b),w] for b,w in sorted(null.items())]).encode()).hexdigest(),'exact_fit_reproduced':True,'independent_score_reproduced':True,'null_margins_exact':True})
        print('Verified null',draw+1,'/49',round(time.monotonic()-started,1),'seconds',flush=True)
    summary={}
    for label,key in [('all_nonempty','gamma'),('three_or_four','gamma_informative')]:
        vals=np.array([x[key] for x in audit]);obs=published['observed'][key]
        summary[label]={'observed':obs,'random_mean':float(vals.mean()),'excess_percentage_points':float(100*(obs-vals.mean())),'random_sd':float(vals.std(ddof=1)),'random_mean_mcse_percentage_points':float(100*vals.std(ddof=1)/np.sqrt(len(vals))),'simulation_tail_fraction':(1+int((vals>=obs).sum()))/(len(vals)+1),'null_draws':len(vals)}
    with (ROOT/'mds/consistency_summary.csv').open(newline='') as f:
        rows=list(csv.DictReader(f))
    for row,label in zip(rows[:2],['all_nonempty','three_or_four']):
        for saved_key,key in [('observed_consistency','observed'),('random_mean','random_mean'),('excess_percentage_points','excess_percentage_points'),('random_sd','random_sd'),('simulation_tail_fraction','simulation_tail_fraction')]:
            assert float(row[saved_key])==summary[label][key]
    report={'status':'passed','ballot_source':SOURCE.name,'source_sha256':published['source_sha256'],'source_rows':n,'unique_ids':unique,'profile_patterns':len(profile),'profile_exactly_rederived_from_raw_CSV':True,'dissimilarity_independently_recomputed':True,'observed_and_all49_null_fits_exactly_reproduced':True,'all49_null_profiles_independently_rederived':True,'all50_consistency_summaries_independently_reproduced':True,'independent_geometry_checks':geometry_checks,'observed_axis':list(map(float,observed)),'summary':summary,'limitations':['Full-profile fit/score measures structural consistency, not held-out prediction.','Only explicitly ranked candidates constrain each ballot; one/two-name prefixes pass automatically.','49 randomized profiles produce a Monte Carlo estimate; the tail fraction cannot resolve below 0.02.','Candidate order is ranking structure, not a calibrated ideology scale.','Exact positions depend on nonmetric fitting and are not identified ideological distances.'],'seconds':time.monotonic()-started,'null_reruns':audit}
    (HERE/'mds_audit.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    print(json.dumps({k:v for k,v in report.items() if k!='null_reruns'},indent=2),flush=True)

if __name__=='__main__':main()
