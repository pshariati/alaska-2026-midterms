"""Mahshad-style imputed voter distributions on full-contest one-dimensional axes.

Only Rachel's supplied CSVs are ballot inputs. Positions are not identified voter
ideologies: multiple-name ballots are spread over their feasible ranked-only
interval and one-name ballots are pinned to their sole candidate, following the
upstream plotting convention. Every omitted/missing/inconsistent ballot is counted.
"""
from pathlib import Path
from analysis.shared.paths import REPO_ROOT, INPUTS_ROOT, REFERENCES_ROOT, SHARED_ROOT, race_dir, model_dir, cross_race_dir, resolve_recorded_path
from collections import Counter,defaultdict
from itertools import permutations
import sys,csv,json,hashlib,datetime,math
import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.special import ndtr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

ROOT=REPO_ROOT
OUT=Path(__file__).resolve().parent
from analysis.shared.data import RACES,SLUGS,SENATE_LABELS,SENATE_ORDER,read_rows,normalized_id,countable_tokens,sha256

BINS=8192
GROUPS=['all']+[str(c) for c in SENATE_ORDER]
COLORS={'525':'#2869a6','526':'#d59b36','524':'#8061aa','527':'#bb4f51','all':'#466985'}
SHORT_NAMES={
 'us_senate':{524:'Heikes',525:'Peltola',526:'Dan J.',527:'Daniel S.'},
 'governor':{537:'Bronson',538:'Kreiss-Tomkins',536:'Taylor',539:'Wilson'},
 'us_house':{528:'Begich',529:'Hafner',530:'Hill',531:'McDermott'}}

def write_csv(path,rows):
 rows=list(rows)
 with path.open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def feasible_interval(ranking,axis):
 """Exact positive-width strict-distance interval, on normalized domain [0,1]."""
 if not ranking:return None
 lo,hi=0.,1.
 for left,right in zip(ranking,ranking[1:]):
  a,b=float(axis[left]),float(axis[right]);mid=(a+b)/2
  if a==b:return None
  if a<b:hi=min(hi,mid)
  else:lo=max(lo,mid)
 return (lo,hi) if hi-lo>1e-12 else None

def independent_interval(ranking,axis):
 """Independent all-pair-midpoint cell sweep, rather than interval inequalities."""
 if not ranking:return None
 points=sorted(set([0.,1.]+[(float(axis[i])+float(axis[j]))/2 for i in range(4) for j in range(i)]))
 valid=[]
 for a,b in zip(points,points[1:]):
  if b-a<=1e-12:continue
  x=(a+b)/2;dist=[abs(x-axis[c]) for c in ranking]
  if all(u<v-1e-12 for u,v in zip(dist,dist[1:])):valid.append((a,b))
 return (valid[0][0],valid[-1][1]) if valid else None

def load_axes():
 axes={};metadata={}
 for race in SLUGS:
  path=model_dir(race)/'candidate_axis.csv'
  with path.open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
  indexed={int(r['candidate_id']):r for r in rows}
  assert set(indexed)==set(RACES[race]['ids'])
  display=np.array([float(indexed[c].get('display_axis_position',indexed[c]['axis_position'])) for c in RACES[race]['ids']])
  raw=np.array([float(indexed[c]['axis_position']) for c in RACES[race]['ids']])
  assert np.all(np.isfinite(display)) and np.min(np.diff(np.sort(display)))>1e-12
  assert display.min()>=-1e-12 and display.max()<=1+1e-12
  axes[race]=display
  metadata[race]={'axis_source_file':str(path.relative_to(ROOT)),'axis_source_sha256':sha256(path),
   'candidate_ids':RACES[race]['ids'],'candidate_names':RACES[race]['names'],
   'raw_axis':raw.tolist(),'display_axis':display.tolist(),
   'display_reflected':bool(np.allclose(display,1-raw,atol=1e-12)) and not bool(np.allclose(display,raw,atol=1e-12))}
 return axes,metadata

