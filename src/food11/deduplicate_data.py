"""Create a separate processed dataset without exact cross-split duplicates.

Preserve evaluation first, then validation, then training. Never edit the source
or overwrite an existing destination. Review and version the derivative before
using it for new training or evaluation.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path

from food11.data import CLASSES
from food11.validate_data import validate

PRIORITY = ("evaluation", "validation", "training")


def clean_copy(source: Path, destination: Path) -> tuple[int, int]:
    source, destination = source.resolve(), destination.resolve()
    if (
        source == destination
        or source in destination.parents
        or destination in source.parents
    ):
        raise ValueError(
            "Source and destination must be separate, non-nested directories"
        )
    if destination.exists():
        raise ValueError("Destination already exists; refusing to overwrite it")
    for split in PRIORITY:
        folder = source / split
        if not folder.is_dir() or {
            p.name for p in folder.iterdir() if p.is_dir()
        } != set(CLASSES):
            raise ValueError(f"Missing or invalid class directories: {folder}")
    seen: dict[str, tuple[str, str, Path]] = {}
    kept = dropped = 0
    destination.mkdir(parents=True)
    for split in PRIORITY:
        for category in CLASSES:
            output = destination / split / category
            output.mkdir(parents=True)
            for path in sorted((source / split / category).rglob("*")):
                if not path.is_file():
                    continue
                digest = hashlib.md5(
                    path.read_bytes(), usedforsecurity=False
                ).hexdigest()
                if digest in seen and seen[digest][0] != split:
                    if seen[digest][1] != category:
                        raise ValueError(
                            f"Conflicting labels for identical contents: {path} and {seen[digest][2]}"
                        )
                    # Confirm actual equality before excluding a matching hash.
                    if path.read_bytes() != seen[digest][2].read_bytes():
                        raise ValueError(f"MD5 collision: {path}")
                    print(f"EXCLUDE from copy: {path}; retained {seen[digest][2]}")
                    dropped += 1
                    continue
                seen[digest] = (split, category, path)
                target = destination / path.relative_to(source)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
                kept += 1
    print(
        f"COPY: {kept} retained; {dropped} cross-split duplicates excluded; source unchanged"
    )
    return kept, dropped


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    try:
        clean_copy(args.source, args.destination)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Clean copy failed: {exc}\n")
    raise SystemExit(0 if validate(args.destination) else 1)


if __name__ == "__main__":
    main()
