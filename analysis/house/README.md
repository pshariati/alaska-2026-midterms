# House analysis

All active House-specific analysis is in this folder. The main notebook combining the three elections is in [`../reporting/`](../reporting/).

| Folder | Contents |
| --- | --- |
| `candidate_axis/` | Saved House candidate positions, source profile, randomized profiles, matrices and consistency results. The fitting driver is shared with governor in `../shared/fit_races.py`. |
| `hafner/` | Hafner-first preferences, transfers, geography and independent source checks. |
| `hafner/bullet_votes/` | Strict Hafner bullet-ballot cohort and its linked Senate/governor first choices. |
| `flows/` | Whole-election House Sankey analysis and rendering. |

Shared MDS mathematics and source definitions live in [`../shared/`](../shared/). General linked-ballot comparisons and voter-distribution calculations live in [`../cross_race/`](../cross_race/).

Run active Python modules from the repository root using `python -m analysis.house.<folder>.<module>`. November 11 producers require the pinned FairVote CSVs in `data/nov11/`. Raw ballot files and most derived ballot-level outputs are not included in this public repository.

Scientific figure generators require the analysis outputs they name. The finished presentation is supplied as a PDF under `slides/`; slide-deck generation code is omitted.

The folder reorganization did not rerun analyses or change saved estimates. Consult the repository's known-issues documentation for the existing MDS solver limitation.
