"""Path discovery and directory helpers."""

from pathlib import Path
from typing import Iterable

from .constants import ARTIFACT_ROOT, OUTPUT_ROOT, RAW_ROOT, SCHEMA_ROOT, WIKI_ROOT


def discover_workspace_root(start: Path = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "pyproject.toml").exists():
            return candidate
    return current


def ensure_directories(root: Path, extras: Iterable[Path] = ()) -> None:
    directories = [
        RAW_ROOT,
        ARTIFACT_ROOT,
        WIKI_ROOT / "sessions",
        WIKI_ROOT / "themes",
        WIKI_ROOT / "patterns",
        WIKI_ROOT / "participants",
        WIKI_ROOT / "formulation",
        WIKI_ROOT / "questions",
        WIKI_ROOT / "notes" / "personas" / "close-friend",
        OUTPUT_ROOT / "reports",
        OUTPUT_ROOT / "lint",
        SCHEMA_ROOT,
    ]
    directories.extend(extras)
    for directory in directories:
        (root / directory).mkdir(parents=True, exist_ok=True)

