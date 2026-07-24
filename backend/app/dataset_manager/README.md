# TruthLens Dataset Manager

Automatic dataset management for TruthLens AI detection models.

## Overview

The Dataset Manager provides a complete solution for downloading, organizing, and preparing datasets for AI content detection. It supports multiple popular datasets and automates the entire pipeline from download to benchmark preparation.

## Features

- **Multi-Dataset Support**: Download and organize FFHQ, COCO, Open Images, GenImage, FaceForensics++, and DFDC
- **Automatic Organization**: Structures datasets into TruthLens format with proper categorization
- **Image Processing**: Automatic resizing to configurable dimensions (default: 512x512)
- **Duplicate Detection**: Removes duplicate images using MD5 and perceptual hashing
- **Corruption Detection**: Identifies and removes corrupted image files
- **Statistics Generation**: Comprehensive dataset statistics and reports
- **Benchmark Building**: Creates balanced benchmark datasets for model evaluation
- **CLI Interface**: Easy-to-use command-line interface for all operations

## Installation

### Requirements

```bash
pip install pillow imagehash tqdm requests
```

### Optional Dependencies

For perceptual hashing:
```bash
pip install imagehash
```

## Dataset Structure

The Dataset Manager organizes datasets into the following structure:

```
TruthLensDataset/
├── images/
│   ├── real/
│   │   ├── portrait/
│   │   ├── landscape/
│   │   ├── object/
│   │   ├── document/
│   │   └── screenshot/
│   └── ai/
│       ├── midjourney/
│       ├── sdxl/
│       ├── adm/
│       └── glide/
└── videos/
    ├── real/
    │   └── portrait/
    └── ai/
        └── portrait/
```

## Usage

### Command Line Interface

#### Download a Specific Dataset

```bash
python -m app.dataset_manager.cli --dataset genimage
```

#### Download All Datasets

```bash
python -m app.dataset_manager.cli --all
```

#### Organize Imported Dataset

```bash
python -m app.dataset_manager.cli --organize /path/to/images --content-type real --category portrait
```

#### Organize Tiny GenImage Dataset

Automatically organize the extracted Tiny GenImage dataset into unified TruthLens structure:

```bash
python -m app.dataset_manager.cli --organize-tiny-genimage /path/to/tiny-genimage
```

Force overwrite existing data:

```bash
python -m app.dataset_manager.cli --organize-tiny-genimage /path/to/tiny-genimage --force
```

This command:
- Automatically detects all generator folders (e.g., imagenet_ai_0419_biggan, imagenet_glide)
- Preserves existing train/val splits
- Copies images to unified structure:
  - `TruthLensDataset/images/real/train` and `TruthLensDataset/images/real/val`
  - `TruthLensDataset/images/ai/<generator>/train` and `TruthLensDataset/images/ai/<generator>/val`
- Generates `metadata.csv` with file_path, label, generator, split, and source_dataset
- Detects and skips duplicate images using MD5 hashing
- Validates image integrity and skips corrupted files
- **Validates target directory to prevent accidental overwrites** (use --force to override)
- **Validates generated metadata.csv for completeness and correctness**
- Produces a summary report with counts per generator and split totals

#### Organize CIFAKE Dataset

Automatically organize the CIFAKE dataset into unified TruthLens structure:

```bash
python -m app.dataset_manager.cli --organize-cifake /path/to/cifake
```

Force overwrite existing data:

```bash
python -m app.dataset_manager.cli --organize-cifake /path/to/cifake --force
```

This command:
- Maps CIFAKE structure to TruthLens format:
  - `train/FAKE` → `images/ai/cifake/train`
  - `train/REAL` → `images/real/train`
  - `test/FAKE` → `images/ai/cifake/val`
  - `test/REAL` → `images/real/val`
- Sets generator to "cifake" for AI images
- Sets source_dataset to "cifake"
- Generates `metadata.csv` with proper TruthLens format
- Detects and skips duplicate images using MD5 hashing
- Validates image integrity and skips corrupted files
- **Validates target directory to prevent accidental overwrites** (use --force to override)
- **Validates generated metadata.csv for completeness and correctness**
- Produces a summary report with counts per split and label

#### Clean Dataset