def load_cohort_profiles():
 """Join by normalized source IDs; preserve the literal-rank-1 Senate cohorts."""
 senate={};cohort_n=Counter();profiles={};coverage={};source_sets={}
 names=RACES['us_senate']['names'];ids=RACES['us_senate']['ids']
 for _,row,tokens in read_rows('us_senate'):
  uid=normalized_id(row['ballotID'])
  assert uid not in senate
  group=str(ids[names.index(tokens[0])]) if tokens[0] in names else None
  senate[uid]=group
  if group:cohort_n[group]+=1
 for race in SLUGS:
  bygroup={g:Counter() for g in GROUPS};seen=set();observed=Counter()
  names=RACES[race]['names']
  for _,row,tokens in read_rows(race):
   uid=normalized_id(row['ballotID']);assert uid not in seen;seen.add(uid)
   pref,_,_=countable_tokens(tokens)
   ranking=tuple(names.index(x) for x in pref if x!='Write-in')
   bygroup['all'][ranking]+=1;observed['all']+=1
   assert uid in senate,'Contest ID absent from Senate file'
   group=senate[uid]
   if group:bygroup[group][ranking]+=1;observed[group]+=1
  source_sets[race]=seen
  profiles[race]=bygroup
  coverage[race]={'all':{'cohort_n':len(seen),'source_rows_present':len(seen),'missing_source_rows':0}}
  for group in GROUPS[1:]:
   coverage[race][group]={'cohort_n':cohort_n[group],'source_rows_present':observed[group],
      'missing_source_rows':cohort_n[group]-observed[group]}
 assert source_sets['us_house']==source_sets['us_senate']
 assert source_sets['governor']<=source_sets['us_senate']
 assert len(source_sets['us_senate']-source_sets['governor'])==130
 return profiles,coverage,dict(cohort_n)

def impute_points(profile,axis,singleton_mode='candidate'):
 points=[];records=[];counts=Counter();meansum=0.;second=0.
 for ranking,count in sorted(profile.items()):
  if not count:continue
  length=len(ranking)
  counts['source_rows_present']+=count
  interval=feasible_interval(ranking,axis)
  state='no_named_usable_preference' if length==0 else 'inconsistent' if interval is None else 'plotted'
  record={'ranking_local_indices':json.dumps(ranking),'length':length,'ballots':count,
   'state':state,'feasible_lo':None if interval is None else interval[0],
   'feasible_hi':None if interval is None else interval[1],
   'allocation_lo':None,'allocation_hi':None,'allocation_convention':None}
  if state!='plotted':
   counts[state]+=count;records.append(record);continue
  lo,hi=interval
  if length==1 and singleton_mode=='candidate':
   a=b=float(axis[ranking[0]]);allocated=np.full(count,a,dtype=float)
   convention='Mahshad singleton pinned at sole candidate'
  else:
   a,b=(0.,1.) if length==1 else (lo,hi)
   # Exact finite linspace convention used by the upstream plot_KDE. Boundary
   # points are a plotting allocation convention; gamma uses open intervals.
   allocated=np.linspace(a,b,count,dtype=float)
   convention='finite linspace across feasible interval' if length>1 else 'singleton uniform0to1 sensitivity'
  points.append(allocated);counts['plotted']+=count;counts['length_'+str(length)+'_plotted']+=count
  if length==1:counts['single_name_pinned' if singleton_mode=='candidate' else 'single_name_uniform']+=count
  else:counts['multiple_name_interval_allocated']+=count
  record.update(allocation_lo=a,allocation_hi=b,allocation_convention=convention)
  records.append(record)
 result=np.concatenate(points) if points else np.empty(0,dtype=float)
 assert len(result)==counts['plotted']
 assert counts['plotted']+counts['inconsistent']+counts['no_named_usable_preference']==counts['source_rows_present']
 return result,records,counts

def scott_bandwidth(points):
 if len(points)<2:return .04
 sd=float(np.std(points,ddof=1))
 return sd*len(points)**(-.2) if sd>1e-12 else .04

def binned_reflected_kde(points,bandwidth):
 hist,edges=np.histogram(points,bins=BINS,range=(0,1))
 assert hist.sum()==len(points)
 dx=1/BINS;grid=(edges[:-1]+edges[1:])/2
 if not len(points):return grid,np.zeros(BINS)
 density=gaussian_filter1d(hist.astype(float),bandwidth/dx,mode='reflect',truncate=6)/(len(points)*dx)
 assert abs(float(density.sum()*dx)-1)<1e-12
 return grid,density

