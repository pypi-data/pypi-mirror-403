#!/usr/bin/env python3
"""
Dataset slicing script for Screw Detector.

This script provides a command-line interface for slicing
datasets into smaller tiles for training.
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from screw_detector.dataset import slice_yolo_dataset, DatasetStats, validate_dataset, print_validation_results


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Slice YOLO dataset into smaller tiles",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Data arguments
    parser.add_argument(
        "--data",
        type=str,
        default="data/configs/data.yaml",
        help="Path to data configuration file"
    )
    
    # Slicing arguments
    parser.add_argument(
        "--slice-size",
        type=int,
        default=640,
        help="Size of each slice (square)"
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=128,
        help="Overlap between adjacent slices in pixels"
    )
    parser.add_argument(
        "--visibility-threshold",
        type=float,
        default=0.3,
        help="Minimum visibility ratio for objects to be kept"
    )
    
    # Output arguments
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed/sliced",
        help="Output directory for sliced dataset"
    )
    
    # Validation arguments
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate dataset before slicing"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show dataset statistics"
    )
    
    return parser.parse_args()


def main():
    """Main slicing function."""
    args = parse_args()
    
    print("\n" + "="*60)
    print("SCREW DETECTOR - DATASET SLICING")
    print("="*60)
    print(f"Data config: {args.data}")
    print(f"Slice size: {args.slice_size}x{args.slice_size}")
    print(f"Overlap: {args.overlap}px")
    print(f"Visibility threshold: {args.visibility_threshold}")
    print(f"Output directory: {args.output_dir}")
    print("="*60)
    
    # Show dataset statistics if requested
    if args.stats:
        print("\nDataset Statistics:")
        print("-"*60)
        stats = DatasetStats(args.data)
        stats.print_stats()
    
    # Validate dataset if requested
    if args.validate:
        print("\nValidating dataset...")
        validation_results = validate_dataset(args.data)
        print_validation_results(validation_results)
        
        # Check for critical issues
        total_issues = sum(
            len(results['missing_labels']) + len(results['empty_labels']) + len(results['corrupt_images'])
            for results in validation_results.values()
        )
        
        if total_issues > 0:
            print(f"\nWarning: Found {total_issues} issues in the dataset.")
            response = input("Continue with slicing? (y/n): ")
            if response.lower() != 'y':
                print("Aborting.")
                return
    
    # Slice dataset
    print("\nStarting dataset slicing...")
    tile_counts = slice_yolo_dataset(
        data_yaml=args.data,
        out_dir=args.output_dir,
        slice_size=args.slice_size,
        overlap=args.overlap,
        visibility_threshold=args.visibility_threshold
    )
    
    # Print summary
    print("\n" + "="*60)
    print("SLICING SUMMARY")
    print("="*60)
    total_tiles = sum(tile_counts.values())
    print(f"Total tiles generated: {total_tiles}")
    for split, count in tile_counts.items():
        print(f"  {split.upper()}: {count} tiles")
    
    # Update data config for sliced dataset
    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    print("1. Update data/configs/sliced_data.yaml with the new paths")
    print("2. Train a model using the sliced dataset:")
    print(f"   python -m src.scripts.train --data data/configs/sliced_data.yaml --sliced-data")
    print("="*60)


if __name__ == "__main__":
    main()
