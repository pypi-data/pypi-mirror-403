#!/usr/bin/env python3
"""
Evaluation script for Screw Detector.

This script provides a command-line interface for evaluating
YOLOv8 models with various inference strategies.
"""

import argparse
import sys
import time
from pathlib import Path
from typing import List, Dict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from screw_detector.config import SAHIConfig, Config
from screw_detector.inference import BaselineInference, SAHIInference
from screw_detector.utils import (
    calculate_metrics,
    calculate_size_based_recall,
    print_results_table,
    plot_metrics_comparison,
    plot_size_based_recall,
    load_ground_truth,
    get_image_size
)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Evaluate YOLOv8 model for screw detection",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Model arguments
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="Path to trained model file (.pt)"
    )
    
    # Data arguments
    parser.add_argument(
        "--data",
        type=str,
        default="data/configs/data.yaml",
        help="Path to data configuration file"
    )
    parser.add_argument(
        "--split",
        type=str,
        default="test",
        choices=["train", "val", "test"],
        help="Dataset split to evaluate"
    )
    
    # Inference arguments
    parser.add_argument(
        "--strategy",
        type=str,
        default="both",
        choices=["baseline", "sahi", "both"],
        help="Inference strategy to use"
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Image size for baseline inference"
    )
    
    # SAHI arguments
    parser.add_argument(
        "--slice-size",
        type=int,
        default=640,
        help="Slice size for SAHI"
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=128,
        help="Overlap between slices in pixels"
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.6,
        help="Confidence threshold"
    )
    parser.add_argument(
        "--nms-threshold",
        type=float,
        default=0.6,
        help="NMS threshold for SAHI"
    )
    
    # Device arguments
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        help="Device to use (cpu, cuda, mps)"
    )
    
    # Output arguments
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results/evaluation",
        help="Directory to save evaluation results"
    )
    parser.add_argument(
        "--save-plots",
        action="store_true",
        help="Save evaluation plots"
    )
    parser.add_argument(
        "--save-table",
        action="store_true",
        help="Save results table as CSV"
    )
    
    return parser.parse_args()


def load_test_images(data_yaml: str, split: str) -> List[Path]:
    """Load test image paths from data configuration."""
    import yaml
    
    with open(data_yaml, 'r') as f:
        data_cfg = yaml.safe_load(f)
    
    img_dir = Path(data_cfg[split])
    return list(img_dir.glob('*.jpg')) + list(img_dir.glob('*.png'))


def evaluate_baseline(
    model_path: str,
    test_images: List[Path],
    imgsz: int,
    device: str
) -> tuple:
    """Evaluate using baseline inference."""
    print("\n" + "="*60)
    print("BASELINE INFERENCE EVALUATION")
    print("="*60)
    
    baseline = BaselineInference(model_path, device=device)
    
    predictions = []
    ground_truth = []
    image_sizes = []
    
    start_time = time.time()
    
    for img_path in test_images:
        # Get image size
        w, h = get_image_size(img_path)
        image_sizes.append((w, h))
        
        # Load ground truth
        lbl_path = img_path.parent.parent / 'labels' / (img_path.stem + '.txt')
        gt = load_ground_truth(lbl_path, w, h)
        ground_truth.append(gt)
        
        # Run inference
        preds = baseline.predict(img_path, imgsz=imgsz)
        predictions.append(preds)
    
    inference_time = time.time() - start_time
    
    # Calculate metrics
    metrics = calculate_metrics(predictions, ground_truth)
    size_recall = calculate_size_based_recall(predictions, ground_truth, image_sizes)
    
    print(f"\nInference time: {inference_time:.2f}s")
    print(f"Average time per image: {inference_time / len(test_images) * 1000:.2f}ms")
    
    return metrics, size_recall, inference_time


