from pathlib import Path
from html import escape
import json,csv,hashlib,zipfile,shutil

BASE=Path(__file__).resolve().parent
r=json.loads((BASE/'results.json').read_text())
assert r['status']=='exact_match'
with (BASE/'comparison_to_sam.csv').open() as f:checks=list(csv.DictReader(f))
assert len(checks)==14 and all(row['difference']=='0' and row['percent_match']=='True' for row in checks)
names=['Begich, Nick','Hill, Bill','Hafner, Eric','McDermott, James C. "Jim"','Write-in']
rounds=r['display_rounds']
rows=[]
for name in names:
    cells=[]
    for i,rd in enumerate(rounds):
        count=rd['counts'].get(name)
        if count is None:cells.append('<td class="eliminated">Eliminated</td>')
        else:
            pct=100*count/rd['active_ballots']
            cells.append(f'<td><strong>{count:,}</strong><span>{pct:.2f}%</span></td>')
    rows.append('<tr><th scope="row">'+escape(name)+'</th>'+''.join(cells)+'</tr>')
for label,values in [
    ('Continuing ballots',[rd['active_ballots'] for rd in rounds]),
    ('Inactive ballots: total',[rd['counts'].get('Inactive',0) for rd in rounds]),
    ('Newly inactive since displayed round 1',[rd['counts'].get('Inactive',0)-r['initially_inactive'] for rd in rounds])]:
    rows.append('<tr class="totals"><th scope="row">'+label+'</th>'+''.join(f'<td>{v:,}</td>' for v in values)+'</tr>')
detail=''.join('<tr>'+''.join('<td>'+escape(str(row[k]))+'</td>' for k in ['round','candidate','recomputed_votes','screenshot_votes','difference','recomputed_percent','screenshot_percent'])+'</tr>' for row in checks)
official_rows=[]
for i,rd in enumerate(r['official_settings_rounds'],1):
    official_rows.append('<tr>'+f'<td>{i}</td>'+''.join(f'<td>{rd["counts"].get(name,0):,}</td>' if name in rd['counts'] else '<td>Eliminated</td>' for name in names[:4])+f'<td>{rd["counts"]["Inactive"]:,}</td></tr>')
