"""
Tests for dataset module.
"""

import pytest
import yaml
from pathlib import Path

from screw_detector.dataset import DatasetStats, slice_yolo_dataset, validate_dataset


class TestDatasetStats:
    """Tests for DatasetStats class."""
    
    def test_init(self, configs_dir):
        """Test DatasetStats initialization."""
        data_yaml = configs_dir / "data.yaml"
        if data_yaml.exists():
            stats = DatasetStats(str(data_yaml))
            assert stats.data_yaml_path == data_yaml
            assert stats.data_cfg is not None
    
    def test_load_data_config(self, configs_dir):
        """Test loading data configuration."""
        data_yaml = configs_dir / "data.yaml"
        if data_yaml.exists():
            stats = DatasetStats(str(data_yaml))
            assert "names" in stats.data_cfg
            assert "nc" in stats.data_cfg
    
    def test_get_split_stats(self, configs_dir):
        """Test getting statistics for a split."""
        data_yaml = configs_dir / "data.yaml"
        if data_yaml.exists():
            stats = DatasetStats(str(data_yaml))
            try:
                n_img, n_obj, avg_sz = stats.get_split_stats("test")
                assert isinstance(n_img, int)
                assert isinstance(n_obj, int)
                assert isinstance(avg_sz, float)
            except ValueError:
                # Split might not exist in config
                pass
    
    def test_get_all_stats(self, configs_dir):
        """Test getting statistics for all splits."""
        data_yaml = configs_dir / "data.yaml"
        if data_yaml.exists():
            stats = DatasetStats(str(data_yaml))
            all_stats = stats.get_all_stats()
            assert isinstance(all_stats, dict)


class TestValidateDataset:
    """Tests for dataset validation."""
    
    def test_validate_dataset(self, configs_dir):
        """Test dataset validation."""
        data_yaml = configs_dir / "data.yaml"
        if data_yaml.exists():
            results = validate_dataset(str(data_yaml))
            assert isinstance(results, dict)
            for split, split_results in results.items():
                assert "missing_labels" in split_results
                assert "empty_labels" in split_results
                assert "corrupt_images" in split_results


class TestSliceDataset:
    """Tests for dataset slicing."""
    
    def test_slice_yolo_dataset(self, configs_dir, temp_dir):
        """Test dataset slicing."""
        data_yaml = configs_dir / "data.yaml"
        if data_yaml.exists():
            # Use a small slice size for faster testing
            output_dir = temp_dir / "sliced"
            tile_counts = slice_yolo_dataset(
                str(data_yaml),
                out_dir=str(output_dir),
                slice_size=320,
                overlap=64,
                visibility_threshold=0.3
            )
            
            assert isinstance(tile_counts, dict)
            assert output_dir.exists()
    
    def test_slice_yolo_dataset_with_custom_params(self, configs_dir, temp_dir):
        """Test dataset slicing with custom parameters."""
        data_yaml = configs_dir / "data.yaml"
        if data_yaml.exists():
            output_dir = temp_dir / "sliced_custom"
            tile_counts = slice_yolo_dataset(
                str(data_yaml),
                out_dir=str(output_dir),
                slice_size=256,
                overlap=32,
                visibility_threshold=0.5
            )
            
            assert isinstance(tile_counts, dict)
            assert output_dir.exists()