def exact_reflected_kde_at(points,bandwidth,where):
 values=np.zeros(len(where));normal=1/(math.sqrt(2*math.pi)*bandwidth*len(points))
 for start in range(0,len(points),8192):
  part=points[start:start+8192]
  for center in (part,-part,2-part):
   z=(where[:,None]-center[None,:])/bandwidth
   values+=np.exp(-.5*z*z).sum(axis=1)*normal
 return values

def analytical_uniform_mean(records):
 good=[r for r in records if r['state']=='plotted'];n=sum(r['ballots'] for r in good)
 return sum(r['ballots']*(r['allocation_lo']+r['allocation_hi'])/2 for r in good)/n

def geometry_sensitivity(profiles,axes,metadata,results,point_arrays):
 rows=[];axis_details={}
 for race in SLUGS:
  path=model_dir(race)/'mds_verification.json'
  verification=json.loads(path.read_text())
  strong=np.array(verification['strong_fit_axis'],dtype=float)
  if metadata[race]['display_reflected']:strong=1-strong
  axis_details[race]={'source_file':str(path.relative_to(ROOT)),'source_sha256':sha256(path),
   'main_display_axis':axes[race].tolist(),'strong_display_axis':strong.tolist(),
   'max_candidate_coordinate_shift':float(np.max(np.abs(strong-axes[race])))}
  for group in GROUPS:
   original=point_arrays[race+'__'+group]
   changed,_,counts=impute_points(profiles[race][group],strong)
   full_bandwidth=scott_bandwidth(point_arrays[race+'__all'])
   grid,density=binned_reflected_kde(changed,full_bandwidth)
   a=np.sort(original);b=np.sort(changed)
   supports=np.unique(np.r_[a,b])
   cdf_difference=float(np.max(np.abs(np.searchsorted(a,supports,side='right')/len(a)-np.searchsorted(b,supports,side='right')/len(b))))
   rows.append({'contest':race,'senate_group':group,'group_name':results[race,group]['coverage']['group_name'],
    'main_plotted_n':len(original),'strong_plotted_n':len(changed),
    'main_imputed_mean':float(np.mean(original)),'strong_imputed_mean':float(np.mean(changed)),
    'mean_change':float(np.mean(changed)-np.mean(original)),
    'main_imputed_median':float(np.median(original)),'strong_imputed_median':float(np.median(changed)),
    'median_change':float(np.median(changed)-np.median(original)),
    'max_empirical_CDF_difference':cdf_difference,
    'max_absolute_density_difference_fixed_bandwidth':float(np.max(np.abs(density-results[race,group]['density']))),
    'full_axis_bandwidth_held_fixed':full_bandwidth})
 write_csv(OUT/'axis_geometry_sensitivity.csv',rows)
 return {'axes':axis_details,'rows':rows,'interpretation':'Observed-only100outer×16starts geometry sensitivity; main models remain20×8. Display reflection is identical to main. Density comparisons hold the main full-axis bandwidth fixed. Singleton point masses can make CDF changes large even for small coordinate shifts; they are imputation conventions.'}

def candidate_ticks(ax,race,axis):
 # Candidate markers keep actual normalized spacings; names alternate in two rows.
 for j,i in enumerate(np.argsort(axis)):
  x=float(axis[i]);name=SHORT_NAMES[race][RACES[race]['ids'][i]]
  ax.axvline(x,color='#c4ced6',lw=.65,ls=(0,(2,3)),zorder=0)
  ax.annotate(name,xy=(x,0),xycoords=('data','axes fraction'),xytext=(0,-21 if j%2==0 else -35),
   textcoords='offset points',ha='center',va='top',fontsize=8,color='#536b7e')

def setup_style():
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'text.color':'#243449',
  'axes.labelcolor':'#40566f','xtick.color':'#40566f','ytick.color':'#40566f',
  'figure.facecolor':'white','axes.facecolor':'white','savefig.facecolor':'white',
  'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})

def save_figure(fig,name):
 fig.savefig(OUT/(name+'.png'),dpi=190,bbox_inches='tight')
 fig.savefig(OUT/(name+'.svg'),bbox_inches='tight');plt.close(fig)

