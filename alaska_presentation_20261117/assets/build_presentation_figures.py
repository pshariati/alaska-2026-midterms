"""Presentation-only rendering of saved, verified Rachel November 11 results.

No ballot interpretation, MDS fitting, density estimation, or notebook mutation.
Run with the existing audited notebook Python environment.
"""
from pathlib import Path
from collections import defaultdict
import csv
import hashlib
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from matplotlib.ticker import PercentFormatter, MaxNLocator

OUT = Path(__file__).resolve().parent
PROJECT = OUT.parent.parent
ROOT = PROJECT / 'alaska_2026_sam_followup_20261116'
NAVY = '#243449'
TEXT = '#40566f'
LINE = '#c5d1db'
GRID = '#e9edf1'
PARTY = {'Democrat': '#2c73b5', 'Republican': '#c34c50',
         'Independent / Nonpartisan': '#dfa92e', 'Libertarian': '#8560aa'}
BAR = {'Democrat/Nonpartisan': '#397aad', 'Democrat': '#397aad',
       'Nonpartisan': '#5e9988', 'Republican': '#ba5355',
       'Libertarian': '#c29739', 'Other / blank / overvote': '#bdc9d3'}
ORDER = [525, 526, 524, 527]
SENATE_PARTIES = ['Democrat', 'Independent / Nonpartisan', 'Republican', 'Republican']
SENATE_LABELS = ['Mary Peltola', 'Dan J.', 'Gerald Heikes', 'Daniel S.']
TICK_LABELS = ['Mary\nPeltola', 'Dan J.', 'Gerald\nHeikes', 'Daniel S.']
RACES = ['us_senate', 'governor', 'us_house']
TITLE = {'us_senate': 'Senate', 'governor': 'Governor', 'us_house': 'House'}
NAMES = {525:'Mary Peltola',526:'Dan J.',524:'Gerald Heikes',527:'Daniel S.',
         538:'Kreiss-Tomkins / Johnson',536:'Taylor / English',537:'Bronson / Church',539:'Wilson / Shower',
         529:'Eric Hafner',530:'Bill Hill',531:'Jim McDermott',528:'Nick Begich'}
SHORT = {525:'Peltola',526:'Dan J.',524:'Heikes',527:'Daniel S.',
         538:'Kreiss-Tomkins',536:'Taylor',537:'Bronson',539:'Wilson',
         529:'Hafner',530:'Hill',531:'McDermott',528:'Begich'}
PARTIES = {525:'Democrat',526:'Independent / Nonpartisan',524:'Republican',527:'Republican',
           538:'Democrat',536:'Republican',537:'Republican',539:'Republican',
           529:'Democrat',530:'Independent / Nonpartisan',531:'Libertarian',528:'Republican'}
SPECS = [('governor', 'Governor first choice', ['Democrat/Nonpartisan','Republican','Other / blank / overvote']),
         ('us_house', 'House first choice', ['Democrat','Nonpartisan','Libertarian','Republican','Other / blank / overvote'])]
SOURCES = [ROOT/'completed/descriptive/first_choice_party_crosstabs.csv',
           ROOT/'voter_distributions/density_grid.csv',
           ROOT/'voter_distributions/voter_distribution_coverage.csv']
SOURCES += [ROOT/'axis_models'/r/'candidate_axis.csv' for r in RACES]
MANIFEST = {'source_snapshot':'Rachel/FairVote November 11, 2026',
            'purpose':'Presentation-only rendering; saved values and fits unchanged.',
            'sources':[], 'assets':[], 'affiliation_values':[], 'candidate_axes':{}, 'density_coverage':{}}

def rows(path):
    with path.open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))

COUNTS = defaultdict(int)
COHORTS = {}
for r in rows(SOURCES[0]):
    candidate = int(r['senate_candidate_id'])
    group = r['other_first_choice']
    if group not in BAR:
        group = 'Other / blank / overvote'
    COUNTS[r['other_contest'],candidate,group] += int(r['ballots'])
    cohort = int(r['senate_cohort_n'])
    assert COHORTS.get(candidate,cohort) == cohort
    COHORTS[candidate] = cohort

AXES = {}
for race in RACES:
    data = rows(ROOT/'axis_models'/race/'candidate_axis.csv')
    AXES[race] = sorted([(int(r['candidate_id']),float(r['display_axis_position'])) for r in data], key=lambda p:p[1])
    MANIFEST['candidate_axes'][race] = [dict(candidate_id=c, public_label=NAMES[c], coordinate=x, party=PARTIES[c]) for c,x in AXES[race]]

