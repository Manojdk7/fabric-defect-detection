#!/usr/bin/env python3
"""
Merge multiple YOLO fabric datasets into datasets/combined_fabric.

Unified classes: 0=hole, 1=tear, 2=stain

Sources (by default):
  - datasets/roboflow_saad          (Roboflow: Hole, Knot→tear, Stain)
  - datasets/fabric_defects/temp_extract/FD_Dataset/YOLO  (FD: 0 hole, 2 stain, 3 tear)
  - datasets/roboflow_fabric_defects  (77bcs: hole, knots→tear, spot→stain)
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from config import BASE_DIR

# Unified class IDs used by the app
UNIFIED_NAMES = ["hole", "tear", "stain"]
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def remap_roboflow_saad_line(parts: list[str]) -> str | None:
    """Roboflow export: 0=Hole, 1=Knot, 2=Stain → hole, tear, stain."""
    if len(parts) < 5:
        return None
    cls = int(float(parts[0]))
    mapping = {0: 0, 1: 1, 2: 2}
    if cls not in mapping:
        return None
    parts[0] = str(mapping[cls])
    return " ".join(parts)


def remap_fabric_defects_77bcs_line(parts: list[str]) -> str | None:
    """Fabric Defects 77bcs (20 classes): hole, knots, spot → hole, tear, stain."""
    if len(parts) < 5:
        return None
    cls = int(float(parts[0]))
    mapping = {10: 0, 11: 1, 19: 2}  # hole, knots, spot
    if cls not in mapping:
        return None
    parts[0] = str(mapping[cls])
    return " ".join(parts)


def remap_fd_dataset_line(parts: list[str]) -> str | None:
    """FD YOLO: 0=hole, 1=unused, 2=stain, 3=tear."""
    if len(parts) < 5:
        return None
    cls = int(float(parts[0]))
    mapping = {0: 0, 2: 2, 3: 1}
    if cls not in mapping:
        return None
    parts[0] = str(mapping[cls])
    return " ".join(parts)


def remap_generic_line(parts: list[str], class_map: dict[int, int]) -> str | None:
    if len(parts) < 5:
        return None
    cls = int(float(parts[0]))
    if cls not in class_map:
        return None
    parts[0] = str(class_map[cls])
    return " ".join(parts)


def find_image(images_dir: Path, stem: str) -> Path | None:
    for ext in IMAGE_EXTENSIONS:
        candidate = images_dir / f"{stem}{ext}"
        if candidate.exists():
            return candidate
    return None


def copy_split(
    source_root: Path,
    split: str,
    dest_root: Path,
    prefix: str,
    remap_fn,
) -> tuple[int, int]:
    images_dir = source_root / split / "images"
    labels_dir = source_root / split / "labels"
    if not images_dir.exists():
        return 0, 0

    dest_images = dest_root / split / "images"
    dest_labels = dest_root / split / "labels"
    dest_images.mkdir(parents=True, exist_ok=True)
    dest_labels.mkdir(parents=True, exist_ok=True)

    copied = 0
    skipped = 0

    for label_path in labels_dir.glob("*.txt"):
        stem = label_path.stem
        image_path = find_image(images_dir, stem)
        if not image_path:
            skipped += 1
            continue

        lines_out = []
        for raw in label_path.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            remapped = remap_fn(raw.split())
            if remapped:
                lines_out.append(remapped)

        if not lines_out:
            skipped += 1
            continue

        safe_stem = f"{prefix}{stem}"[:180]
        shutil.copy2(image_path, dest_images / f"{safe_stem}{image_path.suffix.lower()}")
        (dest_labels / f"{safe_stem}.txt").write_text("\n".join(lines_out) + "\n", encoding="utf-8")
        copied += 1

    return copied, skipped


def write_data_yaml(dest_root: Path) -> None:
    yaml_content = f"""# Merged fabric defect datasets (hole, tear, stain)
path: datasets/combined_fabric
train: train/images
val: valid/images
test: test/images

nc: 3
names:
  0: hole
  1: tear
  2: stain
"""
    (dest_root / "data.yaml").write_text(yaml_content, encoding="utf-8")


def merge_datasets(dest_root: Path, sources: list[tuple[Path, str, callable]]) -> None:
    if dest_root.exists():
        shutil.rmtree(dest_root)
    dest_root.mkdir(parents=True)

    totals = {"train": 0, "valid": 0, "test": 0}
    for source_root, prefix, remap_fn in sources:
        if not source_root.exists():
            print(f"[!] Skip missing source: {source_root}")
            continue
        print(f"\n[+] Merging {source_root.name} (prefix={prefix})")
        for split in ("train", "valid", "test"):
            n, skipped = copy_split(source_root, split, dest_root, prefix, remap_fn)
            totals[split] += n
            if n or skipped:
                print(f"    {split}: {n} images ({skipped} skipped)")

    write_data_yaml(dest_root)
    print("\n" + "=" * 60)
    print("COMBINED DATASET READY")
    print("=" * 60)
    print(f"Output: {dest_root}")
    print(f"  train: {totals['train']} images")
    print(f"  valid: {totals['valid']} images")
    print(f"  test:  {totals['test']} images")
    print(f"  classes: {', '.join(UNIFIED_NAMES)}")
    print("\nNext: python train_fabric_detector.py")


def default_sources() -> list[tuple[Path, str, callable]]:
    return [
        (
            BASE_DIR / "datasets" / "roboflow_saad",
            "saad_",
            remap_roboflow_saad_line,
        ),
        (
            BASE_DIR / "datasets" / "fabric_defects" / "temp_extract" / "FD_Dataset" / "YOLO",
            "fd_",
            remap_fd_dataset_line,
        ),
        (
            BASE_DIR / "datasets" / "roboflow_fabric_defects",
            "77bcs_",
            remap_fabric_defects_77bcs_line,
        ),
    ]


def main():
    parser = argparse.ArgumentParser(description="Merge YOLO fabric datasets")
    parser.add_argument(
        "--output",
        default=str(BASE_DIR / "datasets" / "combined_fabric"),
        help="Output dataset directory",
    )
    parser.add_argument(
        "--extra",
        nargs="*",
        default=[],
        help="Extra dataset roots (YOLO layout: train/valid/test with images+labels)",
    )
    args = parser.parse_args()

    sources = default_sources()
    for i, extra in enumerate(args.extra):
        extra_path = Path(extra)
        if not extra_path.is_absolute():
            extra_path = BASE_DIR / extra_path
        sources.append(
            (
                extra_path,
                f"extra{i}_",
                lambda parts, _m={0: 0, 1: 1, 2: 2}: remap_generic_line(parts, _m),
            )
        )

    merge_datasets(Path(args.output), sources)


if __name__ == "__main__":
    main()
