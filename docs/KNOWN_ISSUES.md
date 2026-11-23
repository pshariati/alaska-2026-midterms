# Known issues and validation limits

## Historical MDS solver

The saved statewide results and legacy requirements specify scikit-learn 1.6.1.
The [official 1.7 release notes](https://scikit-learn.org/1.7/whats_new/v1.7.html#sklearn-manifold)
document corrections to nonmetric MDS, correspondence between returned stress
and embedding, the convergence criterion and normalized stress. The relevant
source changes are [30514](https://github.com/scikit-learn/scikit-learn/pull/30514)
and [31117](https://github.com/scikit-learn/scikit-learn/pull/31117).

The Alaska code here retains the historical solver for provenance. A controlled
comparison using identical Alaska inputs and matched fitting budgets under a
corrected solver has not been completed. Saved gamma and matrix checks establish
agreement with the saved axis, not correctness or stability of the old solver.
Do not describe the historical results as verified unaffected by those fixes.

## Search and spacing

Repeated starts do not prove a global optimum. A stronger observed-only 100 by
16 search preserved the reported orders and gamma but shifted some coordinates.
That does not replace a matched observed/null comparison or fix a library bug.
Modal-order frequency is not a confidence level. Candidate spacing and inferred
voter distributions remain model- and allocation-dependent.

## Data and interpretation

Rachel's November 11 files are a snapshot, not the complete certified election.
Generic lower-rank overvotes can hide candidate names. Hidden identities are not
reconstructed from another source. Literal first-choice groups, legally
interpreted prefixes and replay allocations use distinct denominators.
Cross-race matching uses normalized ballot IDs rather than row order; missing
governor records remain missing. Ballots do not establish confusion, intent,
voter knowledge or causation. RCV replays are independent of MDS.

## Code-only release

Original CVR CSVs, individual ballot exports, the November 18 legislative ZIP,
and most generated presentation media are excluded. Some archived scripts
require these omitted inputs. Presentation builders using a desktop-specific
runtime are retained as provenance and are not portable Python entry points.
Python modules are syntax-checked; that is not a claim that every archived stage
has been rerun or that every external dependency is present.
