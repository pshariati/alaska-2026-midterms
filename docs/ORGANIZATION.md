# Organization and file history

For a reader's guide, start with [How to use this repository](NAVIGATION.md).
The active analyses are grouped under `analysis/senate/`, `analysis/house/` and
`analysis/governor/`. Linked comparisons live in `analysis/cross_race/`; common
methods live in `analysis/shared/`; the combined notebook lives in
`analysis/reporting/`.

The original working packages mixed race-specific analyses, linked-ballot
comparisons and report assembly. Their active pieces have been assigned by
purpose. Duplicate copies of the mathematical core, candidate metadata and
saved Senate results were consolidated. The Senate axis CSV retains its
additional display-position column; the earlier CSV contained the same
coordinates.

The earlier Senate report and one-time notebook maintenance scripts are retained
under `analysis/senate/archive/report_20261111/` as historical source. They are
not the current report or supported execution entry points.

The finished presentation is under `slides/`. Presentation and slide-deck
generation code is omitted from the current repository. Python code that draws
scientific analysis figures and tables remains alongside the relevant analysis.

The path map is in `provenance/layout_migration.json`. Historical source hashes
and the release manifest record lineage and packaging changes. Public data-source
labels use FairVote consistently. These label and path changes do not represent
new numerical fits; the mathematical core and saved numerical results are
preserved. The common path helper resolves retained recorded paths without
maintaining duplicate compatibility folders.

## Verification scope

Independent calculations check observed matrices and consistency scores for all
three races, all 49 saved House and Governor randomized profiles, null-summary
arithmetic, and 16,807 possible five-rank parser cases. Integrity checks track
the current saved artifacts and the mathematical core. These checks do not
refit MDS or resolve the historical solver issue. Senate's randomized profiles
are not packaged, so its randomized scores cannot be rederived from archived
randomized input profiles here.