```bash
python -m app.dataset_manager.cli --clean
```

#### Generate Statistics

```bash
python -m app.dataset_manager.cli --stats
```

#### Generate Reports

```bash
python -m app.dataset_manager.cli --report --report-dir reports
```

#### Build Benchmark Dataset

```bash
python -m app.dataset_manager.cli --build-benchmark --samples 100 --split-ratio 0.8
```

#### Full Pipeline

```bash
python -m app.dataset_manager.cli --full-pipeline --datasets ffhq genimage
```

### Python API

#### Basic Usage

```python
from app.dataset_manager import DatasetManager

# Initialize manager
manager = DatasetManager(base_dir="TruthLensDataset", resize_size=(512, 512))

# Create directory structure
manager.setup_structure()

# Download dataset
result = manager.download_dataset("genimage")
print(result)

# Organize imported dataset
result = manager.organize_imported_dataset(
    source_dir="/path/to/images",
    content_type="ai",
    generator="midjourney"
)
print(result)

# Clean dataset
result = manager.clean_dataset()
print(result)

# Generate statistics
stats = manager.get_statistics()
print(stats)

# Generate reports
reports = manager.generate_report(output_dir="reports")
print(reports)

# Generate benchmark CSV
benchmark_csv = manager.generate_benchmark_csv()
print(benchmark_csv)
```

#### Full Pipeline

```python
from app.dataset_manager import DatasetManager

manager = DatasetManager()

# Run complete pipeline
results = manager.full_pipeline(datasets=["ffhq", "genimage"])
print(results)
```

#### Benchmark Builder

```python
from app.dataset_manager.benchmark_builder import BenchmarkBuilder

builder = BenchmarkBuilder(dataset_dir="TruthLensDataset", output_dir="benchmark")

# Build benchmark with all categories
stats = builder.build_benchmark(
    categories=None,  # All categories
    samples_per_category=100,
    split_ratio=0.8
)
print(stats)

# Build benchmark for specific categories
stats = builder.build_benchmark(
    categories=["real_portrait", "ai_midjourney"],
    samples_per_category=50,
    split_ratio=0.8
)
print(stats)

# Get category distribution
distribution = builder.get_category_distribution()
print(distribution)
```

## Supported Datasets

### Real Images

1. **FFHQ (Flickr-Faces-HQ)**
   - 70,000 high-quality face images
   - 1024x1024 resolution
   - Category: portrait
   - Content type: real

2. **COCO (Common Objects in Context)**
   - 330K images (2017)
   - Various object categories
   - Category: mixed
   - Content type: real

3. **Open Images**
   - 9M images (v6)
   - Image-level labels
   - Category: mixed
   - Content type: real

### AI-Generated Images

4. **GenImage**
   - ~100K AI-generated images
   - Multiple generators
   - Category: mixed
   - Content type: ai
   - Generators: midjourney, sdxl, adm, glide

5. **Tiny GenImage**
   - Subset of GenImage dataset
   - Multiple generators with train/val splits
   - Category: mixed
   - Content type: ai
   - Generators: biggan, glide, adm, vqdm, diffusion, midjourney, sdxl, stable_diffusion, dalle

6. **CIFAKE**
   - 120K images (60K real, 60K AI)
   - Train/test split
   - Category: mixed
   - Content type: ai
   - Generator: cifake
   - Automatic organization support for unified structure

### Deepfake Videos

7. **FaceForensics++**
   - 1,000 original videos
   - 4,000 manipulated videos
   - Category: portrait
   - Content type: ai

8. **DFDC (DeepFake Detection Challenge)**
   - 100K+ videos
   - Kaggle challenge dataset
   - Category: portrait
   - Content type: ai

## Dataset Download Instructions

Most datasets require manual download from their official sources due to licensing agreements. The Dataset Manager provides instructions and creates the necessary directory structure.

### FFHQ
1. Visit https://github.com/NVlabs/ffhq-dataset
2. Download the dataset files
3. Extract to `TruthLensDataset/ffhq/images/real/portrait/`

### COCO
1. Visit https://cocodataset.org/#download
2. Download the 2017 Train/Val images
3. Extract to `TruthLensDataset/coco/images/real/`

