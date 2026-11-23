"""Independent source-row audit of the focused Hafner analysis.

No producer parser or replay code is imported. The prefix oracle uses the
earliest marked barrier, preserving write-in rank occupancy before exclusion.
"""
from pathlib import Path
from collections import Counter, defaultdict
import csv
import datetime
import gzip
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
HAFNER = 'Hafner, Eric'
BEGICH = 'Begich, Nick'
HILL = 'Hill, Bill'
MCDERMOTT = 'McDermott, James C. "Jim"'
HOUSE_NAMES = {HAFNER, BEGICH, HILL, MCDERMOTT}
SOURCES = {
    'us_house': ('Alaska_20261103_US_House_11_11.csv',
                 'b57fad2ef5a8845ba5b3da1eeb3c5e7cfb036c1c174af640b3acee65e45f8b48',
                 244705, HOUSE_NAMES),
    'us_senate': ('Alaska_20261103_US_Senate_11_11.csv',
                  '3f0a1a946f23d2d1195f98c5ee5f123916d5f91ede334397465692d5e7f2d972',
                  244705, {'Peltola, Mary', 'Sullivan, Dan S.',
                           'Sullivan, Daniel J. Jr.', 'Heikes, Gerald L.'}),
    'governor': ('Alaska_20261103_US_Governor_11_11.csv',
                 '3d76cd612870025d9c470f78a60d0bde0cd274aeb9a4e57d575704b588f4b8b3',
                 244575, {'Bronson/Church', 'Kreiss-Tomkins/Johnson',
                          'Taylor/English', 'Wilson/Shower'}),
}


def normalize_id(value):
    match = re.fullmatch(r'([0-9]+)_([0-9]+)_([0-9]+)_?', value)
    assert match, value
    return ':'.join(str(int(x)) for x in match.groups())


def prefix_oracle(tokens):
    last = max((i for i, x in enumerate(tokens) if x != 'skipped'), default=-1)
    barriers = [(i, 'overvote') for i, x in enumerate(tokens) if x == 'overvote']
    barriers += [(i, 'two_consecutive_skips') for i in range(len(tokens)-1)
                 if tokens[i] == tokens[i+1] == 'skipped' and i+1 < last]
    stop, reason = min(barriers, default=(len(tokens),
                        'blank' if last < 0 else 'end_of_ranks'))
    pref = tuple(dict.fromkeys(x for x in tokens[:stop]
                              if x not in {'skipped', 'overvote'}))
    # Exclusion starts at the first blank; the barrier is reached at the second.
    rank = stop+2 if reason == 'two_consecutive_skips' else stop+1
    return pref, reason, (rank if barriers else None)


def read_source(slug):
    filename, expected_hash, expected_n, names = SOURCES[slug]
    path = ROOT/'inputs'/filename
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == expected_hash, filename
    rows = {}
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        assert len(reader.fieldnames) == 15
        assert all('rank'+str(i) in reader.fieldnames for i in range(1, 6))
        for source_index, row in enumerate(reader):
            uid = normalize_id(row['ballotID'])
            assert uid not in rows, uid
            tokens = tuple(row['rank'+str(i)] for i in range(1, 6))
            assert set(tokens) <= names | {'Write-in', 'skipped', 'overvote'}
            pref, reason, barrier_rank = prefix_oracle(tokens)
            rows[uid] = {'source_index': source_index, 'tokens': tokens,
                         'pref': pref, 'reason': reason, 'barrier_rank': barrier_rank,
                         'named': tuple(x for x in pref if x != 'Write-in')}
            if slug == 'us_house':
                rows[uid]['precinct'] = row['precinct']
                rows[uid]['counting_group'] = row['countingGroup']
                if tokens[0] == HAFNER:
                    rows[uid]['original_source_row'] = row
    assert len(rows) == expected_n
    return rows, {'filename': filename, 'sha256': digest,
                  'rows': len(rows), 'unique_normalized_ids': len(rows)}


def allocation(pref, continuing):
    return next((x for x in pref if x in continuing), 'Inactive')


