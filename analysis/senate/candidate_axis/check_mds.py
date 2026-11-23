"""Observed fitting-budget sensitivity and independent midpoint-interval scoring check."""
from pathlib import Path
from itertools import permutations
import json,hashlib
import numpy as np
from analysis.shared.og_axis import FitConfig,fit_axis,summarize,prefix_flags,seed_for
from analysis.shared.paths import model_dir
R=model_dir('us_senate')

def scan_feasible(ranking,axis):
    # Independent brute-force sweep of all open distance-order cells, including
    # irrelevant candidates' midpoints. No inequality recursion from prefix_flags.
    if len(ranking)<2:return True
    points=sorted(set([0.,1.]+[(float(axis[i])+float(axis[j]))/2 for i in range(len(axis)) for j in range(i)]))
    for lo,hi in zip(points,points[1:]):
        if hi-lo<=1e-12:continue
        voter=(lo+hi)/2
        distances=[abs(voter-axis[c]) for c in ranking]
        if all(distances[i]<distances[i+1]-1e-12 for i in range(len(ranking)-1)):return True
    return False

def main():
    p=json.loads((R/'profile.json').read_text());profile={tuple(x['ranking']):x['count'] for x in p['ballots']}
    axis,diag=fit_axis(profile,4,seed_for(20261112,'alaska_senate','observed'),FitConfig(n_runs=100,n_init=16,max_iter=1000,eps=1e-6))
    strong=summarize(profile,axis)
    original=json.loads((R/'mds_results.json').read_text())
    assert original['status']=='complete' and len(original['null'])==49
    assert p['source_sha256']==original['source_sha256']
    axes=[original['axis'],list(map(float,axis))]+[x['axis'] for x in original['null']]
    checked=0
    for coords in axes:
        a=np.array(coords)
        for m in range(1,5):
            ranks=np.array(list(permutations(range(4),m)),dtype=int)
            flags=prefix_flags(a[ranks])[:,-1]
            for b,expected in zip(ranks,flags):
                assert scan_feasible(tuple(map(int,b)),a)==bool(expected)
                checked+=1
    result={'source_filename':p['source_filename'],'source_sha256':p['source_sha256'],'status':'passed','independent_feasibility_rankings_checked':checked,'axes_checked':len(axes),'strong_fit_axis':list(map(float,axis)),'strong_fit_diagnostics':diag,'strong_fit_gamma':strong['gamma'],'strong_fit_gamma_informative':strong['gamma_informative'],'main_fit_gamma':original['observed']['gamma'],'main_fit_gamma_informative':original['observed']['gamma_informative'],'change_overall_percentage_points':100*(strong['gamma']-original['observed']['gamma']),'change_three_plus_percentage_points':100*(strong['gamma_informative']-original['observed']['gamma_informative']),'interpretation':'100outer×16 starts observed-only fitting-budget sensitivity; null comparison remains prespecified20outer×8 starts per observed and randomized profile.'}
    (R/'mds_verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
