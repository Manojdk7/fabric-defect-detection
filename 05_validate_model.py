"""
Step 5: Validate and Test Improved Model
Creates a structured validation report for the trained model.
"""

import json
from datetime import datetime
from pathlib import Path

import torch
from ultralytics import YOLO

from config import Config


def first_existing(paths):
    for path in paths:
        if path.exists():
            return path
    return None


def safe_percent(value):
    return round(float(value) * 100, 2) if value is not None else 0


def validate_model():
    """Validate trained model and write a report to validation_reports/."""

    print("=" * 60)
    print("STEP 5: VALIDATE AND TEST MODEL")
    print("=" * 60)

    data_yaml = Config.MVTEC_DATA_DIR / "data.yaml"
    val_images = Config.MVTEC_DATA_DIR / "images" / "val"
    report_dir = Config.VALIDATION_REPORTS_DIR
    report_dir.mkdir(parents=True, exist_ok=True)

    model_path = first_existing(
        [
            Config.MODELS_DIR / "retrained_model_v2" / "weights" / "best.pt",
            Config.MODELS_DIR / "retrained_model_test" / "weights" / "best.pt",
            Path("runs/detect/models/fabric_defect_detector/weights/best.pt"),
        ]
    )

    if not model_path:
        print("[!] ERROR: No trained model found.")
        return

    if not data_yaml.exists():
        print(f"[!] ERROR: Dataset config not found: {data_yaml}")
        return

    device = 0 if torch.cuda.is_available() else "cpu"
    print(f"[+] Loading model: {model_path}")
    print(f"[+] Device: {device}")

    model = YOLO(str(model_path))
    report = {
        "generated_at": datetime.now().isoformat(),
        "model_path": str(model_path),
        "data_yaml": str(data_yaml),
        "device": str(device),
        "metrics": {},
        "speed_ms": {},
        "sample_tests": [],
        "comparison": {},
    }

    print("\n--- Validating Model ---")
    val_results = model.val(
        data=str(data_yaml),
        imgsz=640,
        batch=16,
        half=torch.cuda.is_available(),
        device=device,
    )

    if val_results and hasattr(val_results, "box"):
        report["metrics"] = {
            "map50_percent": safe_percent(val_results.box.map50),
            "map50_95_percent": safe_percent(val_results.box.map),
            "precision_percent": safe_percent(getattr(val_results.box, "mp", 0)),
            "recall_percent": safe_percent(getattr(val_results.box, "mr", 0)),
        }

    if val_results and hasattr(val_results, "speed"):
        report["speed_ms"] = {
            key: round(float(value), 2)
            for key, value in val_results.speed.items()
        }

    print("\n--- Testing Sample Images ---")
    test_images = list(val_images.glob("*.png"))[:10] if val_images.exists() else []
    correct_predictions = 0

    for img_path in test_images:
        results = model.predict(str(img_path), conf=0.65, augment=False, verbose=False)
        boxes = results[0].boxes if results else []
        confidence = float(boxes.conf[0]) if len(boxes) > 0 else 0
        has_defect = len(boxes) > 0 and confidence > 0.65
        filename = img_path.name.lower()
        is_defect_image = any(keyword in filename for keyword in ["hole", "cut", "tear", "color", "defect"])
        correct = has_defect == is_defect_image
        correct_predictions += int(correct)

        report["sample_tests"].append(
            {
                "filename": img_path.name,
                "expected_defect": is_defect_image,
                "predicted_defect": has_defect,
                "confidence_percent": round(confidence * 100, 2),
                "correct": correct,
            }
        )

    total_predictions = len(test_images)
    sample_accuracy = (correct_predictions / total_predictions * 100) if total_predictions else 0
    report["sample_accuracy_percent"] = round(sample_accuracy, 2)

    old_model_path = Path("yolov8n.pt")
    if old_model_path.exists() and test_images:
        old_model = YOLO(str(old_model_path))
        old_correct = 0

        for img_path in test_images:
            old_results = old_model.predict(str(img_path), conf=0.5, verbose=False)
            has_defect = len(old_results[0].boxes) > 0 if old_results else False
            filename = img_path.name.lower()
            is_defect_image = any(keyword in filename for keyword in ["hole", "cut", "tear", "color", "defect"])
            old_correct += int(has_defect == is_defect_image)

        old_accuracy = old_correct / total_predictions * 100
        report["comparison"] = {
            "baseline_model": str(old_model_path),
            "baseline_sample_accuracy_percent": round(old_accuracy, 2),
            "current_sample_accuracy_percent": round(sample_accuracy, 2),
            "sample_improvement_percent": round(sample_accuracy - old_accuracy, 2),
        }

    report_path = report_dir / f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    for key, value in report["metrics"].items():
        print(f"{key}: {value}")
    print(f"Sample accuracy: {report['sample_accuracy_percent']}%")
    print(f"Report saved: {report_path}")


if __name__ == "__main__":
    try:
        validate_model()
    except Exception as e:
        print(f"\n[!] ERROR: {e}")
        import traceback

        traceback.print_exc()
