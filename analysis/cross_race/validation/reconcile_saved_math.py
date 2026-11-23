"""Read-only reconciliation of saved profiles and fitted-axis outputs; no fits."""
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from analysis.shared.paths import REPO_ROOT, INPUTS_ROOT, REFERENCES_ROOT, SHARED_ROOT, race_dir, model_dir, cross_race_dir, resolve_recorded_path

HERE = Path(__file__).resolve().parent
PROJECT = REPO_ROOT
ROOT = REPO_ROOT
TOL = 1e-12


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_matrix(path, names):
    with path.open(newline='') as f:
        rows = list(csv.reader(f))
    assert rows[0][1:] == names
    assert [row[0] for row in rows[1:]] == names
    return [[float(x) for x in row[1:]] for row in rows[1:]]


def compatible(ranking, axis):
    # Independent midpoint-cell sweep; not the notebook's interval recursion.
    if len(ranking) < 2:
        return bool(ranking)
    cuts = sorted(set([0.0, 1.0] + [
        (axis[i] + axis[j]) / 2 for i in range(len(axis)) for j in range(i)
    ]))
    for left, right in zip(cuts, cuts[1:]):
        if right - left <= TOL:
            continue
        u = (left + right) / 2
        d = [abs(u - axis[c]) for c in ranking]
        if all(a < b for a, b in zip(d, d[1:])):
            return True
    return False


