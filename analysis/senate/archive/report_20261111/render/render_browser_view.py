"""Classic white notebook presentation, summary first, with unaltered result outputs."""
from pathlib import Path
from collections import OrderedDict
import json,hashlib,re,shutil
import nbformat
from nbconvert import HTMLExporter
from bs4 import BeautifulSoup
R=Path(__file__).resolve().parent.parent
p=R/'Alaska_2026_Senate_FairVote.ipynb'
nb=nbformat.read(p,as_version=4)
exporter=HTMLExporter(template_name='classic');exporter.exclude_input=False;exporter.exclude_input_prompt=False;exporter.exclude_output_prompt=True;exporter.embed_images=True
html,_=exporter.from_notebook_node(nb)
soup=BeautifulSoup(html,'html.parser')
container=soup.select_one('#notebook-container');cells=container.select(':scope > .cell')
assert len(cells)==len(nb.cells),(len(cells),len(nb.cells))
groups=OrderedDict((k,[]) for k in ['definitions','sensitivity','method','data','provenance'])
for i,(cell,source) in enumerate(zip(cells,nb.cells)):
    group=source.metadata.get('presentation_group')
    if group in groups:groups[group].append(cell.extract())
    if source.cell_type=='code' and source.source.startswith('from pathlib import Path'):
        cell['class']=cell.get('class',[])+['sam-setup']
appendix=soup.new_tag('section',attrs={'class':'sam-appendix'})
h=soup.new_tag('h2');h.string='Methods, checks, and additional tables';appendix.append(h)
intro=soup.new_tag('p');intro.string='The full details are preserved below. Expand any section to read them.';appendix.append(intro)
titles={'definitions':'Why the FairVote subgroup counts differ from usable transfers','sensitivity':'First-usable-choice sensitivity tables','method':'MDS formulas, fitting settings, and randomized comparison','data':'Source files, ballot coverage, and ID checks','provenance':'Source policy, hashes, and complete validation results'}
for key,groupcells in groups.items():
    if not groupcells:continue
    details=soup.new_tag('details',attrs={'class':'sam-details','data-group':key});summary=soup.new_tag('summary');summary.string=titles[key];details.append(summary)
    for cell in groupcells:details.append(cell)
    appendix.append(details)
container.append(appendix)
for table in soup.select('table.sam-wide-table'):
    hint=soup.new_tag('p',attrs={'class':'sam-scroll-hint'});hint.string='Scroll sideways to see the remaining columns →';table.insert_before(hint)
