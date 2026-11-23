"""Independently verify both finalists' routes in the fixed Dan J.-first cohort."""
from pathlib import Path
from collections import Counter
import csv
import datetime
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
J = 'Sullivan, Daniel J. Jr.'
S = 'Sullivan, Dan S.'
P = 'Peltola, Mary'
H = 'Heikes, Gerald L.'
LABEL = {P: 'Peltola', S: 'Daniel S.', H: 'Heikes', None: 'Inactive'}


def main():
    path = ROOT/'inputs/Alaska_20261103_US_Senate_11_11.csv'
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == '3f0a1a946f23d2d1195f98c5ee5f123916d5f91ede334397465692d5e7f2d972'
    routes = Counter()
    patterns = Counter()
    for row in csv.DictReader(path.open(encoding='utf-8-sig', newline='')):
        tokens = tuple(row[f'rank{i}'] for i in range(1, 6))
        if tokens[0] != J:
            continue
        last = max(i for i, token in enumerate(tokens) if token != 'skipped')
        barriers = [i for i, token in enumerate(tokens) if token == 'overvote']
        barriers += [i for i in range(4)
                     if tokens[i] == tokens[i+1] == 'skipped' and i+1 < last]
        stop = min(barriers, default=5)
        prefix = tuple(dict.fromkeys(x for x in tokens[:stop]
                                     if x not in {'skipped', 'overvote'}))
        patterns[tuple(x for x in prefix if x != 'Write-in')] += 1
        after_j = next((x for x in prefix if x in {P, S, H}), None)
        final = next((x for x in prefix if x in {P, S}), None)
        routes[after_j, final] += 1
    assert sum(routes.values()) == 3940
    assert routes == {(P, P): 1147, (H, P): 186, (S, S): 638,
                      (H, S): 266, (None, None): 1447, (H, None): 256}
    ids = {J: 526, S: 527, P: 525, H: 524}
    saved = {tuple(json.loads(r['candidate_ids_json'])): int(r['literal_rank1_daniel_ballots'])
             for r in csv.DictReader((ROOT/'confusion/daniel_first_usable_permutations.csv').open(newline=''))}
    assert {tuple(ids[x] for x in p): n for p, n in patterns.items()} == saved
    summaries = [{
        'final_destination': LABEL[dest],
        'direct_after_Dan_J_elimination': routes[dest, dest],
        'via_Heikes': routes[H, dest],
        'total': routes[dest, dest] + routes[H, dest],
        'cohort_n': 3940,
        'pct_of_full_cohort': 100*(routes[dest, dest]+routes[H, dest])/3940,
    } for dest in [P, S, None]]
    assert [r['total'] for r in summaries] == [1333, 904, 1703]
    target = ROOT/'confusion/dan_j_first_finalist_routes.csv'
    with target.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(summaries[0]))
        writer.writeheader()
        writer.writerows(summaries)
    result = {
        'status': 'passed', 'source_filename': path.name, 'source_sha256': digest,
        'checked_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'cohort': 'Literal recorded Dan J. Senate rank 1', 'cohort_n': 3940,
        'method': 'Independent earliest-barrier source parser; allocation with Peltola, Daniel S. and Heikes continuing, then Peltola/Daniel S. continuing. Generic write-in occupancy retained before exclusion.',
        'interpretation': 'Hypothetical snapshot replay; rankings do not identify confusion or intent.',
        'routes': summaries, 'all_16_saved_permutations_agree': True,
    }
    (ROOT/'validation/peltola_route_verification.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
    return result


if __name__ == '__main__':
    main()
