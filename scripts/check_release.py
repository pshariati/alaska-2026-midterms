"""Check packaged-file hashes and syntax without reading CVRs or fitting models."""
from pathlib import Path
import ast
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
IGNORED_PARTS = {'.git', '.venv', '__pycache__', '.pytest_cache', '.ipynb_checkpoints', 'node_modules'}

def release_files():
    return {str(p.relative_to(ROOT)): p for p in ROOT.rglob('*')
            if p.is_file() and not any(part in IGNORED_PARTS for part in p.relative_to(ROOT).parts)
            and p.name != '.DS_Store' and p.suffix not in {'.pyc', '.log', '.tmp'}}

def main():
    manifest = json.loads((ROOT / 'provenance/source_manifest.json').read_text())
    paths = set()
    for record in manifest['files']:
        relative = record['path']
        assert relative not in paths, 'Duplicate manifest path: ' + relative
        paths.add(relative)
        path = ROOT / relative
        assert path.is_file(), str(path)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record['release_sha256'], str(path)
        if record['transformation'] == 'Byte-for-byte copy.':
            assert record['source_sha256'] == record['release_sha256'], str(path)
    files = release_files()
    assert set(files) == paths | {'provenance/source_manifest.json'}, sorted(set(files) ^ (paths | {'provenance/source_manifest.json'}))
    count = notebooks = 0
    for relative, path in files.items():
        assert not path.is_symlink(), relative
        assert not (relative.startswith('data/') and path.suffix.lower() in {'.csv', '.zip', '.gz'}), relative
        assert not relative.endswith(('.jsonl.gz', '.csv.gz')), relative
        if path.suffix == '.py':
            ast.parse(path.read_text(), filename=relative)
            count += 1
        if path.suffix == '.ipynb':
            notebooks += 1
            nb = json.loads(path.read_text())
            for cell in nb.get('cells', []):
                if cell.get('cell_type') == 'code':
                    assert cell.get('outputs') == [] and cell.get('execution_count') is None, relative
                    source = cell.get('source', '')
                    ast.parse(''.join(source) if isinstance(source, list) else source, filename=relative)
    print(f'Passed: {len(paths)} packaged-file hashes; {count} Python files; {notebooks} cleared notebooks and code-cell syntax; excluded ballot data.')

if __name__ == '__main__':
    main()
