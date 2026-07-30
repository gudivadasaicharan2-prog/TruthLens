"""
Model Introspection Utility for TruthLens
=========================================
Utility for inspecting model architecture and finding Grad-CAM target layers.
Supports multiple backbone architectures: EfficientNet, ConvNeXt, ResNet, Swin.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import argparse
import torch
import torch.nn as nn

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.training.models import create_model
from app.training.utils import get_device


class ModelInspector:
    """
    Model introspection utility for finding Grad-CAM target layers.
    """
    
    # Convolutional layer types for different backbones
    CONV_LAYER_TYPES = (
        nn.Conv2d,
        # Add more conv types as needed for other backbones
        # nn.Conv3d, nn.Conv1d, etc.
    )
    
    def __init__(self, model: nn.Module):
        """
        Initialize model inspector.
        
        Args:
            model: PyTorch model to inspect
        """
        self.model = model
        self.layer_info = []
        self.final_conv_layer = None
        self._analyze_model()
    
    def _analyze_model(self):
        """Analyze model structure and collect layer information."""
        self.layer_info = []
        self.final_conv_layer = None
        self._traverse_module(self.model, prefix="")
        
        # Find final convolutional layer
        for layer_name, layer_type, layer_obj, channels in reversed(self.layer_info):
            if isinstance(layer_obj, self.CONV_LAYER_TYPES):
                self.final_conv_layer = {
                    'name': layer_name,
                    'type': layer_type,
                    'object': layer_obj,
                    'out_channels': channels
                }
                break
    
    def _traverse_module(self, module: nn.Module, prefix: str = ""):
        """
        Recursively traverse model hierarchy.
        
        Args:
            module: Current module to traverse
            prefix: Name prefix for current module
        """
        for name, child in module.named_children():
            full_name = f"{prefix}.{name}" if prefix else name
            
            # Get layer type
            layer_type = child.__class__.__name__
            
            # Get output channels if applicable
            out_channels = None
            if isinstance(child, self.CONV_LAYER_TYPES):
                out_channels = child.out_channels
            elif isinstance(child, nn.Linear):
                out_channels = child.out_features
            
            # Store layer info
            self.layer_info.append((full_name, layer_type, child, out_channels))
            
            # Recurse into child modules
            self._traverse_module(child, full_name)
    
    def print_hierarchy(self, max_depth: int = 10):
        """
        Print complete module hierarchy.
        
        Args:
            max_depth: Maximum depth to print (default: 10)
        """
        print("\n" + "=" * 80)
        print("MODEL HIERARCHY")
        print("=" * 80)
        
        for layer_name, layer_type, layer_obj, out_channels in self.layer_info:
            # Calculate depth
            depth = layer_name.count('.')
            if depth > max_depth:
                continue
            
            # Format output
            indent = "  " * depth
            channel_info = f" [out: {out_channels}]" if out_channels is not None else ""
            print(f"{indent}{layer_name}: {layer_type}{channel_info}")
        
        print("=" * 80)
    
    def print_layer_info(self):
        """Print detailed information for all layers."""
        print("\n" + "=" * 80)
        print("LAYER INFORMATION")
        print("=" * 80)
        print(f"{'Layer Name':<50} {'Type':<20} {'Out Channels':<15}")
        print("-" * 80)
        
        for layer_name, layer_type, layer_obj, out_channels in self.layer_info:
            channel_str = str(out_channels) if out_channels is not None else "N/A"
            print(f"{layer_name:<50} {layer_type:<20} {channel_str:<15}")
        
        print("=" * 80)
    
    def get_final_conv_layer(self) -> Optional[Dict[str, Any]]:
        """
        Get the final convolutional layer for Grad-CAM.
        
        Returns:
            Dictionary with layer information or None if no conv layer found
        """
        return self.final_conv_layer
    
    def get_gradcam_target_layer(self) -> Optional[str]:
        """
        Get recommended Grad-CAM target layer name.
        
        Returns:
            Layer name string or None if no suitable layer found
        """
        if self.final_conv_layer:
            return self.final_conv_layer['name']
        return None
    
    def print_gradcam_recommendation(self):
        """Print Grad-CAM target layer recommendation."""
        print("\n" + "=" * 80)
        print("GRAD-CAM TARGET LAYER RECOMMENDATION")
        print("=" * 80)
        
        if self.final_conv_layer:
            print(f"Recommended Target Layer: {self.final_conv_layer['name']}")
            print(f"Layer Type: {self.final_conv_layer['type']}")
            print(f"Output Channels: {self.final_conv_layer['out_channels']}")
            print("\nThis is the final convolutional layer in the model.")
            print("Use this layer for Grad-CAM visualization.")
        else:
            print("No convolutional layer found in the model.")
            print("Grad-CAM may not be suitable for this architecture.")
        
        print("=" * 80)
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of model architecture.
        
        Returns:
            Dictionary with model summary
        """
        total_layers = len(self.layer_info)
        conv_layers = sum(1 for _, _, obj, _ in self.layer_info 
                        if isinstance(obj, self.CONV_LAYER_TYPES))
        linear_layers = sum(1 for _, _, obj, _ in self.layer_info 
                          if isinstance(obj, nn.Linear))
        
        return {
            'total_layers': total_layers,
            'convolutional_layers': conv_layers,
            'linear_layers': linear_layers,
            'final_conv_layer': self.final_conv_layer['name'] if self.final_conv_layer else None,
            'gradcam_target': self.get_gradcam_target_layer()
        }


