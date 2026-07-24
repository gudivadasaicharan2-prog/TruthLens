# TruthLens Training Pipeline Documentation

## Overview

The TruthLens training pipeline provides a complete, production-ready system for training AI content detection models. This document covers the training process, configuration, and best practices.

## Prerequisites

### Required Software
- Python 3.8+
- PyTorch 1.10+
- torchvision 0.11+
- CUDA 11.0+ (for GPU training)

### Required Python Packages
```bash
pip install torch torchvision
pip install pyyaml tensorboard
pip install scikit-learn pillow numpy
```

### Dataset Preparation
1. Organize your dataset using the dataset_manager
2. Ensure metadata.csv exists in the dataset directory
3. Verify train/val splits are present
4. Check image integrity

## Quick Start

### 1. Prepare Configuration

Edit `configs/train_config.yaml`:

```yaml
model:
  architecture: efficientnet_b4
  num_classes: 2
  pretrained: true
  dropout: 0.3

data:
  train_metadata: TruthLensDataset/metadata.csv
  val_metadata: TruthLensDataset/metadata.csv
  dataset_dir: TruthLensDataset
  image_size: 224
  batch_size: 32
  balanced_sampling: true

training:
  epochs: 50
  optimizer:
    type: adamw
    lr: 0.0001
  mixed_precision: true
  use_tensorboard: true
```

### 2. Start Training

```bash
cd backend
python -m app.training.train --config app/training/configs/train_config.yaml
```

### 3. Monitor Training

```bash
tensorboard --logdir logs
```

### 4. Resume Training (if needed)

```bash
python -m app.training.train --config app/training/configs/train_config.yaml --resume
```

## Detailed Training Process

### Phase 1: Initialization

**Steps**:
1. Load configuration from YAML file
2. Set random seed for reproducibility
3. Detect available device (CUDA/CPU)
4. Initialize model architecture
5. Load pretrained weights (if configured)
6. Create data loaders with transforms
7. Initialize optimizer and scheduler
8. Set up checkpoint manager
9. Configure early stopping
10. Initialize TensorBoard writer

**Output**:
- Model loaded on device
- Data loaders ready
- Optimizer configured
- Checkpoint directory created
- TensorBoard logging initialized

### Phase 2: Training Loop

**Per Epoch**:
1. **Training Phase**:
   - Set model to train mode
   - Iterate over training batches
   - Apply mixed precision (if enabled)
   - Forward pass
   - Compute loss
   - Backward pass
   - Optimizer step
   - Update metrics
   - Log to TensorBoard

2. **Validation Phase**:
   - Set model to eval mode
   - Iterate over validation batches
   - Forward pass (no gradient)
   - Compute loss and accuracy
   - Store predictions for analysis
   - Log to TensorBoard

3. **Post-Validation**:
   - Update learning rate scheduler
   - Save checkpoint (if best)
   - Check early stopping
   - Print epoch summary

**Termination Conditions**:
- All epochs completed
- Early stopping triggered
- Manual interruption (Ctrl+C)

### Phase 3: Completion

**Steps**:
1. Close TensorBoard writer
2. Print final statistics
3. Save best model path
4. Generate training summary

## Configuration Guide

### Model Configuration

```yaml
model:
  architecture: efficientnet_b4  # Model architecture
  num_classes: 2                 # Number of output classes
  pretrained: true               # Use ImageNet weights
  dropout: 0.3                   # Dropout probability
  freeze_backbone: false          # Freeze backbone weights
```

**Architecture Options**:
- `efficientnet_b4`: Efficient, good balance of speed/accuracy
- `convnext_tiny`: Modern architecture, higher accuracy
- `resnet50`: Classic architecture, widely used

**Recommendations**:
- Use `pretrained: true` for better convergence
- Set `freeze_backbone: true` for small datasets
- Adjust `dropout` based on overfitting

### Data Configuration

```yaml
data:
  train_metadata: TruthLensDataset/metadata.csv
  val_metadata: TruthLensDataset/metadata.csv
  dataset_dir: TruthLensDataset
  image_size: 224
  batch_size: 32
  num_workers: 4
  pin_memory: true
  augment: true
  balanced_sampling: true
  samples_per_generator: null
```

**Parameters**:
- `image_size`: Input size (224 for most models)
- `batch_size`: Larger = faster but more memory
- `num_workers`: Parallel data loading (4-8 recommended)
- `pin_memory`: Faster GPU transfer (keep true)
- `augment`: Data augmentation for training
- `balanced_sampling`: Equal generator representation
- `samples_per_generator`: Custom sampling count