DENSITY = {race:{'x':[],'y':[]} for race in RACES}
FOCAL = {(race,group):{'x':[],'y':[]} for race in RACES for group in ('525','526')}
for r in rows(ROOT/'voter_distributions/density_grid.csv'):
    if r['senate_group'] == 'all':
        item = DENSITY[r['contest']]
        item['x'].append(float(r['coordinate']))
        item['y'].append(float(r['density_common_axis_bandwidth']))
    elif r['senate_group'] in ('525','526'):
        item = FOCAL[r['contest'],r['senate_group']]
        item['x'].append(float(r['coordinate']))
        item['y'].append(float(r['density_common_axis_bandwidth']))
for r in rows(ROOT/'voter_distributions/voter_distribution_coverage.csv'):
    if r['senate_group'] == 'all':
        race = r['contest']
        DENSITY[race]['plotted'] = int(r['plotted'])
        DENSITY[race]['source'] = int(r['source_rows_present'])
        MANIFEST['density_coverage'][race] = {'plotted':int(r['plotted']), 'source':int(r['source_rows_present']), 'saved_grid_n':len(DENSITY[race]['x'])}
    elif r['senate_group'] in ('525','526'):
        FOCAL[r['contest'],r['senate_group']]['plotted'] = int(r['plotted'])
        FOCAL[r['contest'],r['senate_group']]['cohort'] = int(r['cohort_n'])

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'text.color':NAVY,
    'axes.labelcolor':TEXT,'xtick.color':TEXT,'ytick.color':TEXT,
    'figure.facecolor':'white','axes.facecolor':'white','savefig.facecolor':'white',
    'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})

def save(fig, stem, note):
    fig.savefig(OUT/(stem+'.png'), dpi=240, facecolor='white')
    fig.savefig(OUT/(stem+'.svg'), facecolor='white')
    MANIFEST['assets'].append({'name':stem,'files':[stem+'.png',stem+'.svg'],
        'size_inches':list(fig.get_size_inches()),'note':note})
    plt.close(fig)

def party_handles():
    return [Line2D([0],[0],marker='o',color='none',markerfacecolor=color,
                   markeredgecolor='white',markersize=9,label=party)
            for party,color in PARTY.items()]

def order_strip(ax):
    ax.set_xlim(-.62,3.62);ax.set_ylim(0,1);ax.axis('off')
    ax.plot([-.45,3.45],[.28,.28],color=LINE,lw=2.5,zorder=0)
    for i,(name,party) in enumerate(zip(SENATE_LABELS,SENATE_PARTIES)):
        ax.scatter(i,.28,s=95,c=PARTY[party],edgecolors='white',lw=1.5,zorder=3)
        ax.text(i,.63,name,ha='center',va='bottom',fontsize=11.7,fontweight='bold')
    ax.text(-.62,1.05,'Senate candidate order',ha='left',va='bottom',fontsize=10.7,color=TEXT)

def affiliation_panel(fig, race, title, groups, barpos, strippos, titley, legendy):
    ax = fig.add_axes(barpos)
    order_strip(fig.add_axes(strippos))
    fig.text(barpos[0],titley,title,ha='left',va='top',fontsize=18,fontweight='bold')
    ax.set_axisbelow(True);ax.grid(axis='y',color=GRID,lw=.8)
    bottom = np.zeros(4)
    for group in groups:
        values = np.array([100*COUNTS[race,c,group]/COHORTS[c] for c in ORDER])
        ax.bar(range(4), values,bottom=bottom,width=.53,color=BAR[group],edgecolor='none',zorder=3)
        for i,(v,b) in enumerate(zip(values,bottom)):
            if v>=8:
                ax.text(i,b+v/2,f'{v:.1f}%',ha='center',va='center',color='white',fontsize=13,fontweight='bold')
        bottom += values
    assert np.allclose(bottom,100,atol=1e-11)
    ax.set(xlim=(-.62,3.62),ylim=(0,100))
    ax.set_yticks([0,25,50,75,100]);ax.yaxis.set_major_formatter(PercentFormatter(100,decimals=0))
    ax.set_xticks(range(4),TICK_LABELS);ax.tick_params(axis='both',length=0,pad=8)
    ax.spines['left'].set_visible(False);ax.spines['bottom'].set_color(LINE)
    fig.canvas.draw()
    box = ax.get_xticklabels()[0].get_window_extent(fig.canvas.get_renderer())
    px,py = fig.transFigure.inverted().transform((box.x0-9,(box.y0+box.y1)/2))
    fig.text(px,py,'Senate 1st choice:',ha='right',va='center',fontsize=10.5,color=TEXT)
    fig.legend(handles=[Patch(color=BAR[g],label=g) for g in groups],loc='upper center',
        bbox_to_anchor=(barpos[0]+barpos[2]/2,legendy),ncol=3,frameon=False,
        fontsize=10.5,handlelength=1.6,columnspacing=1.6,handletextpad=.6)
    return ax

