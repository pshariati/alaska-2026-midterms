"""Independent raw-source and interval/finite-allocation audit of voter plots.

No producer parser, interval solver or plotting module is imported.
"""
from pathlib import Path
from analysis.shared.paths import REPO_ROOT, INPUTS_ROOT, REFERENCES_ROOT, SHARED_ROOT, race_dir, model_dir, cross_race_dir, resolve_recorded_path
from collections import Counter,defaultdict
import csv,datetime,hashlib,json,math
import numpy as np
from scipy.ndimage import gaussian_filter1d

ROOT=REPO_ROOT
OUT=Path(__file__).resolve().parent
VOTER=cross_race_dir('voter_distributions')
RACES={
 'us_senate':('Alaska_20261103_US_Senate_11_11.csv',[524,525,526,527],
 ['Heikes, Gerald L.','Peltola, Mary','Sullivan, Daniel J. Jr.','Sullivan, Dan S.'],
 '3f0a1a946f23d2d1195f98c5ee5f123916d5f91ede334397465692d5e7f2d972'),
 'governor':('Alaska_20261103_US_Governor_11_11.csv',[537,538,536,539],
 ['Bronson/Church','Kreiss-Tomkins/Johnson','Taylor/English','Wilson/Shower'],
 '3d76cd612870025d9c470f78a60d0bde0cd274aeb9a4e57d575704b588f4b8b3'),
 'us_house':('Alaska_20261103_US_House_11_11.csv',[528,529,530,531],
 ['Begich, Nick','Hafner, Eric','Hill, Bill','McDermott, James C. "Jim"'],
 'b57fad2ef5a8845ba5b3da1eeb3c5e7cfb036c1c174af640b3acee65e45f8b48')}
GROUPS=['all','525','526','524','527']
BINS=8192

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read_csv(path):
 with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def prefix(tokens,names):
 # Independent look-ahead barrier, with write-in occupying its original rank.
 last=max((i for i,x in enumerate(tokens) if x!='skipped'),default=-1)
 barriers=[i for i,x in enumerate(tokens) if x=='overvote']
 barriers += [i for i in range(len(tokens)-1) if tokens[i]==tokens[i+1]=='skipped' and i+1<last]
 stop=min(barriers,default=len(tokens))
 values=tuple(dict.fromkeys(x for x in tokens[:stop] if x not in ['skipped','Write-in']))
 return tuple(names.index(x) for x in values)

def interval(ranking,axis):
 # All ranked-pair inequalities, independently of adjacent-recursion producer.
 if not ranking:return None
 lo,hi=0.,1.
 for i,a in enumerate(ranking):
  for b in ranking[i+1:]:
   first,second=float(axis[a]),float(axis[b]);cut=(first+second)/2
   if first<second:hi=min(hi,cut)
   elif first>second:lo=max(lo,cut)
   else:return None
 return (lo,hi) if hi-lo>1e-12 else None

def impute(profile,axis,uniform_singletons=False):
 pieces=[];counts=Counter();records={}
 for ranking,weight in sorted(profile.items()):
  counts['source_rows_present']+=weight;bounds=interval(ranking,axis);m=len(ranking)
  state='no_named_usable_preference' if not ranking else 'inconsistent' if bounds is None else 'plotted'
  records[ranking]={'ballots':weight,'length':m,'state':state,'feasible':bounds,'allocated':None}
  if state!='plotted':counts[state]+=weight;continue
  counts['plotted']+=weight;counts['length_'+str(m)+'_plotted']+=weight
  if m==1 and not uniform_singletons:
   a=b=float(axis[ranking[0]]);counts['single_name_pinned']+=weight
   values=np.repeat(a,weight)
  else:
   a,b=(0.,1.) if m==1 else bounds
   if m>1:counts['multiple_name_interval_allocated']+=weight
   # Same explicit finite Mahshad convention, separately reconstructed.
   values=np.linspace(a,b,weight,dtype=np.float64)
  records[ranking]['allocated']=(a,b);pieces.append(values)
 points=np.concatenate(pieces) if pieces else np.empty(0,dtype=float)
 assert len(points)==counts['plotted']
 return points,counts,records

