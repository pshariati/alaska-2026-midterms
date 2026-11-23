SAVED GOVERNOR AND HOUSE AXES — OG ONE-DIMENSIONAL METHOD

All numerical inputs come from the unmodified FairVote November11 CSV for the
relevant contest. analysis/shared/data.py applies Alaska barriers before removing generic
write-ins and collapses repeated names. Empty named prefixes are retained in the
profile and source totals but excluded from the nonempty consistency denominator.
Candidate IDs are explicit internal annotations; source name tokens are preserved.

The adapted mathematical core is preserved unchanged in analysis/shared/og_axis.py
(SHA256 b4ef0b5f1a152e655a114570e71d88791831241994c0a04d095f37363a4d001a).
Each contest's full eligible profile is fitted and scored with20outer×8starts,
max_iter1000,eps1e-6. Each of49matched first-choice×length randomized profiles is
freshly fitted and scored with the same budget. Seeds are deterministic and saved.
All null profiles, individual axes, diagnostics and summaries are retained.
This is full-profile structural consistency, not held-out predictive accuracy.
Only ranked names constrain distances, so one/two-name prefixes pass automatically.

Raw algorithm coordinates are axis_position in candidate_axis.csv and axis in
mds_results.json. display_axis_position/display_axis apply reflection only, if
needed, to put Kreiss-Tomkins left of Wilson or Hill left of Begich. Governor
needed no reflection; House was reflected. Each race defines its own candidate
scale. These are not a common calibrated ideology metric, and equally normalized
numbers in different races do not identify equivalent substantive positions.
The House display puts Hafner0,Hill.254147,McDermott.745856,Begich1; the Governor
display puts Kreiss0,Taylor.507917,Bronson.633023,Wilson1. Use the explicit display
column directly, without a second reflection.

A100outer×16starts observed-only sensitivity leaves both candidate orders and
consistency values unchanged. Coordinates shift, however: Governor Taylor moves
from.507917to.570309 and Bronson.633023to.659857; House raw Hill from.745853to.721417
and McDermott.254144to.278582. Density plots built on these coordinates should be
read as assumption-dependent descriptive reconstructions, not exactly identified
voter positions or ideology. The main observed/randomized comparisons retain
identical20×8fitbudgets; the stronger fit does not replace only the real side.

Reproduce:
  python -m analysis.shared.fit_races
  python -m analysis.cross_race.validation.axes.audit_axes
or choose one new contest with --only governor / --only us_house.

Independent audit uses a separate raw token parser, reconstructs the entire source
profile and pair matrices, verifies every observed/null score and length-specific
gamma through all-pairs half-space geometry, checks every null margin, and validates
reflection invariance. It does not import the producer parser or scorer. Producer
verification also checks64rankings on each of51axes per contest, including strong
fit. Independent audit evidence is independent_axis_audit.json. Neither script
reads older raw archives or older ballot-derived inputs.

Summary, three/four named preferences:
- Governor57.2345%observed vs50.5088%random, +6.7257percentagepoints; N88693.
- House65.2699%observed vs41.2601%random, +24.0098percentagepoints; N43003.
Full nonempty:
- Governor84.2337%vs81.7541%, N240576;3999empty named prefixes.
- House93.8369%vs89.5761%, N242328;2377empty named prefixes.
The random means are49drawMonteCarlo estimates, with saved MCSEs and null ranges.

Historical solver caveat: these saved fits used scikit-learn 1.6.1.
A controlled comparison with the corrected nonmetric solver has not been
completed. Independent score/matrix checks do not resolve that issue; see
docs/KNOWN_ISSUES.md. Reproduction commands refit and overwrite saved outputs.
