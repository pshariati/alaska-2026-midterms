"""Reformat the audited Rachel-only affiliation figure without changing its values."""
from pathlib import Path
from analysis.shared.paths import REPO_ROOT, INPUTS_ROOT, REFERENCES_ROOT, SHARED_ROOT, race_dir, model_dir, cross_race_dir, resolve_recorded_path
from collections import defaultdict
import csv,hashlib,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import PercentFormatter

OUT=Path(__file__).resolve().parent
ROOT=REPO_ROOT
SOURCE=cross_race_dir('first_choices')/'first_choice_party_crosstabs.csv'
# Swap only the two Sullivans relative to the original Peltola/Dan/Heikes/Daniel order.
ORDER=[525,526,524,527]
LABELS=['Mary\nPeltola','Daniel J.\nSullivan Jr.','Gerald\nHeikes','Dan S.\nSullivan']
COLORS={'Democrat/Nonpartisan':'#397aad','Democrat':'#397aad',
        'Nonpartisan':'#5e9988','Republican':'#ba5355',
        'Libertarian':'#c29739','Other / blank / overvote':'#bdc9d3'}

def main():
    counts=defaultdict(int);cohorts={}
    with SOURCE.open(encoding='utf-8',newline='') as f:
        for row in csv.DictReader(f):
            race=row['other_contest'];candidate=int(row['senate_candidate_id'])
            group=row['other_first_choice']
            if group not in COLORS:group='Other / blank / overvote'
            counts[race,candidate,group]+=int(row['ballots'])
            n=int(row['senate_cohort_n'])
            assert cohorts.get(candidate,n)==n
            cohorts[candidate]=n
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,
        'text.color':'#243449','axes.labelcolor':'#344d66',
        'xtick.color':'#40566f','ytick.color':'#40566f',
        'figure.facecolor':'white','axes.facecolor':'white',
        'svg.fonttype':'none','savefig.facecolor':'white'})
    fig=plt.figure(figsize=(8.5,8.0))
    # Low plotting areas keep the vertical columns physically short, preserving 0–100%.
    positions=[[.115,.635,.855,.265],[.115,.175,.855,.265]]
    specifications=[('governor','Governor first choice',
        ['Democrat/Nonpartisan','Republican','Other / blank / overvote']),
        ('us_house','House first choice',
        ['Democrat','Nonpartisan','Libertarian','Republican','Other / blank / overvote'])]
    plotted=[]
    for position,(race,title,groups) in zip(positions,specifications):
        ax=fig.add_axes(position);bottom=[0.]*4
        ax.set_axisbelow(True);ax.grid(axis='y',color='#e6ebef',lw=.7)
        for group in groups:
            values=[100*counts[race,c,group]/cohorts[c] for c in ORDER]
            ax.bar(range(4),values,bottom=bottom,width=.53,color=COLORS[group],
                   edgecolor='none',zorder=3)
            for i,(value,base) in enumerate(zip(values,bottom)):
                if value>=8:
                    ax.text(i,base+value/2,f'{value:.1f}%',ha='center',va='center',
                            color='white',fontsize=11,fontweight='bold',zorder=4)
                plotted.append({'contest':race,'senate_candidate_id':ORDER[i],
                    'group':group,'ballots':counts[race,ORDER[i],group],
                    'cohort_n':cohorts[ORDER[i]],'percent':value})
            bottom=[a+b for a,b in zip(bottom,values)]
        assert all(abs(total-100)<1e-10 for total in bottom)
        ax.set_ylim(0,100);ax.set_xlim(-.62,3.62)
        ax.set_yticks([0,25,50,75,100]);ax.yaxis.set_major_formatter(PercentFormatter(100,decimals=0))
        ax.set_xticks(range(4),LABELS);ax.tick_params(axis='x',length=0,pad=9)
        ax.tick_params(axis='y',length=0,pad=7)
        for side in ['top','right','left']:ax.spines[side].set_visible(False)
        ax.spines['bottom'].set_color('#b9c5ce')
        ax.set_title(title,loc='left',fontsize=14,fontweight='bold',pad=14)
        ax.legend(handles=[Patch(color=COLORS[g],label=g) for g in groups],
            loc='upper center',bbox_to_anchor=(.5,-.32),ncol=3,frameon=False,
            fontsize=9,handlelength=1.6,columnspacing=1.8,handletextpad=.6)
        # Align the cohort label with the two-line Mary Peltola tick label.
        fig.canvas.draw()
        bbox=ax.get_xticklabels()[0].get_window_extent(fig.canvas.get_renderer())
        label_position=fig.transFigure.inverted().transform((bbox.x0-12,(bbox.y0+bbox.y1)/2))
        fig.text(*label_position,'Senate 1st choice:',ha='right',va='center',
                 fontsize=9.5,color='#40566f')
    fig.text(.022,.525,'Share within each Senate first-choice cohort (%)',
             rotation=90,va='center',ha='center',fontsize=11,color='#344d66')
    output=OUT/'Alaska_Governor_House_First_Choice_Presentation.png'
    fig.savefig(output,dpi=220)
    fig.savefig(output.with_suffix('.svg'))
    plt.close(fig)
    (OUT/'build_vertical_provenance.json').write_text(json.dumps({
        'source':str(SOURCE.relative_to(ROOT)),
        'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'source_policy':'Audited Rachel-only affiliation cross-tabs; source data unchanged.',
        'candidate_order':ORDER,'candidate_labels':[x.replace('\n',' ') for x in LABELS],
        'house_stack_bottom_to_top':specifications[1][2],
        'cohort_labels_added_to_both_panels':'Senate 1st choice:',
        'bold_titles':['Governor first choice','House first choice'],
        'format':'Two vertical100percent stacked-bar panels; short physical bar height; full0to100scale',
        'values':plotted},indent=2))
    print(output)

if __name__=='__main__':main()
