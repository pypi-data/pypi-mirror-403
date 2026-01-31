"""
Common utilities for Screw Detector.

This module provides utility functions for visualization,
metrics calculation, and other common operations.
"""

from pathlib import Path
from typing import List, Dict, Optional, Union, Tuple
import cv2
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd


def visualize_predictions(
    image_path: Union[str, Path],
    detections: List[Dict],
    output_path: Optional[Union[str, Path]] = None,
    show_confidence: bool = True,
    line_thickness: int = 2,
    font_scale: float = 0.5
) -> np.ndarray:
    """
    Visualize detections on an image.
    
    Args:
        image_path: Path to the input image.
        detections: List of detection dictionaries.
        output_path: Optional path to save the visualization.
        show_confidence: Whether to show confidence scores.
        line_thickness: Thickness of bounding box lines.
        font_scale: Scale factor for text.
        
    Returns:
        Annotated image as numpy array.
    """
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
    
    # Color map for different classes
    colors = [
        (255, 0, 0),    # Red
        (0, 255, 0),    # Green
        (0, 0, 255),    # Blue
        (255, 255, 0),  # Cyan
        (255, 0, 255),  # Magenta
        (0, 255, 255),  # Yellow
        (255, 128, 0),  # Orange
        (128, 0, 255),  # Purple
    ]
    
    for det in detections:
        x1, y1, x2, y2 = map(int, det['bbox'])
        class_id = det.get('class_id', 0)
        class_name = det.get('class_name', f'Class {class_id}')
        confidence = det.get('confidence', 0.0)
        
        color = colors[class_id % len(colors)]
        
        # Draw bounding box
        cv2.rectangle(img, (x1, y1), (x2, y2), color, line_thickness)
        
        # Draw label
        label = class_name
        if show_confidence:
            label += f" {confidence:.2f}"
        
        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 1)
        cv2.rectangle(
            img,
            (x1, y1 - label_size[1] - 10),
            (x1 + label_size[0], y1),
            color,
            -1
        )
        cv2.putText(
            img,
            label,
            (x1, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            (255, 255, 255),
            1
        )
    
    if output_path:
        cv2.imwrite(str(output_path), img)
    
    return img


def visualize_comparison(
    image_path: Union[str, Path],
    baseline_detections: List[Dict],
    sahi_detections: List[Dict],
    output_path: Optional[Union[str, Path]] = None
) -> np.ndarray:
    """
    Visualize comparison between baseline and SAHI detections.
    
    Args:
        image_path: Path to the input image.
        baseline_detections: List of baseline detection dictionaries.
        sahi_detections: List of SAHI detection dictionaries.
        output_path: Optional path to save the visualization.
        
    Returns:
        Comparison image as numpy array.
    """
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
    
    h, w = img.shape[:2]
    comparison = np.zeros((h, w * 2, 3), dtype=np.uint8)
    comparison[:, :w] = img
    comparison[:, w:] = img.copy()
    
    # Draw baseline detections (left side)
    for det in baseline_detections:
        x1, y1, x2, y2 = map(int, det['bbox'])
        cv2.rectangle(comparison, (x1, y1), (x2, y2), (0, 255, 0), 2)
    
    # Draw SAHI detections (right side)
    for det in sahi_detections:
        x1, y1, x2, y2 = map(int, det['bbox'])
        cv2.rectangle(comparison, (x1 + w, y1), (x2 + w, y2), (0, 0, 255), 2)
    
    # Add labels
    cv2.putText(
        comparison,
        "Baseline",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )
    cv2.putText(
        comparison,
        "SAHI",
        (w + 10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 0, 255),
        2
    )
    
    if output_path:
        cv2.imwrite(str(output_path), comparison)
    
    return comparison


def calculate_metrics(
    predictions: List[List[Dict]],
    ground_truth: List[List[Dict]],
    iou_threshold: float = 0.5
) -> Dict[str, float]:
    """
    Calculate evaluation metrics.
    
    Args:
        predictions: List of prediction lists for each image.
        ground_truth: List of ground truth annotation lists for each image.
        iou_threshold: IoU threshold for matching.
        
    Returns:
        Dictionary with precision, recall, and F1 score.
    """
    from .inference import match_detections
    
    total_tp = 0
    total_fp = 0
    total_fn = 0
    
    for preds, gt in zip(predictions, ground_truth):
        tp, fp, fn = match_detections(preds, gt, iou_threshold)
        total_tp += tp
        total_fp += fp
        total_fn += fn
    
    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'true_positives': total_tp,
        'false_positives': total_fp,
        'false_negatives': total_fn
    }


