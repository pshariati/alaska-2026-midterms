"""Independent Alaska-prefix / IRV audit; reads Rachel inputs and frozen references.

No producer module is imported. The oracle locates all structural barriers before
deduplicating candidates, rather than reusing the producer's state-machine parser.
It independently derives the removal order, then checks every node/link/path.
"""
from pathlib import Path
from collections import Counter
from html.parser import HTMLParser
import csv, hashlib, itertools, json, math, re

from analysis.shared.paths import INPUTS_ROOT, REFERENCES_ROOT, race_dir
ROOT=race_dir('us_senate')
HERE=ROOT/'flows'/'audits'
SENATE=INPUTS_ROOT/'Alaska_20261103_US_Senate_11_11.csv'
MAPPING={'Peltola, Mary':'peltola','Sullivan, Dan S.':'dan_sullivan',
         'Heikes, Gerald L.':'heikes','Sullivan, Daniel J. Jr.':'daniel_sullivan',
         'Write-in':'writein'}
NAMES={'peltola':'Mary Peltola','dan_sullivan':'Dan S. Sullivan',
       'heikes':'Gerald L. Heikes','daniel_sullivan':'Daniel J. Sullivan Jr.',
       'writein':'Generic write-in',None:'Inactive'}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def oracle(tokens):
    """Choose the earliest overvote/double-blank boundary before deduplication."""
    stop=[i for i,t in enumerate(tokens) if t=='overvote']
    stop += [i for i in range(len(tokens)-1)
             if tokens[i]==tokens[i+1]=='skipped']
    end=min(stop,default=len(tokens))
    named=[t for t in tokens[:end] if t!='skipped']
    return tuple(dict.fromkeys(named))

def allocate(profiles,continuing):
    c=Counter()
    for pref,n in profiles.items():
        c[next((x for x in pref if x in continuing),None)]+=n
    return c

class TableParser(HTMLParser):
    def __init__(self):
        super().__init__();self.on=False;self.cell=None;self.row=None;self.rows=[]
    def handle_starttag(self,tag,attrs):
        if tag=='tbody':self.on=True
        if not self.on:return
        if tag=='tr':self.row=[]
        elif tag in ['th','td']:self.cell=[]
    def handle_data(self,data):
        if self.on and self.cell is not None:self.cell.append(data)
    def handle_endtag(self,tag):
        if tag=='tbody':self.on=False
        if not self.on:return
        if tag in ['th','td'] and self.cell is not None:
            self.row.append(' '.join(' '.join(self.cell).split()));self.cell=None
        if tag=='tr' and self.row:self.rows.append(self.row);self.row=None

def read_reference(p):
    parser=TableParser();parser.feed(p.read_text())
    result={}
    for row in parser.rows:
        result[row[0]]=[]
        for x in row[1:]:
            match=re.search(r'([0-9,]+)\s+(?:votes|ballots)',x)
            result[row[0]].append(int(match[1].replace(',','')) if match else None)
    return result

