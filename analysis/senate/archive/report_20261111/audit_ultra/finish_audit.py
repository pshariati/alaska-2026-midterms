"""Verify the freshly executed notebook and consolidate independent audit evidence."""
from pathlib import Path
import base64,datetime,hashlib,json
import nbformat
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
HERE=Path(__file__).resolve().parent
def read(path):return json.loads((ROOT/path).read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    baseline=read('audit_ultra/pre_full_run_results.json')
    compared=[]
    for file,before in baseline.items():
        after=read(file)
        if file=='mds/mds_results.json':
            before.pop('seconds',None);after.pop('seconds',None)
        assert before==after,'Analytical results changed: '+file
        compared.append(file)
    descriptive=read('audit_ultra/descriptive/independent_descriptive_audit.json')
    flows=read('audit_ultra/flows/independent_flow_audit.json')
    mds=read('audit_ultra/mds/mds_audit.json')
    assert all(x['status']=='passed' for x in (descriptive,flows,mds))
    assert sum(x['nonzero_cells'] for x in descriptive['cross_tab_checks'])==208
    assert mds['observed_and_all49_null_fits_exactly_reproduced']
    assert mds['all49_null_profiles_independently_rederived']
    assert flows['all_node_link_path_and_CSV_counts_match']
    assert flows['independent_frozen_benchmark_matches']==54
    article=read('descriptive/descriptive_verification.json')
    assert article['article_comparison_matches']==article['article_comparison_numeric_cells']==9
    assert article['article_reference_sha256']==sha(ROOT/article['article_reference_file'])
    nbpath=ROOT/'Alaska_2026_Senate_Rachel_FairVote.ipynb'
    nb=nbformat.read(nbpath,as_version=4);nbformat.validate(nb)
    code=[c for c in nb.cells if c.cell_type=='code']
    assert len(code)==11 and [c.execution_count for c in code]==list(range(1,12))
    assert not any(o.output_type=='error' for c in code for o in c.outputs)
    assert any('usable_verification=verify_usable_preferences.main()' in c.source for c in code)
    assert any('benchmark_validation=validate_all_contest_benchmarks.main()' in c.source for c in code)
    metadata=read('notebook_execution.json')
    assert metadata['all_cells_executed'] and metadata['error_outputs']==0
    assert metadata['notebook_sha256']==sha(nbpath)
    policy=read('source_policy_audit.json')
    assert policy['alaska_prefix_verifier_executed']
    assert policy['all54_reference_cells_checked_in_Run_All']
    assert policy['observed_ballot_input_reads']==policy['allowed_ballot_input_files']
    provenance=read('descriptive/source_provenance.json')
    for race,item in provenance['inputs'].items():
        assert item['sha256']==sha(ROOT/'inputs'/item['filename'])
        assert item['sha256']==descriptive['sole_ballot_sources'][race]['sha256']
    image_hashes=[];table_count=0
    for cell in code:
        for output in cell.outputs:
            data=output.get('data',{})
            if 'image/png' in data:image_hashes.append(hashlib.sha256(base64.b64decode(data['image/png'])).hexdigest())
            table_count+=len(BeautifulSoup(data.get('text/html',''),'html.parser').find_all('table'))
    expected_images=[ROOT/'figures/cross_race_party.png',ROOT/'flows/senate_sankey.png',ROOT/'figures/senate_candidate_axis.png',ROOT/'figures/real_vs_random.png']
    assert image_hashes==[sha(p) for p in expected_images]
    assert table_count==19
    html=ROOT/'Alaska_2026_Senate_Rachel_FairVote_Readable.html'
    soup=BeautifulSoup(html.read_text(),'html.parser')
    assert len(soup.select('table'))==table_count
    assert len(soup.select('img[src^="data:image/png;base64,"]'))==4
    q1=next(c for c in code if c.source.startswith('show.preference_table()'))
    texts=[BeautifulSoup(o.get('data',{}).get('text/html',''),'html.parser').get_text(' ',strip=True) for o in q1.outputs]
    for number in ['568','423','765','481','1,703']:assert number in texts[0]
    scope=read('references/official_scope_comparison.json')
    assert all(row['official_minus_Rachel']==6383 for row in scope['comparisons'])
    result={
        'status':'passed','completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'source_policy':'Rachel CSVs only; archived public aggregates used only as validation references',
        'fresh_Run_All_results_reproduced':True,'fresh_Run_All_code_cells':11,
        'fresh_Run_All_error_outputs':0,'analytical_results_compared_without_runtime_timing':compared,
        'independent_original_contest_records_verified':sum(descriptive['source_rows_preserved_in_linked_records'].values()),
        'independent_nonzero_cross_tab_cells_verified':208,
        'independent_sankey_nodes_links_paths':[18,24,24],
        'independent_observed_and_49_null_fits_exactly_reproduced':True,
        'independent_null_profiles_and_fixed_first_choice_by_length_margins_verified':True,
        'archived_Nov11_RCVis_numeric_cells_matched':54,
        'archived_Nov12_article_Nov11_CVR_subgroup_cells_matched':9,
        'source_CSV_hashes_unchanged':True,
        'notebook_embedded_tables':table_count,'notebook_embedded_figures_verified_against_files':4,
        'notebook_sha256':sha(nbpath),'html_sha256':sha(html),
        'numerical_corrections_needed':False,
        'repairs':['Run All now executes the independent Alaska-prefix check and all54 external round-table checks.','Reference subgroup figures now parsed from authenticated archived article HTML rather than hardcoded constants.','Added full data-quality and original-versus-usable rank-length appendix.','Clarified same-version FairVote references, official coverage gap, residual governor group and affiliation labels.','Clarified49-draw Monte Carlo precision and supported Python version.','Removed obsolete dependence on byte-identical timing-containing model files from a ballot-rule check.'],
        'limits':['Rachel11/11scanned records are not every official ballot or certified results.','Ancillary ambiguity fields are preserved; ballot-image adjudication cannot be independently verified here.','Descriptive cohorts use explicitly labeled literal rank1, with structural-first-choice sensitivity separate.','MDS is full-profile ranked-only structural consistency; one/two-name ballots pass automatically.','49null draws estimate the random mean; MCSE about0.625percentagepoints for3+; no predictive or ideological claim.']}
    (HERE/'final_audit.json').write_text(json.dumps(result,indent=2))
    (HERE/'AUDIT_REPORT.txt').write_text('''FULL INDEPENDENT AUDIT — RACHEL-ONLY ALASKA NOTEBOOK

No numerical correction was needed to the Alaska-rule results delivered before
this audit. A fresh real Jupyter Run All executed all 11 code cells with zero
errors, rebuilding all descriptive data, all flows, the observed MDS fit, all 49
randomized fits and the stronger observed-fit check. Numerical results reproduced
exactly; the model's elapsed runtime was excluded from that equality test.

Independent checks (separate source implementations, not just rerunning producer):
- 733,985 original contest records, all 15 columns, every linked ID and prefix.
- All 208 nonzero cross-tab cells, percentages and full-cohort denominators.
- All 18 Sankey nodes, 24 links and 24 complete paths, with conserved ballots.
- Exact model profile, adjacency/co-ranking dissimilarities, observed fit, all49
  null profiles, fits and scores; fixed first-choice by length margins verified.
- 54 frozen preliminary Nov11 RCVis cells; nine actual cells parsed from the
  authenticated article updated Nov12 using the Nov11 CVR.
- Source hashes unchanged; all19embedded tables and4figures checked.

Repairs made:
1. Connected the countable-prefix verifier to Run All; made the verifier robust
   to ordinary model timing changes. All54benchmark checks now run in Run All.
2. Replaced embedded article-reference constants with parsing of archived HTML,
   verified its fetch hash, and clearly separated this snapshot from the live
   article, which subsequently changed to newer data.
3. Added full source quality counts and original/usable length definitions;
   clarified residual governor categories and candidate affiliation references.
4. Stated the supported Python version and Monte Carlo precision of49null draws.
5. Documented the official-summary coverage difference without imputing ballots.

Confirmed main results:
- Same3940literal-rank1Daniel ballots:568Peltola-above/423Dan-above with both
  finalists countable;765Peltola-only/481Dan-only/1703neither countable.
- Senate final replay:119933Peltola/119223Dan/5549inactive.
- MDS3–4named preferences:61.5351%observed vs41.5687%random mean, +19.9664pp.

Data and validation limits:
The Rachel files contain244705Senate/House records and244575governor records.
They are6383records short of the contemporaneous broader official summary in
each race. Exact match to frozen FairVote round tables is not equality to every
official ballot, later data updates or certified results. DOE excludes hand-count-
only ballots from CVR; these aggregates do not establish every reason for the gap.
All130governor-file absences remain absences; no ID collisions or disagreements
in7shared metadata fields were found. Original ambiguity annotations are retained,
but ballot images/adjudication history are unavailable for independent adjudication.

There are976Senate ballots containing an overvote token, not five (1070overvote
cells;330rank1overvotes and687rows with lower overvotes overlap). The main Daniel
cohort has26lower-overvote ballots. A small change in a comparison is not a count
of all overvotes. Flags overlap. A one-cell original bullet and a one-usable-choice
ballot are distinct; all definitions and distributions are supplied.

The 169-ballot residual governor group is126blank-first/39write-in/3overvote/
1absent, despite the historical article's blanket 'blank' label. Party refers to
candidate/ticket reference affiliations, not voter registration. Daniel has no
affiliation printed on the sampled general ballot; the general list says Undeclared.

MDS fits and scores the full profile and constrains only explicitly ranked names.
One-/two-name prefixes pass automatically. Overall consistency is therefore not
an informative stand-alone percentage; the3–4name group is shown separately.
The random mean's Monte Carlo SE is0.625percentagepoints with49draws. These are
descriptive ranking-structure measures, not predictive accuracy or ideology scales.

See the scoped independent scripts/reports under descriptive/, flows/ and mds/,
plus final_audit.json, notebook_execution.json and the archived reference provenance.
''')
    print(json.dumps({k:v for k,v in result.items() if k not in ['repairs','limits','analytical_results_compared_without_runtime_timing']},indent=2))

if __name__=='__main__':main()
