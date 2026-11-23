"""Presentation-only repair: keep every analysis value and executable cell intact."""
from pathlib import Path
import json,hashlib,re,shutil,datetime
from bs4 import BeautifulSoup
import nbformat
R=Path(__file__).resolve().parent.parent
p=R/'Alaska_2026_Senate_FairVote.ipynb'
backup=R/'render/before_layout_fix';backup.mkdir(exist_ok=True)
if not (backup/p.name).exists():shutil.copy2(p,backup/p.name)
nb=nbformat.read(p,as_version=4)
code_before=[c.source for c in nb.cells if c.cell_type=='code']
values_before=[]
for c in nb.cells:
 for o in c.get('outputs',[]):
  data=o.get('data',{})
  if 'text/html' in data:
   for t in BeautifulSoup(data['text/html'],'html.parser').find_all('table'):values_before.append(t.get_text(' ',strip=True))
  if 'image/png' in data:values_before.append(hashlib.sha256(data['image/png'].encode()).hexdigest())
nb.cells[0].source='''<div class="sam-kicker">Princeton · FairVote data · November 13, 2026</div>
<div class="sam-title">Alaska 2026: crossover preferences,<br>vote transfers, and a single candidate axis</div>

**Prepared for Sam · FairVote’s November 11 ballot files**

This notebook answers the ballot questions and repeats the original one-axis Senate analysis using FairVote’s three CSVs only. **Daniel J. Sullivan Jr. is the outsider; Dan S. Sullivan is the incumbent senator.** The source covers 244,705 scanned Senate ballots and is preliminary.

<div class="sam-cards"><div class="sam-card"><div class="n">568</div><div class="l">Peltola above Dan S. · both legally usable</div></div><div class="sam-card"><div class="n">765</div><div class="l">Only Peltola in usable finalist rankings</div></div><div class="sam-card"><div class="n">61.5%</div><div class="l">Observed consistency · 3–4 named ranks</div></div><div class="sam-card"><div class="n">41.6%</div><div class="l">Random consistency · 49 fresh profiles</div></div></div>

### Findings to take into the meeting

- **568 of 3,940 literal Daniel-first ballots (14.42%) have both finalists in their usable rankings, with Peltola above Dan S.** The reverse count is **423 (10.74%)**. Headline comparisons apply Alaska’s overvote and skipped-rank rules.
- The governor/House distributions and every Senate Sankey count are unchanged from the previous analysis.
- **One-axis consistency is 61.54% observed versus 41.57% random** among three-/four-name prefixes, a 19.97-point difference.
- All 54 published round-count values match. The supplementary visible-name audit matches nine subgroup cells in the archived November 12 article using November 11 data; these are distinct from countable preferences.

<div class="sam-note"><b>First choice:</b> the descriptive questions use literal rank 1. All headline preference comparisons, the Sankey and MDS use usable preferences after skipped-rank and overvote rules. The literal-rank-1 cohort is retained explicitly. Candidate affiliations are not voters’ registered parties.</div>'''
# Assign presentation groups without changing executable-cell order or source.
current=None
for c in nb.cells[2:]:
 s=c.source
 if c.cell_type=='markdown':
  if s.startswith('## 1 · Rebuild'):current='data'
  elif s.startswith(('## 1 · Daniel','## 2 · Daniel')):current=None;c.source=s.replace('## 2 ·','## 1 ·',1)
  elif s.startswith(('## 2 · Governor','## 3 · Governor')):current=None;c.source=s.replace('## 3 ·','## 2 ·',1)
  elif s.startswith('### First-usable-choice sensitivity'):current='sensitivity'
  elif s.startswith(('## 4 · Visible','## Supplementary audit')):current='definitions'
  elif s.startswith(('## 5 · FairVote-only','## 3 · Sankey')):current=None;c.source=s.replace('## 5 · FairVote-only Sankey: all Senate ballot paths','## 3 · Sankey: how Senate ballots transfer',1)
  elif s.startswith('## 6 · Original'):current='method'
  elif s.startswith('The fresh FairVote-only results'):current=None
  elif s.startswith('## 7 · Source'):current='provenance'
  elif s.startswith('## Supplemental'):current='provenance'
 if c.cell_type=='code' and c.source.startswith('import run_mds,check_mds'):current=None
 if current:
  c.metadata['presentation_group']=current
  if c.cell_type=='code':
   c.metadata['collapsed']=True;c.metadata.setdefault('jupyter',{})['outputs_hidden']=True
