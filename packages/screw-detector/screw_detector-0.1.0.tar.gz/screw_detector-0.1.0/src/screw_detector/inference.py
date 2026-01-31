"""
Inference utilities for Screw Detector.

This module provides classes and functions for running inference
using both baseline YOLOv8 and SAHI-enhanced detection.
"""

from pathlib import Path
from typing import List, Dict, Optional, Union, Tuple
import cv2
import numpy as np

from sahi import AutoDetectionModel
from sahi.predict import get_sliced_prediction, get_prediction
from ultralytics import YOLO

from .config import SAHIConfig, Config


class BaselineInference:
    """
    Baseline inference using standard YOLOv8.
    
    This class provides a simple interface for running inference
    with YOLOv8 models without SAHI slicing.
    """
    
    def __init__(
        self,
        model_path: Union[str, Path],
        confidence_threshold: float = 0.5,
        device: str = "cpu"
    ):
        """
        Initialize BaselineInference.
        
        Args:
            model_path: Path to the YOLOv8 model file (.pt).
            confidence_threshold: Confidence threshold for detections.
            device: Device to run inference on (cpu, cuda, mps).
        """
        self.model_path = Path(model_path)
        self.confidence_threshold = confidence_threshold
        self.device = device
        self.model = YOLO(str(self.model_path))
    
    def predict(
        self,
        image_path: Union[str, Path],
        imgsz: int = 640,
        **kwargs
    ) -> List[Dict]:
        """
        Run inference on a single image.
        
        Args:
            image_path: Path to the input image.
            imgsz: Image size for inference.
            **kwargs: Additional arguments passed to YOLO predict.
            
        Returns:
            List of detection dictionaries.
        """
        results = self.model.predict(
            str(image_path),
            conf=self.confidence_threshold,
            imgsz=imgsz,
            device=self.device,
            **kwargs
        )
        
        detections = []
        for result in results:
            for box in result.boxes:
                detections.append({
                    'class_id': int(box.cls),
                    'class_name': result.names[int(box.cls)],
                    'confidence': float(box.conf),
                    'bbox': box.xyxy[0].tolist(),
                })
        
        return detections
    
    def predict_batch(
        self,
        image_paths: List[Union[str, Path]],
        imgsz: int = 640,
        **kwargs
    ) -> Dict[str, List[Dict]]:
        """
        Run inference on multiple images.
        
        Args:
            image_paths: List of paths to input images.
            imgsz: Image size for inference.
            **kwargs: Additional arguments passed to YOLO predict.
            
        Returns:
            Dictionary mapping image paths to detection lists.
        """
        results_dict = {}
        for img_path in image_paths:
            results_dict[str(img_path)] = self.predict(img_path, imgsz, **kwargs)
        return results_dict


class SAHIInference:
    """
    SAHI-enhanced inference using Slicing Aided Hyper Inference.
    
    This class provides an interface for running inference with SAHI,
    which slices images into smaller patches for better small object detection.
    """
    
    def __init__(
        self,
        model_path: Union[str, Path],
        config: Optional[SAHIConfig] = None,
        device: str = "cpu"
    ):
        """
        Initialize SAHIInference.
        
        Args:
            model_path: Path to the YOLOv8 model file (.pt).
            config: SAHIConfig instance. If None, uses default config.
            device: Device to run inference on (cpu, cuda, mps).
        """
        self.model_path = Path(model_path)
        self.config = config or SAHIConfig()
        self.device = device
        
        self.detection_model = AutoDetectionModel.from_pretrained(
            model_type="ultralytics",
            model_path=str(self.model_path),
            confidence_threshold=self.config.confidence_threshold,
            device=self.device
        )
    
    def predict(
        self,
        image_path: Union[str, Path],
        slice_height: Optional[int] = None,
        slice_width: Optional[int] = None,
        overlap_height_ratio: Optional[float] = None,
        overlap_width_ratio: Optional[float] = None,
        **kwargs
    ) -> List[Dict]:
        """
        Run SAHI inference on a single image.
        
        Args:
            image_path: Path to the input image.
            slice_height: Height of each slice. Uses config default if None.
            slice_width: Width of each slice. Uses config default if None.
            overlap_height_ratio: Overlap ratio for height. Uses config default if None.
            overlap_width_ratio: Overlap ratio for width. Uses config default if None.
            **kwargs: Additional arguments passed to get_sliced_prediction.
            
        Returns:
            List of detection dictionaries.
        """
        result = get_sliced_prediction(
            str(image_path),
            self.detection_model,
            slice_height=slice_height or self.config.slice_height,
            slice_width=slice_width or self.config.slice_width,
            overlap_height_ratio=overlap_height_ratio or self.config.overlap_height_ratio,
            overlap_width_ratio=overlap_width_ratio or self.config.overlap_width_ratio,
            postprocess_type=self.config.postprocess_type,
            postprocess_match_threshold=self.config.postprocess_match_threshold,
            **kwargs
        )
        
        detections = []
        for obj_pred in result.object_prediction_list:
            detections.append({
                'class_id': obj_pred.category.id,
                'class_name': obj_pred.category.name,
                'confidence': obj_pred.score.value,
                'bbox': [
                    obj_pred.bbox.minx,
                    obj_pred.bbox.miny,
                    obj_pred.bbox.maxx,
                    obj_pred.bbox.maxy
                ],
            })
        
        return detections
    
    def predict_batch(
        self,
        image_paths: List[Union[str, Path]],
        **kwargs
    ) -> Dict[str, List[Dict]]:
        """
        Run SAHI inference on multiple images.
        
        Args:
            image_paths: List of paths to input images.
            **kwargs: Additional arguments passed to predict.
            
        Returns:
            Dictionary mapping image paths to detection lists.
        """
        results_dict = {}
        for img_path in image_paths:
            results_dict[str(img_path)] = self.predict(img_path, **kwargs)
        return results_dict