def replay_house(rows, literal):
    profile = Counter(row['named'] for row in rows.values())
    continuing = set(HOUSE_NAMES)
    rounds, eliminated = [], []
    hafner_node_ids = None
    while True:
        tally = Counter()
        for pref, weight in profile.items():
            tally[allocation(pref, continuing)] += weight
        assert sum(tally.values()) == len(rows)
        cohort = Counter(allocation(row['named'], continuing) for row in literal.values())
        assert sum(cohort.values()) == len(literal)
        rounds.append({'continuing': sorted(continuing), 'tallies': dict(tally),
                       'literal_hafner_allocations': dict(cohort)})
        if len(continuing) == 2:
            break
        smallest = min(tally.get(name, 0) for name in continuing)
        last = [name for name in continuing if tally.get(name, 0) == smallest]
        assert len(last) == 1, 'An official tie-break would be needed.'
        loser = last[0]
        if loser == HAFNER:
            hafner_node_ids = {uid for uid, row in rows.items()
                               if allocation(row['named'], continuing) == HAFNER}
        continuing.remove(loser)
        eliminated.append(loser)
    assert hafner_node_ids is not None
    node_destinations = Counter(allocation(rows[uid]['named'], continuing)
                                for uid in hafner_node_ids)
    assert sum(node_destinations.values()) == len(hafner_node_ids)
    return {'rounds': rounds, 'elimination_order': eliminated,
            'finalists': sorted(continuing), 'final_counts': rounds[-1]['tallies'],
            'literal_hafner_destinations': rounds[-1]['literal_hafner_allocations'],
            'actual_hafner_elimination_node_n': len(hafner_node_ids),
            'actual_node_destinations': dict(node_destinations)}


def independent_results():
    house, house_source = read_source('us_house')
    senate, senate_source = read_source('us_senate')
    governor, governor_source = read_source('governor')
    assert house.keys() == senate.keys()
    assert set(governor) <= set(house)
    assert len(set(house)-set(governor)) == 130
    literal = {uid: row for uid, row in house.items() if row['tokens'][0] == HAFNER}
    n = len(literal)
    assert n == 17918
    patterns = Counter(row['named'] for row in literal.values())
    assert len(patterns) == 16 and sum(patterns.values()) == n
    raw_patterns = Counter(row['tokens'] for row in literal.values())
    comparison = Counter()
    next_named = Counter()
    for row in literal.values():
        pref = row['named']
        assert pref and pref[0] == HAFNER
        if HILL in pref and BEGICH in pref:
            category = 'Hill_above_Begich' if pref.index(HILL) < pref.index(BEGICH) else 'Begich_above_Hill'
        else:
            category = 'Hill_only' if HILL in pref else 'Begich_only' if BEGICH in pref else 'neither'
        comparison[category] += 1
        next_named[pref[1] if len(pref) > 1 else 'No other usable named choice'] += 1
    assert sum(comparison.values()) == sum(next_named.values()) == n
    replay = replay_house(house, literal)
    assert replay['elimination_order'] == [MCDERMOTT, HAFNER]
    assert replay['final_counts'] == {BEGICH: 122405, HILL: 108917, 'Inactive': 13383}
    assert replay['literal_hafner_destinations'] == {HILL: 8131, BEGICH: 1142, 'Inactive': 8645}
    sources = {'us_house': house_source, 'us_senate': senate_source, 'governor': governor_source}
    cross, all_group_cross = {}, {}
    for slug, linked in [('us_senate', senate), ('governor', governor)]:
        counts = Counter(linked[uid]['tokens'][0] if uid in linked else 'Missing contest record'
                         for uid in literal)
        assert sum(counts.values()) == n
        cross[slug] = {'cohort_n': n, 'counts': dict(counts)}
        groups = {}
        for candidate in sorted(HOUSE_NAMES):
            ids = [uid for uid, row in house.items() if row['tokens'][0] == candidate]
            c = Counter(linked[uid]['tokens'][0] if uid in linked else 'Missing contest record'
                        for uid in ids)
            assert sum(c.values()) == len(ids)
            groups[candidate] = {'cohort_n': len(ids), 'counts': dict(c)}
        all_group_cross[slug] = groups
    strict = raw_patterns[(HAFNER, 'skipped', 'skipped', 'skipped', 'skipped')]
    facts = {
        'n': n, 'share_all_house_records': n/len(house),
        'raw_strict_bullet': strict, 'named_only': patterns[(HAFNER,)],
        'usable_length_counts': dict(Counter(len(row['named']) for row in literal.values())),
        'barriers': dict(Counter(row['reason'] for row in literal.values())),
        'any_overvote': sum('overvote' in row['tokens'] for row in literal.values()),
        'lower_overvote': sum('overvote' in row['tokens'][1:] for row in literal.values()),
        'any_repeated_named_candidate': sum(len([x for x in row['tokens'] if x in HOUSE_NAMES]) !=
                len({x for x in row['tokens'] if x in HOUSE_NAMES}) for row in literal.values()),
        'any_writein': sum('Write-in' in row['tokens'] for row in literal.values()),
        'any_skipped_rank': sum('skipped' in row['tokens'] for row in literal.values()),
        'any_internal_skip_before_last_mark': sum(
            any(x == 'skipped' for x in row['tokens'][:max(i for i,x in enumerate(row['tokens']) if x != 'skipped')])
            for row in literal.values()),
        'any_internal_two_consecutive_skips': sum(
            any(row['tokens'][i] == row['tokens'][i+1] == 'skipped'
                and i+1 < max(j for j,x in enumerate(row['tokens']) if x != 'skipped')
                for i in range(4)) for row in literal.values()),
        'first_rank_ambiguous_annotation_nonempty': sum(bool(row['original_source_row']['rank1_ambiguous_candidates']) for row in literal.values()),
        'first_rank_overvote_annotation_nonempty': sum(bool(row['original_source_row']['rank1_overvote_candidates']) for row in literal.values()),
        'rank1_ambiguous_not_a_candidate_imputation': True,
        'raw_rank2': dict(Counter(row['tokens'][1] for row in literal.values())),
        'next_usable_named': dict(next_named), 'raw_patterns_n': len(raw_patterns),
    }
    return {'sources': sources, 'cohort': facts,
            'house_first_choices': dict(Counter(row['tokens'][0] for row in house.values())),
            'permutations': [{'ranking': list(pref), 'ballots': count}
                             for pref, count in patterns.most_common()],
            'finalist_comparison': dict(comparison), 'replay': replay,
            'cross_election': cross, 'all_house_groups_cross': all_group_cross,
            '_house_records': house, '_literal_records': literal}


