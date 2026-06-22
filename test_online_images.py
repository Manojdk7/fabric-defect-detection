#!/usr/bin/env python
"""
Download and test fabric images from online sources
"""

import requests
import os
from pathlib import Path
from ultralytics import YOLO
import json
from datetime import datetime

MODEL_PATH = "models/retrained_model_test/weights/best.pt"
DOWNLOAD_DIR = "test_images_online"
RESULTS_DIR = "inspection_results"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# Good fabric images for testing
TEST_IMAGES = {
    "pexels_fabric_1": "https://images.pexels.com/photos/4551832/pexels-photo-4551832.jpeg",
    "pexels_fabric_2": "https://images.pexels.com/photos/5632399/pexels-photo-5632399.jpeg",
    "pexels_fabric_3": "https://images.pexels.com/photos/5866438/pexels-photo-5866438.jpeg",
    "unsplash_cloth": "https://images.unsplash.com/photo-1598394692202-bf96a3ee82c9",
    "pixabay_weave": "https://pixabay.com/get/gd5cd8f46a9d2b2b4e7b7f3c6c6d6f8f8f/fabric-2837.jpg",
}

print("\n" + "="*70)
print("ONLINE FABRIC DEFECT MODEL TEST")
print("="*70)

# Load model
print("\n[1] Loading trained model...")
if not os.path.exists(MODEL_PATH):
    print(f"ERROR: Model not found at {MODEL_PATH}")
    exit(1)

model = YOLO(MODEL_PATH)
print("SUCCESS: Model loaded (197 MB)")

# Download and test images
print("\n[2] Downloading test images from online sources...")
downloaded_images = {}
for img_name, img_url in TEST_IMAGES.items():
    try:
        print(f"\n  Downloading: {img_name}...", end=" ")
        response = requests.get(img_url, timeout=10)
        
        if response.status_code == 200:
            file_path = os.path.join(DOWNLOAD_DIR, f"{img_name}.jpg")
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            file_size = os.path.getsize(file_path) / 1024
            print(f"OK ({file_size:.1f} KB)")
            downloaded_images[img_name] = file_path
        else:
            print(f"FAILED (HTTP {response.status_code})")
    except Exception as e:
        print(f"ERROR: {str(e)[:50]}")

if not downloaded_images:
    print("\nNo images downloaded. Please check your internet connection.")
    exit(1)

print(f"\nSuccessfully downloaded: {len(downloaded_images)} images")

# Run inference
print("\n[3] Running inference on downloaded images...")
results_data = {
    "timestamp": datetime.now().isoformat(),
    "model": MODEL_PATH,
    "images_tested": len(downloaded_images),
    "total_detections": 0,
    "results": []
}

for img_name, img_path in downloaded_images.items():
    print(f"\n  Testing: {img_name}...", end=" ")
    
    try:
        # Run inference
        results = model.predict(
            source=img_path, 
            conf=0.25, 
            verbose=False,
            device=0  # GPU, falls back to CPU
        )
        
        if results and len(results) > 0:
            boxes = results[0].boxes
            num_detections = len(boxes) if boxes else 0
            
            print(f"{num_detections} objects detected")
            
            detection_info = {
                "image": img_name,
                "url": TEST_IMAGES[img_name],
                "detections": num_detections,
                "local_path": img_path
            }
            
            if num_detections > 0:
                confidences = [float(b.conf[0]) for b in boxes]
                detection_info["avg_confidence"] = round(sum(confidences) / len(confidences), 4)
                detection_info["max_confidence"] = round(max(confidences), 4)
                detection_info["min_confidence"] = round(min(confidences), 4)
                results_data["total_detections"] += num_detections
            
            results_data["results"].append(detection_info)
            
            # Save annotated image
            annotated_image = results[0].plot()
            import cv2
            output_path = os.path.join(RESULTS_DIR, f"result_{img_name}.jpg")
            cv2.imwrite(output_path, annotated_image)
            detection_info["annotated_image"] = output_path
            
    except Exception as e:
        print(f"ERROR: {str(e)[:50]}")

# Save results
print("\n[4] Saving results...")
results_file = os.path.join(RESULTS_DIR, "online_test_results.json")
with open(results_file, 'w') as f:
    json.dump(results_data, f, indent=2)

# Print summary
print("\n" + "="*70)
print("TEST SUMMARY")
print("="*70)
print(f"Images downloaded: {len(downloaded_images)}")
print(f"Images successfully tested: {len(results_data['results'])}")
print(f"Total defects detected: {results_data['total_detections']}")
print(f"\nResults saved to: {results_file}")
print(f"Downloaded images in: {DOWNLOAD_DIR}")
print(f"Annotated results in: {RESULTS_DIR}")

# Print detailed results
print("\n" + "-"*70)
print("DETAILED RESULTS:")
print("-"*70)
for result in results_data['results']:
    print(f"\n{result['image']}:")
    print(f"  URL: {result['url']}")
    print(f"  Defects detected: {result['detections']}")
    if result['detections'] > 0:
        print(f"  Confidence - Avg: {result['avg_confidence']}, Max: {result['max_confidence']}, Min: {result['min_confidence']}")
    print(f"  Annotated image: {result.get('annotated_image', 'N/A')}")

print("\n" + "="*70)
print("NEXT STEPS:")
print("="*70)
print("1. Check annotated images in inspection_results/")
print("2. Upload custom images to test further")
print("3. Deploy to Flask web app: python app.py")
print("="*70 + "\n")
