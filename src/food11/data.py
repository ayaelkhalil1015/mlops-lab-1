"""Food-11 preprocessing: resize raw images to 128x128 and organize by class.

Reads data/food11_raw/{training,evaluation,validation}/<class>_<idx>.jpg,
resizes every image to 128x128, and writes two ImageFolder-style datasets:
  - data/food11_processed/<split>/<class_name>/...        (all images)
  - data/food11_processed_mini/<split>/<class_name>/...    (<=100 images each)

Run with: uv run python ./src/food11/data.py
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from PIL import Image, ImageOps

SPLITS = ("training", "evaluation", "validation")

CLASS_NAMES = {
    0: "Bread",
    1: "Dairy product",
    2: "Dessert",
    3: "Egg",
    4: "Fried food",
    5: "Meat",
    6: "Noodles-Pasta",
    7: "Rice",
    8: "Seafood",
    9: "Soup",
    10: "Vegetable-Fruit",
}

TARGET_SIZE = (128, 128)
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}
MINI_LIMIT = 100

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "food11_raw"
PROCESSED_DIR = REPO_ROOT / "data" / "food11_processed"
PROCESSED_MINI_DIR = REPO_ROOT / "data" / "food11_processed_mini"


def validate_raw_dataset() -> None:
    """Fail loudly if the raw dataset is missing or incomplete."""
    if not RAW_DIR.is_dir():
        sys.exit(f"Raw dataset not found at {RAW_DIR}. Expected data/food11_raw/.")
    for split in SPLITS:
        if not (RAW_DIR / split).is_dir():
            sys.exit(f"Missing raw split directory: {RAW_DIR / split}")


def parse_class_id(file_name: str) -> int:
    """Parse the numeric class id encoded at the start of a filename like '3_120.jpg'."""
    prefix = file_name.split("_", 1)[0]
    if not prefix.isdigit():
        raise ValueError(f"Cannot parse class id from filename: {file_name}")
    class_id = int(prefix)
    if class_id not in CLASS_NAMES:
        raise ValueError(f"Class id {class_id} out of range 0-10 (file: {file_name})")
    return class_id


def list_raw_images(split: str) -> list[Path]:
    """List valid raw image files for a split, sorted for deterministic ordering."""
    split_dir = RAW_DIR / split
    files = [
        f
        for f in split_dir.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    return sorted(files)


def prepare_output_directories() -> None:
    """Remove stale generated outputs and recreate the ImageFolder-style tree."""
    for out_dir in (PROCESSED_DIR, PROCESSED_MINI_DIR):
        if out_dir.exists():
            shutil.rmtree(out_dir)
        for split in SPLITS:
            for class_name in CLASS_NAMES.values():
                (out_dir / split / class_name).mkdir(parents=True, exist_ok=True)


def process_image(src_path: Path, dst_path: Path) -> None:
    """Open, normalize orientation, convert to RGB, resize, and save one image."""
    with Image.open(src_path) as img:
        img = ImageOps.exif_transpose(img)
        img = img.convert("RGB")
        img = img.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
        img.save(dst_path)


def process_split(split: str) -> dict[str, int]:
    """Process one split into both the full and mini processed datasets.

    Returns a mapping of class_name -> full-image count for reporting.
    """
    files = list_raw_images(split)
    by_class: dict[int, list[Path]] = {class_id: [] for class_id in CLASS_NAMES}
    for f in files:
        class_id = parse_class_id(f.name)
        by_class[class_id].append(f)

    counts: dict[str, int] = {}
    for class_id, class_files in by_class.items():
        class_name = CLASS_NAMES[class_id]
        for f in class_files:
            process_image(f, PROCESSED_DIR / split / class_name / f.name)
        for f in sorted(class_files)[:MINI_LIMIT]:
            process_image(f, PROCESSED_MINI_DIR / split / class_name / f.name)
        counts[class_name] = len(class_files)
    return counts


def validate_processed_dataset(raw_counts: dict[str, dict[str, int]]) -> None:
    """Check structure, counts, and image dimensions of both processed datasets."""
    for split in SPLITS:
        for class_name in CLASS_NAMES.values():
            full_dir = PROCESSED_DIR / split / class_name
            mini_dir = PROCESSED_MINI_DIR / split / class_name
            if not full_dir.is_dir() or not mini_dir.is_dir():
                sys.exit(f"Missing expected output directory: {full_dir} or {mini_dir}")

            full_files = list(full_dir.iterdir())
            expected_full = raw_counts[split][class_name]
            if len(full_files) != expected_full:
                sys.exit(
                    f"Count mismatch in {full_dir}: got {len(full_files)}, "
                    f"expected {expected_full}"
                )

            expected_mini = min(expected_full, MINI_LIMIT)
            mini_files = list(mini_dir.iterdir())
            if len(mini_files) != expected_mini:
                sys.exit(
                    f"Count mismatch in {mini_dir}: got {len(mini_files)}, "
                    f"expected {expected_mini}"
                )

            for check_file in full_files[:3]:
                with Image.open(check_file) as img:
                    if img.size != TARGET_SIZE:
                        sys.exit(f"Wrong size for {check_file}: {img.size}")


def print_report(raw_counts: dict[str, dict[str, int]]) -> None:
    total_raw = sum(sum(c.values()) for c in raw_counts.values())
    total_mini = sum(
        min(count, MINI_LIMIT)
        for split_counts in raw_counts.values()
        for count in split_counts.values()
    )

    print("\nFood-11 preprocessing completed\n")
    for split in SPLITS:
        print(f"{split}:")
        for class_name in CLASS_NAMES.values():
            print(f"  {class_name}: {raw_counts[split][class_name]}")

    print(f"\nTotal raw/processed images: {total_raw}")
    print(f"Total mini images: {total_mini}")
    print(f"Target resolution: {TARGET_SIZE[0]}x{TARGET_SIZE[1]}")
    print(f"Full dataset output: {PROCESSED_DIR}")
    print(f"Mini dataset output: {PROCESSED_MINI_DIR}")


def main() -> None:
    validate_raw_dataset()
    prepare_output_directories()

    raw_counts = {split: process_split(split) for split in SPLITS}

    validate_processed_dataset(raw_counts)
    print_report(raw_counts)


if __name__ == "__main__":
    main()
