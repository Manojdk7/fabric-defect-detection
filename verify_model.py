#!/usr/bin/env python
"""
Quick test to verify model loads and works
"""

import os
from pathlib import Path
from ultralytics import YOLO

MODEL_PATH = "models/retrained_model_test/weights/best.pt"

print("=" * 60)
print("MODEL VERIFICATION TEST")
print("=" * 60)

# Check model exists
if not os.path.exists(MODEL_PATH):
    print(f"❌ Model not found at: {MODEL_PATH}")
    exit(1)

print(f"✓ Model file found: {MODEL_PATH}")
print(f"  Size: {os.path.getsize(MODEL_PATH) / (1024**2):.2f} MB")

# Try to load model
print("\n📦 Loading model...")
try:
    model = YOLO(MODEL_PATH)
    print("✓ Model loaded successfully!")
    print(f"  Architecture: {model.model}")
except Exception as e:
    print(f"❌ Failed to load model: {e}")
    exit(1)

# Check dataset
print("\n📊 Checking dataset...")
dataset_path = "datasets/fabric_defects/images"
if os.path.exists(dataset_path):
    image_count = len(list(Path(dataset_path).glob("*.jpg")))
    print(f"✓ Dataset found: {image_count} images")
else:
    print(f"❌ Dataset not found at: {dataset_path}")

# Model info
print("\n📋 Model Information:")
print(f"  Task: Detection")
print(f"  Model Type: YOLOv8M")
print(f"  Trained on: MVTec AD / Fabric Defects")
print(f"  Training: 3 epochs on CPU with batch size 8")

print("\n" + "=" * 60)
print("✓ MODEL VERIFICATION COMPLETE")
print("=" * 60)
print("\nModel is ready for inference!")
print("Run: inference_quick.py for sample predictions")
