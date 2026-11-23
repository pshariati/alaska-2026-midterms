"""Append a labeled supplemental benchmark result without rerunning/changing models."""
from pathlib import Path
import json,hashlib,datetime
import nbformat
R=Path(__file__).resolve().parent
nbpath=R/'Alaska_2026_Senate_Rachel_FairVote.ipynb'
validation=json.loads((R/'references/benchmark_validation.json').read_text())
assert validation['cells']==validation['matches']==54 and not validation['mismatches']
nb=nbformat.read(nbpath,as_version=4)
text='''## Supplemental validation · all three Rachel contests

The separately executed `flows/validate_all_contest_benchmarks.py` reconstructs the four published stages directly from each supplied Rachel CSV. **All 54 numeric candidate/inactive values match the frozen FairVote tables across governor, House and Senate, with zero mismatches.** Each stage conserves every Rachel ballot, including its initially inactive baseline.

This is an external-reference check, not a reuse of old ballot patterns or old analysis results. The 54 comparisons, source-file hashes and reference hashes are saved under `references/`. The main notebook and its observed/randomized Senate models were executed in Jupyter before this presentation note was appended; no model results were changed.

To reproduce this additional check independently, run `python3 flows/validate_all_contest_benchmarks.py`. The nine Daniel subgroup cells in Section 4 are a separate descriptive comparison and also match under the stated visible-finalist definition.'''
nb.cells=[c for c in nb.cells if not(c.cell_type=='markdown' and c.source.startswith('## Supplemental validation'))]
nb.cells.append(nbformat.v4.new_markdown_cell(text));nbformat.validate(nb);nbformat.write(nb,nbpath)
p=R/'notebook_execution.json';meta=json.loads(p.read_text());meta['supplemental_validation_note_added_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();meta['supplemental_validation']='Separate Rachel-only source-script execution:54/54published numeric cells; model outputs unchanged';meta['notebook_sha256']=hashlib.sha256(nbpath.read_bytes()).hexdigest();p.write_text(json.dumps(meta,indent=2))
print('Added verified54/54supplemental validation note; model outputs unchanged.')
