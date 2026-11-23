"""No-fit regressions for the preserved statewide aggregate results.

These checks read committed, aggregated profiles only. They neither read CVRs
nor call an MDS solver. Agreement with saved scores does not establish that the
historical scikit-learn 1.6.1 solver was correct; see docs/KNOWN_ISSUES.md.
"""
from collections import Counter
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path
import statistics
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

RACES = ("senate", "governor", "house")
CORE_SHA256 = "b4ef0b5f1a152e655a114570e71d88791831241994c0a04d095f37363a4d001a"

# Frozen before the race-folder reorganization, from the former
# statewide_analysis/axis_models directory. These are historical artifacts, so
# even embedded historical paths/provenance must not be rewritten in place.
SAVED_SHA256 = {
    "analysis/governor/candidate_axis/adjacency_matrix.csv": "39634ad963c8b323ac643eea9f4b32e84cf5863a8650383352fe735d00b89339",
    "analysis/governor/candidate_axis/candidate_axis.csv": "ca6816d5bf29840ef84134a273e29d75a5d246a74b51e6928fbe855375ad89d9",
    "analysis/governor/candidate_axis/consistency_summary.csv": "991dfe6a449f1e1387fde17cd34327339c81431781416a583c59224c8c4eea6c",
    "analysis/governor/candidate_axis/coranking_matrix.csv": "310d4e369782a935ee860c0d88212fde7d93333b373e0a9ea2eedb49b71f781d",
    "analysis/governor/candidate_axis/dissimilarity_matrix.csv": "eca6598327c29fa415588f6486141f339e81254469674ffff933b1cca0b4b4d1",
    "analysis/governor/candidate_axis/mds_results.json": "ef2714856d9da7d05f3d86465ffc271609f8642e18384ee4a161f4b206c64273",
    "analysis/governor/candidate_axis/mds_verification.json": "0edc8207bb871379066fc5f55c32d40e909d82bda8336b148a041cd4f89a9de1",
    "analysis/governor/candidate_axis/method_provenance.json": "b6d93269fb506be48ee1a9c58ec10539bace21553323f87caaa99ab6a4c18654",
    "analysis/governor/candidate_axis/null_profiles.json": "5c939c7dea3084d5ef4e9bfb9a56f86f4d30e24c093f82a7fdfe61d5ec2cfd54",
    "analysis/governor/candidate_axis/profile.json": "cd9a477a797bf1af388bfe8dab5f2f4656197c54e553b5d7760816b69344c4dc",
    "analysis/house/candidate_axis/adjacency_matrix.csv": "c5ca0effe14e8979411046a89c122c7165a9431914d90cba1b192871bd3a1c20",
    "analysis/house/candidate_axis/candidate_axis.csv": "74078bb9103d3331fcc7dcf1e9302071a2fc5b51430234aac5bafefab7745b0e",
    "analysis/house/candidate_axis/consistency_summary.csv": "26db70587c0c057e88cdac76ea362e42a936f1336ff6e53ccadfc33e0e4f10ab",
    "analysis/house/candidate_axis/coranking_matrix.csv": "d9f140eefd84106744e09e21135fc2a534429ba0916dc12307bfce0d74079c78",
    "analysis/house/candidate_axis/dissimilarity_matrix.csv": "fccd0d426cfa8959d1dfa4ed2739b15352dbef547c79b61ad2a115ac281c6f8b",
    "analysis/house/candidate_axis/mds_results.json": "5dcde9acd9de965ad7c66859504dbafcf4af671456b789e370a79dab9c283e68",
    "analysis/house/candidate_axis/mds_verification.json": "e3575ca223cf9cfc9c3922a9b37e04061a3ed96028c854a3f07b0782bb8d4090",
    "analysis/house/candidate_axis/method_provenance.json": "9211d3057c13692c9a154728e8b19958954f1b79b8b540dca20c57b20a3dc4fc",
    "analysis/house/candidate_axis/null_profiles.json": "7812e52cc4dea09c5c8cf3afbb665a7ab2e3553edfcedfd102d3052b77249cc2",
    "analysis/house/candidate_axis/profile.json": "7560c93754787d75222d48f26d05f0a5838fd243bee11d38ad64f7c8edc51b61",
    "analysis/senate/candidate_axis/candidate_axis.csv": "ed9a018c4182447a3c5599d9f8f7d3d3304c95fc6da222d3a7c3975d82e6774e",
    "analysis/senate/candidate_axis/carryover_provenance.json": "393e1430d4bcd0c75a3a8c7674539a758f95cbaddbdbf71949a25f32327d26db",
    "analysis/senate/candidate_axis/consistency_summary.csv": "68b7f08ec97c00b155c7845a73494fcc9922439c6e37418fef86d3e365f21a3e",
    "analysis/senate/candidate_axis/dissimilarity_matrix.csv": "cea7e7c5e961016bb77b81130f1350f82af1e18b2cf5764ac23cbb9d0a810166",
    "analysis/senate/candidate_axis/mds_results.json": "903c3b99a456be4b479d90918401a8c3eda2ccd6d457d23e19e74e50171f28be",
    "analysis/senate/candidate_axis/mds_verification.json": "0d49a714b06275cfff020d748781d81a51b259624586498ef736cbd96c053879",
    "analysis/senate/candidate_axis/method_provenance.json": "edc7b3666b008420a53e54b3ad15ae2a3515d29942cba91eb37cbb48d1bba871",
    "analysis/senate/candidate_axis/profile.json": "ad670cead53acf886f275ddc943e151d15f61edcbc9bc4848a7c01e0fdfb1031",
    "analysis/senate/candidate_axis/rachel_profile_provenance.json": "82d420b13fafc06be53584b8cbdb6b4c59463ab7f11f7b1b4a638af5a7712a56",
    "analysis/cross_race/validation/axes/independent_axis_audit.json": "4bf81acc8086db16d830ec62ff991b433a0482d2581f35a358b91f30fa37bc3e",
    "analysis/cross_race/validation/axes/new_contests_consistency.csv": "bcf493957787a592cd9936accbb9891acd10d38e42ca166caf61e2d53d8eb598",
}


