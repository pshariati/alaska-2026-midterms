"""Notebook cells and presentation helpers for the focused Hafner analysis."""
from pathlib import Path
import json
import nbformat as nbf
import pandas as pd
from IPython.display import Markdown, display

ROOT = Path(__file__).resolve().parent


def notebook_cells():
    def md(source, group=None):
        return nbf.v4.new_markdown_cell(source, metadata={
            **({'presentation_group': group} if group else {}),
            'analysis_extension': 'hafner_20261116'})

    def code(source, group=None):
        return nbf.v4.new_code_cell(source, metadata={
            'tags': ['hide-input'], 'jupyter': {'source_hidden': True},
            **({'presentation_group': group} if group else {}),
            'analysis_extension': 'hafner_20261116'})

    return [
        md('''## 7 · Eric Hafner’s House ballots

**What did Hafner’s voters actually rank, and how did they vote in the other races?** This section uses only Rachel’s unchanged **November 11** files. The main group consists of ballots that **recorded Eric Hafner in House rank 1**. It does not assume that those voters were confused, uninformed, or voting insincerely.

**Background.** The [U.S. Department of Justice](https://www.justice.gov/usao-nj/pr/monmouth-county-man-sentenced-20-years-prison-making-threatening-communications-and) announced that Hafner was sentenced to **20 years in federal prison on December 7, 2023**, for threatening communications and false bomb threats. [Alaska’s News Source reported in June 2026](https://www.alaskasnewssource.com/2026/06/06/prisoner-his-mom-how-are-candidates-whove-never-visited-alaska-able-run-states-federal-seats/) that he had never visited Alaska and was serving his sentence in New York. The [official 2026 candidate list](https://www.elections.alaska.gov/election-candidates/?election=26genr) listed him as a registered Democrat. These are background annotations; the linked articles supply no ballot data.'''),
        code('''sys.path.insert(0,str(ROOT/'hafner'))
import run_hafner,audit_hafner
from hafner_notebook import show_summary,show_cross_election,show_details
with contextlib.redirect_stdout(io.StringIO()):
    hafner_results=run_hafner.main()
    hafner_audit=audit_hafner.main()
assert hafner_results['status']=='passed'
assert hafner_audit['status']=='passed'
show_summary(hafner_results)
'''),
        md('''### Backup rankings and hypothetical House destinations

The left panel shows the **next usable named preference** after Hafner. The right panel shows where the same ballots would end up in the **full-source House replay**.

**McDermott is eliminated before Hafner in this snapshot.** A ballot ranking `Hafner → McDermott → Hill` would therefore move **directly from Hafner to Hill** when Hafner is eliminated: McDermott is already out. A `Hafner → McDermott` ballot with no eligible later preference would become inactive. The listed backup order is not automatically the sequence of actual transfers.

“Inactive” means that no usable preference remains for either continuing finalist. Earlier valid votes still count in earlier rounds. These are hypothetical transfers in a dated snapshot, not official or final statewide results.'''),
        code("show.image('hafner/hafner_backup_choices_and_destinations.png',width=1150)"),
        md('''### The same voters in the Senate and governor races

These are **linked records from the same ballots**, joined by normalized ballot ID. They show literal first choices in the other contests. All four House first-choice groups are shown for comparison. Candidate affiliations describe the chosen candidates, not voters’ party registration. Missing governor records stay in the denominator.'''),
        code("show_cross_election(hafner_results)\nshow.image('hafner/hafner_cross_election_comparison.png',width=1150)"),
        md('''### Where did Hafner receive the most support?

Compare **the number of Hafner-first ballots** with **his share of all House records in an area**. A larger population can produce more votes without producing a higher share. The district chart combines all recorded voting modes; the geographic-precinct table is Election Day only in these files.

Area descriptions follow the source precinct labels and the [Division of Elections’ district references](https://www.elections.alaska.gov/research/district-maps/). The [District 18 precinct maps](https://www.elections.alaska.gov/doc/maps/2023-precincts/HD18_May2023Final_Maps.pdf) show Government Hill, JBER and North Muldoon. State House districts and administrative counting groups must not be treated as exact city boundaries.'''),
        code('''import hafner_geography
hafner_geography_results=hafner_geography.main()
assert hafner_geography_results['status']=='passed'
hafner_geography.show_geography(hafner_geography_results)
'''),
        md('''### What the ballots establish

Hafner-first voters overwhelmingly also chose Peltola for Senate and Kreiss-Tomkins/Johnson for governor, resembling the cross-race choices of Hill-first voters. At the same time, many Hafner-first ballots contain no usable backup for either House finalist. The tables distinguish strictly blank later ranks from repeats, write-ins, and preferences stopped by counting barriers.

This describes the recorded choices. Explaining **why** people selected Hafner would require evidence about what voters knew or intended, such as a voter survey. These records do not identify party-label voting, protest voting, confusion, awareness of his imprisonment, or the effect of campaign messages. A large tally alone does not establish that the tally is erroneous.

The full **16-row ranking distribution**, original-mark diagnostics, exact other-race counts, and denominator checks are in **“Eric Hafner: all rankings, original marks, and additional checks”** under **Methods, checks, and additional tables**. Machine-readable tables and a source-preserving cohort export are in the package’s `hafner/` folder.'''),
        md('''### Eric Hafner: full distributions and checks

All percentages below use the **17,918 literal Hafner-first ballots**, unless the table explicitly gives a different denominator. Generic write-ins retain their rank occupancy while the Alaska overvote/skipped-rank barriers are applied; only then are write-ins removed from the named-candidate sequences. Repeated names are collapsed. Original five-cell patterns and source annotations are preserved separately.

“Next usable named preference” describes the ranking after Hafner; the later replay allocation also depends on which candidates are still running. These definitions must not be interchanged. The 254 original five-cell patterns remain available in `hafner/hafner_raw_five_rank_patterns.csv`; the complete source rows are in `hafner/hafner_literal_first_ballots.csv.gz`.''', 'hafner_details'),
        code('show_details(hafner_results)\nhafner_geography.show_geography_details(hafner_geography_results)', 'hafner_details'),
    ]


