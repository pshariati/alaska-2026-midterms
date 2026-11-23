# Senate analysis

All active Senate-specific analysis is in this folder. The main notebook combining the three elections is in [`../reporting/`](../reporting/).

| Folder | Contents |
| --- | --- |
| `candidate_axis/` | Senate MDS driver, ranking interpreter, saved candidate positions, profiles, consistency results and model audits. The canonical saved profile is `profile.json`. |
| `rankings/` | Dan J.–first ranking distributions, finalist comparisons, hypothetical transfer routes and independent checks. |
| `flows/` | Whole-election Senate transfer replay, Sankey builder and independent flow audit. |
| `figures/` | Presentation rendering of the saved Senate flows and ranking tables. |
| `archive/report_20261111/` | Frozen earlier notebook and its historical maintenance scripts. Its former paths are preserved for reference; it is not the current entry point. |

Shared MDS mathematics and source definitions live in [`../shared/`](../shared/). Analyses linking Senate ballots to governor and House choices live in [`../cross_race/`](../cross_race/), so these are not duplicated here.

Run active Python modules from the repository root using `python -m analysis.senate.<folder>.<module>`. The parser checks require no ballot data:

```sh
python -m analysis.senate.flows.test_flows
python -m analysis.senate.candidate_axis.test_rachel_rules
```

The analysis producers require the pinned Rachel/FairVote November 11 CSVs in `data/nov11/`; raw ballot files and most derived ballot-level outputs are not included in this public repository. Figure renderers additionally require the saved output files they name. JavaScript image rendering requires `sharp`.

`candidate_axis/run_mds.py`, `candidate_axis/check_mds.py` and the independent MDS audit perform fitting when explicitly executed. They were not rerun as part of the folder reorganization. Saved results retain their original settings and limitations; see the repository's known-issues documentation before interpreting a fresh fit.
