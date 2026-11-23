"""Half-width presentation rendering from saved November11 density grids only.

No refitting, KDE recalculation, ballot filtering, or notebook mutation.
"""
from pathlib import Path
import importlib.util,json,hashlib
import numpy as np
import matplotlib.pyplot as plt

BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('saved_figures',BASE.parent/'assets/build_presentation_figures.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
receipt={'snapshot':'Rachel/FairVote November 11, 2026','source_width_inches':9.6,'new_width_inches':4.8,
         'figure_height_inches':4.8,'density_recomputed':False,'axis_refitted':False,'assets':[]}
for race in m.RACES:
    item=m.DENSITY[race];x=np.array(item['x']);y=np.array(item['y'])
    assert len(x)==8192 and np.all(y>=0)
    fig,ax=plt.subplots(figsize=(4.8,4.8))
    m.density_panel(ax,race)
    ax.set_title(f"{m.TITLE[race]} axis\n{item['plotted']:,} plotted / {item['source']:,} source ballots",
                 loc='left',fontweight='bold',fontsize=11.2,pad=12,linespacing=1.5)
    ax.set_ylabel('Estimated voter density',fontsize=11)
    ax.set_xlabel('Normalized candidate-axis coordinate',labelpad=42,fontsize=10.4)
    fig.subplots_adjust(left=.145,right=.915,top=.81,bottom=.34)
    footer=fig.text(.145,.032,'Assigned positions, not observed locations.\nMahshad convention; spatially consistent ballots.\nRachel/FairVote November 11 snapshot.',
                    fontsize=8.6,color=m.TEXT,linespacing=1.45)
    fig.canvas.draw();renderer=fig.canvas.get_renderer();canvas=fig.bbox
    texts=[ax.title,ax.xaxis.label,ax.yaxis.label,footer,*ax.texts,*ax.get_xticklabels(),*ax.get_yticklabels()]
    bounds=[]
    for text in texts:
        if not text.get_text():continue
        box=text.get_window_extent(renderer)
        assert box.x0>=-.5 and box.x1<=canvas.x1+.5 and box.y0>=-.5 and box.y1<=canvas.y1+.5,(race,text.get_text(),box.bounds)
        bounds.append({'text':text.get_text(),'bounds_pixels':list(box.bounds)})
    assert footer.get_window_extent(renderer).y1+3<ax.xaxis.label.get_window_extent(renderer).y0,(race,'footer overlaps x label')
    stem=race.replace('us_','')+'_voter_density_half_width'
    fig.savefig(BASE/(stem+'.png'),dpi=360,facecolor='white')
    fig.savefig(BASE/(stem+'.svg'),facecolor='white')
    # Ensure the artist still contains each saved sample unchanged.
    assert np.array_equal(ax.lines[0].get_xdata(),x) and np.array_equal(ax.lines[0].get_ydata(),y)
    receipt['assets'].append({'race':race,'files':[stem+'.png',stem+'.svg'],
        'density_sample_sha256':hashlib.sha256(np.column_stack((x,y)).tobytes()).hexdigest(),
        'saved_samples':len(x),'text_bounds':bounds})
    plt.close(fig)
(BASE/'render_verification.json').write_text(json.dumps(receipt,indent=2))
print('Rendered three half-width figures; all saved curve samples unchanged; labels fit.')