def show_summary(result):
    import presentation as show
    q = result['cohort']
    n = q['n']
    dest = result['replay']['hafner_literal_destinations']
    p = lambda k: f'{100*k/n:.2f}%'
    display(Markdown(
        f"**{n:,} ballots recorded Hafner first:** "
        f"**{q['pct_of_all_house_records']:.2f}% of all {result['house_source_n']:,} House records** "
        f"in this file, or {q['pct_of_four_named_literal_first_choices']:.2f}% of literal "
        "first choices for the four named candidates. These are different denominators.\n\n"
        f"**{q['raw_strict_bullet']:,} ({p(q['raw_strict_bullet'])}) are strict bullet votes**, "
        "with all four later recorded ranks blank. "
        f"**{q['named_only']:,} ({p(q['named_only'])}) have only Hafner as a usable named preference**. "
        "That larger category also includes repeats, generic write-ins and choices beyond counting barriers.\n\n"
        f"In the hypothetical final round, **{dest['Bill Hill']:,} ({p(dest['Bill Hill'])}) "
        f"reach Hill**, **{dest['Nick Begich']:,} ({p(dest['Nick Begich'])}) reach Begich**, "
        f"and **{dest['Inactive']:,} ({p(dest['Inactive'])}) become inactive**."))
    rows = [{'Recorded House first choice': k, 'Ballots': f'{v:,}',
             'Share of all House records': f'{100*v/result["house_source_n"]:.2f}%'}
            for k, v in sorted(result['house_first_choices'].items(), key=lambda z: -z[1])]
    show.table(rows, 'House first-choice totals: all categories retained')


def show_cross_election(result):
    n = result['cohort']['n']
    p = result['cross_election']['us_senate']['label_counts']['Mary Peltola']
    k = result['cross_election']['governor']['label_counts']['Kreiss-Tomkins/Johnson']
    h = result['house_first_choices']['Bill Hill']
    hp = result['cross_election_all_House_first_groups']['us_senate']['Bill Hill']['Mary Peltola']
    hk = result['cross_election_all_House_first_groups']['governor']['Bill Hill']['Kreiss-Tomkins/Johnson']
    display(Markdown(
        f"Among Hafner-first ballots, **{p:,}/{n:,} ({100*p/n:.2f}%) put Peltola first** "
        f"for Senate, and **{k:,}/{n:,} ({100*k/n:.2f}%) put Kreiss-Tomkins/Johnson first** "
        "for governor.\n\n"
        f"For comparison, Hill-first ballots are **{100*hp/h:.2f}% Peltola-first** "
        f"and **{100*hk/h:.2f}% Kreiss-Tomkins/Johnson-first**. "
        f"**{result['joins']['governor']['hafner_missing_other_contest']:,} Hafner-first ballots "
        "have no linked governor record; these remain separately counted."))


