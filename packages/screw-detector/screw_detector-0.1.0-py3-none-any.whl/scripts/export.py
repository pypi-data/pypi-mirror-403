#!/usr/bin/env python3
"""
Export script for Screw Detector.

This script provides a command-line interface for exporting
YOLOv8 models to various formats for deployment.
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from screw_detector.config import ExportConfig
from screw_detector.models import ModelExporter, get_model_size


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Export YOLOv8 model for deployment",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Model arguments
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="Path to trained model file (.pt)"
    )
    
    # Export format arguments
    parser.add_argument(
        "--format",
        type=str,
        default="onnx",
        choices=["onnx", "openvino", "torchscript", "all"],
        help="Export format"
    )
    
    # ONNX arguments
    parser.add_argument(
        "--half",
        action="store_true",
        help="Export in FP16 (half precision)"
    )
    parser.add_argument(
        "--simplify",
        action="store_true",
        default=True,
        help="Simplify the ONNX model"
    )
    parser.add_argument(
        "--no-simplify",
        action="store_false",
        dest="simplify",
        help="Do not simplify the ONNX model"
    )
    parser.add_argument(
        "--dynamic",
        action="store_true",
        help="Use dynamic axes for ONNX export"
    )
    
    # OpenVINO arguments
    parser.add_argument(
        "--int8",
        action="store_true",
        help="Export in INT8 (quantized) for OpenVINO"
    )
    
    # Output arguments
    parser.add_argument(
        "--output-dir",
        type=str,
        default="models/exported",
        help="Directory to save exported models"
    )
    
    return parser.parse_args()


def main():
    """Main export function."""
    args = parse_args()
    
    print("\n" + "="*60)
    print("SCREW DETECTOR - MODEL EXPORT")
    print("="*60)
    print(f"Model: {args.model}")
    print(f"Format: {args.format}")
    print("="*60)
    
    # Show original model size
    original_size = get_model_size(args.model)
    print(f"\nOriginal model size:")
    print(f"  {original_size['bytes']:,} bytes")
    print(f"  {original_size['kb']:.2f} KB")
    print(f"  {original_size['mb']:.2f} MB")
    
    # Create exporter
    config = ExportConfig(
        format=args.format if args.format != "all" else "onnx",
        half=args.half,
        simplify=args.simplify,
        dynamic=args.dynamic,
        int8=args.int8
    )
    
    exporter = ModelExporter(args.model, config=config)
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Export based on format
    if args.format == "all":
        print("\nExporting to all formats...")
        exports = exporter.export_all(output_dir)
        
        print("\n" + "="*60)
        print("EXPORT SUMMARY")
        print("="*60)
        for format_name, export_path in exports.items():
            if export_path.is_dir():
                # OpenVINO exports to a directory
                size = sum(f.stat().st_size for f in export_path.rglob('*') if f.is_file())
            else:
                size = export_path.stat().st_size
            
            print(f"\n{format_name.upper()}:")
            print(f"  Path: {export_path}")
            print(f"  Size: {size:,} bytes ({size / (1024*1024):.2f} MB)")
    
    elif args.format == "onnx":
        print("\nExporting to ONNX...")
        export_path = exporter.export_onnx(
            half=args.half,
            simplify=args.simplify,
            dynamic=args.dynamic
        )
        
        # Show exported model size
        exported_size = get_model_size(export_path)
        print(f"\nExported model size:")
        print(f"  {exported_size['bytes']:,} bytes")
        print(f"  {exported_size['kb']:.2f} KB")
        print(f"  {exported_size['mb']:.2f} MB")
        
        # Calculate size reduction
        reduction = (1 - exported_size['bytes'] / original_size['bytes']) * 100
        print(f"\nSize reduction: {reduction:.2f}%")
    
    elif args.format == "openvino":
        print("\nExporting to OpenVINO...")
        export_path = exporter.export_openvino(
            half=args.half,
            int8=args.int8
        )
        
        # Show exported model size
        if export_path.is_dir():
            size = sum(f.stat().st_size for f in export_path.rglob('*') if f.is_file())
        else:
            size = export_path.stat().st_size
        
        print(f"\nExported model size:")
        print(f"  {size:,} bytes ({size / (1024*1024):.2f} MB)")
        
        # Calculate size reduction
        reduction = (1 - size / original_size['bytes']) * 100
        print(f"\nSize reduction: {reduction:.2f}%")
    
    elif args.format == "torchscript":
        print("\nExporting to TorchScript...")
        export_path = exporter.export_torchscript()
        
        # Show exported model size
        exported_size = get_model_size(export_path)
        print(f"\nExported model size:")
        print(f"  {exported_size['bytes']:,} bytes")
        print(f"  {exported_size['kb']:.2f} KB")
        print(f"  {exported_size['mb']:.2f} MB")
        
        # Calculate size reduction
        reduction = (1 - exported_size['bytes'] / original_size['bytes']) * 100
        print(f"\nSize reduction: {reduction:.2f}%")
    
    print("\n" + "="*60)
    print("EXPORT COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
