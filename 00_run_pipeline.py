"""
MAIN WORKFLOW: Complete retraining pipeline
Runs all steps in sequence: Setup → Augment → Label → Train → Validate
"""

import subprocess
import sys
from pathlib import Path
import time

from config import BASE_DIR, Config

def run_pipeline():
    """Run complete retraining pipeline"""
    
    print("\n" + "=" * 80)
    print("QUALITY INSPECTION SYSTEM - MODEL RETRAINING PIPELINE")
    print("=" * 80)
    print("\nThis will:")
    print("  1. Setup MVTec data from Downloads")
    print("  2. Augment dataset (600 -> 2000+ images)")
    print("  3. Create YOLO labels")
    print("  4. Retrain YOLOv8 model (50 epochs)")
    print("  5. Validate and test new model")
    print("\nEstimated time: 20-30 minutes")
    print("=" * 80)
    
    response = input("\nStart pipeline? (yes/no): ").lower().strip()
    if response != 'yes':
        print("Pipeline cancelled.")
        return
    
    scripts = [
        "01_setup_data.py",
        "02_augment_data.py",
        "03_prepare_yolo_labels.py",
        "04_retrain_model.py",
        "05_validate_model.py"
    ]
    
    project_dir = BASE_DIR
    
    for i, script in enumerate(scripts, 1):
        script_path = project_dir / script
        
        if not script_path.exists():
            print(f"\n✗ ERROR: {script} not found!")
            continue
        
        print(f"\n{'=' * 80}")
        print(f"STEP {i}/5: {script.replace('_', ' ').replace('.py', '').upper()}")
        print("=" * 80)
        
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(project_dir),
                capture_output=False
            )
            
            if result.returncode != 0:
                print(f"\n✗ Script failed with error code: {result.returncode}")
                cont = input("Continue with next step? (yes/no): ").lower().strip()
                if cont != 'yes':
                    print("Pipeline stopped.")
                    return
            
            # Wait between steps
            if i < len(scripts):
                print(f"\nStep {i} complete. Proceeding to step {i+1}...\n")
                time.sleep(2)
        
        except Exception as e:
            print(f"\n✗ ERROR running script: {e}")
            cont = input("Continue? (yes/no): ").lower().strip()
            if cont != 'yes':
                return
    
    print("\n" + "=" * 80)
    print("PIPELINE COMPLETE!")
    print("=" * 80)
    print(f"\nResults:")
    print(f"  ✓ Models saved to: {Config.MODELS_DIR}")
    print(f"  ✓ Best model: models/retrained_model_v2/weights/best.pt")
    print(f"\nNext steps:")
    print(f"  1. Update defect_detector.py to use new model")
    print(f"  2. Restart Flask backend and React dashboard")
    print(f"  3. Test improved accuracy")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    run_pipeline()
