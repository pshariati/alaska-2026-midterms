"""Presentation-only flow assets from verified saved CSVs; no ballot refit or source edits."""
from pathlib import Path
import csv, json, hashlib, html

from analysis.shared.paths import race_dir
BASE=race_dir('us_senate')
OUT=BASE/'figures'/'flows'
OUT.mkdir(exist_ok=True)
def rows(p):
    with p.open(newline='') as f: return list(csv.DictReader(f))
nodes=rows(BASE/'flows/senate_flow_nodes.csv')
links=rows(BASE/'flows/senate_flow_links.csv')
for stage in range(1,5):
    assert sum(int(r['ballots']) for r in nodes if int(r['stage'])==stage)==244705
for n in nodes:
    if int(n['stage'])<4:
        assert sum(int(r['ballots']) for r in links if r['source']==n['node_id'])==int(n['ballots'])
    if int(n['stage'])>1:
        assert sum(int(r['ballots']) for r in links if r['target']==n['node_id'])==int(n['ballots'])
assert next(int(r['ballots']) for r in nodes if r['node_id']=='1:daniel_sullivan')==4055

# Preserve every saved path coordinate and ribbon width in the full-election Sankey.
s=(BASE/'flows/senate_sankey.svg').read_text()
s=s.replace('Daniel J. Sullivan Jr.','Dan J.').replace('Dan S. Sullivan','Daniel S.')
s=s.replace('Daniel J. removed','Dan J. removed')
s=s.replace('Alaska Senate: how recorded preferences transfer','Senate: hypothetical transfers in the November 11 snapshot')
s=s.replace('Rachel/FairVote November 11 CSV · all 244,705 ballot rows · four-stage replay · prepared November 13',
            'Rachel/FairVote November 11 CSV · all 244,705 ballot records · Alaska-rule replay')
s=s.replace('Ribbon width is proportional to ballots. Hover over a ribbon to see its exact count.',
            'Ribbon width is proportional to ballots. Dan J.’s 4,055-ballot node includes incoming transfers.')
s=s.replace('This is a preliminary replay, not certified election results.',
            'Hypothetical snapshot replay; this is not a certified statewide result.')
s=s.replace('Initially inactive: 1,363. Final inactive: 5,549, including 4,186 newly inactive during transfers.',
            'Initially inactive: 1,363. Inactive after these eliminations: 5,549 (4,186 additional).')
(OUT/'senate_full_sankey.svg').write_text(s)

# Literal rank-1 cohort, deliberately separate from the full Sankey’s 4,055 node.
p=rows(BASE/'rankings/daniel_first_usable_permutations.csv')
assert sum(int(r['literal_rank1_daniel_ballots']) for r in p)==3940
immediate={}
final={}
via={}
for r in p:
    n=int(r['literal_rank1_daniel_ballots'])
    immediate[r['after_Daniel_elimination']]=immediate.get(r['after_Daniel_elimination'],0)+n
    final[r['final_destination']]=final.get(r['final_destination'],0)+n
    if r['after_Daniel_elimination']=='Gerald Heikes':
        via[r['final_destination']]=via.get(r['final_destination'],0)+n
assert immediate=={'Inactive':1447,'Gerald Heikes':708,'Mary Peltola':1147,'Dan S. Sullivan':638}
assert final=={'Inactive':1703,'Mary Peltola':1333,'Dan S. Sullivan':904}
assert via=={'Inactive':256,'Mary Peltola':186,'Dan S. Sullivan':266}

W,H=1600,800
colors={'J':'#DEA332','P':'#2E78AD','S':'#BC4F52','H':'#8060A8','I':'#A7B5C3'}
height=450
scale=height/3940
gap=24
top=173
counts=[3940,1147,638,708,1447,1333,904,1703]
keys=['J','P','S','H','I','P','S','I']
ys=[top]
for cts in ([1147,638,708,1447],[1333,904,1703]):
    y=top
    for v in cts:
        ys.append(y);y+=v*scale+gap
