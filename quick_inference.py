#!/usr/bin/env python
"""
Quick inference test on sample images - Fast version
"""

import os
from pathlib import Path
from ultralytics import YOLO
import json
from datetime import datetime

MODEL_PATH = "models/retrained_model_test/weights/best.pt"
SAMPLE_IMAGES_DIR = "datasets/fabric_defects/images"
OUTPUT_DIR = "inspection_results"

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("\n" + "="*70)
print("QUICK INFERENCE TEST - FABRIC DEFECT DETECTION")
print("="*70)

# Load model
print("\n[1/4] Loading model...")
if not os.path.exists(MODEL_PATH):
    print(f"ERROR: Model not found at {MODEL_PATH}")
    exit(1)

try:
    model = YOLO(MODEL_PATH)
    print("SUCCESS: Model loaded")
except Exception as e:
    print(f"ERROR loading model: {e}")
    exit(1)

# Get sample images
print("\n[2/4] Finding sample images...")
image_dir = Path(SAMPLE_IMAGES_DIR)
if not image_dir.exists():
    print(f"ERROR: {SAMPLE_IMAGES_DIR} not found")
    exit(1)

image_files = sorted(list(image_dir.glob("*.jpg")))[:2]  # Just 2 images for speed
if not image_files:
    print("ERROR: No images found")
    exit(1)

print(f"Found {len(image_files)} sample images for testing")

# Run inference
print("\n[3/4] Running inference...")
results_data = {
    "timestamp": datetime.now().isoformat(),
    "model_path": MODEL_PATH,
    "total_images": len(image_files),
    "detections": []
}

for idx, img_path in enumerate(image_files, 1):
    print(f"\n  [{idx}/{len(image_files)}] Processing: {img_path.name}")
    
    try:
        # Run inference with conf threshold
        results = model.predict(
            source=str(img_path), 
            conf=0.25, 
            verbose=False,
            device=0  # Try GPU, fall back to CPU
        )
        
        if results and len(results) > 0:
            result = results[0]
            boxes = result.boxes.cpu().numpy() if result.boxes else None
            
            if boxes is not None and len(boxes) > 0:
                num_detections = len(boxes)
                print(f"     DETECTIONS: {num_detections} object(s) found")
                
                detection_list = []
                for box_idx, box in enumerate(boxes, 1):
                    conf = float(box.conf[0])
                    print(f"       - Object {box_idx}: confidence = {conf:.4f}")
                    detection_list.append({
                        "object_id": box_idx,
                        "confidence": round(conf, 4)
                    })
                
                results_data["detections"].append({
                    "image": img_path.name,
                    "detections_count": num_detections,
                    "objects": detection_list
                })
            else:
                print(f"     No defects detected in this image")
                results_data["detections"].append({
                    "image": img_path.name,
                    "detections_count": 0,
                    "objects": []
                })
    
    except Exception as e:
        print(f"     ERROR: {str(e)[:80]}")

# Save results
print("\n[4/4] Saving results...")
results_file = os.path.join(OUTPUT_DIR, "quick_inference_results.json")
with open(results_file, 'w') as f:
    json.dump(results_data, f, indent=2)

print(f"SUCCESS: Results saved to {results_file}")

# Summary
print("\n" + "="*70)
print("INFERENCE COMPLETE")
print("="*70)
print(f"Total images tested: {len(image_files)}")
print(f"Total detections: {sum(d['detections_count'] for d in results_data['detections'])}")
print(f"Results saved: {results_file}")
print("="*70 + "\n")
