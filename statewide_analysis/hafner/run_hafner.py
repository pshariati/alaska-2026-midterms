"""Reproduce a descriptive Hafner-first analysis from Rachel's November 11 CSVs.

Raw ranks are retained separately. All transfer results are snapshot simulations,
and none of these ballot patterns identifies voter intent or candidate knowledge.
"""
from pathlib import Path
from collections import Counter, defaultdict
import csv
import datetime
import gzip
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'common'))
from data import RACES, read_rows, countable_tokens, normalized_id

E = 'Hafner, Eric'
B = 'Begich, Nick'
L = 'Hill, Bill'
M = 'McDermott, James C. "Jim"'
W = 'Write-in'
INACTIVE = 'Inactive'
HOUSE = [L, E, M, B]
LABEL = {
    E: 'Eric Hafner', B: 'Nick Begich', L: 'Bill Hill', M: 'Jim McDermott',
    'Peltola, Mary': 'Mary Peltola', 'Sullivan, Daniel J. Jr.': 'Dan J.',
    'Sullivan, Dan S.': 'Daniel S.', 'Heikes, Gerald L.': 'Gerald Heikes',
    'Kreiss-Tomkins/Johnson': 'Kreiss-Tomkins/Johnson',
    'Bronson/Church': 'Bronson/Church', 'Taylor/English': 'Taylor/English',
    'Wilson/Shower': 'Wilson/Shower',
    'skipped': 'Blank first rank', 'overvote': 'First-rank overvote',
    W: 'Write-in', INACTIVE: 'Inactive', 'Missing contest record': 'Missing contest record'
}


def text(pref):
    return ' → '.join(LABEL[x] for x in pref) or '(no usable named candidate)'


def rank2_label(token):
    return {'skipped': 'Skipped second rank', 'overvote': 'Second-rank overvote'}.get(token, LABEL[token])


def write_csv(name, rows):
    rows = list(rows)
    if not rows:
        raise ValueError('Empty export: ' + name)
    with (OUT / name).open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def allocation(pref, continuing):
    return next((x for x in pref if x in continuing), INACTIVE)


def replay(profile):
    """Exclude unresolved generic write-ins, eliminate dynamically until two remain."""
    continuing = set(RACES['us_house']['names'])
    rounds = []
    eliminated = []
    while True:
        tally = Counter()
        for pref, count in profile.items():
            tally[allocation(pref, continuing)] += count
        assert sum(tally.values()) == sum(profile.values())
        stage = {
            'round': len(rounds) + 1,
            'continuing': sorted(continuing),
            'counts': dict(tally),
            'inactive': tally[INACTIVE],
            'total_records': sum(tally.values())
        }
        if not rounds:
            active = sum(tally[x] for x in continuing)
            winners = [x for x in continuing if tally[x] * 2 > active]
            if winners:
                stage['first_round_majority_winner'] = winners[0]
                rounds.append(stage)
                break
        if len(continuing) <= 2:
            rounds.append(stage)
            break
        lowest = min(tally[x] for x in continuing)
        losers = sorted(x for x in continuing if tally[x] == lowest)
        if len(losers) != 1:
            raise ValueError('Elimination tie requires an explicit official resolution')
        loser = losers[0]
        stage['eliminated_after_round'] = loser
        rounds.append(stage)
        eliminated.append(loser)
        continuing.remove(loser)
    return rounds, eliminated


