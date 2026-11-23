"""Build the complete presentation notebook for the combined statewide report."""
from pathlib import Path
import nbformat as nbf
from analysis.shared.paths import REPO_ROOT, REPORTING_ROOT, INPUTS_ROOT, model_dir, resolve_recorded_path
ROOT=REPO_ROOT

def md(text,group=None):
 return nbf.v4.new_markdown_cell(text,metadata={'presentation_group':group} if group else {})
def code(text,group=None):
 meta={'tags':['hide-input'],'jupyter':{'source_hidden':True}}
 if group:meta.update(presentation_group=group,collapsed=True)
 return nbf.v4.new_code_cell(text,metadata=meta)

cells=[
md('''<div class="sam-kicker">Alaska ranked-ballot analysis</div>
<div class="sam-title">Alaska 2026: voter distributions across three candidate axes</div>

**FairVote’s November 11 CSV snapshot · Alaska counting rules · original one-dimensional method**

**Historical saved fits:** the axes below were fitted with scikit-learn 1.6.1. Later releases corrected nonmetric-MDS behavior. No controlled corrected-solver Alaska comparison has been completed; matrix and gamma checks do not resolve this issue. See `docs/KNOWN_ISSUES.md`.

**Public checkout:** outputs are cleared. Full execution requires the pinned source CSVs and omitted generated intermediates; see `docs/REPRODUCIBILITY.md`. Race-specific `Overview.ipynb` notebooks read the committed saved aggregates without those inputs.

This notebook brings the completed descriptive results together with Governor/House candidate axes, Mahshad-style voter distributions, permutation-based confusion scenarios, and a dedicated analysis of **Eric Hafner’s House ballots in section 7**. It includes both presentation figures with Sam’s requested labels and stacking order.

- The completed Senate result is unchanged: **gamma is 92.76% across nonempty named prefixes, or 61.54% among three-/four-name prefixes**; the matched random means are **89.00%** and **41.57%**.
- New three-/four-name consistency is **57.23% Governor versus 50.51% random**, and **65.27% House versus 41.26% random**.
- In the hypothetical replay of **3,940 Dan J.–first ballots**, **1,333 reach Peltola (33.83%)**, **904 reach Daniel S. (22.94%)**, and **1,703 become inactive (43.22%)**. Peltola receives **1,147 directly after Dan J.’s elimination and 186 through Heikes**. Both finalists’ routes are shown explicitly in section 5; the rankings do not identify confusion.
- The **2,468** Daniel-first ballots with no countable incumbent preference include **765 with a countable Peltola preference** and **1,703 with neither finalist countable**. Treating every one as intended incumbent support is a strong conditional scenario, not an estimate of confusion.

<div class="sam-note"><b>Reading the voter curves:</b> rankings generally identify intervals, not unique voter locations. The curves use Mahshad’s allocation convention and show only placeable ballots. Singleton-pinning and fitting-budget sensitivities, full cohort coverage, and all exclusions are reported. The three elections have separate coordinate systems.</div>'''),
code('''from pathlib import Path
import sys,json,csv,hashlib,contextlib,io,os
import numpy as np
import pandas as pd
from IPython.display import display,HTML,Image
ROOT=next((p for p in [Path.cwd().resolve(),*Path.cwd().resolve().parents] if (p/'analysis/shared/paths.py').is_file()),None)
assert ROOT is not None, 'Open this notebook within the alaska-2026-midterms checkout.'
sys.path.insert(0,str(ROOT))
from analysis.shared.paths import INPUTS_ROOT, REPORTING_ROOT, model_dir
assert (INPUTS_ROOT/'Alaska_20261103_US_Senate_11_11.csv').is_file(), 'Supply the pinned November 11 inputs in data/nov11; see docs/DATA.md.'
FAIRVOTE_INPUT_READS=set()
def source_guard(event,args):
    if event!='open' or not args or not isinstance(args[0],(str,bytes,os.PathLike)):return
    try:p=Path(os.fsdecode(args[0])).resolve()
    except (ValueError,OSError):return
    mode=args[1] if len(args)>1 else None
    reading=not isinstance(mode,str) or 'r' in mode
    if ROOT.parent in p.parents and ROOT not in p.parents and p.suffix.lower() in {'.csv','.tsv','.gz','.zip','.json','.sqlite','.xlsx'} and reading:
        raise PermissionError('FairVote-only analysis: external workspace data access blocked: '+str(p))
    if ROOT/'data' in p.parents and INPUTS_ROOT not in p.parents and p.suffix.lower() in {'.csv','.tsv','.gz','.zip','.json','.sqlite','.xlsx'} and reading:
        raise PermissionError('FairVote-only analysis: external workspace data access blocked: '+str(p))
    if INPUTS_ROOT in p.parents and p.suffix.lower()=='.csv' and reading:FAIRVOTE_INPUT_READS.add(p.name)
sys.addaudithook(source_guard)
from analysis.reporting import display as show
from analysis.shared.data import RACES,profile,sha256
show.theme()
'''),
md('''## 1 · Completed descriptive questions

The earlier descriptive questions are retained and revalidated, rather than treated as new analyses. The main cohorts use **literal rank 1** in the Senate and in the Governor/House first-choice tables. They include **117,437 Peltola**, **115,849 incumbent Dan S. Sullivan**, **5,054 Heikes**, and **3,940 outsider Daniel J. Sullivan Jr.** ballots.

**568 Daniel-first ballots rank both finalists countably, with Peltola above Dan S. Sullivan (14.42%).** The reverse is **423 (10.74%)**. Keeping the original cohort fixed makes the comparison explicit. A ballot naming only Peltola in its countable portion is shown separately from a ballot ranking both finalists.'''),
code('''from analysis.cross_race.validation import verify_completed
with contextlib.redirect_stdout(io.StringIO()):completed_check=verify_completed.main()
assert completed_check['status']=='passed'
show.first_choice_comparison()
'''),
md('''### Governor and House first choices

Affiliation refers to the **chosen candidate or ticket**, not voter party registration. FairVote’s files contain no voter-registration party field. Original blank first ranks, overvotes, write-ins, and absent Governor rows remain in the cohort denominator. The Governor ticket labels include the Democrat/Nonpartisan Kreiss-Tomkins/Johnson ticket; House nonpartisan is Bill Hill.

The first figure presents the four cohorts equally spaced. The second places the same paired bars at their actual Senate MDS coordinates. Both include the presentation edits: **Governor first choice**, **House first choice**, **Senate 1st choice:**, and Libertarian below Republican in the House stacks.'''),
code('''from analysis.cross_race.first_choices.figures import build_vertical,build_axis
with contextlib.redirect_stdout(io.StringIO()):
    build_vertical.main()
    build_axis.main()
show.image('analysis/cross_race/first_choices/figures/Alaska_Governor_House_First_Choice_Presentation.png',width=1000)
show.image('analysis/cross_race/first_choices/figures/Alaska_Candidate_Axis_First_Choice_Presentation.png',width=1250)
'''),
md('''### Complete first-choice tables

Each cell is ballots and the percentage of the **full Senate first-choice cohort**. These tables retain all recorded categories, including Governor-file absences.''','full_tables'),
code("show.cross_table('governor')\nshow.cross_table('us_house')\nshow.cross_table('governor',party=True)\nshow.cross_table('us_house',party=True)",'full_tables'),
md('''## 2 · Senate Sankey and actual transfers

The completed Sankey retains **all 244,705 Senate records** through its four display stages: initial allocation, generic write-in exclusion, Daniel J. elimination, and Heikes elimination. It follows countable preferences. Candidate order and flow conservation have been rechecked from FairVote’s source rows.

Daniel’s **literal first-choice cohort is 3,940**. His **first-structurally-usable-choice cohort is 3,992**; after write-in transfers, his replay node is **4,055**. Those are different denominators. The diagram’s initial write-in stage is explanatory; unresolved generic write-ins are excluded from the four-candidate named model.

Final replay counts remain **119,933 Peltola**, **119,223 Dan S. Sullivan**, and **5,549 inactive**. There are **1,363 initially inactive**, so **4,186 become newly inactive** relative to the graphic’s initial stage. This is a preliminary snapshot replay, not a certified statewide result.'''),
code("show.image('analysis/senate/flows/senate_sankey.png',width=1250)"),
md('''## 3 · The original one-axis model in all three elections

Each election is fitted on its **full nonempty countable named profile** and scored on that profile. Only explicitly ranked candidates constrain a ballot; unranked candidates are not silently appended. One-/two-name prefixes pass automatically, so overall gamma and the more informative three-/four-name gamma are shown separately.

The Senate fit and its 49 randomized fits were already completed and independently audited; they are carried forward unchanged after verifying that the new package’s source profile matches exactly. Governor and House are newly fitted using the same **20 outer runs × 8 starts**, 1,000-iteration budget and 10⁻⁶ tolerance. Each of their **49 matched-tail randomized profiles is independently refitted and scored**, preserving first named choice × prefix length.

The displayed House axis is reflected for readability; raw coordinates remain saved. Reflection changes neither gamma nor interval feasibility. Separate normalization to [0,1] does **not** make the three axes a shared ideology scale.'''),
code('''from analysis.shared import fit_races as run_axes
from analysis.cross_race.validation.axes import audit_axes
# The unchanged, independently audited spatial fits are supplied with this notebook.
# Set True only to repeat the expensive Governor/House observed and 98 null fits.
REFIT_NEW_AXES=False
if REFIT_NEW_AXES:
    with contextlib.redirect_stdout(io.StringIO()):
        newly_fitted=run_axes.main()
        axis_audit=audit_axes.main()
else:
    axis_audit=show.load('analysis/cross_race/validation/axes/independent_axis_audit.json')
assert axis_audit['status']=='passed'
senate_profile,senate_source=profile('us_senate')
saved=show.load('analysis/senate/candidate_axis/profile.json')
assert senate_profile=={tuple(row['ranking']):row['count'] for row in saved['ballots']}
assert senate_source['source_sha256']==show.load('analysis/senate/candidate_axis/mds_results.json')['source_sha256']
show.axis_summary()
show.plot_axes()
'''),
md('''## 4 · Voter distributions on the candidate axes

**Mahshad’s plotting convention.** For a compatible multi-name ranking, intersect the ranked-pair distance constraints to obtain a possible interval on the candidate axis. A pattern occurring *n* times contributes *n* equally spaced locations across that interval, as in the original `np.linspace` procedure. A one-name ballot is placed at that candidate’s position. These are **imputed locations**, not directly measured voter positions.

Each curve is a boundary-corrected Gaussian density of those finite allocated points. Cohorts share a bandwidth within each election, derived from all allocated points using their actual repeated-point count. Reflection at the 0/1 boundaries is a display convention. The exact point arrays, alternative group-specific bandwidths, numerical approximation checks, and interval bounds are included. This compares cohort distributions; the synthetic positions within a repeated ranking pattern are not uniquely assigned to individual ballot IDs, and no individual cross-election location correlation is estimated.

Missing contest rows, no usable named choice, and inconsistent rankings remain separately counted. An inconsistent ranking cannot be placed exactly on the fitted line and is excluded from these curves, rather than forced to a convenient location. Every displayed group’s curve integrates to one **among its plotted ballots**; full-cohort mass-scaled densities are also supplied.'''),
code('''from analysis.cross_race.voter_distributions import run_distributions
with contextlib.redirect_stdout(io.StringIO()):voter_results=run_distributions.main()
assert voter_results['status']=='passed'
show.image('analysis/cross_race/voter_distributions/all_voters_three_axes.png',width=1150)
'''),
md('''### Peltola and challenger Sullivan across the three elections

Here “Peltola voters” always means the **same 117,437 literal Senate Peltola-first ballots**. “Challenger Sullivan” means the **same 3,940 literal Senate Daniel J. Sullivan Jr.-first ballots**, not incumbent Dan S. Sullivan. Their Governor and House rankings are linked by normalized ballot ID.

Under the main allocation convention, Peltola’s group has imputed medians at **Peltola on the Senate line**, **Kreiss-Tomkins on the Governor line**, and **Hill on the House line**. Daniel’s group is spread much more broadly across the Governor and House lines. These summaries are conditional on placement and strongly influenced by the one-name allocation convention; they are not measurements on a common political scale.'''),
code("show.image('analysis/cross_race/voter_distributions/peltola_challenger_across_three_axes.png',width=1250)\nshow.distribution_coverage(focal=True)\nshow.focal_position_summaries()"),
md('''### All four Senate first-choice groups on each election’s line

Each panel uses the named candidates of that election. The colored curves refer to Senate first-choice groups throughout. Comparisons within a panel share a smoothing bandwidth. The coverage figure accounts for each group’s full cohort, including ballots absent from a particular contest file.'''),
code("show.image('analysis/cross_race/voter_distributions/senate_groups_across_three_axes.png',width=1150)\nshow.image('analysis/cross_race/voter_distributions/voter_distribution_coverage.png',width=1150)"),
md('''### Placement and fitting sensitivities

A one-name ranking alone imposes no ranked-pair restriction: every point in [0,1] is feasible under this consistency definition. Pinning it at the candidate is Mahshad’s convention. The singleton-uniform sensitivity shows how the curves change if those ballots are spread across their full feasible interval instead. Large changes reveal assumption dependence.

A stronger **100 × 16** observed fitting budget preserves each election’s candidate order and gamma but shifts some coordinates. The saved fitting-budget sensitivity recalculates all group placements under those stronger-fit maps; the main plots retain the prespecified 20 × 8 maps. Moving point masses can produce large empirical-CDF differences, so those differences are not an ideological-location error measure.''','sensitivities'),
code('''show.image('analysis/cross_race/voter_distributions/singleton_allocation_sensitivity.png',width=1150)
geometry=pd.read_csv(ROOT/'analysis/cross_race/voter_distributions/axis_geometry_sensitivity.csv')
show.table(geometry[['contest','group_name','main_plotted_n','strong_plotted_n','main_imputed_mean','strong_imputed_mean','main_imputed_median','strong_imputed_median']].round(4),'Main versus stronger-fit geometry; allocation-dependent coordinates')
show.distribution_coverage()
''','sensitivities'),
md('''## 5 · Where do Dan J.–first ballots go?

### Support reaching Daniel S., the incumbent

Among the same **3,940 ballots that recorded Dan J. first**, **904 would reach Daniel S. (22.94%)** in our hypothetical replay: **638 directly after Dan J.’s elimination**, and **266 through Heikes**. These are fallback preferences recorded on the ballots. The rankings do not establish that the original first choice was a name-confusion error.

Examples are `Dan J. → Daniel S.` and `Dan J. → Heikes → Daniel S.`. If a continuing Peltola appears before Daniel S., the ballot stays with Peltola; a lower Daniel S. ranking does not jump over her. Thus the **1,472 ballots with both Sullivans usable are not all incumbent transfers**: **568 put Peltola above Daniel S.**

On the separate **4,055-ballot Dan J. replay allocation**, **933** would eventually reach Daniel S. (**655 direct + 278 through Heikes**). That allocation includes incoming ballots from other first choices. **904** remains the answer for the original **3,940-ballot** cohort.'''),
code('''from analysis.senate.rankings import run_confusion,verify_confusion
with contextlib.redirect_stdout(io.StringIO()):
    confusion=run_confusion.main()
    confusion_audit=verify_confusion.main()
assert confusion['status']=='passed'
show.routes_and_omissions()
'''),
md('''### Support reaching Peltola

**Peltola would receive more of these Dan J.–first ballots than Daniel S. would:**

- **1,147** would transfer directly to Peltola after Dan J. is eliminated.
- **186** would first count for Heikes, then transfer to Peltola when Heikes is eliminated.
- **Total: 1,333 reach Peltola (33.83%)**, compared with **904 reaching Daniel S. (22.94%)**. Another **1,703 become inactive (43.22%)** because no usable preference remains for either finalist.

These are **hypothetical final destinations**, assuming Dan J. and then Heikes are eliminated while Peltola and Daniel S. remain. They use the same Alaska counting rules and the same **3,940 literal first-choice ballots** as the incumbent analysis, rather than the larger Sankey allocation.

The **1,333** comprise **568** ballots that validly rank both finalists with Peltola ahead, plus **765** with a usable Peltola preference and no usable Daniel S. preference. These are two separate categories. The transfer pattern documents Peltola’s recorded fallback support; it does not establish why voters chose Dan J. first.'''),
code('''from analysis.senate.rankings import verify_peltola_routes
with contextlib.redirect_stdout(io.StringIO()):peltola_route_audit=verify_peltola_routes.main()
assert peltola_route_audit['status']=='passed'
show.finalist_route_comparison()
'''),
md('''### Which permutations might reflect confusion?

An outsider-first ranking followed by the incumbent, or an outsider-first ranking omitting the incumbent, is **compatible with** a name-confusion explanation. Both can also be sincere preferences. Adjacent Sullivans, a Heikes intermediary, or an omitted finalist are observable pattern definitions; none identifies intent by itself.

The complete permutation table retains all 16 countable named patterns beginning with Daniel. Pattern sets overlap where stated. Counts of “could be confused” are ceilings within defined sets, not observed counts of confused people. A protest-vote interpretation is likewise not established by these ballots.'''),
md('''### All Dan J.–first permutations

These are countable unique-name permutations, with write-in removed only after applying overvote/skip barriers. Original five-cell rank strings and all annotations remain in the source files and detailed exports.''','permutations'),
code('show.permutation_table()','permutations'),
md('''## 6 · Possible lost support: omissions and conditional ceilings

**No countable incumbent preference:** **2,468** literal Daniel-first ballots, split into **765 with countable Peltola** and **1,703 with neither finalist countable**. This is the clean Alaska-rule answer for support unavailable to the incumbent.

**“Not ranked at all” needs a source qualification.** There are **2,462 with no explicit incumbent name in the five coded cells**. Of these, **2,441 have no overvote token** and **21 contain generic overvotes whose candidate membership is unknown**. Another **six visibly name the incumbent only beyond a counting barrier**. We do not fill hidden identities from the old CVR.

Within the 2,462 visibly-incumbent-absent ballots, **777 visibly name Peltola**, while **765 have Peltola in the countable portion**. Within the narrower 2,441 no-overvote ballots, **760 have countable Peltola** and **1,681 become inactive**. Original visible marks are used here only to distinguish what “not ranked anywhere” can mean; the main transfer counts use legal availability.

**Conditional ceiling:** assume every ballot in a chosen set intended incumbent Dan first, correct those ballots to him, and leave all other ballots fixed. For the 2,468 no-countable-incumbent set, the ceiling is **2,468 additional incumbent votes**. The Dan-minus-Peltola margin could increase by **3,233**: twice the 765 switches from Peltola, plus the 1,703 inactive recoveries. Actual confusion could be zero. These assumptions are stronger than anything the rankings establish.

The broader all-Daniel-first scenario has a ceiling of **3,036 additional incumbent votes** and **4,369 in margin change**, because 904 already reach the incumbent. These scenarios are **not added together**, do not estimate actual confusion, and do not bound every conceivable confusion mechanism in the election.'''),
code('show.upper_bounds()'),
md('''### Identified ballot examples

Sam’s “ballot #34” is treated as an illustration because no corresponding source ID was supplied. The examples below instead use actual anonymous FairVote ballot IDs and show their source rank cells and replay path. A source row index is explicitly zero-based; it is not a voter identity or a claim to have identified Sam’s #34.''','examples'),
code('''examples=pd.read_csv(ROOT/'analysis/senate/rankings/anonymous_example_ballots.csv').head(5)
show.table(examples[['illustration','source_ballotID','rank1','rank2','rank3','rank4','rank5','after_Daniel_elimination','after_Heikes_elimination']],'Actual source records illustrating the mechanisms')
''','examples'),
md('''## 8 · Sources, versioning and reproducibility

All ballot analyses use only the three unmodified FairVote **November 11** CSVs, placed locally under `data/nov11/` with exact hashes. This remains the selected input version even though later election data may exist. Every original rank cell and metadata column is preserved. Candidate IDs and affiliation labels are reference annotations, not fields invented as FairVote-supplied IDs or voter registration.

Alaska-countable prefixes keep earlier valid choices, stop before an overvote, cross one internal skipped rank, stop at two consecutive internal skips, and collapse repeat candidates. A generic write-in occupies its original rank while barriers are evaluated, then is excluded from the four-candidate models. The [Alaska Division of Elections](https://www.elections.alaska.gov/election-results/e/?id=26genr) documents these rules.

The source files have **244,705 Senate/House** rows and **244,575 Governor** rows; **130 Governor rows are absent** from the federal ID universe. These are scanned CVR records, not all statewide or certified ballots. The archived November 11 FairVote-linked round tables match all 54 available numeric cells; that validation does not turn the scanned snapshot into a certified tally. The older article’s visible-name subgroup comparison remains supplementary and does not enter these main results.

**Run All:** revalidates the completed descriptive/Sankey outputs from source, rebuilds both presentation figures, reconstructs voter placements and densities, recomputes confusion permutations/scenarios, and rebuilds the Hafner analysis with an independent source audit. By default, the unchanged, independently audited spatial fits are reused; set `REFIT_NEW_AXES=True` to repeat Governor/House observed and all 98 null fits. The completed Senate fit is explicitly carried forward and checked against the exact current source profile. Independent audit scripts and machine-readable tables are included. Python 3.11+ is required; the pinned execution environment uses Python 3.12.14.''','provenance'),
code('''assert FAIRVOTE_INPUT_READS=={meta['filename'] for meta in RACES.values()}
source_audit={'source_policy':'FairVote November11CSV inputs only','observed_input_files':sorted(FAIRVOTE_INPUT_READS),
 'old_workspace_ballot_inputs_blocked':True,'completed_results_revalidated':completed_check['status']=='passed',
 'new_Governor_House_models_refitted':REFIT_NEW_AXES,'Senate_model_carried_forward_with_exact_profile_verification':True,
 'unchanged_audited_spatial_models_reused':not REFIT_NEW_AXES,
 'hafner_analysis_recomputed':hafner_results['status']=='passed','independent_hafner_audit':hafner_audit['status'],
 'both_finalists_routes_independently_verified':peltola_route_audit['status']=='passed',
 'hafner_geography_recomputed_and_reconciled':hafner_geography_results['status']=='passed'}
(ROOT/'analysis/cross_race/validation/notebook_source_audit.json').write_text(json.dumps(source_audit,indent=2))
show.table([{'FairVote input':slug,'Rows':completed_check['sources'][slug]['rows'],'SHA-256':meta['sha256']} for slug,meta in RACES.items()],'Exact source versions')
print('All notebook analyses completed using FairVote’s selected source version.')
''','provenance')]

from analysis.reporting.hafner_section import notebook_cells as hafner_notebook_cells
insertion=next(i for i,cell in enumerate(cells) if cell.source.startswith('## 8 · Sources'))
cells[insertion:insertion]=hafner_notebook_cells()

def build_document():
 nb=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'},
 'language_info':{'name':'python','version':'3.12.14'},'title':'Alaska2026 — voter distributions and ranking scenarios',
 'authors':[{'name':'Princeton research analysis'}],'source_version':'FairVote November11CSV files only',
 'analysis_date':'2026-11-16','hafner_section_added':'2026-11-16'})
 nbf.validate(nb)
 return nb

if __name__=='__main__':
 path=REPORTING_ROOT/'Alaska_2026_Statewide_Analysis.ipynb';nbf.write(build_document(),path)
 print(path)
