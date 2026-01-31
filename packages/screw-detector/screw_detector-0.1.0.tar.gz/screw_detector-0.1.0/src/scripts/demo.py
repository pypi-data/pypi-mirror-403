#!/usr/bin/env python3
"""
Demo script for Screw Detector.

This script provides an interactive demo for running inference
on images or video streams.
"""

import argparse
import sys
import cv2
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from screw_detector.config import SAHIConfig
from screw_detector.inference import BaselineInference, SAHIInference
from screw_detector.utils import visualize_predictions, visualize_comparison


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run inference demo for screw detection",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Input arguments
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to input image, video, or camera index (0, 1, ...)"
    )
    
    # Model arguments
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="Path to trained model file (.pt)"
    )
    
    # Inference arguments
    parser.add_argument(
        "--strategy",
        type=str,
        default="sahi",
        choices=["baseline", "sahi", "compare"],
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
        "--output",
        type=str,
        default=None,
        help="Path to save output image/video"
    )
    parser.add_argument(
        "--show",
        action="store_true",
        default=True,
        help="Show output in a window"
    )
    parser.add_argument(
        "--no-show",
        action="store_false",
        dest="show",
        help="Do not show output in a window"
    )
    
    return parser.parse_args()


def run_image_demo(args):
    """Run demo on a single image."""
    print("\n" + "="*60)
    print("IMAGE DEMO")
    print("="*60)
    print(f"Input: {args.input}")
    print(f"Model: {args.model}")
    print(f"Strategy: {args.strategy}")
    print("="*60)
    
    # Read image
    img = cv2.imread(args.input)
    if img is None:
        print(f"Error: Could not read image: {args.input}")
        return
    
    print(f"\nImage size: {img.shape[1]}x{img.shape[0]}")
    
    # Run inference based on strategy
    if args.strategy == "baseline":
        baseline = BaselineInference(args.model, confidence_threshold=args.confidence, device=args.device)
        detections = baseline.predict(args.input, imgsz=args.imgsz)
        annotated = visualize_predictions(args.input, detections, show_confidence=True)
        
        print(f"\nDetected {len(detections)} objects")
        for det in detections:
            print(f"  - {det['class_name']}: {det['confidence']:.2f}")
    
    elif args.strategy == "sahi":
        config = SAHIConfig(
            slice_height=args.slice_size,
            slice_width=args.slice_size,
            overlap_height_ratio=args.overlap / args.slice_size,
            overlap_width_ratio=args.overlap / args.slice_size,
            confidence_threshold=args.confidence,
            postprocess_match_threshold=args.nms_threshold
        )
        sahi = SAHIInference(args.model, config=config, device=args.device)
        detections = sahi.predict(args.input)
        annotated = visualize_predictions(args.input, detections, show_confidence=True)
        
        print(f"\nDetected {len(detections)} objects")
        for det in detections:
            print(f"  - {det['class_name']}: {det['confidence']:.2f}")
    
    elif args.strategy == "compare":
        baseline = BaselineInference(args.model, confidence_threshold=args.confidence, device=args.device)
        config = SAHIConfig(
            slice_height=args.slice_size,
            slice_width=args.slice_size,
            overlap_height_ratio=args.overlap / args.slice_size,
            overlap_width_ratio=args.overlap / args.slice_size,
            confidence_threshold=args.confidence,
            postprocess_match_threshold=args.nms_threshold
        )
        sahi = SAHIInference(args.model, config=config, device=args.device)
        
        baseline_detections = baseline.predict(args.input, imgsz=args.imgsz)
        sahi_detections = sahi.predict(args.input)
        
        annotated = visualize_comparison(args.input, baseline_detections, sahi_detections)
        
        print(f"\nBaseline detected: {len(baseline_detections)} objects")
        print(f"SAHI detected: {len(sahi_detections)} objects")
        print(f"Difference: {len(sahi_detections) - len(baseline_detections):+d}")
    
    # Save output
    if args.output:
        cv2.imwrite(args.output, annotated)
        print(f"\nOutput saved to: {args.output}")
    
    # Show output
    if args.show:
        cv2.imshow("Screw Detection Demo", annotated)
        print("\nPress any key to exit...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()


def run_video_demo(args):
    """Run demo on a video file or camera."""
    print("\n" + "="*60)
    print("VIDEO DEMO")
    print("="*60)
    print(f"Input: {args.input}")
    print(f"Model: {args.model}")
    print(f"Strategy: {args.strategy}")
    print("="*60)
    
    # Initialize video capture
    try:
        cap = cv2.VideoCapture(int(args.input))
        print(f"\nUsing camera {args.input}")
    except ValueError:
        cap = cv2.VideoCapture(args.input)
        print(f"\nUsing video file: {args.input}")
    
    if not cap.isOpened():
        print(f"Error: Could not open video source: {args.input}")
        return
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Video properties: {width}x{height} @ {fps:.2f} FPS")
    
    # Initialize inference
    if args.strategy == "baseline":
        baseline = BaselineInference(args.model, confidence_threshold=args.confidence, device=args.device)
        print(f"\nUsing baseline inference (imgsz={args.imgsz})")
    else:
        config = SAHIConfig(
            slice_height=args.slice_size,
            slice_width=args.slice_size,
            overlap_height_ratio=args.overlap / args.slice_size,
            overlap_width_ratio=args.overlap / args.slice_size,
            confidence_threshold=args.confidence,
            postprocess_match_threshold=args.nms_threshold
        )
        sahi = SAHIInference(args.model, config=config, device=args.device)
        print(f"\nUsing SAHI inference (slice={args.slice_size}, overlap={args.overlap})")
    
    # Initialize video writer
    writer = None
    if args.output:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(args.output, fourcc, fps, (width, height))
        print(f"Output will be saved to: {args.output}")
    
    # Process frames
    frame_count = 0
    print("\nProcessing video... Press 'q' to quit")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # Save frame temporarily
        temp_path = Path("temp_frame.jpg")
        cv2.imwrite(str(temp_path), frame)
        
        # Run inference
        if args.strategy == "baseline":
            detections = baseline.predict(temp_path, imgsz=args.imgsz)
        else:
            detections = sahi.predict(temp_path)
        
        # Visualize
        annotated = visualize_predictions(temp_path, detections, show_confidence=True)
        
        # Clean up temp file
        temp_path.unlink()
        
        # Write output
        if writer:
            writer.write(annotated)
        
        # Show output
        if args.show:
            cv2.imshow("Screw Detection Demo", annotated)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        # Print progress
        if frame_count % 30 == 0:
            print(f"Processed {frame_count} frames...")
    
    # Clean up
    cap.release()
    if writer:
        writer.release()
    cv2.destroyAllWindows()
    
    print(f"\nProcessed {frame_count} frames total")
    print("Demo complete!")


def main():
    """Main demo function."""
    args = parse_args()
    
    # Check if input is image or video
    input_path = Path(args.input)
    
    if input_path.exists() and input_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']:
        # Image input
        run_image_demo(args)
    else:
        # Video or camera input
        run_video_demo(args)


if __name__ == "__main__":
    main()
