"""Tables and figures for the new Sam notebook; analyses live in their own modules."""
from pathlib import Path
import csv,json,html
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from IPython.display import display,HTML,Image

from analysis.shared.paths import REPO_ROOT, REPORTING_ROOT, INPUTS_ROOT, model_dir, resolve_recorded_path
ROOT=REPO_ROOT
COLORS={525:'#2869a6',526:'#d59b36',524:'#8061aa',527:'#bb4f51'}
SHORT={525:'Mary Peltola',526:'Daniel J. Sullivan Jr.',524:'Gerald Heikes',527:'Dan S. Sullivan'}
RACES=['us_senate','governor','us_house']
TITLES={'us_senate':'Senate','governor':'Governor','us_house':'House'}

def load(path):return json.loads((ROOT/path).read_text())
def image(path,width=1100):display(Image(filename=str(ROOT/path),width=width))

def theme():
 plt.rcParams.update({'font.family':'DejaVu Sans','text.color':'#243449','axes.labelcolor':'#344d66',
  'xtick.color':'#40566f','ytick.color':'#40566f','figure.facecolor':'white','axes.facecolor':'white',
  'savefig.facecolor':'white','font.size':11,'svg.fonttype':'none'})
 display(HTML('''<style>
 .sam-title{font:600 34px/1.2 Arial,sans-serif;color:#18324e;margin:10px 0 20px}
 .sam-kicker{font:600 12px Arial,sans-serif;color:#567a96;letter-spacing:1.2px;text-transform:uppercase}
 .sam-table{border-collapse:collapse;width:100%;font:13px/1.5 Arial,sans-serif;margin:12px 0 28px}
 .sam-table th{background:#1c3d5b;color:white;padding:11px;text-align:right}
 .sam-table td{padding:11px;border-bottom:1px solid #dde6ec;text-align:right;white-space:nowrap}
 .sam-table td:first-child,.sam-table th:first-child{text-align:left;white-space:normal;min-width:145px}
 .sam-table tr:nth-child(even) td{background:#f4f7fa}.sam-table caption{text-align:left;font-weight:600;font-size:16px;color:#243b53;padding:12px 0}
 .sam-scroll{max-width:100%;overflow-x:auto}.sam-wide-table{min-width:1050px}
 .sam-note{border-left:4px solid #5d90b4;background:#f1f6f9;padding:13px 16px;color:#334d65;margin:16px 0}
 </style>'''))

def table(frame,title=None):
 if not isinstance(frame,pd.DataFrame):frame=pd.DataFrame(frame)
 markup=frame.to_html(index=False,escape=True,border=0,classes='sam-table'+(' sam-wide-table' if len(frame.columns)>=7 else ''))
 if title:markup=markup.replace('<thead>','<caption>'+html.escape(title)+'</caption><thead>',1)
 display(HTML('<div class="sam-scroll">'+markup+'</div>'))

def first_choice_comparison():
 d=load('analysis/cross_race/first_choices/descriptive_results.json');q=d['question1_usable_prefix_categories'];n=d['question1_literal_rank1_daniel_j_n']
 labels=[('peltola_above_senator_both_ranked','Both countable: Peltola above Dan S.'),
 ('senator_above_peltola_both_ranked','Both countable: Dan S. above Peltola'),
 ('peltola_only_explicitly_ranked','Only Peltola countable among the finalists'),
 ('senator_only_explicitly_ranked','Only Dan S. countable among the finalists'),
 ('neither_explicitly_ranked','Neither finalist countable')]
 table([{'Countable rankings':label,'Ballots':f'{q[key]:,}','Share of Daniel-first cohort':f'{100*q[key]/n:.2f}%'} for key,label in labels],f'Daniel J. Sullivan Jr.: same {n:,} literal first-choice ballots')

def cross_table(race,party=False):
 file='first_choice_party_crosstabs.csv' if party else 'first_choice_candidate_crosstabs.csv'
 df=pd.read_csv(ROOT/'analysis/cross_race/first_choices'/file);df=df[df.other_contest==race]
 aliases={'blank_rank1':'Blank rank 1','overvote_rank1':'Overvote rank 1','not_in_governor_file':'Absent governor record','Write-in':'Write-in'}
 cols=sorted(df.other_first_choice.unique(),key=lambda x:(x in aliases,x));rows=[]
 for cid in [525,526,524,527]:
  part=df[df.senate_candidate_id==cid].set_index('other_first_choice');n=int(part.senate_cohort_n.iloc[0]);row={'Senate first choice':SHORT[cid],'Cohort N':f'{n:,}'}
  for col in cols:
   count=int(part.loc[col,'ballots']) if col in part.index else 0
   row[aliases.get(col,col)]=f'{count:,} ({100*count/n:.1f}%)'
  rows.append(row)
 table(rows,TITLES[race]+(' affiliations' if party else ' first choices')+' within Senate literal-rank-1 groups')

