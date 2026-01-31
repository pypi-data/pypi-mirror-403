#!/usr/bin/env python3
"""
Training script for Screw Detector.

This script provides a command-line interface for training YOLOv8 models
with various configurations including baseline and sliced training.
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from screw_detector.config import TrainingConfig, Config
from screw_detector.dataset import DatasetStats
from screw_detector.models import ModelTrainer


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Train YOLOv8 model for screw detection",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Model arguments
    parser.add_argument(
        "--model",
        type=str,
        default="yolov8s.pt",
        help="Base model to train (e.g., yolov8s.pt, yolov8m.pt)"
    )
    
    # Data arguments
    parser.add_argument(
        "--data",
        type=str,
        default="data/configs/data.yaml",
        help="Path to data configuration file"
    )
    parser.add_argument(
        "--sliced-data",
        action="store_true",
        help="Use sliced dataset for training"
    )
    
    # Training arguments
    parser.add_argument(
        "--imgsz",
        type=int,
        default=1280,
        help="Image size for training"
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=150,
        help="Number of training epochs"
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=4,
        help="Batch size"
    )
    parser.add_argument(
        "--optimizer",
        type=str,
        default="AdamW",
        choices=["SGD", "Adam", "AdamW"],
        help="Optimizer to use"
    )
    parser.add_argument(
        "--patience",
        type=int,
        default=30,
        help="Early stopping patience"
    )
    
    # Output arguments
    parser.add_argument(
        "--project",
        type=str,
        default="results",
        help="Project directory for results"
    )
    parser.add_argument(
        "--name",
        type=str,
        default="train_baseline",
        help="Experiment name"
    )
    
    # Device arguments
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        help="Device to use (cpu, cuda, mps)"
    )
    
    # Other arguments
    parser.add_argument(
        "--pretrained",
        action="store_true",
        default=True,
        help="Use pretrained weights"
    )
    parser.add_argument(
        "--no-pretrained",
        action="store_false",
        dest="pretrained",
        help="Do not use pretrained weights"
    )
    parser.add_argument(
        "--resume",
        type=str,
        default=None,
        help="Path to checkpoint to resume training from"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show dataset statistics before training"
    )
    
    return parser.parse_args()


def main():
    """Main training function."""
    args = parse_args()
    
    print("\n" + "="*60)
    print("SCREW DETECTOR - TRAINING")
    print("="*60)
    
    # Show dataset statistics if requested
    if args.stats:
        print("\nDataset Statistics:")
        print("-"*60)
        stats = DatasetStats(args.data)
        stats.print_stats()
    
    # Create training configuration
    config = TrainingConfig(
        data=args.data,
        imgsz=args.imgsz,
        epochs=args.epochs,
        batch=args.batch,
        optimizer=args.optimizer,
        patience=args.patience,
        project=args.project,
        name=args.name,
        device=args.device,
        pretrained=args.pretrained,
    )
    
    # Update data path if using sliced dataset
    if args.sliced_data:
        config.data = "data/configs/sliced_data.yaml"
        config.imgsz = 640  # Sliced data uses 640x640 tiles
        config.batch = 16  # Larger batch for smaller images
        config.name = "train_sliced"
        print("\nUsing sliced dataset configuration")
    
    # Create trainer
    trainer = ModelTrainer(model_name=args.model, config=config)
    
    # Resume from checkpoint if specified
    if args.resume:
        print(f"\nResuming training from: {args.resume}")
        results = trainer.resume(args.resume)
    else:
        # Train from scratch
        print(f"\nTraining model: {args.model}")
        results = trainer.train()
    
    print("\n" + "="*60)
    print("TRAINING COMPLETE")
    print("="*60)
    print(f"Results saved to: {Path(config.project) / config.name}")


if __name__ == "__main__":
    main()
