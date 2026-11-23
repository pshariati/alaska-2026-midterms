"""FairVote-only, fully recomputed research notebook. No historical results are inputs."""
from pathlib import Path
import json
import nbformat as nbf
R=Path(__file__).resolve().parent
D=json.loads((R/'descriptive/descriptive_results.json').read_text())
M=json.loads((R/'mds/mds_results.json').read_text())
assert M['status']=='complete'
md=nbf.v4.new_markdown_cell
def code(s):return nbf.v4.new_code_cell(s,metadata={'tags':['hide-input'],'jupyter':{'source_hidden':True}})
cells=[
md('''<div class="sam-kicker">Princeton · FairVote data · November 13, 2026</div>
<div class="sam-title">Alaska 2026 Senate<br>FairVote-only rerun for Sam</div>

**Active analysis version · November 11 CSV snapshot · fully rerun November 13**

This notebook rebuilds the linked ballot analysis, Sankey, and original one-axis MDS analysis from **FairVote’s three supplied CSVs only**. It does not read the earlier official-JSON extraction, old linked ballots, old rank patterns, old fitted axes, or old randomized results. The previous notebook is preserved as historical work. Candidate-party labels are clearly identified reference annotations; they are not voter-registration data.'''),
code('''from pathlib import Path
import sys,json,csv,gzip,hashlib,contextlib,io,os
import numpy as np
import pandas as pd
from IPython.display import display,HTML,Image
ROOT=Path.cwd().resolve()
assert (ROOT/'inputs/Alaska_20261103_US_Senate_11_11.csv').is_file(), 'Open from the FairVote package folder.'
WORKSPACE=ROOT.parent
FAIRVOTE_INPUT_READS=set()
# Enforce the source policy: workspace data outside this FairVote package cannot be opened.
def fairvote_source_guard(event,args):
    if event!='open' or not args or not isinstance(args[0],(str,bytes,os.PathLike)):return
    try:p=Path(os.fsdecode(args[0])).resolve()
    except (ValueError,OSError):return
    if WORKSPACE in p.parents and ROOT not in p.parents and p.suffix.lower() in {'.csv','.tsv','.gz','.zip','.json','.sqlite','.xlsx'}:
        raise PermissionError('FairVote-only analysis: external workspace data source blocked: '+str(p))
    mode=args[1] if len(args)>1 else None
    if ROOT/'inputs' in p.parents and p.suffix.lower()=='.csv' and (not isinstance(mode,str) or 'r' in mode):
        FAIRVOTE_INPUT_READS.add(p.name)
sys.addaudithook(fairvote_source_guard)
for folder in [ROOT,ROOT/'descriptive',ROOT/'mds',ROOT/'flows']:sys.path.insert(0,str(folder))
import display as show
show.theme()
print('Source policy active: only the supplied FairVote ballot CSVs are used.')
'''),
md('''## 1 · Rebuild and link FairVote’s files

The source files contain one row per ballot/contest, five literal rank tokens, ballot identifiers, geography/counting metadata, and first-rank ambiguity/overvote annotations. Every original 15-column row is preserved. A named cell, `skipped`, and `overvote` remain distinct.

IDs are normalized only for joining: trailing underscores and zero-padding are removed from the three numeric ID components. We check for collisions and join by ID, never row position. **No older source fills absent records or hidden overvote identities.**'''),
code('''import descriptive_analysis
with contextlib.redirect_stdout(io.StringIO()):
    descriptive_analysis.ingest(ROOT/'inputs')
    descriptive_analysis.analyze()
    import verify_fairvote
    descriptive_verification=verify_fairvote.main()
descriptive=json.loads((ROOT/'descriptive/descriptive_results.json').read_text())
provenance=json.loads((ROOT/'descriptive/source_provenance.json').read_text())
assert provenance['id_join']['senate_house_ids_identical']
assert provenance['id_join']['governor_subset_of_federal']
assert provenance['id_join']['missing_governor_rows']==130
show.table(pd.DataFrame([{'Source':slug,'Ballots':f"{provenance['rows'][slug]:,}",'File':meta['filename']} for slug,meta in provenance['inputs'].items()]),'FairVote-only source coverage')
show.table(pd.DataFrame([{'Senate literal first choice':name,'Ballots':f'{count:,}'} for name,count in descriptive['literal_rank1_senate_cohorts'].items()]),'All Senate first-choice categories; no ballots dropped')
'''),
md('''## 2 · Daniel J. Sullivan Jr. first-choice ballots

**Daniel J. Sullivan Jr. is the outsider; Dan S. Sullivan is the incumbent senator.** There are **3,940 literal first-choice ballots** for Daniel J. in FairVote’s Senate file.

**568 ballots explicitly name both finalists and place Peltola above Dan S. Sullivan: 14.42% of the cohort.** Another **777 name Peltola but do not explicitly name Dan S.** These visible-name categories total **1,345 ballots (34.14%)** when combined. They describe the candidate names actually visible in FairVote’s rank columns.

The reverse visible-name comparison is **424 both-named ballots with Dan S. above Peltola**, plus **486 naming Dan S. but not explicitly Peltola**, or **910 combined**. Neither finalist is explicitly named on **1,685 ballots**.

**Information limit:** 26 of Daniel’s ballots have a lower-rank `overvote` marker, without the names of the candidates involved. “Not explicitly named” therefore does not always establish that a candidate was unranked. We keep those original markers and do not restore identities from the earlier archive.'''),
code('''show.preference_table()
bounds=descriptive['question1_partial_information_bounds']
show.table(pd.DataFrame([
 {'Measure':'Peltola above Dan S., both named in visible rank cells','Ballots':descriptive['question1_visible_named_slot_categories'].get('peltola_above_senator_both_ranked',0)},
 {'Measure':'Minimum strict both-ranked Peltola-above count consistent with hidden identities','Ballots':bounds['definite_both_ranked_peltola_above']},
 {'Measure':'Maximum strict both-ranked Peltola-above count consistent with hidden identities','Ballots':bounds['possible_both_ranked_peltola_above']},
 {'Measure':'Ballots containing lower-rank overvote markers','Ballots':descriptive['question1_flags_and_finalist_transfers']['lower_overvote_ballots']}
]),'What FairVote’s files identify, and what remains partially observed')
'''),
md('''The strict original-mark comparison is therefore bounded at **568–574** under the unknown lower-overvote identities. The earlier archive-based figure of 573 lies within that range, but **FairVote’s files alone do not identify 573 exactly**, so it is not carried over as this notebook’s result. These bounds are sensitivity bounds, not reconstructed candidate identities.

The first usable-choice sensitivity gives **3,992** Daniel ballots, including ballots with a valid initial skip; in that larger cohort, **574** visibly name both finalists with Peltola above Dan S. The headline cohort remains literal rank 1.'''),
md('''## 3 · Governor and House choices within each Senate first-choice group

Each cell gives **ballots (percentage of its full Senate cohort)**. Main tables use literal rank 1 in every race. Blanks, overvotes, write-ins and the 130 governor-file absences remain explicit categories. Those absent governor rows are not filled and are not treated as blank votes.

**Party means the selected candidate’s or ticket’s affiliation.** FairVote’s CSVs contain no voter-registration party column. We use an explicit static candidate-party annotation lookup: Kreiss-Tomkins/Johnson is Democrat/Nonpartisan; Bill Hill is Nonpartisan; Daniel J. has no listed affiliation. All ballot counts are derived only from FairVote’s files.'''),
code('''show.cross_table('governor')
show.cross_table('us_house')
show.party_plot()
show.cross_table('governor',party=True)
show.cross_table('us_house',party=True)
'''),
md('''### First-usable-choice sensitivity

These tables use the structural first usable choice consistently in all three contests, allowing one internal skipped rank and retaining a generic write-in as a named first usable option. They are labeled separately from literal-rank-1 tables.'''),
code('''show.cross_table('governor',sensitivity=True)
show.cross_table('us_house',sensitivity=True)
'''),
md('''## 4 · Visible finalist preferences and rule-based transfers are different calculations

FairVote’s visible rank columns reproduce the FairVote article’s Daniel subgroup totals exactly when we select the **first explicitly named finalist, ignoring counting barriers**:

- Peltola first among visible finalists: **1,345**.
- Dan S. first among visible finalists: **910**.
- Neither finalist explicitly named: **1,685**.

Under the documented overvote/skip barriers, the same literal-first-choice cohort instead yields **1,333 Peltola**, **904 Dan S.**, and **1,703 inactive**. That second calculation describes usable transfers. We do not label the first calculation an official-rule transfer tally. Reproducing the article’s descriptive numbers does not prove which internal code FairVote used.'''),
code('''flags=descriptive['question1_flags_and_finalist_transfers'];visible=descriptive['question1_visible_named_slot_categories']
show.table(pd.DataFrame([
 {'Destination':'Peltola','First visible named finalist':visible.get('peltola_above_senator_both_ranked',0)+visible.get('peltola_only_explicitly_ranked',0),'Rule-based usable finalist':flags['transfer_to_peltola']},
 {'Destination':'Dan S. Sullivan','First visible named finalist':visible.get('senator_above_peltola_both_ranked',0)+visible.get('senator_only_explicitly_ranked',0),'Rule-based usable finalist':flags['transfer_to_senator']},
 {'Destination':'Neither / inactive','First visible named finalist':visible.get('neither_explicitly_ranked',0),'Rule-based usable finalist':flags['transfer_to_neither_finalist']}
]),'Same 3,940 ballots; two explicitly different measures')
assert descriptive_verification['article_comparison_matches']==descriptive_verification['article_comparison_numeric_cells']==9
article=pd.read_csv(ROOT/'descriptive/visible_finalist_article_comparison.csv')
show.table(article[['governor_first_choice_group','visible_named_finalist','observed_fairvote','article_reference','strict_prefix_count']],'All nine FairVote article subgroup cells reproduced by the visible-finalist definition')
'''),
md('''## 5 · FairVote-only Sankey: all Senate ballot paths

This diagram is rebuilt directly from FairVote’s five Senate rank columns. It follows the predeclared comparison sequence **write-in removed → Daniel J. removed → Heikes removed**. Each ballot goes to its first usable continuing candidate, or to inactive if none remains. Every node and link is checked for conservation, and each stage totals **244,705 ballots**.

Initial allocation uses the first usable choice, so Daniel begins at **3,992**, rather than the literal 3,940 cohort. After receiving write-in transfers his node is **4,055**. The width of each ribbon represents ballots; horizontal placement separates counting stages.'''),
code('''import build_flows
with contextlib.redirect_stdout(io.StringIO()):flow=build_flows.build()
assert flow['mass_conservation_passed']
assert flow['benchmark']['matches']==flow['benchmark']['numeric_cells']==18
display(Image(filename=str(ROOT/'flows/senate_sankey.png'),width=1250))
show.table(pd.read_csv(ROOT/'flows/senate_flow_nodes.csv'),'Exact FairVote-only Sankey node counts')
'''),
md('''There are **1,363 initially inactive** and **5,549 finally inactive** ballots; **4,186** become newly inactive. Final active counts are **119,933 Peltola** and **119,223 Dan S. Sullivan**. All **18 published Senate round-table numeric values** match the frozen FairVote benchmark after aligning its incremental inactive baseline.

This is the preliminary November 11 snapshot, not a final certified tally or a prediction for ballots absent from these files. The diagram tracks counting allocations, not voters changing their minds.'''),
md('''## 6 · Original one-axis MDS · fresh fit and fresh randomized profiles

The only model is the original one-dimensional **candidate-axis** method, using the same mathematical core and fitting budget as before. No earlier profiles, positions or simulation results are used as inputs.

**FairVote-only cohort preparation.** Read the Senate CSV directly. Cross a single internal `skipped` token; stop at an `overvote` token or the second consecutive internal skip; retain the first occurrence of repeated candidates. Preserve the occupied rank of a generic write-in before excluding it from the four-candidate model. Empty prefixes remain counted separately. Original FairVote strings remain preserved in the input and linked rows.

**Axis construction.** Let Aᵢⱼ count ballots where j immediately follows i, and Tᵢⱼ count ballots ranking both. Use the inherited symmetric frequency Sᵢⱼ = ½(Aᵢⱼ/Tᵢⱼ + Aⱼᵢ/Tⱼᵢ), with dissimilarity Dᵢⱼ = 1/√Sᵢⱼ. The inherited zero-frequency fallback is 2 divided by the smallest positive S. Fit one-dimensional nonmetric MDS using **20 outer runs × 8 starts**, 1,000-iteration limit and tolerance 10⁻⁶. Align reflected orders, select the modal order, average its coordinates and normalize to [0,1].

**Consistency.** A prefix is consistent if some positive-width interval of voter positions produces its strictly increasing distances to the explicitly ranked candidates. Unranked candidates impose no constraint. One- and two-name prefixes pass automatically; the three-/four-name group is reported separately.

**Randomized comparison.** Generate **49 new profiles**, exactly preserving first named choice × usable-prefix length counts while randomizing distinct ordered tails. Fit and score each randomized profile using its own full-profile axis and the same budget as the observed profile. These are full-profile consistency measures, not held-out predictive accuracy.'''),
code('''import run_mds,check_mds
from og_axis import summarize,matched_null,seed_for
# This FairVote-only notebook actually reruns the observed fit and every null fit.
with contextlib.redirect_stdout(io.StringIO()):
    mds=run_mds.main()
    check_mds.main()
verification=json.loads((ROOT/'mds/mds_verification.json').read_text())
assert mds['status']=='complete' and len(mds['null'])==49
assert mds['source_sha256']==provenance['inputs']['us_senate']['sha256']
assert verification['status']=='passed' and verification['axes_checked']==51
show.cards()
show.mds_plots()
show.consistency_table()
'''),
md('''The fresh FairVote-only results are **61.54% observed consistency versus 41.57% random** for **45,743 three-/four-name prefixes**, a **19.97-point difference**. Across all **243,006 nonempty prefixes**, consistency is **92.76% versus 89.00%**. There are **1,699 empty named prefixes**, retained separately rather than forced into a consistency denominator.

The candidate order is **Peltola → Daniel J. Sullivan Jr. → Heikes → Dan S. Sullivan**, up to reflection. This summarizes ranking structure, not a calibrated ideology scale or evidence of voter motives. The stronger observed-only 100×16 fitting-budget check produces the same consistency; it does not replace the matched 20×8 real-versus-random comparison. Independent strict-distance checks cover **3,264 rankings across all 51 axes**.'''),
code('''show.table(pd.read_csv(ROOT/'mds/candidate_axis.csv').round({'axis_position':6}),'Observed positions from FairVote’s Senate CSV')
show.table(pd.DataFrame([
 {'Check':'MDS inputs','Result':mds['source_filename']},
 {'Check':'Fresh randomized profiles, each with a fresh fit','Result':len(mds['null'])},
 {'Check':'Independent feasibility checks passed','Result':verification['independent_feasibility_rankings_checked']},
 {'Check':'Stronger observed fit: change in 3–4-name consistency','Result':f"{verification['change_three_plus_percentage_points']:.6f} pp"}
]),'Model verification')
'''),
md('''## 7 · Source policy, reproducibility and limits

- **Sole ballot sources:** the three original FairVote November 11 CSVs included unchanged under `inputs/`. SHA-256 hashes are recorded for each. No older ballot source is read, including to restore hidden overvote candidate identities.
- **Preservation:** all source columns, IDs, rank tokens, first-rank ambiguity annotations and first-rank overvote candidate lists remain in the linked records. A missing governor row remains missing. No irregular ballot is discarded.
- **Reference annotations:** candidate-party labels and stable internal candidate numbers are explicit analysis annotations, not fields supplied in FairVote’s CSVs and not voter registration. The published FairVote HTML is a validation reference only; it does not supply source counts.
- **Interpretation:** visible-name comparisons, hidden-identity sensitivity bounds and rule-based transfer availability are separate results. FairVote’s generic lower-overvote markers do not identify the candidate names hidden inside them.
- **Reproduction:** Run All rebuilds the linked inputs from the three CSVs, recomputes the descriptive tables and Sankey, and freshly fits the observed and all 49 randomized profiles. This run is recorded in `notebook_execution.json`. Historical versions remain preserved outside this active package.

The future-use preference is saved in `ALASKA_2026_ANALYSIS_SOURCE_POLICY.md`: FairVote’s supplied files are the exclusive ballot source for subsequent Alaska 2026 analyses unless you explicitly change that instruction.'''),
code('''expected_files={x['filename'] for x in provenance['inputs'].values()}
assert FAIRVOTE_INPUT_READS==expected_files,(FAIRVOTE_INPUT_READS,expected_files)
source_audit={'allowed_ballot_input_files':sorted(expected_files),'observed_ballot_input_reads':sorted(FAIRVOTE_INPUT_READS),'old_workspace_ballot_sources_blocked':True,'candidate_parties_are_reference_annotations':True,'all_analyses_freshly_recomputed':True}
(ROOT/'source_policy_audit.json').write_text(json.dumps(source_audit,indent=2))
show.table(pd.DataFrame([{'FairVote source':slug,'SHA-256':meta['sha256']} for slug,meta in provenance['inputs'].items()]),'Source identity')
print('All FairVote-only notebook checks passed. No older ballot source was accessed.')
''')]
nb=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'},'language_info':{'name':'python','version':'3.12.14'},'title':'Alaska 2026 Senate — FairVote Rerun','authors':[{'name':'Princeton research analysis'}]})
nbf.validate(nb);nbf.write(nb,R/'Alaska_2026_Senate_FairVote.ipynb')

# Ensure regenerated notebooks use the selected Alaska-rule headline definition.
import runpy
runpy.run_path(str(R/'apply_alaska_rule_revision.py'),run_name='__main__')
runpy.run_path(str(R/'repair_audit_findings.py'),run_name='__main__')
