"""
Grad-CAM Implementation for TruthLens
====================================
Grad-CAM visualization for model explainability.
"""

import sys
from pathlib import Path
from typing import Optional, Tuple
import argparse
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.training.models import create_model
from app.training.dataloader import get_default_transforms
from app.training.utils import get_device


class GradCAM:
    """
    Grad-CAM visualization class.
    
    Computes gradient-weighted class activation mapping for model explainability.
    """
    
    def __init__(self, model: nn.Module, target_layer: Optional[str] = None):
        """
        Initialize Grad-CAM.
        
        Args:
            model: PyTorch model to explain
            target_layer: Target layer name for Grad-CAM (default: backbone.features.8.0)
        """
        self.model = model
        self.target_layer = target_layer or "backbone.features.8.0"
        self.activations = None
        self.gradients = None
        self.handles = []
        
        # Get model device dynamically
        self.device = next(self.model.parameters()).device
        
        # Register hooks
        self._register_hooks()
    
    def _register_hooks(self):
        """Register forward and backward hooks on target layer."""
        # Get target layer
        target_layer = self.model
        for name in self.target_layer.split('.'):
            target_layer = getattr(target_layer, name)
        
        # Forward hook to capture activations
        def forward_hook(module, input, output):
            self.activations = output.detach()
        
        # Backward hook to capture gradients
        def backward_hook(module, grad_input, grad_output):
            self.gradients = grad_output[0].detach()
        
        # Register hooks
        handle_forward = target_layer.register_forward_hook(forward_hook)
        handle_backward = target_layer.register_backward_hook(backward_hook)
        
        self.handles.extend([handle_forward, handle_backward])
    
    def _remove_hooks(self):
        """Remove all registered hooks."""
        for handle in self.handles:
            handle.remove()
        self.handles = []
    
    def generate_heatmap(
        self,
        input_tensor: torch.Tensor,
        target_class: Optional[int] = None
    ) -> np.ndarray:
        """
        Generate Grad-CAM heatmap for an input tensor.
        
        Args:
            input_tensor: Input image tensor (1, C, H, W)
            target_class: Target class index (uses predicted class if None)
        
        Returns:
            Normalized heatmap as numpy array (H, W)
        """
        # Debug print
        print(f"[GradCAM Debug] Model device: {self.device}")
        print(f"[GradCAM Debug] Input tensor device: {input_tensor.device}")
        
        # Reset stored values
        self.activations = None
        self.gradients = None
        
        # Move input tensor to model device
        input_tensor = input_tensor.to(self.device)
        print(f"[GradCAM Debug] Input tensor moved to: {input_tensor.device}")
        
        # Forward pass
        self.model.eval()
        with torch.enable_grad():
            input_tensor = input_tensor.requires_grad_(True)
            output = self.model(input_tensor)
            
            # Get target class
            if target_class is None:
                target_class = output.argmax(dim=1).item()
            
            # Backward pass for target class
            self.model.zero_grad()
            class_score = output[0, target_class]
            class_score.backward()
        
        # Compute weights
        if self.gradients is None or self.activations is None:
            raise RuntimeError("Hooks did not capture activations/gradients")
        
        print(f"[GradCAM Debug] Gradients device: {self.gradients.device}")
        print(f"[GradCAM Debug] Activations device: {self.activations.device}")
        
        # Global average pooling of gradients
        weights = self.gradients.mean(dim=(2, 3), keepdim=True)  # (1, C, 1, 1)
        
        # Weighted combination of activations
        cam = (weights * self.activations).sum(dim=1, keepdim=True)  # (1, 1, H, W)
        
        # ReLU to remove negative values
        cam = F.relu(cam)
        
        # Resize to input size
        cam = F.interpolate(
            cam,
            size=(input_tensor.shape[2], input_tensor.shape[3]),
            mode='bilinear',
            align_corners=False
        )
        
        # Normalize to [0, 1]
        cam = cam.squeeze().cpu().numpy()
        print(f"[GradCAM Debug] Heatmap moved to CPU for numpy conversion")
        if cam.max() > cam.min():
            cam = (cam - cam.min()) / (cam.max() - cam.min())
        
        return cam
    
    def __del__(self):
        """Clean up hooks when object is destroyed."""
        self._remove_hooks()