report = {
    'scope': 'Read-only arithmetic reconciliation of saved profiles, matrices, fitted axes and summaries. No ballot reinterpretation, axis refit, new randomized data, or source modification.',
    'method': 'Python standard library; direct weighted loops for C/A/F/S/D and independent midpoint-cell sweep for gamma.',
    'tolerance': TOL,
    'races': {},
}
for slug in ['us_senate', 'governor', 'us_house']:
    folder = model_dir(slug)
    profile_path = folder / 'profile.json'
    result_path = folder / 'mds_results.json'
    profile = json.loads(profile_path.read_text())
    result = json.loads(result_path.read_text())
    names = profile['candidates']
    n = len(names)
    c = [[0] * n for _ in range(n)]
    a = [[0] * n for _ in range(n)]
    bylength = Counter()
    goodlength = Counter()
    axis = result.get('display_axis', result['axis'])
    source_total = empty = 0
    for row in profile['ballots']:
        ranking, w = row['ranking'], row['count']
        source_total += w
        if not ranking:
            empty += w
            continue
        bylength[len(ranking)] += w
        goodlength[len(ranking)] += w * compatible(ranking, axis)
        for i in ranking:
            for j in ranking:
                c[i][j] += w
        for i, j in zip(ranking, ranking[1:]):
            a[i][j] += w
    f = [[a[i][j] / c[i][j] if c[i][j] else 0.0 for j in range(n)] for i in range(n)]
    s = [[(f[i][j] + f[j][i]) / 2 for j in range(n)] for i in range(n)]
    positive = [x for row in s for x in row if x > 0]
    fallback = 2 / min(positive)
    d = [[0.0 if i == j else 1 / math.sqrt(s[i][j]) if s[i][j] > 0 else fallback
          for j in range(n)] for i in range(n)]
    matrices = {'adjacency_matrix.csv': a, 'coranking_matrix.csv': c, 'dissimilarity_matrix.csv': d}
    comparison = {}
    mismatches = []
    for filename, reconstructed in matrices.items():
        path = folder / filename
        if not path.exists():
            comparison[filename] = {'status': 'not_saved', 'note': 'No saved standalone matrix to compare; independently reconstructed matrix retained below.'}
            continue
        saved = read_matrix(path, names)
        errors = [abs(saved[i][j] - reconstructed[i][j]) for i in range(n) for j in range(n)]
        mismatch_count = sum(error > TOL for error in errors)
        comparison[filename] = {'entries_checked': n*n, 'mismatches': mismatch_count, 'max_absolute_error': max(errors), 'sha256': sha(path)}
        if mismatch_count:
            mismatches.append(filename)
    obs = result['observed']
    nonempty = sum(bylength.values())
    consistent = sum(goodlength.values())
    informative = sum(w for length, w in bylength.items() if length >= 3)
    informative_good = sum(w for length, w in goodlength.items() if length >= 3)
    gamma = consistent / nonempty
    gamma3 = informative_good / informative
    checks = {
        'source_rows': source_total == result['source_rows'],
        'empty_ballots': empty == obs['empty_ballots'],
        'nonempty_ballots': nonempty == obs['ballots'],
        'informative_ballots': informative == obs['informative_ballots'],
        'gamma_all': abs(gamma - obs['gamma']) <= TOL,
        'gamma_three_four': abs(gamma3 - obs['gamma_informative']) <= TOL,
    }
    for row in obs['by_length']:
        length = row['length']
        checks[f'length_{length}_N'] = bylength[length] == row['ballots']
        checks[f'length_{length}_consistent'] = goodlength[length] == row['consistent']
        checks[f'length_{length}_gamma'] = abs(goodlength[length]/bylength[length] - row['gamma']) <= TOL
    nulls = result['null']
    assert len(nulls) == 49
    with (folder / 'consistency_summary.csv').open(newline='') as ff:
        summary = list(csv.DictReader(ff))
    for label, field, denominator, observed in [
        ('All nonempty', 'gamma', nonempty, gamma),
        ('Three or four named ranks', 'gamma_informative', informative, gamma3),
    ]:
        saved = next(row for row in summary if row['group'] == label)
        mean = sum(row[field] for row in nulls) / len(nulls)
        checks[label + '_summary_N'] = int(saved['ballots']) == denominator
        checks[label + '_summary_observed'] = abs(float(saved['observed_consistency'])-observed) <= TOL
        checks[label + '_summary_random_mean'] = abs(float(saved['random_mean'])-mean) <= TOL
    assert all(checks.values()), checks
    assert not mismatches, mismatches
    report['races'][slug] = {
        'profile_sha256': sha(profile_path), 'result_sha256': sha(result_path),
        'candidate_ids': profile['candidate_ids'], 'candidate_names': names,
        'source_rows': source_total, 'empty_named_rankings': empty,
        'nonempty_N': nonempty, 'nonempty_consistent': consistent, 'nonempty_gamma': gamma,
        'three_four_N': informative, 'three_four_consistent': informative_good, 'three_four_gamma': gamma3,
        'random_mean_all': sum(row['gamma'] for row in nulls)/len(nulls),
        'random_mean_three_four': sum(row['gamma_informative'] for row in nulls)/len(nulls),
        'random_draws': len(nulls), 'sklearn_version': result['environment']['sklearn'],
        'checks': checks, 'check_failures': sum(not x for x in checks.values()),
        'matrix_comparisons': comparison,
        'zero_similarity_offdiagonal_ordered_pairs': sum(s[i][j] == 0 for i in range(n) for j in range(n) if i != j),
        'zero_similarity_offdiagonal_unordered_pairs': sum(s[i][j] == 0 for i in range(n) for j in range(i)),
        'smallest_positive_similarity': min(positive),
        'zero_similarity_fallback_value': fallback,
        'reconstructed_C': c, 'reconstructed_A': a, 'reconstructed_F': f, 'reconstructed_S': s, 'reconstructed_D': d,
    }
report['total_saved_matrix_entries_checked'] = sum(x.get('entries_checked', 0) for race in report['races'].values() for x in race['matrix_comparisons'].values())
report['total_saved_matrix_mismatches'] = sum(x.get('mismatches', 0) for race in report['races'].values() for x in race['matrix_comparisons'].values())
report['total_summary_check_failures'] = sum(race['check_failures'] for race in report['races'].values())
out = HERE / 'saved_math_reconciliation.json'
out.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
print(json.dumps({key: report[key] for key in ['total_saved_matrix_entries_checked','total_saved_matrix_mismatches','total_summary_check_failures']}))
for slug, race in report['races'].items():
    print(slug, {key: race[key] for key in ['nonempty_N','nonempty_consistent','nonempty_gamma','three_four_N','three_four_consistent','three_four_gamma','zero_similarity_offdiagonal_unordered_pairs']} )
