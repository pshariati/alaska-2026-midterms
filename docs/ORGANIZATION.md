# Organization

The active analysis is organized by race. Shared code is imported once; linked
comparisons have their own home because they require more than one race.

| Question or material | Location |
| --- | --- |
| Senate rankings and finalist scenarios | `analysis/senate/rankings/` |
| Senate transfer replay | `analysis/senate/flows/` |
| Senate presentation figures and ranking tables | `analysis/senate/figures/` |
| House transfers and Sankey | `analysis/house/flows/` |
| Hafner rankings, geography and linked bullet-voter choices | `analysis/house/hafner/` |
| Separate November 16 House snapshot | `analysis/house/snapshots/nov16_check/` |
| Each race's saved MDS/profile/consistency files | `analysis/<race>/candidate_axis/` |
| Linked Senate first-choice groups in Governor and House | `analysis/cross_race/first_choices/` |
| Voter distributions across the three axes | `analysis/cross_race/voter_distributions/` |
| Combined and all-contest validation | `analysis/cross_race/validation/` |
| Mathematical core, source definitions and common paths | `analysis/shared/` |
| Full combined notebook, rendering and display helpers | `analysis/reporting/` |
| Combined slides and math companion builders | `presentations/` |

## What changed

The three former top-level working directories were dismantled. Their files
were assigned by purpose instead of keeping overlapping packages:

- `statewide_analysis/`
- `alaska_2026_senate_sam_rachel/`
- `alaska_presentation_20261117/`

The old Senate package contained unique cross-race ingestion and transfer code;
it was not simply a duplicate of the combined report. Those active pieces now
live in the appropriate locations above. Identical copies of the mathematical
core and candidate metadata were consolidated. The standardized Senate axis
CSV retains its additional display-position column; the earlier CSV contained
the same coordinates. Duplicate result JSONs were consolidated without changes.

The earlier Senate report and one-time notebook editing scripts are retained
under `analysis/senate/archive/report_20261111/` as historical source. They are
not the active report and are not advertised as runnable in the new layout.
The current full report is under `analysis/reporting/`.

The complete old-to-new path map is in `provenance/layout_migration.json`.
Historical scientific JSON contents stay unchanged, including the old paths
and hashes they record; readers resolve those explicit recorded paths through
`analysis/shared/paths.py`. No duplicate compatibility folders or symlinks
are required.

## Verification scope

Tests freeze all 31 saved statewide axis artifacts and the mathematical core by
hash. Independent calculations check the observed matrices and consistency
scores for all three races, all 49 saved House and Governor randomized profiles,
null-summary arithmetic, and 16,807 possible five-rank parser cases. These
checks do not refit MDS or resolve the historical solver issue. Senate's saved
null profiles are not packaged, so its randomized scores cannot be rederived
from archived randomized input profiles here.
