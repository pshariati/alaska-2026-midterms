"""Presentation Sankey: Rachel November11 House records, with mass checks.

No MDS, ballot source, notebook or Google Slides content is overwritten.
"""
from pathlib import Path
from collections import Counter
import csv,sys,json,html,hashlib

BASE=Path(__file__).resolve().parent
PROJECT=BASE.parents[1]
ROOT=PROJECT/'alaska_2026_sam_followup_20261116'
sys.path.insert(0,str(ROOT/'common'))
from data import read_rows,countable_tokens,RACES,source_path,sha256

L='Hill, Bill';B='Begich, Nick';E='Hafner, Eric';M='McDermott, James C. "Jim"';I='Inactive'
ORDER=[L,B,E,M,I]
LABEL={L:'Bill Hill',B:'Nick Begich',E:'Eric Hafner',M:'Jim McDermott',I:'Inactive'}
COLOR={L:'#D9A431',B:'#BD5054',E:'#347CB1',M:'#8560AA',I:'#A7B6C3'}
profile=Counter()
for _,row,tokens in read_rows('us_house'):
    pref,reason,barrier=countable_tokens(tokens)
    profile[pref]+=1
total=sum(profile.values());assert total==244705

def choice(pref,continuing):return next((v for v in pref if v in continuing),I)

cont=set(RACES['us_house']['names']);stages=[];losers=[]
while True:
    counts=Counter({c:0 for c in cont})
    for pref,n in profile.items():counts[choice(pref,cont)]+=n
    assert sum(counts.values())==total
    stages.append({'continuing':set(cont),'counts':counts})
    if len(cont)==2:break
    active=total-counts[I]
    if len(stages)==1:
        assert max(counts[c] for c in cont)*2<=active,'First-round majority: do not invent extra stages'
    minimum=min(counts[c] for c in cont);tied=[c for c in cont if counts[c]==minimum]
    assert len(tied)==1,'Tie needs an official resolution'
    loser=tied[0];losers.append(loser);cont.remove(loser)
assert losers==[M,E] and len(stages)==3
links=Counter();paths=Counter()
for pref,n in profile.items():
    p=tuple(choice(pref,s['continuing']) for s in stages);paths[p]+=n
    for k,(a,b) in enumerate(zip(p,p[1:])):links[k,a,b]+=n
for k,stage in enumerate(stages):
    for c,n in stage['counts'].items():
        if k<2:assert sum(v for (t,a,b),v in links.items() if t==k and a==c)==n
        if k>0:assert sum(v for (t,a,b),v in links.items() if t==k-1 and b==c)==n
for (k,a,b),n in links.items():
    assert a!=I or b==I,'Inactive ballots cannot reactivate'
    assert a not in stages[k+1]['continuing'] or a==b,'Continuing candidates retain their votes'
ref=json.loads((ROOT/'references/benchmark_validation.json').read_text())['contests']['us_house']['round_counts'][1:]
for actual,expected in zip(stages,ref):
    assert {('Inactive Ballots' if c==I else c):n for c,n in actual['counts'].items()}==expected
assert stages[-1]['counts']=={L:108917,B:122405,I:13383}

def write_csv(name,rows):
    with (BASE/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
write_csv('house_flow_nodes.csv',[{'stage':k+1,'candidate':LABEL[c],'ballots':n} for k,s in enumerate(stages) for c,n in s['counts'].items()])
write_csv('house_flow_links.csv',[{'source_stage':k+1,'source':LABEL[a],'target_stage':k+2,'target':LABEL[b],'ballots':n} for (k,a,b),n in links.items()])
write_csv('house_flow_paths.csv',[{'initial':LABEL[p[0]],'after_McDermott':LABEL[p[1]],'after_Hafner':LABEL[p[2]],'ballots':n} for p,n in paths.items()])

W,H=1920,1080
scale=522/total;gap=32;top=230;region=650;barwidth=22;xs=[290,910,1530]
nodes={}
for k,s in enumerate(stages):
    present=[c for c in ORDER if s['counts'].get(c,0)]
    height=total*scale+gap*(len(present)-1)
    y=top+(region-height)/2
    for c in present:
        n=s['counts'][c];nodes[k,c]={'x':xs[k],'y':y,'h':n*scale,'count':n}
        y+=n*scale+gap

parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="House ranked-choice transfer Sankey, Rachel November 11 snapshot">',
 '<rect width="1920" height="1080" fill="white"/>',
 '<style>text{font-family:Arial,sans-serif;fill:#24384F}.title{font-size:38px;font-weight:700}.sub{font-size:23px;fill:#526A80}.stage{font-size:25px;font-weight:700}.stage2{font-size:20px;fill:#526A80}.name{font-size:24px;font-weight:700;paint-order:stroke;stroke:white;stroke-width:6px;stroke-linejoin:round}.count{font-size:22px;paint-order:stroke;stroke:white;stroke-width:6px}.small{font-size:21px;font-weight:700;paint-order:stroke;stroke:white;stroke-width:6px}.foot{font-size:20px;fill:#526A80}</style>',
 '<text class="title" x="54" y="62">House: hypothetical ranked-choice transfers</text>',
 '<text class="sub" x="54" y="103">Rachel/FairVote November 11 snapshot · all 244,705 House ballot records</text>']
