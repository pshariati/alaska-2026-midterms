# Comparisons across races

This folder contains analyses that link the same ballots across Senate, House,
and governor. Code and saved models specific to one election live in the sibling
`senate`, `house`, or `governor` folder.

- `first_choices/`: linked-ballot ingestion, first-choice party/candidate tables,
  and the descriptive Senate finalist comparison. `figures/` draws the paired
  governor/House bars for Senate first-choice groups.
- `voter_distributions/`: the shared allocation and density engine, including
  comparisons of the same Senate cohorts on each election’s separately fitted
  candidate axis. These coordinates are not a common measured ideology scale.
- `validation/`: checks spanning multiple races. The `axes/` subfolder retains
  the saved governor/House audit and combined consistency table.

The public checkout contains code and selected aggregate model artifacts. It
excludes individual ballot files, linked exports, archived reference HTML, and
most generated tables and figures. Source-driven scripts require the exact
Rachel/FairVote November 11 CSVs in `data/nov11/`; the reference checks also
require the archived benchmark files in `references/nov11/`. Missing files must
be supplied explicitly; do not substitute a newer snapshot silently.

Run modules from the repository root, for example:

```bash
python -m analysis.cross_race.first_choices.descriptive_analysis --help
```

This reorganization did not run election fits or new legislative experiments.
See the repository reproduction guide and solver caveat before interpreting or
regenerating saved MDS results.
