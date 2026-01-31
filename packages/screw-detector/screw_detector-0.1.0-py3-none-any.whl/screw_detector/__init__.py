"""
Screw Detector - YOLOv8 + SAHI Detection Pipeline

A high-precision object detection system for tiny objects (screws, bolts, washers)
using YOLOv8 and Slicing Aided Hyper Inference (SAHI).
"""

__version__ = "0.1.0"
__author__ = "Screw Detector Team"

# Import main classes and functions for easy access
from .config import Config, load_config
from .dataset import DatasetStats, slice_yolo_dataset
from .inference import SAHIInference, BaselineInference
from .models import YOLOModel, ModelTrainer
from .sahi_utils import SAHIPredictor, get_sliced_prediction
from .utils import visualize_predictions, calculate_metrics

__all__ = [
    # Version info
    "__version__",
    "__author__",
    # Config
    "Config",
    "load_config",
    # Dataset
    "DatasetStats",
    "slice_yolo_dataset",
    # Inference
    "SAHIInference",
    "BaselineInference",
    # Models
    "YOLOModel",
    "ModelTrainer",
    # SAHI Utils
    "SAHIPredictor",
    "get_sliced_prediction",
    # Utils
    "visualize_predictions",
    "calculate_metrics",
]