def load_json(path):
    return json.loads(path.read_text())


def profile_counts(rows):
    """Reject duplicate patterns instead of silently merging saved records."""
    profile = {}
    for row in rows:
        ranking, weight = tuple(row["ranking"]), row["count"]
        if ranking in profile:
            raise AssertionError(f"Duplicate saved ranking: {ranking}")
        if not isinstance(weight, int) or isinstance(weight, bool) or weight < 0:
            raise AssertionError(f"Invalid saved count: {weight}")
        if len(ranking) != len(set(ranking)) or any(
                type(candidate) is not int or candidate not in range(4)
                for candidate in ranking):
            raise AssertionError(f"Invalid saved ranking: {ranking}")
        profile[ranking] = weight
    return profile


def compatible(ranking, axis):
    """Independently intersect all pairwise strict-distance half-spaces."""
    lower, upper = 0., 1.
    for i, first in enumerate(ranking):
        for second in ranking[i + 1:]:
            a, b = axis[first], axis[second]
            if a == b:
                return False
            midpoint = (a + b) / 2
            if a < b:
                upper = min(upper, midpoint)
            else:
                lower = max(lower, midpoint)
    return upper - lower > 1e-12


def scores(profile, axis):
    totals, consistent = Counter(), Counter()
    for ranking, weight in profile.items():
        if not ranking:
            continue
        length = len(ranking)
        totals[length] += weight
        if compatible(ranking, axis):
            consistent[length] += weight
    nonempty = sum(totals.values())
    informative = sum(n for length, n in totals.items() if length >= 3)
    return {
        "ballots": nonempty,
        "empty_ballots": profile.get((), 0),
        "informative_ballots": informative,
        "gamma": sum(consistent.values()) / nonempty,
        "gamma_informative": sum(n for length, n in consistent.items()
                                 if length >= 3) / informative,
        "by_length": {length: {"ballots": count,
                               "consistent": consistent[length],
                               "gamma": consistent[length] / count}
                      for length, count in totals.items()},
    }


