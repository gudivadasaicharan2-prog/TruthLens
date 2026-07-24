# TruthLens Training Infrastructure Architecture

## Overview

The TruthLens Training Infrastructure provides a unified, production-ready system for training AI content detection models. The architecture is designed to be modular, configurable, and extensible, supporting multiple model architectures and training strategies.

## Architecture Components

### 1. Dataset Layer (`dataset.py`)

**Purpose**: Efficient data loading from metadata.csv

**Key Features**:
- **Metadata-driven**: Reads from metadata.csv instead of scanning directories
- **Flexible Filtering**: Filter by split, label, generator, and source dataset
- **PyTorch Compatible**: Inherits from `torch.utils.data.Dataset`
- **Metadata Preservation**: Returns original metadata with each sample

**Class**: `TruthLensDataset`

```python
dataset = TruthLensDataset(
    metadata_path="TruthLensDataset/metadata.csv",
    dataset_dir="TruthLensDataset",
    split="train",
    label="ai",
    generator="midjourney",
    transform=train_transform
)
```

**Methods**:
- `__len__()`: Returns number of samples
- `__getitem__()`: Returns (image, label, metadata) tuple
- `get_label_counts()`: Count samples per label
- `get_generator_counts()`: Count samples per generator
- `get_split_counts()`: Count samples per split

### 2. DataLoader Layer (`dataloader.py`)

**Purpose**: Configurable data loading with balanced sampling

**Key Features**:
- **Balanced Sampling**: Ensures equal contribution from AI generators
- **Configurable Transforms**: Separate train/val transforms
- **Multiprocessing**: Parallel data loading
- **Pinned Memory**: Optimized GPU transfer
- **Deterministic Mode**: Reproducible training

**Classes**:
- `BalancedGeneratorSampler`: Custom sampler for balanced generator sampling
- `create_data_loaders()`: Factory function for creating train/val loaders

**Balanced Sampling Strategy**:
- Groups AI images by generator
- Samples equally from each generator per epoch
- Uses minimum generator count as baseline
- Supports custom samples per generator

```python
data_loaders = create_data_loaders(
    train_metadata="TruthLensDataset/metadata.csv",
    val_metadata="TruthLensDataset/metadata.csv",
    dataset_dir="TruthLensDataset",
    batch_size=32,
    num_workers=4,
    pin_memory=True,
    balanced_sampling=True,
    samples_per_generator=100
)
```

### 3. Model Layer (`models.py`)

**Purpose**: Unified interface for multiple model architectures

**Supported Architectures**:
- **EfficientNet-B4**: Efficient convolutional neural network (19M params)
- **ConvNeXt-Tiny**: Modern convolutional architecture (29M params)
- **ResNet-50**: Residual neural network (26M params)

**Class**: `TruthLensModel`

**Key Features**:
- **Unified Interface**: Same API for all architectures
- **Pretrained Weights**: Optional ImageNet initialization
- **Transfer Learning**: Freeze/unfreeze backbone
- **Custom Classifier**: Configurable dropout and output classes

```python
model = create_model(
    architecture="efficientnet_b4",
    num_classes=2,
    pretrained=True,
    dropout=0.3,
    freeze_backbone=False
)
```

**Methods**:
- `forward()`: Forward pass
- `freeze_backbone()`: Freeze backbone parameters
- `unfreeze_backbone()`: Unfreeze backbone parameters
- `get_feature_extractor()`: Get backbone without classifier
- `get_classifier()`: Get classifier head

### 4. Training Utilities (`utils.py`)

**Purpose**: Training helpers and utilities

**Classes**:
- `EarlyStopping`: Stop training when validation metric doesn't improve
- `CheckpointManager`: Save and load model checkpoints
- `AverageMeter`: Track running averages

**Functions**:
- `get_lr()`: Get current learning rate
- `set_seed()`: Set random seed for reproducibility
- `count_parameters()`: Count trainable parameters
- `get_device()`: Get best available device (CUDA/CPU)

**Early Stopping**:
- Configurable patience
- Minimum delta for improvement
- Support for min/max modes
- Automatic reset capability

**Checkpoint Management**:
- Save best model only
- Keep N most recent checkpoints
- Save optimizer and scheduler state
- Save training configuration
- Automatic cleanup of old checkpoints

### 5. Training Script (`train.py`)

**Purpose**: Main training orchestration

**Key Features**:
- **Configuration-driven**: YAML-based configuration
- **Mixed Precision**: Automatic mixed precision (AMP)
- **Learning Rate Scheduling**: Multiple scheduler options
- **TensorBoard Integration**: Real-time training visualization
- **Automatic Resume**: Resume from checkpoints
- **Early Stopping**: Automatic stopping on plateau

**Training Loop**:
1. Load configuration from YAML
2. Initialize model and data loaders
3. Set up optimizer and scheduler
4. Initialize checkpoint manager and early stopping
5. Training epochs:
   - Train one epoch with mixed precision
   - Validate on validation set
   - Update learning rate scheduler
   - Save checkpoint if best
   - Check early stopping
6. Close TensorBoard writer

**Supported Optimizers**:
- Adam
- AdamW
- SGD

**Supported Schedulers**:
- StepLR
- CosineAnnealingLR
- ReduceLROnPlateau

### 6. Validation Script (`validate.py`)

**Purpose**: Comprehensive model evaluation

**Metrics Computed**:
- **Overall**: Accuracy, Precision, Recall, F1, ROC-AUC
- **Confusion Matrix**: TP, TN, FP, FN counts
- **Per-Generator**: Metrics for each AI generator
- **Per-Dataset**: Metrics for each source dataset
- **Per-Label**: Metrics for real vs AI classes

