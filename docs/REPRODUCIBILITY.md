# Reproduction

Run package commands from the repository root. Python 3.12 and the pinned
`requirements-core.txt` preserve the historical numerical environment. This is
provenance, not a recommendation to use the old solver for new findings; read
[known issues](KNOWN_ISSUES.md).

## Checks requiring no ballot files and no new fitting

```bash
python -m pip install -r requirements-core.txt
python -m unittest discover -s tests -v
python scripts/check_release.py
```

The tests check weighted pair counting, the dissimilarity transform, independent
strict-distance geometry, matched-null margins, parser barriers, saved-profile
scores and matrices, saved randomized profiles, and immutable result hashes.
The release checker checks manifest hashes, Python/notebook syntax, cleared
notebook outputs, and excluded ballot data. These are not new model fits or
validation against omitted source CVRs. Senate randomized profiles are absent;
House and Governor each include 49 saved randomized profiles.

## Read the saved results

Open `analysis/senate/Overview.ipynb`, `analysis/house/Overview.ipynb` or
`analysis/governor/Overview.ipynb` in Jupyter. These small notebooks read committed
aggregate results and display their source version, candidate axis and gamma
summaries. They do not refit or reconstruct individual ballots.

## Fitting entry points

The generic runner accepts weighted JSON profiles with `candidates` and
`ballots`, including `analysis/<race>/candidate_axis/profile.json`. A ranking is
an ordered, duplicate-free list of zero-based candidate indices and each count
is a nonnegative integer. Empty rankings are retained but excluded from the
nonempty gamma denominator. `examples/toy_profile.json` is synthetic.

```bash
python scripts/fit_candidate_axis.py --help
```

It records the actual library versions and requires explicit permission via
`--allow-different-environment` to run outside the historical numerical versions.
Its seed labels differ from the original contest drivers, so it is not promised
to reproduce saved coordinates bit for bit.

The original seed-protocol drivers, now with updated paths, are:

```bash
python -m analysis.senate.candidate_axis.run_mds
python -m analysis.governor.candidate_axis.fit
python -m analysis.house.candidate_axis.fit
```

**These commands perform expensive new fits and overwrite the corresponding
saved output files.** Use a disposable checkout for a replication. They require
the exact source CSVs under `data/nov11/`; the Senate driver retains its own
independent ranking interpreter. Governor and House share one fitting engine
in `analysis/shared/fit_races.py`. No fitting command was run for the reorganization.

## Rebuilding the combined research report

The source notebook and builders are in `analysis/reporting/`. Install its
additional requirements, supply the pinned inputs, and generate or restore
required intermediate artifacts before running it. The code-only release does
not include linked ballot exports, generated descriptive tables, density grids,
Sankey media or every archived reference webpage. Supplying the three CSVs alone
does not automatically restore all of those dependencies.

The upstream stages are grouped by race and under `analysis/cross_race/`; their
READMEs identify their entry points. The combined notebook reuses saved spatial
fits by default. Its optional refitting flag must remain false if the intention
is to rebuild the report without new MDS fitting. The earlier report under
`analysis/senate/archive/` is frozen historical source, not a runnable entry point.

Presentation Python code builds figures from generated tables. Some JavaScript
deck builders depend on the author's desktop presentation runtime; they are
preserved with that limitation, not presented as portable public commands.
