"""Apply reproducibility and documentation repairs identified in the full audit."""
from pathlib import Path
import nbformat

ROOT=Path(__file__).resolve().parent
path=ROOT/'Alaska_2026_Senate_FairVote.ipynb'
nb=nbformat.read(path,as_version=4)
for cell in nb.cells:
    source=cell.source
    if cell.cell_type=='code' and source.startswith('import descriptive_analysis'):
        if 'import verify_usable_preferences' not in source:
            source=source.replace('    descriptive_verification=verify_fairvote.main()',
                '    descriptive_verification=verify_fairvote.main()\n    import verify_usable_preferences\n    usable_verification=verify_usable_preferences.main()')
        assert 'usable_verification=verify_usable_preferences.main()' in source
    elif cell.cell_type=='code' and source.startswith('import build_flows'):
        source=source.replace('import build_flows\n','import build_flows,validate_all_contest_benchmarks\n')
        source=source.replace('with contextlib.redirect_stdout(io.StringIO()):flow=build_flows.build()',
            "with contextlib.redirect_stdout(io.StringIO()):\n    flow=build_flows.build()\n    benchmark_validation=validate_all_contest_benchmarks.main()\nassert benchmark_validation['matches']==benchmark_validation['cells']==54")
    elif cell.cell_type=='markdown' and source.startswith('## Supplementary audit'):
        source=source.replace('FairVote’s visible rank columns reproduce the FairVote article’s Daniel subgroup totals exactly',
            'FairVote’s visible rank columns reproduce the Daniel subgroup totals in the **archived FairVote article updated November 12, using the November 11 CVR**, exactly')
        if 'broader residual category' not in source:
            source+='\n\nThe article labels its residual governor group “blank.” Our matching **broader residual category** has **126 blank first ranks, 39 write-ins, 3 overvotes, and 1 absent governor row**. We preserve that distinction. The archived article and retrieval record are included; its subsequently updated live version uses newer data and is not the benchmark here.'
    elif cell.cell_type=='code' and "'All nine FairVote article subgroup cells reproduced" in source:
        source=source.replace('All nine FairVote article subgroup cells reproduced by the visible-finalist definition',
            'Archived November 12 article / November 11 CVR: nine subgroup cells, visible-name definition')
    elif cell.cell_type=='markdown' and source.startswith('## 2 · Governor'):
        source=source.replace('Daniel J. has no listed affiliation.',
            'Daniel J. has no affiliation printed on the sampled general-election ballot (the official candidate list says Undeclared).')
    elif cell.cell_type=='markdown' and source.startswith('The fresh FairVote-only results'):
        if 'Monte Carlo' not in source:
            source+='\n\nThe random mean is an estimate from **49 simulations**. Its **Monte Carlo standard error is about 0.62 percentage points** for the three-/four-name group; reporting 41.57% identifies this run’s mean, rather than that degree of population precision.'
    elif cell.cell_type=='markdown' and source.startswith('## Supplemental validation'):
        source='''## Supplemental validation · all three FairVote contests

Run All reconstructs four stages directly from each FairVote CSV and compares them with the **frozen FairVote-linked RCVis pages explicitly labeled preliminary November 11**. All **54 available numeric candidate/inactive cells match**, with zero mismatches. Every source ballot is retained at each stage; matching the published newly-inactive series requires subtracting the initial inactive baseline only for that reference comparison.

These archived benchmarks are different from the subsequently updated live article and from certified official results. Article comparisons refer specifically to the archived article updated **November 12, 5:30 a.m. Alaska time**, using the **November 11, 6:34 p.m. CVR**. Its nine subgroup cells are the separate supplementary visible-name comparison, not legal transfer counts. The article HTML, fetch record, reference hashes, source hashes, and all 54 comparisons are included in the package.

A separate archived official first-choice summary printed **November 11 at 5:47:54 p.m.** reports **251,088 Senate/House ballots and 250,958 governor ballots**, versus FairVote’s **244,705 and 244,575** records: **6,383 fewer records in each contest**. This is a coverage comparison, not equality to official totals. DOE states its CVR excludes hand-count-only ballots; the aggregate gap alone cannot identify the exact source of every missing record. No absent votes are imputed. This comparison is reproducible with `python3 flows/validate_official_scope.py` against the preserved report.

Alaska’s overvote/skip interpretation follows the [Division of Elections’ 2026 guidance](https://www.elections.alaska.gov/election-results/e/?id=26genr). Matching these preliminary external tables does not independently verify ballot-image adjudication or establish that these CSVs cover the final certified election.'''
    elif cell.cell_type=='code' and source.startswith('expected_files='):
        source=source.replace("'all_analyses_freshly_recomputed':True", "'all_analyses_freshly_recomputed':True,'alaska_prefix_verifier_executed':usable_verification['status']=='passed','all54_reference_cells_checked_in_Run_All':benchmark_validation['matches']==54")
    cell.source=source