def bandwidth(points):
 if len(points)<2:return .04
 sd=float(np.std(points,ddof=1))
 return sd*len(points)**(-.2) if sd>1e-12 else .04

def exact_kde_probes(points,h,where):
 """Direct finite Gaussian mixture with boundary images, no binned producer."""
 density=np.zeros(len(where));constant=1/(len(points)*h*math.sqrt(2*math.pi))
 for batch in np.array_split(points,max(1,int(np.ceil(len(points)/5000)))):
  images=np.r_[batch,-batch,2-batch]
  delta=(where[:,None]-images[None,:])/h
  density+=np.exp(-(delta*delta)/2).sum(axis=1)*constant
 return density

def binned_density(points,h):
 weights,_=np.histogram(points,bins=BINS,range=(0,1))
 return gaussian_filter1d(weights.astype(float),h*BINS,mode='reflect',truncate=6)*BINS/len(points)

def main():
 result=json.loads((VOTER/'results.json').read_text());assert result['status']=='passed'
 # First read all source rows independently and join exactly normalized IDs.
 source_hashes={};senate={};cohorts=Counter();profiles={};source_ids={}
 for race,(filename,ids,names,expected_sha) in RACES.items():
  path=INPUTS_ROOT/filename;assert sha(path)==expected_sha
  assert result['sole_ballot_sources'][race]['sha256']==expected_sha
  source_hashes[race]=expected_sha
  source_ids[race]=set();bygroup={group:Counter() for group in GROUPS}
  with path.open(encoding='utf-8-sig',newline='') as f:
   for row in csv.DictReader(f):
    uid=tuple(int(x) for x in row['ballotID'].rstrip('_').split('_'));assert len(uid)==3
    assert uid not in source_ids[race];source_ids[race].add(uid)
    tokens=tuple(row['rank'+str(i)] for i in range(1,6))
    if race=='us_senate':
     group=str(ids[names.index(tokens[0])]) if tokens[0] in names else None
     senate[uid]=group
     if group:cohorts[group]+=1
    else:assert uid in senate;group=senate[uid]
    ranking=prefix(tokens,names);bygroup['all'][ranking]+=1
    if group:bygroup[group][ranking]+=1
  profiles[race]=bygroup
 assert source_ids['us_senate']==source_ids['us_house']
 assert source_ids['governor']<=source_ids['us_senate']
 assert len(source_ids['us_senate']-source_ids['governor'])==130
 assert dict(cohorts)==result['senate_literal_rank1_cohort_counts']
 axes={};strong_axes={};reflection_checks={}
 for race,metadata in result['axes'].items():
  path=resolve_recorded_path(metadata['axis_source_file']);assert sha(path)==metadata['axis_source_sha256']
  mapping={int(row['candidate_id']):row for row in read_csv(path)}
  ids=RACES[race][1]
  raw=np.array([float(mapping[c]['axis_position']) for c in ids])
  display=np.array([float(mapping[c].get('display_axis_position',mapping[c]['axis_position'])) for c in ids])
  assert np.array_equal(raw,metadata['raw_axis']) and np.array_equal(display,metadata['display_axis'])
  assert np.array_equal(display,1-raw if metadata['display_reflected'] else raw)
  axes[race]=display
  verification=json.loads((model_dir(race)/'mds_verification.json').read_text())
  raw_strong=np.array(verification['strong_fit_axis'])
  strong_axes[race]=1-raw_strong if metadata['display_reflected'] else raw_strong
  assert verification['main_fit_gamma']==verification['strong_fit_gamma']
  assert verification['main_fit_gamma_informative']==verification['strong_fit_gamma_informative']
  reflection_checks[race]=True
 coverage={(r['contest'],r['senate_group']):r for r in result['coverage']}
 saved_coverage={(r['contest'],r['senate_group']):r for r in read_csv(VOTER/'voter_distribution_coverage.csv')}
 summaries={(r['contest'],r['senate_group']):r for r in result['summaries']}
 intervals={(r['contest'],r['senate_group'],tuple(json.loads(r['ranking_local_indices']))):r for r in read_csv(VOTER/'intervals_by_cohort.csv')}
 density_rows=defaultdict(list)
 for row in read_csv(VOTER/'density_grid.csv'):density_rows[row['contest'],row['senate_group']].append(row)
 geometry={(r['contest'],r['senate_group']):r for r in result['fitting_budget_geometry_sensitivity']['rows']}
 arrays=np.load(VOTER/'imputed_points.npz',allow_pickle=False)
 points_by_key={};checks=[];interval_count=0;direct_errors=[]
 coverage_keys=['source_rows_present','plotted','inconsistent','no_named_usable_preference','single_name_pinned','multiple_name_interval_allocated']
 for race in RACES:
  allpoints,_,_=impute(profiles[race]['all'],axes[race]);h=bandwidth(allpoints)
  for group in GROUPS:
   key=(race,group);profile=profiles[race][group];points,counts,records=impute(profile,axes[race])
   alternate,alt_counts,_=impute(profile,axes[race],uniform_singletons=True)
   points_by_key[key]=points;item=coverage[key];summary=summaries[key]
   n=len(source_ids[race]) if group=='all' else cohorts[group]
   missing=n-sum(profile.values())
   assert item['cohort_n']==n and item['missing_source_rows']==missing
   assert item['plotted']+item['inconsistent']+item['no_named_usable_preference']+missing==n
   for name in coverage_keys:
    assert item.get(name,0)==counts.get(name,0),(key,name,item.get(name),counts.get(name))
    assert int(saved_coverage[key].get(name) or 0)==counts.get(name,0)
   for m in range(1,5):assert item.get('length_'+str(m)+'_plotted',0)==counts.get('length_'+str(m)+'_plotted',0)
   assert counts['plotted']==alt_counts['plotted'] and counts['inconsistent']==alt_counts['inconsistent']
   saved=arrays[race+'__'+group];saved_alt=arrays[race+'__'+group+'__singleton_uniform_sensitivity']
   assert np.array_equal(points,saved) and np.array_equal(alternate,saved_alt)
   assert np.all(np.isfinite(points)) and np.all((points>=0)&(points<=1))
   assert summary['plotted_n']==len(points) and summary['plotted_share_of_cohort']==len(points)/n
   for field,value in [('imputed_mean',np.mean(points)),('imputed_median',np.median(points)),
    ('imputed_q25',np.quantile(points,.25)),('imputed_q75',np.quantile(points,.75)),
    ('singleton_uniform_sensitivity_median',np.median(alternate))]:assert summary[field]==float(value),(key,field)
   assert summary['common_axis_bandwidth']==h and summary['own_group_Scott_bandwidth']==bandwidth(points)
   for ranking,record in records.items():
    saved_record=intervals[race,group,ranking];interval_count+=1
    assert int(saved_record['ballots'])==record['ballots'] and int(saved_record['length'])==record['length']
    assert saved_record['state']==record['state']
    for prefix_name,bounds in [('feasible',record['feasible']),('allocation',record['allocated'])]:
     for index,suffix in enumerate(['lo','hi']):
      value=saved_record[prefix_name+'_'+suffix]
      assert value=='' if bounds is None else float(value)==bounds[index]
    if record['state']=='plotted' and record['length']==1:
     assert 'pinned' in saved_record['allocation_convention']
   rows=density_rows[key];assert len(rows)==BINS
   grid=np.array([float(r['coordinate']) for r in rows]);assert np.array_equal(grid,(np.arange(BINS)+.5)/BINS)
   densities={field:np.array([float(row[field]) for row in rows]) for field in ['density_common_axis_bandwidth','density_group_Scott_bandwidth','density_singleton_uniform_sensitivity']}
   for values in densities.values():
    assert np.all(np.isfinite(values)) and np.all(values>=0)
    assert abs(float(values.sum()/BINS)-1)<1e-12
   assert np.array_equal(densities['density_common_axis_bandwidth'],binned_density(points,h))
   assert np.array_equal(densities['density_group_Scott_bandwidth'],binned_density(points,bandwidth(points)))
   assert np.array_equal(densities['density_singleton_uniform_sensitivity'],binned_density(alternate,h))
   full_mass_present='density_full_cohort_mass' in rows[0]
   assert full_mass_present
   mass=np.array([float(r['density_full_cohort_mass']) for r in rows])
   assert np.allclose(mass,densities['density_common_axis_bandwidth']*len(points)/n,atol=1e-13,rtol=1e-13)
   assert abs(float(mass.sum()/BINS)-len(points)/n)<1e-12
   probes=np.unique(np.r_[np.linspace(0,1,33),axes[race]])
   exact=exact_kde_probes(points,h,probes)
   error=float(np.max(np.abs(exact-np.interp(probes,grid,densities['density_common_axis_bandwidth']))))
   relative=error/max(1.,float(exact.max()));assert relative<.006
   direct_errors.append(relative)
   strong,strong_counts,_=impute(profile,strong_axes[race]);g=geometry[key]
   assert len(strong)==len(points)==g['main_plotted_n']==g['strong_plotted_n']
   for name in coverage_keys:assert strong_counts.get(name,0)==counts.get(name,0)
   assert g['main_imputed_mean']==float(np.mean(points)) and g['strong_imputed_mean']==float(np.mean(strong))
   assert g['main_imputed_median']==float(np.median(points)) and g['strong_imputed_median']==float(np.median(strong))
   strong_density=binned_density(strong,h)
   difference=float(np.max(np.abs(strong_density-densities['density_common_axis_bandwidth'])))
   assert g['max_absolute_density_difference_fixed_bandwidth']==difference
   a=np.sort(points);b=np.sort(strong);supports=np.unique(np.r_[a,b])
   ks=float(np.max(np.abs(np.searchsorted(a,supports,side='right')/len(a)-np.searchsorted(b,supports,side='right')/len(b))))
   assert g['max_empirical_CDF_difference']==ks
   checks.append({'contest':race,'senate_group':group,'cohort_n':n,'plotted_n':len(points),
    'missing_n':missing,'empty_n':counts['no_named_usable_preference'],'inconsistent_n':counts['inconsistent'],
    'finite_points_exactly_reproduced':True,'finite_point_summaries_exact':True,
    'all_interval_records_match_independent_all_pairs_solver':True,'bandwidth_uses_actual_repeated_point_N':True,
    'conditional_density_mass':float(densities['density_common_axis_bandwidth'].sum()/BINS),
    'full_cohort_density_mass':float(mass.sum()/BINS),'direct_KDE_probe_relative_error':relative,
    'strong_geometry_sensitivity_reproduced':True})
 assert len(checks)==15 and len(intervals)==interval_count
 assert len(result['axes'])==3 and result['normalization'].startswith('Every curve integrates to1')
 assert 'not identified' in result['limitations'][0] or 'not point identified' in result['limitations'][0]
 assert 'one-name ballots' in result['singleton_sensitivity'] or 'singleton' in result['singleton_sensitivity']
 output={'status':'passed','completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'source_policy':'Only raw Rachel CSVs, delivered axes, and new voter outputs; producer modules not imported.',
  'source_hashes':source_hashes,'raw_direct_ID_join_verified':True,'missing_governor_ids':130,
  'independent_cohort_curves_checked':15,'independent_interval_records_checked':interval_count,
  'saved_finite_point_arrays_and_singleton_alternatives_exact':True,
  'all_coverage_partitions_means_quantiles_and_bandwidths_reproduced':True,
  'all_density_grids_nonnegative_and_conditional_mass_one':True,
  'all_full_cohort_density_masses_equal_plotted_share':True,
  'max_independent_direct_KDE_probe_relative_error':max(direct_errors),
  'strong_budget_axes_preserve_gamma_and_coverage_but_geometry_changes_reported':True,
  'axis_reflections_consistent':reflection_checks,
  'interpretation':'Mahshad allocation convention plus explicit smoothing; singleton spikes and interval allocations are assumptions, not point-identified voter ideology. Inconsistent/missing/empty ballots remain explicit.',
  'curves':checks}
 (OUT/'independent_voter_audit.json').write_text(json.dumps(output,indent=2))
 print(json.dumps({k:v for k,v in output.items() if k!='curves'},indent=2));return output

if __name__=='__main__':main()
