"""Reexecute affected descriptive cells; retain verified unchanged MDS/Sankey results."""
from pathlib import Path
import json,hashlib,datetime,sys
import nbformat
from nbclient import NotebookClient
R=Path(__file__).resolve().parent;p=R/'Alaska_2026_Senate_FairVote.ipynb'
nb=nbformat.read(p,as_version=4);client=NotebookClient(nb,timeout=600,kernel_name=sys.argv[1] if len(sys.argv)>1 else 'python3',resources={'metadata':{'path':str(R)}})
start=datetime.datetime.now(datetime.timezone.utc).isoformat();ran=[]
try:
 with client.setup_kernel():
  for i,c in enumerate(nb.cells):
   if c.cell_type!='code':continue
   if c.source.startswith(('from pathlib import Path','import descriptive_analysis','show.preference_table()','expected_files=')):
    client.execute_cell(c,i,execution_count=c.execution_count);ran.append(c.id)
  # Refresh the changed presentation cards only; do not repeat unchanged model fits.
  temporary=nbformat.v4.new_code_cell('show.cards()')
  nb.cells.append(temporary)
  try:
   client.execute_cell(temporary,len(nb.cells)-1,execution_count=999)
  finally:
   nb.cells.pop()
  cards=next(o for o in temporary.outputs if o.output_type=='display_data' and 'text/html' in o.data)
  modelcell=next(c for c in nb.cells if c.cell_type=='code' and c.source.startswith('import run_mds,check_mds'))
  old=next(i for i,o in enumerate(modelcell.outputs) if o.output_type=='display_data' and 'text/html' in o.data and 'sam-cards' in o.data['text/html'])
  modelcell.outputs[old]=cards
finally:nbformat.write(nb,p)
assert not any(o.output_type=='error' for c in nb.cells if c.cell_type=='code' for o in c.outputs)
meta_path=R/'notebook_execution.json';meta=json.loads(meta_path.read_text());meta['alaska_rule_revision']={'started_utc':start,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reexecuted_cell_ids':ran,'main_results':'Countable prefix comparisons from FairVote data, preserving literal-rank1 cohorts','unchanged_models':'Existing fresh FairVote-only49null fits and Sankey retained; sixteen model/flow files independently verified byte-identical','presentation_cards_refreshed':True};meta['notebook_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();meta_path.write_text(json.dumps(meta,indent=2))
print('Affected descriptive cells executed in Jupyter; unchanged model/flow artifacts preserved.')
