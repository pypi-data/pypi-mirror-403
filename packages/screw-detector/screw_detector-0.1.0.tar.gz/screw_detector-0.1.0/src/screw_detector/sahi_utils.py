"""
SAHI (Slicing Aided Hyper Inference) utilities for Screw Detector.

This module provides utilities for SAHI configuration and prediction.
"""

from pathlib import Path
from typing import List, Dict, Optional, Union, Tuple
import time

from sahi import AutoDetectionModel
from sahi.predict import get_sliced_prediction, get_prediction
from sahi.utils.cv import read_image

from .config import SAHIConfig


class SAHIPredictor:
    """
    SAHI predictor for object detection.
    
    This class provides a convenient interface for running
    SAHI-enhanced inference on images.
    """
    
    def __init__(
        self,
        model_path: Union[str, Path],
        config: Optional[SAHIConfig] = None,
        device: str = "cpu"
    ):
        """
        Initialize SAHIPredictor.
        
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
        image: Union[str, Path],
        slice_height: Optional[int] = None,
        slice_width: Optional[int] = None,
        overlap_height_ratio: Optional[float] = None,
        overlap_width_ratio: Optional[float] = None,
        return_image: bool = False,
        **kwargs
    ) -> Union[List[Dict], Tuple[List[Dict], object]]:
        """
        Run SAHI prediction on an image.
        
        Args:
            image: Path to the input image or numpy array.
            slice_height: Height of each slice. Uses config default if None.
            slice_width: Width of each slice. Uses config default if None.
            overlap_height_ratio: Overlap ratio for height. Uses config default if None.
            overlap_width_ratio: Overlap ratio for width. Uses config default if None.
            return_image: Whether to return the annotated image.
            **kwargs: Additional arguments passed to get_sliced_prediction.
            
        Returns:
            List of detection dictionaries, or tuple of (detections, image) if return_image=True.
        """
        result = get_sliced_prediction(
            str(image) if isinstance(image, (str, Path)) else image,
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
                'area': obj_pred.bbox.area,
            })
        
        if return_image:
            return detections, result
        return detections
    
    def predict_batch(
        self,
        images: List[Union[str, Path]],
        **kwargs
    ) -> Dict[str, List[Dict]]:
        """
        Run SAHI prediction on multiple images.
        
        Args:
            images: List of paths to input images.
            **kwargs: Additional arguments passed to predict.
            
        Returns:
            Dictionary mapping image paths to detection lists.
        """
        results_dict = {}
        for img in images:
            results_dict[str(img)] = self.predict(img, **kwargs)
        return results_dict
    
    def benchmark(
        self,
        image_path: Union[str, Path],
        num_runs: int = 10,
        **kwargs
    ) -> Dict[str, float]:
        """
        Benchmark SAHI inference speed.
        
        Args:
            image_path: Path to the test image.
            num_runs: Number of inference runs for benchmarking.
            **kwargs: Additional arguments passed to predict.
            
        Returns:
            Dictionary with timing statistics.
        """
        times = []
        
        # Warm-up run
        self.predict(image_path, **kwargs)
        
        for _ in range(num_runs):
            start_time = time.time()
            self.predict(image_path, **kwargs)
            times.append(time.time() - start_time)
        
        return {
            'mean_time': sum(times) / len(times),
            'min_time': min(times),
            'max_time': max(times),
            'std_time': (sum((t - sum(times)/len(times))**2 for t in times) / len(times))**0.5,
            'fps': 1.0 / (sum(times) / len(times)),
        }


def get_sliced_prediction(
    image: Union[str, Path],
    model_path: Union[str, Path],
    slice_height: int = 640,
    slice_width: int = 640,
    overlap_height_ratio: float = 0.2,
    overlap_width_ratio: float = 0.2,
    confidence_threshold: float = 0.6,
    postprocess_type: str = "NMS",
    postprocess_match_threshold: float = 0.6,
    device: str = "cpu",
    **kwargs
) -> List[Dict]:
    """
    Run SAHI sliced prediction on an image.
    
    This is a convenience function that creates a detection model
    and runs sliced prediction in one call.
    
    Args:
        image: Path to the input image.
        model_path: Path to the YOLOv8 model file.
        slice_height: Height of each slice.
        slice_width: Width of each slice.
        overlap_height_ratio: Overlap ratio for height.
        overlap_width_ratio: Overlap ratio for width.
        confidence_threshold: Confidence threshold for detections.
        postprocess_type: Post-processing type (NMS, GREEDYNMS, NMM).
        postprocess_match_threshold: Threshold for post-processing.
        device: Device to run inference on.
        **kwargs: Additional arguments passed to get_sliced_prediction.
        
    Returns:
        List of detection dictionaries.
    """
    detection_model = AutoDetectionModel.from_pretrained(
        model_type="ultralytics",
        model_path=str(model_path),
        confidence_threshold=confidence_threshold,
        device=device
    )
    
    result = get_sliced_prediction(
        str(image),
        detection_model,
        slice_height=slice_height,
        slice_width=slice_width,
        overlap_height_ratio=overlap_height_ratio,
        overlap_width_ratio=overlap_width_ratio,
        postprocess_type=postprocess_type,
        postprocess_match_threshold=postprocess_match_threshold,
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


def optimize_sahi_parameters(
    model_path: Union[str, Path],
    validation_images: List[Union[str, Path]],
    ground_truth: List[List[Dict]],
    confidence_range: Tuple[float, float] = (0.3, 0.8),
    nms_range: Tuple[float, float] = (0.4, 0.8),
    step: float = 0.1,
    device: str = "cpu"
) -> Dict[str, float]:
    """
    Optimize SAHI parameters using grid search.
    
    Args:
        model_path: Path to the YOLOv8 model file.
        validation_images: List of validation image paths.
        ground_truth: List of ground truth annotations for each image.
        confidence_range: Range of confidence thresholds to test.
        nms_range: Range of NMS thresholds to test.
        step: Step size for grid search.
        device: Device to run inference on.
        
    Returns:
        Dictionary with optimal parameters and their score.
    """
    from .inference import match_detections
    
    best_score = 0.0
    best_params = {}
    
    conf_values = [round(confidence_range[0] + i * step, 2) 
                   for i in range(int((confidence_range[1] - confidence_range[0]) / step) + 1)]
    nms_values = [round(nms_range[0] + i * step, 2) 
                  for i in range(int((nms_range[1] - nms_range[0]) / step) + 1)]
    
    print("\n" + "="*60)
    print("SAHI PARAMETER OPTIMIZATION")
    print("="*60)
    print(f"Confidence range: {confidence_range}")
    print(f"NMS range: {nms_range}")
    print(f"Step: {step}")
    print(f"Total combinations: {len(conf_values) * len(nms_values)}")
    print("="*60)
    
    for conf in conf_values:
        for nms in nms_values:
            total_tp = 0
            total_fp = 0
            total_fn = 0
            
            for img_path, gt in zip(validation_images, ground_truth):
                detections = get_sliced_prediction(
                    img_path,
                    model_path,
                    confidence_threshold=conf,
                    postprocess_match_threshold=nms,
                    device=device
                )
                
                tp, fp, fn = match_detections(detections, gt)
                total_tp += tp
                total_fp += fp
                total_fn += fn
            
            # Calculate F1 score
            precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
            recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            if f1 > best_score:
                best_score = f1
                best_params = {
                    'confidence_threshold': conf,
                    'nms_threshold': nms,
                    'precision': precision,
                    'recall': recall,
                    'f1_score': f1
                }
            
            print(f"Conf: {conf:.2f}, NMS: {nms:.2f} -> F1: {f1:.4f}")
    
    print("\n" + "="*60)
    print("OPTIMAL PARAMETERS FOUND")
    print("="*60)
    print(f"Confidence threshold: {best_params['confidence_threshold']}")
    print(f"NMS threshold: {best_params['nms_threshold']}")
    print(f"Precision: {best_params['precision']:.4f}")
    print(f"Recall: {best_params['recall']:.4f}")
    print(f"F1 Score: {best_params['f1_score']:.4f}")
    print("="*60)
    
    return best_params


def calculate_slice_count(
    image_width: int,
    image_height: int,
    slice_size: int = 640,
    overlap: int = 128
) -> Tuple[int, int]:
    """
    Calculate the number of slices needed for an image.
    
    Args:
        image_width: Width of the input image.
        image_height: Height of the input image.
        slice_size: Size of each slice (square).
        overlap: Overlap between adjacent slices in pixels.
        
    Returns:
        Tuple of (num_slices_x, num_slices_y).
    """
    stride = slice_size - overlap
    num_slices_x = max(1, (image_width + stride - 1) // stride)
    num_slices_y = max(1, (image_height + stride - 1) // stride)
    
    return num_slices_x, num_slices_y
