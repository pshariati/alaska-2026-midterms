# Reproduction

## Historical candidate-axis fits

The reusable runner reads a JSON weighted profile with `candidates` and
`ballots`. Each ballot has an ordered, duplicate-free list of zero-based
candidate indices in `ranking` and a nonnegative integer `count`. Empty
rankings remain represented but do not enter the nonempty gamma denominator.
See `examples/toy_profile.json` for a synthetic format example.

The historical environment is Python 3.12 with numpy 2.0.2, scipy 1.13.1 and
scikit-learn 1.6.1. These versions reproduce the old solver; they are not a
recommendation for future substantive results. Read the known solver issue.

```bash
python -m pip install -r requirements-core.txt
python scripts/fit_candidate_axis.py   --profile alaska_2026_sam_followup_20261116/axis_models/governor/profile.json   --output runs/governor/replay.json   --seed 20261112 --null-draws 49
```

This portable runner uses the preserved mathematical functions with its own
documented seed labels. Its default seed labels differ from the original
contest-specific driver; it is not promised to reproduce saved coordinates
bit for bit. Use the original drivers and exact inputs for their saved seed
protocols. The runner records the core hash and its actual library versions.
It refuses a different numerical environment unless explicitly allowed; such
a run is labeled a different-environment result, never a historical replication.

## Full original statewide workflow

Install the matching pipeline requirements in a separate environment, obtain
the pinned CSV inputs, and restore any omitted generated inputs needed by a
chosen stage. Original relative directory names are preserved to retain paths.
The combined notebook is:
`alaska_2026_sam_followup_20261116/Alaska_2026_Sam_Followup.ipynb`.
Run it from that directory, following the source guard in its first code cell.

The combined notebook defaults to reusing saved models; that setting must not
be described as a fresh MDS fit. The original `axis_models/run_axes.py` freshly
fits Governor and House, while the earlier Senate driver is
`alaska_2026_senate_sam_rachel/mds/run_mds.py`. The drivers write their results,
so use a fresh checkout or a separate run directory for comparisons.

The code-only checkout excludes generated distributions, completed descriptive
tables and individual-linked exports. Before running a downstream notebook cell,
generate its inputs with the supplied relevant stage or restore your original
research package. No automatic download of a changing live CVR is performed.

## Checks supplied with this release

```bash
python -m unittest discover -s tests -v
python scripts/check_release.py
```

Unit checks cover weighted pair counts, the dissimilarity transform, independent
strict-distance geometry, exact first-choice/length null margins, preservation
of the archived core, and parser/help behavior. They do not constitute a new
legislative experiment or a corrected-solver statewide rerun. Python source
syntax and notebook source preservation are checked separately in the manifest.
