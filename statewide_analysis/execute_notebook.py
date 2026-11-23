"""Execute the complete follow-up in a real Jupyter kernel and record provenance."""
from pathlib import Path
import sys,json,hashlib,datetime,importlib.metadata
import nbformat
from nbclient import NotebookClient
ROOT=Path(__file__).resolve().parent
path=ROOT/'Alaska_2026_Statewide_Analysis.ipynb'
nb=nbformat.read(path,as_version=4)
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
try:
 NotebookClient(nb,timeout=1800,kernel_name=sys.argv[1] if len(sys.argv)>1 else 'python3',
  resources={'metadata':{'path':str(ROOT)}}).execute()
finally:nbformat.write(nb,path)
nbformat.validate(nb)
code=[cell for cell in nb.cells if cell.cell_type=='code']
assert all(cell.execution_count is not None for cell in code)
assert not any(o.output_type=='error' for cell in code for o in cell.outputs)
source_audit=json.loads((ROOT/'validation/notebook_source_audit.json').read_text())
record={'started_utc':start,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'execution':'Real Jupyter Run All. Completed descriptive and Sankey results revalidated from Rachel CSVs; unchanged audited spatial fits reused unless the notebook explicitly requests refitting. Voter-distribution pointsets and densities, confusion patterns and counterfactuals rebuilt. Hafner analysis freshly computed and independently audited. Source-profile and source-hash verification retained.',
 'Governor_and_House_spatial_models_refitted_in_this_run':source_audit['new_Governor_House_models_refitted'],
 'unchanged_audited_spatial_models_reused':source_audit['unchanged_audited_spatial_models_reused'],
 'hafner_analysis_recomputed':source_audit['hafner_analysis_recomputed'],
 'independent_hafner_audit':source_audit['independent_hafner_audit'],
 'both_finalists_routes_independently_verified':source_audit['both_finalists_routes_independently_verified'],
 'hafner_geography_recomputed_and_reconciled':source_audit['hafner_geography_recomputed_and_reconciled'],
 'code_cells':len(code),'all_cells_executed':True,'error_outputs':0,
 'notebook_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
 'packages':{name:importlib.metadata.version(name) for name in ['numpy','scipy','scikit-learn','matplotlib','pandas','Pillow','nbformat','nbclient','ipykernel','nbconvert']}}
(ROOT/'validation/notebook_execution.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record,indent=2))
