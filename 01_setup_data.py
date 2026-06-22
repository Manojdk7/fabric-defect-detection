"""
Step 1: Setup and organize MVTec data for training - FIXED VERSION
Moves data from Downloads to proper location
Creates folder structure for YOLO training
"""

import os
import shutil
from pathlib import Path

from config import Config

def setup_mvtec_data():
    """Setup MVTec AD data for YOLO training"""
    
    print("=" * 60)
    print("STEP 1: SETUP MVTec DATA FOR YOLO TRAINING")
    print("=" * 60)
    
    # Define paths
    downloads_path = Config.SOURCE_DATA_DIR
    data_base_path = Config.MVTEC_DATA_DIR
    
    # Create base directory
    data_base_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\n[+] Creating directories at: {data_base_path}")
    
    # Create YOLO structure
    train_path = data_base_path / "images" / "train"
    val_path = data_base_path / "images" / "val"
    train_path.mkdir(parents=True, exist_ok=True)
    val_path.mkdir(parents=True, exist_ok=True)
    
    # Copy and organize dataset
    categories = ['carpet', 'leather']
    total_train = 0
    total_val = 0
    
    for category in categories:
        print(f"\n--- Processing {category.upper()} ---")
        
        source = downloads_path / category
        
        if not source.exists():
            print(f"[!] ERROR: {source} not found!")
            continue
        
        # Find all PNG files recursively in ALL subdirectories
        all_images = list(source.rglob("*.png"))
        print(f"Found {len(all_images)} images in {category}")
        
        if len(all_images) == 0:
            print(f"[!] WARNING: No PNG images found")
            continue
        
        # Split into train (80%) and validation (20%)
        split_index = int(len(all_images) * 0.8)
        train_images = all_images[:split_index]
        val_images = all_images[split_index:]
        
        print(f"  Train: {len(train_images)}, Val: {len(val_images)}")
        
        # Copy training images
        for i, img_file in enumerate(train_images):
            dest = train_path / f"{category}_{i:04d}_{img_file.name}"
            shutil.copy2(img_file, dest)
            total_train += 1
        
        # Copy validation images
        for i, img_file in enumerate(val_images):
            dest = val_path / f"{category}_{i:04d}_{img_file.name}"
            shutil.copy2(img_file, dest)
            total_val += 1
    
    # Verify
    train_images = list(train_path.glob("*.png"))
    val_images = list(val_path.glob("*.png"))
    
    print("\n" + "=" * 60)
    print("DATA ORGANIZATION SUMMARY")
    print("=" * 60)
    print(f"\n[+] Training images: {len(train_images)}")
    print(f"[+] Validation images: {len(val_images)}")
    print(f"[+] Total images: {len(train_images) + len(val_images)}")
    print(f"[+] Data location: {data_base_path} ")
    
    if len(train_images) == 0:
        print("\n✗ ERROR: No images were copied!")
        return False
    
    # Create data.yaml for YOLO
    data_yaml_path = data_base_path / "data.yaml"
    data_yaml_content = f"""path: {data_base_path}
train: images/train
val: images/val

nc: 2
names: ['good', 'defect']
"""
    
    with open(data_yaml_path, 'w') as f:
        f.write(data_yaml_content)
    
    print(f"\n✓ Created data.yaml at: {data_yaml_path}")
    
    print("\n" + "=" * 60)
    print("NEXT STEP: Run 02_augment_data.py")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    setup_mvtec_data()
