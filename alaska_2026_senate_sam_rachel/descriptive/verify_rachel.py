"""Independent Rachel-only question1 check, article-definition comparison and tests."""
from pathlib import Path
from collections import Counter,defaultdict
import gzip,csv,json,itertools,unittest,hashlib
from html.parser import HTMLParser
R=Path(__file__).resolve().parent
P='Peltola, Mary';D='Sullivan, Dan S.';OUT='Sullivan, Daniel J. Jr.'
GOVR={'Bronson/Church','Taylor/English','Wilson/Shower'}
ARTICLE=R.parent/'references/fairvote_article_20261112.html'

class ArticleTables(HTMLParser):
    def __init__(self):
        super().__init__();self.tables=[];self.rows=None;self.row=None;self.cell=None
    def handle_starttag(self,tag,attrs):
        if tag=='table':self.rows=[]
        elif tag=='tr' and self.rows is not None:self.row=[]
        elif tag in ('td','th') and self.row is not None:self.cell=[]
    def handle_data(self,data):
        if self.cell is not None:self.cell.append(data)
    def handle_endtag(self,tag):
        if tag in ('td','th') and self.cell is not None:
            self.row.append(' '.join(' '.join(self.cell).split()));self.cell=None
        elif tag=='tr' and self.row is not None:self.rows.append(self.row);self.row=None
        elif tag=='table' and self.rows is not None:self.tables.append(self.rows);self.rows=None

def historical_article_reference():
    """Read the authenticated Nov12 article containing Nov11 CVR results."""
    expected='9351b68a1dd65a7965d8500c2b11a975c3e3d147bd77a8c53b9528ab508ca2c2'
    assert hashlib.sha256(ARTICLE.read_bytes()).hexdigest()==expected
    parser=ArticleTables();parser.feed(ARTICLE.read_text(encoding='utf-8'))
    table=next(t for t in parser.tables if t and 'First choice in governor' in t[0][0])
    assert len(table)==5 and all(len(row)==5 for row in table)
    rows=[[int(x.replace(',','')) for x in row[1:]] for row in table[1:]]
    assert all(sum(row[:3])==row[3] for row in rows)
    assert [sum(row[i] for row in rows[:3]) for i in range(4)]==rows[3]
    assert rows[3][3]==3940
    groups=['Republican','Kreiss-Tomkins','Other/blank/write-in/overvote/not in governor file']
    destinations=['Peltola','Dan S. Sullivan','No visible named finalist']
    return {group:dict(zip(destinations,row[:3])) for group,row in zip(groups,rows[:3])}

def simple_possibilities(tokens):
    # Separate oracle: lists of possible earliest P/D positions rather than the
    # producer's candidate-category function. Unknown OV is never filled in data.
    hidden=[i+1 for i,x in enumerate(tokens) if x=='overvote'];out=set()
    seenp=next((i+1 for i,x in enumerate(tokens) if x==P),99)
    seend=next((i+1 for i,x in enumerate(tokens) if x==D),99)
    for includes in itertools.product([(False,False),(True,False),(False,True),(True,True)],repeat=len(hidden)):
        p=min([seenp]+[rank for rank,(hasp,hasd) in zip(hidden,includes) if hasp])
        d=min([seend]+[rank for rank,(hasp,hasd) in zip(hidden,includes) if hasd])
        out.add((p<d and p<99 and d<99,d<p and p<99 and d<99))
    return out

class HiddenOvervoteTests(unittest.TestCase):
    def test_after_first_visible_finalist_cannot_reverse(self):
        self.assertEqual(simple_possibilities([OUT,P,'overvote',D,'skipped']),{(True,False)})
    def test_before_visible_finalists_can_reverse_or_tie(self):
        self.assertEqual(simple_possibilities([OUT,'overvote',P,D,'skipped']),{(True,False),(False,True),(False,False)})
    def test_absent_finalist_can_be_hidden(self):
        self.assertEqual(simple_possibilities([OUT,P,'overvote','skipped','skipped']),{(True,False),(False,False)})
    def test_no_overvote_is_complete(self):
        self.assertEqual(simple_possibilities([OUT,P,D,'skipped','skipped']),{(True,False)})

