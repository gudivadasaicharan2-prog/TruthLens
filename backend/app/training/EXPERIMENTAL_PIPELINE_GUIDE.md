# TruthLens Experimental AI Pipeline Guide

## Overview

This guide provides complete instructions for running the Phase 5 experimental AI pipeline, including baseline training, comprehensive evaluation, and model comparison.

## Infrastructure Components

### New Modules Created

1. **`error_analysis.py`** - Error analysis module
   - False positive/negative analysis
   - Confidence distributions
   - Representative misclassified examples
   - Per-generator and per-dataset error breakdown

2. **`benchmarking.py`** - Benchmarking module
   - Training time measurement
   - Inference speed (samples/second)
   - GPU memory usage
   - Model size and parameter count

3. **`evaluate.py`** - Comprehensive evaluation script
   - Full metrics calculation
   - Error analysis integration
   - Benchmarking integration
   - Plot generation (ROC, PR, confusion matrix)

4. **`compare_models.py`** - Model comparison script
   - Multi-model comparison
   - Consolidated comparison report
   - Production model recommendation

### Enhanced Modules

1. **`validate.py`** - Enhanced with:
   - PR-AUC metric
   - Error analysis integration
   - Benchmarking integration

2. **`plotting.py`** - Enhanced with:
   - ROC curve generation with probabilities
   - PR curve generation with probabilities

## Experiment Workflow

### Step 1: Train Baseline EfficientNet-B4

```bash
python -m app.training.train --config backend/app/training/configs/train_config_efficientnet_b4.yaml
```

**Expected Outputs:**
- Experiment directory: `experiments/cifake_efficientnet_b4_baseline/`
- Checkpoints: `best_model.pth`, `last_model.pth`
- Training history: `training_history.json`
- Plots: `training_curves.png`, `confusion_matrix.png`, etc.
- TensorBoard logs: `logs/`

### Step 2: Evaluate Baseline Model

```bash
python -m app.training.evaluate --config backend/app/training/configs/eval_config.yaml --checkpoint experiments/cifake_efficientnet_b4_baseline/checkpoints/best_model.pth --output experiments/cifake_efficientnet_b4_baseline/evaluation_results
```

**Expected Outputs:**
- `metrics.json` - Complete metrics (Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC)
- `error_analysis.json` - Detailed error analysis
- `benchmark.json` - Performance benchmarks
- `plots/` - ROC curve, PR curve, confusion matrix, per-generator/dataset metrics
- `complete_results.json` - All results combined

### Step 3: Train ConvNeXt-Tiny

```bash
python -m app.training.train --config backend/app/training/configs/train_config_convnext_tiny.yaml
```

### Step 4: Evaluate ConvNeXt-Tiny

```bash
python -m app.training.evaluate --config backend/app/training/configs/eval_config.yaml --checkpoint experiments/cifake_convnext_tiny/checkpoints/best_model.pth --output experiments/cifake_convnext_tiny/evaluation_results
```

### Step 5: Train ResNet50

```bash
python -m app.training.train --config backend/app/training/configs/train_config_resnet50.yaml
```

### Step 6: Evaluate ResNet50

```bash
python -m app.training.evaluate --config backend/app/training/configs/eval_config.yaml --checkpoint experiments/cifake_resnet50/checkpoints/best_model.pth --output experiments/cifake_resnet50/evaluation_results
```

### Step 7: Compare All Models

```bash
python -m app.training.compare_models --experiments experiments/cifake_efficientnet_b4_baseline experiments/cifake_convnext_tiny experiments/cifake_resnet50 --output model_comparison
```

**Expected Outputs:**
- `model_comparison.csv` - Comparison table
- `model_comparison.json` - Comparison data
- `comparison_report.txt` - Detailed comparison report
- `recommendation.txt` - Production model recommendation

## Standard Artifacts Generated

### Training Artifacts
- `best_model.pth` - Best model checkpoint
- `last_model.pth` - Last epoch checkpoint
- `training_history.json` - Per-epoch metrics
- `config.yaml` - Training configuration
- `metadata.json` - Experiment metadata

