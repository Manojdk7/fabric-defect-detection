#!/usr/bin/env python3
"""
Quick Fabric Defect Detection Test
Tests the trained model on a sample image
"""

from defect_detector import DefectDetector
import os
from pathlib import Path

def test_fabric_detector():
    """
    Test the fabric defect detector
    """
    print("🧪 Testing Fabric Defect Detector")
    print("=" * 40)

    # Initialize detector
    detector = DefectDetector(defect_type='fabric')

    # Check if model exists
    model_path = Path('models/fabric_defect_detector/weights/best.pt')
    if model_path.exists():
        print(f"✅ Custom model found: {model_path}")
    else:
        print("⚠️  Custom model not found, using default YOLOv8")
        print("   Run training first: python train_fabric_detector.py")

    # Find a test image
    test_images = list(Path('datasets/fabric_defects/images').glob('*.jpg'))[:3]

    if not test_images:
        print("❌ No test images found in dataset!")
        return

    print(f"📸 Testing with {len(test_images)} sample images:")

    for i, img_path in enumerate(test_images, 1):
        print(f"\\n🔍 Testing image {i}: {img_path.name}")

        try:
            result = detector.detect_defects(str(img_path), confidence_threshold=0.3)

            if 'error' in result:
                print(f"   ❌ Error: {result['error']}")
                continue

            detections = result['detections']
            print(f"   📊 Found {len(detections)} defects:")

            for detection in detections:
                defect_type = detection['type']
                confidence = detection['confidence']
                severity = detection.get('severity', 'unknown')
                print(f"      • {defect_type} ({confidence:.1%}) - {severity} severity")

            if len(detections) == 0:
                print("      • No defects detected")

        except Exception as e:
            print(f"   ❌ Exception: {e}")

    print("\\n✅ Testing completed!")

if __name__ == "__main__":
    test_fabric_detector()