**Recommendations**:
- Start with `batch_size: 32` on GPU
- Set `num_workers` to CPU core count
- Enable `balanced_sampling` for AI generators
- Use `augment: true` for better generalization

### Training Configuration

```yaml
training:
  epochs: 50
  seed: 42
  deterministic: false
  
  optimizer:
    type: adamw
    lr: 0.0001
    weight_decay: 0.01
  
  scheduler:
    type: cosine
    T_max: 50
  
  mixed_precision: true
  
  checkpoint_dir: checkpoints
  save_best_only: true
  max_checkpoints: 3
  resume: false
  
  early_stopping:
    enabled: true
    patience: 7
    min_delta: 0.001
  
  use_tensorboard: true
  log_dir: logs
```

**Optimizer Options**:
- `adamw`: Recommended for most cases
- `adam`: Good alternative
- `sgd`: Requires careful tuning

**Scheduler Options**:
- `cosine`: Smooth decay, recommended
- `step`: Step-wise decay
- `plateau`: Reduce on plateau
- `null`: No scheduling

**Learning Rate Guidelines**:
- AdamW: 1e-4 to 1e-3
- Adam: 1e-4 to 1e-3
- SGD: 1e-2 to 1e-1 (with momentum)

**Early Stopping**:
- `patience`: Epochs to wait (5-10 recommended)
- `min_delta`: Minimum improvement (0.001)

## Advanced Features

### Mixed Precision Training

**Benefits**:
- 2x faster training on modern GPUs
- Reduced memory usage
- Minimal accuracy loss

**Usage**:
```yaml
training:
  mixed_precision: true
```

**Requirements**:
- NVIDIA GPU with Tensor Cores (Volta, Turing, Ampere)
- PyTorch >= 1.6

### Balanced Generator Sampling

**Purpose**: Ensure equal representation of AI generators

**How It Works**:
1. Groups AI images by generator
2. Counts samples per generator
3. Uses minimum count as baseline
4. Samples equally from each generator

**Configuration**:
```yaml
data:
  balanced_sampling: true
  samples_per_generator: null  # Auto-detect
```

**Custom Sampling**:
```yaml
data:
  balanced_sampling: true
  samples_per_generator: 100  # Fixed count
```

### Transfer Learning

**Freeze Backbone**:
```yaml
model:
  freeze_backbone: true
```

**Unfreeze Later**:
```python
# In custom training loop
model.unfreeze_backbone()
```

**When to Use**:
- Small datasets (< 10K samples)
- Limited compute resources
- Fine-tuning from similar domain

### Learning Rate Scheduling

**Cosine Annealing**:
```yaml
scheduler:
  type: cosine
  T_max: 50  # Usually = epochs
```

**Step Decay**:
```yaml
scheduler:
  type: step
  step_size: 10
  gamma: 0.1
```

**Plateau**:
```yaml
scheduler:
  type: plateau
  factor: 0.1
  patience: 5
```

### Checkpoint Management

**Save Best Only**:
```yaml
training:
  save_best_only: true
  max_checkpoints: 3
```

**Save All**:
```yaml
training:
  save_best_only: false
  max_checkpoints: 5
```

**Checkpoint Contents**:
- Model state dict
- Optimizer state dict
- Scheduler state dict
- Epoch number
- Validation score
- Training configuration

## Monitoring and Debugging

### TensorBoard

**Start TensorBoard**:
```bash
tensorboard --logdir logs --port 6006
```

**View Metrics**:
- Training loss and accuracy
- Validation loss and accuracy
- Learning rate over time
- Batch-level metrics

**Common Issues**:
- Loss not decreasing: Check learning rate
- Overfitting: Add augmentation, increase dropout
- Underfitting: Increase model capacity, train longer

### Common Training Issues

**Out of Memory**:
- Reduce batch size
- Use gradient accumulation
- Use smaller model
- Enable mixed precision

**Slow Training**:
- Increase num_workers
- Use mixed precision
- Check GPU utilization
- Reduce image size

**Poor Convergence**:
- Check learning rate
- Verify data loading
- Ensure correct labels
- Check for data imbalance

**NaN Loss**:
- Reduce learning rate
- Check for corrupted data
- Verify loss function
- Add gradient clipping

## Best Practices

### Before Training
1. Validate dataset integrity
2. Check metadata.csv correctness
3. Verify train/val split balance
4. Test data loading
5. Validate configuration

### During Training
1. Monitor TensorBoard regularly
2. Check for overfitting
3. Verify loss convergence
4. Monitor GPU utilization
5. Save checkpoints frequently

