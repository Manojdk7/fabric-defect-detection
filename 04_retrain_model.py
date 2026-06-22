"""
Step 4: Retrain YOLOv8 Model
Trains improved model with new MVTec dataset
Expected: 85-90% accuracy
"""

from ultralytics import YOLO
from pathlib import Path
import torch

from config import Config

def retrain_model():
    """Retrain YOLOv8 model with enhanced dataset"""
    
    print("=" * 60)
    print("STEP 4: RETRAIN YOLOv8 MODEL")
    print("=" * 60)
    
    # Check GPU availability
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"\n✓ Device: {device}")
    if device == 'cuda':
        print(f"  GPU: {torch.cuda.get_device_name(0)}")
        print(f"  CUDA Version: {torch.version.cuda}")
    
    # Define paths
    data_dir = Config.MVTEC_DATA_DIR
    data_yaml = data_dir / "data.yaml"
    model_dir = Config.MODELS_DIR
    
    model_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n✓ Dataset: {data_yaml}")
    print(f"✓ Model save directory: {model_dir}")
    
    # Verify data.yaml exists
    if not data_yaml.exists():
        print(f"\n✗ ERROR: {data_yaml} not found!")
        print("Please run 01_setup_data.py first")
        return
    
    # Load model - using medium model for better accuracy
    print("\n--- Loading YOLOv8 Model ---")
    model = YOLO('yolov8m.pt')  # Medium model for better accuracy than nano
    print("✓ Loaded YOLOv8 Medium model")
    
    # Training configuration
    print("\n--- Training Configuration ---")
    print("Epochs: 50")
    print("Image Size: 640")
    print("Batch Size: 16")
    print("Patience: 20 (early stopping)")
    
    # Train model
    print("\n--- Starting Training ---")
    print("This will take 5-15 minutes depending on GPU...\n")
    
    results = model.train(
        data=str(data_yaml),
        epochs=50,
        imgsz=640,
        batch=16,
        patience=20,
        device=device,
        augment=True,
        flipud=0.5,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.1,
        perspective=0.0,
        optimizer='auto',
        lr0=0.01,
        lrf=0.01,
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3,
        warmup_momentum=0.8,
        warmup_bias_lr=0.1,
        box=7.5,
        cls=0.5,
        dfl=1.5,
        nbs=64,
        save=True,
        save_period=10,
        half=True if device == 'cuda' else False,
        project=str(model_dir),
        name='retrained_model_v2',
        exist_ok=False,
        verbose=True,
        seed=0,
        deterministic=True,
        single_cls=False,
        rect=False,
        cos_lr=False,
        close_mosaic=10,
        plots=True,
    )
    
    # Print results
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)
    
    if results:
        print(f"\n✓ Model trained successfully!")
        print(f"✓ Results location: {results}")
        
        # Get metrics
        metrics = model.metrics
        print(f"\n--- Final Metrics ---")
        if hasattr(metrics, 'box'):
            print(f"Box mAP50: {metrics.box.map50:.2%}")
            print(f"Box mAP: {metrics.box.map:.2%}")
        if hasattr(metrics, 'confusion_matrix'):
            print(f"Confusion Matrix saved")
    
    # Save best model
    best_model_path = model_dir / "retrained_model_v2" / "weights" / "best.pt"
    if best_model_path.exists():
        print(f"\n✓ Best model saved: {best_model_path}")
    
    print("\n" + "=" * 60)
    print("NEXT STEP: Run 05_validate_model.py")
    print("=" * 60)

if __name__ == "__main__":
    try:
        retrain_model()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
