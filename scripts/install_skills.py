#!/usr/bin/env python3
"""Copy project-local skills into ~/.codex/skills."""

import shutil
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    source_root = repo_root / "skills"
    target_root = Path.home() / ".codex" / "skills"
    target_root.mkdir(parents=True, exist_ok=True)

    for skill_dir in sorted(path for path in source_root.iterdir() if path.is_dir()):
        destination = target_root / skill_dir.name
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(skill_dir, destination)
        print(f"installed {skill_dir.name} -> {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
