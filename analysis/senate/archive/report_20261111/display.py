"""Presentation helpers for the self-contained Sam notebook."""
from pathlib import Path
import json,html
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from IPython.display import display,HTML,Image
R=Path(__file__).resolve().parent
FIG=R/'figures';FIG.mkdir(exist_ok=True)
ORDER=[525,527,524,526]
SHORT={525:'Mary Peltola',527:'Dan S. Sullivan',524:'Gerald Heikes',526:'Daniel J. Sullivan Jr.'}
COLORS={525:'#2869a6',527:'#bb4f51',524:'#8061aa',526:'#d59b36'}
OTHER={'Bronson/Church':'Bronson / Church','Kreiss-Tomkins/Johnson':'Kreiss-Tomkins / Johnson','Taylor/English':'Taylor / English','Wilson/Shower':'Wilson / Shower','Begich, Nick':'Nick Begich','Hill, Bill':'Bill Hill','Hafner, Eric':'Eric Hafner','McDermott, James C. "Jim"':'Jim McDermott','blank_rank1':'Blank rank 1','overvote_rank1':'Overvote rank 1','not_on_ballot_type':'Not on ballot type','not_in_governor_file':'Absent from governor file','no_interpretable_first_choice':'No usable first choice','no_interpretable_named_first_choice':'No usable named choice','Write-in':'Write-in'}

def theme():
    plt.rcParams.update({'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':'#243449','text.color':'#243449','xtick.color':'#40566f','ytick.color':'#40566f','font.size':11,'figure.facecolor':'white','axes.facecolor':'white','savefig.facecolor':'white'})
    display(HTML('''<style>.sam-title{font-family:system-ui,sans-serif;color:#18324e;font-size:34px;line-height:1.15;margin:8px 0 16px}.sam-kicker{color:#437999;font-weight:700;text-transform:uppercase;letter-spacing:1.4px;font-size:12px}.sam-note{border-left:4px solid #5d90b4;background:#f1f6f9;padding:12px 16px;color:#334d65;margin:16px 0}.sam-table{border-collapse:collapse;font-family:system-ui,sans-serif;font-size:12px;line-height:1.5;width:100%;margin:14px 0 24px}.sam-table th{background:#1c3d5b;color:white;text-align:right;padding:10px 8px;white-space:normal}.sam-table td{padding:10px 8px;border-bottom:1px solid #dde6ec;text-align:right}.sam-table th:first-child,.sam-table td:first-child{text-align:left}.sam-table tr:nth-child(even) td{background:#f4f7fa}.sam-table caption{text-align:left;color:#243b53;font-weight:700;font-size:16px;padding:10px 0}.sam-card{background:#f2f6fa;border-radius:6px;padding:16px 20px;flex:1;min-width:150px}.sam-card .n{font-size:29px;font-weight:750;color:#193b5c}.sam-card .l{font-size:13px;color:#4a6176;margin-top:6px}.sam-cards{display:flex;gap:12px;flex-wrap:wrap;margin:16px 0 24px}pre{font-size:11px}h2{color:#183b56;border-bottom:1px solid #d8e4ed;padding-bottom:8px}h3{color:#315877}</style>'''))
    theme_rc=plt.rcParams

def table(df,title=None):
    markup=df.to_html(index=False,escape=True,classes='sam-table'+(' sam-wide-table' if len(df.columns)>=7 else ''),border=0)
    if title:markup=markup.replace('<thead>',f'<caption>{html.escape(title)}</caption><thead>',1)
    display(HTML('<div class="sam-scroll" style="overflow-x:auto">'+markup+'</div>'))

def cards():
    s=json.loads((R/'descriptive/descriptive_results.json').read_text());m=json.loads((R/'mds/mds_results.json').read_text());summ=m['summary'][1]
    q=s['question1_usable_prefix_categories']
    strict=q.get('peltola_above_senator_both_ranked',0)
    p_only=q.get('peltola_only_explicitly_ranked',0)
    items=[(f"{strict:,}",'Peltola above Dan S. · both in usable prefix'),(f"{p_only:,}",'Only Peltola appears in the usable finalist rankings'),(f"{100*summ['observed_consistency']:.1f}%",'Observed consistency · 3–4 named ranks'),(f"{100*summ['random_mean']:.1f}%",'Random consistency · 49 freshly fitted FairVote profiles')]
    display(HTML('<div class="sam-cards">'+''.join(f'<div class="sam-card"><div class="n">{n}</div><div class="l">{l}</div></div>' for n,l in items)+'</div>'))

