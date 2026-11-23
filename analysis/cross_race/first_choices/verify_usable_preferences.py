"""Independent check of the Alaska-rule headline, using FairVote's Senate CSV only."""
from pathlib import Path
from analysis.shared.paths import REPO_ROOT, INPUTS_ROOT, REFERENCES_ROOT, SHARED_ROOT, race_dir, model_dir, cross_race_dir, resolve_recorded_path
from collections import Counter
import csv,json,unittest
from analysis.cross_race.first_choices.descriptive_analysis import prefix
R=Path(__file__).resolve().parent
P='Peltola, Mary';D='Sullivan, Dan S.';OUT='Sullivan, Daniel J. Jr.'

def oracle(tokens):
    # Look-ahead barrier selection, independent of the producer's sequential scan.
    occupied=[i for i,x in enumerate(tokens) if x!='skipped']
    last=max(occupied,default=-1)
    barriers=[i for i,x in enumerate(tokens) if x=='overvote']
    barriers += [i+1 for i in range(len(tokens)-1) if tokens[i]==tokens[i+1]=='skipped' and i+1<last]
    stop=min(barriers,default=len(tokens))
    return list(dict.fromkeys(x for x in tokens[:stop] if x not in ['skipped','Write-in']))

class AlaskaRuleChecks(unittest.TestCase):
 def test_earlier_preference_kept(self):self.assertEqual(prefix([OUT,'overvote',P,D,'skipped'],'us_senate')[0],[526])
 def test_one_skip_crossed(self):self.assertEqual(prefix([OUT,'skipped',P,D,'skipped'],'us_senate')[0],[526,525,527])
 def test_two_skips_stop(self):self.assertEqual(prefix([OUT,'skipped','skipped',P,D],'us_senate')[0],[526])
 def test_trailing_blanks_normal(self):self.assertEqual(prefix([OUT,'skipped','skipped','skipped','skipped'],'us_senate')[1],'end_of_ranks')
 def test_writein_is_occupied(self):self.assertEqual(prefix([OUT,'skipped','Write-in','skipped',P],'us_senate')[0],[526,373,525])
 def test_repeat_counts_once(self):self.assertEqual(prefix([OUT,OUT,P,D,'skipped'],'us_senate')[0],[526,525,527])

def main():
 tests=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(AlaskaRuleChecks))
 if not tests.wasSuccessful():raise AssertionError('Rule tests failed')
 counts=Counter();n=0
 with (INPUTS_ROOT/'Alaska_20261103_US_Senate_11_11.csv').open(encoding='utf-8-sig',newline='') as f:
  for row in csv.DictReader(f):
   if row['rank1']!=OUT:continue
   n+=1;pref=oracle([row[f'rank{i}'] for i in range(1,6)])
   p=pref.index(P) if P in pref else None;d=pref.index(D) if D in pref else None
   key='neither_explicitly_ranked' if p is None and d is None else 'senator_only_explicitly_ranked' if p is None else 'peltola_only_explicitly_ranked' if d is None else 'peltola_above_senator_both_ranked' if p<d else 'senator_above_peltola_both_ranked'
   counts[key]+=1
 result=json.loads((R/'descriptive_results.json').read_text());assert dict(counts)==result['question1_usable_prefix_categories'];assert sum(counts.values())==n==result['question1_literal_rank1_daniel_j_n']
 # This verification must remain valid after a fresh model rerun. Timing fields
 # change on rerun; model reproducibility is checked separately in the full audit.
 record={'source':'FairVote Senate CSV only','cohort_n':n,'independent_usable_counts':dict(counts),'regression_tests_passed':tests.testsRun,'status':'passed'}
 (R/'usable_preference_verification.json').write_text(json.dumps(record,indent=2));print(json.dumps(record,indent=2));return record
if __name__=='__main__':main()
