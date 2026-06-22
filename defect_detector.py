import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
from ultralytics import YOLO
import json
from typing import Dict, List, Optional, Tuple

class DefectDetector:
    """
    Computer Vision-based defect detector for quality inspection.
    Supports detection of fabric defects.
    """

    def __init__(self, model_path: str = None, defect_type: str = 'fabric'):
        """
        Initialize the defect detector.

        Args:
            model_path: Path to YOLOv8 model file. If None, downloads pretrained model.
            defect_type: Type of defects to detect ('fabric')
        """
        self.defect_type = defect_type
        self.non_defect_classes = {'good', 'unused'}
        self.primary_model_path = None
        self.fallback_model_path = None

        if model_path:
            self.model = YOLO(model_path)
            self.primary_model_path = model_path
        else:
            self.defect_type = 'fabric'
            self.model = self._load_fabric_model()

        self.defect_classes = {
            'hole': {'color': (0, 0, 255), 'severity': 'high'},
            'stain': {'color': (0, 165, 255), 'severity': 'medium'},
            'tear': {'color': (255, 0, 0), 'severity': 'high'},
            'knot': {'color': (255, 0, 0), 'severity': 'high'},  # Roboflow label alias → tear
            'defect': {'color': (0, 0, 255), 'severity': 'high'},
            'fabric_anomaly': {'color': (0, 0, 255), 'severity': 'high'},
        }

    def _load_fabric_model(self):
        """Load the best available fabric model and keep a binary fallback if present."""
        primary_candidates = [
            'models/fabric_defect_detector/weights/best.pt',
            'runs/detect/models/fabric_defect_detector/weights/best.pt',
        ]
        fallback_candidates = [
            'models/retrained_model_test/weights/best.pt',
        ]

        for model_file in primary_candidates:
            if Path(model_file).exists():
                self.primary_model_path = model_file
                print(f"Loaded fabric detector model: {model_file}")
                break

        for model_file in fallback_candidates:
            if Path(model_file).exists():
                self.fallback_model_path = model_file
                if model_file != self.primary_model_path:
                    print(f"Loaded fallback fabric defect model: {model_file}")
                break

        if self.primary_model_path:
            return YOLO(self.primary_model_path)

        if self.fallback_model_path:
            self.primary_model_path = self.fallback_model_path
            print(f"Using fallback fabric model as primary: {self.primary_model_path}")
            return YOLO(self.primary_model_path)

        self.primary_model_path = 'yolov8n.pt'
        print("Using default YOLOv8 model (fabric model not found)")
        return YOLO('yolov8n.pt')

    def _extract_detections(self, results, width: int, height: int) -> Tuple[List[Dict], np.ndarray]:
        """Convert YOLO results into application detection objects."""
        detections = []
        annotated_image = None

        for result in results:
            boxes = result.boxes
            annotated_image = result.orig_img.copy()

            for box in boxes:
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                class_name = result.names[class_id]

                if class_name in self.non_defect_classes:
                    continue

                x1, y1, x2, y2 = map(int, box.xyxy[0])

                detection_info = {
                    'type': class_name,
                    'confidence': round(confidence, 3),
                    'bbox': [x1, y1, x2, y2],
                    'area_pixels': (x2 - x1) * (y2 - y1),
                    'area_percentage': round(((x2 - x1) * (y2 - y1) / (width * height)) * 100, 2)
                }

                if class_name in self.defect_classes:
                    detection_info['severity'] = self.defect_classes[class_name]['severity']
                    color = self.defect_classes[class_name]['color']
                else:
                    detection_info['severity'] = 'unknown'
                    color = (128, 128, 128)

                detections.append(detection_info)

                cv2.rectangle(annotated_image, (x1, y1), (x2, y2), color, 2)

                label = f"{class_name} {confidence:.2f}"
                cv2.putText(
                    annotated_image,
                    label,
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    2,
                )

        return detections, annotated_image
    
    def detect_defects(self, image_path: str, confidence_threshold: float = 0.5) -> Dict:
        """
        Detect defects in an image.
        
        Args:
            image_path: Path to input image
            confidence_threshold: Minimum confidence score (0-1)
        
        Returns:
            Dictionary with detection results, annotated image, and metrics
        """
        image = cv2.imread(image_path)
        if image is None:
            return {'error': f'Could not read image: {image_path}'}
        
        original_image = image.copy()
        height, width = image.shape[:2]
        
        results = self.model(image_path, conf=confidence_threshold, verbose=False)
        detections, annotated_image = self._extract_detections(results, width, height)

        if not detections and self.fallback_model_path and self.fallback_model_path != self.primary_model_path:
            fallback_model = YOLO(self.fallback_model_path)
            fallback_results = fallback_model(
                image_path,
                conf=max(0.1, min(confidence_threshold, 0.25)),
                verbose=False,
            )
            fallback_detections, fallback_annotated = self._extract_detections(
                fallback_results,
                width,
                height,
            )
            if fallback_detections:
                detections = fallback_detections
                annotated_image = fallback_annotated
        
        metrics = self._calculate_metrics(detections, width, height)
        
        return {
            'image_path': image_path,
            'width': width,
            'height': height,
            'detections': detections,
            'total_defects': len(detections),
            'metrics': metrics,
            'annotated_image': annotated_image,
            'original_image': original_image,
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_metrics(self, detections: List[Dict], width: int, height: int) -> Dict:
        """Calculate inspection metrics from detections."""
        metrics = {
            'total_defects': len(detections),
            'critical_defects': sum(1 for d in detections if d.get('severity') == 'high'),
            'medium_defects': sum(1 for d in detections if d.get('severity') == 'medium'),
            'minor_defects': sum(1 for d in detections if d.get('severity') == 'low'),
            'defect_types': {},
            'total_defect_area_percentage': 0
        }
        
        for detection in detections:
            defect_type = detection['type']
            metrics['defect_types'][defect_type] = metrics['defect_types'].get(defect_type, 0) + 1
        
        total_area = sum(d['area_percentage'] for d in detections)
        metrics['total_defect_area_percentage'] = round(total_area, 2)
        
        metrics['pass_fail'] = 'PASS' if len(detections) == 0 else 'FAIL'
        
        return metrics
    
    def save_annotated_image(self, result: Dict, output_path: str) -> str:
        """Save annotated image to file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        cv2.imwrite(str(output_path), result['annotated_image'])
        return str(output_path)
    
    def generate_inspection_report(self, result: Dict) -> Dict:
        """
        Generate a detailed inspection report.
        
        Returns:
            Dictionary with formatted report data
        """
        report = {
            'inspection_id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'timestamp': result['timestamp'],
            'image_info': {
                'filename': Path(result['image_path']).name,
                'dimensions': f"{result['width']}x{result['height']}",
                'resolution': result['width'] * result['height']
            },
            'summary': {
                'total_defects': result['total_defects'],
                'status': result['metrics']['pass_fail'],
                'quality_score': round(100 * (1 - min(result['metrics']['total_defect_area_percentage'] / 10, 1)), 1)
            },
            'defect_breakdown': result['metrics']['defect_types'],
            'severity_breakdown': {
                'critical': result['metrics']['critical_defects'],
                'medium': result['metrics']['medium_defects'],
                'minor': result['metrics']['minor_defects']
            },
            'detections': result['detections'],
            'recommendations': self._generate_recommendations(result)
        }
        
        return report
    
    def _generate_recommendations(self, result: Dict) -> List[str]:
        """Generate recommendations based on inspection results."""
        recommendations = []
        
        if result['total_defects'] == 0:
            recommendations.append("✓ Product passed quality inspection")
            return recommendations
        
        metrics = result['metrics']
        
        if metrics['critical_defects'] > 0:
            recommendations.append(f"⚠️ {metrics['critical_defects']} critical defect(s) found - REJECT product")
        
        if metrics['medium_defects'] > 0:
            recommendations.append(f"⚠️ {metrics['medium_defects']} medium severity defect(s) - Review for rework")
        
        if metrics['total_defect_area_percentage'] > 5:
            recommendations.append("⚠️ Defect coverage exceeds 5% - Consider product rework or rejection")
        
        defect_types = metrics['defect_types']
        if 'hole' in defect_types:
            recommendations.append("→ Cracks detected: Check production equipment calibration")
        if 'tear' in defect_types:
            recommendations.append("→ Misalignment detected: Verify assembly process")
        
        return recommendations
