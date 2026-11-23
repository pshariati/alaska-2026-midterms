"""Repository locations; source slugs stay stable while folders use plain names.

Recorded paths resolve the retained historical analysis artifacts. resolve_recorded_path is
only for reading that provenance, not an alternative output directory tree.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INPUTS_ROOT = REPO_ROOT / "data" / "nov11"
REFERENCES_ROOT = REPO_ROOT / "references" / "nov11"
REPORTING_ROOT = REPO_ROOT / "analysis" / "reporting"
SHARED_ROOT = REPO_ROOT / "analysis" / "shared"
_RACES = {"us_senate": "senate", "us_house": "house", "governor": "governor"}


def race_dir(slug):
    return REPO_ROOT / "analysis" / _RACES[slug]


def model_dir(slug):
    return race_dir(slug) / "candidate_axis"


def cross_race_dir(name):
    return REPO_ROOT / "analysis" / "cross_race" / name


def resolve_recorded_path(value):
    """Resolve a path stored by the pre-reorganization research package.

    Absolute external paths are rejected. Source artifacts keep their original
    hashes; public source labels use FairVote. the explicit move map supplies the current location.
    """
    import json
    value = str(value).replace("\\", "/")
    if Path(value).is_absolute() or ".." in Path(value).parts:
        raise ValueError("Expected a repository-relative recorded path: " + value)
    moves = json.loads((REPO_ROOT / "provenance" / "layout_migration.json").read_text())["paths"]
    if value in moves:
        return REPO_ROOT / moves[value]
    for old, new in sorted(moves.items(), key=lambda item: len(item[0]), reverse=True):
        if value.startswith(old + "/"):
            return REPO_ROOT / new / value[len(old) + 1:]
    candidate = REPO_ROOT / value
    if candidate.is_file() or value.startswith(("analysis/", "references/", "data/")):
        return candidate
    raise ValueError("Unmapped historical artifact path: " + value)
