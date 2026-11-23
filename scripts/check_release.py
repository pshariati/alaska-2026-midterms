"""Check copied source integrity and syntax without running election fits."""
from pathlib import Path
import ast
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / 'provenance/source_manifest.json').read_text())
for record in manifest['files']:
    path = ROOT / record['path']
    assert path.is_file(), str(path)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == record['release_sha256'], str(path)
    if record['transformation'] == 'Byte-for-byte copy.':
        assert record['source_sha256'] == record['release_sha256'], str(path)
count = 0
for path in ROOT.rglob('*.py'):
    if '.venv' in path.parts:
        continue
    ast.parse(path.read_text(), filename=str(path))
    count += 1
for path in ROOT.rglob('*.ipynb'):
    if '.venv' in path.parts:
        continue
    nb = json.loads(path.read_text())
    for cell in nb.get('cells', []):
        if cell.get('cell_type') == 'code':
            assert cell.get('outputs') == [], str(path)
            assert cell.get('execution_count') is None, str(path)
assert not list(ROOT.glob('**/inputs/*.csv'))
assert not list(ROOT.glob('**/*.jsonl.gz'))
print(f'Passed: {len(manifest["files"])} copied-source/aggregate hashes; {count} Python files; cleared notebook outputs.')
