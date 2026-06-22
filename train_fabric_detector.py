#!/usr/bin/env python3
"""
Fabric Defect Detection Training Script
Trains YOLOv8 on merged fabric datasets (hole, tear, stain).
"""

from pathlib import Path

import torch
from ultralytics import YOLO

from config import BASE_DIR

DEFAULT_DATA = "datasets/combined_fabric/data.yaml"
FALLBACK_DATA = "datasets/roboflow_saad/data.yaml"


def resolve_data_yaml() -> str:
    combined = BASE_DIR / DEFAULT_DATA
    if combined.exists():
        return DEFAULT_DATA
    return FALLBACK_DATA


def resolve_pretrained_weights() -> str:
    """Fine-tune from last trained fabric model if available."""
    candidates = [
        BASE_DIR / "models" / "fabric_defect_detector" / "weights" / "best.pt",
        BASE_DIR / "runs" / "detect" / "models" / "fabric_defect_detector-2" / "weights" / "best.pt",
        BASE_DIR / "runs" / "detect" / "models" / "fabric_defect_detector" / "weights" / "best.pt",
    ]
    for path in candidates:
        if path.exists():
            print(f"Fine-tuning from: {path}")
            return str(path)
    print("No existing fabric weights found — starting from yolov8n.pt")
    return "yolov8n.pt"


def copy_best_to_app_weights(run_dir: Path) -> Path | None:
    """Copy training output to path the Flask app loads."""
    src = run_dir / "weights" / "best.pt"
    if not src.exists():
        return None
    dest_dir = BASE_DIR / "models" / "fabric_defect_detector" / "weights"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "best.pt"
    import shutil

    shutil.copy2(src, dest)
    print(f"App model updated: {dest}")
    return dest


def train_fabric_detector(data_yaml: str | None = None, epochs: int = 80):
    """Train YOLOv8 on combined (or fallback) fabric dataset."""
    data_yaml = data_yaml or resolve_data_yaml()
    device = 0 if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    print(f"Dataset: {data_yaml}")

    weights = resolve_pretrained_weights()
    model = YOLO(weights)

    training_config = {
        "data": data_yaml,
        "epochs": epochs,
        "imgsz": 640,
        "batch": 8,
        "name": "fabric_defect_detector",
        "project": "models",
        "exist_ok": True,
        "save": True,
        "save_period": 10,
        "cache": True,
        "workers": 2,
        "patience": 25,
        "optimizer": "Adam",
        "lr0": 0.0005 if weights.endswith("best.pt") else 0.001,
        "lrf": 0.01,
        "momentum": 0.937,
        "weight_decay": 0.0005,
        "warmup_epochs": 3.0,
        "warmup_momentum": 0.8,
        "warmup_bias_lr": 0.1,
        "box": 7.5,
        "cls": 0.5,
        "dfl": 1.5,
        "cos_lr": True,
        "close_mosaic": 10,
        "device": device,
    }

    print("Starting fabric defect detector training...")
    print(f"Training config: {training_config}")

    results = model.train(**training_config)

    print("Training completed!")
    print(f"Best model saved at: {results.save_dir}/weights/best.pt")
    copy_best_to_app_weights(Path(results.save_dir))

    return results


def _default_best_weights():
    candidates = [
        Path("models/fabric_defect_detector/weights/best.pt"),
        Path("runs/detect/models/fabric_defect_detector/weights/best.pt"),
        Path("runs/detect/models/fabric_defect_detector-2/weights/best.pt"),
    ]
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


def validate_model(model_path=None, data_yaml: str | None = None):
    """Validate trained model."""
    model_path = Path(model_path) if model_path else _default_best_weights()
    data_yaml = data_yaml or resolve_data_yaml()

    if not model_path.exists():
        print(f"[!] Weights not found: {model_path}")
        return None

    print(f"Loading model: {model_path}")
    model = YOLO(str(model_path))
    results = model.val(data=data_yaml)

    print("Validation Results:")
    print(f"mAP50: {results.box.map50:.4f}")
    print(f"mAP50-95: {results.box.map:.4f}")

    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "merge-only":
        from merge_fabric_datasets import main as merge_main

        merge_main()
    else:
        data = resolve_data_yaml()
        if "combined_fabric" not in data:
            print("Combined dataset not found. Running merge first...")
            from merge_fabric_datasets import merge_datasets, default_sources

            merge_datasets(BASE_DIR / "datasets" / "combined_fabric", default_sources())

        train_fabric_detector()
        validate_model()
