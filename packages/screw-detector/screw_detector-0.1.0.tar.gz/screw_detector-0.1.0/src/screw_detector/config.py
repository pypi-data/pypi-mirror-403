"""
Configuration management for Screw Detector.

This module provides configuration classes and utilities for managing
training, inference, and dataset configurations.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union

import yaml


@dataclass
class SAHIConfig:
    """Configuration for SAHI (Slicing Aided Hyper Inference)."""
    
    slice_height: int = 640
    slice_width: int = 640
    overlap_height_ratio: float = 0.2
    overlap_width_ratio: float = 0.2
    confidence_threshold: float = 0.6
    postprocess_type: str = "NMS"
    postprocess_match_threshold: float = 0.6


@dataclass
class TrainingConfig:
    """Configuration for model training."""
    
    data: str = "data/configs/data.yaml"
    imgsz: int = 1280
    epochs: int = 150
    batch: int = 4
    optimizer: str = "AdamW"
    patience: int = 30
    mosaic: float = 1.0
    project: str = "results"
    name: str = "train_baseline"
    device: str = "cpu"
    pretrained: bool = True
    verbose: bool = True
    save: bool = True
    plots: bool = True


@dataclass
class SlicingConfig:
    """Configuration for dataset slicing."""
    
    slice_size: int = 640
    overlap: int = 128
    visibility_threshold: float = 0.3
    output_dir: str = "data/processed/sliced"


@dataclass
class ExportConfig:
    """Configuration for model export."""
    
    format: str = "onnx"  # onnx, openvino
    half: bool = False
    simplify: bool = True
    dynamic: bool = False
    int8: bool = False  # For OpenVINO INT8 quantization


@dataclass
class Config:
    """Main configuration class for Screw Detector."""
    
    # Paths
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent)
    data_dir: Path = field(init=False)
    models_dir: Path = field(init=False)
    results_dir: Path = field(init=False)
    notebooks_dir: Path = field(init=False)
    
    # Sub-configurations
    sahi: SAHIConfig = field(default_factory=SAHIConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    slicing: SlicingConfig = field(default_factory=SlicingConfig)
    export: ExportConfig = field(default_factory=ExportConfig)
    
    def __post_init__(self):
        """Initialize path configurations."""
        self.data_dir = self.project_root / "data"
        self.models_dir = self.project_root / "models"
        self.results_dir = self.project_root / "results"
        self.notebooks_dir = self.project_root / "notebooks"
    
    @classmethod
    def from_yaml(cls, yaml_path: Union[str, Path]) -> "Config":
        """
        Load configuration from a YAML file.
        
        Args:
            yaml_path: Path to the YAML configuration file.
            
        Returns:
            Config instance with values from YAML file.
        """
        yaml_path = Path(yaml_path)
        if not yaml_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {yaml_path}")
        
        with open(yaml_path, "r") as f:
            config_dict = yaml.safe_load(f)
        
        config = cls()
        
        # Update SAHI config
        if "sahi" in config_dict:
            for key, value in config_dict["sahi"].items():
                if hasattr(config.sahi, key):
                    setattr(config.sahi, key, value)
        
        # Update training config
        if "training" in config_dict:
            for key, value in config_dict["training"].items():
                if hasattr(config.training, key):
                    setattr(config.training, key, value)
        
        # Update slicing config
        if "slicing" in config_dict:
            for key, value in config_dict["slicing"].items():
                if hasattr(config.slicing, key):
                    setattr(config.slicing, key, value)
        
        # Update export config
        if "export" in config_dict:
            for key, value in config_dict["export"].items():
                if hasattr(config.export, key):
                    setattr(config.export, key, value)
        
        return config
    
    def to_yaml(self, yaml_path: Union[str, Path]) -> None:
        """
        Save configuration to a YAML file.
        
        Args:
            yaml_path: Path to save the YAML configuration file.
        """
        yaml_path = Path(yaml_path)
        yaml_path.parent.mkdir(parents=True, exist_ok=True)
        
        config_dict = {
            "sahi": {
                "slice_height": self.sahi.slice_height,
                "slice_width": self.sahi.slice_width,
                "overlap_height_ratio": self.sahi.overlap_height_ratio,
                "overlap_width_ratio": self.sahi.overlap_width_ratio,
                "confidence_threshold": self.sahi.confidence_threshold,
                "postprocess_type": self.sahi.postprocess_type,
                "postprocess_match_threshold": self.sahi.postprocess_match_threshold,
            },
            "training": {
                "data": self.training.data,
                "imgsz": self.training.imgsz,
                "epochs": self.training.epochs,
                "batch": self.training.batch,
                "optimizer": self.training.optimizer,
                "patience": self.training.patience,
                "mosaic": self.training.mosaic,
                "project": self.training.project,
                "name": self.training.name,
                "device": self.training.device,
                "pretrained": self.training.pretrained,
                "verbose": self.training.verbose,
                "save": self.training.save,
                "plots": self.training.plots,
            },
            "slicing": {
                "slice_size": self.slicing.slice_size,
                "overlap": self.slicing.overlap,
                "visibility_threshold": self.slicing.visibility_threshold,
                "output_dir": self.slicing.output_dir,
            },
            "export": {
                "format": self.export.format,
                "half": self.export.half,
                "simplify": self.export.simplify,
                "dynamic": self.export.dynamic,
                "int8": self.export.int8,
            },
        }
        
        with open(yaml_path, "w") as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)


def load_config(config_path: Optional[Union[str, Path]] = None) -> Config:
    """
    Load configuration from a YAML file or return default configuration.
    
    Args:
        config_path: Optional path to a YAML configuration file.
                    If None, returns default configuration.
    
    Returns:
        Config instance.
    """
    if config_path is not None:
        return Config.from_yaml(config_path)
    return Config()


def get_data_config(data_yaml_path: Union[str, Path]) -> Dict:
    """
    Load dataset configuration from a YAML file.
    
    Args:
        data_yaml_path: Path to the data YAML file.
        
    Returns:
        Dictionary containing dataset configuration.
    """
    data_yaml_path = Path(data_yaml_path)
    if not data_yaml_path.exists():
        raise FileNotFoundError(f"Data configuration file not found: {data_yaml_path}")
    
    with open(data_yaml_path, "r") as f:
        return yaml.safe_load(f)