for k,(a,b) in enumerate([('Initial allocation*','Unresolved write-ins excluded'),('After McDermott','is eliminated'),('After Hafner','is eliminated')]):
    parts.append(f'<text class="stage" text-anchor="middle" x="{xs[k]+11}" y="164">{a}</text>')
    parts.append(f'<text class="stage2" text-anchor="middle" x="{xs[k]+11}" y="195">{b}</text>')
source_offsets=Counter();target_offsets=Counter()
for k in range(2):
    for a in ORDER:
        for b in ORDER:
            n=links.get((k,a,b),0)
            if not n:continue
            left=nodes[k,a];right=nodes[k+1,b]
            x1=left['x']+barwidth;x2=right['x'];mid=(x1+x2)/2
            y1=left['y']+source_offsets[k,a];y2=right['y']+target_offsets[k+1,b];h=n*scale
            source_offsets[k,a]+=h;target_offsets[k+1,b]+=h
            d=f'M {x1},{y1} C {mid},{y1} {mid},{y2} {x2},{y2} L {x2},{y2+h} C {mid},{y2+h} {mid},{y1+h} {x1},{y1+h} Z'
            parts.append(f'<path d="{d}" fill="{COLOR[a]}" fill-opacity="0.32"><title>{html.escape(LABEL[a])} → {html.escape(LABEL[b])}: {n:,} ballots</title></path>')
for (k,c),n in nodes.items():
    x,y,h=n['x'],n['y'],n['h'];cy=y+h/2
    assert 0<=y and y+h<H
    parts.append(f'<rect x="{x}" y="{y}" width="{barwidth}" height="{h}" fill="{COLOR[c]}"/>')
    tx=x-18 if k==0 else x+40;anchor='end' if k==0 else 'start'
    if h<50:
        parts.append(f'<text class="small" text-anchor="{anchor}" x="{tx}" y="{cy+7}">{html.escape(LABEL[c])} · {n["count"]:,}</text>')
    else:
        parts.append(f'<text class="name" text-anchor="{anchor}" x="{tx}" y="{cy-5}">{html.escape(LABEL[c])}</text>')
        parts.append(f'<text class="count" text-anchor="{anchor}" x="{tx}" y="{cy+24}">{n["count"]:,}</text>')
parts.extend([
 '<line x1="54" y1="930" x2="1866" y2="930" stroke="#D4DFE7"/>',
 '<text class="foot" x="54" y="968">Ribbon width is proportional to ballots. Inactive = no remaining valid ranking for a continuing candidate.</text>',
 '<text class="foot" x="54" y="1001">*Initial allocation follows write-in exclusion. Candidate totals include incoming transfers at each stage.</text>',
 '<text class="foot" x="54" y="1040">Preliminary snapshot replay, not certified statewide results. Final replay: Begich 122,405 · Hill 108,917.</text>',
 '</svg>'])
(BASE/'House_Sankey_Nov11.svg').write_text('\n'.join(parts))
receipt={'snapshot':'Rachel/FairVote November11,2026','source':str(source_path('us_house')),
         'source_sha256':sha256(source_path('us_house')),'total_ballots':total,
         'stages':[{LABEL[c]:n for c,n in s['counts'].items()} for s in stages],
         'elimination_order':[LABEL[c] for c in losers],
         'all_node_inflows_outflows_match':True,'all_stage_totals_conserved':True,
         'all_3_stages_match_saved_validated_results':True,
         'flows':[{ 'source_stage':k+1,'source':LABEL[a],'target':LABEL[b],'ballots':n} for (k,a,b),n in links.items()],
         'scope':'All House records, not just Hafner-first ballots. Unresolved write-ins excluded before first shown stage. No original notebook or source changes.'}
(BASE/'House_Sankey_Verification.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps({'ballots':total,'stages':receipt['stages'],'eliminations':receipt['elimination_order'],'links':len(links)},indent=2))
