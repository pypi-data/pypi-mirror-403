"""
Dataset utilities for Screw Detector.

This module provides functions for dataset statistics, validation,
and dataset slicing for training.
"""

import os
import cv2
import numpy as np
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from tqdm import tqdm


class DatasetStats:
    """Class for calculating and storing dataset statistics."""
    
    def __init__(self, data_yaml_path: str):
        """
        Initialize DatasetStats.
        
        Args:
            data_yaml_path: Path to the data YAML configuration file.
        """
        self.data_yaml_path = Path(data_yaml_path)
        self.data_cfg = self._load_data_config()
    
    def _load_data_config(self) -> Dict:
        """Load data configuration from YAML file."""
        with open(self.data_yaml_path, 'r') as f:
            return yaml.safe_load(f)
    
    def get_split_stats(self, split: str) -> Tuple[int, int, float]:
        """
        Get statistics for a specific dataset split.
        
        Args:
            split: Dataset split name (train, val, test).
            
        Returns:
            Tuple of (num_images, num_objects, avg_object_size_px).
        """
        if split not in self.data_cfg:
            raise ValueError(f"Split '{split}' not found in data config")
        
        img_dir = Path(self.data_cfg[split])
        return self._analyze_directory(img_dir)
    
    def get_all_stats(self) -> Dict[str, Tuple[int, int, float]]:
        """
        Get statistics for all dataset splits.
        
        Returns:
            Dictionary mapping split names to their statistics.
        """
        stats = {}
        for split in ['train', 'val', 'test']:
            if split in self.data_cfg:
                stats[split] = self.get_split_stats(split)
        return stats
    
    def _analyze_directory(self, img_dir: Path) -> Tuple[int, int, float]:
        """
        Analyze a directory of images and their labels.
        
        Args:
            img_dir: Path to the images directory.
            
        Returns:
            Tuple of (num_images, num_objects, avg_object_size_px).
        """
        lbl_dir = img_dir.parent / 'labels'
        images = list(img_dir.glob('*.jpg')) + list(img_dir.glob('*.png'))
        total_objs = 0
        sizes = []
        
        for img_p in tqdm(images, desc=f"Analyzing {img_dir.name}"):
            lbl_p = lbl_dir / (img_p.stem + '.txt')
            if not lbl_p.exists():
                continue
            
            img = cv2.imread(str(img_p))
            if img is None:
                continue
            
            h, w, _ = img.shape
            
            with open(lbl_p, 'r') as f:
                for line in f:
                    parts = list(map(float, line.split()))
                    coords = parts[1:]
                    
                    if len(coords) == 4:
                        # YOLO format: class x_center y_center width height
                        bw, bh = coords[2], coords[3]
                        sizes.append(max(bw * w, bh * h))
                    else:
                        # Polygon format
                        xs, ys = coords[0::2], coords[1::2]
                        sizes.append(max((max(xs)-min(xs))*w, (max(ys)-min(ys))*h))
                    
                    total_objs += 1
        
        avg_size = np.mean(sizes) if sizes else 0.0
        return len(images), total_objs, avg_size
    
    def print_stats(self) -> None:
        """Print dataset statistics in a formatted table."""
        print("\n" + "="*60)
        print("DATASET STATISTICS")
        print("="*60)
        print(f"Classes: {self.data_cfg.get('names', [])}")
        print(f"Number of classes: {self.data_cfg.get('nc', 0)}")
        print("-"*60)
        
        stats = self.get_all_stats()
        for split, (n_img, n_obj, avg_sz) in stats.items():
            print(f"{split.upper()}:")
            print(f"  Images: {n_img}")
            print(f"  Objects: {n_obj}")
            print(f"  Avg Object Size: {avg_sz:.1f}px")
            print("-"*60)


