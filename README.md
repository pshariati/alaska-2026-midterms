# Alaska 2026 Midterms

Code for the Alaska 2026 Senate, U.S. House and Governor ranked-ballot analysis:
candidate axes from one-dimensional nonmetric MDS, ranking consistency and
matched randomized comparisons, cross-race first choices, RCV transfer replays,
voter-distribution figures, and presentation assets.

The project is led by [Pejmon Shariati](https://github.com/pshariati) and
[Sam Wang](https://github.com/SamWangPhD). The candidate-axis approach
is adapted from Mahshad Habibpourparizi's work and the
[Bugs in Democracy project](https://github.com/SamWangPhD/bugs-in-democracy/tree/2b1e69572a32d866253170facd85abc36ef252c4).
See [attribution](THIRD_PARTY_NOTICES.md) and the
[specific implementation changes](docs/CHANGES_FROM_MAHSHAD.md).

## Read this first

This initial release preserves the implementation and saved statewide fits that
produced the reported November 11 snapshot results. Those fits used scikit-learn
**1.6.1**. Version 1.7 corrected nonmetric-MDS behavior. A controlled
Alaska comparison with the corrected solver has **not** been completed here.
Independent checks of the saved matrices and scores do not establish that the
old numerical solver was correct. See [known issues](docs/KNOWN_ISSUES.md).

The code is an adapted implementation of Mahshad's approach. It should not be
described as an unchanged copy of her script or as a corrected-solver rerun.

## Start here

- [Method and definitions](docs/METHODS.md)
- [Changes from Mahshad's implementation](docs/CHANGES_FROM_MAHSHAD.md)
- [Data versions and input checksums](docs/DATA.md)
- [Reproduction instructions](docs/REPRODUCIBILITY.md)
- [Known issues and validation limits](docs/KNOWN_ISSUES.md)
- [Archived mathematical core](statewide_analysis/common/og_axis.py)
- [Generic candidate-axis runner](scripts/fit_candidate_axis.py)

## Repository layout

| Location | Contents |
| --- | --- |
| `statewide_analysis/` | Combined statewide notebook, axes, distributions, permutation scenarios, Hafner analysis, independent checks |
| `alaska_2026_senate_sam_rachel/` | Earlier Rachel-only Senate analysis, source parser, descriptive tables and Senate transfer replay |
| `alaska_presentation_20261117/` | Figure, table, Sankey, math-companion and presentation-generation code; includes the separate November 16 House check |
| `scripts/` | Portable entry point for a weighted candidate-ranking profile |
| `examples/` | Clearly labeled synthetic format example; no real election claims |
| `tests/` | Pair-counting, geometry and matched-null checks that do not refit election data |
| `provenance/` | Source-file checksums and packaging transformations |

The mathematical core is preserved byte for byte. Folder and notebook path updates are recorded in the source manifest. Notebook outputs and
execution metadata are cleared for sharing, while their cell sources are
preserved. Saved axis results and aggregate ranking profiles are included; raw
CVR files, individual ballot identifiers and linked ballot exports are excluded.
Not every archived notebook can run from a code-only checkout: see the explicit
input requirements in [reproduction instructions](docs/REPRODUCIBILITY.md).

## Quick start: candidate-axis code

Use Python 3.12 and an isolated environment to reproduce the historical solver:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-core.txt
python scripts/fit_candidate_axis.py --help
```

The runner accepts a weighted JSON profile, including the saved aggregate
`axis_models/<race>/profile.json` files. It records library versions and refuses
to relabel a run under a different solver as the historical environment. A
different version requires the explicit `--allow-different-environment` flag.
Read the solver issue above before generating or interpreting new fits.

```bash
python -m unittest discover -s tests -v
```

No legislative experiments or new statewide fits were run to assemble this
release. Bryan's November 18 archive is a separate prospective data version and
has not been analyzed here.
