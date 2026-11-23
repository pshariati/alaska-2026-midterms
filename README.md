# Alaska 2026 Midterms

**Analysis by [Pejmon Shariati](https://github.com/pshariati) and [Sam Wang](https://github.com/SamWangPhD).**

Ranked-ballot analysis of Alaska's Senate, Governor and U.S. House elections,
using FairVote's November 11, 2026 cast-vote-record snapshot.

## Start here

- **[Read the presentation (PDF)](slides/Alaska_Midterm_Elections.pdf)** for the overview and figures.
- **[Read the navigation guide](docs/NAVIGATION.md)** to find the analysis behind a question or figure.
- **Choose a race:** [Senate](analysis/senate/), [House](analysis/house/) or [Governor](analysis/governor/). Each folder has a short guide, an `Overview.ipynb` notebook and saved aggregate model results.
- **[Open the combined research notebook](analysis/reporting/Alaska_2026_Statewide_Analysis.ipynb)** for the full report source and analysis workflow.

You do not need to read every file. Start with the PDF, then the race folder or
method that interests you. The overview notebooks read the saved results without
original ballot files or new model fitting. The full research notebook has
cleared outputs and needs additional local inputs to run; see
[reproduction instructions](docs/REPRODUCIBILITY.md).

## Repository map

| Folder | What it contains |
| --- | --- |
| `analysis/senate/` | Senate rankings, hypothetical transfers, candidate axis and figures |
| `analysis/house/` | House candidate axis, transfers, Hafner rankings, bullet votes and geography |
| `analysis/governor/` | Governor candidate axis and consistency results |
| `analysis/cross_race/` | Comparisons linking the same ballots across elections |
| `analysis/shared/` | Common mathematical methods, ballot interpretation and candidate metadata |
| `analysis/reporting/` | Combined research notebook and notebook display helpers |
| `slides/` | Finished presentation PDF |
| `docs/` | Navigation, methods, data versions, reproduction and limitations |
| `tests/`, `references/`, `provenance/` | Verification code, saved benchmark checks and source history |

## Methods and limits

- [Methods and definitions](docs/METHODS.md)
- [Changes from Mahshad's implementation](docs/CHANGES_FROM_MAHSHAD.md)
- [Data versions and checksums](docs/DATA.md)
- [Reproduction and verification](docs/REPRODUCIBILITY.md)
- [Known issues](docs/KNOWN_ISSUES.md)

These records are a dated snapshot, not certified statewide totals. Raw CVRs and
individual ballot exports are not redistributed here. The saved MDS fits use
scikit-learn **1.6.1**; a controlled comparison with the corrected nonmetric-MDS
solver has **not** been completed. Saved-score and matrix checks do not resolve
that limitation. No new election fits or legislative experiments were run for
this repository cleanup.

The candidate-axis approach is adapted from Mahshad Habibpourparizi's work and
the [Bugs in Democracy project](https://github.com/SamWangPhD/bugs-in-democracy/tree/2b1e69572a32d866253170facd85abc36ef252c4).
See [attribution and source lineage](THIRD_PARTY_NOTICES.md).