def plot_results(results,axes):
 setup_style()
 # Full electorates, each on its own full-contest candidate axis.
 fig,axs=plt.subplots(3,1,figsize=(12,9))
 for ax,race in zip(axs,SLUGS):
  item=results[race,'all'];x=item['grid'];y=item['density']
  ax.plot(x,y,color=COLORS['all'],lw=2);ax.fill_between(x,0,y,color=COLORS['all'],alpha=.13)
  c=item['coverage'];ax.set_title(RACES[race]['title']+f" axis — {c['plotted']:,} plotted / {c['source_rows_present']:,} source ballots",loc='left',fontsize=12,fontweight='bold')
  ax.set(xlim=(0,1),ylim=(0,None),ylabel='Imputed density');candidate_ticks(ax,race,axes[race]);ax.grid(axis='y',alpha=.15)
 axs[-1].set_xlabel('Normalized candidate-axis coordinate',labelpad=42)
 fig.suptitle('Voter distributions under Mahshad’s allocation convention',x=.095,ha='left',fontsize=16,fontweight='bold')
 fig.text(.095,-.04,'Conditional on spatial consistency; singleton ballots are pinned to their candidate. These are imputed distributions, not identified voter locations.',fontsize=9,color='#61798e')
 fig.subplots_adjust(left=.095,right=.97,top=.91,bottom=.11,hspace=.65)
 save_figure(fig,'all_voters_three_axes')

 # Four literal Senate first-choice groups shown within each election-specific map.
 fig,axs=plt.subplots(3,1,figsize=(12,10))
 for ax,race in zip(axs,SLUGS):
  for group in GROUPS[1:]:
   item=results[race,group];c=item['coverage']
   label=SENATE_LABELS[int(group)]+f" ({100*c['plotted']/c['cohort_n']:.1f}% plotted)"
   ax.plot(item['grid'],item['density'],color=COLORS[group],lw=1.9,label=label)
  ax.set_title(RACES[race]['title']+' axis',loc='left',fontsize=12,fontweight='bold')
  ax.set(xlim=(0,1),ylim=(0,None),ylabel='Imputed density');candidate_ticks(ax,race,axes[race])
  ax.legend(frameon=False,fontsize=8.5,ncol=2,loc='upper right');ax.grid(axis='y',alpha=.15)
 axs[-1].set_xlabel('Normalized candidate-axis coordinate',labelpad=42)
 fig.suptitle('Senate first-choice groups across the three candidate axes',x=.095,ha='left',fontsize=16,fontweight='bold')
 fig.text(.095,-.04,'Each curve integrates to1 among plotted ballots. “Plotted” is the share of the original Senate cohort; missing, empty and inconsistent ballots are reported separately.',fontsize=9,color='#61798e')
 fig.subplots_adjust(left=.095,right=.97,top=.91,bottom=.11,hspace=.65)
 save_figure(fig,'senate_groups_across_three_axes')

 # Peltola/challenger focus: compare shapes without merging distinct axes.
 fig,axs=plt.subplots(2,3,figsize=(15,7.4),sharex=True)
 for row,group in enumerate(['525','526']):
  for col,race in enumerate(SLUGS):
   ax=axs[row,col];item=results[race,group];c=item['coverage']
   ax.plot(item['grid'],item['density'],color=COLORS[group],lw=2)
   ax.fill_between(item['grid'],0,item['density'],color=COLORS[group],alpha=.14)
   ax.set_title(RACES[race]['title']+' axis',loc='left',fontsize=11,fontweight='bold')
   ax.text(.98,.94,f"{c['plotted']:,} / {c['cohort_n']:,} plotted",transform=ax.transAxes,ha='right',va='top',fontsize=8)
   ax.set(xlim=(0,1),ylim=(0,None));candidate_ticks(ax,race,axes[race]);ax.grid(axis='y',alpha=.15)
   if col==0:ax.set_ylabel(SENATE_LABELS[int(group)]+' first choice\nImputed density')
 fig.suptitle('Peltola and challenger Sullivan voters on each election’s candidate axis',x=.075,ha='left',fontsize=15,fontweight='bold')
 fig.text(.075,.02,'Each panel uses its own candidate map and common within-axis smoothing. Coordinates across elections are not a shared ideology scale.',fontsize=9,color='#61798e')
 fig.subplots_adjust(left=.075,right=.98,top=.88,bottom=.14,hspace=.72,wspace=.22)
 save_figure(fig,'peltola_challenger_across_three_axes')

 # Singleton convention sensitivity changes the distribution, not the candidate fit.
 fig,axs=plt.subplots(3,1,figsize=(12,9))
 for ax,race in zip(axs,SLUGS):
  item=results[race,'all'];ax.plot(item['grid'],item['density'],color='#466985',lw=2,label='Mahshad: singleton pinned')
  ax.plot(item['grid'],item['singleton_uniform_density'],color='#a06345',lw=1.8,ls='--',label='Sensitivity: singleton spread across0–1')
  ax.set_title(RACES[race]['title']+' axis',loc='left',fontweight='bold',fontsize=12)
  ax.set(xlim=(0,1),ylim=(0,None),ylabel='Imputed density');candidate_ticks(ax,race,axes[race]);ax.legend(frameon=False,fontsize=9)
 axs[-1].set_xlabel('Normalized candidate-axis coordinate',labelpad=42)
 fig.suptitle('The assumed locations of one-name ballots affect the density',x=.095,ha='left',fontsize=16,fontweight='bold')
 fig.text(.095,-.04,'Both curves use identical candidate positions and located ballot sets. Ranked-only consistency places no location constraint on a one-name ballot.',fontsize=9,color='#61798e')
 fig.subplots_adjust(left=.095,right=.97,top=.91,bottom=.11,hspace=.65)
 save_figure(fig,'singleton_allocation_sensitivity')

 # Coverage remains on full fixed Senate cohorts, rather than hiding exclusions.
 fig,axs=plt.subplots(3,1,figsize=(12,8),sharex=True)
 status_specs=[('plotted','Located under convention','#5e9988'),
  ('inconsistent','Spatially inconsistent','#bb5e60'),
  ('no_named_usable_preference','No usable named choice','#bdc9d3'),
  ('missing_source_rows','Missing contest record','#d2a54e')]
 for ax,race in zip(axs,SLUGS):
  left=np.zeros(4)
  for key,label,color in status_specs:
   values=np.array([100*results[race,g]['coverage'][key]/results[race,g]['coverage']['cohort_n'] for g in GROUPS[1:]])
   ax.barh(range(4),values,left=left,height=.58,color=color,label=label)
   if key=='plotted':
    for i,value in enumerate(values):ax.text(value/2,i,f'{value:.1f}%',ha='center',va='center',color='white',fontweight='bold',fontsize=9)
   left+=values
  assert np.allclose(left,100)
  ax.set_yticks(range(4),[SENATE_LABELS[int(g)] for g in GROUPS[1:]])
  ax.invert_yaxis();ax.set_xlim(0,100);ax.set_title(RACES[race]['title']+' rankings',loc='left',fontsize=12,fontweight='bold')
  ax.tick_params(axis='y',length=0);ax.spines['left'].set_visible(False)
 axs[-1].set_xlabel('Share of the full literal-rank-1 Senate cohort (%)')
 handles,labels=axs[0].get_legend_handles_labels()
 fig.legend(handles,labels,loc='lower center',bbox_to_anchor=(.55,.015),ncol=2,frameon=False,fontsize=9)
 fig.suptitle('Coverage of the voter-distribution plots',x=.23,ha='left',fontsize=16,fontweight='bold')
 fig.subplots_adjust(left=.23,right=.98,top=.9,bottom=.13,hspace=.4)
 save_figure(fig,'voter_distribution_coverage')

