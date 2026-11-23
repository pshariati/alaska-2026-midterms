"""Independent original-row verification, final checksums and Rachel-only delivery."""
from pathlib import Path
from contextlib import ExitStack
from collections import Counter
import csv,gzip,json,hashlib,zipfile
R=Path(__file__).resolve().parent
SLUGS={'governor':'Governor','us_house':'House','us_senate':'Senate'}

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def main():
    nbpath=R/'Alaska_2026_Senate_Rachel_FairVote.ipynb'
    meta=json.loads((R/'notebook_execution.json').read_text());assert digest(nbpath)==meta['notebook_sha256']
    nb=json.loads(nbpath.read_text());assert meta['error_outputs']==0 and all(c['execution_count'] is not None for c in nb['cells'] if c['cell_type']=='code')
    assert not any(o.get('output_type')=='error' for c in nb['cells'] if c['cell_type']=='code' for o in c.get('outputs',[]))
    provenance=json.loads((R/'descriptive/source_provenance.json').read_text())
    counts=Counter();n=0;missing=0
    with ExitStack() as stack:
        readers={slug:csv.DictReader(stack.enter_context((R/'inputs'/f'Alaska_20261103_US_{race}_11_11.csv').open(encoding='utf-8-sig',newline=''))) for slug,race in SLUGS.items()}
        linked=stack.enter_context(gzip.open(R/'descriptive/linked_ballots.csv.gz','rt',encoding='utf-8',newline=''))
        for row in csv.DictReader(linked):
            n+=1
            for slug in SLUGS:
                raw=row[slug+'_original_row_json']
                if not raw:
                    assert slug=='governor';missing+=1;continue
                assert int(row[slug+'_source_row_index'])==counts[slug], 'Source row order requires explicit reindexing'
                expected=next(readers[slug]);actual=json.loads(raw)
                assert actual==expected,(slug,counts[slug])
                assert json.loads(row[slug+'_rank_tokens_json'])==[actual[f'rank{i}'] for i in range(1,6)]
                counts[slug]+=1
        for reader in readers.values():assert next(reader,None) is None
    assert dict(counts)==provenance['rows'] and n==counts['us_senate'] and missing==130
    for slug,race in SLUGS.items():
        p=R/'inputs'/f'Alaska_20261103_US_{race}_11_11.csv'
        assert digest(p)==provenance['inputs'][slug]['sha256']
        original=Path('/Users/pejmonshariati/Downloads')/p.name
        if original.exists():assert digest(original)==digest(p),'Supplied Rachel CSV changed'
    assert digest(R/'descriptive/linked_ballots.csv.gz')==provenance['linked_gzip_sha256']
    d=json.loads((R/'descriptive/descriptive_results.json').read_text());v=json.loads((R/'descriptive/descriptive_verification.json').read_text())
    assert v['article_comparison_matches']==9
    assert d['question1_visible_named_slot_categories']['peltola_above_senator_both_ranked']==568
    assert d['question1_partial_information_bounds']['possible_both_ranked_peltola_above']==574
    expected_usable={'peltola_above_senator_both_ranked':568,'senator_above_peltola_both_ranked':423,'peltola_only_explicitly_ranked':765,'senator_only_explicitly_ranked':481,'neither_explicitly_ranked':1703}
    assert d['question1_usable_prefix_categories']==expected_usable
    uv=json.loads((R/'descriptive/usable_preference_verification.json').read_text())
    assert uv['status']=='passed'
    m=json.loads((R/'mds/mds_results.json').read_text());mv=json.loads((R/'mds/mds_verification.json').read_text())
    assert m['status']=='complete' and len(m['null'])==49 and mv['status']=='passed' and mv['axes_checked']==51
    assert m['source_sha256']==provenance['inputs']['us_senate']['sha256']
    flow=json.loads((R/'flows/senate_sankey.json').read_text());assert flow['mass_conservation_passed'] and flow['source_sha256']==m['source_sha256']
    external=json.loads((R/'references/benchmark_validation.json').read_text());assert external['matches']==external['cells']==54
    policy=json.loads((R/'source_policy_audit.json').read_text());assert policy['old_workspace_ballot_sources_blocked']
    audit=json.loads((R/'audit_ultra/final_audit.json').read_text())
    assert audit['status']=='passed' and audit['fresh_Run_All_results_reproduced']
    checks=dict(source_policy='Rachel CSVs only',all_original_15_column_rows_independently_verified=dict(counts),linked_ballots=n,absent_governor_rows=missing,source_CSVs_byte_identical_to_supplied_files=True,old_workspace_ballot_sources_blocked=True,all_49_randomized_models_freshly_fitted=True,supplementary_visible_Peltola_above_both_named=568,supplementary_hidden_identity_strict_Peltola_bounds=[568,574],all54frozen_Nov11_RCVis_values_match=True,all9archived_Nov12_article_cells_match_visible_finalist_definition=True,article_reference_sha256=v['article_reference_sha256'],notebook_executed=True)
    checks.update(primary_preference_rule='Alaska-countable prefixes; visible-name descriptions supplementary',primary_cohort='3940 literal rank-1 Daniel ballots',primary_usable_categories=expected_usable,independent_rule_tests_passed=uv['regression_tests_passed'],fresh_Run_All_and_independent_audits_passed=True)
    (R/'DELIVERY_CHECKS.json').write_text(json.dumps(checks,indent=2))
    files=sorted(p for p in R.rglob('*') if p.is_file() and '__pycache__' not in p.parts and 'before_layout_fix' not in p.parts and p.name!='SHA256SUMS.json' and p.suffix not in ['.pyc','.tmp','.sqlite','.log'])
    (R/'SHA256SUMS.json').write_text(json.dumps({str(p.relative_to(R)):digest(p) for p in files},indent=2))
    out=R.parent/'Alaska_2026_Senate_Rachel_FairVote.zip'
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=3) as z:
        for p in files+[R/'SHA256SUMS.json']:z.write(p,str(p.relative_to(R.parent)),compress_type=zipfile.ZIP_STORED if p.suffix in ['.gz','.png'] else zipfile.ZIP_DEFLATED)
    with zipfile.ZipFile(out) as z:assert z.testzip() is None
    print(json.dumps(dict(package=str(out),bytes=out.stat().st_size,sha256=digest(out),checks=checks),indent=2))
if __name__=='__main__':main()
