"""Explicit Governor refit entry point; see docs/REPRODUCIBILITY.md."""
from analysis.shared.fit_races import main

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Refit the pinned November 11 Governor profile and 49 null profiles. Overwrites saved results; use a disposable checkout.")
    parser.parse_args()
    main("governor")
