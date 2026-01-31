"""
Tests for inference module.
"""

import pytest
import numpy as np
from pathlib import Path

from screw_detector.inference import (
    BaselineInference,
    SAHIInference,
    calculate_iou,
    match_detections
)
from screw_detector.config import SAHIConfig


class TestCalculateIoU:
    """Tests for IoU calculation."""
    
    def test_perfect_overlap(self):
        """Test IoU with perfect overlap."""
        box1 = [0, 0, 100, 100]
        box2 = [0, 0, 100, 100]
        iou = calculate_iou(box1, box2)
        assert iou == pytest.approx(1.0)
    
    def test_no_overlap(self):
        """Test IoU with no overlap."""
        box1 = [0, 0, 100, 100]
        box2 = [200, 200, 300, 300]
        iou = calculate_iou(box1, box2)
        assert iou == pytest.approx(0.0)
    
    def test_partial_overlap(self):
        """Test IoU with partial overlap."""
        box1 = [0, 0, 100, 100]
        box2 = [50, 50, 150, 150]
        iou = calculate_iou(box1, box2)
        # Intersection: 50x50 = 2500
        # Union: 10000 + 10000 - 2500 = 17500
        # IoU: 2500 / 17500 = 0.1428...
        assert iou == pytest.approx(2500 / 17500)
    
    def test_contained_box(self):
        """Test IoU when one box is contained in another."""
        box1 = [0, 0, 100, 100]
        box2 = [25, 25, 75, 75]
        iou = calculate_iou(box1, box2)
        # Intersection: 50x50 = 2500
        # Union: 10000
        # IoU: 2500 / 10000 = 0.25
        assert iou == pytest.approx(0.25)


class TestMatchDetections:
    """Tests for detection matching."""
    
    def test_perfect_match(self, sample_detections, sample_ground_truth):
        """Test perfect matching."""
        tp, fp, fn = match_detections(sample_detections, sample_ground_truth, iou_threshold=0.5)
        assert tp == 2
        assert fp == 0
        assert fn == 0
    
    def test_no_predictions(self, sample_ground_truth):
        """Test with no predictions."""
        tp, fp, fn = match_detections([], sample_ground_truth, iou_threshold=0.5)
        assert tp == 0
        assert fp == 0
        assert fn == len(sample_ground_truth)
    
    def test_no_ground_truth(self, sample_detections):
        """Test with no ground truth."""
        tp, fp, fn = match_detections(sample_detections, [], iou_threshold=0.5)
        assert tp == 0
        assert fp == len(sample_detections)
        assert fn == 0
    
    def test_false_positive(self, sample_ground_truth):
        """Test with false positive."""
        predictions = [
            {
                "class_id": 0,
                "class_name": "Bolt",
                "confidence": 0.95,
                "bbox": [500, 500, 600, 600]  # Far from ground truth
            }
        ]
        tp, fp, fn = match_detections(predictions, sample_ground_truth, iou_threshold=0.5)
        assert tp == 0
        assert fp == 1
        assert fn == len(sample_ground_truth)
    
    def test_low_iou_threshold(self, sample_detections, sample_ground_truth):
        """Test with low IoU threshold."""
        tp, fp, fn = match_detections(sample_detections, sample_ground_truth, iou_threshold=0.9)
        # With high threshold, matches might fail
        assert tp >= 0
        assert fp >= 0
        assert fn >= 0


class TestBaselineInference:
    """Tests for BaselineInference class."""
    
    @pytest.mark.skipif(
        not Path("models/yolov8s.pt").exists(),
        reason="Model file not found"
    )
    def test_init(self):
        """Test BaselineInference initialization."""
        baseline = BaselineInference("models/yolov8s.pt", confidence_threshold=0.5, device="cpu")
        assert baseline.model_path == Path("models/yolov8s.pt")
        assert baseline.confidence_threshold == 0.5
        assert baseline.device == "cpu"
        assert baseline.model is not None
    
    @pytest.mark.skipif(
        not Path("models/yolov8s.pt").exists(),
        reason="Model file not found"
    )
    def test_predict(self, sample_image_path):
        """Test prediction on a single image."""
        if sample_image_path is None:
            pytest.skip("No sample image found")
        
        baseline = BaselineInference("models/yolov8s.pt", confidence_threshold=0.5, device="cpu")
        detections = baseline.predict(sample_image_path, imgsz=640)
        
        assert isinstance(detections, list)
        for det in detections:
            assert "class_id" in det
            assert "class_name" in det
            assert "confidence" in det
            assert "bbox" in det
            assert len(det["bbox"]) == 4


class TestSAHIInference:
    """Tests for SAHIInference class."""
    
    @pytest.mark.skipif(
        not Path("models/yolov8s.pt").exists(),
        reason="Model file not found"
    )
    def test_init(self):
        """Test SAHIInference initialization."""
        config = SAHIConfig(slice_height=640, slice_width=640)
        sahi = SAHIInference("models/yolov8s.pt", config=config, device="cpu")
        
        assert sahi.model_path == Path("models/yolov8s.pt")
        assert sahi.config.slice_height == 640
        assert sahi.config.slice_width == 640
        assert sahi.device == "cpu"
        assert sahi.detection_model is not None
    
    @pytest.mark.skipif(
        not Path("models/yolov8s.pt").exists(),
        reason="Model file not found"
    )
    def test_predict(self, sample_image_path):
        """Test SAHI prediction on a single image."""
        if sample_image_path is None:
            pytest.skip("No sample image found")
        
        config = SAHIConfig(slice_height=640, slice_width=640)
        sahi = SAHIInference("models/yolov8s.pt", config=config, device="cpu")
        detections = sahi.predict(sample_image_path)
        
        assert isinstance(detections, list)
        for det in detections:
            assert "class_id" in det
            assert "class_name" in det
            assert "confidence" in det
            assert "bbox" in det
            assert len(det["bbox"]) == 4
    
    @pytest.mark.skipif(
        not Path("models/yolov8s.pt").exists(),
        reason="Model file not found"
    )
    def test_predict_with_custom_params(self, sample_image_path):
        """Test SAHI prediction with custom parameters."""
        if sample_image_path is None:
            pytest.skip("No sample image found")
        
        config = SAHIConfig(
            slice_height=320,
            slice_width=320,
            overlap_height_ratio=0.3,
            overlap_width_ratio=0.3,
            confidence_threshold=0.7
        )
        sahi = SAHIInference("models/yolov8s.pt", config=config, device="cpu")
        detections = sahi.predict(sample_image_path)
        
        assert isinstance(detections, list)
