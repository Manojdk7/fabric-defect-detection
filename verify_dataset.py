#!/usr/bin/env python3
"""
Fabric Defect Dataset Verification Script
Checks dataset integrity and provides statistics
"""

import os
from pathlib import Path
import cv2
import yaml

def verify_dataset():
    """
    Verify the fabric defect dataset integrity
    """
    dataset_path = Path('datasets/fabric_defects')
    images_path = dataset_path / 'images'
    labels_path = dataset_path / 'labels'

    print("🔍 Verifying Fabric Defect Dataset")
    print("=" * 50)

    # Check directories exist
    if not images_path.exists():
        print("❌ Images directory not found!")
        return False

    if not labels_path.exists():
        print("❌ Labels directory not found!")
        return False

    # Get file lists
    image_files = list(images_path.glob('*.jpg')) + list(images_path.glob('*.png')) + list(images_path.glob('*.jpeg'))
    label_files = list(labels_path.glob('*.txt'))

    print(f"📁 Images found: {len(image_files)}")
    print(f"🏷️  Labels found: {len(label_files)}")

    # Check for matching files
    image_names = {f.stem for f in image_files}
    label_names = {f.stem for f in label_files}

    matched = image_names & label_names
    missing_labels = image_names - label_names
    extra_labels = label_names - image_names

    print(f"✅ Matched pairs: {len(matched)}")
    if missing_labels:
        print(f"⚠️  Images without labels: {len(missing_labels)}")
    if extra_labels:
        print(f"⚠️  Labels without images: {len(extra_labels)}")

    # Analyze label contents
    class_counts = {}
    total_annotations = 0

    for label_file in label_files[:100]:  # Check first 100 files
        try:
            with open(label_file, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        class_id = int(parts[0])
                        class_counts[class_id] = class_counts.get(class_id, 0) + 1
                        total_annotations += 1
        except Exception as e:
            print(f"Error reading {label_file}: {e}")

    print(f"\\n📊 Dataset Statistics:")
    print(f"   Total annotations: {total_annotations}")
    print(f"   Classes found: {sorted(class_counts.keys())}")
    for class_id, count in sorted(class_counts.items()):
        print(f"   Class {class_id}: {count} instances")

    # Check data.yaml
    config_path = dataset_path / 'data.yaml'
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        print(f"\\n⚙️  Config classes: {len(config.get('names', []))}")
        print(f"   Class names: {config.get('names', [])}")
    else:
        print("\\n❌ data.yaml not found!")

    # Sample image check
    if image_files:
        sample_img = cv2.imread(str(image_files[0]))
        if sample_img is not None:
            h, w = sample_img.shape[:2]
            print(f"\\n🖼️  Sample image: {w}x{h} pixels")
        else:
            print("\\n❌ Cannot read sample image!")

    print("\\n✅ Dataset verification completed!")
    return len(image_files) > 0 and len(label_files) > 0

if __name__ == "__main__":
    verify_dataset()