"""Execute the notebook and save verifiable execution metadata."""
from pathlib import Path
import sys,json,datetime,hashlib,importlib.metadata
import nbformat
from nbclient import NotebookClient
R=Path(__file__).resolve().parent
p=R/'Alaska_2026_Senate_Rachel_FairVote.ipynb'
nb=nbformat.read(p,as_version=4);start=datetime.datetime.now(datetime.timezone.utc).isoformat()
try:
    NotebookClient(nb,timeout=1800,kernel_name=sys.argv[1] if len(sys.argv)>1 else 'python3',resources={'metadata':{'path':str(R)}}).execute()
finally:nbformat.write(nb,p)
nbformat.validate(nb)
code=[c for c in nb.cells if c.cell_type=='code']
assert all(c.execution_count is not None for c in code)
assert not any(o.output_type=='error' for c in code for o in c.outputs)
meta={'started_utc':start,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'execution':'Real Jupyter kernel; all descriptive tables, Sankey, observed MDS and all49 randomized MDS fits freshly recomputed from Rachel CSVs only','code_cells':len(code),'all_cells_executed':True,'error_outputs':0,'notebook_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'packages':{k:importlib.metadata.version(k) for k in ['numpy','scipy','scikit-learn','matplotlib','pandas','nbformat','nbclient','ipykernel']}}
(R/'notebook_execution.json').write_text(json.dumps(meta,indent=2));print(json.dumps(meta,indent=2))
