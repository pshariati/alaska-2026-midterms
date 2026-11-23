"""Independent raw-source reconstruction and geometric scoring for new axes."""
from pathlib import Path
from analysis.shared.paths import REPO_ROOT, INPUTS_ROOT, REFERENCES_ROOT, SHARED_ROOT, race_dir, model_dir, cross_race_dir, resolve_recorded_path
from collections import Counter
from itertools import permutations
import csv,hashlib,json,sys
import numpy as np

ROOT=REPO_ROOT
HERE=Path(__file__).resolve().parent
from analysis.shared.data import RACES  # Metadata only; no producer parser or scorer is imported.

def direct_profile(slug):
    metadata=RACES[slug];source=INPUTS_ROOT/metadata['filename'];profile=Counter();ids=set();rows=0
    assert hashlib.sha256(source.read_bytes()).hexdigest()==metadata['sha256']
    with source.open(encoding='utf-8-sig',newline='') as f:
        for row in csv.DictReader(f):
            rows+=1
            uid=tuple(int(x) for x in row['ballotID'].rstrip('_').split('_'))
            assert uid not in ids;ids.add(uid)
            tokens=[row['rank'+str(i)] for i in range(1,6)]
            last=max((i for i,x in enumerate(tokens) if x!='skipped'),default=-1)
            barriers=[i for i,x in enumerate(tokens) if x=='overvote']
            barriers.extend(i for i in range(len(tokens)-1) if tokens[i]==tokens[i+1]=='skipped' and i+1<last)
            end=min(barriers,default=len(tokens))
            named=list(dict.fromkeys(x for x in tokens[:end] if x not in ['Write-in','skipped']))
            profile[tuple(metadata['names'].index(x) for x in named)]+=1
    return profile,rows

def interval(ranking,axis):
    """Derive all pairwise half-spaces, unlike the producer's adjacent recursion."""
    lo,hi=0.,1.
    for i,a in enumerate(ranking):
        for b in ranking[i+1:]:
            pa,pb=axis[a],axis[b]
            midpoint=(pa+pb)/2
            if pa<pb:hi=min(hi,midpoint)
            elif pa>pb:lo=max(lo,midpoint)
            else:return None
    return (lo,hi) if hi-lo>1e-12 else None

def direct_score(profile,axis):
    counts=Counter();good=Counter()
    for ranking,weight in profile.items():
        if not ranking:continue
        m=len(ranking);counts[m]+=weight
        if interval(ranking,axis) is not None:good[m]+=weight
    total=sum(counts.values());informative=sum(v for m,v in counts.items() if m>=3)
    return {'gamma':sum(good.values())/total,
        'gamma_informative':sum(v for m,v in good.items() if m>=3)/informative,
        'by_length':{m:{'ballots':counts[m],'consistent':good[m],'gamma':good[m]/counts[m]} for m in counts}}

def main():
    records={}
    for slug in ['governor','us_house']:
        folder=model_dir(slug);result=json.loads((folder/'mds_results.json').read_text())
        assert result['status']=='complete' and len(result['null'])==49
        profile,rows=direct_profile(slug)
        saved=json.loads((folder/'profile.json').read_text())
        assert profile==Counter({tuple(x['ranking']):x['count'] for x in saved['ballots']})
        assert rows==result['source_rows']==sum(profile.values())
        adjacent=np.zeros((4,4));together=np.zeros((4,4))
        for b,w in profile.items():
            for a,c in zip(b,b[1:]):adjacent[a,c]+=w
            for a in b:
                for c in b:together[a,c]+=w
        frequency=np.divide(adjacent,together,out=np.zeros((4,4)),where=together>0)
        symmetric=(frequency+frequency.T)/2
        positive=symmetric[symmetric>0];dist=np.full((4,4),2/positive.min())
        for a in range(4):
            for b in range(4):
                if a==b:dist[a,b]=0
                elif symmetric[a,b]>0:dist[a,b]=1/np.sqrt(symmetric[a,b])
        for filename,expected in [('adjacency_matrix.csv',adjacent),('coranking_matrix.csv',together),('dissimilarity_matrix.csv',dist)]:
            with (folder/filename).open(newline='') as f:
                reader=csv.reader(f);next(reader);actual=np.array([[float(x) for x in row[1:]] for row in reader])
            assert np.array_equal(actual,expected)
        profiles=json.loads((folder/'null_profiles.json').read_text())['draws']
        axes=[(profile,result['axis'],result['observed'])]
        def first_by_length(values):
            margin=Counter()
            for ranking,w in values.items():margin[(ranking[0] if ranking else None,len(ranking))]+=w
            return margin
        main_margins=first_by_length(profile)
        for saved_null,draw in zip(profiles,result['null']):
            assert saved_null['draw']==draw['draw']
            randomized=Counter({tuple(x['ranking']):x['count'] for x in saved_null['rankings']})
            assert first_by_length(randomized)==main_margins
            axes.append((randomized,draw['axis'],draw))
        checked=0
        for values,axis,score in axes:
            independent=direct_score(values,axis)
            assert independent['gamma']==score['gamma'] and independent['gamma_informative']==score['gamma_informative']
            for row in score['by_length']:
                assert independent['by_length'][row['length']]['gamma']==row['gamma']
                assert independent['by_length'][row['length']]['consistent']==row['consistent']
            for length in range(1,5):
                for ranking in permutations(range(4),length):
                    feasible=interval(ranking,axis)
                    if feasible:
                        midpoint=sum(feasible)/2
                        distances=[abs(midpoint-axis[c]) for c in ranking]
                        assert all(a<b for a,b in zip(distances,distances[1:]))
                    checked+=1
        raw=np.array(result['axis']);display=np.array(result['display_axis'])
        assert np.array_equal(display,1-raw if result['display_reflected'] else raw)
        assert direct_score(profile,display)['gamma']==result['observed']['gamma']
        records[slug]={'status':'passed','source_rows':rows,'profile_patterns':len(profile),
            'source_profile_rederived_independently':True,'pair_matrices_rederived_independently':True,
            'observed_and_all49_null_scores_independent':True,'all49_null_first_choice_by_length_margins_exact':True,
            'by_length_scores_exact':True,'pairwise_halfspace_geometry_checks':checked,
            'reflection_preserves_consistency':True}
    report={'status':'passed','source_policy':'Only Rachel source CSVs and new model outputs; no producer parser/scorer imported.',
        'contests':records}
    (HERE/'independent_axis_audit.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2));return report

if __name__=='__main__':main()
