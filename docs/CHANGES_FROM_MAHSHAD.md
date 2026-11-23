# Changes from Mahshad's implementation

Reference: `MDS_analysis.py`, `consistency.py` and `null_elections.py` in the
[pinned upstream snapshot](https://github.com/SamWangPhD/bugs-in-democracy/tree/2b1e69572a32d866253170facd85abc36ef252c4/2026/analysis).
The Alaska mathematical core is `analysis/shared/og_axis.py`.

| Part | Upstream behavior | Alaska implementation |
| --- | --- | --- |
| Co-ranking indexing | Candidate mapping starts at zero but pair-mention counting subtracts one | Consistent zero-based candidate indices |
| Fitting parameters | `max_itr` triggers a fallback that does not pass the requested initialization count | Explicit initialization count, iteration limit, tolerance and seeds |
| Reflections | Reverse-order counts are combined, while coordinate lists remain separate | Reflect and center each accepted run before combining coordinates |
| Modal-order ties | First most-common order from the counter | Deterministic frequency, mean-stress and candidate-order tie breaks |
| Degenerate fits | No corresponding explicit rejection in the saved reference function | Reject nonfinite, collapsed and coincident-position fits without silently jittering them |
| Scale | Normalize to [0, number of candidates minus one] | Normalize to [0,1]; this rescaling alone preserves distance order |
| Gamma | Linear-programming interval feasibility with asymmetric epsilon bounds | Direct midpoint-interval feasibility with a positive-width strict-distance criterion |
| Randomization | Multiple legacy null generators exist, including a generator using one random tail per first-choice/length stratum | Independent uniformly sampled tails with exact joint first-choice/length counts |
| Data preparation | General upstream parser | Explicit Alaska ranking interpreter and pinned FairVote source versions |

The conceptual structure is retained: co-ranking-normalized adjacency,
inverse-square-root dissimilarity, one-dimensional nonmetric MDS and modal-order
selection. The changes are substantive implementation changes and can affect
coordinates and gamma. An unchanged-upstream Alaska run isolating their combined
effect has not been performed for this release.

The retained scikit-learn 1.6.1 solver is an additional, unresolved issue for the
historical Alaska fits. Corrections to our wrapper must not be confused with the
solver fixes in scikit-learn 1.7. No version-upgrade result is claimed here.
