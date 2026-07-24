"""
Training Module
===============
Provides training pipeline for AI image detection classifier.
Supports training on datasets of real vs AI-generated images from various sources.
"""

from .dataset_loader import AIDetectionDataset, create_dataloaders
from .trainer import AIDetectionTrainer
from .validator import AIDetectionValidator

__all__ = ["AIDetectionDataset", "create_dataloaders", "AIDetectionTrainer", "AIDetectionValidator"]