def test_gradcam():
    """
    Standalone test for Grad-CAM implementation.
    Loads model, processes one image, and reports heatmap shape and value range.
    """
    print("=" * 80)
    print("Grad-CAM Test")
    print("=" * 80)
    
    # Paths
    checkpoint_path = "experiments/cifake_efficientnet_b4_baseline/checkpoints/latest_checkpoint.pth"
    test_image_path = "TruthLensDataset/real/train/00000.jpg"  # Adjust as needed
    
    # Check if test image exists
    if not Path(test_image_path).exists():
        print(f"[Test] Test image not found: {test_image_path}")
        print("[Test] Please provide a valid image path")
        return
    
    # Load model
    print("\n[Step 1] Loading model...")
    device = get_device()
    model = create_model(
        architecture='efficientnet_b4',
        num_classes=2,
        pretrained=False,
        dropout=0.3
    )
    
    checkpoint = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(device)
    print(f"[Test] Loaded checkpoint from {checkpoint_path}")
    
    # Load and preprocess image
    print("\n[Step 2] Loading and preprocessing image...")
    _, val_transform = get_default_transforms(image_size=224, augment=False)
    image = Image.open(test_image_path).convert('RGB')
    input_tensor = val_transform(image).unsqueeze(0).to(device)
    print(f"[Test] Input tensor shape: {input_tensor.shape}")
    
    # Initialize Grad-CAM
    print("\n[Step 3] Initializing Grad-CAM...")
    gradcam = GradCAM(model, target_layer="backbone.features.8.0")
    print(f"[Test] Target layer: {gradcam.target_layer}")
    
    # Generate heatmap
    print("\n[Step 4] Generating Grad-CAM heatmap...")
    heatmap = gradcam.generate_heatmap(input_tensor)
    
    # Report results
    print("\n[Step 5] Results:")
    print("-" * 40)
    print(f"Heatmap shape: {heatmap.shape}")
    print(f"Value range: [{heatmap.min():.4f}, {heatmap.max():.4f}]")
    print(f"Mean value: {heatmap.mean():.4f}")
    print(f"Std deviation: {heatmap.std():.4f}")
    
    # Clean up
    gradcam._remove_hooks()
    
    print("\n" + "=" * 80)
    print("Grad-CAM Test Complete")
    print("=" * 80)


def main():
    """CLI entry point for Grad-CAM testing."""
    parser = argparse.ArgumentParser(description='Test Grad-CAM implementation')
    parser.add_argument(
        '--checkpoint',
        type=str,
        default='experiments/cifake_efficientnet_b4_baseline/checkpoints/latest_checkpoint.pth',
        help='Path to model checkpoint'
    )
    parser.add_argument(
        '--image',
        type=str,
        help='Path to test image'
    )
    parser.add_argument(
        '--target-layer',
        type=str,
        default='backbone.features.8.0',
        help='Target layer for Grad-CAM'
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("TruthLens Grad-CAM Test")
    print("=" * 80)
    
    # Load model
    print("\n[Step 1] Loading model...")
    device = get_device()
    model = create_model(
        architecture='efficientnet_b4',
        num_classes=2,
        pretrained=False,
        dropout=0.3
    )
    
    checkpoint = torch.load(args.checkpoint, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(device)
    print(f"[Test] Loaded checkpoint from {args.checkpoint}")
    
    # Load and preprocess image
    if args.image:
        print("\n[Step 2] Loading and preprocessing image...")
        _, val_transform = get_default_transforms(image_size=224, augment=False)
        image = Image.open(args.image).convert('RGB')
        input_tensor = val_transform(image).unsqueeze(0).to(device)
        print(f"[Test] Input tensor shape: {input_tensor.shape}")
    else:
        print("\n[Step 2] No image provided, creating dummy tensor...")
        input_tensor = torch.randn(1, 3, 224, 224).to(device)
        print(f"[Test] Dummy tensor shape: {input_tensor.shape}")
    
    # Initialize Grad-CAM
    print("\n[Step 3] Initializing Grad-CAM...")
    gradcam = GradCAM(model, target_layer=args.target_layer)
    print(f"[Test] Target layer: {gradcam.target_layer}")
    
    # Generate heatmap
    print("\n[Step 4] Generating Grad-CAM heatmap...")
    heatmap = gradcam.generate_heatmap(input_tensor)
    
    # Report results
    print("\n[Step 5] Results:")
    print("-" * 40)
    print(f"Heatmap shape: {heatmap.shape}")
    print(f"Value range: [{heatmap.min():.4f}, {heatmap.max():.4f}]")
    print(f"Mean value: {heatmap.mean():.4f}")
    print(f"Std deviation: {heatmap.std():.4f}")
    
    # Clean up
    gradcam._remove_hooks()
    
    print("\n" + "=" * 80)
    print("Grad-CAM Test Complete")
    print("=" * 80)


if __name__ == "__main__":
    main()

