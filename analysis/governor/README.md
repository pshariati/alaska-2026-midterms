# Governor

- [Overview.ipynb](Overview.ipynb): read the saved aggregate results without source ballots or new fitting.
- [candidate_axis/](candidate_axis/): the November 11 profile, candidate positions, dissimilarities, 49 randomized profiles, gamma summaries and historical fit diagnostics.
- `candidate_axis/fit.py`: Governor-specific entry point to the shared fitting engine. It performs new fits and overwrites saved results; see [reproduction](../../docs/REPRODUCIBILITY.md).

Linked comparisons with Senate first-choice groups are under [cross-race analysis](../cross_race/). The combined report is under [reporting](../reporting/). Those analyses use multiple contests and are not duplicated here.

Historical fits use scikit-learn 1.6.1; the unresolved solver caveat is in [known issues](../../docs/KNOWN_ISSUES.md). These are snapshot records, not certified statewide totals.
