# House analysis

All active House-specific analysis is in this folder. The main notebook combining the three elections is in [`../reporting/`](../reporting/).

| Folder | Contents |
| --- | --- |
| `candidate_axis/` | Saved House candidate positions, source profile, randomized profiles, matrices and consistency results. The fitting driver is shared with governor in `../shared/fit_races.py`. |
| `hafner/` | Hafner-first preferences, transfers, geography and independent source checks. |
| `hafner/bullet_votes/` | Strict Hafner bullet-ballot cohort and its linked Senate/governor first choices, plus the corresponding slide builder. |
| `flows/` | Whole-election House Sankey analysis and rendering. |
| `snapshots/nov16_check/` | Separate raw-state-CVR November 16 House replay and comparison with Sam's supplied table. It is not mixed into the November 11 analysis. |

Shared MDS mathematics and source definitions live in [`../shared/`](../shared/). General linked-ballot comparisons and voter-distribution calculations live in [`../cross_race/`](../cross_race/).

Run active Python modules from the repository root using `python -m analysis.house.<folder>.<module>`. November 11 producers require the pinned Rachel/FairVote CSVs in `data/nov11/`. The separate November 16 producer instead requires the exact archived state export at `data/nov16/CVR_Export.zip` and checks its hash. Raw ballot files and most derived ballot-level outputs are not included in this public repository.

Presentation scripts require their saved analysis outputs. The Sankey image renderer requires `sharp`; the editable Hafner slide builder additionally uses the presentation runtime, with `PRESENTATIONS_SKILL_ROOT` identifying that installation and optional `PYTHON_EXECUTABLE` selecting its Python executable.

The folder reorganization did not rerun analyses or change saved estimates. Consult the repository's known-issues documentation for the existing MDS solver limitation.