source=escape(r['source_url']);benchmark=escape(r['benchmark_url']);rules=escape(r['rules_url'])
html='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>November 16 Alaska House: independent comparison</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f3f6f8;color:#23384f;font:16px/1.55 Arial,sans-serif}main{max-width:1120px;margin:32px auto;background:white;padding:40px 44px;border:1px solid #dce4ea;border-radius:10px}.eyebrow{font-size:12px;letter-spacing:.1em;color:#147e83;font-weight:bold}h1{font-size:32px;line-height:1.2;margin:12px 0 16px}h2{font-size:21px;margin:30px 0 12px}p{max-width:950px}small,.muted{color:#5b7083}.metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:26px 0}.metric{padding:18px;background:#eef5f6;border-left:4px solid #147e83}.metric strong{display:block;font-size:27px}.metric span{font-size:14px}.tablewrap{overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:14px}thead{background:#23384f;color:#fff}th,td{padding:12px 14px;text-align:right;border-bottom:1px solid #dce4ea;vertical-align:middle}th:first-child,td:first-child{text-align:left}tbody th{font-weight:normal;width:30%;text-align:left}td strong{display:block;font-size:17px}td span{display:block;color:#5b7083;font-size:13px}.eliminated{background:#f3f5f7;color:#718295;font-size:12px}.totals{font-size:12px;background:#f4f7f9}.note{padding:16px 20px;background:#f3f6f9;border-left:3px solid #b6cbd6;font-size:14px}.pass{color:#147e83;font-weight:bold}li{margin:8px 0}a{color:#147e83}details{margin-top:24px}summary{cursor:pointer;font-weight:bold}code{font-size:12px;overflow-wrap:anywhere}.sources{font-size:13px;border-top:1px solid #dce4ea;margin-top:32px;padding-top:18px}footer{margin-top:26px;font-size:12px;color:#5b7083}@media(max-width:650px){main{margin:0;padding:24px 16px;border-radius:0}h1{font-size:27px}.metrics{grid-template-columns:1fr}table{min-width:720px}}@media print{body{background:white}main{border:0;margin:0;padding:12px}details{display:block}a{color:inherit}}
</style></head><body><main><div class="eyebrow">ALASKA 2026 / SEPARATE NOVEMBER 16 CHECK</div>
<h1>Independent House tally matches Sam’s snapshot exactly</h1>
<p>Recomputed directly from the state’s November 16 cast vote records. Every candidate vote total and displayed percentage in the supplied screenshot agrees. This check uses the raw state export; Rachel’s November 11 data and the existing notebook are separate.</p>
<div class="metrics"><div class="metric"><strong>14 / 14</strong><span>Candidate vote totals match</span></div><div class="metric"><strong>14 / 14</strong><span>Displayed percentages match</span></div><div class="metric"><strong>285,439</strong><span>House ballot records retained</span></div></div>
<h2>Round-by-round results</h2><p class="muted">Round numbering follows FairVote’s display so it can be compared directly with the screenshot. Percentages use continuing ballots in each round.</p>
<div class="tablewrap"><table><thead><tr><th>Candidate / measure</th><th>Round 1</th><th>Round 2</th><th>Round 3</th><th>Round 4</th></tr></thead><tbody>'''+''.join(rows)+'''</tbody></table></div>
<p class="note"><b>Inactive counts:</b> 2,668 ballots were already inactive at the first displayed stage. The published RCVis “Inactive Ballots” series starts at zero and reports additional inactivity: 0; 252; 2,738; 13,904. Including the initial 2,668 gives 16,572 total inactive ballots in the final replay. No ballot records were removed to match that display.</p>
<h2>Final replay</h2><p><b>Begich: 138,417 (51.48%). Hill: 130,450 (48.52%). Margin: 7,967 votes.</b></p>
<h2>What was checked</h2><ul>
<li>All 1,760 CVR files were read. Every session has a unique TabulatorId / BatchId / RecordId identity and exactly one current ballot state. Two current Modified records supersede their Original states.</li>
<li>The House contest and eligible ballot types were identified from the archive manifests. All 285,439 eligible sessions are retained, including blank and inactive records.</li>
<li>Accepted marks follow the vendor’s IsVote flag. The 862 recorded ambiguous marks flagged IsVote=false remain preserved in the raw data; they were not converted into votes.</li>
<li>Overvotes stop that rank and lower preferences; one skipped rank can be crossed, two consecutive skips stop lower preferences; repeated candidates retain their highest ranking. These rules are applied to original rank occupancy before excluding unresolved write-ins.</li>
<li>Each round was calculated two ways: from interpreted preference sequences and by a separate scan of original rank cells. All allocations agree and every round conserves all 285,439 ballots.</li>
<li>Eliminations were derived from the lowest tally, rather than imposed from the screenshot: Write-in, McDermott, Hafner. No elimination tie required a decision.</li>
</ul>
<h2>Write-in rule: separately verified</h2><p>The combined initial write-in tally is 435; the leading printed candidate has 134,732. Under 6 AAC 25.071, all write-ins are defeated when W &lt; L and L − W ≥ 0.005 × (L + W). This comparison was made with exact integer arithmetic. The raw CVR does not identify individual written names; the analysis would stop for individual resolution if that were required.</p>
<p>Excluding unresolved write-ins before the named-candidate rounds produces the following three rounds. They are <b>identical to displayed rounds 2–4 above</b>, including total inactivity.</p>
<div class="tablewrap"><table><thead><tr><th>Named-candidate round</th><th>Begich</th><th>Hill</th><th>Hafner</th><th>McDermott</th><th>Inactive total</th></tr></thead><tbody>'''+''.join(official_rows)+'''</tbody></table></div>
<details><summary>Inspect all candidate comparisons</summary><div class="tablewrap"><table><thead><tr><th>Round</th><th>Candidate</th><th>Recomputed</th><th>Screenshot</th><th>Difference</th><th>Recomputed %</th><th>Screenshot %</th></tr></thead><tbody>'''+detail+'''</tbody></table></div></details>
<div class="sources"><b>Sources and version</b><ul>
<li><a href="'''+source+'''">State cast vote record archive</a>. Saved unmodified before extraction. Internal files dated November 16; retrieved November 17, 2026.</li>
<li><a href="'''+benchmark+'''">FairVote-linked November 16 House table</a> and Sam’s supplied screenshot. The screenshot’s 14 candidate counts and 14 percentages were transcribed as external benchmarks, not used to fit or alter the tally.</li>
<li><a href="'''+rules+'''">Alaska official tabulation explanations</a>; <a href="https://www.akleg.gov/statutesPDF/aac%20Title%206.pdf">6 AAC 25.071–.072</a>.</li>
</ul><p>Archive SHA-256: <code>'''+r['source_sha256']+'''</code></p></div>
<footer>Scope: unofficial replay of the scanned ballots in this dated export, not certified final statewide results. The state says the CVR excludes ballots counted only by hand. This check does not establish voter intent or independently adjudicate paper marks.</footer>
</main></body></html>'''
(BASE/'Alaska_Nov16_House_Comparison.html').write_text(html)
assert html.count('<table>')==3 and '138,417' in html and '130,450' in html
readme='''NOVEMBER 16 ALASKA HOUSE CHECK

