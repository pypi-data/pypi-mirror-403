"""
Model utilities for Screw Detector.

This module provides classes and functions for training,
loading, and exporting YOLOv8 models.
"""

from pathlib import Path
from typing import Dict, Optional, Union, List
import time

from ultralytics import YOLO

from .config import TrainingConfig, ExportConfig, Config


class YOLOModel:
    """
    Wrapper class for YOLOv8 models.
    
    This class provides a convenient interface for loading
    and using YOLOv8 models.
    """
    
    def __init__(
        self,
        model_path: Union[str, Path],
        device: str = "cpu"
    ):
        """
        Initialize YOLOModel.
        
        Args:
            model_path: Path to the YOLOv8 model file (.pt).
            device: Device to run inference on (cpu, cuda, mps).
        """
        self.model_path = Path(model_path)
        self.device = device
        self.model = YOLO(str(self.model_path))
    
    @classmethod
    def from_pretrained(
        cls,
        model_name: str = "yolov8s.pt",
        device: str = "cpu"
    ) -> "YOLOModel":
        """
        Load a pretrained YOLOv8 model.
        
        Args:
            model_name: Name of the pretrained model (e.g., yolov8s.pt, yolov8m.pt).
            device: Device to run inference on.
            
        Returns:
            YOLOModel instance.
        """
        return cls(model_name, device=device)
    
    def predict(self, *args, **kwargs):
        """Run prediction using the underlying YOLO model."""
        return self.model.predict(*args, **kwargs)
    
    def export(
        self,
        format: str = "onnx",
        **kwargs
    ) -> Path:
        """
        Export the model to a different format.
        
        Args:
            format: Export format (onnx, torchscript, openvino, etc.).
            **kwargs: Additional arguments passed to YOLO export.
            
        Returns:
            Path to the exported model file.
        """
        export_path = self.model.export(format=format, **kwargs)
        return Path(export_path)


class ModelTrainer:
    """
    Class for training YOLOv8 models.
    
    This class provides a convenient interface for training
    YOLOv8 models with custom configurations.
    """
    
    def __init__(
        self,
        model_name: str = "yolov8s.pt",
        config: Optional[TrainingConfig] = None
    ):
        """
        Initialize ModelTrainer.
        
        Args:
            model_name: Name of the base model to train.
            config: TrainingConfig instance. If None, uses default config.
        """
        self.model_name = model_name
        self.config = config or TrainingConfig()
        self.model = YOLO(model_name)
    
    def train(self, **kwargs) -> Dict:
        """
        Train the model.
        
        Args:
            **kwargs: Override training configuration parameters.
            
        Returns:
            Training results dictionary.
        """
        # Merge config with kwargs
        train_params = {
            'data': self.config.data,
            'imgsz': self.config.imgsz,
            'epochs': self.config.epochs,
            'batch': self.config.batch,
            'optimizer': self.config.optimizer,
            'patience': self.config.patience,
            'mosaic': self.config.mosaic,
            'project': self.config.project,
            'name': self.config.name,
            'device': self.config.device,
            'pretrained': self.config.pretrained,
            'verbose': self.config.verbose,
            'save': self.config.save,
            'plots': self.config.plots,
        }
        train_params.update(kwargs)
        
        print("\n" + "="*60)
        print("TRAINING CONFIGURATION")
        print("="*60)
        for key, value in train_params.items():
            print(f"{key}: {value}")
        print("="*60)
        
        start_time = time.time()
        results = self.model.train(**train_params)
        training_time = time.time() - start_time
        
        print(f"\nTraining completed in {training_time:.2f} seconds")
        
        return {
            'results': results,
            'training_time': training_time,
            'config': train_params
        }
    
    def resume(self, checkpoint_path: Union[str, Path], **kwargs) -> Dict:
        """
        Resume training from a checkpoint.
        
        Args:
            checkpoint_path: Path to the checkpoint file (.pt).
            **kwargs: Additional training parameters.
            
        Returns:
            Training results dictionary.
        """
        self.model = YOLO(str(checkpoint_path))
        return self.train(**kwargs)
    
    def tune(
        self,
        data: str,
        epochs: int = 30,
        iterations: int = 300,
        optimizer: str = "AdamW",
        plots: bool = True,
        save: bool = True,
        val: bool = True
    ) -> Dict:
        """
        Run hyperparameter tuning.
        
        Args:
            data: Path to the data YAML file.
            epochs: Number of epochs for each tuning iteration.
            iterations: Number of tuning iterations.
            optimizer: Optimizer to use.
            plots: Whether to save plots.
            save: Whether to save results.
            val: Whether to validate during tuning.
            
        Returns:
            Tuning results dictionary.
        """
        print("\n" + "="*60)
        print("HYPERPARAMETER TUNING")
        print("="*60)
        print(f"Data: {data}")
        print(f"Epochs: {epochs}")
        print(f"Iterations: {iterations}")
        print("="*60)
        
        start_time = time.time()
        results = self.model.tune(
            data=data,
            epochs=epochs,
            iterations=iterations,
            optimizer=optimizer,
            plots=plots,
            save=save,
            val=val
        )
        tuning_time = time.time() - start_time
        
        print(f"\nTuning completed in {tuning_time:.2f} seconds")
        
        return {
            'results': results,
            'tuning_time': tuning_time
        }


