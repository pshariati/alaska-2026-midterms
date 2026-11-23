from pathlib import Path
from collections import Counter
from itertools import permutations
import hashlib
import importlib.util
import json
import subprocess
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'alaska_2026_sam_followup_20261116/common'))
import og_axis as core


def independent_compatible(ranking, axis):
    if len(ranking) <= 1:
        return True
    cuts = sorted({0., 1.} | {(axis[a] + axis[b]) / 2
                              for a in ranking for b in ranking if a < b})
    for a, b in zip(cuts, cuts[1:]):
        if b-a <= 1e-12:
            continue
        distances = [abs((a+b)/2-axis[c]) for c in ranking]
        if all(x < y for x, y in zip(distances, distances[1:])):
            return True
    return False


class CoreChecks(unittest.TestCase):
    def test_preserved_core(self):
        path = Path(core.__file__)
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),
                         'b4ef0b5f1a152e655a114570e71d88791831241994c0a04d095f37363a4d001a')

    def test_weighted_pair_counts(self):
        profile = {(0, 1, 2): 7, (2, 0): 3, (1,): 11, (): 5}
        adjacency, together = core.pair_matrices(profile, 3)
        expected_a = np.array([[0, 7, 0], [0, 0, 7], [3, 0, 0]])
        expected_c = np.array([[10, 7, 10], [7, 18, 7], [10, 7, 10]])
        np.testing.assert_array_equal(adjacency, expected_a)
        np.testing.assert_array_equal(together, expected_c)

    def test_dissimilarity_and_zero_fallback(self):
        profile = {(0, 1, 2): 7, (2, 0): 3, (1,): 11}
        distance = core.dissimilarity(profile, 3)
        expected = np.array([[0, np.sqrt(2), 1/np.sqrt(.15)],
                             [np.sqrt(2), 0, np.sqrt(2)],
                             [1/np.sqrt(.15), np.sqrt(2), 0]])
        np.testing.assert_allclose(distance, expected)
        sparse = core.dissimilarity({(0, 1): 2, (2,): 3}, 3)
        self.assertEqual(sparse[0, 2], 4.)
        np.testing.assert_array_equal(sparse, sparse.T)

    def test_strict_geometry_all_partial_rankings(self):
        for axis in [np.array([0., .2, .7, 1.]), np.array([0., 1/3, 2/3, 1.])]:
            for length in range(1, 5):
                rankings = list(permutations(range(4), length))
                flags = core.prefix_flags(axis[np.array(rankings)])[:, -1]
                for ranking, flag in zip(rankings, flags):
                    self.assertEqual(bool(flag), independent_compatible(ranking, axis), ranking)

    def test_null_exact_joint_margins(self):
        profile = {(0, 1, 2): 47, (0, 3): 19, (2, 1): 13, (1,): 7, (): 3}
        null = core.matched_null(profile, 4, 731)
        def margins(p):
            counts = Counter()
            for b, weight in p.items():
                counts[b[0] if b else None, len(b)] += weight
            return counts
        self.assertEqual(margins(profile), margins(null))
        self.assertEqual(sum(profile.values()), sum(null.values()))
        core.validate_profile(null, 4)
        self.assertEqual(null, core.matched_null(profile, 4, 731))

    def test_empty_ballots_excluded_from_gamma(self):
        result = core.summarize({(0,): 5, (1, 0): 3, (): 11}, np.array([0., 1.]))
        self.assertEqual(result['ballots'], 8)
        self.assertEqual(result['empty_ballots'], 11)
        self.assertEqual(result['gamma'], 1.)

    def test_portable_help_does_not_fit(self):
        result = subprocess.run([sys.executable, str(ROOT/'scripts/fit_candidate_axis.py'), '--help'],
                                capture_output=True, text=True, check=True)
        self.assertIn('--null-draws', result.stdout)


if __name__ == '__main__':
    unittest.main()