def independent_article_audit():
    article=REFERENCES_ROOT/'fairvote_article_20261112.html'
    provenance=json.loads((REFERENCES_ROOT/'fairvote_article_provenance.json').read_text())
    assert sha(article)==provenance['sha256']==provenance['source_fetch_record']['sha256']
    parser=TableParser();parser.feed(article.read_text())
    desired=['Republican candidate (Wilson, Bronson or Taylor)','Kreiss-Tomkins','Blank first ranking for governor','Total']
    found={r[0]:r for r in parser.rows if r[0] in desired}
    assert set(found)==set(desired)
    article_rows={name:[int(x.replace(',','')) for x in found[name][1:]] for name in desired}
    assert all(len(x)==4 and sum(x[:3])==x[3] for x in article_rows.values())
    assert [sum(article_rows[k][i] for k in desired[:3]) for i in range(4)]==article_rows['Total']
    def normalize(value):return tuple(int(x) for x in value.rstrip('_').split('_'))
    governor={}
    with (INPUTS_ROOT/'Alaska_20261103_US_Governor_11_11.csv').open(encoding='utf-8-sig',newline='') as f:
        for row in csv.DictReader(f):
            uid=normalize(row['ballotID']);assert uid not in governor;governor[uid]=row['rank1']
    observed=Counter();other_contents=Counter();n=0
    with SENATE.open(encoding='utf-8-sig',newline='') as f:
        for row in csv.DictReader(f):
            if row['rank1']!='Sullivan, Daniel J. Jr.':continue
            n+=1;g=governor.get(normalize(row['ballotID']))
            group=desired[0] if g in ['Bronson/Church','Taylor/English','Wilson/Shower'] else desired[1] if g=='Kreiss-Tomkins/Johnson' else desired[2]
            if group==desired[2]:other_contents[str(g)]+=1
            finalist=next((row[f'rank{i}'] for i in range(1,6) if row[f'rank{i}'] in ['Peltola, Mary','Sullivan, Dan S.']),None)
            j=0 if finalist=='Peltola, Mary' else 1 if finalist=='Sullivan, Dan S.' else 2
            observed[group,j]+=1
    cells=[]
    for group in desired[:3]:
        for j,dest in enumerate(['Peltola','Dan S. Sullivan','No visible named finalist']):
            assert observed[group,j]==article_rows[group][j]
            cells.append({'article_governor_row_label':group,'destination':dest,'observed_raw_Rachel':observed[group,j],'frozen_article':article_rows[group][j]})
    assert n==article_rows['Total'][3]==3940
    result={'frozen_article_sha256':sha(article),'article_provenance':provenance,'independent_raw_Rachel_join':True,'cohort_n':n,'verified_actual_frozen_article_cells':cells,'other_governor_group_contents':dict(other_contents),'scope':'Visible first-named finalist, ignoring barriers; supplementary descriptive audit, not legal transfers. Broader Other label retained if article blank label is inaccurate.','status':'passed'}
    (HERE/'independent_article_audit.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

def main():
    report={'source_policy':'Only Rachel supplied ballot CSVs are ballot inputs; producer modules not imported.'}
    patterns=Counter();source_tokens=Counter();ids=set();repeat_rows=0;ov_rows=0;two_skip_rows=0
    with SENATE.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f);columns=reader.fieldnames
        for row in reader:
            assert row['ballotID'] not in ids;ids.add(row['ballotID'])
            toks=tuple(row[f'rank{i}'] for i in range(1,6));source_tokens[toks]+=1
            assert not (set(toks)-set(MAPPING)-{'overvote','skipped'})
            patterns[tuple(MAPPING[x] for x in oracle(toks))]+=1
            names=[x for x in toks if x in MAPPING]
            repeat_rows+=len(names)!=len(set(names));ov_rows+='overvote' in toks
            last=max((i for i,t in enumerate(toks) if t!='skipped'),default=-1)
            two_skip_rows+=any(toks[i]==toks[i+1]=='skipped' for i in range(last))
    total=sum(patterns.values());assert total==len(ids)
    full=set(MAPPING.values());without_writein=full-{'writein'}
    active_sets=[full,without_writein];removal=['writein']
    while len(active_sets[-1])>2:
        counts=allocate(patterns,active_sets[-1])
        fewest=min(counts[x] for x in active_sets[-1])
        tied=[x for x in active_sets[-1] if counts[x]==fewest]
        assert len(tied)==1,'A tie needs a separately documented random resolution'
        loser=tied[0];removal.append(loser);active_sets.append(active_sets[-1]-{loser})
    assert removal==['writein','daniel_sullivan','heikes']
    stages=[allocate(patterns,active) for active in active_sets]
    assert all(sum(c.values())==total for c in stages)
    # No first-round named-candidate majority is present in this source cohort.
    assert max(stages[1][x] for x in without_writein)*2 < total-stages[1][None]
    assert stages[0]['writein']<stages[0]['heikes']<stages[0]['dan_sullivan']
    paths=Counter()
    for pref,n in patterns.items():
        paths[tuple(next((x for x in pref if x in a),None) for a in active_sets)]+=n
    links=[Counter() for _ in range(3)]
    for p,n in paths.items():
        for s in range(3):links[s][p[s],p[s+1]]+=n
    result=json.loads((ROOT/'flows/senate_sankey.json').read_text())
    assert result['source_sha256']==sha(SENATE)
    assert result['total_ballots']==total
    for i,counts in enumerate(stages):
        assert {str(k):v for k,v in counts.items()}==result['round_counts'][i]
    expected_nodes={(i+1,k):n for i,c in enumerate(stages) for k,n in c.items()}
    actual_nodes={(x['stage'],x['candidate_key']):x['ballots'] for x in result['nodes']}
    assert expected_nodes==actual_nodes
    actual_links={(x['stage_from'],x['source_candidate_key'],x['target_candidate_key']):x['ballots'] for x in result['links']}
    expected_links={(i+1,a,b):n for i,c in enumerate(links) for (a,b),n in c.items()}
    assert actual_links==expected_links
    actual_paths=Counter({tuple(x[f'stage{i}'] for i in range(1,5)):x['ballots'] for x in result['paths']})
    assert actual_paths==Counter({tuple(NAMES[k] for k in p):n for p,n in paths.items()})
    for i,ls in enumerate(links):
        assert sum(ls.values())==total
        for k,n in stages[i].items():assert sum(n2 for (a,b),n2 in ls.items() if a==k)==n
        for k,n in stages[i+1].items():assert sum(n2 for (a,b),n2 in ls.items() if b==k)==n
    # Check CSV delivery tables exactly correspond to the independently verified JSON.
    for suffix,objects in [('nodes',result['nodes']),('links',result['links']),('paths',result['paths'])]:
        with (ROOT/f'flows/senate_flow_{suffix}.csv').open(newline='') as f:
            rows=list(csv.DictReader(f));assert len(rows)==len(objects)
            assert rows==[{k:('' if v is None else str(v)) for k,v in row.items()} for row in objects]
    # Check SVG ribbon heights use one common per-ballot scale, including self flows.
    svg=(ROOT/'flows/senate_sankey.svg').read_text();scale=(886-232-30*5)/total
    band_counts=Counter()
    for line in svg.splitlines():
        if not line.startswith('<path '):continue
        d=re.search(r' d="([^"]+)"',line)[1]
        label=re.search(r'<title>(.*?)</title>',line)[1]
        n=int(re.search(r': ([0-9,]+) ballots$',label)[1].replace(',',''))
        coords=[float(x) for x in re.findall(r'-?\d+(?:\.\d+)?(?:e[+-]?\d+)?',d)]
        # Top path ends at coords[6:8], vertical edge ends at coords[8:10].
        assert math.isclose(coords[9]-coords[7],n*scale,abs_tol=1e-8)
        band_counts[n]+=1
    assert band_counts==Counter(x['ballots'] for x in result['links'])
    report.update(source_sha256=sha(SENATE),source_rows=total,source_columns=columns,
                  source_rank_patterns=len(source_tokens),prefix_patterns=len(patterns),
                  irregularities={'rows_with_overvote':ov_rows,'rows_with_internal_double_skip':two_skip_rows,'rows_with_repeated_candidate':repeat_rows},
                  independently_derived_removal_order=removal,
                  nodes_verified=len(actual_nodes),links_verified=len(actual_links),paths_verified=len(actual_paths),
                  all_node_link_path_and_CSV_counts_match=True,all_stage_totals_conserved=True,
                  all_svg_ribbons_use_constant_ballot_scale=True,
                  initial_inactive=stages[0][None],final_inactive=stages[-1][None],
                  newly_inactive=stages[-1][None]-stages[0][None],
                  final_active={NAMES[k]:v for k,v in stages[-1].items() if k is not None},
                  named_candidate_initial_allocation={NAMES[k]:v for k,v in stages[1].items()})
    benchmarks=[]
    for slug,race in [('governor','Governor'),('us_house','House'),('us_senate','Senate')]:
        source=INPUTS_ROOT/f'Alaska_20261103_US_{race}_11_11.csv'
        fp=REFERENCES_ROOT/f'fairvote_{slug}.html';ref=read_reference(fp)
        pref=Counter();seen=set()
        with source.open(encoding='utf-8-sig',newline='') as f:
            for row in csv.DictReader(f):
                assert row['ballotID'] not in seen;seen.add(row['ballotID'])
                pref[oracle(tuple(row[f'rank{i}'] for i in range(1,6)))]+=1
        active=set(ref)-{'Inactive Ballots'};stage_sets=[set(active)]
        active.remove('Write-in');stage_sets.append(set(active))
        while len(active)>2:
            cc=allocate(pref,active);lowest=min(active,key=lambda k:cc[k]);active.remove(lowest);stage_sets.append(set(active))
        for stage,active in enumerate(stage_sets):
            published_active={k for k,v in ref.items() if k!='Inactive Ballots' and v[stage] is not None}
            assert active==published_active,(slug,stage,'elimination order differs')
            cc=allocate(pref,active);assert sum(cc.values())==len(seen)
            for k,v in ref.items():
                if v[stage] is None:continue
                observed=cc[None]-pref[()] if k=='Inactive Ballots' else cc[k]
                assert observed==v[stage],(slug,stage,k,observed,v[stage])
                benchmarks.append({'contest':slug,'stage':stage+1,'candidate':k,'observed':observed,'expected':v[stage]})
    assert len(benchmarks)==54
    report['independent_frozen_benchmark_matches']=len(benchmarks)
    article=independent_article_audit()
    report['independent_actual_frozen_article_cells_verified']=len(article['verified_actual_frozen_article_cells'])
    report['benchmark_status']='Matches frozen preliminary 11/11 RCVis tables; not current live article or certified DOE results.'
    report['status']='passed'
    (HERE/'independent_flow_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    (HERE/'independent_benchmark_cells.json').write_text(json.dumps(benchmarks,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
