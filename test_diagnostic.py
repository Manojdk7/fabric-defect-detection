#!/usr/bin/env python
"""
Simple diagnostic - test online images with better error handling
"""

import os
import sys

print("\n" + "="*70)
print("STARTING ONLINE IMAGE TEST...")
print("="*70)
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")

try:
    import requests
    print("✓ requests library imported")
except ImportError as e:
    print(f"✗ Error importing requests: {e}")
    print("Installing requests...")
    os.system("pip install requests")

try:
    from ultralytics import YOLO
    print("✓ ultralytics library imported")
except ImportError as e:
    print(f"✗ Error importing ultralytics: {e}")
    sys.exit(1)

try:
    import cv2
    print("✓ opencv library imported")
except ImportError as e:
    print(f"✗ Error importing cv2: {e}")
    sys.exit(1)

print("\n[1] Checking model file...")
MODEL_PATH = "models/retrained_model_test/weights/best.pt"
if os.path.exists(MODEL_PATH):
    size = os.path.getsize(MODEL_PATH) / (1024**2)
    print(f"✓ Model found: {MODEL_PATH}")
    print(f"  Size: {size:.2f} MB")
else:
    print(f"✗ Model NOT found: {MODEL_PATH}")
    sys.exit(1)

print("\n[2] Loading YOLO model...")
try:
    model = YOLO(MODEL_PATH)
    print("✓ Model loaded successfully")
except Exception as e:
    print(f"✗ Failed to load model: {e}")
    sys.exit(1)

print("\n[3] Testing with LOCAL sample image...")
sample_path = "datasets/fabric_defects/images/photo_2023-11-19_18-10-08_jpg.rf.db41ad69486d59a031eb3f17918b8920.jpg"
if os.path.exists(sample_path):
    print(f"✓ Sample image found: {sample_path.split('/')[-1]}")
    try:
        results = model.predict(sample_path, conf=0.25, verbose=False)
        num_detections = len(results[0].boxes) if results[0].boxes else 0
        print(f"✓ Inference successful: {num_detections} objects detected")
    except Exception as e:
        print(f"✗ Inference failed: {e}")
else:
    print(f"✗ Sample image not found")

print("\n[4] Attempting to download ONLINE fabric image...")
print("Trying Pexels image...")

try:
    import requests
    from pathlib import Path
    
    test_url = "https://images.pexels.com/photos/4551832/pexels-photo-4551832.jpeg"
    print(f"URL: {test_url}")
    print("Downloading...", end=" ", flush=True)
    
    response = requests.get(test_url, timeout=10)
    print(f"HTTP {response.status_code}...", end=" ", flush=True)
    
    if response.status_code == 200:
        os.makedirs("test_images_online", exist_ok=True)
        file_path = "test_images_online/pexels_test.jpg"
        
        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        file_size = os.path.getsize(file_path) / 1024
        print(f"Downloaded ({file_size:.1f} KB)!")
        print(f"✓ Saved to: {file_path}")
        
        print("\nTesting online image with model...")
        print("Running inference...", end=" ", flush=True)
        
        results = model.predict(file_path, conf=0.25, verbose=False)
        num_detections = len(results[0].boxes) if results[0].boxes else 0
        
        print(f"Done!")
        print(f"✓ Detections: {num_detections} objects found")
        
        if num_detections > 0:
            confidences = [float(b.conf[0]) for b in results[0].boxes]
            print(f"  Average confidence: {sum(confidences) / len(confidences):.4f}")
            print(f"  Max confidence: {max(confidences):.4f}")
            print(f"  Min confidence: {min(confidences):.4f}")
    else:
        print(f"✗ HTTP Error {response.status_code}")
        
except requests.exceptions.ConnectionError as e:
    print(f"\n✗ Connection Error: No internet or URL unreachable")
    print(f"  Details: {str(e)[:100]}")
except requests.exceptions.Timeout as e:
    print(f"\n✗ Timeout: Request took too long")
    print(f"  Details: {str(e)[:100]}")
except Exception as e:
    print(f"\n✗ Error: {e}")
    print(f"  Type: {type(e).__name__}")

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)
print("\nFiles created: check test_images_online/ folder")
print("\nTo test Flask API:")
print("  python app.py")
print("="*70 + "\n")