def render_saved_figures():
 """Re-render after a presentation-only change, without repeating analysis."""
 axes,_=load_axes();results={}
 with (OUT/'voter_distribution_coverage.csv').open(encoding='utf-8',newline='') as f:
  for row in csv.DictReader(f):
   race,group=row['contest'],row['senate_group']
   c={key:(int(value) if value and key not in ('contest','senate_group','group_name') else value) for key,value in row.items()}
   results[race,group]={'coverage':c,'grid':[],'density':[],'singleton_uniform_density':[],'group_scott_density':[]}
 with (OUT/'density_grid.csv').open(encoding='utf-8',newline='') as f:
  for row in csv.DictReader(f):
   item=results[row['contest'],row['senate_group']]
   for key,column in [('grid','coordinate'),('density','density_common_axis_bandwidth'),('singleton_uniform_density','density_singleton_uniform_sensitivity'),('group_scott_density','density_group_Scott_bandwidth')]:item[key].append(float(row[column]))
 for item in results.values():
  for key in ['grid','density','singleton_uniform_density','group_scott_density']:item[key]=np.array(item[key])
  assert len(item['grid'])==BINS
 plot_results(results,axes)
 print('Presentation figures refreshed from saved verified distribution arrays.')

def main():
 started=datetime.datetime.now(datetime.timezone.utc).isoformat()
 axes,axis_metadata=load_axes();profiles,coverage,cohort_n=load_cohort_profiles()
 interval_checks=0
 for race,axis in axes.items():
  for length in range(1,5):
   for ranking in permutations(range(4),length):
    a=feasible_interval(ranking,axis);b=independent_interval(ranking,axis)
    assert (a is None)==(b is None)
    if a is not None:assert np.allclose(a,b,atol=1e-12,rtol=0)
    interval_checks+=1
 results={};point_arrays={};coverage_rows=[];interval_rows=[];summary=[];accuracy=[]
 for race in SLUGS:
  all_points,_,_=impute_points(profiles[race]['all'],axes[race])
  bandwidth=scott_bandwidth(all_points)
  for group in GROUPS:
   points,records,counts=impute_points(profiles[race][group],axes[race])
   alternate,_,_=impute_points(profiles[race][group],axes[race],singleton_mode='uniform')
   c={**coverage[race][group],**dict(counts)}
   c.update(contest=race,senate_group=group,group_name='All source ballots' if group=='all' else SENATE_LABELS[int(group)])
   for key in ['plotted','inconsistent','no_named_usable_preference','single_name_pinned','multiple_name_interval_allocated']:c.setdefault(key,0)
   assert c['cohort_n']==c['missing_source_rows']+c['no_named_usable_preference']+c['inconsistent']+c['plotted']
   grid,density=binned_reflected_kde(points,bandwidth)
   _,uniform_density=binned_reflected_kde(alternate,bandwidth)
   own_bandwidth=scott_bandwidth(points);_,own_density=binned_reflected_kde(points,own_bandwidth)
   probes=np.unique(np.r_[np.linspace(0,1,41),axes[race]])
   exact=exact_reflected_kde_at(points,bandwidth,probes)
   approximate=np.interp(probes,grid,density)
   max_error=float(np.max(np.abs(exact-approximate)))
   peak=float(np.max(exact));assert max_error<.006*max(peak,1),'Binned KDE insufficiently accurate'
   accuracy.append({'contest':race,'senate_group':group,'probe_count':len(probes),
    'max_absolute_density_error':max_error,'max_error_as_fraction_probe_peak':max_error/max(peak,1),
    'exact_finite_point_kde_comparison':True,'density_mass':float(density.sum()/BINS),
    'finite_point_mean':float(np.mean(points)),
    'continuous_uniform_mixture_mean':analytical_uniform_mean(records),
    'mean_finite_minus_continuous':float(np.mean(points))-analytical_uniform_mean(records)})
   results[race,group]={'grid':grid,'density':density,'singleton_uniform_density':uniform_density,
    'group_scott_density':own_density,'coverage':c}
   point_arrays[race+'__'+group]=points
   point_arrays[race+'__'+group+'__singleton_uniform_sensitivity']=alternate
   coverage_rows.append(c)
   for record in records:
    record.update(contest=race,senate_group=group);interval_rows.append(record)
   summary.append({'contest':race,'senate_group':group,'group_name':c['group_name'],
    'cohort_n':c['cohort_n'],'plotted_n':len(points),'plotted_share_of_cohort':len(points)/c['cohort_n'],
    'imputed_mean':float(np.mean(points)),'imputed_median':float(np.median(points)),
    'imputed_q25':float(np.quantile(points,.25)),'imputed_q75':float(np.quantile(points,.75)),
    'singleton_uniform_sensitivity_median':float(np.median(alternate)),
    'common_axis_bandwidth':bandwidth,'own_group_Scott_bandwidth':own_bandwidth,
    'source_axis_reflected_for_display':axis_metadata[race]['display_reflected']})
  print('Completed distributions:',race,flush=True)
 write_csv(OUT/'voter_distribution_coverage.csv',coverage_rows)
 write_csv(OUT/'voter_distribution_summary.csv',summary)
 write_csv(OUT/'intervals_by_cohort.csv',interval_rows)
 write_csv(OUT/'numerical_kde_checks.csv',accuracy)
 density_rows=[]
 for (race,group),item in results.items():
  for i,x in enumerate(item['grid']):density_rows.append({'contest':race,'senate_group':group,'coordinate':float(x),
   'density_common_axis_bandwidth':float(item['density'][i]),
   'density_full_cohort_mass':float(item['density'][i])*item['coverage']['plotted']/item['coverage']['cohort_n'],
   'density_group_Scott_bandwidth':float(item['group_scott_density'][i]),
   'density_singleton_uniform_sensitivity':float(item['singleton_uniform_density'][i])})
 write_csv(OUT/'density_grid.csv',density_rows)
 np.savez_compressed(OUT/'imputed_points.npz',**point_arrays)
 geometry=geometry_sensitivity(profiles,axes,axis_metadata,results,point_arrays)
 plot_results(results,axes)
 record={'status':'passed','started_utc':started,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'sole_ballot_sources':{race:{'filename':RACES[race]['filename'],'sha256':RACES[race]['sha256']} for race in SLUGS},
  'senate_literal_rank1_cohort_counts':cohort_n,'axes':axis_metadata,
  'method':'Mahshad-style: finite np.linspace(lo,hi,pattern_count) over exact feasible ranked-only interval; one-name ballots pinned at candidate. Empty/inconsistent/missing records counted, not located.',
  'interval_domain':'Normalized0to1; open strict preference feasibility; finite plotting allocation includes interval endpoints by upstream convention.',
  'density_display':'8192bin Gaussian KDE with reflection at0and1; fixed Scott bandwidth from full plotted electorate reused for every Senate group within each axis. KDE binned approximation checked against exact finite-point kernels.',
  'normalization':'Every curve integrates to1 conditional on being plotted; cohort coverage and exclusions supplied separately. Candidate maps fitted on full contest profiles, never on groups.',
  'singleton_sensitivity':'All one-name ballots instead allocated over0to1, the full ranked-only feasible interval. This is an alternative convention, not a claim of uniform true ideology.',
  'independent_interval_checks':interval_checks,'max_binned_KDE_error_fraction_probe_peak':max(x['max_error_as_fraction_probe_peak'] for x in accuracy),
  'mean_difference_finite_vs_continuous_max':max(abs(x['mean_finite_minus_continuous']) for x in accuracy),
  'fitting_budget_geometry_sensitivity':geometry,
  'coverage':coverage_rows,'summaries':summary,
  'figures':['all_voters_three_axes.png','senate_groups_across_three_axes.png','peltola_challenger_across_three_axes.png','singleton_allocation_sensitivity.png','voter_distribution_coverage.png'],
  'limitations':['Voter positions are not point identified by truncated rankings. Uniform intervals and singleton spikes are explicit plotting conventions.',
   'Only spatially consistent usable named rankings are placed. Missing governor records, empty prefixes and inconsistent ballots remain in coverage denominators.',
   'Separate normalized candidate axes are not a common calibrated ideology scale; visual shape/ordering comparisons are descriptive.',
   'The upstream CSV ignore-values parser is not reused; all main ranks obey Alaska barriers.',
   'Candidate-axis direction is arbitrary. Supplied display reflections are applied to both candidates and voter placements.',
   'Cohort membership is joined by ballot ID, but artificial interval points are not individually paired across races; no cross-axis individual-location correlation is estimated.']}
 (OUT/'results.json').write_text(json.dumps(record,indent=2))
 (OUT/'METHODOLOGY.txt').write_text('''VOTER DISTRIBUTIONS: METHOD AND IDENTIFICATION LIMITS

The original Mahshad rcv_distribution.py plot_KDE places a pattern with c ballots
at np.linspace(lo,hi,c), where solve_lp finds the interval consistent with all
ranked candidate-pair distances. It pins a one-name ballot at that candidate.
This follow-up preserves those allocation conventions while using the corrected
OG positive-width strict ranked-only feasibility and Alaska-countable prefixes.
The domain is [0,1] because candidate axes are normalized to [0,1]; the upstream
[0,n-1] domain corresponds to that code's own coordinate scaling. No unranked
candidate is silently added as a lower-preference constraint.

Input data are the three unchanged Rachel November11 CSVs only. Senate groups
use literal rank1, fixed at their original full sizes. IDs are normalized and
joined, never matched by row order. For each other race, a missing row is missing;
130 governor records are absent. A generic write-in occupies its original rank
while overvote/double-skip barriers are applied, then is removed from the
four-candidate model. No whole irregular ballot is silently discarded.

A ranking defines an interval of permissible voter locations, not a uniquely
estimated voter point. For a ranked adjacent pair a before b, distance order
requires x<(a+b)/2 if a<b, and x>(a+b)/2 if a>b. Intersect these constraints with
[0,1]. A positive-width interval is consistent; an empty ranking or inconsistent
ranking is not plotted. One-name ballots impose no ranked-pair constraint, so
their full feasible interval is [0,1]. Pinning them to the sole named candidate
is a Mahshad visualization assumption, not a finding about their true location.
The singleton-uniform sensitivity explicitly shows the consequence of replacing
that convention. Single-name spikes should not be interpreted as measured voter
ideological concentrations. Distribution medians/means depend on these assumptions.

Finite np.linspace points are saved in imputed_points.npz. Endpoint allocation
matches the plotting convention, though strict feasibility concerns the open
interval interior; the endpoints should not be read as additional strict ballots.
For density presentation, fixed bandwidth within each race makes Senate-cohort
curves comparable. The bandwidth uses the actual repeated-point N and unbiased
SD of all located ballots: h=SD*N^(-1/5). Compressed-profile effective sample size
is not used. The table also reports each cohort's own Scott bandwidth and the
density_grid.csv includes that sensitivity. No axis is refitted to a subgroup.

The displayed KDE bins finite points into8192bins and uses Gaussian smoothing
with reflected boundaries at0and1. Each conditional curve integrates to1. An
independent direct finite-point reflected Gaussian kernel evaluation at at least
41grid locations, plus candidate coordinates, checks the numerical approximation.
All192possible nonempty partial rankings across the3axes are checked by an
independent all-pair-midpoint cell sweep. Coverage separately tracks full cohort,
missing source, empty named prefix, inconsistent prefix and plotted records.

Senate, Governor and House are separately fitted candidate spaces. Display axes
are reflected only for readability, using the axis model's saved transformation;
their normalized distances are not a common ideology measurement. Compare shapes
and candidate ordering descriptively, without reading one race's x=.4 as the same
latent ideology as another race's x=.4. This is full-profile descriptive analysis,
not held-out prediction and not a measure of knowledge, sincerity or confusion.

The stronger observed-only100outer×16starts fit preserves candidate order and
gamma in all three contests, but moves some candidate coordinates. The separate
axis_geometry_sensitivity.csv recomputes every group's finite allocation on those
stronger-fit axes, with the same display reflection. It reports imputed mean and
median changes, exact finite-point empirical CDF differences and density changes
holding the main full-axis bandwidth fixed. The main plots retain the prespecified
20×8fits; stronger fits are not selected because they give desirable voter shapes.

Cohort identity is joined across offices by ballotID. Within a ranking pattern,
there is no identified pairing between individual voter IDs and artificial
linspace points. These are cohort distributions, not individual-location
trajectories or cross-axis voter-coordinate correlations.
''')
 print(json.dumps({'status':'passed','coverage_rows':len(coverage_rows),'independent_interval_checks':interval_checks,
  'max_KDE_relative_probe_error':record['max_binned_KDE_error_fraction_probe_peak']},indent=2))
 return record

if __name__=='__main__':
 if '--render-only' in sys.argv:render_saved_figures()
 else:main()