### Evaluation Artifacts
- `metrics.json` - Complete metrics
  - Accuracy
  - Precision
  - Recall
  - F1-score
  - ROC-AUC
  - PR-AUC
  - Confusion matrix
  - Per-generator metrics
  - Per-dataset metrics

- `error_analysis.json` - Error analysis
  - Total errors
  - False positives/negatives
  - Confidence distributions
  - Per-generator error breakdown
  - Per-dataset error breakdown
  - Representative misclassified examples

- `benchmark.json` - Performance benchmarks
  - Model parameters
  - Model size
  - Inference speed
  - GPU memory usage
  - Training time

- `plots/` - Visualization
  - `roc_curve.png`
  - `pr_curve.png`
  - `confusion_matrix.png`
  - `per_generator_metrics.png`
  - `per_dataset_metrics.png`

## Configuration Files

### Training Configurations
- `train_config_efficientnet_b4.yaml` - EfficientNet-B4 baseline
- `train_config_convnext_tiny.yaml` - ConvNeXt-Tiny
- `train_config_resnet50.yaml` - ResNet50

All configs use identical training settings for fair comparison:
- 50 epochs
- AdamW optimizer (lr=0.0001, weight_decay=0.01)
- Cosine learning rate scheduler
- Mixed precision training
- Early stopping (patience=7)
- Batch size=32
- Image size=224

### Evaluation Configuration
- `eval_config.yaml` - Comprehensive evaluation settings

## Monitoring Training

### TensorBoard
```bash
tensorboard --logdir experiments/cifake_efficientnet_b4_baseline/logs
```

### Experiment Registry
The `experiments/experiments.csv` file tracks all experiments with:
- Experiment ID
- Model architecture
- Dataset
- Epochs
- Metrics
- Best epoch
- Date
- Checkpoint path
- Status

## Metrics Explained

### Performance Metrics
- **Accuracy**: Overall classification accuracy
- **Precision**: True positives / (True positives + False positives)
- **Recall**: True positives / (True positives + False negatives)
- **F1-score**: Harmonic mean of precision and recall
- **ROC-AUC**: Area under ROC curve (higher is better)
- **PR-AUC**: Area under Precision-Recall curve (higher is better)

### Error Metrics
- **Error Rate**: Total misclassifications / total samples
- **FP Rate**: False positives / total real samples
- **FN Rate**: False negatives / total AI samples

### Efficiency Metrics
- **Parameters**: Total model parameters
- **Model Size**: Disk size of checkpoint
- **Inference Speed**: Samples processed per second
- **GPU Memory**: Peak GPU memory usage

## Production Model Selection

The comparison script uses a weighted composite score:
- Accuracy: 30%
- F1-score: 20%
- ROC-AUC: 20%
- Inference speed: 15%
- Model size: 10%
- Error rate: 5%

The recommendation report provides:
- Best performer in each category
- Overall recommended model
- Trade-off analysis
- Rationale for recommendation

## Troubleshooting

### Out of Memory
- Reduce batch size in config
- Reduce image size
- Disable mixed precision (set `mixed_precision: false`)

### Slow Training
- Increase batch size (if memory allows)
- Reduce `num_workers` if CPU-bound
- Use smaller model architecture

### Poor Performance
- Check data distribution in metadata.csv
- Verify image paths are correct
- Increase training epochs
- Adjust learning rate
- Try different optimizer

## Next Steps After Experiments

1. Review comparison report
2. Analyze error analysis for each model
3. Check benchmark results for efficiency
4. Select production model based on requirements
5. Deploy selected model to production
6. Monitor performance in production

## Notes

- All experiments use the same CIFAKE dataset via metadata.csv
- No modifications to dataset_manager or metadata schema
- Each experiment is fully reproducible from saved config
- All artifacts are versioned in experiment directories
- Experiment registry provides tracking across all experiments
