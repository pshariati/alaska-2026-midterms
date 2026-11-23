"""Recompute Alaska Senate flows from Rachel's CSV only, with no prior-data fallback.

The four stages replay the predeclared write-in, Daniel J., Heikes removal order.
All source rows remain; generic overvote tokens stop transfers; two internal skips
stop later preferences; a write-in occupies its original rank before exclusion.
Frozen published FairVote HTML is an external benchmark, never an input to counts.
Run with Python standard library; Pillow is optional for high-resolution PNG.
"""
from pathlib import Path
from collections import Counter,defaultdict
import csv,json,html,math,re,hashlib
from analysis.shared.paths import INPUTS_ROOT, REFERENCES_ROOT, race_dir
R=race_dir('us_senate')/'flows'
SOURCE=INPUTS_ROOT/'Alaska_20261103_US_Senate_11_11.csv'
REFERENCE=REFERENCES_ROOT/'fairvote_us_senate.html'
TOKEN_TO_KEY={'Peltola, Mary':'peltola','Sullivan, Dan S.':'dan_sullivan','Heikes, Gerald L.':'heikes','Sullivan, Daniel J. Jr.':'daniel_sullivan','Write-in':'writein'}
NAMES={'peltola':'Mary Peltola','dan_sullivan':'Dan S. Sullivan','heikes':'Gerald L. Heikes','daniel_sullivan':'Daniel J. Sullivan Jr.','writein':'Generic write-in',None:'Inactive'}
SHORT={'peltola':'Peltola','dan_sullivan':'Dan S. Sullivan','heikes':'Heikes','daniel_sullivan':'Daniel J. Sullivan Jr.','writein':'Write-in',None:'Inactive'}
COLORS={'peltola':'#246AA8','dan_sullivan':'#BD4F4F','heikes':'#8063AA','daniel_sullivan':'#DA9C39','writein':'#778B94',None:'#BAC4CD'}
ORDER=['peltola','dan_sullivan','heikes','daniel_sullivan','writein',None]
CONT=[set(ORDER[:-1]),{'peltola','dan_sullivan','heikes','daniel_sullivan'},{'peltola','dan_sullivan','heikes'},{'peltola','dan_sullivan'}]
TITLES=['Initial allocation','Write-in removed','Daniel J. removed','Heikes removed']

def prefix(tokens):
    last=max((i for i,x in enumerate(tokens,1) if x!='skipped'),default=0)
    result=[];empty=0
    for token in tokens[:last]:
        if token=='skipped':
            empty+=1
            if empty==2:break
            continue
        empty=0
        if token=='overvote':break
        candidate=TOKEN_TO_KEY[token]
        if candidate not in result:result.append(candidate)
    return result

