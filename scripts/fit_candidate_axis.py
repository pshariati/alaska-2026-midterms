"""Run the preserved Alaska 1D method on an explicit weighted JSON profile."""
from pathlib import Path
from collections import Counter
import argparse
import hashlib
import json
import platform
import sys

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / 'analysis/shared/og_axis.py'


def read_profile(path):
    data = json.loads(path.read_text())
    names = data['candidates']
    if len(names) < 2 or len(set(names)) != len(names):
        raise ValueError('At least two distinct candidate names are required.')
    ballots = Counter()
    for row in data['ballots']:
        ranking, count = tuple(row['ranking']), row['count']
        if type(count) is not int or count < 0:
            raise ValueError('Counts must be nonnegative integers.')
        if len(set(ranking)) != len(ranking) or any(
            type(c) is not int or not 0 <= c < len(names) for c in ranking
        ):
            raise ValueError('Rankings must contain distinct valid zero-based candidate indices.')
        ballots[ranking] += count
    if not sum(ballots.values()):
        raise ValueError('Profile is empty.')
    return names, dict(ballots)


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--seed', type=int, default=20261112)
    p.add_argument('--null-draws', type=int, default=49)
    p.add_argument('--runs', type=int, default=20)
    p.add_argument('--initializations', type=int, default=8)
    p.add_argument('--max-iter', type=int, default=1000)
    p.add_argument('--eps', type=float, default=1e-6)
    p.add_argument('--allow-different-environment', action='store_true',
                   help='Explicitly label results from a non-historical numerical environment.')
    return p


def main():
    args = parser().parse_args()
    if args.null_draws < 0:
        raise ValueError('null-draws must be nonnegative.')
    if args.output.exists():
        raise FileExistsError('Choose a new output path; existing results are preserved.')
    names, ballots = read_profile(args.profile)
    import numpy as np
    import scipy
    import sklearn
    environment = {'python': platform.python_version(), 'numpy': np.__version__,
                   'scipy': scipy.__version__, 'sklearn': sklearn.__version__}
    historical = (np.__version__ == '2.0.2' and scipy.__version__ == '1.13.1'
                  and sklearn.__version__ == '1.6.1')
    if not historical and not args.allow_different_environment:
        raise RuntimeError('Numerical versions differ from the historical fits. '
                           'Use the documented environment or explicitly label this '
                           'comparison with --allow-different-environment.')
    sys.path.insert(0, str(CORE.parent))
    from og_axis import FitConfig, fit_axis, summarize, matched_null, seed_for
    config = FitConfig(args.runs, args.initializations, args.max_iter, args.eps)
    axis, diagnostics = fit_axis(ballots, len(names), seed_for(args.seed, 'portable', 'observed'), config)
    null = []
    for draw in range(args.null_draws):
        profile = matched_null(ballots, len(names), seed_for(args.seed, 'portable', 'null', draw))
        coords, diag = fit_axis(profile, len(names), seed_for(args.seed, 'portable', 'null-fit', draw), config)
        null.append({'draw': draw, 'axis': coords.tolist(), 'diagnostics': diag,
                     'summary': summarize(profile, coords)})
    result = {'candidates': names, 'axis': axis.tolist(), 'diagnostics': diagnostics,
              'observed': summarize(ballots, axis), 'null': null,
              'environment': environment, 'historical_numerical_versions': historical,
              'source_sha256': hashlib.sha256(args.profile.read_bytes()).hexdigest(),
              'core_sha256': hashlib.sha256(CORE.read_bytes()).hexdigest(),
              'seed': args.seed, 'seed_protocol': 'seed_for(seed, portable, observed/null/null-fit[,draw])',
              'note': 'Historical solver has documented nonmetric-MDS issues; see docs/KNOWN_ISSUES.md. '
                      'This portable seed protocol differs from the archived contest-specific drivers.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print('Wrote', args.output)


if __name__ == '__main__':
    main()