def main(render=True):
    OUT.mkdir(parents=True, exist_ok=True)
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    source_meta = {}
    first = Counter()
    profile = Counter()
    house_first_by_uid = {}
    hafner_records = []
    raw_patterns = Counter()
    patterns = Counter()
    raw_second = Counter()
    next_named = Counter()
    stop_reasons = Counter()
    lengths = Counter()
    quality = Counter()
    all_precinct = Counter()
    hafner_precinct = Counter()
    all_groups = Counter()
    hafner_groups = Counter()
    first_usable_hafner = 0
    named_initial_hafner = 0
    all_rank_presence = Counter()
    for index, row, tokens in read_rows('us_house'):
        uid = normalized_id(row['ballotID'])
        assert uid not in house_first_by_uid
        house_first_by_uid[uid] = tokens[0]
        pref, reason, barrier_rank = countable_tokens(tokens)
        named = tuple(x for x in pref if x != W)
        first[tokens[0]] += 1
        profile[named] += 1
        all_precinct[row['precinct']] += 1
        all_groups[row['countingGroup']] += 1
        first_usable_hafner += bool(pref) and pref[0] == E
        named_initial_hafner += bool(named) and named[0] == E
        all_rank_presence['Hafner_visibly_named_anywhere'] += E in tokens
        all_rank_presence['Hafner_usable_named_anywhere'] += E in named
        if tokens[0] != E:
            continue
        hafner_records.append((index, row, tokens, pref, named, reason, barrier_rank))
        raw_patterns[tokens] += 1
        patterns[named] += 1
        raw_second[tokens[1]] += 1
        next_named[named[1] if len(named) > 1 else INACTIVE] += 1
        stop_reasons[reason] += 1
        lengths[len(named)] += 1
        hafner_precinct[row['precinct']] += 1
        hafner_groups[row['countingGroup']] += 1
        quality['raw_strict_bullet'] += tokens[1:] == ('skipped',) * 4
        quality['named_only'] += named == (E,)
        quality['any_overvote'] += 'overvote' in tokens
        quality['lower_overvote'] += 'overvote' in tokens[1:]
        quality['any_skipped_rank'] += 'skipped' in tokens
        quality['any_writein'] += W in tokens
        quality['any_repeated_named_candidate'] += any(tokens.count(x) > 1 for x in HOUSE)
        last = max(i for i, x in enumerate(tokens) if x != 'skipped')
        quality['any_internal_skip_before_last_mark'] += 'skipped' in tokens[:last]
        quality['any_internal_two_consecutive_skips'] += any(
            tokens[i:i + 2] == ('skipped', 'skipped') for i in range(max(0, last - 1)))
        quality['first_rank_ambiguous_annotation_nonempty'] += bool(row['rank1_ambiguous_candidates'])
        quality['first_rank_overvote_annotation_nonempty'] += bool(row['rank1_overvote_candidates'])
    n = len(hafner_records)
    total = len(house_first_by_uid)
    assert total == 244705 and n == first[E] and sum(patterns.values()) == n
    assert len(patterns) == 16
    source_meta['us_house'] = {**RACES['us_house'], 'rows': total}
    rounds, eliminated = replay(profile)
    assert set(rounds[-1]['continuing']) == {L, B}
    final_set = {L, B}
    e_round_index = next(i for i, r in enumerate(rounds) if r.get('eliminated_after_round') == E)
    e_round = rounds[e_round_index]
    after_e = set(e_round['continuing']) - {E}
    final_dest = Counter()
    next_after_e = Counter()
    route_counts = Counter()
    all_node_final = Counter()
    for pref, count in profile.items():
        if allocation(pref, set(e_round['continuing'])) == E:
            all_node_final[allocation(pref, final_set)] += count
    comparison = Counter()
    for _, row, tokens, pref, named, reason, barrier_rank in hafner_records:
        final = allocation(named, final_set)
        final_dest[final] += 1
        after = allocation(named, after_e)
        next_after_e[after] += 1
        route = tuple(allocation(named, set(r['continuing'])) for r in rounds)
        route_counts[route] += 1
        if L in named and B in named:
            comparison['Hill_above_Begich_both_usable' if named.index(L) < named.index(B)
                       else 'Begich_above_Hill_both_usable'] += 1
        else:
            comparison['Hill_only_usable' if L in named else 'Begich_only_usable' if B in named
                       else 'Neither_finalist_usable'] += 1
    assert sum(final_dest.values()) == n == sum(next_after_e.values()) == sum(comparison.values())
    assert sum(all_node_final.values()) == e_round['counts'][E]
    assert final_dest[L] == comparison['Hill_above_Begich_both_usable'] + comparison['Hill_only_usable']
    assert final_dest[B] == comparison['Begich_above_Hill_both_usable'] + comparison['Begich_only_usable']
    assert final_dest[INACTIVE] == comparison['Neither_finalist_usable']

    write_csv('house_literal_first_choices.csv', [
        {'source_rank1': x, 'label': LABEL[x], 'ballots': count,
         'denominator_all_house_records': total, 'pct': 100 * count / total}
        for x, count in first.most_common()])
    write_csv('hafner_usable_permutations.csv', [
        {'usable_named_ranking': text(p), 'source_names_json': json.dumps(p),
         'named_length': len(p), 'ballots': count, 'cohort_n': n, 'pct': 100 * count / n,
         'after_Hafner_elimination': LABEL[allocation(p, after_e)],
         'hypothetical_final_destination': LABEL[allocation(p, final_set)]}
        for p, count in patterns.most_common()])
    write_csv('hafner_raw_five_rank_patterns.csv', [
        {**{f'rank{i + 1}': x for i, x in enumerate(tokens)}, 'ballots': count,
         'cohort_n': n, 'pct': 100 * count / n,
         'countable_prefix_json': json.dumps(countable_tokens(tokens)[0]),
         'stop_reason': countable_tokens(tokens)[1], 'barrier_rank': countable_tokens(tokens)[2]}
        for tokens, count in raw_patterns.most_common()])
    export_rows = []
    for index, row, tokens, pref, named, reason, rank in hafner_records:
        export_rows.append({
            **row, 'normalized_ballot_id': normalized_id(row['ballotID']),
            'source_csv_line_including_header': index + 2,
            'countable_prefix_json': json.dumps(pref), 'usable_named_ranking': text(named),
            'usable_named_prefix_source_json': json.dumps(named),
            'first_barrier_reason': reason, 'barrier_rank': rank,
            'hypothetical_final_destination': LABEL[allocation(named, final_set)]})
    with gzip.open(OUT / 'hafner_literal_first_ballots.csv.gz', 'wt', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(export_rows[0]))
        writer.writeheader()
        writer.writerows(export_rows)
    write_csv('hafner_next_preferences.csv', [
        {'definition': definition, 'source_choice': x,
         'label': rank2_label(x) if definition == 'literal_recorded_rank2' else
                  'No usable named backup' if definition == 'next_usable_named_choice' and x == INACTIVE else LABEL[x],
         'ballots': count,
         'cohort_n': n, 'pct': 100 * count / n}
        for definition, counter in [('literal_recorded_rank2', raw_second),
                                    ('next_usable_named_choice', next_named),
                                    ('after_Hafner_elimination', next_after_e),
                                    ('hypothetical_final_destination', final_dest)]
        for x, count in counter.most_common()])
    write_csv('house_replay_rounds.csv', [
        {'round': r['round'], 'candidate': LABEL[x], 'source_name': x, 'ballots': r['counts'].get(x, 0),
         'eliminated_after_round': LABEL.get(r.get('eliminated_after_round'), ''),
         'all_records': total, 'active_denominator': total - r['inactive']}
        for r in rounds for x in HOUSE + [INACTIVE]])
    write_csv('hafner_replay_routes.csv', [
        {'route': ' → '.join(LABEL[x] for x in route), 'source_route_json': json.dumps(route),
         'ballots': count, 'cohort_n': n, 'pct': 100 * count / n}
        for route, count in route_counts.most_common()])

    cross = {}
    cross_rows = []
    all_cross_rows = []
    join_meta = {}
    hafner_uids = {normalized_id(r[1]['ballotID']) for r in hafner_records}
    cross_for_groups = {}
    for slug in ['us_senate', 'governor']:
        other = {}
        for _, row, tokens in read_rows(slug):
            uid = normalized_id(row['ballotID'])
            assert uid not in other
            other[uid] = tokens[0]
        source_meta[slug] = {**RACES[slug], 'rows': len(other)}
        absent = len(set(house_first_by_uid) - set(other))
        extra = len(set(other) - set(house_first_by_uid))
        join_meta[slug] = {'missing_from_house_IDs': absent, 'other_IDs_not_in_house': extra,
                          'hafner_missing_other_contest': len(hafner_uids - set(other))}
        counters = {c: Counter() for c in HOUSE}
        for uid, house_first in house_first_by_uid.items():
            if house_first in counters:
                counters[house_first][other.get(uid, 'Missing contest record')] += 1
        for house_first, counter in counters.items():
            assert sum(counter.values()) == first[house_first]
            for x, count in counter.most_common():
                r = {'house_first_source_name': house_first, 'house_first': LABEL[house_first],
                     'other_contest': slug, 'other_literal_rank1_source': x,
                     'other_first_choice': LABEL[x], 'ballots': count,
                     'cohort_n': first[house_first], 'pct': 100 * count / first[house_first]}
                all_cross_rows.append(r)
                if house_first == E:
                    cross_rows.append(r)
        cross[slug] = {'cohort_n': n, 'source_counts': dict(counters[E]),
                       'label_counts': {LABEL[x]: v for x, v in counters[E].items()}}
        cross_for_groups[slug] = {LABEL[c]: {LABEL[x]: v for x, v in cc.items()}
                                  for c, cc in counters.items()}
    assert join_meta['us_senate']['missing_from_house_IDs'] == 0
    assert join_meta['governor']['missing_from_house_IDs'] == 130
    write_csv('hafner_cross_election_first_choices.csv', cross_rows)
    write_csv('all_house_first_groups_cross_election.csv', all_cross_rows)
    write_csv('hafner_by_precinct.csv', [
        {'precinct': x, 'hafner_first_ballots': count, 'all_house_records_in_precinct': all_precinct[x],
         'pct_Hafner_of_all_House_precinct_records': 100 * count / all_precinct[x],
         'pct_of_Hafner_cohort': 100 * count / n}
        for x, count in hafner_precinct.most_common()])
    write_csv('hafner_by_counting_group.csv', [
        {'counting_group': x, 'hafner_first_ballots': hafner_groups[x],
         'all_house_records_in_group': count,
         'pct_Hafner_of_all_House_group_records': 100 * hafner_groups[x] / count,
         'pct_of_Hafner_cohort': 100 * hafner_groups[x] / n}
        for x, count in all_groups.most_common()])

    result = {
        'status': 'passed', 'analysis': 'Eric Hafner literal House-first ballots',
        'source_version': 'Rachel/FairVote supplied November 11, 2026 CSVs',
        'sources': source_meta, 'started_utc': started,
        'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'house_first_choices': {LABEL[x]: count for x, count in first.items()},
        'house_source_n': total,
        'cohort': {'definition': 'Literal recorded House rank1 is Hafner, Eric', 'n': n,
                   'pct_of_all_house_records': 100 * n / total,
                   'pct_of_four_named_literal_first_choices': 100 * n / sum(first[c] for c in HOUSE),
                   **dict(quality), 'usable_length_counts': dict(lengths),
                   'barriers': dict(stop_reasons), 'raw_pattern_count': len(raw_patterns),
                   'named_permutation_count': len(patterns),
                   'literal_rank2': {rank2_label(x): v for x, v in raw_second.items()},
                   'next_usable_named_choice': {LABEL[x]: v for x, v in next_named.items()}},
        'Hafner_presence_all_house_records': dict(all_rank_presence),
        'finalist_comparison': dict(comparison),
        'replay': {'definition': 'Hypothetical full-source Alaska-rule replay, not official transfers',
                   'generic_writeins_excluded_after_barriers': True,
                   'rounds': rounds, 'elimination_order': eliminated,
                   'elimination_order_labels': [LABEL[x] for x in eliminated],
                   'finalists': [LABEL[x] for x in rounds[-1]['continuing']],
                   'final_counts': {LABEL[x]: v for x, v in rounds[-1]['counts'].items()},
                   'hafner_literal_destinations': {LABEL[x]: v for x, v in final_dest.items()},
                   'hafner_literal_after_Hafner_elimination': {LABEL[x]: v for x, v in next_after_e.items()},
                   'first_structurally_usable_Hafner_n': first_usable_hafner,
                   'Hafner_after_initial_generic_writein_exclusion_n': named_initial_hafner,
                   'actual_Hafner_elimination_node_n': e_round['counts'][E],
                   'actual_node_destinations': {LABEL[x]: v for x, v in all_node_final.items()}},
        'cross_election': cross, 'cross_election_all_House_first_groups': cross_for_groups,
        'joins': join_meta,
        'interpretation_limits': [
            'The records cannot establish whether voters knew the candidate biography or why they voted.',
            'Candidate affiliations are reference labels, not voter registration.',
            'Cross-election choices and rank patterns do not identify confusion, protest, fraud, or intent.',
            'Literal first choice, first usable choice, and the later elimination node are different populations.',
            'McDermott is eliminated before Hafner: a Hafner > McDermott > Hill ranking transfers directly to Hill at Hafner elimination, not via McDermott.',
            'A later-round majority does not end this replay before two remain; only a first-round majority would stop immediately.',
            'Precinct and counting-group summaries describe this snapshot; no anomaly or causal inference is made.',
            'Source records are not final statewide totals; hand-count-only ballots are outside CVR coverage.',
            'Generic overvotes hide candidate membership; no identities are reconstructed from older data.'
        ]
    }
    (OUT / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    if render:
        render_figures(result)
    print(json.dumps({'status': result['status'], 'cohort_n': n,
                      'final_destinations': result['replay']['hafner_literal_destinations'],
                      'elimination_order': result['replay']['elimination_order_labels'],
                      'raw_strict_bullet': result['cohort']['raw_strict_bullet']}))
    return result


def render_figures(result=None):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    if result is None:
        result = json.loads((OUT / 'results.json').read_text())
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
                         'text.color': '#26384c', 'axes.labelcolor': '#26384c',
                         'xtick.color': '#4d627b', 'ytick.color': '#4d627b',
                         'svg.fonttype': 'none', 'savefig.facecolor': 'white'})
    n = result['cohort']['n']
    colors = {'Bill Hill': '#5e9e8d', 'Nick Begich': '#bd4f4f',
              'Jim McDermott': '#c39a38', 'Inactive': '#bdcbd7',
              'Mary Peltola': '#377fae', 'Dan J.': '#db9b31',
              'Gerald Heikes': '#8260ae', 'Daniel S.': '#bd4f4f',
              'Kreiss-Tomkins/Johnson': '#377fae', 'Taylor/English': '#cb8792',
              'Bronson/Church': '#c16b62', 'Wilson/Shower': '#ad4149',
              'Other / blank / overvote / missing': '#bdcbd7'}
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 5.7), gridspec_kw={'wspace': .42})
    for ax, data, title, order in [
        (axes[0], result['cohort']['next_usable_named_choice'],
         'Next usable named preference', ['Bill Hill', 'Jim McDermott', 'Nick Begich', 'Inactive']),
        (axes[1], result['replay']['hafner_literal_destinations'],
         'Hypothetical final destination', ['Bill Hill', 'Nick Begich', 'Inactive'])]:
        vals = [100 * data.get(x, 0) / n for x in order]
        display_order = [('No named backup' if x == INACTIVE and ax is axes[0] else x) for x in order]
        ax.barh(display_order, vals, color=[colors[x] for x in order], height=.50)
        ax.invert_yaxis()
        ax.set_xlim(0, max(vals) + 16)
        ax.set_xlabel('Share of all Hafner-first ballots (%)')
        ax.set_title(title, loc='left', fontweight='bold', fontsize=14, pad=20)
        for i, (x, val) in enumerate(zip(order, vals)):
            ax.text(val + .7, i, f'{val:.1f}%  ({data.get(x, 0):,})', va='center', fontsize=11)
        ax.spines[['top', 'right', 'left']].set_visible(False)
        ax.tick_params(axis='y', length=0)
        ax.xaxis.grid(True, color='#e7edf2', linewidth=.8)
        ax.set_axisbelow(True)
    fig.suptitle(f'Eric Hafner-first ballots: backup choices and transfers',
                 x=.07, y=.97, ha='left', fontsize=18, fontweight='bold')
    fig.text(.07, .895, f'Rachel’s November 11 snapshot · {n:,} literal House first-choice ballots', fontsize=11)
    fig.text(.07, .035,
             'Left shows ranked backup preferences, not actual transfers; McDermott is eliminated before Hafner in this replay.\n'
             'Right follows the full replay to Hill/Begich or inactivity. Usable rankings apply Alaska barriers; generic write-ins omitted.',
             fontsize=9, color='#627990')
    fig.subplots_adjust(top=.77, bottom=.22, left=.12, right=.93)
    for suffix in ['png', 'svg']:
        fig.savefig(OUT / f'hafner_backup_choices_and_destinations.{suffix}', dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(2, 1, figsize=(12.8, 9.8))
    other_label = 'Other / blank / overvote / missing'
    for ax, slug, title, cats in [
        (axes[0], 'us_senate', 'Senate first choice',
         ['Mary Peltola', 'Dan J.', 'Gerald Heikes', 'Daniel S.']),
        (axes[1], 'governor', 'Governor first choice',
         ['Kreiss-Tomkins/Johnson', 'Taylor/English', 'Bronson/Church', 'Wilson/Shower'])]:
        groups = result['cross_election_all_House_first_groups'][slug]
        names = [LABEL[x] for x in HOUSE]
        categories = cats + [other_label]
        left = np.zeros(len(names))
        denoms = np.array([result['house_first_choices'][x] for x in names])
        for cat in categories:
            counts = np.array([groups[name].get(cat, 0) if cat != other_label else
                               sum(v for k, v in groups[name].items() if k not in cats) for name in names])
            vals = 100 * counts / denoms
            ax.barh(names, vals, left=left, color=colors[cat], label=cat, height=.57)
            for i, val in enumerate(vals):
                if val >= 6:
                    ax.text(left[i] + val / 2, i, f'{val:.1f}%', ha='center', va='center',
                            color='white', fontsize=10, fontweight='bold')
            left += vals
        assert np.max(np.abs(left - 100)) < 1e-8
        ax.invert_yaxis()
        ax.set_xlim(0, 100)
        ax.set_title(title, loc='left', fontweight='bold', fontsize=15, pad=15)
        ax.spines[['top', 'right', 'left']].set_visible(False)
        ax.tick_params(axis='y', length=0)
        for lab in ax.get_yticklabels():
            if lab.get_text() == 'Eric Hafner':
                lab.set_fontweight('bold')
        ax.legend(loc='upper left', bbox_to_anchor=(0, -.16), ncol=3, frameon=False, fontsize=9)
        ax.set_xlabel('Share of the full House first-choice cohort (%)')
    fig.suptitle('House first-choice groups in the other two races', x=.07, y=.985,
                 ha='left', fontsize=19, fontweight='bold')
    fig.text(.07, .942, 'Rachel’s November 11 snapshot · Hafner’s group is shown alongside the other House groups', fontsize=11)
    fig.text(.07, .018, 'Literal first ranks; missing Governor records remain in the denominator. Candidate choices do not identify voter intent.',
             fontsize=9, color='#627990')
    fig.subplots_adjust(top=.875, bottom=.155, left=.16, right=.96, hspace=.82)
    for suffix in ['png', 'svg']:
        fig.savefig(OUT / f'hafner_cross_election_comparison.{suffix}', dpi=180)
    plt.close(fig)


if __name__ == '__main__':
    main()