**Output**:
- Console output with formatted metrics
- JSON file with detailed results
- Classification report per class

**Validation Process**:
1. Load model from checkpoint
2. Create validation dataset and loader
3. Run inference on validation set
4. Compute comprehensive metrics
5. Print and save results

## Data Flow

```
metadata.csv → TruthLensDataset → DataLoader → Model
                    ↓                    ↓
                Filtering         Balanced Sampling
                    ↓                    ↓
                Transforms         Batching
```

## Configuration System

**YAML-based Configuration**:
- Model architecture and parameters
- Data paths and preprocessing
- Training hyperparameters
- Optimizer and scheduler settings
- Checkpoint and logging settings

**Configuration Files**:
- `configs/train_config.yaml`: Training configuration
- `configs/val_config.yaml`: Validation configuration

## Key Design Decisions

### 1. Metadata-Driven Dataset
**Rationale**: Reading from metadata.csv is more efficient than directory scanning and enables flexible filtering.

**Benefits**:
- Faster dataset loading
- Easy filtering by any metadata field
- Consistent with dataset_manager output
- Supports complex queries

### 2. Balanced Generator Sampling
**Rationale**: AI generators often have imbalanced sample counts, leading to bias toward dominant generators.

**Benefits**:
- Equal representation of all generators
- Prevents model from favoring dominant generators
- Improves generalization across generators
- Configurable sampling strategy

### 3. Unified Model Interface
**Rationale**: Single interface simplifies experimentation and deployment.

**Benefits**:
- Easy model switching
- Consistent API across architectures
- Simplified configuration
- Easier maintenance

### 4. Configuration-Driven Training
**Rationale**: Separates configuration from code, enabling experimentation without code changes.

**Benefits**:
- No code changes for hyperparameter tuning
- Easy experiment tracking
- Reproducible experiments
- Version-controlled configurations

### 5. Comprehensive Validation
**Rationale**: Single accuracy metric insufficient for understanding model performance.

**Benefits**:
- Detailed performance analysis
- Identifies weak spots (specific generators/datasets)
- Better understanding of model behavior
- Informs training improvements

## Performance Considerations

### Memory Optimization
- **Pinned Memory**: Faster GPU transfer
- **Multiprocessing**: Parallel data loading
- **Mixed Precision**: Reduced memory usage, faster training
- **Gradient Accumulation**: Supports larger effective batch sizes

### Training Speed
- **Balanced Sampling**: Optimized with numpy
- **Data Augmentation**: GPU-accelerated transforms
- **Checkpoint Management**: Efficient state saving
- **Deterministic Mode**: Optional (impacts performance)

### Scalability
- **Distributed Training**: Ready for multi-GPU (future)
- **Large Datasets**: Streaming from metadata.csv
- **Multiple Models**: Easy to add new architectures
- **Extensible Metrics**: Simple to add new validation metrics

## Error Handling

### Dataset Errors
- Missing metadata file: Clear error message
- Invalid paths: Validation before loading
- Corrupted images: Skipped with warning

### Training Errors
- Out of memory: Clear error message
- Checkpoint loading: Graceful fallback
- NaN losses: Detected and reported

### Validation Errors
- Missing checkpoint: Clear error message
- Empty dataset: Warning and skip
- Metric calculation: Safe division with zero_division

## Extension Points

### Adding New Models
1. Add architecture to `models.py`
2. Update `get_model_info()` function
3. Add to configuration documentation

### Adding New Metrics
1. Add metric calculation to `validate.py`
2. Update `print_metrics()` function
3. Add to results dictionary

### Adding New Samplers
1. Create sampler class in `dataloader.py`
2. Add to `create_data_loaders()` function
3. Update configuration schema

### Adding New Schedulers
1. Add scheduler creation in `train.py`
2. Update configuration schema
3. Add documentation

## Dependencies

**Core**:
- PyTorch >= 1.10
- torchvision >= 0.11
- numpy
- Pillow

**Training**:
- PyYAML
- tensorboard
- scikit-learn

**Optional**:
- wandb (for experiment tracking)
- apex (for advanced mixed precision)

## File Structure

```
backend/app/training/
├── __init__.py
├── dataset.py              # PyTorch Dataset class
├── dataloader.py           # DataLoader and samplers
├── models.py               # Model architectures
├── utils.py                # Training utilities
├── train.py                # Training script
├── validate.py             # Validation script
├── configs/
│   ├── train_config.yaml   # Training configuration
│   └── val_config.yaml     # Validation configuration
├── ARCHITECTURE.md         # This file
├── TRAINING.md             # Training pipeline documentation
└── VALIDATION.md           # Validation pipeline documentation
```

## Best Practices

### Training
1. Always use a random seed for reproducibility
2. Monitor TensorBoard during training
3. Use early stopping to prevent overfitting
4. Save checkpoints regularly
5. Validate on held-out set

### Validation
1. Use multiple metrics, not just accuracy
2. Analyze per-generator performance
3. Check confusion matrix for error patterns
4. Compare against baseline models
5. Validate on diverse datasets

### Configuration
1. Keep configurations version-controlled
2. Document configuration changes
3. Use descriptive names for experiments
4. Separate training and validation configs
5. Validate configuration before training

## Future Enhancements

### Planned
- [ ] Distributed training support
- [ ] Advanced data augmentation (AutoAugment, RandAugment)
- [ ] Model ensembling
- [ ] Hyperparameter optimization (Optuna)
- [ ] Automated MLflow integration

### Potential
- [ ] ONNX export for deployment
- [ ] Model quantization
- [ ] Knowledge distillation
- [ ] Neural architecture search
- [ ] Custom loss functions
