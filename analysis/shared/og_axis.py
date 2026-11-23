"""Weighted RCV analysis. Rankings constrain only candidates explicitly ranked.

No inference about voter knowledge, sincerity, strategy or unranked preferences.
"""
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from itertools import permutations
from math import perm
import hashlib
import numpy as np
from sklearn.manifold import MDS

VERSION = "rcv-corrected-2"
TOL = 1e-12


@dataclass(frozen=True)
class FitConfig:
    n_runs: int = 10
    n_init: int = 8
    max_iter: int = 1000
    eps: float = 1e-6


def seed_for(*parts):
    return int.from_bytes(hashlib.sha256("|".join(map(str, parts)).encode()).digest()[:4], "little")


def validate_profile(ballots, n):
    if n < 1:
        raise ValueError("Empty candidate list")
    for b, w in ballots.items():
        if type(w) is not int or w < 0:
            raise ValueError("Ballot weights must be nonnegative integers")
        if len(set(b)) != len(b) or any(type(c) is not int or not 0 <= c < n for c in b):
            raise ValueError("Repeated or unknown candidate")


def blocks(ballots):
    grouped = defaultdict(list)
    for b, w in ballots.items():
        if w and b:
            grouped[len(b)].append((b, w))
    for m in sorted(grouped):
        rows = sorted(grouped[m])
        yield m, np.array([b for b, _ in rows], dtype=int), np.array([w for _, w in rows], dtype=np.int64)


def pair_matrices(ballots, n):
    validate_profile(ballots, n)
    adjacent = np.zeros((n, n), dtype=float)
    together = np.zeros((n, n), dtype=float)
    for m, b, w in blocks(ballots):
        for i in range(m):
            for j in range(m):
                np.add.at(together, (b[:, i], b[:, j]), w)
            if i + 1 < m:
                np.add.at(adjacent, (b[:, i], b[:, i+1]), w)
    return adjacent, together


def dissimilarity(ballots, n):
    adjacent, together = pair_matrices(ballots, n)
    freq = np.divide(adjacent, together, out=np.zeros_like(adjacent), where=together > 0)
    symmetric = (freq + freq.T) / 2
    positive = symmetric[symmetric > 0]
    if not len(positive):
        raise ValueError("No adjacent candidate pairs; cannot estimate an axis")
    # Retain upstream's substitution rule, correcting only candidate indexing.
    dist = np.full_like(symmetric, 2 / positive.min())
    np.divide(1, np.sqrt(symmetric), out=dist, where=symmetric > 0)
    np.fill_diagonal(dist, 0)
    return dist


def fit_axis(ballots, n, seed, config=FitConfig()):
    if min(config.n_runs, config.n_init, config.max_iter) < 1:
        raise ValueError("Fit budgets must be positive")
    dist = dissimilarity(ballots, n)
    groups = defaultdict(list)
    all_stress = []
    discarded = 0
    for run in range(config.n_runs):
        model = MDS(n_components=1, metric=False, dissimilarity="precomputed",
                    n_init=config.n_init, max_iter=config.max_iter, eps=config.eps,
                    normalized_stress=True, random_state=seed_for(seed, run), n_jobs=1)
        coords = model.fit_transform(dist).ravel()
        coords -= coords.mean()
        # A coincident candidate pair cannot represent strict preferences.
        # Discard this solution, without extra attempts or arbitrary jitter.
        if (not np.all(np.isfinite(coords)) or np.ptp(coords) <= TOL
                or np.min(np.diff(np.sort(coords))) / np.ptp(coords) <= TOL):
            discarded += 1
            continue
        order = tuple(map(int, np.argsort(coords, kind="stable")))
        reverse = order[::-1]
        if reverse < order:
            coords = -coords
            order = reverse
        groups[order].append((coords, float(model.stress_), int(model.n_iter_)))
        all_stress.append(float(model.stress_))
    # Same modal-order rule as upstream, with deterministic ties and aligned mirrors.
    if not groups:
        raise ValueError("All MDS solutions had coincident candidate positions")
    order = min(groups, key=lambda o: (-len(groups[o]), np.mean([r[1] for r in groups[o]]), o))
    chosen = groups[order]
    coords = np.mean([r[0] for r in chosen], axis=0)
    if np.ptp(coords) <= TOL:
        raise ValueError("Collapsed MDS axis")
    coords = (coords - coords.min()) / np.ptp(coords)
    validate_axis(coords)
    return coords, {"modal_order_share": len(chosen)/config.n_runs,
                    "valid_runs": config.n_runs-discarded, "discarded_coincident_runs": discarded,
                    "distinct_orders": len(groups), "modal_order": list(order),
                    "mean_modal_stress": float(np.mean([r[1] for r in chosen])),
                    "min_stress": min(all_stress),
                    "max_iter_hits_selected": sum(r[2] >= config.max_iter for r in chosen),
                    "settings": asdict(config)}