def show_details(result):
    import presentation as show
    n = result['cohort']['n']
    q = result['cohort']
    def counts_table(mapping, title, category='Category'):
        show.table([{
            category: k, 'Ballots': f'{v:,}', 'Share of Hafner-first cohort': f'{100*v/n:.2f}%'}
            for k, v in mapping.items()], title)

    df = pd.read_csv(ROOT/'hafner/hafner_usable_permutations.csv')
    show.table(pd.DataFrame({
        'Usable named ranking': df.usable_named_ranking,
        'Ballots': df.ballots.map(lambda x: f'{x:,}'),
        'Share of Hafner-first cohort': df.pct.map(lambda x: f'{x:.2f}%'),
        'Hypothetical final destination': df.hypothetical_final_destination}),
        'All 16 Hafner-first usable named permutations')
    counts_table({str(k)+' usable named preference'+('' if str(k)=='1' else 's'):
                  q['usable_length_counts'].get(str(k), 0) for k in range(1,5)},
                 'Usable named rank lengths')
    counts_table(q['literal_rank2'], 'Original recorded rank 2, including repeats and irregular marks', 'Recorded rank 2')
    counts_table({('No usable named backup' if k=='Inactive' else k): v
                  for k,v in q['next_usable_named_choice'].items()},
                 'Next usable named preference after Hafner', 'Next usable named preference')
    labels = {
        'Hill_above_Begich_both_usable': 'Both usable: Hill above Begich',
        'Begich_above_Hill_both_usable': 'Both usable: Begich above Hill',
        'Hill_only_usable': 'Hill usable; Begich not usable',
        'Begich_only_usable': 'Begich usable; Hill not usable',
        'Neither_finalist_usable': 'Neither finalist usable'}
    counts_table({labels[k]: result['finalist_comparison'][k] for k in labels},
                 'Hill versus Begich in Hafner-first usable preferences')
    counts_table({
        'Strict bullet: all later recorded ranks blank': q['raw_strict_bullet'],
        'Only Hafner in usable named sequence': q['named_only'],
        'Any overvote token': q['any_overvote'],
        'First effective barrier is an overvote': q['barriers'].get('overvote', 0),
        'First effective barrier is two consecutive skips': q['barriers'].get('two_consecutive_skips', 0),
        'At least one internal skipped rank before a later mark': q['any_internal_skip_before_last_mark'],
        'Repeated named candidate in recorded ranks': q['any_repeated_named_candidate'],
        'Any generic write-in token': q['any_writein'],
        'Nonempty rank-1 ambiguity annotation (no identities imputed)': q['first_rank_ambiguous_annotation_nonempty']},
        'Original-mark diagnostics: overlapping categories, not a partition')
    for slug, title in [('us_senate', 'Senate'), ('governor', 'Governor')]:
        counts_table(dict(sorted(result['cross_election'][slug]['label_counts'].items(),key=lambda z:-z[1])),
                     title+' first choices among the same Hafner-first ballots', title+' first choice')
    show.table([{
        'Replay round': r['round'],
        'Nick Begich': f'{r["counts"].get("Begich, Nick",0):,}',
        'Bill Hill': f'{r["counts"].get("Hill, Bill",0):,}',
        'Eric Hafner': (f'{r["counts"]["Hafner, Eric"]:,}' if 'Hafner, Eric' in r['counts'] else 'Eliminated'),
        'Jim McDermott': (f'{r["counts"]["McDermott, James C. "+chr(34)+"Jim"+chr(34)]:,}'
                           if 'McDermott, James C. "Jim"' in r['counts'] else 'Eliminated'),
        'Inactive': f'{r["inactive"]:,}'} for r in result['replay']['rounds']],
        'Full-source hypothetical House count after generic write-in exclusion; every round totals 244,705')
    replay = result['replay']
    show.table([
        {'Definition': 'Literal recorded Hafner rank 1 (main cohort)', 'Ballots': f'{n:,}'},
        {'Definition': 'Hafner first structurally usable choice', 'Ballots': f'{replay["first_structurally_usable_Hafner_n"]:,}'},
        {'Definition': 'Hafner allocation after initial generic write-in exclusion', 'Ballots': f'{replay["Hafner_after_initial_generic_writein_exclusion_n"]:,}'},
        {'Definition': 'Hafner allocation after McDermott is eliminated', 'Ballots': f'{replay["actual_Hafner_elimination_node_n"]:,}'},
    ], 'Different Hafner populations: do not interchange these denominators')
    counts_table(replay['hafner_literal_destinations'], 'Main 17,918-ballot cohort: final replay destinations', 'Final destination')
    node_n = replay['actual_Hafner_elimination_node_n']
    show.table([{'Final destination': k, 'Ballots': f'{v:,}',
                 'Share of later Hafner allocation': f'{100*v/node_n:.2f}%'}
                for k,v in replay['actual_node_destinations'].items()],
               f'Later {node_n:,}-ballot Hafner allocation: includes incoming ballots from other first choices')
    display(Markdown(
        'Additional exports retain all 254 original rank patterns, the source-preserving '
        '17,918-row cohort, and descriptive precinct/counting-group summaries. '
        'Precinct fields include administrative labels such as early-voting groups; '
        'these summaries are not geographic anomaly tests. Source hashes, normalized-ID '
        'uniqueness, all 16 permutations, original marks, cross-race joins and full replay '
        'totals are independently checked by `validation/audit_hafner.py`.'))
