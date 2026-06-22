#!/usr/bin/env python
"""
Simple sequential pipeline runner without Unicode characters
Runs each step in order
"""

import subprocess
import sys
import time

print("=" * 70)
print("QUALITY INSPECTION SYSTEM - RETRAINING PIPELINE")
print("=" * 70)

steps = [
    ("01_setup_data.py", "Setup MVTec Data"),
    ("02_augment_data.py", "Augment Dataset"),
    ("03_prepare_yolo_labels.py", "Create YOLO Labels"),
    ("04_retrain_model.py", "Train YOLOv8 Model"),
    ("05_validate_model.py", "Validate New Model"),
]

failed_steps = []

for i, (script, description) in enumerate(steps, 1):
    print(f"\n[STEP {i}/5] Running: {description}")
    print("-" * 70)
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, script],
            cwd="C:\\Users\\lenovo\\OneDrive\\Desktop\\Quality-inspection",
            capture_output=False,
            text=True
        )
        
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            print(f"[OK] {description} COMPLETE ({elapsed:.0f}s)")
        else:
            print(f"[ERROR] {description} FAILED with code {result.returncode}")
            failed_steps.append((i, script, description))
    
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[ERROR] Exception in {description}: {e}")
        failed_steps.append((i, script, description))

print("\n" + "=" * 70)
print("PIPELINE SUMMARY")
print("=" * 70)

if failed_steps:
    print(f"\nFailed {len(failed_steps)} steps:")
    for step_num, script, desc in failed_steps:
        print(f"  - Step {step_num}: {desc}")
else:
    print("\nAll steps completed successfully!")

print("\n" + "=" * 70)
