"""
TruthLens Models
================
Model architectures for AI content detection.
"""

import torch
import torch.nn as nn
from typing import Optional, Dict, Any
from torchvision import models
from torchvision.models import EfficientNet_B4_Weights, ConvNeXt_Tiny_Weights, ResNet50_Weights


class TruthLensModel(nn.Module):
    """
    Unified model interface for AI content detection.
    
    Supports multiple architectures: EfficientNet-B4, ConvNeXt, ResNet50.
    """
    
    def __init__(
        self,
        architecture: str = 'efficientnet_b4',
        num_classes: int = 2,
        pretrained: bool = True,
        dropout: float = 0.3
    ):
        """
        Initialize TruthLens model.
        
        Args:
            architecture: Model architecture ('efficientnet_b4', 'convnext_tiny', 'resnet50')
            num_classes: Number of output classes (default: 2 for binary classification)
            pretrained: Whether to use pretrained weights
            dropout: Dropout probability for classifier head
        """
        super(TruthLensModel, self).__init__()
        
        self.architecture = architecture
        self.num_classes = num_classes
        
        # Load base model
        if architecture == 'efficientnet_b4':
            weights = EfficientNet_B4_Weights.DEFAULT if pretrained else None
            self.backbone = models.efficientnet_b4(weights=weights)
            num_features = self.backbone.classifier[1].in_features
            self.backbone.classifier = nn.Sequential(
                nn.Dropout(p=dropout),
                nn.Linear(num_features, num_classes)
            )

        elif architecture == 'convnext_tiny':
            weights = ConvNeXt_Tiny_Weights.DEFAULT if pretrained else None
            self.backbone = models.convnext_tiny(weights=weights)
            num_features = self.backbone.classifier[2].in_features
            self.backbone.classifier = nn.Sequential(
                nn.LayerNorm(num_features),
                nn.Dropout(p=dropout),
                nn.Linear(num_features, num_classes)
            )

        elif architecture == 'resnet50':
            weights = ResNet50_Weights.DEFAULT if pretrained else None
            self.backbone = models.resnet50(weights=weights)
            num_features = self.backbone.fc.in_features
            self.backbone.fc = nn.Sequential(
                nn.Dropout(p=dropout),
                nn.Linear(num_features, num_classes)
            )
        
        else:
            raise ValueError(
                f"Unknown architecture: {architecture}. "
                f"Supported: efficientnet_b4, convnext_tiny, resnet50"
            )
        
        print(f"[TruthLensModel] Initialized {architecture} with {num_classes} classes")
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            x: Input tensor of shape (batch_size, 3, height, width)
        
        Returns:
            Output logits of shape (batch_size, num_classes)
        """
        return self.backbone(x)
    
    def get_feature_extractor(self) -> nn.Module:
        """
        Get the feature extractor part of the model (without classifier).
        
        Returns:
            Feature extractor module
        """
        if self.architecture == 'efficientnet_b4':
            return self.backbone.features
        elif self.architecture == 'convnext_tiny':
            return self.backbone.features
        elif self.architecture == 'resnet50':
            return nn.Sequential(*list(self.backbone.children())[:-1])
        else:
            raise ValueError(f"Unknown architecture: {self.architecture}")
    
    def freeze_backbone(self):
        """Freeze the backbone parameters for transfer learning."""
        if self.architecture == 'efficientnet_b4':
            for param in self.backbone.features.parameters():
                param.requires_grad = False
        elif self.architecture == 'convnext_tiny':
            for param in self.backbone.features.parameters():
                param.requires_grad = False
        elif self.architecture == 'resnet50':
            for param in self.backbone.parameters():
                param.requires_grad = False
        print(f"[TruthLensModel] Frozen backbone of {self.architecture}")
    
    def unfreeze_backbone(self):
        """Unfreeze the backbone parameters."""
        for param in self.backbone.parameters():
            param.requires_grad = True
        print(f"[TruthLensModel] Unfrozen backbone of {self.architecture}")
    
    def get_classifier(self) -> nn.Module:
        """
        Get the classifier head of the model.
        
        Returns:
            Classifier module
        """
        if self.architecture == 'efficientnet_b4':
            return self.backbone.classifier
        elif self.architecture == 'convnext_tiny':
            return self.backbone.classifier
        elif self.architecture == 'resnet50':
            return self.backbone.fc
        else:
            raise ValueError(f"Unknown architecture: {self.architecture}")


def create_model(
    architecture: str = 'efficientnet_b4',
    num_classes: int = 2,
    pretrained: bool = True,
    dropout: float = 0.3,
    freeze_backbone: bool = False
) -> TruthLensModel:
    """
    Create a TruthLens model with specified configuration.
    
    Args:
        architecture: Model architecture
        num_classes: Number of output classes
        pretrained: Whether to use pretrained weights
        dropout: Dropout probability
        freeze_backbone: Whether to freeze backbone parameters
    
    Returns:
        Configured TruthLensModel instance
    """
    model = TruthLensModel(
        architecture=architecture,
        num_classes=num_classes,
        pretrained=pretrained,
        dropout=dropout
    )
    
    if freeze_backbone:
        model.freeze_backbone()
    
    return model


def get_model_info(architecture: str) -> Dict[str, Any]:
    """
    Get information about a model architecture.
    
    Args:
        architecture: Model architecture name
    
    Returns:
        Dict with model information
    """
    info = {
        'efficientnet_b4': {
            'input_size': 224,
            'params': '19M',
            'flops': '0.4B',
            'description': 'EfficientNet-B4: Efficient convolutional neural network'
        },
        'convnext_tiny': {
            'input_size': 224,
            'params': '29M',
            'flops': '4.5B',
            'description': 'ConvNeXt-Tiny: Modern convolutional architecture'
        },
        'resnet50': {
            'input_size': 224,
            'params': '26M',
            'flops': '4.1B',
            'description': 'ResNet-50: Residual neural network'
        }
    }
    
    return info.get(architecture, {'description': 'Unknown architecture'})