The raw state export independently reproduces Sam's screenshot exactly:
14/14 candidate vote totals; 14/14 displayed percentages; 4/4 additional-inactive values.
Final replay: Begich 138,417; Hill 130,450; margin 7,967. Total source House records: 285,439.

Open nov16_house_check/Alaska_Nov16_House_Comparison.html for the readable report.

To recompute from the preserved raw archive, using Python 3.10 or newer:
python3 nov16_house_check/analyze.py
python3 nov16_house_check/build_report.py

Standard library only; no network or package installation is required.
Keep the extracted directory structure intact. The script verifies the original archive hash.

Data:
new_data_review/public_cvr_retrieved_20261117/CVR_Export.zip: unmodified raw JSON archive.
nov16_house_check/house_ballots.csv.gz: one row per House ballot, original accepted-mark rank sets, valid prefix, source identity and raw current House contest JSON. Original and Modified full states remain in the raw ZIP.
nov16_house_check/rank_patterns.json: lossless weighted aggregation of original accepted-mark rank sets.
nov16_house_check/results.json: counts, checks, denominators and provenance.
nov16_house_check/comparison_to_sam.csv: every candidate count/percentage comparison.
nov16_house_check/house_rounds.csv: candidate tallies and inactive denominators.
nov16_house_check/inactive_comparison.csv: additional inactivity relative to displayed round1.

The original Rachel/FairVote November 11 inputs, notebook, MDS fits and slides are not part of this analysis and were not overwritten. This is a raw-state-CVR House check only.
Not official certified results. See the HTML report for scope and limitations.
'''
(BASE/'README.txt').write_text(readme)
image=Path('/var/folders/7h/xh8qj0js56b289l4ms81l8f80000gn/T/codex-clipboard-980dbf27-a3bb-4498-9bab-83e63925f611.png')
if image.exists():shutil.copy2(image,BASE/'Sam_supplied_snapshot.png')
out=BASE/'Alaska_Nov16_House_Check.zip'
files=[p for p in BASE.iterdir() if p.is_file() and p!=out and p.name!='SHA256SUMS.json']
hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
(BASE/'SHA256SUMS.json').write_text(json.dumps(hashes,indent=2))
files.append(BASE/'SHA256SUMS.json')
rawdir=BASE.parent/'new_data_review/public_cvr_retrieved_20261117'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=5) as z:
    for p in sorted(files):z.write(p,'nov16_house_check/'+p.name)
    for p in sorted(rawdir.iterdir()):
        if p.is_file():z.write(p,'new_data_review/public_cvr_retrieved_20261117/'+p.name)
with zipfile.ZipFile(out) as z:assert z.testzip() is None
print(json.dumps({'report':str(BASE/'Alaska_Nov16_House_Comparison.html'),'package':str(out),'package_bytes':out.stat().st_size,'files':len(files)},indent=2))