### Open Images
1. Visit https://storage.googleapis.com/openimages/web/index.html
2. Download the training/validation sets
3. Extract to `TruthLensDataset/openimages/images/real/`

### GenImage
1. Visit https://github.com/LAION-AI/GenImage
2. Download the dataset files
3. Extract to `TruthLensDataset/genimage/images/ai/`

### FaceForensics++
1. Visit https://github.com/ondyari/FaceForensics
2. Download the dataset files
3. Extract to `TruthLensDataset/faceforensics/videos/ai/portrait/`

### DFDC
1. Visit https://www.kaggle.com/c/deepfake-detection-challenge
2. Accept the competition rules
3. Download the dataset files
4. Extract to `TruthLensDataset/dfdc/videos/ai/portrait/`

## Output Files

### benchmark.csv
Generated CSV file with the following fields:
- `filename`: Image filename
- `label`: Ground truth label (real/ai)
- `content_type`: Content type (real/ai)
- `generator`: AI generator (for AI images)
- `source_dataset`: Original dataset name

### dataset_report.json
JSON report containing:
- Total file count
- Files by content type
- Files by category
- Files by generator
- Generation timestamp

### dataset_report.csv
CSV report with the same information as JSON report.

## Image Processing

### Resizing
Images are automatically resized to the target size (default: 512x512) using high-quality LANCZOS resampling. The resize size can be configured:

```bash
python -m app.dataset_manager.cli --resize-size 1024 1024 --dataset genimage
```

### Duplicate Detection
Two methods are used for duplicate detection:
1. **MD5 Hash**: Detects exact duplicates
2. **Perceptual Hash**: Detects near-duplicates using image similarity

Duplicates are automatically removed, keeping the first occurrence.

### Corruption Detection
Corrupted files are detected by:
- Checking file existence and size
- Verifying image can be opened
- Loading and validating image data

Corrupted files are automatically removed.

## Statistics

The Dataset Manager generates comprehensive statistics including:
- Total number of files
- Distribution by content type (real/ai)
- Distribution by category (for real images)
- Distribution by generator (for AI images)
- Files removed during cleaning (duplicates, corrupted)

## Benchmark Building

The Benchmark Builder creates balanced datasets for model evaluation:

### Categories
- `real_portrait`: Real portrait images
- `real_landscape`: Real landscape images
- `real_object`: Real object images
- `real_document`: Real document images
- `real_screenshot`: Real screenshot images
- `ai_midjourney`: Midjourney-generated images
- `ai_sdxl`: SDXL-generated images
- `ai_adm`: ADM-generated images
- `ai_glide`: GLIDE-generated images

### Split
- Train/validation split (default: 80/20)
- Configurable via `--split-ratio`

### Output
- `train.csv`: Training set metadata
- `val.csv`: Validation set metadata
- `train/`: Training set images
- `val/`: Validation set images

## Advanced Usage

### Custom Resize Size

```python
manager = DatasetManager(resize_size=(1024, 1024))
```

### Custom Output Directory

```bash
python -m app.dataset_manager.cli --base-dir /custom/path --dataset genimage
```

### Organize Specific Categories

```python
manager.organize_imported_dataset(
    source_dir="/path/to/images",
    content_type="real",
    category="portrait"
)
```

### Organize Tiny GenImage Dataset

```python
from app.dataset_manager.tiny_genimage_organizer import TinyGenImageOrganizer

organizer = TinyGenImageOrganizer(
    source_dir="/path/to/tiny-genimage",
    target_dir="TruthLensDataset",
    force=False  # Set to True to overwrite existing data
)

# Run complete organization
result = organizer.organize()
print(result)

# Access validation results
print("Target validation:", result["target_validation"])
print("Metadata validation:", result["metadata_validation"])
```

### Organize CIFAKE Dataset

```python
from app.dataset_manager.handlers import CIFAKEHandler

handler = CIFAKEHandler(
    source_dir="/path/to/cifake",
    target_dir="TruthLensDataset",
    force=False  # Set to True to overwrite existing data
)

# Run complete organization
result = handler.organize()
print(result)

# Access validation results
print("Target validation:", result["target_validation"])
print("Metadata validation:", result["metadata_validation"])
```

### Clean Specific Directory

