"""Package exactly the checked, manifest-listed public code and saved aggregates."""
from pathlib import Path
import argparse
import hashlib
import json
import zipfile
from check_release import ROOT, main as check_release


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='ZIP path outside the checkout')
    args = parser.parse_args()
    output = args.output.resolve()
    if output == ROOT or ROOT in output.parents:
        parser.error('Use an output path outside the checkout.')
    check_release()
    records = json.loads((ROOT/'provenance/source_manifest.json').read_text())['files']
    paths = [r['path'] for r in records] + ['provenance/source_manifest.json']
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for relative in sorted(paths):
            archive.write(ROOT/relative, 'alaska-2026-midterms/'+relative)
    with zipfile.ZipFile(output) as archive:
        for relative in paths:
            assert archive.read('alaska-2026-midterms/'+relative) == (ROOT/relative).read_bytes()
    print(json.dumps({'zip':str(output),'files':len(paths),'sha256':hashlib.sha256(output.read_bytes()).hexdigest()}))

if __name__ == '__main__':
    main()