def affiliations():
    fig = plt.figure(figsize=(10.7,11.1))
    for spec,barpos,strippos,titley,legendy in zip(SPECS,
        [[.16,.618,.81,.218],[.16,.164,.81,.218]],
        [[.16,.850,.81,.063],[.16,.396,.81,.063]],
        [.968,.514],[.56,.097]):
        affiliation_panel(fig,*spec,barpos,strippos,titley,legendy)
    fig.text(.025,.52,'Share within each Senate first-choice cohort (%)',rotation=90,ha='center',va='center',fontsize=12.5,color=TEXT)
    fig.text(.16,.018,'Candidate order follows Senate MDS; bar centers are equally spaced.\nRachel/FairVote November 11 snapshot · candidate affiliation, not voter registration.',fontsize=8.8,color=TEXT,linespacing=1.5)
    save(fig,'affiliations_with_senate_order','Original affiliation percentages and stack colors unchanged. Equal-spacing strip encodes candidate order, not MDS distance.')
    for race,title,groups in SPECS:
        fig = plt.figure(figsize=(11,6.1))
        ax = affiliation_panel(fig,race,title,groups,[.16,.28,.81,.39],[.16,.71,.81,.105],.965,.147)
        ax.set_ylabel('Share within Senate cohort (%)',labelpad=11,fontsize=11.5)
        fig.text(.16,.018,'Order from Senate MDS; equal bar spacing is not fitted distance.  |  Rachel/FairVote, November 11, 2026',fontsize=9.5,color=TEXT)
        save(fig,race.replace('us_','')+'_first_choice','Presentation crop of unchanged affiliation percentages with equal-spaced Senate order strip.')

def axis_panel(ax,race, big=False):
    ax.set_xlim(-.12,1.12);ax.set_ylim(-.9,.9);ax.axis('off')
    ax.plot([-.12,1.12],[0,0],color=LINE,lw=3,zorder=0)
    for i,(candidate,x) in enumerate(AXES[race]):
        ax.scatter(x,0,s=160 if big else 125,c=PARTY[PARTIES[candidate]],edgecolors='white',lw=1.6,zorder=3)
        dy=.30 if i%2==0 else -.30
        label=NAMES[candidate]
        if race=='governor': label=label.replace(' / ',' /\n') if big else label
        ax.text(x,dy,label+f'\n{x:.3f}',ha='center',va='bottom' if dy>0 else 'top',fontsize=13 if big else 11.8,fontweight='bold',linespacing=1.2)
    ax.set_title(TITLE[race]+' candidate axis',loc='left',fontsize=17 if big else 15,fontweight='bold',pad=9)

def candidate_axes():
    fig,axs = plt.subplots(3,1,figsize=(11.5,7.8))
    for ax,race in zip(axs,RACES): axis_panel(ax,race)
    fig.subplots_adjust(left=.055,right=.97,top=.95,bottom=.17,hspace=.55)
    fig.legend(handles=party_handles(),loc='lower center',bbox_to_anchor=(.5,.075),ncol=4,frameon=False,fontsize=10.5,columnspacing=1.5,handletextpad=.3)
    fig.text(.055,.023,'Separate normalized maps; direction is arbitrary. Distances are not a calibrated ideology scale.\nGovernor blue marks a Democrat/Nonpartisan ticket. Rachel/FairVote November 11 snapshot.',fontsize=10,color=TEXT,linespacing=1.5)
    save(fig,'candidate_axes_party','Saved numeric MDS coordinates unchanged; House saved display reflection retained. Party colors apply to candidate annotations.')
    for race in RACES:
        fig,ax=plt.subplots(figsize=(11.5,3.8))
        axis_panel(ax,race,True)
        fig.subplots_adjust(left=.055,right=.97,top=.82,bottom=.25)
        fig.legend(handles=party_handles(),loc='lower center',bbox_to_anchor=(.5,.085),ncol=4,frameon=False,fontsize=10.5,columnspacing=1.5,handletextpad=.3)
        fig.text(.055,.025,'Normalized candidate positions · axis direction is arbitrary · Rachel/FairVote November 11 snapshot',fontsize=10,color=TEXT)
        save(fig,race.replace('us_','')+'_candidate_axis','Individual crop of saved fitted candidate axis, recolored by party.')

