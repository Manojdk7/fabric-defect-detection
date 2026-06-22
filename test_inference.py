#!/usr/bin/env python
"""
Test inference on sample images using the trained model
"""

import cv2
import os
from pathlib import Path
from ultralytics import YOLO
import json
from datetime import datetime

# Model path
MODEL_PATH = "models/retrained_model_test/weights/best.pt"
SAMPLE_IMAGES_DIR = "datasets/fabric_defects/images"
OUTPUT_DIR = "inspection_results"

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

def run_inference():
    """Run inference on sample images"""
    
    # Load the trained model
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Model not found at {MODEL_PATH}")
        return
    
    print(f"✓ Loading model from: {MODEL_PATH}")
    model = YOLO(MODEL_PATH)
    
    # Get sample images
    image_dir = Path(SAMPLE_IMAGES_DIR)
    if not image_dir.exists():
        print(f"❌ Image directory not found: {SAMPLE_IMAGES_DIR}")
        return
    
    # Get first 5 images
    image_files = sorted(list(image_dir.glob("*.jpg")))[:5]
    
    if not image_files:
        print("❌ No images found in dataset")
        return
    
    print(f"\n✓ Found {len(image_files)} sample images\n")
    
    results_summary = {
        "timestamp": datetime.now().isoformat(),
        "model": MODEL_PATH,
        "detections": []
    }
    
    # Run inference on each image
    for image_path in image_files:
        print(f"Processing: {image_path.name}")
        
        # Run inference
        results = model.predict(source=str(image_path), conf=0.25, verbose=False)
        
        for result in results:
            boxes = result.boxes.cpu().numpy()
            
            # Count detections
            num_detections = len(boxes)
            
            detection_info = {
                "image": image_path.name,
                "detections_count": num_detections,
                "boxes": []
            }
            
            # Get detection details
            if num_detections > 0:
                for i, box in enumerate(boxes):
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    
                    detection_info["boxes"].append({
                        "id": i + 1,
                        "confidence": round(conf, 4),
                        "class": cls,
                        "bbox": {
                            "x1": round(x1, 2),
                            "y1": round(y1, 2),
                            "x2": round(x2, 2),
                            "y2": round(y2, 2)
                        }
                    })
                
                print(f"  ✓ {num_detections} object(s) detected")
                for box_info in detection_info["boxes"]:
                    print(f"    - Box {box_info['id']}: confidence={box_info['confidence']}")
            else:
                print(f"  ✓ No objects detected")
            
            results_summary["detections"].append(detection_info)
            
            # Save annotated image
            annotated_image = result.plot()
            output_image_path = os.path.join(OUTPUT_DIR, f"result_{image_path.stem}.jpg")
            cv2.imwrite(output_image_path, annotated_image)
            print(f"  ✓ Saved: {output_image_path}\n")
    
    # Save results summary
    results_file = os.path.join(OUTPUT_DIR, "inference_results.json")
    with open(results_file, 'w') as f:
        json.dump(results_summary, f, indent=2)
    
    print(f"\n✓ Inference complete!")
    print(f"✓ Results saved to: {results_file}")
    print(f"✓ Annotated images saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    run_inference()