def calculate_size_based_recall(
    predictions: List[List[Dict]],
    ground_truth: List[List[Dict]],
    image_sizes: List[Tuple[int, int]],
    size_bins: List[Tuple[str, Tuple[float, float]]] = None
) -> Dict[str, Dict[str, float]]:
    """
    Calculate recall for different object size bins.
    
    Args:
        predictions: List of prediction lists for each image.
        ground_truth: List of ground truth annotation lists for each image.
        image_sizes: List of (width, height) tuples for each image.
        size_bins: List of (name, (min_size, max_size)) tuples.
                   Default: Small (<15px), Medium (15-30px), Large (>30px).
        
    Returns:
        Dictionary with recall metrics for each size bin.
    """
    from .inference import match_detections, calculate_iou
    
    if size_bins is None:
        size_bins = [
            ('Small (<15px)', (0, 15)),
            ('Medium (15-30px)', (15, 30)),
            ('Large (>30px)', (30, float('inf'))),
        ]
    
    # Initialize counters for each bin
    bin_stats = {name: {'tp': 0, 'fn': 0} for name, _ in size_bins}
    
    for preds, gt, (img_w, img_h) in zip(predictions, ground_truth, image_sizes):
        # Calculate object sizes
        gt_sizes = []
        for obj in gt:
            x1, y1, x2, y2 = obj['bbox']
            size = max(x2 - x1, y2 - y1)
            gt_sizes.append(size)
        
        # Match predictions with ground truth
        matched_gt = set()
        for pred in preds:
            best_iou = 0.0
            best_gt_idx = -1
            
            for gt_idx, gt_obj in enumerate(gt):
                if gt_idx in matched_gt:
                    continue
                
                iou = calculate_iou(pred['bbox'], gt_obj['bbox'])
                if iou > best_iou:
                    best_iou = iou
                    best_gt_idx = gt_idx
            
            if best_iou >= 0.5:
                matched_gt.add(best_gt_idx)
        
        # Update bin statistics
        for gt_idx, size in enumerate(gt_sizes):
            for bin_name, (min_size, max_size) in size_bins:
                if min_size <= size < max_size:
                    if gt_idx in matched_gt:
                        bin_stats[bin_name]['tp'] += 1
                    else:
                        bin_stats[bin_name]['fn'] += 1
                    break
    
    # Calculate recall for each bin
    results = {}
    for bin_name, stats in bin_stats.items():
        recall = stats['tp'] / (stats['tp'] + stats['fn']) if (stats['tp'] + stats['fn']) > 0 else 0
        results[bin_name] = {
            'recall': recall,
            'true_positives': stats['tp'],
            'false_negatives': stats['fn'],
            'total_objects': stats['tp'] + stats['fn']
        }
    
    return results


def plot_metrics_comparison(
    metrics_dict: Dict[str, Dict[str, float]],
    output_path: Optional[Union[str, Path]] = None
) -> None:
    """
    Plot comparison of metrics across different models/strategies.
    
    Args:
        metrics_dict: Dictionary mapping model names to metric dictionaries.
        output_path: Optional path to save the plot.
    """
    models = list(metrics_dict.keys())
    metrics = ['precision', 'recall', 'f1_score']
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = np.arange(len(models))
    width = 0.25
    
    for i, metric in enumerate(metrics):
        values = [metrics_dict[model][metric] for model in models]
        ax.bar(x + i * width, values, width, label=metric.capitalize())
    
    ax.set_xlabel('Model/Strategy')
    ax.set_ylabel('Score')
    ax.set_title('Metrics Comparison')
    ax.set_xticks(x + width)
    ax.set_xticklabels(models)
    ax.legend()
    ax.set_ylim([0, 1])
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(str(output_path), dpi=300, bbox_inches='tight')
    else:
        plt.show()
    
    plt.close()