def density_panel(ax,race):
    item = DENSITY[race]
    x=np.array(item['x']); y=np.array(item['y'])
    assert len(x)==8192 and np.all(np.diff(x)>0) and np.all(y>=0)
    ax.plot(x,y,color='#426f90',lw=2.1)
    ax.fill_between(x,0,y,color='#426f90',alpha=.13)
    ax.set_xlim(0,1);ax.set_ylim(0,None);ax.yaxis.set_major_locator(MaxNLocator(nbins=4,integer=True))
    ax.set_xticks(np.linspace(0,1,6));ax.grid(axis='y',color=GRID,lw=.7);ax.set_axisbelow(True)
    ax.spines['left'].set_color('#758698');ax.spines['bottom'].set_color('#758698')
    ax.tick_params(axis='both',labelsize=10,length=3)
    for j,(c,pos) in enumerate(AXES[race]):
        ax.axvline(pos,color=LINE,lw=.75,ls=(0,(2,3)),zorder=0)
        ax.annotate(SHORT[c],xy=(pos,0),xycoords=('data','axes fraction'),xytext=(0,-23 if j%2==0 else -38),textcoords='offset points',ha='center',va='top',fontsize=9.7,color=TEXT)
    ax.set_title(f"{TITLE[race]} axis — {item['plotted']:,} plotted / {item['source']:,} source ballots",loc='left',fontweight='bold',fontsize=12.4,pad=11)

def densities():
    fig,axs=plt.subplots(3,1,figsize=(8.7,9.2))
    for ax,race in zip(axs,RACES): density_panel(ax,race)
    fig.suptitle('Estimated voter distributions',x=.11,y=.974,ha='left',fontsize=19,fontweight='bold')
    fig.text(.11,.921,'Mahshad’s allocation convention',fontsize=11.5,color=TEXT)
    fig.text(.023,.55,'Estimated voter density',rotation=90,ha='center',va='center',fontsize=12.5,color=TEXT)
    axs[-1].set_xlabel('Normalized candidate-axis coordinate',labelpad=43,fontsize=11.5)
    fig.subplots_adjust(left=.11,right=.96,top=.855,bottom=.225,hspace=.95)
    fig.text(.11,.036,'Positions are assigned from rankings, not directly observed or uniquely identified.\nConditional on spatial consistency; one-name ballots are placed at their candidate.\nEach curve integrates to 1 among plotted ballots. Rachel/FairVote November 11 snapshot.',fontsize=9.3,color=TEXT,linespacing=1.55)
    save(fig,'all_voters_density_compact','Saved all-voter density_common_axis_bandwidth curves, coverage totals and coordinates unchanged; narrower rendering and clearer public labels.')
    for race in RACES:
        fig,ax=plt.subplots(figsize=(9.6,4.8))
        density_panel(ax,race)
        ax.set_ylabel('Estimated voter density',fontsize=11.5)
        ax.set_xlabel('Normalized candidate-axis coordinate',labelpad=43,fontsize=11.5)
        fig.subplots_adjust(left=.095,right=.96,top=.88,bottom=.32)
        fig.text(.095,.045,'Mahshad allocation convention: assigned positions, not directly observed locations.\nConditional on spatial consistency; Rachel/FairVote November 11 snapshot.',fontsize=10,color=TEXT,linespacing=1.5)
        save(fig,race.replace('us_','')+'_voter_density','Individual all-voter density panel using saved arrays without recalculation.')