def preference_table():
    s=json.loads((R/'descriptive/descriptive_results.json').read_text());n=s['question1_literal_rank1_daniel_j_n'];q=s['question1_usable_prefix_categories']
    labels=[('peltola_above_senator_both_ranked','Peltola above Dan S. — both usable'),('peltola_only_explicitly_ranked','Only Peltola in usable finalist rankings'),('senator_above_peltola_both_ranked','Dan S. above Peltola — both usable'),('senator_only_explicitly_ranked','Only Dan S. in usable finalist rankings'),('neither_explicitly_ranked','Neither finalist in usable rankings')]
    out=pd.DataFrame([{'Alaska-countable preferences':label,'Ballots':f'{q.get(k,0):,}',f'Share of {n:,}':f'{100*q.get(k,0)/n:.2f}%'} for k,label in labels]);table(out,'Daniel J. Sullivan Jr. first-choice ballots: usable rankings under Alaska rules')

def cross_table(contest,party=False,sensitivity=False):
    filename=('interpreted_first_choice_party_sensitivity.csv' if party else 'interpreted_first_choice_candidate_sensitivity.csv') if sensitivity else ('first_choice_party_crosstabs.csv' if party else 'first_choice_candidate_crosstabs.csv')
    df=pd.read_csv(R/'descriptive'/filename);df=df[df.other_contest==contest];cols=sorted(df.other_first_choice.unique(),key=lambda x:(x in ['blank_rank1','overvote_rank1','not_on_ballot_type','no_interpretable_named_first_choice','not_in_governor_file','no_interpretable_first_choice'],x))
    out=[]
    for senate in ORDER:
        sub=df[df.senate_candidate_id==senate].set_index('other_first_choice');n=int(sub.senate_cohort_n.iloc[0]);row={'Senate first choice':SHORT[senate],'Cohort N':f'{n:,}'}
        for col in cols:
            v=int(sub.loc[col,'ballots']) if col in sub.index else 0;row[OTHER.get(col,col)]=f'{v:,} ({100*v/n:.1f}%)'
        out.append(row)
    table(pd.DataFrame(out),('Governor' if contest=='governor' else 'U.S. House')+(' — candidate affiliation' if party else ' — candidate first choice')+(' (interpreted sensitivity)' if sensitivity else ' (literal rank 1)'))

def party_plot():
    data=pd.read_csv(R/'descriptive/first_choice_party_crosstabs.csv')
    colors={'Democrat/Nonpartisan':'#397aad','Democrat':'#397aad','Republican':'#ba5355','Nonpartisan':'#5e9988','Libertarian':'#c29739','Other / blank / overvote':'#bdc9d3'}
    fig,axs=plt.subplots(2,1,figsize=(11.6,7.3),sharex=True)
    for ax,contest in zip(axs,['governor','us_house']):
        sub=data[data.other_contest==contest].copy();sub['group']=sub.other_first_choice.where(sub.other_first_choice.isin(colors),'Other / blank / overvote')
        groups=(['Democrat/Nonpartisan','Republican'] if contest=='governor' else ['Democrat','Nonpartisan','Republican','Libertarian'])+['Other / blank / overvote']
        vals=sub.groupby(['senate_candidate_id','group']).ballots.sum();left=np.zeros(4)
        for group in groups:
            width=np.array([100*vals.get((s,group),0)/sub[sub.senate_candidate_id==s].senate_cohort_n.iloc[0] for s in ORDER])
            ax.barh(range(4),width,left=left,color=colors[group],label=group,height=.62)
            for i,(x,w) in enumerate(zip(left,width)):
                if w>=8:ax.text(x+w/2,i,f'{w:.1f}%',ha='center',va='center',color='white',fontsize=10,fontweight='bold')
            left+=width
        ax.set_yticks(range(4),[SHORT[x] for x in ORDER]);ax.invert_yaxis();ax.set_xlim(0,100);ax.set_title('Governor ticket affiliation' if contest=='governor' else 'House candidate affiliation',loc='left',fontsize=13,fontweight='bold',pad=12)
        ax.legend(loc='lower left',bbox_to_anchor=(0,-.58 if contest=='us_house' else -.36),ncol=3 if contest=='us_house' else 3,frameon=False,fontsize=9)
        ax.spines['left'].set_visible(False);ax.tick_params(axis='y',length=0)
    axs[-1].set_xlabel('Share within each Senate first-choice cohort (%)');fig.subplots_adjust(left=.23,right=.98,top=.95,bottom=.23,hspace=.7)
    fig.savefig(FIG/'cross_race_party.png',dpi=170,bbox_inches='tight');plt.close(fig)
    display(Image(filename=str(FIG/'cross_race_party.png'),width=1050))