# Put a short visible model introduction before the long-method group.
if not any(c.metadata.get('presentation_insert')=='model-heading' for c in nb.cells):
 idx=next(i for i,c in enumerate(nb.cells) if c.metadata.get('presentation_group')=='method')
 intro=nbformat.v4.new_markdown_cell('''## 4 · Single-axis MDS: real and randomized consistency

The original method places the four Senate candidates on one axis and checks whether each usable ranking can arise from increasing distance along that axis. We fitted the observed profile and **49 fresh randomized profiles**, preserving first choice and prefix length. Detailed formulas and fitting settings are available below.''',metadata={'presentation_insert':'model-heading'})
 nb.cells.insert(idx,intro)
# The presentation stylesheet will also be visible when the .ipynb is trusted/opened in Jupyter.
css='''<style>
.sam-table{font-size:13px!important;line-height:1.5!important;width:100%!important;table-layout:auto!important}
.sam-table th,.sam-table td{padding:10px 12px!important;word-break:normal!important;overflow-wrap:normal!important}
.sam-table td{white-space:nowrap!important}
.sam-table td:first-child,.sam-table th:first-child{min-width:165px;white-space:normal!important}
.sam-wide-table{min-width:1120px!important}
.sam-wide-table th{min-width:90px;white-space:normal!important}
.sam-scroll{width:100%;overflow-x:auto;overscroll-behavior-x:contain;margin:12px 0 28px}
.sam-scroll .sam-table{margin-bottom:0!important}
.sam-table caption{padding-bottom:12px!important}
.sam-title{font-weight:650!important;line-height:1.22!important}
</style>'''
nb.cells[0].source=css+nb.cells[0].source
for c in nb.cells:
 for o in c.get('outputs',[]):
  data=o.get('data',{})
  if 'text/html' not in data:continue
  soup=BeautifulSoup(data['text/html'],'html.parser')
  for t in soup.find_all('table'):
   cols=max([len(row.find_all(['th','td'],recursive=False)) for row in t.find_all('tr')] or [0])
   classes=t.get('class',[])
   if cols>=7 and 'sam-wide-table' not in classes:classes.append('sam-wide-table')
   t['class']=classes
   par=t.parent
   if par.name=='div':par['class']=list(set(par.get('class',[])+['sam-scroll']))
  data['text/html']=str(soup)
values_after=[]
for c in nb.cells:
 for o in c.get('outputs',[]):
  data=o.get('data',{})
  if 'text/html' in data:
   for t in BeautifulSoup(data['text/html'],'html.parser').find_all('table'):values_after.append(t.get_text(' ',strip=True))
  if 'image/png' in data:values_after.append(hashlib.sha256(data['image/png'].encode()).hexdigest())
assert code_before==[c.source for c in nb.cells if c.cell_type=='code']
assert values_before==values_after,'An existing table or figure changed during layout repair'
nbformat.validate(nb);nbformat.write(nb,p)
meta_path=R/'notebook_execution.json';meta=json.loads(meta_path.read_text());meta['presentation_restyled_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();meta['presentation_only_change']='Summary-first layout, readable tables and collapsed technical sections; every executable cell, original table value and figure unchanged.';meta['notebook_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();meta_path.write_text(json.dumps(meta,indent=2))
(R/'render/layout_verification.json').write_text(json.dumps({'all_executable_cells_unchanged':True,'all_original_table_text_and_figure_hashes_unchanged':True,'original_output_elements_verified':len(values_after),'notebook_sha256':meta['notebook_sha256']},indent=2))
print('Presentation repaired; all existing numerical outputs, figures and executable cells preserved.')
