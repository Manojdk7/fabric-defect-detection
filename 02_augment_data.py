"""
Step 2: Data Augmentation
Multiply images using augmentation techniques
Converts ~600 images to 2000+ images
"""

import albumentations as A
import cv2
import os
from pathlib import Path
import json

from config import Config

def augment_dataset():
    """Augment dataset to increase training samples"""
    
    print("=" * 60)
    print("STEP 2: DATA AUGMENTATION")
    print("Multiplying training images using augmentation...")
    print("=" * 60)
    
    # Define augmentation pipeline
    transform = A.Compose([
        # Geometric transforms
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.5),
        A.Rotate(limit=(-45, 45), p=0.7),
        A.ShiftScaleRotate(shift_limit=0.0625, scale_limit=0.2, rotate_limit=45, p=0.3),
        
        # Optical distortions
        A.OpticalDistortion(distort_limit=0.2, p=0.2),
        A.GridDistortion(p=0.2),
        A.ElasticTransform(p=0.2),
        
        # Color/brightness transforms
        A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.5),
        A.GaussNoise(p=0.2),
        A.Blur(blur_limit=3, p=0.3),
        A.Sharpen(alpha=(0.2, 0.5), lightness=(0.5, 1.0), p=0.3),
        
        # Perspective
        A.Perspective(scale=(0.05, 0.1), p=0.2),
    ], p=0.9)
    
    # Paths
    input_path = Config.MVTEC_DATA_DIR / "images" / "train"
    output_path = Config.MVTEC_DATA_DIR / "images" / "train_augmented"
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\nInput: {input_path}")
    print(f"Output: {output_path}")
    
    # Count original images
    original_images = list(input_path.glob("*.png"))
    print(f"\nOriginal images: {len(original_images)}")
    
    # Augmentation parameters
    augmentations_per_image = 10  # Create 10 variations per image
    
    total_augmented = 0
    
    for img_file in original_images:
        # Read image
        image = cv2.imread(str(img_file))
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Save original
        output_file = output_path / f"00_original_{img_file.name}"
        cv2.imwrite(str(output_file), image)
        total_augmented += 1
        
        # Generate augmentations
        for i in range(augmentations_per_image):
            augmented = transform(image=image_rgb)
            augmented_image = cv2.cvtColor(augmented['image'], cv2.COLOR_RGB2BGR)
            
            # Save augmented image
            name, ext = os.path.splitext(img_file.name)
            output_file = output_path / f"{i:02d}_aug_{name}_{i}{ext}"
            cv2.imwrite(str(output_file), augmented_image)
            total_augmented += 1
        
        # Progress
        if total_augmented % 50 == 0:
            print(f"  Processed: {total_augmented} images ({img_file.name})")
    
    print("\n" + "=" * 60)
    print("AUGMENTATION SUMMARY")
    print("=" * 60)
    print(f"✓ Original images: {len(original_images)}")
    print(f"✓ Augmentations per image: {augmentations_per_image}")
    print(f"✓ Total augmented images: {total_augmented}")
    print(f"✓ Multiplication factor: {total_augmented / len(original_images):.1f}x")
    print(f"✓ Augmented data location: {output_path}")
    
    # Rename original folder and move augmented
    import shutil
    original_backup = Config.MVTEC_DATA_DIR / "images" / "train_original"
    if original_backup.exists():
        shutil.rmtree(original_backup)
    os.rename(str(input_path), str(original_backup))
    os.rename(str(output_path), str(input_path))
    
    print(f"\n✓ Replaced training images with augmented dataset")
    
    print("\n" + "=" * 60)
    print("NEXT STEP: Run 03_prepare_yolo_labels.py")
    print("=" * 60)

if __name__ == "__main__":
    try:
        augment_dataset()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        print("\nMake sure you have installed required packages:")
        print("pip install albumentations opencv-python pillow")