def inspect_model_from_checkpoint(
    checkpoint_path: str,
    architecture: str = 'efficientnet_b4',
    num_classes: int = 2,
    pretrained: bool = False,
    dropout: float = 0.3
) -> ModelInspector:
    """
    Load model from checkpoint and create inspector.
    
    Args:
        checkpoint_path: Path to model checkpoint
        architecture: Model architecture name
        num_classes: Number of output classes
        pretrained: Whether to use pretrained weights
        dropout: Dropout rate
    
    Returns:
        ModelInspector instance
    """
    device = get_device()
    
    # Create model
    model = create_model(
        architecture=architecture,
        num_classes=num_classes,
        pretrained=pretrained,
        dropout=dropout
    )
    
    # Load checkpoint
    checkpoint = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(device)
    
    print(f"[ModelInspector] Loaded checkpoint from {checkpoint_path}")
    print(f"  Architecture: {architecture}")
    print(f"  Epoch: {checkpoint['epoch']}")
    print(f"  Score: {checkpoint['score']:.4f}")
    
    # Create inspector
    inspector = ModelInspector(model)
    
    return inspector


def main():
    """CLI entry point for model inspection."""
    parser = argparse.ArgumentParser(
        description='Inspect TruthLens model architecture for Grad-CAM'
    )
    parser.add_argument(
        '--checkpoint',
        type=str,
        default='experiments/cifake_efficientnet_b4_baseline/checkpoints/latest_checkpoint.pth',
        help='Path to model checkpoint'
    )
    parser.add_argument(
        '--architecture',
        type=str,
        default='efficientnet_b4',
        help='Model architecture (efficientnet_b4, convnext_tiny, resnet50, etc.)'
    )
    parser.add_argument(
        '--num-classes',
        type=int,
        default=2,
        help='Number of output classes'
    )
    parser.add_argument(
        '--max-depth',
        type=int,
        default=10,
        help='Maximum hierarchy depth to print'
    )
    parser.add_argument(
        '--summary-only',
        action='store_true',
        help='Print only summary and Grad-CAM recommendation'
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("TruthLens Model Inspector")
    print("=" * 80)
    
    # Load and inspect model
    inspector = inspect_model_from_checkpoint(
        checkpoint_path=args.checkpoint,
        architecture=args.architecture,
        num_classes=args.num_classes
    )
    
    # Print hierarchy
    if not args.summary_only:
        inspector.print_hierarchy(max_depth=args.max_depth)
        inspector.print_layer_info()
    
    # Print Grad-CAM recommendation
    inspector.print_gradcam_recommendation()
    
    # Print summary
    summary = inspector.get_summary()
    print("\n" + "=" * 80)
    print("MODEL SUMMARY")
    print("=" * 80)
    print(f"Total Layers: {summary['total_layers']}")
    print(f"Convolutional Layers: {summary['convolutional_layers']}")
    print(f"Linear Layers: {summary['linear_layers']}")
    print(f"Final Conv Layer: {summary['final_conv_layer']}")
    print(f"Grad-CAM Target: {summary['gradcam_target']}")
    print("=" * 80)


if __name__ == "__main__":
    main()