def first_choice_length_margin(profile):
    counts = Counter()
    for ranking, weight in profile.items():
        counts[(ranking[0] if ranking else None), len(ranking)] += weight
    return counts


def read_matrix(path):
    with path.open(newline="") as stream:
        reader = csv.reader(stream)
        next(reader)
        return [[float(value) for value in row[1:]] for row in reader]


class SavedResultChecks(unittest.TestCase):
    def load_race(self, race):
        folder = ROOT / "analysis" / race / "candidate_axis"
        profile = load_json(folder / "profile.json")
        return folder, profile, load_json(folder / "mds_results.json")

    def assert_score(self, profile, axis, stored):
        independent = scores(profile, axis)
        for key in ("ballots", "empty_ballots", "informative_ballots",
                    "gamma", "gamma_informative"):
            self.assertEqual(independent[key], stored[key], key)
        self.assertEqual(set(independent["by_length"]),
                         {row["length"] for row in stored["by_length"]})
        for row in stored["by_length"]:
            for key in ("ballots", "consistent", "gamma"):
                self.assertEqual(independent["by_length"][row["length"]][key],
                                 row[key], (row["length"], key))

    def test_all_saved_artifacts_unchanged(self):
        for relative, expected in SAVED_SHA256.items():
            with self.subTest(path=relative):
                self.assertEqual(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(),
                                 expected)
        core = ROOT / "analysis/shared/og_axis.py"
        self.assertEqual(hashlib.sha256(core.read_bytes()).hexdigest(), CORE_SHA256)

    def test_observed_profiles_totals_and_scores(self):
        for race in RACES:
            with self.subTest(race=race):
                _, source, result = self.load_race(race)
                profile = profile_counts(source["ballots"])
                self.assertEqual(result["status"], "complete")
                self.assertEqual(sum(profile.values()), source["source_rows"])
                self.assertEqual(source["source_rows"], result["source_rows"])
                for key in ("candidate_ids", "source_filename", "source_sha256"):
                    self.assertEqual(source[key], result[key], key)
                self.assertEqual(len(result["null"]), 49)
                self.assertEqual(result["null_draws"], 49)
                self.assertEqual(result["environment"]["sklearn"], "1.6.1")
                self.assert_score(profile, result["axis"], result["observed"])

    def test_pair_matrices_rederived_independently(self):
        for race in RACES:
            with self.subTest(race=race):
                folder, source, _ = self.load_race(race)
                profile = profile_counts(source["ballots"])
                adjacent = [[0] * 4 for _ in range(4)]
                together = [[0] * 4 for _ in range(4)]
                for ranking, weight in profile.items():
                    for a, b in zip(ranking, ranking[1:]):
                        adjacent[a][b] += weight
                    for a in ranking:
                        for b in ranking:
                            together[a][b] += weight
                frequencies = [[adjacent[a][b] / together[a][b]
                                if together[a][b] else 0.
                                for b in range(4)] for a in range(4)]
                symmetric = [[(frequencies[a][b] + frequencies[b][a]) / 2
                              for b in range(4)] for a in range(4)]
                fallback = 2 / min(value for row in symmetric
                                   for value in row if value > 0)
                distance = [[0. if a == b else
                             (1 / math.sqrt(symmetric[a][b])
                              if symmetric[a][b] > 0 else fallback)
                             for b in range(4)] for a in range(4)]
                self.assertEqual(read_matrix(folder / "dissimilarity_matrix.csv"), distance)
                for filename, expected in (("adjacency_matrix.csv", adjacent),
                                           ("coranking_matrix.csv", together)):
                    if race != "senate":  # These two Senate matrices were not packaged.
                        self.assertEqual(read_matrix(folder / filename), expected)

    def test_saved_candidate_csv_and_display_reflection(self):
        for race in RACES:
            with self.subTest(race=race):
                folder, source, result = self.load_race(race)
                with (folder / "candidate_axis.csv").open(newline="") as stream:
                    rows = list(csv.DictReader(stream))
                self.assertEqual(len(rows), 4)
                by_id = {int(row["candidate_id"]): row for row in rows}
                self.assertEqual(set(by_id), set(result["candidate_ids"]))
                display = result.get("display_axis", result["axis"])
                expected = ([1 - x for x in result["axis"]]
                            if result.get("display_reflected") else result["axis"])
                self.assertEqual(display, expected)
                for candidate, raw, shown in zip(result["candidate_ids"],
                                                  result["axis"], display):
                    self.assertEqual(float(by_id[candidate]["axis_position"]), raw)
                    self.assertEqual(float(by_id[candidate]["display_axis_position"]), shown)
                self.assert_score(profile_counts(source["ballots"]), display, result["observed"])

    def test_house_and_governor_all_saved_null_scores_and_margins(self):
        # Senate's historical null profiles are not packaged. We do not pretend
        # that checking its saved mean independently reconstructs its 49 scores.
        for race in ("house", "governor"):
            folder, source, result = self.load_race(race)
            original = profile_counts(source["ballots"])
            draws = load_json(folder / "null_profiles.json")["draws"]
            self.assertEqual(len(draws), 49)
            self.assertEqual([row["draw"] for row in draws], list(range(49)))
            for draw, stored in zip(draws, result["null"]):
                with self.subTest(race=race, draw=draw["draw"]):
                    self.assertEqual(draw["draw"], stored["draw"])
                    randomized = profile_counts(draw["rankings"])
                    self.assertEqual(first_choice_length_margin(randomized),
                                     first_choice_length_margin(original))
                    self.assert_score(randomized, stored["axis"], stored)

    def test_all_saved_null_means_and_comparison_arithmetic(self):
        for race in RACES:
            _, _, result = self.load_race(race)
            for index, key in ((0, "gamma"), (1, "gamma_informative")):
                with self.subTest(race=race, group=key):
                    summary = result["summary"][index]
                    values = [draw[key] for draw in result["null"]]
                    mean = statistics.mean(values)
                    self.assertAlmostEqual(summary["random_mean"], mean, places=14)
                    self.assertEqual(summary["observed_consistency"], result["observed"][key])
                    self.assertAlmostEqual(summary["excess_percentage_points"],
                                           100 * (result["observed"][key] - mean), places=12)
                    self.assertAlmostEqual(summary["random_sd"], statistics.stdev(values), places=14)
                    self.assertAlmostEqual(summary["random_mcse"],
                                           statistics.stdev(values) / math.sqrt(49), places=14)
                    self.assertEqual(summary["random_draws"], 49)

    def test_senate_and_shared_rules_all_allowed_five_rank_patterns(self):
        from analysis.shared import data
        from analysis.senate.candidate_axis import ranking_rules

        tokens = list(ranking_rules.NAME_TO_INTERNAL_ID) + ["skipped", "overvote"]
        checked = 0
        for pattern in itertools.product(tokens, repeat=5):
            old_names, old_reason, old_barrier = ranking_rules.interpret_tokens(pattern)
            names, reason, barrier = data.countable_tokens(pattern)
            internal = [ranking_rules.NAME_TO_INTERNAL_ID[name] for name in names]
            self.assertEqual((internal, reason, barrier),
                             (old_names, old_reason, old_barrier), pattern)
            checked += 1
        self.assertEqual(checked, 16807)


if __name__ == "__main__":
    unittest.main()
