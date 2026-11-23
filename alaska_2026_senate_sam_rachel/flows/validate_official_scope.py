"""Document coverage against an authenticated contemporaneous aggregate report."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]

def main():
    refs=ROOT/'references'
    provenance=json.loads((refs/'official_summary_provenance.json').read_text())
    for file,expected in provenance['files'].items():
        assert hashlib.sha256((refs/file).read_bytes()).hexdigest()==expected
    text=(refs/'official_summary_20261111.txt').read_text()
    assert '11/11/2026 5:47:54 PM' in text
    source=json.loads((ROOT/'descriptive/source_provenance.json').read_text())
    values=[]
    for slug,title in [('governor','Governor / Lieutenant Governor'),('us_house','U.S. Representative'),('us_senate','U.S. Senator')]:
        section=text.split(title,1)[1]
        official=int(re.search(r'Times Cast\s+([\d,]+)\s*/',section)[1].replace(',',''))
        rows=source['rows'][slug]
        values.append({'contest':slug,'Rachel_scanned_rows':rows,'official_report_times_cast':official,'official_minus_Rachel':official-rows})
    result={'reference_role':'Coverage comparison only; not ballot input or model calibration','official_report_printed':'2026-11-11 17:47:54 Alaska time','comparisons':values,'interpretation':'Rachel records do not equal all ballots in this contemporaneous official summary. DOE states CVR excludes hand-count-only ballots; scope/timing can differ. This aggregate comparison alone cannot identify the exact reason for every missing record, and no ballot is imputed. Exact 54-cell round-table validation refers to the frozen Nov11 FairVote-linked RCVis tables, not official certified totals.'}
    (refs/'official_scope_comparison.json').write_text(json.dumps(result,indent=2))
    return result

if __name__=='__main__':print(json.dumps(main(),indent=2))
