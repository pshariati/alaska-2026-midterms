# Combined research report

`Alaska_2026_Statewide_Analysis.ipynb` is the full combined report source. It brings together the race-specific analyses and linked comparisons. It is not a second copy of their mathematical code or saved models.

`build_notebook.py` assembles its cells; `display.py` and `hafner_section.py` supply display helpers. `execute_notebook.py` runs it in a Jupyter kernel, and `render/render_browser_view.py` renders a completed notebook. `package_results.py` is the delivery checker/packager for a fully restored research package, not a code-only quick start.

The public notebook has cleared outputs. Full execution requires the exact November 11 CSVs, generated descriptive/flow/distribution tables and omitted archived references. Read [reproduction](../../docs/REPRODUCIBILITY.md) before running it. Per-race `Overview.ipynb` notebooks read the committed saved aggregates immediately without these inputs.
