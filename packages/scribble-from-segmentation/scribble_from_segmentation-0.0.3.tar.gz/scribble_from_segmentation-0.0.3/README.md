# Scribble From Segmentation

Generate scribble annotations from segmentation masks using advanced image processing techniques.

## Overview

This tool converts segmentation masks into scribble annotations by applying morphological operations and skeletonization. It's useful for creating weak supervision labels or simplifying segmentation annotations for training purposes.

The tool:

- Processes segmentation masks and extracts individual classes
- Automatically detects and skips background classes
- Applies morphological operations to refine class boundaries
- Skeletonizes regions to create scribble-like annotations
- Preserves the original color information for each class

## Installation

Install from PyPI:

```bash
pip install scribble-from-segmentation
```

Or install from source:

```bash
pip install -e .
```

## Usage

Use the command-line interface to process segmentation masks:

```bash
scribble-from-segmentation --input_dir /path/to/segmentation/masks --output_dir /path/to/output/scribbles
```

### Arguments

- `--input_dir` (required): Path to directory containing segmentation mask images
- `--output_dir` (required): Path to directory where scribble annotations will be saved

### Supported Image Formats

- PNG
- JPG/JPEG
- GIF
- BMP
- TIF

## Python API

You can also use the tool directly in your Python code:

```python
from scribble_from_segmentation import generate_scribbles_from_segmentations

# Generate scribbles from segmentation masks
generate_scribbles_from_segmentations(
    input_dir="/path/to/segmentation/masks",
    output_dir="/path/to/output/scribbles"
)
```

## Requirements

- Python >= 3.8
- numpy
- opencv-python
- Pillow
- scikit-image

## License

MIT License

## Author

Alex Senden
