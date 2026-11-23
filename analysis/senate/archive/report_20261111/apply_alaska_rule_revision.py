"""Promote countable preferences to the headline; preserve raw descriptions in appendix."""
from pathlib import Path
import nbformat,json
R=Path(__file__).resolve().parent;p=R/'Alaska_2026_Senate_FairVote.ipynb'
nb=nbformat.read(p,as_version=4)
source=nb.cells[0].source
source=source.replace('<div class="n">777</div>','<div class="n">765</div>').replace('Peltola above Dan S. · both explicitly named','Peltola above Dan S. · both legally usable').replace('Peltola named; Dan S. not explicitly named','Only Peltola in usable finalist rankings')
source=source.replace('- **568 of 3,940 Daniel-first ballots (14.42%) visibly name both finalists and put Peltola first.** Lower-rank overvotes hide some candidate identities, leaving the full original-mark comparison bounded at 568–574.','- **568 of 3,940 literal Daniel-first ballots (14.42%) have both finalists in their usable rankings, with Peltola above Dan S.** The reverse count is **423 (10.74%)**. Headline comparisons now apply Alaska’s overvote and skipped-rank rules consistently.')
source=source.replace('- All 54 published round-count values match. The nine FairVote subgroup cells also match under the separately labeled first-visible-finalist definition.','- All 54 published round-count values match. A supplementary audit reproduces the nine FairVote article subgroup cells using a different visible-name definition; those are not the headline countable-preference results.')
source=source.replace('The Sankey and MDS use usable preferences after skipped-rank and overvote rules.','All headline preference comparisons, the Sankey and MDS use usable preferences after skipped-rank and overvote rules. We retain the same literal-rank-1 cohort so this change does not silently change the denominator.')
nb.cells[0].source=source
for c in nb.cells:
 s=c.source
 if c.cell_type=='markdown' and s.startswith(('## 1 · Daniel','## 2 · Daniel')):
  c.source='''## 1 · Daniel J. Sullivan Jr. first-choice ballots

**Daniel J. Sullivan Jr. is the outsider; Dan S. Sullivan is the incumbent senator.** The cohort remains **3,940 ballots explicitly naming Daniel J. at literal rank 1**. Keeping this cohort fixed lets us isolate the effect of applying Alaska’s counting rules to later preferences.

For the headline comparison, retain only the countable prefix: **keep earlier valid preferences, stop before an overvote, cross one internal skip, and stop at two consecutive internal skips**. Repeated candidates count once. Original FairVote records stay intact; no whole ballot is discarded merely for containing a later overvote.

**568 ballots (14.42%) have both finalists usable and place Peltola above Dan S. Sullivan.** The reverse count is **423 (10.74%)**. Another **765** have only Peltola in their usable finalist rankings, **481** have only Dan S., and **1,703** have neither finalist available in the usable prefix.

These are exact counts under the stated counting interpretation. Candidate identities hidden inside an excluded overvote do not need to be reconstructed.'''
 elif c.cell_type=='code' and s.startswith('show.preference_table()'):
  c.source='''show.preference_table()
usable=descriptive['question1_usable_prefix_categories']
show.table(pd.DataFrame([
 {'Final usable destination':'Peltola','Ballots':usable['peltola_above_senator_both_ranked']+usable['peltola_only_explicitly_ranked']},
 {'Final usable destination':'Dan S. Sullivan','Ballots':usable['senator_above_peltola_both_ranked']+usable['senator_only_explicitly_ranked']},
 {'Final usable destination':'Neither finalist / inactive','Ballots':usable['neither_explicitly_ranked']}
]),'Same 3,940 ballots: 1,333 Peltola, 904 Dan S., and 1,703 inactive')
'''
 elif c.cell_type=='markdown' and s.startswith('The strict original-mark comparison'):
  c.source='''**What changed:** names inside or below an overvote no longer contribute to the headline ranking comparison. Raw visible-name descriptions are preserved in the supplementary definition audit, where they are explicitly distinguished from countable preferences.

**Cohort sensitivity:** the separate first-structurally-usable-choice cohort contains **3,992** Daniel ballots. Under the same countable-prefix treatment, its both-finalist counts are **574 Peltola-above** and **430 Dan-above**. We do not substitute this larger cohort for the main literal-rank-1 comparison.'''
 elif c.cell_type=='markdown' and s.startswith('## 4 · Visible'):
  c.source=s.replace('## 4 · Visible finalist preferences and rule-based transfers are different calculations','## Supplementary audit · visible names versus countable preferences').replace('FairVote’s visible rank columns reproduce','This is a supplementary recorded-name description, not the main Alaska-rule result. FairVote’s visible rank columns reproduce')
 elif c.cell_type=='markdown' and s.startswith('## 7 · Source'):
  c.source=s.replace('- **Interpretation:** visible-name comparisons, hidden-identity sensitivity bounds and rule-based transfer availability are separate results. FairVote’s generic lower-overvote markers do not identify the candidate names hidden inside them.','- **Primary interpretation:** Alaska-countable preference prefixes are used for headline ranking comparisons, Sankey and MDS. Literal first-choice cohorts are explicitly retained/labeled; the separate first-usable-choice cohort is a sensitivity check. Visible-name comparisons and hidden-identity bounds are supplementary, not headline results.')
 elif c.cell_type=='code' and s.startswith('import descriptive_analysis'):
  if 'import verify_usable_preferences' not in s:
   s=s.replace('descriptive_verification=verify_fairvote.main()', 'descriptive_verification=verify_fairvote.main()\n    import verify_usable_preferences\n    usable_verification=verify_usable_preferences.main()')
nb.metadata['title']='Alaska 2026 Senate — FairVote data, Alaska counting rules'
nb.metadata['main_preference_definition']='Alaska-countable prefixes; raw visible-name descriptions supplementary only'
nbformat.validate(nb);nbformat.write(nb,p)
# Future template builds use the same source definition; no stale raw-mark headline returns.
pp=R/'display.py';t=pp.read_text();t=t.replace("('same_rank','Tied usable ranks (not possible after overvote truncation)'),",'');pp.write_text(t)
print('Alaska-rule main comparison installed; original FairVote source files unchanged.')