def mds_plots():
    m=json.loads((R/'mds/mds_results.json').read_text());axis=np.array(m['axis']);ids=m['candidate_ids'];s=m['summary'][1]
    fig,ax=plt.subplots(figsize=(11.5,2.8));ax.axhline(0,color='#c5d1dc',lw=3,zorder=0)
    for i,(x,cid) in enumerate(zip(axis,ids)):
        ax.scatter([x],[0],s=230,color=COLORS[cid],edgecolor='white',linewidth=1.8,zorder=2)
        y=.27 if cid in [525,524] else -.27
        ax.text(x,y,SHORT[cid]+'\n'+f'{x:.3f}',ha='center',va='center',fontsize=11,fontweight='bold')
    ax.set(xlim=(-.13,1.13),ylim=(-.65,.65));ax.axis('off');ax.set_title('One candidate axis from the observed Senate rankings',loc='left',fontsize=15,fontweight='bold',pad=12)
    fig.text(.13,.04,'Normalized positions · axis direction is arbitrary · distance is not a calibrated ideology scale',fontsize=10,color='#536b7e')
    fig.savefig(FIG/'senate_candidate_axis.png',dpi=170,bbox_inches='tight');plt.close(fig);display(Image(filename=str(FIG/'senate_candidate_axis.png'),width=1000))
    vals=np.array([x['gamma_informative'] for x in m['null']])*100;real=100*m['observed']['gamma_informative']
    fig,ax=plt.subplots(figsize=(10.8,4));ax.hist(vals,bins=10,color='#b5c8d8',edgecolor='white');ax.axvline(real,color='#bd6a31',lw=2.8,label=f'Observed: {real:.2f}%');ax.axvline(vals.mean(),color='#356f96',lw=2,ls='--',label=f'Random mean: {vals.mean():.2f}%');ax.set(xlabel='Consistency among ballots with 3–4 named preferences (%)',ylabel='Randomized profiles',title='Observed consistency exceeds the matched randomized benchmark');ax.legend(frameon=False,loc='upper left',bbox_to_anchor=(.52,.98));ax.set_xlim(min(vals.min()-3,35),max(real+4,65));fig.tight_layout();fig.savefig(FIG/'real_vs_random.png',dpi=170,bbox_inches='tight');plt.close(fig);display(Image(filename=str(FIG/'real_vs_random.png'),width=1000))

def consistency_table():
    df=pd.read_csv(R/'mds/consistency_summary.csv');out=[]
    for _,r in df.iterrows():
        out.append({'Ballot group':' '.join(r['group'].replace('Exactly','Exactly ').split()),'N':f"{int(r.ballots):,}",'Observed':f'{100*r.observed_consistency:.2f}%','Random mean':f'{100*r.random_mean:.2f}%','Excess (pp)':f'{r.excess_percentage_points:+.2f}','Random SD (pp)':f'{100*r.random_sd:.2f}'})
    table(pd.DataFrame(out),'Single-axis consistency: full-profile fit and score')
