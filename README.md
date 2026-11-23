# Alaska 2026 Midterms

Ranked-ballot analysis of Alaska's Senate, U.S. House and Governor races.
Start with the race you want:

- **[Senate](analysis/senate/)** — candidate axis, ranking permutations, hypothetical transfers and Sankey figures.
- **[House](analysis/house/)** — candidate axis, Hafner rankings and bullet votes, transfers, geography and the separate November 16 check.
- **[Governor](analysis/governor/)** — candidate axis, consistency results and fitting entry point.

## Where everything lives

```text
analysis/
  senate/          Senate analysis, saved axis and race-specific figures
  house/           House analysis, saved axis and race-specific figures
  governor/        Governor analysis and saved axis
  cross_race/      Linked first choices, voter distributions and combined checks
  shared/          One copy of the MDS core, ballot interpreter and metadata
  reporting/       Combined statewide notebook and its display helpers
presentations/     Deck assembly and figures combining several races
references/nov11/  Saved November 11 benchmark validation
provenance/        Original hashes, path migration and upstream reference code
```

Each race folder has a README and a small `Overview.ipynb` that reads its saved
aggregate results without needing the original ballot files. The
[combined research notebook](analysis/reporting/Alaska_2026_Statewide_Analysis.ipynb)
retains the full report source. Rebuilding that report requires the pinned CSVs
and generated intermediate tables; a code-only checkout is not a ready-to-run
copy of the complete research package. See [reproduction instructions](docs/REPRODUCIBILITY.md).

## Historical results and limits

The saved candidate axes use Rachel/FairVote's **November 11 snapshot** and
scikit-learn **1.6.1**. Scikit-learn 1.7 corrected nonmetric-MDS behavior.
A controlled Alaska comparison using the corrected solver has **not** been
completed. Checks of saved matrices and scores do not resolve that issue.
Read [known issues](docs/KNOWN_ISSUES.md) before interpreting or refitting them.

The reorganization preserves the mathematical core and all 31 saved statewide
axis artifacts byte for byte. Raw CVRs and individual ballot exports are not
included. No new statewide fits or legislative experiments were run for this
reorganization. The November 16 House check stays separate from the main
November 11 analyses; Bryan's November 18 legislative archive remains unanalyzed.

## Methods and code

- [Methods and definitions](docs/METHODS.md)
- [Changes from Mahshad's implementation](docs/CHANGES_FROM_MAHSHAD.md)
- [Data versions and checksums](docs/DATA.md)
- [Reproduction and verification](docs/REPRODUCIBILITY.md)
- [What moved, and what was consolidated](docs/ORGANIZATION.md)
- [Canonical mathematical core](analysis/shared/og_axis.py)
- [Portable weighted-profile runner](scripts/fit_candidate_axis.py)

For the historical numerical environment, use Python 3.12:

```bash
python -m pip install -r requirements-core.txt
python scripts/fit_candidate_axis.py --help
python -m unittest discover -s tests -v
python scripts/check_release.py
```

The project is led by [Pejmon Shariati](https://github.com/pshariati) and
[Sam Wang](https://github.com/SamWangPhD). The candidate-axis approach is adapted
from Mahshad Habibpourparizi's work and the
[Bugs in Democracy project](https://github.com/SamWangPhD/bugs-in-democracy/tree/2b1e69572a32d866253170facd85abc36ef252c4).
See [attribution](THIRD_PARTY_NOTICES.md).