def axis_summary():
 rows=[]
 for race in RACES:
  d=json.loads((model_dir(race)/'mds_results.json').read_text())
  for entry in d['summary'][:2]:
   rows.append({'Election':TITLES[race],'Scored group':'All nonempty' if entry['group']=='All nonempty' else 'Three/four names',
    'N':f"{entry['ballots']:,}",'Gamma':f"{100*entry['observed_consistency']:.2f}%",'Random mean':f"{100*entry['random_mean']:.2f}%",
    'Difference (pp)':f"{entry['excess_percentage_points']:+.2f}",'Random-mean MCSE (pp)':f"{100*entry['random_mcse']:.2f}"})
 table(rows,'Full-profile OG consistency; 49 matched-tail randomized fits per election')

def plot_axes():
 labels={'Heikes, Gerald L.':'Gerald Heikes','Peltola, Mary':'Mary Peltola','Sullivan, Daniel J. Jr.':'Daniel J. Sullivan Jr.','Sullivan, Dan S.':'Dan S. Sullivan',
 'Bronson/Church':'Bronson / Church','Kreiss-Tomkins/Johnson':'Kreiss-Tomkins / Johnson','Taylor/English':'Taylor / English','Wilson/Shower':'Wilson / Shower',
 'Begich, Nick':'Nick Begich','Hafner, Eric':'Eric Hafner','Hill, Bill':'Bill Hill','McDermott, James C. "Jim"':'Jim McDermott'}
 fig,axs=plt.subplots(3,1,figsize=(12,6.9))
 for ax,race in zip(axs,RACES):
  df=pd.read_csv(model_dir(race)/'candidate_axis.csv');column='display_axis_position' if 'display_axis_position' in df else 'axis_position';df=df.sort_values(column)
  ax.axhline(0,color='#c5d1dc',lw=3,zorder=0)
  for i,(_,row) in enumerate(df.iterrows()):
   x=float(row[column]);ax.scatter([x],[0],s=140,color=COLORS.get(int(row.candidate_id),'#547991'),edgecolor='white',lw=1.5,zorder=2)
   y=.27 if i%2==0 else -.27
   ax.text(x,y,labels[row.candidate]+'\n'+f'{x:.3f}',ha='center',va='center',fontsize=10,fontweight='bold')
  ax.set_xlim(-.13,1.13);ax.set_ylim(-.62,.62);ax.axis('off');ax.set_title(TITLES[race]+' candidate axis',loc='left',fontsize=13,fontweight='bold')
 fig.text(.08,.025,'Each election is normalized separately; matching coordinates across elections do not identify the same ideology.',fontsize=10,color='#61798e')
 fig.subplots_adjust(left=.08,right=.96,top=.95,bottom=.08,hspace=.25)
 path=ROOT/'analysis/reporting/figures/three_candidate_axes.png';path.parent.mkdir(parents=True,exist_ok=True);fig.savefig(path,dpi=190);fig.savefig(path.with_suffix('.svg'));plt.close(fig)
 image('analysis/reporting/figures/three_candidate_axes.png')

def distribution_coverage(focal=False):
 df=pd.read_csv(ROOT/'analysis/cross_race/voter_distributions/voter_distribution_coverage.csv');df=df[df.senate_group.astype(str).isin(['525','526'] if focal else ['525','526','524','527'])]
 rows=[]
 for _,r in df.iterrows():
  rows.append({'Senate first choice':r.group_name,'Axis':TITLES[r.contest],'Cohort N':f'{int(r.cohort_n):,}',
   'Plotted':f'{int(r.plotted):,} ({100*r.plotted/r.cohort_n:.1f}%)','Inconsistent':f'{int(r.inconsistent):,}',
   'No usable named choice':f'{int(r.no_named_usable_preference):,}','Missing row':int(r.missing_source_rows)})
 table(rows,'Placement coverage; every full cohort is accounted for')