LABELS = {
    HAFNER: 'Eric Hafner', BEGICH: 'Nick Begich', HILL: 'Bill Hill', MCDERMOTT: 'Jim McDermott',
    'Peltola, Mary': 'Mary Peltola', 'Sullivan, Dan S.': 'Daniel S.',
    'Sullivan, Daniel J. Jr.': 'Dan J.', 'Heikes, Gerald L.': 'Gerald Heikes',
    'skipped': 'Blank first rank', 'overvote': 'First-rank overvote',
}


def labeled(counts):
    return {LABELS.get(key, key): value for key, value in counts.items()}


def csv_rows(filename):
    with (ROOT/'hafner'/filename).open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def compare_producer(expected):
    producer_path = ROOT/'hafner/results.json'
    assert producer_path.is_file(), 'Run hafner/run_hafner.py before the independent audit.'
    producer = json.loads(producer_path.read_text())
    assert producer['status'] == 'passed'
    comparisons = []

    def same(label, actual, wanted):
        assert actual == wanted, (label, actual, wanted)
        comparisons.append(label)

    def pct(row, numerator, denominator, field='pct'):
        assert abs(float(row[field])-100*numerator/denominator) < 1e-10, (row, field)

    house = expected['_house_records']
    literal = expected['_literal_records']
    n, total = len(literal), len(house)
    for slug, source in expected['sources'].items():
        for key in ['filename', 'sha256', 'rows']:
            same('source_'+slug+'_'+key, producer['sources'][slug][key], source[key])
    same('house_source_n', producer['house_source_n'], total)
    same('house_first_choices', producer['house_first_choices'], labeled(expected['house_first_choices']))
    cohort_keys = ['n', 'raw_strict_bullet', 'named_only', 'any_overvote', 'lower_overvote',
                   'any_skipped_rank', 'any_writein', 'any_repeated_named_candidate',
                   'any_internal_skip_before_last_mark', 'any_internal_two_consecutive_skips',
                   'first_rank_ambiguous_annotation_nonempty', 'first_rank_overvote_annotation_nonempty']
    for key in cohort_keys:
        same('cohort_'+key, producer['cohort'][key], expected['cohort'][key])
    same('usable_length_counts', producer['cohort']['usable_length_counts'],
         {str(k): v for k,v in expected['cohort']['usable_length_counts'].items()})
    same('barriers', producer['cohort']['barriers'], expected['cohort']['barriers'])
    same('raw_pattern_n', producer['cohort']['raw_pattern_count'], expected['cohort']['raw_patterns_n'])
    same('usable_permutations_n', producer['cohort']['named_permutation_count'], len(expected['permutations']))
    assert abs(producer['cohort']['pct_of_all_house_records']-100*n/total) < 1e-10
    assert abs(producer['cohort']['pct_of_four_named_literal_first_choices']-
               100*n/sum(expected['house_first_choices'][x] for x in HOUSE_NAMES)) < 1e-10
    expected_raw2 = {({'skipped':'Skipped second rank', 'overvote':'Second-rank overvote'}.get(k,LABELS.get(k,k))):v
                     for k,v in expected['cohort']['raw_rank2'].items()}
    same('literal_rank2', producer['cohort']['literal_rank2'], expected_raw2)
    expected_next = {LABELS.get(k,k) if k != 'No other usable named choice' else 'Inactive':v
                     for k,v in expected['cohort']['next_usable_named'].items()}
    same('next_usable_named', producer['cohort']['next_usable_named_choice'], expected_next)
    comparison_names = {'Hill_above_Begich':'Hill_above_Begich_both_usable',
                        'Begich_above_Hill':'Begich_above_Hill_both_usable',
                        'Hill_only':'Hill_only_usable','Begich_only':'Begich_only_usable',
                        'neither':'Neither_finalist_usable'}
    same('finalist_comparison', producer['finalist_comparison'],
         {comparison_names[k]:v for k,v in expected['finalist_comparison'].items()})
    same('Hafner_anywhere_visible', producer['Hafner_presence_all_house_records']['Hafner_visibly_named_anywhere'],
         sum(HAFNER in row['tokens'] for row in house.values()))
    same('Hafner_anywhere_usable', producer['Hafner_presence_all_house_records']['Hafner_usable_named_anywhere'],
         sum(HAFNER in row['named'] for row in house.values()))
    er, pr = expected['replay'], producer['replay']
    same('elimination_order', pr['elimination_order'], er['elimination_order'])
    same('finalists', set(pr['finalists']), set(LABELS[x] for x in er['finalists']))
    same('final_counts', pr['final_counts'], labeled(er['final_counts']))
    same('literal_destinations', pr['hafner_literal_destinations'], labeled(er['literal_hafner_destinations']))
    same('literal_after_Hafner', pr['hafner_literal_after_Hafner_elimination'], labeled(er['literal_hafner_destinations']))
    same('node_n', pr['actual_Hafner_elimination_node_n'], er['actual_hafner_elimination_node_n'])
    same('node_destinations', pr['actual_node_destinations'], labeled(er['actual_node_destinations']))
    same('structural_first_Hafner', pr['first_structurally_usable_Hafner_n'],
         sum(bool(row['pref']) and row['pref'][0] == HAFNER for row in house.values()))
    same('named_initial_Hafner', pr['Hafner_after_initial_generic_writein_exclusion_n'],
         sum(bool(row['named']) and row['named'][0] == HAFNER for row in house.values()))
    same('number_of_rounds', len(pr['rounds']), len(er['rounds']))
    for i,(p,e) in enumerate(zip(pr['rounds'], er['rounds'])):
        same('round_'+str(i)+'_continuing', set(p['continuing']), set(e['continuing']))
        same('round_'+str(i)+'_all_counts', p['counts'], e['tallies'])
    first_rows = csv_rows('house_literal_first_choices.csv')
    same('first_choice_csv', {r['source_rank1']:int(r['ballots']) for r in first_rows}, expected['house_first_choices'])
    for r in first_rows:
        assert int(r['denominator_all_house_records']) == total
        pct(r,int(r['ballots']),total)
    permutation_rows = csv_rows('hafner_usable_permutations.csv')
    expected_patterns = {tuple(r['ranking']):r['ballots'] for r in expected['permutations']}
    same('all_16_permutation_csv_counts',
         {tuple(json.loads(r['source_names_json'])):int(r['ballots']) for r in permutation_rows}, expected_patterns)
    same('permutation_csv_n', len(permutation_rows), 16)
    finalists = set(er['finalists'])
    for r in permutation_rows:
        ranking = tuple(json.loads(r['source_names_json']))
        assert int(r['named_length']) == len(ranking)
        assert int(r['cohort_n']) == n
        pct(r,int(r['ballots']),n)
        wanted = LABELS.get(allocation(ranking,finalists), 'Inactive')
        assert r['after_Hafner_elimination'] == r['hypothetical_final_destination'] == wanted
    raw_rows = csv_rows('hafner_raw_five_rank_patterns.csv')
    expected_raw = Counter(row['tokens'] for row in literal.values())
    same('all_254_raw_pattern_csv_counts',
         {tuple(r['rank'+str(i)] for i in range(1,6)):int(r['ballots']) for r in raw_rows}, dict(expected_raw))
    same('raw_pattern_csv_n', len(raw_rows), len(expected_raw))
    for r in raw_rows:
        tokens = tuple(r['rank'+str(i)] for i in range(1,6))
        pref, reason, rank = prefix_oracle(tokens)
        assert tuple(json.loads(r['countable_prefix_json'])) == pref
        assert r['stop_reason'] == reason
        assert r['barrier_rank'] == (str(rank) if rank is not None else '')
        assert int(r['cohort_n']) == n
        pct(r,int(r['ballots']),n)
    original_columns_checked = 0
    seen = set()
    with gzip.open(ROOT/'hafner/hafner_literal_first_ballots.csv.gz','rt',encoding='utf-8',newline='') as stream:
        reader = csv.DictReader(stream)
        for r in reader:
            uid = normalize_id(r['ballotID'])
            assert uid not in seen and uid in literal
            seen.add(uid)
            original = literal[uid]
            for key,value in original['original_source_row'].items():
                assert r[key] == value, (uid,key,r[key],value)
                original_columns_checked += 1
            assert r['normalized_ballot_id'] == uid
            assert int(r['source_csv_line_including_header']) == original['source_index']+2
            assert tuple(json.loads(r['countable_prefix_json'])) == original['pref']
            assert tuple(json.loads(r['usable_named_prefix_source_json'])) == original['named']
            assert r['first_barrier_reason'] == original['reason']
            assert r['barrier_rank'] == (str(original['barrier_rank']) if original['barrier_rank'] is not None else '')
            assert r['hypothetical_final_destination'] == LABELS.get(allocation(original['named'],finalists),'Inactive')
    same('all_literal_ballot_export_IDs', seen, set(literal))
    same('all_original_source_cells_preserved', original_columns_checked, 15*n)
    for slug, cross in expected['cross_election'].items():
        same('cross_'+slug+'_source_counts', producer['cross_election'][slug]['source_counts'], cross['counts'])
        same('cross_'+slug+'_denominator', producer['cross_election'][slug]['cohort_n'], n)
        same('cross_'+slug+'_labels', producer['cross_election'][slug]['label_counts'], labeled(cross['counts']))
        wanted_groups = {LABELS.get(group,group):labeled(detail['counts'])
                         for group,detail in expected['all_house_groups_cross'][slug].items()}
        same('cross_all_house_groups_'+slug, producer['cross_election_all_House_first_groups'][slug], wanted_groups)
    for filename, only_hafner in [('hafner_cross_election_first_choices.csv',True),
                                  ('all_house_first_groups_cross_election.csv',False)]:
        records = csv_rows(filename)
        got = {}
        for r in records:
            slug = r['other_contest']; group = r['house_first_source_name']
            value = r['other_literal_rank1_source']
            key = (slug,group,value)
            assert key not in got
            got[key] = int(r['ballots'])
            denominator = expected['all_house_groups_cross'][slug][group]['cohort_n']
            assert int(r['cohort_n']) == denominator
            pct(r,int(r['ballots']),denominator)
        want = {(slug,group,value):count
                for slug,groups in expected['all_house_groups_cross'].items()
                for group,detail in groups.items() if not only_hafner or group == HAFNER
                for value,count in detail['counts'].items()}
        same(filename+'_all_cells', got,want)
    expected_routes = Counter(tuple(allocation(row['named'],set(r['continuing'])) for r in er['rounds'])
                              for row in literal.values())
    same('replay_route_csv', {tuple(json.loads(r['source_route_json'])):int(r['ballots'])
                            for r in csv_rows('hafner_replay_routes.csv')},dict(expected_routes))
    expected_preferences = {
        'literal_recorded_rank2': expected['cohort']['raw_rank2'],
        'next_usable_named_choice': {k if k != 'No other usable named choice' else 'Inactive':v
                                    for k,v in expected['cohort']['next_usable_named'].items()},
        'after_Hafner_elimination': er['literal_hafner_destinations'],
        'hypothetical_final_destination': er['literal_hafner_destinations'],
    }
    next_rows = csv_rows('hafner_next_preferences.csv')
    wanted_next = {(definition,choice):count for definition,counts in expected_preferences.items()
                   for choice,count in counts.items()}
    same('all_next_preference_csv_cells',
         {(r['definition'],r['source_choice']):int(r['ballots']) for r in next_rows}, wanted_next)
    assert len(next_rows) == len(wanted_next)
    for r in next_rows:
        assert int(r['cohort_n']) == n
        pct(r,int(r['ballots']),n)
        if r['definition'] == 'next_usable_named_choice' and r['source_choice'] == 'Inactive':
            assert r['label'] == 'No usable named backup'
    round_rows = csv_rows('house_replay_rounds.csv')
    wanted_rounds = {(i+1,name):r['tallies'].get(name,0)
                     for i,r in enumerate(er['rounds']) for name in HOUSE_NAMES | {'Inactive'}}
    same('all_round_csv_counts',
         {(int(r['round']),r['source_name']):int(r['ballots']) for r in round_rows},wanted_rounds)
    assert len(round_rows) == len(wanted_rounds)
    for r in round_rows:
        i=int(r['round'])-1
        assert int(r['all_records']) == total
        assert int(r['active_denominator']) == total-er['rounds'][i]['tallies'].get('Inactive',0)
        out = er['elimination_order'][i] if i < len(er['elimination_order']) else ''
        assert r['eliminated_after_round'] == LABELS.get(out,out)
    # Validate descriptive concentration against original per-record metadata.
    for filename, source_key, file_key, denominator_key, percent_key in [
        ('hafner_by_precinct.csv','precinct','precinct','all_house_records_in_precinct','pct_Hafner_of_all_House_precinct_records'),
        ('hafner_by_counting_group.csv','counting_group','counting_group','all_house_records_in_group','pct_Hafner_of_all_House_group_records')]:
        all_counts = Counter(row[source_key] for row in house.values())
        cohort_counts = Counter(row[source_key] for row in literal.values())
        records = csv_rows(filename)
        same(filename+'_cohort_sum',sum(int(r['hafner_first_ballots']) for r in records),n)
        for r in records:
            key=r[file_key]
            assert int(r['hafner_first_ballots']) == cohort_counts[key]
            assert int(r[denominator_key]) == all_counts[key]
            pct(r,cohort_counts[key],all_counts[key],percent_key)
            pct(r,cohort_counts[key],n,'pct_of_Hafner_cohort')
    return {'status':'passed', 'comparisons':comparisons, 'comparison_count':len(comparisons),
            'original_rows_checked':len(seen), 'original_source_cells_checked':original_columns_checked,
            'producer_results_sha256':hashlib.sha256(producer_path.read_bytes()).hexdigest()}


def main():
    result = independent_results()
    result['producer_comparison'] = compare_producer(result)
    del result['_house_records'], result['_literal_records']
    result['generated_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    result['audit_method'] = 'Independent earliest-barrier oracle, normalized-ID joins, and dynamic full-source replay; no producer imports.'
    result['status'] = 'passed'
    path = OUT/'audit_hafner.json'
    path.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'status': result['status'], 'cohort_n': result['cohort']['n'],
                      'final_counts': result['replay']['final_counts'],
                      'literal_hafner_destinations': result['replay']['literal_hafner_destinations']}, indent=2))
    return result


if __name__ == '__main__':
    main()
