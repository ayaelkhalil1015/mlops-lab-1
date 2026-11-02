"""Validate processed data without modifying it."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from PIL import Image

from food11.data import CLASSES, SPLITS


def validate(root: Path, min_per_class: int = 50, tau: float = 0.05) -> bool:
    failures = []
    counts = {}
    checks = {
        split: {
            name: True
            for name in (
                "11 class directories",
                "minimum images per class",
                "readable images",
                "RGB images",
                "128x128 images",
                "no cross-split duplicates",
            )
        }
        for split in SPLITS
    }
    hashes: dict[str, tuple[str, Path]] = {}
    for split in SPLITS:
        directory = root / split
        classes = (
            {p.name for p in directory.iterdir() if p.is_dir()}
            if directory.is_dir()
            else set()
        )
        if classes != set(CLASSES):
            checks[split]["11 class directories"] = False
            failures.append(
                f"{split}: expected exactly the 11 Food-11 class directories"
            )
        counts[split] = {}
        for category in CLASSES:
            folder = directory / category
            files = (
                sorted(p for p in folder.rglob("*") if p.is_file())
                if folder.is_dir()
                else []
            )
            counts[split][category] = len(files)
            if len(files) < min_per_class:
                checks[split]["minimum images per class"] = False
                failures.append(
                    f"{split}/{category}: {len(files)} images < {min_per_class}"
                )
            for path in files:
                try:
                    with Image.open(path) as img:
                        img.load()
                        if img.mode != "RGB":
                            checks[split]["RGB images"] = False
                        if img.size != (128, 128):
                            checks[split]["128x128 images"] = False
                        if img.mode != "RGB" or img.size != (128, 128):
                            failures.append(
                                f"{path}: expected RGB 128x128, got {img.mode} {img.size}"
                            )
                    digest = hashlib.md5(
                        path.read_bytes(), usedforsecurity=False
                    ).hexdigest()
                    if digest in hashes and hashes[digest][0] != split:
                        checks[split]["no cross-split duplicates"] = False
                        checks[hashes[digest][0]]["no cross-split duplicates"] = False
                        failures.append(
                            f"duplicate across splits: {path} and {hashes[digest][1]}"
                        )
                    else:
                        hashes[digest] = (split, path)
                except (OSError, ValueError) as exc:
                    checks[split]["readable images"] = False
                    failures.append(f"{path}: cannot read image: {exc}")
    train_total = sum(counts["training"].values())
    val_total = sum(counts["validation"].values())
    distribution_ok = True
    if not train_total or not val_total:
        distribution_ok = False
        failures.append("distribution: training and validation must be nonempty")
    else:
        for category in CLASSES:
            delta = abs(
                counts["training"][category] / train_total
                - counts["validation"][category] / val_total
            )
            if delta > tau:
                distribution_ok = False
                failures.append(
                    f"distribution: {category} difference {delta:.6f} > {tau}"
                )
    for split, results in checks.items():
        for name, passed in results.items():
            print(f"{'PASS' if passed else 'FAIL'}: {split}: {name}")
    print(
        f"{'PASS' if distribution_ok else 'FAIL'}: training/validation class proportions (tau={tau})"
    )
    for failure in failures:
        print(f"FAIL: {failure}")
    print(
        "FAIL: dataset validation"
        if failures
        else "PASS: dataset validation (including class proportions)"
    )
    return not failures


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--min-per-class", type=int, default=50)
    parser.add_argument("--tau", type=float, default=0.05)
    args = parser.parse_args()
    if args.min_per_class < 1 or not 0 <= args.tau <= 1:
        parser.error("min-per-class must be positive and tau must be between 0 and 1")
    raise SystemExit(0 if validate(args.root, args.min_per_class, args.tau) else 1)


if __name__ == "__main__":
    main()
