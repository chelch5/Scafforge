#!/usr/bin/env python3
"""Asset provenance validator.

Checks that every file in assets/ (excluding briefs/ and pipeline.json)
has a corresponding entry in assets/PROVENANCE.md.
"""

import os
import re
import sys
from pathlib import Path


def parse_provenance(provenance_path: Path) -> set[str]:
    """Extract asset paths from PROVENANCE.md table."""
    paths = set()
    if not provenance_path.exists():
        return paths

    content = provenance_path.read_text()
    # Match table rows: | asset_path | source | license | author | date |
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("|") and not line.startswith("| asset_path") and not line.startswith("|---"):
            cells = [c.strip() for c in line.split("|")]
            if len(cells) >= 2 and cells[1]:
                paths.add(cells[1])
    return paths


def find_asset_files(assets_dir: Path) -> set[str]:
    """Find all asset files that need provenance tracking."""
    skip_dirs = {"briefs"}
    skip_files = {"pipeline.json", "PROVENANCE.md", ".gdignore"}
    asset_files = set()

    for root, dirs, files in os.walk(assets_dir):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        rel_root = Path(root).relative_to(assets_dir.parent)

        for f in files:
            if f in skip_files or f.startswith("."):
                continue
            asset_files.add(str(rel_root / f))

    return asset_files


def main():
    project_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    assets_dir = project_root / "assets"

    if not assets_dir.exists():
        print("No assets/ directory found.")
        sys.exit(0)

    provenance_path = assets_dir / "PROVENANCE.md"
    tracked = parse_provenance(provenance_path)
    actual = find_asset_files(assets_dir)

    untracked = actual - tracked
    orphaned = tracked - actual

    if untracked:
        print(f"FAIL: {len(untracked)} asset(s) missing from PROVENANCE.md:")
        for p in sorted(untracked):
            print(f"  - {p}")

    if orphaned:
        print(f"WARN: {len(orphaned)} PROVENANCE.md entries reference missing files:")
        for p in sorted(orphaned):
            print(f"  - {p}")

    if not untracked and not orphaned:
        print(f"OK: {len(actual)} assets tracked, all accounted for.")
        sys.exit(0)
    elif untracked:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
