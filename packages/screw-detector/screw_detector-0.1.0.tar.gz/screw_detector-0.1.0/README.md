# Screw Detector

[![CI](https://github.com/3bsalam-1/Screw-Detector/workflows/CI/badge.svg)
[![PyPI](https://img.shields.io/pypi/v/screw-detector)
[![Python](https://img.shields.io/pypi/pyversions/screw-detector)
[![License](https://img.shields.io/pypi/l/screw-detector)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)

YOLOv8 + SAHI Detection Pipeline for Tiny Object Optimization

A high-precision object detection system for tiny objects (screws, bolts, washers) using YOLOv8 and Slicing Aided Hyper Inference (SAHI).

## Features

- **High-Precision Detection**: Optimized for detecting tiny objects (10-15px) in high-resolution images
- **SAHI Integration**: Native slicing logic to recover small objects during inference
- **Multiple Inference Strategies**: Baseline YOLOv8 and SAHI-enhanced detection
- **Easy-to-Use CLI**: Command-line tools for training, evaluation, and deployment
- **Production Ready**: Export models to ONNX and OpenVINO for edge deployment
- **Comprehensive Testing**: Full test suite with pytest

## Installation

### From PyPI

```bash
pip install screw-detector
```

### From Source

```bash
git clone https://github.com/3bsalam-1/Screw-Detector.git
cd Screw-Detector
pip install -e .
```

### Development Installation

```bash
pip install -e ".[dev]"
pre-commit install
```

## Quick Start

### Training a Model

```bash
# Train baseline model
screw-train --model yolov8s.pt --data data/configs/data.yaml --epochs 150

# Train on sliced dataset
screw-train --model yolov8s.pt --sliced-data --epochs 150
```

### Running Inference

```bash
# Baseline inference
screw-demo --model models/best.pt --input image.jpg --strategy baseline

# SAHI inference
screw-demo --model models/best.pt --input image.jpg --strategy sahi

# Compare strategies
screw-demo --model models/best.pt --input image.jpg --strategy compare
```

### Evaluating Models

```bash
# Evaluate with both strategies
screw-evaluate --model models/best.pt --data data/configs/data.yaml --strategy both --save-plots
```

### Exporting Models

```bash
# Export to ONNX
screw-export --model models/best.pt --format onnx

# Export to OpenVINO with INT8 quantization
screw-export --model models/best.pt --format openvino --int8

# Export to all formats
screw-export --model models/best.pt --format all
```

## Project Structure

```
screw-detector/
├── .github/              # CI/CD workflows and templates
├── data/                 # Dataset and configurations
│   ├── configs/          # Data configuration files
│   ├── raw/              # Original dataset
│   └── processed/        # Processed/sliced dataset
├── docs/                 # Documentation
├── notebooks/             # Jupyter notebooks
├── src/                  # Source code
│   ├── screw_detector/   # Package modules
│   └── scripts/          # CLI scripts
├── tests/                # Unit tests
├── models/               # Trained models
└── results/              # Training results
```

## Dataset

This project uses a custom-annotated dataset of bolts and washers.

- **Raw Data Source**: [Screw/Washer Dataset](https://www.kaggle.com/datasets/wjybuqi/screwwasher-dataset-for-small-object-detection) on Kaggle
- **Annotated Dataset**: [Bolts and Washers Dataset](https://www.kaggle.com/datasets/ahmedmohamedab/bolts-and-washers) on Kaggle

### Classes

- Bolt
- Bottle
- Washer

## Performance Benchmarks

Based on internal evaluation:

| Strategy | Precision | Recall | F1-Score | Avg Time (ms) |
|-----------|-----------|--------|-----------|----------------|
| Baseline (1280 Resize) | 88.5% | 90.7% | 89.6% | ~85ms |
| Optimized SAHI (1280) | 92.4% | 94.2% | 93.3% | ~450ms |
| Sliced SAHI (640) | 85.1% | 87.8% | 86.4% | ~220ms |

### Size-Based Recall Recovery

SAHI significantly outperforms standard inference for the most challenging objects:

- **Small (<15px)**: ~80.6% recovery
- **Medium (15-30px)**: ~94.0% recovery
- **Large (>30px)**: ~97.6% recovery

## Documentation

- [Architecture](docs/architecture.md) - System architecture overview
- [API Reference](docs/api.md) - Complete API documentation
- [Deployment Guide](docs/deployment.md) - Edge deployment instructions
- [Training Guide](docs/training.md) - Training procedures and best practices
- [Decision Log](docs/decision_log.md) - Architectural decisions

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/3bsalam-1/Screw-Detector.git
cd Screw-Detector

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linting
ruff check src/ tests/
black --check src/ tests/
mypy src/
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use this project in your research, please cite:

```bibtex
@software{screw_detector,
  title = {Screw Detector: YOLOv8 + SAHI Detection Pipeline for Tiny Object Optimization},
  author = {Screw Detector Team},
  year = {2024},
  url = {https://github.com/3bsalam-1/Screw-Detector}
}
```

## Acknowledgments

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) - Object detection framework
- [SAHI](https://github.com/obss/sahi) - Slicing Aided Hyper Inference library
- [Roboflow](https://roboflow.com/) - Dataset annotation platform

## Contact

- GitHub Issues: [https://github.com/3bsalam-1/Screw-Detector/issues](https://github.com/3bsalam-1/Screw-Detector/issues)
- Email: 3bsalam0@gmail.com