def focal_panel(ax,race):
    for group,name,color in [('525','Mary Peltola',PARTY['Democrat']),('526','Dan J.',PARTY['Independent / Nonpartisan'])]:
        item=FOCAL[race,group]
        assert len(item['x'])==8192
        share=100*item['plotted']/item['cohort']
        ax.plot(item['x'],item['y'],color=color,lw=2.3,label=f'{name} ({share:.1f}% plotted)')
    ax.set_xlim(0,1);ax.set_ylim(0,None);ax.yaxis.set_major_locator(MaxNLocator(nbins=4,integer=True))
    ax.set_xticks(np.linspace(0,1,6));ax.grid(axis='y',color=GRID,lw=.7);ax.set_axisbelow(True)
    ax.spines['left'].set_color('#758698');ax.spines['bottom'].set_color('#758698')
    ax.tick_params(axis='both',labelsize=10,length=3)
    for j,(c,pos) in enumerate(AXES[race]):
        ax.axvline(pos,color=LINE,lw=.75,ls=(0,(2,3)),zorder=0)
        ax.annotate(SHORT[c],xy=(pos,0),xycoords=('data','axes fraction'),xytext=(0,-23 if j%2==0 else -38),textcoords='offset points',ha='center',va='top',fontsize=9.7,color=TEXT)
    ax.set_title(TITLE[race]+' axis',loc='left',fontweight='bold',fontsize=13,pad=11)
    ax.legend(loc='upper right',frameon=False,fontsize=9.2)

def focal_densities():
    fig,axs=plt.subplots(3,1,figsize=(8.7,9.2))
    for ax,race in zip(axs,RACES): focal_panel(ax,race)
    fig.suptitle('Peltola and Dan J. first-choice voters',x=.11,y=.974,ha='left',fontsize=18,fontweight='bold')
    fig.text(.11,.921,'Estimated voter distributions on each election’s candidate axis',fontsize=11.3,color=TEXT)
    fig.text(.023,.55,'Estimated voter density',rotation=90,ha='center',va='center',fontsize=12.5,color=TEXT)
    axs[-1].set_xlabel('Normalized candidate-axis coordinate',labelpad=43,fontsize=11.5)
    fig.subplots_adjust(left=.11,right=.96,top=.855,bottom=.225,hspace=.95)
    fig.text(.11,.036,'First-choice groups are defined by literal Senate rank 1. Curves integrate to 1 among\nplotted ballots. Mahshad allocation convention assigns positions; they are not directly\nobserved or uniquely identified. Rachel/FairVote November 11 snapshot.',fontsize=9.3,color=TEXT,linespacing=1.55)
    save(fig,'peltola_dan_j_across_three_axes','Only requested two focal Senate first-choice groups; saved density grids and full-cohort plotted percentages unchanged. Not the excluded four-group overlay.')
    for race in RACES:
        fig,ax=plt.subplots(figsize=(9.6,4.8))
        focal_panel(ax,race)
        ax.set_ylabel('Estimated voter density',fontsize=11.5)
        ax.set_xlabel('Normalized candidate-axis coordinate',labelpad=43,fontsize=11.5)
        fig.subplots_adjust(left=.095,right=.96,top=.88,bottom=.32)
        fig.text(.095,.045,'Literal Senate first-choice groups. Curves integrate to 1 among plotted ballots.\nMahshad allocation convention · assigned positions · Rachel/FairVote November 11 snapshot.',fontsize=10,color=TEXT,linespacing=1.5)
        save(fig,race.replace('us_','')+'_peltola_dan_j_density','Individual two-cohort density panel using saved arrays and preferred aliases.')

def main():
    for source in SOURCES:
        MANIFEST['sources'].append({'file':str(source.relative_to(PROJECT)), 'sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
    for race,_,groups in SPECS:
        for candidate in ORDER:
            for group in groups:
                MANIFEST['affiliation_values'].append({'contest':race,'senate_candidate_id':candidate,'label':NAMES[candidate],'group':group,'ballots':COUNTS[race,candidate,group],'cohort_n':COHORTS[candidate],'percent':100*COUNTS[race,candidate,group]/COHORTS[candidate]})
    affiliations();candidate_axes();densities();focal_densities()
    (OUT/'asset_manifest.json').write_text(json.dumps(MANIFEST,indent=2),encoding='utf-8')
    print(json.dumps({'asset_count':len(MANIFEST['assets']),'files':[x['name'] for x in MANIFEST['assets']],'coverage':MANIFEST['density_coverage']},indent=2))

if __name__=='__main__':main()