xs=[120,655,655,655,655,1225,1225,1225]
names=['Dan J.','Peltola','Daniel S.','Heikes','Inactive','Peltola','Daniel S.','Inactive']
edge=[(0,1,1147),(0,2,638),(0,3,708),(0,4,1447),(1,5,1147),(2,6,638),(3,5,186),(3,6,266),(3,7,256),(4,7,1447)]
source_offsets=[0.]*8;target_offsets=[0.]*8
parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
       '<rect width="1600" height="800" fill="white"/>',
       '<style>text{font-family:Arial,sans-serif;fill:#24354A}.t{font-weight:700;font-size:32px}.sub{font-size:22px;fill:#587083}.stage{font-weight:700;font-size:23px}.label{font-weight:700;font-size:25px;paint-order:stroke;stroke:#FFF;stroke-width:7px;stroke-linejoin:round}.detail{font-size:21px;fill:#587083;paint-order:stroke;stroke:#FFF;stroke-width:5px}</style>',
       '<text class="t" x="40" y="48">Where do the 3,940 Dan J.–first ballots go?</text>',
       '<text class="sub" x="40" y="84">Hypothetical replay: Dan J. is eliminated, then Heikes. Peltola and Daniel S. remain.</text>',
       '<text class="stage" text-anchor="middle" x="130" y="140">First choice</text>',
       '<text class="stage" text-anchor="middle" x="665" y="140">After Dan J.</text>',
       '<text class="stage" text-anchor="middle" x="1235" y="140">After Heikes</text>']
for a,b,v in edge:
    x1=xs[a]+20;x2=xs[b]
    y1=ys[a]+source_offsets[a];y2=ys[b]+target_offsets[b];h=v*scale
    source_offsets[a]+=h;target_offsets[b]+=h
    mid=(x1+x2)/2
    col=colors[keys[b]] if a==0 else colors[keys[a]]
    d=f'M{x1},{y1} C{mid},{y1} {mid},{y2} {x2},{y2} L{x2},{y2+h} C{mid},{y2+h} {mid},{y1+h} {x1},{y1+h} Z'
    parts.append(f'<path d="{d}" fill="{col}" fill-opacity="0.27"><title>{names[a]} → {names[b]}: {v:,}</title></path>')
for i,(x,y,n,k,name) in enumerate(zip(xs,ys,counts,keys,names)):
    h=n*scale
    parts.append(f'<rect x="{x}" y="{y}" width="20" height="{h}" rx="2" fill="{colors[k]}"/>')
    if i==0:
        tx=x+32;anchor='start'
    elif i<5:
        tx=x-16;anchor='end'
    else:
        tx=x+36;anchor='start'
    cy=y+h/2
    parts.append(f'<text class="label" text-anchor="{anchor}" x="{tx}" y="{cy-4}">{name}</text>')
    parts.append(f'<text class="label" text-anchor="{anchor}" x="{tx}" y="{cy+25}">{n:,}</text>')
    if i>=5:
        details={5:'1,147 direct + 186 via Heikes',6:'638 direct + 266 via Heikes',7:'1,447 first + 256 after Heikes'}
        # Place below the node label, on the right margin, where the final ribbons end.
        parts.append(f'<text class="detail" text-anchor="{anchor}" x="{tx}" y="{cy+54}">{details[i]}</text>')
parts.extend(['<line x1="40" y1="724" x2="1550" y2="724" stroke="#D4DFE7"/>',
              '<text class="sub" x="40" y="760">Ribbon width ∝ ballots. Inactive = no further valid ranking for a remaining candidate.</text>',
              '</svg>'])
(OUT/'dan_j_first_flow.svg').write_text('\n'.join(parts))
meta={'inputs':{},'validation':'all four stage totals and every node balance verified',
      'literal_cohort':3940,'full_sankey_dan_j_node':4055,'literal_immediate':immediate,'literal_final':final,'literal_via_heikes':via,
      'notes':'Presentation-only alias changes. Full Sankey geometry preserved verbatim; no new analysis or source edits.'}
for rel in ['flows/senate_flow_nodes.csv','flows/senate_flow_links.csv','flows/senate_sankey.svg','rankings/daniel_first_usable_permutations.csv']:
    meta['inputs'][str(BASE/rel)]=hashlib.sha256((BASE/rel).read_bytes()).hexdigest()
(OUT/'flow_assets_provenance.json').write_text(json.dumps(meta,indent=2)+'\n')
print(json.dumps(meta,indent=2))