class ModelExporter:
    """
    Class for exporting YOLOv8 models to various formats.
    
    This class provides utilities for exporting models to ONNX,
    OpenVINO, and other formats for deployment.
    """
    
    def __init__(
        self,
        model_path: Union[str, Path],
        config: Optional[ExportConfig] = None
    ):
        """
        Initialize ModelExporter.
        
        Args:
            model_path: Path to the YOLOv8 model file (.pt).
            config: ExportConfig instance. If None, uses default config.
        """
        self.model_path = Path(model_path)
        self.config = config or ExportConfig()
        self.model = YOLO(str(self.model_path))
    
    def export_onnx(
        self,
        half: bool = False,
        simplify: bool = True,
        dynamic: bool = False,
        **kwargs
    ) -> Path:
        """
        Export model to ONNX format.
        
        Args:
            half: Export in FP16.
            simplify: Simplify the ONNX model.
            dynamic: Use dynamic axes.
            **kwargs: Additional arguments passed to YOLO export.
            
        Returns:
            Path to the exported ONNX file.
        """
        print("\n" + "="*60)
        print("EXPORTING TO ONNX")
        print("="*60)
        print(f"Model: {self.model_path}")
        print(f"Half: {half}")
        print(f"Simplify: {simplify}")
        print(f"Dynamic: {dynamic}")
        print("="*60)
        
        export_path = self.model.export(
            format="onnx",
            half=half,
            simplify=simplify,
            dynamic=dynamic,
            **kwargs
        )
        
        print(f"\nExported to: {export_path}")
        return Path(export_path)
    
    def export_openvino(
        self,
        half: bool = False,
        int8: bool = False,
        **kwargs
    ) -> Path:
        """
        Export model to OpenVINO format.
        
        Args:
            half: Export in FP16.
            int8: Export in INT8 (quantized).
            **kwargs: Additional arguments passed to YOLO export.
            
        Returns:
            Path to the exported OpenVINO directory.
        """
        print("\n" + "="*60)
        print("EXPORTING TO OPENVINO")
        print("="*60)
        print(f"Model: {self.model_path}")
        print(f"Half: {half}")
        print(f"INT8: {int8}")
        print("="*60)
        
        export_path = self.model.export(
            format="openvino",
            half=half,
            int8=int8,
            **kwargs
        )
        
        print(f"\nExported to: {export_path}")
        return Path(export_path)
    
    def export_torchscript(
        self,
        **kwargs
    ) -> Path:
        """
        Export model to TorchScript format.
        
        Args:
            **kwargs: Additional arguments passed to YOLO export.
            
        Returns:
            Path to the exported TorchScript file.
        """
        print("\n" + "="*60)
        print("EXPORTING TO TORCHSCRIPT")
        print("="*60)
        print(f"Model: {self.model_path}")
        print("="*60)
        
        export_path = self.model.export(
            format="torchscript",
            **kwargs
        )
        
        print(f"\nExported to: {export_path}")
        return Path(export_path)
    
    def export_all(
        self,
        output_dir: Optional[Union[str, Path]] = None
    ) -> Dict[str, Path]:
        """
        Export model to all supported formats.
        
        Args:
            output_dir: Directory to save exported models.
            
        Returns:
            Dictionary mapping format names to export paths.
        """
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        exports = {}
        
        # Export to ONNX
        exports['onnx'] = self.export_onnx(
            half=self.config.half,
            simplify=self.config.simplify,
            dynamic=self.config.dynamic
        )
        
        # Export to OpenVINO
        exports['openvino'] = self.export_openvino(
            half=self.config.half,
            int8=self.config.int8
        )
        
        # Export to TorchScript
        exports['torchscript'] = self.export_torchscript()
        
        return exports


def get_model_size(model_path: Union[str, Path]) -> Dict[str, float]:
    """
    Get the size of a model file in different units.
    
    Args:
        model_path: Path to the model file.
        
    Returns:
        Dictionary with size in bytes, KB, and MB.
    """
    model_path = Path(model_path)
    size_bytes = model_path.stat().st_size
    
    return {
        'bytes': size_bytes,
        'kb': size_bytes / 1024,
        'mb': size_bytes / (1024 * 1024)
    }


def list_available_models() -> List[str]:
    """
    List available pretrained YOLOv8 models.
    
    Returns:
        List of model names.
    """
    return [
        "yolov8n.pt",  # Nano
        "yolov8s.pt",  # Small
        "yolov8m.pt",  # Medium
        "yolov8l.pt",  # Large
        "yolov8x.pt",  # Extra Large
    ]