def focal_position_summaries():
 df=pd.read_csv(ROOT/'analysis/cross_race/voter_distributions/voter_distribution_summary.csv');df=df[df.senate_group.astype(str).isin(['525','526'])]
 rows=[]
 for _,r in df.iterrows():
  rows.append({'Senate first choice':r.group_name,'Axis':TITLES[r.contest],
   'Imputed mean':f'{r.imputed_mean:.3f}','Imputed median':f'{r.imputed_median:.3f}',
   'Median, singleton-uniform sensitivity':f'{r.singleton_uniform_sensitivity_median:.3f}'})
 table(rows,'Placement-dependent summaries; each election has its own coordinate system')

def routes_and_omissions():
 d=load('analysis/senate/rankings/confusion_results.json')['cohorts']['literal_rank1_daniel']
 table([{'Hypothetical usable route':'Dan J. → Daniel S.','Ballots':d['actual_reach_incumbent_routes']['after_Daniel_direct_to_incumbent']},
 {'Hypothetical usable route':'Dan J. → Heikes → Daniel S.','Ballots':d['actual_reach_incumbent_routes']['after_Daniel_to_Heikes_then_incumbent']},
 {'Hypothetical usable route':'Total reaching Daniel S.','Ballots':d['final_destinations']['Dan S. Sullivan']}],
 'Recorded fallback support in the hypothetical replay; these counts do not identify confused voters')
 x=d['incumbent_visibility_status']
 table([{'Incumbent in Rachel’s source / usable rankings':'Countable incumbent preference','Ballots':x['incumbent_countable']},
 {'Incumbent in Rachel’s source / usable rankings':'Not named in any coded rank; no overvote token','Ballots':x['incumbent_not_named_in_coded_cells_no_overvote']},
 {'Incumbent in Rachel’s source / usable rankings':'Not visibly named; overvote could hide a name','Ballots':x['incumbent_not_visible_hidden_overvote_membership_unknown']},
 {'Incumbent in Rachel’s source / usable rankings':'Visibly named only beyond a counting barrier','Ballots':x['incumbent_visible_only_beyond_counting_barrier']}],
 '“Not countable” and “not ranked anywhere” are different source questions')

def finalist_route_comparison():
 df=pd.read_csv(ROOT/'analysis/senate/rankings/dan_j_first_finalist_routes.csv')
 assert df.total.sum()==3940
 table(pd.DataFrame({
  'Hypothetical final destination':df.final_destination,
  'Directly after Dan J. is eliminated':df.direct_after_Dan_J_elimination.map(lambda x:f'{x:,}'),
  'Through Heikes':df.via_Heikes.map(lambda x:f'{x:,}'),
  'Total ballots':df.total.map(lambda x:f'{x:,}'),
  'Share of all 3,940':df.pct_of_full_cohort.map(lambda x:f'{x:.2f}%')}),
  'Dan J.–first ballots: hypothetical routes to both finalists and inactivity')

def permutation_table():
 df=pd.read_csv(ROOT/'analysis/senate/rankings/daniel_first_usable_permutations.csv')
 df=df.sort_values('literal_rank1_daniel_ballots',ascending=False)
 for column in ['named_usable_permutation','after_Daniel_elimination','final_destination']:
  df[column]=df[column].str.replace('Daniel J. Sullivan Jr.','Dan J.',regex=False).str.replace('Dan S. Sullivan','Daniel S.',regex=False)
 table(df[['named_usable_permutation','literal_rank1_daniel_ballots','after_Daniel_elimination','final_destination']].rename(columns={
  'named_usable_permutation':'Usable named ranking','literal_rank1_daniel_ballots':'Dan J.–first ballots',
  'after_Daniel_elimination':'If Dan J. is eliminated','final_destination':'Hypothetical final destination'}),
  'All 16 Dan J.–first usable named permutations; write-in removed after applying barriers')

def upper_bounds():
 df=pd.read_csv(ROOT/'analysis/senate/rankings/conditional_upper_bound_scenarios.csv')
 choices={'no_countable_incumbent':'No countable incumbent preference','no_visible_incumbent_no_overvote':'No coded incumbent name; no overvote','all_literal_Daniel_first':'All literal Daniel-first ballots'}
 rows=[]
 for key,label in choices.items():
  r=df[df.scenario==key].iloc[0]
  rows.append({'Assumed confused set':label,'Set N':int(r.subset_ballots),'Already reaches Dan':int(r.already_reaches_incumbent),
   'Currently Peltola':int(r.currently_Peltola),'Currently inactive':int(r.currently_inactive),
   'Ceiling: extra Dan votes':int(r.maximum_additional_incumbent_votes_in_this_scenario),
   'Ceiling: Dan–Peltola margin gain':int(r.maximum_Dan_minus_Peltola_margin_increase)})
 table(rows,'Strong-assumption ceilings within specified sets; actual confusion could be zero')