def compare_inference(
    image_path: Union[str, Path],
    model_path: Union[str, Path],
    sahi_config: Optional[SAHIConfig] = None,
    device: str = "cpu"
) -> Dict[str, List[Dict]]:
    """
    Compare baseline and SAHI inference on the same image.
    
    Args:
        image_path: Path to the input image.
        model_path: Path to the YOLOv8 model file.
        sahi_config: SAHIConfig instance. If None, uses default config.
        device: Device to run inference on.
        
    Returns:
        Dictionary with 'baseline' and 'sahi' detection lists.
    """
    baseline = BaselineInference(model_path, device=device)
    sahi = SAHIInference(model_path, config=sahi_config, device=device)
    
    return {
        'baseline': baseline.predict(image_path),
        'sahi': sahi.predict(image_path)
    }


def visualize_predictions(
    image_path: Union[str, Path],
    detections: List[Dict],
    output_path: Optional[Union[str, Path]] = None,
    show_confidence: bool = True,
    line_thickness: int = 2
) -> np.ndarray:
    """
    Visualize detections on an image.
    
    Args:
        image_path: Path to the input image.
        detections: List of detection dictionaries.
        output_path: Optional path to save the visualization.
        show_confidence: Whether to show confidence scores.
        line_thickness: Thickness of bounding box lines.
        
    Returns:
        Annotated image as numpy array.
    """
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
    
    # Color map for different classes
    colors = [
        (255, 0, 0),    # Red
        (0, 255, 0),    # Green
        (0, 0, 255),    # Blue
        (255, 255, 0),  # Cyan
        (255, 0, 255),  # Magenta
        (0, 255, 255),  # Yellow
    ]
    
    for det in detections:
        x1, y1, x2, y2 = map(int, det['bbox'])
        class_id = det['class_id']
        class_name = det['class_name']
        confidence = det['confidence']
        
        color = colors[class_id % len(colors)]
        
        # Draw bounding box
        cv2.rectangle(img, (x1, y1), (x2, y2), color, line_thickness)
        
        # Draw label
        label = class_name
        if show_confidence:
            label += f" {confidence:.2f}"
        
        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(
            img,
            (x1, y1 - label_size[1] - 10),
            (x1 + label_size[0], y1),
            color,
            -1
        )
        cv2.putText(
            img,
            label,
            (x1, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1
        )
    
    if output_path:
        cv2.imwrite(str(output_path), img)
    
    return img


def calculate_iou(box1: List[float], box2: List[float]) -> float:
    """
    Calculate Intersection over Union (IoU) between two bounding boxes.
    
    Args:
        box1: First bounding box [x1, y1, x2, y2].
        box2: Second bounding box [x1, y1, x2, y2].
        
    Returns:
        IoU value between 0 and 1.
    """
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    
    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    
    union = area1 + area2 - intersection
    
    return intersection / union if union > 0 else 0.0


def match_detections(
    predictions: List[Dict],
    ground_truth: List[Dict],
    iou_threshold: float = 0.5
) -> Tuple[int, int, int]:
    """
    Match predictions with ground truth annotations.
    
    Args:
        predictions: List of predicted detections.
        ground_truth: List of ground truth annotations.
        iou_threshold: IoU threshold for matching.
        
    Returns:
        Tuple of (true_positives, false_positives, false_negatives).
    """
    tp = 0
    fp = 0
    fn = len(ground_truth)
    
    matched_gt = set()
    
    for pred in predictions:
        best_iou = 0.0
        best_gt_idx = -1
        
        for gt_idx, gt in enumerate(ground_truth):
            if gt_idx in matched_gt:
                continue
            
            iou = calculate_iou(pred['bbox'], gt['bbox'])
            if iou > best_iou:
                best_iou = iou
                best_gt_idx = gt_idx
        
        if best_iou >= iou_threshold:
            tp += 1
            matched_gt.add(best_gt_idx)
            fn -= 1
        else:
            fp += 1
    
    return tp, fp, fn