### After Training
1. Validate on test set
2. Analyze per-generator metrics
3. Check confusion matrix
4. Compare with baselines
5. Document hyperparameters

### Hyperparameter Tuning

**Learning Rate**:
- Start with 1e-4 for AdamW
- Adjust by factor of 10
- Monitor loss curve

**Batch Size**:
- Maximize within memory limits
- Larger = more stable gradients
- Adjust learning rate proportionally

**Epochs**:
- Use early stopping
- Start with 50 epochs
- Adjust based on convergence

**Dropout**:
- 0.3-0.5 for most cases
- Increase if overfitting
- Decrease if underfitting

## Examples

### Train EfficientNet-B4

```bash
python -m app.training.train \
  --config app/training/configs/train_config.yaml
```

### Train ConvNeXt-Tiny

Edit config:
```yaml
model:
  architecture: convnext_tiny
```

Then train:
```bash
python -m app.training.train \
  --config app/training/configs/train_config.yaml
```

### Resume from Checkpoint

```bash
python -m app.training.train \
  --config app/training/configs/train_config.yaml \
  --resume
```

### Train with Custom Config

```bash
python -m app.training.train \
  --config my_custom_config.yaml
```

## Performance Optimization

### GPU Utilization
- Use mixed precision
- Pin memory
- Increase num_workers
- Optimize batch size

### Data Loading
- Use SSD for dataset
- Increase num_workers
- Prefetch with DataLoader
- Cache in memory if possible

### Training Speed
- Use larger batch sizes
- Enable mixed precision
- Use efficient architectures
- Reduce image size if acceptable

## Troubleshooting

### Dataset Issues

**Metadata Not Found**:
```
FileNotFoundError: Metadata file not found
```
**Solution**: Check metadata.csv path in config

**Empty Dataset**:
```
[TruthLensDataset] Loaded 0 samples
```
**Solution**: Verify filters and metadata content

**Corrupted Images**:
```
PIL.UnidentifiedImageError
```
**Solution**: Run dataset_manager corruption detection

### Model Issues

**CUDA Out of Memory**:
```
RuntimeError: CUDA out of memory
```
**Solution**: Reduce batch size or use gradient accumulation

**Model Not Loading**:
```
AttributeError: module has no attribute
```
**Solution**: Check architecture name and torchvision version

### Training Issues

**Loss Not Decreasing**:
- Lower learning rate
- Check data preprocessing
- Verify label correctness
- Try different optimizer

**Overfitting**:
- Add data augmentation
- Increase dropout
- Use smaller model
- Add regularization

**Underfitting**:
- Increase model capacity
- Train longer
- Remove regularization
- Check data quality

## Integration with Dataset Manager

The training pipeline integrates seamlessly with the dataset_manager:

1. **Dataset Organization**:
   ```bash
   python -m app.dataset_manager.cli --organize-tiny-genimage /path/to/data
   ```

2. **Metadata Generation**:
   - Automatically creates metadata.csv
   - Includes all required fields
   - Validates metadata integrity

3. **Training**:
   ```bash
   python -m app.training.train --config app/training/configs/train_config.yaml
   ```

4. **Validation**:
   ```bash
   python -m app.training.validate --config app/training/configs/val_config.yaml
   ```

## Production Considerations

### Model Deployment
- Export to ONNX for inference
- Quantize for edge deployment
- Optimize for target hardware
- Test with production data

### Monitoring
- Track inference latency
- Monitor prediction distribution
- Alert on performance degradation
- Log predictions for analysis

### Maintenance
- Regular retraining
- Data drift detection
- Model versioning
- A/B testing new models

## Security Considerations

### Data Privacy
- Ensure dataset compliance
- Remove sensitive metadata
- Secure training data
- Audit data sources

### Model Security
- Validate model integrity
- Check for adversarial vulnerabilities
- Secure model storage
- Monitor for abuse

## References

### PyTorch Documentation
- [PyTorch Tutorials](https://pytorch.org/tutorials/)
- [PyTorch Documentation](https://pytorch.org/docs/)

### Model Architectures
- [EfficientNet Paper](https://arxiv.org/abs/1905.11946)
- [ConvNeXt Paper](https://arxiv.org/abs/2201.03545)
- [ResNet Paper](https://arxiv.org/abs/1512.03385)

### Training Techniques
- [Mixed Precision Training](https://pytorch.org/docs/stable/amp.html)
- [Learning Rate Schedules](https://pytorch.org/docs/stable/optim.html)
- [Early Stopping](https://en.wikipedia.org/wiki/Early_stopping)
