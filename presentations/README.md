# Presentation and mathematical-companion sources

This folder holds deck assembly and figures that combine multiple races.
Race-specific figure builders live with their analysis:

- Senate transfer and ranking figures: `analysis/senate/figures/`.
- House Sankey: `analysis/house/flows/`.
- Hafner bullet-vote slide: `analysis/house/hafner/bullet_votes/`.
- Governor/House bars grouped by Senate first choice:
  `analysis/cross_race/first_choices/figures/`.

`assets/` builds the cross-race plots; `narrow_density_figures/` and
`new_slides_20261117/` format those saved distributions. `math_qr/` contains the
mathematical PDF and QR-companion source; `v2/` is the polished PDF source.

The hidden `.build/` directory retains the original deck assembly scripts.
They depend on the local Codex presentation runtime and generated assets that
are not included in this code-only checkout. They are source records, not a
portable one-command deck build. Repository asset paths are relative to the
checkout; runtime locations still require local configuration.

Python modules are launched from the repository root. The figure builders need
matplotlib and their saved input tables in addition to the core dependencies.
No new slides or scientific results were generated during this reorganization.