def writecsv(path,rows):
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def cubic(a,b,c,d,t):return (1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*c+t**3*d

def benchmark(counts):
    if not REFERENCE.exists():return {'available':False,'note':'No frozen benchmark provided; no source-count assertions substituted.'}
    body=REFERENCE.read_text().split('<tbody>',1)[1].split('</tbody>',1)[0]
    ref={}
    clean=lambda text:' '.join(html.unescape(re.sub('<[^>]+>',' ',text)).split())
    for tr in re.findall(r'<tr\b[^>]*>(.*?)</tr>',body,re.S):
        label=re.search(r'<th\b[^>]*>(.*?)</th>',tr,re.S)
        if not label:continue
        values=[]
        for td in re.findall(r'<td\b[^>]*>(.*?)</td>',tr,re.S):
            n=re.search(r'([\d,]+)\s+(?:votes|ballots)',clean(td));values.append(int(n[1].replace(',','')) if n else None)
        if values:ref[clean(label[1])]=values
    byname=dict(TOKEN_TO_KEY);byname['Inactive Ballots']=None
    checks=[]
    for name,values in ref.items():
        key=byname[name]
        for stage,expected in enumerate(values):
            if expected is None:continue
            value=counts[stage][key]-(counts[0][None] if key is None else 0)
            checks.append(dict(stage=stage+1,candidate=name,rachel_replay=value,published_benchmark=expected,difference=value-expected,match=value==expected))
    assert len(checks)==18, 'Unexpected published reference schema'
    writecsv(R/'fairvote_benchmark_comparison.csv',checks)
    return dict(available=True,role='External published benchmark only; no source counts borrowed',numeric_cells=len(checks),matches=sum(x['match'] for x in checks),mismatches=[x for x in checks if not x['match']],reference_sha256=hashlib.sha256(REFERENCE.read_bytes()).hexdigest())

def build():
    if not SOURCE.is_file():raise FileNotFoundError(f'Rachel-only input required: {SOURCE}')
    source_hash=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    counts=[Counter() for _ in CONT];links=[Counter() for _ in CONT[:-1]];paths=Counter();patterns=Counter();seen=set();token_counts=Counter()
    with SOURCE.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        assert all(f'rank{i}' in reader.fieldnames for i in range(1,6))
        for row in reader:
            uid=row['ballotID'];assert uid not in seen, f'Duplicate ballotID: {uid}';seen.add(uid)
            tokens=tuple(row[f'rank{i}'].strip() for i in range(1,6))
            unknown=set(tokens)-set(TOKEN_TO_KEY)-{'skipped','overvote'}
            if unknown:raise ValueError(f'Unknown Rachel rank tokens: {unknown}')
            token_counts.update(tokens);patterns[tokens]+=1
            p=prefix(tokens)
            path=tuple(next((candidate for candidate in p if candidate in active),None) for active in CONT)
            paths[path]+=1
            for stage,candidate in enumerate(path):counts[stage][candidate]+=1
            for stage,(a,b) in enumerate(zip(path,path[1:])):links[stage][a,b]+=1
    total=len(seen)
    for stage,count in enumerate(counts):assert sum(count.values())==total
    for stage,ls in enumerate(links):
        assert sum(ls.values())==total
        for candidate,n in counts[stage].items():assert sum(v for (a,b),v in ls.items() if a==candidate)==n
        for candidate,n in counts[stage+1].items():assert sum(v for (a,b),v in ls.items() if b==candidate)==n
    nodes=[]
    for stage,counter in enumerate(counts):
        for candidate in ORDER:
            if candidate in counter:nodes.append(dict(node_id=f'{stage}:{candidate}',stage=stage+1,stage_title=TITLES[stage],candidate_key=candidate,candidate=NAMES[candidate],ballots=counter[candidate],color=COLORS[candidate]))
    linkrows=[]
    for stage,counter in enumerate(links):
        for (a,b),n in sorted(counter.items(),key=lambda x:(ORDER.index(x[0][0]),ORDER.index(x[0][1]))):
            linkrows.append(dict(source=f'{stage}:{a}',target=f'{stage+1}:{b}',stage_from=stage+1,stage_to=stage+2,source_candidate_key=a,target_candidate_key=b,source_candidate=NAMES[a],target_candidate=NAMES[b],ballots=n,is_transfer=a!=b))
    pathrows=[dict(stage1=NAMES[p[0]],stage2=NAMES[p[1]],stage3=NAMES[p[2]],stage4=NAMES[p[3]],ballots=n) for p,n in paths.items()]
    result=dict(source_file=str(SOURCE.relative_to(R.parent)),source_sha256=source_hash,source_only='Every count derived from Rachel CSV rank1-rank5; no old raw ZIP, cleaned CVR, ranking patterns or old result counts are loaded.',total_ballots=total,initial_inactive=counts[0][None],final_inactive=counts[-1][None],additional_inactive=counts[-1][None]-counts[0][None],token_counts=dict(token_counts),mass_conservation_passed=True,round_counts=[{str(k):v for k,v in x.items()} for x in counts],nodes=nodes,links=linkrows,paths=pathrows,scope='Rachel/FairVote November 11 CSV, analyzed November 13. Predeclared four-stage replay, including initially inactive ballots. Not certified results.',benchmark=benchmark(counts))
    (R/'senate_sankey.json').write_text(json.dumps(result,indent=2))
    writecsv(R/'senate_flow_nodes.csv',nodes);writecsv(R/'senate_flow_links.csv',linkrows);writecsv(R/'senate_flow_paths.csv',pathrows)
    writecsv(R/'rachel_rank_patterns.csv',[dict(**{f'rank{i+1}':v for i,v in enumerate(tokens)},ballots=n) for tokens,n in patterns.items()])
    render(counts,links,total)
    print(json.dumps({k:v for k,v in result.items() if k not in ['nodes','links','paths','token_counts','round_counts']},indent=2))
    print('Rachel-only stage counts:',json.dumps(result['round_counts']))
    return result

def render(counts,links,total):
    initial_inactive=counts[0][None];final_inactive=counts[-1][None];additional_inactive=final_inactive-initial_inactive
    W,H=2000,1060;top=232;bottom=886;gap=30;bar=17;xvals=[260,800,1340,1880]
    # Use a single ballot-to-height scale at every stage. Gaps do not carry ballots.
    scale=(bottom-top-gap*(len(ORDER)-1))/total
    pos={}
    for stage,counter in enumerate(counts):
        y=top
        for candidate in ORDER:
            if candidate not in counter:continue
            pos[stage,candidate]=(y,counter[candidate]*scale);y+=counter[candidate]*scale+gap
    bands=[]
    for stage,counter in enumerate(links):
        outgoing=defaultdict(float);incoming=defaultdict(float)
        for (a,b),n in sorted(counter.items(),key=lambda x:(ORDER.index(x[0][0]),ORDER.index(x[0][1]))):
            y0=pos[stage,a][0]+outgoing[a];y1=pos[stage+1,b][0]+incoming[b];h=n*scale
            outgoing[a]+=h;incoming[b]+=h
            x0=xvals[stage]+bar;x1=xvals[stage+1];dx=(x1-x0)*.42
            bands.append((x0,x1,y0,y1,h,dx,a,b,n,stage))
    svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Alaska Senate ranked choice vote flow across four counting stages">',
         '<style>text{font-family:Arial,sans-serif;fill:#24354A}.title{font-size:32px;font-weight:700}.sub{font-size:19px;fill:#55677B}.stage{font-size:21px;font-weight:700}.label{font-size:16px;font-weight:600;paint-order:stroke;stroke:#fff;stroke-width:5px;stroke-linejoin:round}.count{font-size:16px;fill:#536579}.foot{font-size:17px;fill:#536579}path:hover{fill-opacity:.72}</style>',
         f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>',
         '<text class="title" x="48" y="55">Alaska Senate: how recorded preferences transfer</text>',
         f'<text class="sub" x="48" y="91">Rachel/FairVote November 11 CSV · all {total:,} ballot rows · four-stage replay · prepared November 13</text>',
         '<text class="sub" x="48" y="123">Ribbon width is proportional to ballots. Hover over a ribbon to see its exact count.</text>']
    for i,title in enumerate(TITLES):
        svg.append(f'<text class="stage" text-anchor="middle" x="{xvals[i]}" y="182">{title}</text>')
        svg.append(f'<text class="sub" text-anchor="middle" x="{xvals[i]}" y="210">Stage {i+1}</text>')
    for x0,x1,y0,y1,h,dx,a,b,n,stage in bands:
        d=f'M{x0},{y0} C{x0+dx},{y0} {x1-dx},{y1} {x1},{y1} L{x1},{y1+h} C{x1-dx},{y1+h} {x0+dx},{y0+h} {x0},{y0+h} Z'
        title=f'{TITLES[stage]} → {TITLES[stage+1]}: {NAMES[a]} → {NAMES[b]}: {n:,} ballots'
        svg.append(f'<path d="{d}" fill="{COLORS[a]}" fill-opacity="{.26 if a==b else .62}"><title>{html.escape(title)}</title></path>')
    for stage,counter in enumerate(counts):
        for candidate in ORDER:
            if candidate not in counter:continue
            y,h=pos[stage,candidate];mid=y+h/2
            svg.append(f'<rect x="{xvals[stage]}" y="{y}" width="{bar}" height="{h}" fill="{COLORS[candidate]}"><title>{NAMES[candidate]}: {counter[candidate]:,}</title></rect>')
            label=f'{SHORT[candidate]}  {counter[candidate]:,}'
            # Labels sit left of bars; large nodes center vertically; small nodes remain separated by a 30 px gap.
            svg.append(f'<text class="label" text-anchor="end" x="{xvals[stage]-9}" y="{mid+5}">{html.escape(label)}</text>')
    svg.extend(['<line x1="48" x2="1950" y1="935" y2="935" stroke="#D8E0E8"/>',
      f'<text class="foot" x="48" y="969">Initially inactive: {initial_inactive:,}. Final inactive: {final_inactive:,}, including {additional_inactive:,} newly inactive during transfers.</text>',
      '<text class="foot" x="48" y="998">A later overvote or two internal skipped rankings can stop transfers; trailing blanks mean no further preference.</text>',
      '<text class="foot" x="48" y="1027">Generic write-ins are removed first for this comparison. This is a preliminary replay, not certified election results.</text>','</svg>'])
    image='\n'.join(svg);(R/'senate_sankey.svg').write_text(image)
    body='<!doctype html><meta charset="utf-8"><title>Alaska Senate vote flow</title><style>body{margin:0;background:#eef2f6;font-family:Arial,sans-serif}main{max-width:2000px;margin:auto;background:white}svg{width:100%;height:auto}.table{margin:30px;border-collapse:collapse}.table td,.table th{padding:8px 14px;border-bottom:1px solid #ddd;text-align:left}h2{margin:30px}</style><main>'+image+'<h2>Exact transfer counts</h2><table class="table"><tr><th>Stage</th><th>From</th><th>To</th><th>Ballots</th></tr>'
    for stage,counter in enumerate(links):
        for (a,b),n in counter.items():
            if a!=b:body+=f'<tr><td>{stage+1} → {stage+2}</td><td>{NAMES[a]}</td><td>{NAMES[b]}</td><td>{n:,}</td></tr>'
    (R/'senate_sankey.html').write_text(body+'</table></main>')
    try:
        from PIL import Image,ImageDraw,ImageFont
        S=2;im=Image.new('RGBA',(W*S,H*S),'white');draw=ImageDraw.Draw(im)
        def font(n,bold=False):
            choices=['/System/Library/Fonts/Supplemental/Arial Bold.ttf' if bold else '/System/Library/Fonts/Supplemental/Arial.ttf','DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']
            for choice in choices:
                try:return ImageFont.truetype(choice,round(n*S))
                except OSError:pass
            return ImageFont.load_default()
        def txt(x,y,text,n=17,fill='#24354A',bold=False,anchor=None,stroke=0):draw.text((x*S,y*S),text,font=font(n,bold),fill=fill,anchor=anchor,stroke_width=round(stroke*S),stroke_fill='white')
        txt(48,29,'Alaska Senate: how recorded preferences transfer',32,bold=True)
        txt(48,73,f'Rachel/FairVote November 11 CSV · all {total:,} ballot rows · four-stage replay · prepared November 13',19,fill='#55677B')
        txt(48,105,'Ribbon width is proportional to ballots. Exact transfers are supplied in the accompanying tables.',19,fill='#55677B')
        for i,title in enumerate(TITLES):txt(xvals[i],182,title,21,bold=True,anchor='mm');txt(xvals[i],210,f'Stage {i+1}',19,fill='#55677B',anchor='mm')
        for x0,x1,y0,y1,h,dx,a,b,n,stage in bands:
            poly=[]
            for k in range(41):
                t=k/40;poly.append((S*cubic(x0,x0+dx,x1-dx,x1,t),S*cubic(y0,y0,y1,y1,t)))
            for k in range(40,-1,-1):
                t=k/40;poly.append((S*cubic(x0,x0+dx,x1-dx,x1,t),S*cubic(y0+h,y0+h,y1+h,y1+h,t)))
            color=COLORS[a].lstrip('#');rgb=tuple(int(color[i:i+2],16) for i in [0,2,4]);overlay=Image.new('RGBA',im.size,(0,0,0,0));ImageDraw.Draw(overlay).polygon(poly,fill=rgb+(round((.26 if a==b else .62)*255),));im=Image.alpha_composite(im,overlay);draw=ImageDraw.Draw(im)
        for stage,counter in enumerate(counts):
            for candidate in ORDER:
                if candidate not in counter:continue
                y,h=pos[stage,candidate];draw.rectangle((xvals[stage]*S,y*S,(xvals[stage]+bar)*S,(y+h)*S),fill=COLORS[candidate]);txt(xvals[stage]-9,y+h/2,f'{SHORT[candidate]}  {counter[candidate]:,}',16,bold=True,anchor='rm',stroke=2)
        draw.line([(48*S,935*S),(1950*S,935*S)],fill='#D8E0E8',width=2)
        txt(48,951,f'Initially inactive: {initial_inactive:,}. Final inactive: {final_inactive:,}, including {additional_inactive:,} newly inactive during transfers.',17,fill='#536579')
        txt(48,980,'A later overvote or two internal skipped rankings can stop transfers; trailing blanks mean no further preference.',17,fill='#536579')
        txt(48,1009,'Generic write-ins are removed first for this comparison. This is a preliminary replay, not certified election results.',17,fill='#536579')
        im.convert('RGB').save(R/'senate_sankey.png',optimize=True)
    except ImportError:print('PNG optional: install Pillow or use supplied standalone SVG.')


if __name__=='__main__':build()