def plot_size_based_recall(
    size_recall_dict: Dict[str, Dict[str, float]],
    output_path: Optional[Union[str, Path]] = None
) -> None:
    """
    Plot size-based recall comparison.
    
    Args:
        size_recall_dict: Dictionary mapping model names to size-based recall dictionaries.
        output_path: Optional path to save the plot.
    """
    models = list(size_recall_dict.keys())
    size_bins = list(size_recall_dict[models[0]].keys())
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = np.arange(len(size_bins))
    width = 0.8 / len(models)
    
    for i, model in enumerate(models):
        recalls = [size_recall_dict[model][bin_name]['recall'] for bin_name in size_bins]
        ax.bar(x + i * width, recalls, width, label=model)
    
    ax.set_xlabel('Object Size')
    ax.set_ylabel('Recall')
    ax.set_title('Size-Based Recall Comparison')
    ax.set_xticks(x + width / 2)
    ax.set_xticklabels(size_bins, rotation=15, ha='right')
    ax.legend()
    ax.set_ylim([0, 1])
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(str(output_path), dpi=300, bbox_inches='tight')
    else:
        plt.show()
    
    plt.close()


def create_results_table(
    results_dict: Dict[str, Dict[str, float]],
    output_path: Optional[Union[str, Path]] = None
) -> pd.DataFrame:
    """
    Create a results table as a pandas DataFrame.
    
    Args:
        results_dict: Dictionary mapping model names to metric dictionaries.
        output_path: Optional path to save the table as CSV.
        
    Returns:
        pandas DataFrame with results.
    """
    df = pd.DataFrame(results_dict).T
    
    if output_path:
        df.to_csv(str(output_path))
    
    return df


def print_results_table(
    results_dict: Dict[str, Dict[str, float]],
    title: str = "RESULTS"
) -> None:
    """
    Print a formatted results table.
    
    Args:
        results_dict: Dictionary mapping model names to metric dictionaries.
        title: Title for the table.
    """
    print("\n" + "="*60)
    print(title)
    print("="*60)
    
    df = pd.DataFrame(results_dict).T
    print(df.to_string())
    
    print("="*60)


def get_image_size(image_path: Union[str, Path]) -> Tuple[int, int]:
    """
    Get the size of an image.
    
    Args:
        image_path: Path to the image file.
        
    Returns:
        Tuple of (width, height).
    """
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
    
    h, w = img.shape[:2]
    return w, h


def load_ground_truth(
    label_path: Union[str, Path],
    image_width: int,
    image_height: int
) -> List[Dict]:
    """
    Load ground truth annotations from a YOLO format label file.
    
    Args:
        label_path: Path to the label file.
        image_width: Width of the corresponding image.
        image_height: Height of the corresponding image.
        
    Returns:
        List of ground truth annotation dictionaries.
    """
    label_path = Path(label_path)
    if not label_path.exists():
        return []
    
    annotations = []
    
    with open(label_path, 'r') as f:
        for line in f:
            parts = list(map(float, line.split()))
            if len(parts) >= 5:
                class_id = int(parts[0])
                x_center, y_center, width, height = parts[1:5]
                
                # Convert from normalized to absolute coordinates
                x1 = int((x_center - width / 2) * image_width)
                y1 = int((y_center - height / 2) * image_height)
                x2 = int((x_center + width / 2) * image_width)
                y2 = int((y_center + height / 2) * image_height)
                
                annotations.append({
                    'class_id': class_id,
                    'bbox': [x1, y1, x2, y2],
                })
    
    return annotations