def slice_yolo_dataset(
    data_yaml: str,
    out_dir: str = "data/processed/sliced",
    slice_size: int = 640,
    overlap: int = 128,
    visibility_threshold: float = 0.3
) -> Dict[str, int]:
    """
    Slice YOLO dataset into smaller tiles for training.
    
    This function processes images by slicing them into overlapping tiles,
    preserving object annotations that meet the visibility threshold.
    
    Args:
        data_yaml: Path to the data YAML configuration file.
        out_dir: Output directory for sliced dataset.
        slice_size: Size of each slice (square).
        overlap: Overlap between adjacent slices in pixels.
        visibility_threshold: Minimum visibility ratio for objects to be kept.
        
    Returns:
        Dictionary with counts of generated tiles per split.
    """
    with open(data_yaml, 'r') as f:
        data_cfg = yaml.safe_load(f)
    
    print("\n" + "="*60)
    print("DATASET SLICING IN PROGRESS")
    print("="*60)
    print(f"Slice size: {slice_size}x{slice_size}")
    print(f"Overlap: {overlap}px")
    print(f"Visibility threshold: {visibility_threshold}")
    print("-"*60)
    
    tile_counts = {}
    
    for split in ['train', 'val', 'test']:
        if split not in data_cfg:
            continue
        
        img_dir = Path(data_cfg[split])
        lbl_dir = img_dir.parent / 'labels'
        
        out_img_path = Path(out_dir) / split / 'images'
        out_lbl_path = Path(out_dir) / split / 'labels'
        out_img_path.mkdir(parents=True, exist_ok=True)
        out_lbl_path.mkdir(parents=True, exist_ok=True)
        
        tile_count = 0
        
        for img_p in tqdm(img_dir.glob('*.jpg'), desc=f"Processing {split}"):
            img = cv2.imread(str(img_p))
            if img is None:
                continue
            
            h, w, _ = img.shape
            
            # Load ground truth boxes
            gt_boxes = []
            lbl_p = lbl_dir / (img_p.stem + '.txt')
            if lbl_p.exists():
                with open(lbl_p, 'r') as f:
                    for line in f:
                        parts = list(map(float, line.split()))
                        gt_boxes.append({'cls': int(parts[0]), 'bbox': parts[1:]})
            
            stride = slice_size - overlap
            
            for y in range(0, h, stride):
                for x in range(0, w, stride):
                    x1, y1 = min(x, w - slice_size), min(y, h - slice_size)
                    x2, y2 = x1 + slice_size, y1 + slice_size
                    
                    tile = img[y1:y2, x1:x2]
                    tile_labels = []
                    
                    for gt in gt_boxes:
                        # Convert normalized to absolute coordinates
                        bx, by, bw, bh = gt['bbox']
                        gx1, gy1 = (bx-bw/2)*w, (by-bh/2)*h
                        gx2, gy2 = (bx+bw/2)*w, (by+bh/2)*h
                        
                        # Calculate intersection
                        ix1, iy1 = max(gx1, x1), max(gy1, y1)
                        ix2, iy2 = min(gx2, x2), min(gy2, y2)
                        inter_w, inter_h = max(0, ix2-ix1), max(0, iy2-iy1)
                        inter_area = inter_w * inter_h
                        gt_area = (gx2-gx1)*(gy2-gy1)
                        
                        if (inter_area / (gt_area + 1e-9)) >= visibility_threshold:
                            # Convert to normalized coordinates relative to tile
                            rx = ((ix1+ix2)/2 - x1) / slice_size
                            ry = ((iy1+iy2)/2 - y1) / slice_size
                            rw, rh = inter_w / slice_size, inter_h / slice_size
                            tile_labels.append(f"{gt['cls']} {rx} {ry} {rw} {rh}")
                    
                    # Only save tiles that have at least one object
                    if tile_labels:
                        tile_name = f"{img_p.stem}_tile_{x1}_{y1}"
                        cv2.imwrite(str(out_img_path / (tile_name + ".jpg")), tile)
                        with open(out_lbl_path / (tile_name + ".txt"), 'w') as f:
                            for tl in tile_labels:
                                f.write(tl + "\n")
                        tile_count += 1
        
        tile_counts[split] = tile_count
        print(f"{split.upper()}: {tile_count} tiles generated")
    
    print("="*60)
    print("SLICING COMPLETE")
    print("="*60)
    
    return tile_counts


def validate_dataset(data_yaml: str) -> Dict[str, List[str]]:
    """
    Validate dataset integrity.
    
    Args:
        data_yaml: Path to the data YAML configuration file.
        
    Returns:
        Dictionary with validation results for each split.
    """
    with open(data_yaml, 'r') as f:
        data_cfg = yaml.safe_load(f)
    
    validation_results = {}
    
    for split in ['train', 'val', 'test']:
        if split not in data_cfg:
            continue
        
        img_dir = Path(data_cfg[split])
        lbl_dir = img_dir.parent / 'labels'
        
        missing_labels = []
        empty_labels = []
        corrupt_images = []
        
        for img_p in img_dir.glob('*.jpg'):
            lbl_p = lbl_dir / (img_p.stem + '.txt')
            
            # Check for missing labels
            if not lbl_p.exists():
                missing_labels.append(img_p.name)
                continue
            
            # Check for corrupt images
            img = cv2.imread(str(img_p))
            if img is None:
                corrupt_images.append(img_p.name)
                continue
            
            # Check for empty labels
            with open(lbl_p, 'r') as f:
                content = f.read().strip()
                if not content:
                    empty_labels.append(img_p.name)
        
        validation_results[split] = {
            'missing_labels': missing_labels,
            'empty_labels': empty_labels,
            'corrupt_images': corrupt_images,
        }
    
    return validation_results


def print_validation_results(validation_results: Dict[str, Dict[str, List[str]]]) -> None:
    """
    Print dataset validation results.
    
    Args:
        validation_results: Dictionary with validation results.
    """
    print("\n" + "="*60)
    print("DATASET VALIDATION RESULTS")
    print("="*60)
    
    for split, results in validation_results.items():
        print(f"\n{split.upper()}:")
        print(f"  Missing labels: {len(results['missing_labels'])}")
        if results['missing_labels']:
            for name in results['missing_labels'][:5]:
                print(f"    - {name}")
            if len(results['missing_labels']) > 5:
                print(f"    ... and {len(results['missing_labels']) - 5} more")
        
        print(f"  Empty labels: {len(results['empty_labels'])}")
        if results['empty_labels']:
            for name in results['empty_labels'][:5]:
                print(f"    - {name}")
            if len(results['empty_labels']) > 5:
                print(f"    ... and {len(results['empty_labels']) - 5} more")
        
        print(f"  Corrupt images: {len(results['corrupt_images'])}")
        if results['corrupt_images']:
            for name in results['corrupt_images'][:5]:
                print(f"    - {name}")
            if len(results['corrupt_images']) > 5:
                print(f"    ... and {len(results['corrupt_images']) - 5} more")
    
    print("\n" + "="*60)
