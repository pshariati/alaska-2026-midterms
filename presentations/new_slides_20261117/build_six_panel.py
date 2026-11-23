"""Slide-only rendering from the six saved Rachel November11 KDE grids."""
from pathlib import Path
import importlib.util,json,hashlib
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('saved_figures',BASE.parent/'assets/build_presentation_figures.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
fig=plt.figure(figsize=(16,9),facecolor='white')
fig.text(.045,.942,'Peltola-first and Dan J.-first voters across three races',fontsize=26,fontweight='bold',color=m.NAVY)
fig.text(.045,.895,'The same Senate first-choice groups, located separately on each election’s candidate axis',fontsize=14,color=m.TEXT)
colors=['#2C73B5','#D9A12C'];groups=['525','526'];cohorts=[117437,3940]
panel_data=[]
for row,group in enumerate(groups):
    rowtop=.817 if row==0 else .452
    label='Peltola first for Senate' if row==0 else 'Dan J. first for Senate (outsider)'
    fig.text(.07,rowtop,f'{label}  ·  {cohorts[row]:,} ballots',fontsize=15,fontweight='bold',color=colors[row])
    bottom=.581 if row==0 else .216
    for col,race in enumerate(m.RACES):
        left=.075+col*.312
        ax=fig.add_axes([left,bottom,.266,.195])
        item=m.FOCAL[race,group];x=np.array(item['x']);y=np.array(item['y'])
        assert len(x)==8192 and np.all(y>=0)
        ax.plot(x,y,color=colors[row],lw=2)
        ax.fill_between(x,0,y,color=colors[row],alpha=.13)
        ax.set(xlim=(0,1),ylim=(0,None))
        ax.yaxis.set_major_locator(MaxNLocator(nbins=4))
        ax.set_xticks(np.linspace(0,1,6));ax.tick_params(labelsize=10.2,length=3)
        ax.set_title(m.TITLE[race]+' axis',loc='left',fontsize=13,fontweight='bold',pad=8)
        ax.grid(axis='y',color=m.GRID,lw=.7);ax.set_axisbelow(True)
        ax.spines['left'].set_color('#758698');ax.spines['bottom'].set_color('#758698')
        if col==0:ax.set_ylabel('Estimated density',fontsize=11)
        for j,(c,pos) in enumerate(m.AXES[race]):
            ax.axvline(pos,color=m.LINE,lw=.65,ls=(0,(2,3)),zorder=0)
            ax.annotate(m.SHORT[c],xy=(pos,0),xycoords=('data','axes fraction'),
                xytext=(0,-24 if j%2==0 else -38),textcoords='offset points',
                ha='center',va='top',fontsize=10.1,color=m.TEXT)
        assert item['cohort']==cohorts[row]
        ax.text(.985,.94,f"{item['plotted']:,} / {cohorts[row]:,} plotted",transform=ax.transAxes,
                ha='right',va='top',fontsize=9.5,color=m.TEXT)
        assert np.array_equal(ax.lines[0].get_xdata(),x) and np.array_equal(ax.lines[0].get_ydata(),y)
        panel_data.append({'race':race,'senate_first_choice':group,'plotted':item['plotted'],'cohort':cohorts[row],
                           'saved_grid_points':len(x),'xy_sha256':hashlib.sha256(np.column_stack((x,y)).tobytes()).hexdigest()})
fig.text(.045,.075,'Each curve integrates to 1 among plotted ballots. Assigned positions follow Mahshad’s convention; single-name ballots are placed at their candidate.',fontsize=11.1,color=m.TEXT)
fig.text(.045,.037,'Each race has its own normalized axis, not a shared ideology scale.  |  Rachel/FairVote November 11, 2026 snapshot',fontsize=11.1,color=m.TEXT)
fig.canvas.draw();renderer=fig.canvas.get_renderer()
for text in fig.findobj(match=lambda a:hasattr(a,'get_text') and hasattr(a,'get_window_extent')):
    if not text.get_visible() or not text.get_text():continue
    box=text.get_window_extent(renderer)
    # Some unused ticks outside the selected range remain as invisible artists.
    if hasattr(text,'axes') and text.axes is not None and (box.x1<text.axes.bbox.x0-150 or box.x0>text.axes.bbox.x1+150):continue
    assert box.x0>=-2 and box.x1<=fig.bbox.x1+2 and box.y0>=-2 and box.y1<=fig.bbox.y1+2,(text.get_text(),box.bounds)
fig.savefig(BASE/'Six_Voter_Distributions.png',dpi=240,facecolor='white')
fig.savefig(BASE/'Six_Voter_Distributions.svg',facecolor='white')
(BASE/'six_panel_verification.json').write_text(json.dumps({'panels':panel_data,'panels_rendered':len(panel_data),
    'density_recomputed':False,'MDS_refitted':False,'source_snapshot':'Rachel November11',
    'output_pixels':[3840,2160],'all_saved_curve_samples_unchanged':True},indent=2))
print(json.dumps({'panels':panel_data,'rendered_pixels':[3840,2160]},indent=2))