```bash
python -m app.dataset_manager.cli --clean --clean-dir /path/to/directory
```

## Troubleshooting

### Import Errors
Ensure you're running from the backend directory:
```bash
cd backend
python -m app.dataset_manager.cli --dataset genimage
```

### Missing Dependencies
Install required packages:
```bash
pip install pillow imagehash tqdm requests
```

### Dataset Download Issues
Most datasets require manual download. Follow the instructions provided by the downloader for each dataset.

### Memory Issues
For large datasets, process in smaller batches or increase system memory.

### Target Directory Validation
The Tiny GenImage organizer now validates the target directory before organization:
- If the target directory contains existing images, the organization will fail
- Use the `--force` flag to overwrite existing data
- This prevents accidental data loss

### Metadata Validation
After organization, the metadata.csv file is automatically validated:
- Checks that all referenced files exist
- Validates labels (real/ai) and splits (train/val)
- Detects duplicate entries
- Results are included in the organization output

### Filesystem Errors
Enhanced error handling for filesystem operations:
- Permission errors are clearly reported
- Disk space errors are detected and reported
- Invalid paths are caught and reported with context

## CLI Options Reference

| Option | Description | Default |
|--------|-------------|---------|
| `--dataset` | Dataset to download | - |
| `--all` | Download all datasets | False |
| `--organize` | Source directory to organize | - |
| `--organize-tiny-genimage` | Path to Tiny GenImage dataset | - |
| `--organize-cifake` | Path to CIFAKE dataset | - |
| `--force` | Force overwrite existing data | False |
| `--content-type` | Content type (real/ai) | - |
| `--category` | Category for real images | - |
| `--generator` | Generator for AI images | - |
| `--clean` | Clean dataset | False |
| `--clean-dir` | Directory to clean | TruthLensDataset |
| `--stats` | Generate statistics | False |
| `--report` | Generate reports | False |
| `--report-dir` | Report output directory | reports |
| `--build-benchmark` | Build benchmark | False |
| `--benchmark-categories` | Categories for benchmark | All |
| `--samples` | Samples per category | 100 |
| `--split-ratio` | Train/val split ratio | 0.8 |
| `--full-pipeline` | Run full pipeline | False |
| `--datasets` | Datasets for pipeline | All |
| `--base-dir` | Base directory | TruthLensDataset |
| `--resize-size` | Target resize size | 512 512 |
| `--output` | Output file path | - |

## Module Structure

```
app/dataset_manager/
├── __init__.py
├── dataset_manager.py      # Main dataset manager
├── benchmark_builder.py     # Benchmark dataset builder
├── tiny_genimage_organizer.py  # Tiny GenImage organizer (backward compatibility wrapper)
├── cli.py                  # Command-line interface
├── handlers/               # Dataset-specific organization handlers
│   ├── __init__.py
│   ├── base_handler.py     # Abstract base class for dataset handlers
│   ├── tiny_genimage_handler.py  # Tiny GenImage dataset handler
│   └── cifake_handler.py   # CIFAKE dataset handler
├── downloaders/
│   ├── __init__.py
│   ├── base_downloader.py   # Base downloader class
│   ├── ffhq_downloader.py   # FFHQ downloader
│   ├── coco_downloader.py   # COCO downloader
│   ├── openimages_downloader.py  # Open Images downloader
│   ├── genimage_downloader.py    # GenImage downloader
│   ├── faceforensics_downloader.py  # FaceForensics++ downloader
│   └── dfdc_downloader.py   # DFDC downloader
└── organizers/
    ├── __init__.py
    ├── image_processor.py   # Image processing (resize, etc.)
    ├── duplicate_detector.py    # Duplicate detection
    ├── corruption_detector.py   # Corruption detection
    └── dataset_organizer.py     # Dataset organization
```

## Notes

- This is a **dataset preparation utility** and does not modify production inference code
- Most datasets require manual download due to licensing
- Image resizing uses high-quality LANCZOS resampling
- Duplicate detection uses both MD5 and perceptual hashing for comprehensive coverage
- All operations are non-destructive to original datasets (copies are made)

## License

This dataset manager is part of TruthLens and follows the same license terms.

## Support

For issues or questions, refer to the main TruthLens documentation or create an issue in the project repository.
