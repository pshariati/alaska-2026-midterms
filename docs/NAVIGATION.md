# How to use this repository

This repository contains the analysis behind the Alaska presentation. It keeps
the scientific work, saved results and verification code together; most readers
will need only a few files.

## Choose your route

| If you want to… | Start with… |
| --- | --- |
| See the story and figures | [Presentation PDF](../slides/Alaska_Midterm_Elections.pdf) |
| Inspect one race's saved axis and consistency results | Its overview notebook: [Senate](../analysis/senate/Overview.ipynb), [House](../analysis/house/Overview.ipynb) or [Governor](../analysis/governor/Overview.ipynb) |
| Find a specific analysis | The question-to-folder guide below |
| Understand the mathematics and counting definitions | [Methods](METHODS.md) and [implementation changes](CHANGES_FROM_MAHSHAD.md) |
| Run code or check results | [Reproduction instructions](REPRODUCIBILITY.md), then [data requirements](DATA.md) |
| Understand what has and has not been validated | [Known issues](KNOWN_ISSUES.md) |

An `.ipynb` file is a Jupyter notebook: it combines explanation and executable
analysis cells. The three short overview notebooks use committed aggregate
results and do not refit the models. The
[combined notebook](../analysis/reporting/Alaska_2026_Statewide_Analysis.ipynb)
contains the full research report source, with outputs cleared for sharing.
Running the complete report requires the original pinned inputs and additional
generated tables that are not distributed here.

## Find an analysis

| Question or material | Location |
| --- | --- |
| Dan J.–first rankings, finalist comparisons and hypothetical transfer routes | [Senate rankings](../analysis/senate/rankings/) |
| Whole-election Senate transfer replay and Sankey | [Senate flows](../analysis/senate/flows/) |
| Senate ranking-table and flow figures | [Senate figures](../analysis/senate/figures/) |
| Whole-election House transfer replay and Sankey | [House flows](../analysis/house/flows/) |
| Hafner-first rankings, backup preferences and geography | [Hafner analysis](../analysis/house/hafner/) |
| Other-race choices of strict Hafner bullet voters | [Hafner bullet-vote analysis](../analysis/house/hafner/bullet_votes/) |
| Governor and House first choices within Senate first-choice groups | [Linked first choices](../analysis/cross_race/first_choices/) |
| Estimated voter distributions on the three candidate axes | [Voter distributions](../analysis/cross_race/voter_distributions/) |
| Each race's MDS coordinates and consistency results | `candidate_axis/` inside [Senate](../analysis/senate/), [House](../analysis/house/) or [Governor](../analysis/governor/) |
| Full report source and display helpers | [Combined reporting](../analysis/reporting/) |
| Common mathematical implementation and ballot interpreter | [Shared methods](../analysis/shared/) |

Cross-race work has its own folder because it links multiple contests. Shared
methods have one location so the races use the same common implementation.
These folders complement the three race folders; they are not competing
versions of the analyses.

## What the files mean

Inside a race's `candidate_axis/` folder:

- `candidate_axis.csv` contains candidate coordinates. A display-position column applies a reflection for readability where documented.
- `consistency_summary.csv` gives observed consistency, the randomized comparison and related summaries.
- `profile.json` contains aggregate ranking patterns and counts, rather than individual ballot identities.
- `mds_results.json` contains the saved fit, randomized-fit summaries, settings and source information.
- `mds_verification.json` and `method_provenance.json` describe checks and how the saved result was produced.
- House and Governor also include `null_profiles.json`, the saved randomized aggregate profiles. The corresponding Senate profiles are not packaged.

Files named `run_…`, `build_…`, `verify_…` or `audit_…` are executable code.
Some perform new fitting or require omitted source inputs. Read the reproduction
guide before running them; a filename containing “check” does not guarantee that
it is a quick, data-free command.

The earlier Senate report in `analysis/senate/archive/` is historical source.
Use the combined reporting folder for the current full report. The finished
presentation is supplied as a PDF; slide-deck generation code is not part of the
current repository.

## Data and interpretation

The main analyses use FairVote's fixed November 11, 2026 snapshot. Candidate
party annotations describe candidates, not voter registration. Cross-race
matching uses ballot IDs, while missing contest records remain missing.
Transfer scenarios depend on the stated continuing candidates; rankings alone
do not identify confusion or intent. Each election's MDS axis has its own
normalization and is not a shared measured ideology scale.

The historical solver limitation remains relevant even when saved scores can
be reproduced. Consult [known issues](KNOWN_ISSUES.md) before using these results
for a substantive conclusion or producing new fits.
