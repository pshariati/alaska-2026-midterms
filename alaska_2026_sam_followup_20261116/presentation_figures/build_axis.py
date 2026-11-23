"""Place Governor/House affiliation pairs at the audited candidate-axis positions."""
from pathlib import Path
from collections import defaultdict
import csv,json,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch,ConnectionPatch
from matplotlib.ticker import PercentFormatter

OUT=Path(__file__).resolve().parent
ROOT=OUT.parent
PACKAGE=ROOT
PARTY=PACKAGE/'completed/descriptive/first_choice_party_crosstabs.csv'
AXIS=PACKAGE/'axis_models/us_senate/candidate_axis.csv'
NAMES={525:'Mary Peltola',526:'Daniel J. Sullivan Jr.',524:'Gerald Heikes',527:'Dan S. Sullivan'}
DOTS={525:'#2869a6',526:'#d59b36',524:'#8061aa',527:'#bb4f51'}
COLORS={'Democrat/Nonpartisan':'#397aad','Democrat':'#397aad',
    'Nonpartisan':'#5e9988','Republican':'#ba5355','Libertarian':'#c29739',
    'Other / blank / overvote':'#bdc9d3'}
SPECS=[('governor','Governor',-.030,['Democrat/Nonpartisan','Republican','Other / blank / overvote']),
    ('us_house','House',.030,['Democrat','Nonpartisan','Libertarian','Republican','Other / blank / overvote'])]

def main():
    counts=defaultdict(int);cohorts={}
    with PARTY.open(encoding='utf-8',newline='') as f:
        for row in csv.DictReader(f):
            c=int(row['senate_candidate_id']);g=row['other_first_choice'];race=row['other_contest']
            if g not in COLORS:g='Other / blank / overvote'
            counts[race,c,g]+=int(row['ballots'])
            n=int(row['senate_cohort_n']);assert cohorts.get(c,n)==n;cohorts[c]=n
    with AXIS.open(encoding='utf-8',newline='') as f:
        positions={int(row['candidate_id']):float(row['axis_position']) for row in csv.DictReader(f)}
    order=sorted(positions,key=positions.get)
    assert order==[525,526,524,527]
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,
        'text.color':'#243449','axes.labelcolor':'#344d66','xtick.color':'#40566f',
        'ytick.color':'#40566f','figure.facecolor':'white','axes.facecolor':'white',
        'svg.fonttype':'none','savefig.facecolor':'white'})
    fig=plt.figure(figsize=(15.3,7.2))
    bar=fig.add_axes([.075,.29,.89,.385])
    axis=fig.add_axes([.075,.735,.89,.13],sharex=bar)
    for ax in (axis,bar):ax.set_xlim(-.13,1.13)
    axis.set_ylim(0,1);axis.axis('off')
    axis.plot([-.13,1.13],[.14,.14],color='#c5d1dc',lw=3,zorder=1)
    width=.043;plotted=[];candidate_texts={}
    for cid in order:
        x=positions[cid]
        axis.scatter([x],[.14],s=190,color=DOTS[cid],edgecolor='white',linewidth=1.7,zorder=4)
        candidate_texts[cid]=axis.text(x,.63,NAMES[cid]+'\n'+f'{x:.3f}',ha='center',va='center',
                  fontsize=12,fontweight='bold',linespacing=1.2)
        fig.add_artist(ConnectionPatch((x,.14),(x,100),coordsA=axis.transData,
            coordsB=bar.transData,color='#cbd5de',lw=1.1,ls=(0,(3,3)),zorder=0))
        pair=[]
        for race,label,offset,groups in SPECS:
            center=x+offset;pair.append(center);bottom=0.
            for group in groups:
                value=100*counts[race,cid,group]/cohorts[cid]
                bar.bar(center,value,width=width,bottom=bottom,color=COLORS[group],
                        edgecolor='none',zorder=3)
                if value>=8:
                    bar.text(center,bottom+value/2,f'{value:.1f}%',ha='center',va='center',
                             fontsize=9,fontweight='bold',color='white',zorder=4)
                plotted.append({'candidate_id':cid,'candidate_axis_position':x,
                    'contest':race,'bar_center':center,'affiliation':group,
                    'ballots':counts[race,cid,group],'cohort_n':cohorts[cid],'percent':value})
                bottom+=value
            assert abs(bottom-100)<1e-10
            bar.text(center,-6,label,ha='center',va='top',fontsize=9,color='#40566f',clip_on=False)
        assert abs(sum(pair)/2-x)<1e-14
    bar.set_ylim(0,100);bar.set_yticks([0,25,50,75,100])
    bar.yaxis.set_major_formatter(PercentFormatter(100,decimals=0))
    bar.set_ylabel('Share within Senate first-choice cohort (%)',labelpad=12,fontsize=11)
    bar.set_axisbelow(True);bar.grid(axis='y',color='#e6ebef',lw=.8)
    bar.tick_params(axis='y',length=0,pad=7);bar.tick_params(axis='x',bottom=False,labelbottom=False)
    for side in ['top','right','left']:bar.spines[side].set_visible(False)
    bar.spines['bottom'].set_color('#b9c5ce')
    fig.text(.075,.94,'One candidate axis from the observed Senate rankings',
             ha='left',va='center',fontsize=18,fontweight='bold')
    # Separate legends preserve the original ticket versus candidate distinction.
    for (_,label,_,groups),y in zip(SPECS,[.195,.135]):
        fig.text(.075,y,label+' first choice',fontsize=10.5,fontweight='bold',va='center')
        fig.legend(handles=[Patch(color=COLORS[g],label=g) for g in groups],
            loc='center left',bbox_to_anchor=(.215,y),bbox_transform=fig.transFigure,
            frameon=False,ncol=len(groups),fontsize=10,handlelength=1.5,
            columnspacing=1.8,handletextpad=.6,borderaxespad=0)
    fig.text(.075,.055,'Normalized candidate positions · axis direction is arbitrary · distance is not a calibrated ideology scale',
             ha='left',va='center',fontsize=10,color='#61798e')
    fig.canvas.draw()
    bbox=candidate_texts[525].get_window_extent(fig.canvas.get_renderer())
    label_position=fig.transFigure.inverted().transform((bbox.x0-14,(bbox.y0+bbox.y1)/2))
    fig.text(*label_position,'Senate 1st choice:',ha='right',va='center',
             fontsize=10.5,color='#40566f')
    output=OUT/'Alaska_Candidate_Axis_First_Choice_Presentation.png'
    fig.savefig(output,dpi=220)
    fig.savefig(output.with_suffix('.svg'))
    plt.close(fig)
    (OUT/'build_axis_provenance.json').write_text(json.dumps({
        'source_policy':'Existing audited Rachel-only results; no recalculation or change of analysis.',
        'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [PARTY,AXIS]},
        'candidate_order':order,'axis_positions':positions,'bar_width':width,
        'house_stack_bottom_to_top':SPECS[1][3],
        'cohort_label_added':'Senate 1st choice:',
        'bold_titles':['Governor first choice','House first choice'],
        'pair_center_equals_candidate_axis_position':True,'all_eight_bars_sum_to100percent':True,
        'values':plotted},indent=2))
    print(output)

if __name__=='__main__':main()
