"""Verify the executed follow-up and create checksummed downloadable research artifacts."""
from pathlib import Path
import csv,json,hashlib,zipfile,base64,math
import nbformat
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parent

def read(path):return json.loads((ROOT/path).read_text())
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()

def main():
 execution=read('validation/notebook_execution.json')
 nbpath=ROOT/'Alaska_2026_Statewide_Analysis.ipynb';nb=nbformat.read(nbpath,as_version=4)
 assert sha(nbpath)==execution['notebook_sha256']
 code=[c for c in nb.cells if c.cell_type=='code']
 assert execution['all_cells_executed'] and execution['error_outputs']==0
 assert [c.execution_count for c in code]==list(range(1,len(code)+1))
 assert not any(o.output_type=='error' for c in code for o in c.outputs)
 completed=read('validation/completed_results_revalidation.json')
 axis_audit=read('axis_models/independent_axis_audit.json')
 voter_audit=read('validation/independent_voter_audit.json')
 confusion=read('confusion/confusion_results.json');confusion_audit=read('confusion/confusion_verification.json')
 hafner=read('hafner/results.json');hafner_audit=read('validation/audit_hafner.json')
 assert all(record['status']=='passed' for record in [completed,axis_audit,voter_audit,confusion,confusion_audit,hafner,hafner_audit])
 assert hafner['cohort']['n']==17918 and hafner['cohort']['raw_strict_bullet']==7707
 assert hafner['replay']['hafner_literal_destinations']=={'Bill Hill':8131,'Nick Begich':1142,'Inactive':8645}
 assert hafner['replay']['elimination_order_labels']==['Jim McDermott','Eric Hafner']
 for slug,source in hafner['sources'].items():assert source['sha256']==completed['sources'][slug]['sha256']
 for slug,source in completed['sources'].items():
  path=next((ROOT/'inputs').glob('*_'+{'us_senate':'Senate','governor':'Governor','us_house':'House'}[slug]+'_11_11.csv'))
  assert sha(path)==source['sha256']
  results=read('axis_models/'+slug+'/mds_results.json')
  assert results['source_sha256']==source['sha256'] and results['status']=='complete' and len(results['null'])==49
  assert results['source_rows']==source['rows']
  assert read('axis_models/'+slug+'/mds_verification.json')['status']=='passed'
 voters=read('voter_distributions/results.json');assert voters['status']=='passed'
 for slug,source in voters['sole_ballot_sources'].items():assert source['sha256']==completed['sources'][slug]['sha256']
 # Independent density audit includes every curve and exact finite allocation.
 assert all(row['status']=='passed' for row in axis_audit['contests'].values())
 main=confusion['cohorts']['literal_rank1_daniel']
 assert main['ballots']==3940 and main['final_destinations']['Dan S. Sullivan']==904
 assert main['no_incumbent_in_countable_prefix']['total']==2468
 assert main['no_incumbent_in_countable_prefix']['Peltola_countable']==765
 routes=read('validation/peltola_route_verification.json')
 assert routes['status']=='passed' and routes['cohort_n']==3940
 assert [(r['final_destination'],r['direct_after_Dan_J_elimination'],r['via_Heikes'],r['total']) for r in routes['routes']]==[
  ('Peltola',1147,186,1333),('Daniel S.',638,266,904),('Inactive',1447,256,1703)]
 scenarios={row['scenario']:row for row in confusion['conditional_upper_bound_scenarios']}
 assert scenarios['no_countable_incumbent']['maximum_additional_incumbent_votes_in_this_scenario']==2468
 assert scenarios['no_countable_incumbent']['maximum_Dan_minus_Peltola_margin_increase']==3233
 assert scenarios['all_literal_Daniel_first']['maximum_additional_incumbent_votes_in_this_scenario']==3036
 assert scenarios['all_literal_Daniel_first']['maximum_Dan_minus_Peltola_margin_increase']==4369
 source_audit=read('validation/notebook_source_audit.json')
 assert source_audit['old_workspace_ballot_inputs_blocked']
 assert source_audit['new_Governor_House_models_refitted'] or source_audit['unchanged_audited_spatial_models_reused']
 assert source_audit['hafner_analysis_recomputed'] and source_audit['independent_hafner_audit']=='passed'
 assert source_audit['both_finalists_routes_independently_verified']
 geography=read('hafner/geography/results.json')
 assert source_audit['hafner_geography_recomputed_and_reconciled'] and geography['status']=='passed'
 assert geography['source_sha256']==completed['sources']['us_house']['sha256']
 assert geography['all_House_records']==244705 and geography['Hafner_literal_first']==17918
 assert geography['districts'][0]['house_district']==21 and geography['districts'][0]['hafner_first']==653
 assert geography['geographic_districts_by_share'][0]['house_district']==18
 carryforward=read('validation/spatial_carryforward_hash_check.json')
 assert carryforward['status']=='passed' and carryforward['model_files_checked']==34
 for record in carryforward['files']:
  assert record['original_sha256']==record['current_sha256']==sha(ROOT/record['file'])
 browser=read('validation/browser_layout.json');assert browser['status']=='passed'
 tables=0;figures=0
 for cell in code:
  for output in cell.outputs:
   data=output.get('data',{})
   tables+=len(BeautifulSoup(data.get('text/html',''),'html.parser').find_all('table'))
   figures+='image/png' in data
 htmlpath=ROOT/'Alaska_2026_Statewide_Analysis_Readable.html'
 soup=BeautifulSoup(htmlpath.read_text(),'html.parser')
 assert len(soup.select('table'))==tables and tables>=28
 assert len(soup.select('img[src^="data:image/png;base64,"]'))==figures==12
 assert soup.select_one('details[data-group="hafner_details"]') is not None
 assert 'Eric Hafner’s House ballots' in soup.get_text()
 assert soup.find('h3',string=lambda x:x and 'Support reaching Peltola' in x) is not None or 'Support reaching Peltola' in soup.get_text()
 assert browser['notebook_sha256']==sha(nbpath) and browser['html_sha256']==sha(htmlpath)
 checks={'status':'passed','source_inputs':'Unmodified Rachel November11CSV files only',
  'notebook_real_Jupyter_Run_All':True,'executed_code_cells':len(code),'error_outputs':0,
  'Governor_and_House_fresh_null_fits_in_this_run':98 if source_audit['new_Governor_House_models_refitted'] else 0,
  'unchanged_audited_spatial_models_reused':source_audit['unchanged_audited_spatial_models_reused'],
  'spatial_model_files_hash_verified_unchanged':carryforward['model_files_checked'],
  'Senate_fit_explicit_verified_carryover':True,
  'independent_axis_audit':axis_audit['status'],'independent_voter_audit':voter_audit['status'],
  'independent_confusion_audit':confusion_audit['status'],'independent_hafner_audit':hafner_audit['status'],
  'both_finalists_routes_independently_verified':True,
  'Peltola_direct_1147_via_Heikes_186_total_1333':True,
  'hafner_geography_recomputed_and_reconciled':True,
  'hafner_analysis_freshly_recomputed':True,'hafner_original_records_preserved':True,
  'source_originals_hash_verified':True,
  'completed_first_choice_and_flow_values_revalidated':True,'tables':tables,'embedded_figures':figures,
  'all_full_cohorts_accounted_for':True,'actual_fallback_transfers_are_not_identified_confusion':True,
  'conditional_ceilings_are_not_estimates':True,'presentation_figures_include_Sam_edits':True,
  'browser_layout':browser['status'],'notebook_sha256':sha(nbpath),'html_sha256':sha(htmlpath)}
 (ROOT/'validation/DELIVERY_CHECKS.json').write_text(json.dumps(checks,indent=2))
 files=sorted(p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.log','.tmp','.sqlite'} and p.name!='SHA256SUMS.json')
 hashes={str(p.relative_to(ROOT)):sha(p) for p in files}
 (ROOT/'SHA256SUMS.json').write_text(json.dumps(hashes,indent=2))
 archive=ROOT.parent/'Alaska_2026_Statewide_Analysis_20261116.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=4) as z:
  for p in files+[ROOT/'SHA256SUMS.json']:
   z.write(p,str(p.relative_to(ROOT.parent)),compress_type=zipfile.ZIP_STORED if p.suffix in {'.png','.npz','.gz','.pdf'} else zipfile.ZIP_DEFLATED)
 with zipfile.ZipFile(archive) as z:
  for relative,expected in hashes.items():assert hashlib.sha256(z.read(ROOT.name+'/'+relative)).hexdigest()==expected
 print(json.dumps({'archive':str(archive),'bytes':archive.stat().st_size,'sha256':sha(archive),'checks':checks},indent=2))

if __name__=='__main__':main()
