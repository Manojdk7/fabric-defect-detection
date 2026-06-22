"""
Step 3: Prepare YOLO Labels
Creates label files for YOLO training format
"""

import os
from pathlib import Path

from config import Config

def create_yolo_labels():
    """Create YOLO format label files"""
    
    print("=" * 60)
    print("STEP 3: PREPARE YOLO LABELS")
    print("=" * 60)
    
    # Paths
    train_path = Config.MVTEC_DATA_DIR / "images" / "train"
    train_labels = Config.MVTEC_DATA_DIR / "labels" / "train"
    val_path = Config.MVTEC_DATA_DIR / "images" / "val"
    val_labels = Config.MVTEC_DATA_DIR / "labels" / "val"
    
    train_labels.mkdir(parents=True, exist_ok=True)
    val_labels.mkdir(parents=True, exist_ok=True)
    
    def create_labels_for_folder(img_folder, label_folder):
        """Create label files for all images in folder"""
        
        images = list(img_folder.glob("*.png"))
        print(f"\nProcessing {len(images)} images in {img_folder.name}")
        
        for img_file in images:
            # Determine defect type from filename
            filename = img_file.name.lower()
            
            # Class mapping
            class_id = 0  # Default: no defect (good)
            
            # Check for defect keywords
            if any(keyword in filename for keyword in ['hole', 'cut', 'tear']):
                class_id = 1  # Defect found
            elif any(keyword in filename for keyword in ['good', 'original']):
                class_id = 0  # No defect
            else:
                # Default to defect for other types
                class_id = 1
            
            # Create label file
            label_file = label_folder / f"{img_file.stem}.txt"
            
            # YOLO format: <class_id> <x_center> <y_center> <width> <height>
            # For whole image classification: class 0 center with full width/height
            label_content = f"{class_id} 0.5 0.5 1.0 1.0\n"
            
            with open(label_file, 'w') as f:
                f.write(label_content)
        
        print(f"✓ Created {len(images)} label files")
        return len(images)
    
    # Process train and validation
    train_count = create_labels_for_folder(train_path, train_labels)
    val_count = create_labels_for_folder(val_path, val_labels)
    
    print("\n" + "=" * 60)
    print("YOLO LABELS SUMMARY")
    print("=" * 60)
    print(f"✓ Training images/labels: {train_count}")
    print(f"✓ Validation images/labels: {val_count}")
    print(f"✓ Total dataset: {train_count + val_count}")
    print(f"✓ Label format: YOLO (class_id x_center y_center width height)")
    
    # Create index files for verification
    with open(Config.MVTEC_DATA_DIR / "train.txt", 'w') as f:
        for img in train_path.glob("*.png"):
            f.write(f"{img}\n")
    
    with open(Config.MVTEC_DATA_DIR / "val.txt", 'w') as f:
        for img in val_path.glob("*.png"):
            f.write(f"{img}\n")
    
    print(f"\n✓ Created train.txt and val.txt index files")
    
    print("\n" + "=" * 60)
    print("NEXT STEP: Run 04_retrain_model.py")
    print("=" * 60)

if __name__ == "__main__":
    create_yolo_labels()