nb.cells[0].source=nb.cells[0].source.replace(
    'A supplementary audit reproduces the nine FairVote article subgroup cells using a different visible-name definition; those are not the headline countable-preference results.',
    'The supplementary visible-name audit matches nine subgroup cells in the archived November 12 article using November 11 data; these are distinct from the headline countable-preference results.')

if not any(c.metadata.get('audit_insert')=='quality-heading' for c in nb.cells):
    index=next(i for i,c in enumerate(nb.cells) if c.cell_type=='code' and c.source.startswith('import descriptive_analysis'))+1
    heading=nbformat.v4.new_markdown_cell('''### Data quality and original rankings

The full audit independently reconstructs every original source row, normalized ID, countable prefix and cross-office table. The original CSVs and all 15 supplied columns remain unchanged. The checks also cover first-rank ambiguity annotations; those annotations are retained without overriding FairVote’s rank cells or pretending to re-adjudicate ballot images.

The flags below overlap. “One named cell” means exactly one visibly named cell and no overvote anywhere, including write-in as a name. It differs from one usable preference after counting barriers. Raw named-cell lengths count repeat names and names below barriers; usable named lengths collapse repeats and exclude generic write-ins only after applying the barriers.''',metadata={'presentation_group':'data','audit_insert':'quality-heading'})
    code=nbformat.v4.new_code_cell('''import importlib.util
quality_spec=importlib.util.spec_from_file_location('fairvote_quality_audit',ROOT/'audit_ultra/descriptive/independent_descriptive_audit.py')
quality_module=importlib.util.module_from_spec(quality_spec)
quality_spec.loader.exec_module(quality_module)
with contextlib.redirect_stdout(io.StringIO()):quality_module.main()
quality=json.loads((ROOT/'audit_ultra/descriptive/independent_descriptive_audit.json').read_text())
assert quality['status']=='passed'
quality_rows=[]
for race,label in [('governor','Governor'),('us_house','House'),('us_senate','Senate')]:
    q=quality['data_quality'][race]['counts']
    quality_rows.append({'Contest':label,'Rows':q['rows'],'One named cell, no overvote':q['exact_one_named_cell_no_overvote'],'Any overvote':q['any_overvote_token'],'Overvote at rank 1':q['literal_rank1_overvote'],'Internal skip':q['any_internal_skip'],'Repeated name':q['any_repeat_named_candidate']})
show.table(pd.DataFrame(quality_rows),'Full-source quality counts; overlapping flags')
senate_quality=quality['data_quality']['us_senate']
show.table(pd.DataFrame([{'Length':k,'Original named cells (includes write-in/repeats)':senate_quality['literal_named_cell_length_distribution'].get(str(k),0),'Usable distinct named choices (excludes write-in)':senate_quality['usable_prefix_length_excluding_writein_distribution'].get(str(k),0)} for k in range(6)]),'Senate rank lengths: original cells versus countable model input')
''',metadata={'presentation_group':'data','audit_insert':'quality-code','tags':['hide-input'],'jupyter':{'source_hidden':True,'outputs_hidden':True},'collapsed':True})
    nb.cells[index:index]=[heading,code]
nb.metadata['audit_revision']='Independent source reconstruction, authenticated same-version references, and full Run All verification'
nbformat.validate(nb);nbformat.write(nb,path)
print('Audit repairs applied; no source ballots or numerical analysis definitions changed.')
