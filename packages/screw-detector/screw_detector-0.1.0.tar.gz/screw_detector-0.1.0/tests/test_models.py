"""
Tests for models module.
"""

import pytest
from pathlib import Path

from screw_detector.models import (
    YOLOModel,
    ModelTrainer,
    ModelExporter,
    get_model_size,
    list_available_models
)
from screw_detector.config import TrainingConfig, ExportConfig


class TestYOLOModel:
    """Tests for YOLOModel class."""
    
    @pytest.mark.skipif(
        not Path("models/yolov8s.pt").exists(),
        reason="Model file not found"
    )
    def test_init(self):
        """Test YOLOModel initialization."""
        model = YOLOModel("models/yolov8s.pt", device="cpu")
        assert model.model_path == Path("models/yolov8s.pt")
        assert model.device == "cpu"
        assert model.model is not None
    
    @pytest.mark.skipif(
        not Path("models/yolov8s.pt").exists(),
        reason="Model file not found"
    )
    def test_from_pretrained(self):
        """Test loading pretrained model."""
        model = YOLOModel.from_pretrained("yolov8s.pt", device="cpu")
        assert model.model is not None


class TestModelTrainer:
    """Tests for ModelTrainer class."""
    
    def test_init(self):
        """Test ModelTrainer initialization."""
        config = TrainingConfig(epochs=10, batch=2)
        trainer = ModelTrainer("yolov8s.pt", config=config)
        
        assert trainer.model_name == "yolov8s.pt"
        assert trainer.config.epochs == 10
        assert trainer.config.batch == 2
        assert trainer.model is not None
    
    def test_init_with_default_config(self):
        """Test ModelTrainer with default configuration."""
        trainer = ModelTrainer("yolov8s.pt")
        
        assert trainer.model_name == "yolov8s.pt"
        assert trainer.config is not None
        assert trainer.config.epochs == 150
        assert trainer.config.batch == 4


class TestModelExporter:
    """Tests for ModelExporter class."""
    
    @pytest.mark.skipif(
        not Path("models/yolov8s.pt").exists(),
        reason="Model file not found"
    )
    def test_init(self):
        """Test ModelExporter initialization."""
        config = ExportConfig(format="onnx")
        exporter = ModelExporter("models/yolov8s.pt", config=config)
        
        assert exporter.model_path == Path("models/yolov8s.pt")
        assert exporter.config.format == "onnx"
        assert exporter.model is not None
    
    @pytest.mark.skipif(
        not Path("models/yolov8s.pt").exists(),
        reason="Model file not found"
    )
    def test_init_with_default_config(self):
        """Test ModelExporter with default configuration."""
        exporter = ModelExporter("models/yolov8s.pt")
        
        assert exporter.model_path == Path("models/yolov8s.pt")
        assert exporter.config is not None
        assert exporter.config.format == "onnx"


class TestGetModelSize:
    """Tests for get_model_size function."""
    
    @pytest.mark.skipif(
        not Path("models/yolov8s.pt").exists(),
        reason="Model file not found"
    )
    def test_get_model_size(self):
        """Test getting model size."""
        size = get_model_size("models/yolov8s.pt")
        
        assert "bytes" in size
        assert "kb" in size
        assert "mb" in size
        assert size["bytes"] > 0
        assert size["kb"] > 0
        assert size["mb"] > 0
    
    def test_get_model_size_nonexistent(self):
        """Test getting size of non-existent model."""
        with pytest.raises(FileNotFoundError):
            get_model_size("nonexistent_model.pt")


class TestListAvailableModels:
    """Tests for list_available_models function."""
    
    def test_list_available_models(self):
        """Test listing available models."""
        models = list_available_models()
        
        assert isinstance(models, list)
        assert len(models) > 0
        assert "yolov8s.pt" in models
        assert "yolov8n.pt" in models
        assert "yolov8m.pt" in models
        assert "yolov8l.pt" in models
        assert "yolov8x.pt" in models