def main():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(HiddenOvervoteTests)
    check=unittest.TextTestRunner(verbosity=2).run(suite)
    if not check.wasSuccessful():raise ValueError('Hidden overvote unit test failed')
    groups=defaultdict(Counter);prefix=defaultdict(Counter);n=0;visibleboth=0;lowerov=0;bounds=Counter();ids=set();metadata_flags=Counter()
    with gzip.open(R/'linked_ballots.csv.gz','rt',encoding='utf-8',newline='') as f:
      for row in csv.DictReader(f):
        tokens=json.loads(row['us_senate_rank_tokens_json'])
        if tokens[0]!=OUT:continue
        n+=1;assert row['ballot_uid'] not in ids;ids.add(row['ballot_uid'])
        posp=[i for i,x in enumerate(tokens) if x==P];posd=[i for i,x in enumerate(tokens) if x==D]
        visibleboth+=bool(posp and posd and min(posp)<min(posd))
        lowerov+='overvote' in tokens[1:]
        possible=simple_possibilities(tokens)
        bounds['peltola_strict_both_lower']+=all(x[0] for x in possible)
        bounds['peltola_strict_both_upper']+=any(x[0] for x in possible)
        bounds['dan_strict_both_lower']+=all(x[1] for x in possible)
        bounds['dan_strict_both_upper']+=any(x[1] for x in possible)
        metadata_flags['nonempty_senate_rank1_ambiguous_candidates']+=bool(row['us_senate_rank1_ambiguous_candidates'])
        metadata_flags['nonempty_senate_rank1_overvote_candidates']+=bool(row['us_senate_rank1_overvote_candidates'])
        # Earliest visible named finalist intentionally ignores unknown OV tokens.
        # It is an observable named-slot statistic, not an official-rule transfer.
        dest=next((x for x in tokens if x in [P,D]),None)
        dest='Peltola' if dest==P else 'Dan S. Sullivan' if dest==D else 'No visible named finalist'
        gov=json.loads(row['governor_rank_tokens_json']) if row['governor_rank_tokens_json'] else None
        first=gov[0] if gov else None
        group='Republican' if first in GOVR else 'Kreiss-Tomkins' if first=='Kreiss-Tomkins/Johnson' else 'Other/blank/write-in/overvote/not in governor file'
        groups[group][dest]+=1
        pref=json.loads(row['us_senate_alaska_prefix_json'])
        pd=next((x for x in pref if x in [525,527]),None)
        prefix[group]['Peltola' if pd==525 else 'Dan S. Sullivan' if pd==527 else 'No visible named finalist']+=1
    records=[]
    for group,dests in historical_article_reference().items():
      for destination,expected in dests.items():
        observed=groups[group][destination]
        records.append(dict(governor_first_choice_group=group,visible_named_finalist=destination,observed_rachel=observed,article_reference=expected,difference=observed-expected,match=observed==expected,strict_prefix_count=prefix[group][destination],definition='First finalist named in visible Rachel rank cells, ignoring unknown overvote tokens; not an official-rule transfer'))
    with (R/'visible_finalist_article_comparison.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    result=dict(sole_ballot_input='Rachel-only linked data; every original Rachel row preserved in linked GZ. No original CVR or old normalized files read.',cohort_n=n,independent_visible_both_ranked_peltola_before_dan=visibleboth,lower_overvote_ballots=lowerov,independent_partial_information_bounds=dict(bounds),rank1_metadata_flags=dict(metadata_flags),article_comparison_numeric_cells=len(records),article_comparison_matches=sum(r['match'] for r in records),article_reference_status='Authenticated archived article updated November12 2026, using November11 CVR; not a claim to match the subsequently updated live article.',article_reference_file=str(ARTICLE.relative_to(R.parent)),article_reference_sha256=hashlib.sha256(ARTICLE.read_bytes()).hexdigest(),visible_finalist_governor_groups={k:dict(v) for k,v in groups.items()},strict_prefix_governor_groups={k:dict(v) for k,v in prefix.items()},interpretation='Nine cells parsed from the archived article are reproduced by the stated visible-name definition. This does not establish FairVote internal implementation, and these descriptive counts are not official-rule transfers. The article labels its residual governor group blank; our broader category includes blanks, overvotes, write-ins and file absences, so agreement does not establish every residual ballot was literally blank.',tests=dict(hidden_overvote_cases=check.testsRun,failures=0,unique_cohort_ballot_ids=len(ids)))
    (R/'descriptive_verification.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
    assert all(r['match'] for r in records)
    assert visibleboth==bounds['peltola_strict_both_lower']
    return result
if __name__=='__main__':main()