style=soup.new_tag('style');style.string='''
:root{color-scheme:light!important}html,body{background:#fff!important;color:#243449!important}body{padding:80px 0 0!important;margin:0!important}
#notebook{background:#fff!important;padding:12px 0 60px!important}#notebook-container{width:calc(100% - 64px)!important;max-width:1160px!important;background:#fff!important;margin:0 auto!important;padding:20px 0!important;box-shadow:none!important}
.cell{padding:0!important;margin:0!important;background:white!important}.text_cell .prompt,.output_area .prompt{display:none!important}.text_cell_render{font-family:Arial,Helvetica,sans-serif!important;font-size:16px!important;line-height:1.7!important;padding:12px 0!important;color:#243449!important}.output_wrapper,.output_subarea{padding-left:0!important;margin-left:0!important}.output_subarea{max-width:100%!important}.output_area{padding:0!important}.output_png img{max-width:100%;height:auto;display:block;margin:16px auto 28px}.output_html{width:100%;max-width:100%;overflow-x:auto}.input{display:none!important}body.show-code .input{display:flex!important}.output_stderr,.sam-setup .output_stream{display:none!important}
.sam-title{font-size:34px!important;font-weight:600;line-height:1.25!important;letter-spacing:-.5px;margin:12px 0 22px!important}.sam-kicker{font-size:12px!important;letter-spacing:1.4px}.sam-cards{display:grid!important;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px!important;margin:26px 0!important}.sam-card{min-width:0!important;padding:18px!important}.sam-card .n{font-size:29px!important}.sam-card .l{font-size:13px!important;line-height:1.5!important}.sam-note{margin:22px 0 18px!important;font-size:14px!important}
h2{font-size:24px!important;line-height:1.35!important;color:#193f5b!important;border-bottom:1px solid #dbe5ed;padding-bottom:10px;margin-top:34px!important;scroll-margin-top:100px}h3{font-size:19px!important;line-height:1.4!important;scroll-margin-top:100px}p{margin:12px 0!important}li{margin:7px 0!important}
.sam-table{width:100%!important;font-family:Arial,Helvetica,sans-serif!important;font-size:13px!important;line-height:1.5!important;table-layout:auto!important;border-collapse:collapse!important;margin:12px 0 30px!important}.sam-table caption{font-size:16px!important;line-height:1.45!important;color:#233f57!important;padding:14px 0!important;caption-side:top;text-align:left;white-space:normal}.sam-table th{background:#1c3d5b!important;color:white!important;font-weight:600!important;padding:12px!important;white-space:normal!important;word-break:normal!important;overflow-wrap:normal!important}.sam-table td{padding:12px!important;white-space:nowrap!important;word-break:normal!important;overflow-wrap:normal!important;vertical-align:middle!important}.sam-table th:first-child,.sam-table td:first-child{min-width:165px;white-space:normal!important;text-align:left!important}.sam-wide-table{min-width:1120px!important}.sam-scroll-hint{font:12px/1.5 Arial,sans-serif!important;color:#5b7185;position:sticky;left:0;margin:0 0 6px!important}.sam-wide-table td:first-child{position:sticky;left:0;background:white;z-index:1}.sam-wide-table tr:nth-child(even) td:first-child{background:#f4f7fa}.sam-wide-table th:first-child{position:sticky;left:0;background:#1c3d5b!important;z-index:2}.sam-wide-table th{min-width:90px}.sam-scroll{width:100%;max-width:100%;overflow-x:auto!important;overscroll-behavior-x:contain;margin:10px 0 24px}.sam-scroll .sam-table{margin-bottom:0!important}
.sam-appendix{margin-top:44px;border-top:1px solid #dde6ed;padding-top:12px}.sam-details{border:1px solid #dce5eb;border-radius:6px;margin:14px 0;background:white;scroll-margin-top:90px}.sam-details summary{font:600 15px/1.5 Arial,sans-serif;padding:16px 18px;color:#254d6b;cursor:pointer;background:#f5f8fa}.sam-details[open]{padding-bottom:16px}.sam-details>.cell{margin:12px 18px!important}.sam-details .text_cell_render{font-size:14px!important}.sam-details .sam-table{font-size:12px!important}.sam-details code,.sam-details pre{overflow-wrap:anywhere;word-break:break-word;white-space:pre-wrap}.sam-details .sam-table td{white-space:normal!important;overflow-wrap:anywhere!important}
.sam-browser-bar{position:fixed;inset:0 0 auto 0;z-index:1000;display:flex;align-items:center;justify-content:space-between;height:66px;padding:0 24px;background:#fff;border-bottom:1px solid #e3e8ed;box-sizing:border-box;font-family:Arial,sans-serif}.sam-browser-brand{display:flex;align-items:center;gap:12px;font-size:18px;font-weight:600;color:#222}.sam-browser-dot{color:#e57526;font-size:29px;line-height:1}.sam-browser-sub{font-size:13px;color:#647483;font-weight:400}.sam-browser-button{font:13px Arial,sans-serif;padding:8px 12px;background:white;color:#334b5d;border:1px solid #ccd6de;border-radius:4px;cursor:pointer}
@media(max-width:800px){#notebook-container{width:calc(100% - 36px)!important}.sam-browser-sub{display:none}.sam-title{font-size:28px!important}.sam-cards{grid-template-columns:repeat(2,minmax(0,1fr))}.text_cell_render{font-size:15px!important}h2{font-size:21px!important}.sam-details>.cell{margin:8px 12px!important}}
@media print{body{padding-top:0!important}.sam-browser-bar,.input{display:none!important}#notebook-container{max-width:none!important;width:100%!important}.sam-details{break-inside:avoid}.sam-scroll{overflow:visible!important}.sam-wide-table{min-width:0!important;font-size:10px!important}}
'''
soup.head.append(soup.new_tag('meta',attrs={'name':'color-scheme','content':'light'}));soup.head.append(style)
bar=BeautifulSoup('''<header class="sam-browser-bar"><div class="sam-browser-brand"><span class="sam-browser-dot" aria-hidden="true">◉</span><span>Jupyter Notebook <span class="sam-browser-sub">&nbsp;/&nbsp; Alaska 2026 Senate · FairVote</span></span></div><button class="sam-browser-button" type="button" id="sam-code-toggle" aria-pressed="false">Show code</button></header>''','html.parser').header
soup.body.insert(0,bar)
script=soup.new_tag('script');script.string="document.getElementById('sam-code-toggle').addEventListener('click',function(){const on=document.body.classList.toggle('show-code');this.textContent=on?'Hide code':'Show code';this.setAttribute('aria-pressed',String(on));if(on)document.querySelectorAll('details.sam-details').forEach(d=>d.open=true);});";soup.body.append(script)
if soup.title:soup.title.string='Alaska 2026 Senate — FairVote notebook'
out=R/'Alaska_2026_Senate_FairVote.html';out.write_text(str(soup),encoding='utf-8')
readable=R/'Alaska_2026_Senate_FairVote_Readable.html';shutil.copy2(out,readable)
expected_tables=sum(len(BeautifulSoup(o.get('data',{}).get('text/html',''),'html.parser').select('table')) for c in nb.cells for o in c.get('outputs',[]))
assert len(soup.select('table'))==expected_tables
assert len(soup.select('img[src^="data:image/png;base64,"]'))==4
print(json.dumps({'file':str(readable),'embedded_tables':len(soup.select('table')),'embedded_figures':4,'collapsed_appendices':len(groups),'notebook_sha256':hashlib.sha256(p.read_bytes()).hexdigest()},indent=2))
