"""Structural regressions for moved modules and public notebook sources."""
from pathlib import Path
import ast
import json
import re
import subprocess
import sys
import unittest
from unittest.mock import patch, Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from analysis.shared.paths import INPUTS_ROOT, REPO_ROOT, model_dir, resolve_recorded_path


class LayoutTests(unittest.TestCase):
    def test_canonical_paths_and_historical_provenance(self):
        self.assertEqual(REPO_ROOT, ROOT)
        self.assertEqual(INPUTS_ROOT, ROOT/'data/nov11')
        for slug, race in [('us_senate','senate'),('us_house','house'),('governor','governor')]:
            self.assertEqual(model_dir(slug), ROOT/'analysis'/race/'candidate_axis')
            self.assertTrue((model_dir(slug)/'profile.json').is_file())
            self.assertEqual(resolve_recorded_path('axis_models/'+slug+'/candidate_axis.csv'), model_dir(slug)/'candidate_axis.csv')
        self.assertEqual(resolve_recorded_path('inputs/example.csv'), INPUTS_ROOT/'example.csv')
        for bad in ['/private/secret.csv', '../outside.csv']:
            with self.assertRaises(ValueError): resolve_recorded_path(bad)

    def test_one_canonical_core_and_metadata(self):
        self.assertEqual(list(ROOT.glob('analysis/**/og_axis.py')), [ROOT/'analysis/shared/og_axis.py'])
        self.assertEqual(list(ROOT.glob('analysis/**/candidate_metadata.json')), [ROOT/'analysis/shared/candidate_metadata.json'])
        for obsolete in ['statewide_analysis','alaska_2026_senate_sam_rachel','alaska_presentation_20261117']:
            self.assertFalse((ROOT/obsolete).exists())

    def test_local_package_import_targets(self):
        for path in (ROOT/'analysis').rglob('*.py'):
            if 'archive' in path.parts: continue
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith('analysis.'):
                    base = ROOT.joinpath(*node.module.split('.'))
                    self.assertTrue(base.is_dir() or base.with_suffix('.py').is_file(), (path,node.module))
                    if base.is_dir():
                        for alias in node.names:
                            # Package imports in this project name modules, not re-exported objects.
                            self.assertTrue((base/alias.name).is_dir() or (base/(alias.name+'.py')).is_file(), (path,node.module,alias.name))

    def test_notebook_sources_parse_and_outputs_are_cleared(self):
        for path in ROOT.rglob('*.ipynb'):
            if '.git' in path.parts: continue
            nb = json.loads(path.read_text())
            for cell in nb['cells']:
                if cell['cell_type']=='code':
                    self.assertEqual(cell['outputs'], [])
                    self.assertIsNone(cell['execution_count'])
                    ast.parse(''.join(cell['source']), filename=str(path))

    def test_markdown_local_links(self):
        for path in ROOT.rglob('*.md'):
            if '.git' in path.parts or 'archive' in path.parts: continue
            for target in re.findall(r'\]\(([^)]+)\)',path.read_text()):
                if target.startswith(('http:','https:','#','mailto:')): continue
                target=target.split('#')[0]
                self.assertTrue((path.parent/target).exists(), (str(path.relative_to(ROOT)),target))

    def test_senate_source_version_rejected_before_parsing_or_fitting(self):
        from analysis.senate.candidate_axis import run_mds
        fake_input = Mock()
        with patch.object(run_mds, 'INPUT', fake_input), patch.object(run_mds, 'sha256', return_value='wrong-version'), patch.object(run_mds, 'fit_axis') as fit:
            with self.assertRaises(ValueError): run_mds.main()
            fake_input.open.assert_not_called()
            fake_input.read_bytes.assert_not_called()
            fit.assert_not_called()

    def test_safe_help_entrypoints(self):
        for args in [['scripts/fit_candidate_axis.py','--help'],['scripts/package_code.py','--help'],
                     ['-m','analysis.house.candidate_axis.fit','--help'],
                     ['-m','analysis.governor.candidate_axis.fit','--help']]:
            completed=subprocess.run([sys.executable,*args],cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(completed.returncode,0,completed.stderr)


if __name__ == '__main__': unittest.main()