def evaluate_sahi(
    model_path: str,
    test_images: List[Path],
    slice_size: int,
    overlap: int,
    confidence: float,
    nms_threshold: float,
    device: str
) -> tuple:
    """Evaluate using SAHI inference."""
    print("\n" + "="*60)
    print("SAHI INFERENCE EVALUATION")
    print("="*60)
    
    config = SAHIConfig(
        slice_height=slice_size,
        slice_width=slice_size,
        overlap_height_ratio=overlap / slice_size,
        overlap_width_ratio=overlap / slice_size,
        confidence_threshold=confidence,
        postprocess_match_threshold=nms_threshold
    )
    
    sahi = SAHIInference(model_path, config=config, device=device)
    
    predictions = []
    ground_truth = []
    image_sizes = []
    
    start_time = time.time()
    
    for img_path in test_images:
        # Get image size
        w, h = get_image_size(img_path)
        image_sizes.append((w, h))
        
        # Load ground truth
        lbl_path = img_path.parent.parent / 'labels' / (img_path.stem + '.txt')
        gt = load_ground_truth(lbl_path, w, h)
        ground_truth.append(gt)
        
        # Run inference
        preds = sahi.predict(img_path)
        predictions.append(preds)
    
    inference_time = time.time() - start_time
    
    # Calculate metrics
    metrics = calculate_metrics(predictions, ground_truth)
    size_recall = calculate_size_based_recall(predictions, ground_truth, image_sizes)
    
    print(f"\nInference time: {inference_time:.2f}s")
    print(f"Average time per image: {inference_time / len(test_images) * 1000:.2f}ms")
    
    return metrics, size_recall, inference_time


def main():
    """Main evaluation function."""
    args = parse_args()
    
    print("\n" + "="*60)
    print("SCREW DETECTOR - EVALUATION")
    print("="*60)
    print(f"Model: {args.model}")
    print(f"Data: {args.data}")
    print(f"Split: {args.split}")
    print(f"Strategy: {args.strategy}")
    print("="*60)
    
    # Load test images
    test_images = load_test_images(args.data, args.split)
    print(f"\nFound {len(test_images)} test images")
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    # Evaluate baseline
    if args.strategy in ["baseline", "both"]:
        baseline_metrics, baseline_size_recall, baseline_time = evaluate_baseline(
            args.model, test_images, args.imgsz, args.device
        )
        results['Baseline'] = {
            **baseline_metrics,
            'inference_time': baseline_time,
            'avg_time_ms': baseline_time / len(test_images) * 1000
        }
    
    # Evaluate SAHI
    if args.strategy in ["sahi", "both"]:
        sahi_metrics, sahi_size_recall, sahi_time = evaluate_sahi(
            args.model, test_images, args.slice_size, args.overlap,
            args.confidence, args.nms_threshold, args.device
        )
        results['SAHI'] = {
            **sahi_metrics,
            'inference_time': sahi_time,
            'avg_time_ms': sahi_time / len(test_images) * 1000
        }
    
    # Print results
    print("\n" + "="*60)
    print("EVALUATION RESULTS")
    print("="*60)
    print_results_table(results, "METRICS COMPARISON")
    
    # Print size-based recall
    if args.strategy == "both":
        print("\n" + "="*60)
        print("SIZE-BASED RECALL COMPARISON")
        print("="*60)
        for size_bin in baseline_size_recall.keys():
            baseline_recall = baseline_size_recall[size_bin]['recall']
            sahi_recall = sahi_size_recall[size_bin]['recall']
            improvement = (sahi_recall - baseline_recall) / baseline_recall * 100 if baseline_recall > 0 else 0
            print(f"{size_bin}:")
            print(f"  Baseline: {baseline_recall:.4f}")
            print(f"  SAHI: {sahi_recall:.4f}")
            print(f"  Improvement: {improvement:+.2f}%")
    
    # Save plots
    if args.save_plots:
        plot_metrics_comparison(results, output_dir / "metrics_comparison.png")
        if args.strategy == "both":
            size_recall_comparison = {
                'Baseline': {k: v['recall'] for k, v in baseline_size_recall.items()},
                'SAHI': {k: v['recall'] for k, v in sahi_size_recall.items()}
            }
            plot_size_based_recall(size_recall_comparison, output_dir / "size_recall_comparison.png")
        print(f"\nPlots saved to: {output_dir}")
    
    # Save table
    if args.save_table:
        import pandas as pd
        df = pd.DataFrame(results).T
        df.to_csv(output_dir / "results.csv")
        print(f"Results table saved to: {output_dir / 'results.csv'}")
    
    print("\n" + "="*60)
    print("EVALUATION COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
