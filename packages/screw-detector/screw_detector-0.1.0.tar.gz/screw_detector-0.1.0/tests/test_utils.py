"""
Tests for utils module.
"""

import pytest
import numpy as np
from pathlib import Path

from screw_detector.utils import (
    calculate_metrics,
    calculate_size_based_recall,
    get_image_size,
    load_ground_truth
)


class TestCalculateMetrics:
    """Tests for calculate_metrics function."""
    
    def test_perfect_predictions(self, sample_detections, sample_ground_truth):
        """Test with perfect predictions."""
        predictions = [sample_detections]
        ground_truth = [sample_ground_truth]
        
        metrics = calculate_metrics(predictions, ground_truth)
        
        assert metrics["precision"] == pytest.approx(1.0)
        assert metrics["recall"] == pytest.approx(1.0)
        assert metrics["f1_score"] == pytest.approx(1.0)
        assert metrics["true_positives"] == 2
        assert metrics["false_positives"] == 0
        assert metrics["false_negatives"] == 0
    
    def test_no_predictions(self, sample_ground_truth):
        """Test with no predictions."""
        predictions = [[]]
        ground_truth = [sample_ground_truth]
        
        metrics = calculate_metrics(predictions, ground_truth)
        
        assert metrics["precision"] == pytest.approx(0.0)
        assert metrics["recall"] == pytest.approx(0.0)
        assert metrics["f1_score"] == pytest.approx(0.0)
        assert metrics["true_positives"] == 0
        assert metrics["false_positives"] == 0
        assert metrics["false_negatives"] == len(sample_ground_truth)
    
    def test_no_ground_truth(self, sample_detections):
        """Test with no ground truth."""
        predictions = [sample_detections]
        ground_truth = [[]]
        
        metrics = calculate_metrics(predictions, ground_truth)
        
        assert metrics["precision"] == pytest.approx(0.0)
        assert metrics["recall"] == pytest.approx(0.0)
        assert metrics["f1_score"] == pytest.approx(0.0)
        assert metrics["true_positives"] == 0
        assert metrics["false_positives"] == len(sample_detections)
        assert metrics["false_negatives"] == 0


class TestCalculateSizeBasedRecall:
    """Tests for calculate_size_based_recall function."""
    
    def test_size_based_recall(self):
        """Test size-based recall calculation."""
        # Create predictions and ground truth with different object sizes
        predictions = [
            [
                {"class_id": 0, "bbox": [10, 10, 20, 20]},  # Small (10px)
                {"class_id": 0, "bbox": [30, 30, 50, 50]},  # Medium (20px)
                {"class_id": 0, "bbox": [60, 60, 100, 100]},  # Large (40px)
            ]
        ]
        ground_truth = [
            [
                {"class_id": 0, "bbox": [10, 10, 20, 20]},  # Small
                {"class_id": 0, "bbox": [30, 30, 50, 50]},  # Medium
                {"class_id": 0, "bbox": [60, 60, 100, 100]},  # Large
            ]
        ]
        image_sizes = [(100, 100)]
        
        results = calculate_size_based_recall(predictions, ground_truth, image_sizes)
        
        assert "Small (<15px)" in results
        assert "Medium (15-30px)" in results
        assert "Large (>30px)" in results
        
        # All objects should be detected
        for size_bin, stats in results.items():
            assert stats["recall"] == pytest.approx(1.0)
            assert stats["true_positives"] == 1
            assert stats["false_negatives"] == 0
    
    def test_size_based_recall_with_misses(self):
        """Test size-based recall with missed detections."""
        predictions = [
            [
                {"class_id": 0, "bbox": [30, 30, 50, 50]},  # Medium detected
                # Small and Large missed
            ]
        ]
        ground_truth = [
            [
                {"class_id": 0, "bbox": [10, 10, 20, 20]},  # Small missed
                {"class_id": 0, "bbox": [30, 30, 50, 50]},  # Medium detected
                {"class_id": 0, "bbox": [60, 60, 100, 100]},  # Large missed
            ]
        ]
        image_sizes = [(100, 100)]
        
        results = calculate_size_based_recall(predictions, ground_truth, image_sizes)
        
        # Small and Large should have 0 recall
        assert results["Small (<15px)"]["recall"] == pytest.approx(0.0)
        assert results["Large (>30px)"]["recall"] == pytest.approx(0.0)
        
        # Medium should have 1.0 recall
        assert results["Medium (15-30px)"]["recall"] == pytest.approx(1.0)


class TestGetImageSize:
    """Tests for get_image_size function."""
    
    @pytest.mark.skipif(
        not Path("data/raw/test/images").exists(),
        reason="Test images not found"
    )
    def test_get_image_size(self, test_data_dir):
        """Test getting image size."""
        images = list(test_data_dir.glob("*.jpg"))
        if not images:
            pytest.skip("No test images found")
        
        width, height = get_image_size(images[0])
        
        assert isinstance(width, int)
        assert isinstance(height, int)
        assert width > 0
        assert height > 0
    
    def test_get_image_size_nonexistent(self):
        """Test getting size of non-existent image."""
        with pytest.raises(ValueError):
            get_image_size("nonexistent_image.jpg")


class TestLoadGroundTruth:
    """Tests for load_ground_truth function."""
    
    @pytest.mark.skipif(
        not Path("data/raw/test/labels").exists(),
        reason="Test labels not found"
    )
    def test_load_ground_truth(self, test_data_dir):
        """Test loading ground truth annotations."""
        label_dir = test_data_dir.parent / "labels"
        labels = list(label_dir.glob("*.txt"))
        if not labels:
            pytest.skip("No test labels found")
        
        # Assume image size of 640x640
        annotations = load_ground_truth(labels[0], 640, 640)
        
        assert isinstance(annotations, list)
        for ann in annotations:
            assert "class_id" in ann
            assert "bbox" in ann
            assert len(ann["bbox"]) == 4
    
    def test_load_ground_truth_nonexistent(self):
        """Test loading non-existent ground truth file."""
        annotations = load_ground_truth("nonexistent_label.txt", 640, 640)
        
        assert annotations == []
    
    def test_load_ground_truth_empty(self, temp_dir):
        """Test loading empty ground truth file."""
        empty_label = temp_dir / "empty.txt"
        empty_label.write_text("")
        
        annotations = load_ground_truth(empty_label, 640, 640)
        
        assert annotations == []