def validate_axis(axis):
    axis = np.asarray(axis, dtype=float)
    if len(axis) < 2 or not np.all(np.isfinite(axis)) or np.ptp(axis) <= TOL:
        raise ValueError("Invalid axis")
    if np.min(np.diff(np.sort(axis))) <= TOL:
        raise ValueError("Coincident candidate positions; strict rankings undefined")
    return (axis - axis.min()) / np.ptp(axis)


def matched_null(ballots, n, seed):
    """Exact first-choice x length margins; independent uniform distinct tails."""
    validate_profile(ballots, n)
    rng = np.random.default_rng(seed)
    strata = Counter()
    result = Counter()
    for b, w in ballots.items():
        if b:
            strata[b[0], len(b)] += w
        elif w:
            result[()] += w
    for (first, m), count in sorted(strata.items()):
        if not count:
            continue
        if m == 1:
            result[(first,)] += count
            continue
        others = np.array([i for i in range(n) if i != first])
        possibilities = perm(n-1, m-1)
        if possibilities <= 20000:
            weights = rng.multinomial(count, np.full(possibilities, 1/possibilities))
            for tail, w in zip(permutations(map(int, others), m-1), weights):
                if w:
                    result[(first,) + tail] += int(w)
        else:
            for start in range(0, count, 30000):
                size = min(30000, count-start)
                # IID continuous priorities give uniform ordered sampling without replacement.
                priority = rng.random((size, n-1))
                order = np.argsort(priority, axis=1)[:, :m-1]
                tails, weights = np.unique(others[order], axis=0, return_counts=True)
                for tail, w in zip(tails, weights):
                    result[(first,) + tuple(map(int, tail))] += int(w)
    return dict(result)


def prefix_flags(positions):
    """For each row, feasibility after each new rank; positive-width strict interval."""
    p = np.asarray(positions)
    count, m = p.shape
    flags = np.ones((count, m), dtype=bool)
    lo, hi = np.zeros(count), np.ones(count)
    for j in range(1, m):
        a, b = p[:, j-1], p[:, j]
        mid = (a+b)/2
        lo = np.maximum(lo, np.where(a > b, mid, 0))
        hi = np.minimum(hi, np.where(a < b, mid, 1))
        flags[:, j] = flags[:, j-1] & (a != b) & (hi-lo > TOL)
    return flags


def swap_distances(positions):
    """Exact minimum adjacent swaps, using a sweep through pairwise midpoints.

    Every crossing reverses that pair's distance order. Coincident crossings
    are applied together: tie-only rankings are never counted as feasible.
    """
    p = np.asarray(positions)
    rows, m = p.shape
    if m <= 2:
        return np.zeros(rows, dtype=int)
    i, j = np.triu_indices(m, 1)
    mids = (p[:, i] + p[:, j])/2
    delta = np.where(p[:, i] < p[:, j], 1, -1)
    order = np.argsort(mids, axis=1, kind="stable")
    mids = np.take_along_axis(mids, order, axis=1)
    delta = np.take_along_axis(delta, order, axis=1)
    initial = np.sum(p[:, i] > p[:, j], axis=1)
    distances = np.column_stack((initial, initial[:, None] + np.cumsum(delta, axis=1)))
    bounds = np.column_stack((np.zeros(rows), mids, np.ones(rows)))
    valid = np.diff(bounds, axis=1) > TOL
    return np.min(np.where(valid, distances, m*m), axis=1).astype(int)


def summarize(ballots, axis):
    axis = validate_axis(axis)
    validate_profile(ballots, len(axis))
    by_length, prefixes = [], []
    total, consistent, informative, informative_consistent = 0, 0, 0, 0
    for m, b, w in blocks(ballots):
        p = axis[b]
        flags = prefix_flags(p)
        d = swap_distances(p)
        if not np.array_equal(d == 0, flags[:, -1]):
            raise AssertionError("Consistency and exact swap distance disagree")
        n = int(w.sum())
        good = int(w[flags[:, -1]].sum())
        hist = {str(int(k)): int(w[d == k].sum()) for k in np.unique(d)}
        swaps = int(np.dot(w, d))
        row = {"length": m, "ballots": n, "consistent": good, "gamma": good/n,
               "swap_histogram": hist, "mean_swaps": swaps/n,
               "mean_swaps_inconsistent": swaps/(n-good) if n > good else None,
               "mean_swaps_pair_normalized": swaps/n/(m*(m-1)/2) if m >= 2 else 0}
        by_length.append(row)
        for k in range(3, m+1):
            g = int(w[flags[:, k-1]].sum())
            prefixes.append({"cohort_length": m, "prefix_length": k, "ballots": n,
                             "consistent": g, "gamma": g/n})
        total += n
        consistent += good
        if m >= 3:
            informative += n
            informative_consistent += good
    return {"ballots": total, "empty_ballots": ballots.get((), 0),
            "informative_ballots": informative, "gamma": consistent/total if total else None,
            "gamma_informative": informative_consistent/informative if informative else None,
            "by_length": by_length, "prefixes": prefixes}
