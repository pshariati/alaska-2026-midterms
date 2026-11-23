# Method

Each election is modeled separately. The method summarizes relationships among
candidates on a single line; its coordinates are not a calibrated ideology scale.

## Ranking interpretation

The historical main inputs are Rachel/FairVote's three November 11 CSVs. Original
rank cells are preserved outside the model. The interpreter keeps preferences
before the first overvote or two consecutive internal skipped ranks, crosses one
skip, and collapses repeated candidate names. A generic write-in keeps its rank
occupancy during this step, then is removed from the four-name model. Only the
retained, explicitly ranked candidates impose preference constraints.

## Candidate relationships

For candidates i and j, let A_ij be the ballot-weighted number of named sequences
where j immediately follows i. Let C_ij count sequences containing both names.
Set F_ij = A_ij / C_ij when C_ij > 0 and zero otherwise. Symmetrize with
S_ij = (F_ij + F_ji) / 2.

For positive off-diagonal S_ij, dissimilarity D_ij = 1 / sqrt(S_ij).
The inherited finite fallback for S_ij = 0 is 2 / min_positive(S), not
2 / sqrt(min_positive(S)); the diagonal is zero. A profile with no positive
association cannot supply an axis. Adjacency is in the interpreted named
sequence, not necessarily in consecutive original rank cells.

## One-dimensional nonmetric MDS

The historical main fit uses scikit-learn 1.6.1, 20 outer runs, eight
initializations per run, max_iter=1000 and eps=1e-6. Each run retains the
initialization selected by the library. Nonfinite, collapsed and coincident
candidate solutions are rejected. Reflections are aligned and coordinates
centered. Select the most frequent candidate order, breaking frequency ties by
mean reported stress, then candidate order. Average centered coordinates from
that order and normalize once to [0,1]. A display reflection is only orientation.
The old solver has documented limitations; see [known issues](KNOWN_ISSUES.md).

## Consistency and gamma

A ranking is compatible if some voter location u in [0,1] makes the distances to
its named candidates strictly increase in the recorded order. Each consecutive
ranked pair gives a midpoint bound on u; intersecting those bounds suffices.
Feasible interval width must exceed 1e-12. Tie-only solutions do not qualify.
Gamma is the ballot-weighted compatible fraction in a stated nonempty group.
One- and two-name rankings automatically pass on a nondegenerate axis, so
three-/four-name results are reported separately. This strict-distance criterion
is distinct from the separate legacy heuristic also called "strict gamma" in
the upstream repository. Spatial inconsistency does not invalidate a ballot.

## Matched randomized comparison

The current generator preserves the exact joint first-choice-by-ranking-length
counts and samples distinct lower candidates uniformly without replacement.
Each of 49 randomized profiles receives its own dissimilarity matrix, candidate
axis and score, using the same main fitting budget. Seeds are recorded. The
reported random mean is not itself a p-value. Fitting and scoring use the full
profile, so this measures descriptive consistency, not held-out accuracy.

## Distribution plots and transfers

Voter distributions are a subsequent allocation convention: each compatible
multi-name pattern supplies evenly spaced finite points across the closure of
its feasible interval; single-name patterns are placed at their candidate.
Endpoints may be distance ties, although gamma still uses strict compatibility.
A reflected Gaussian KDE smooths the points. The locations are not uniquely
identified voter positions; each race has its own coordinate system.

RCV transfer replays are a separate calculation using the interpreted rankings,
not the candidate-axis coordinates. Hypothetical snapshot replays are not
certified election outcomes. Strict bullet ballots, all inactive ballots, and
ballots lacking a named finalist preference have different definitions.
