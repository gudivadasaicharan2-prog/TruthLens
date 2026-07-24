"""
Grad-CAM Visualization for EfficientNet-B2 Classifier

This module implements Gradient-weighted Class Activation Mapping (Grad-CAM)
to visualize which regions of an image contribute most to the AI detection prediction.

Grad-CAM works by:
1. Computing gradients of the predicted class score w.r.t. feature maps
2. Weighting feature maps by these gradients (global average pooling)
3. Generating a heatmap highlighting important regions
4. Overlaying the heatmap on the original image

Optimized for inference speed by:
- Reusing the existing model instance
- Minimizing unnecessary computations
- Using efficient tensor operations
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import cv2
from PIL import Image
from pathlib import Path
from typing import Tuple, Optional
import uuid


class GradCAMGenerator:
    """
    Grad-CAM generator for EfficientNet-B2 classifier.
    
    This class hooks into the model to capture gradients and activations
    from the final convolutional layer, then computes and visualizes
    the class activation map.
    """
    
    def __init__(self, model: nn.Module, device: str = 'cuda'):
        """
        Initialize Grad-CAM generator.
        
        Args:
            model: The EfficientNet-B2 model with classifier head
            device: Device to run computations on ('cuda' or 'cpu')
        """
        self.model = model
        self.device = device
        self.model.eval()  # Set to evaluation mode
        
        # Storage for gradients and activations
        self.gradients = None
        self.activations = None
        
        # Find the final convolutional layer in EfficientNet-B2
        # EfficientNet architecture: features -> avgpool -> flatten -> classifier
        # The final conv layer is the last layer in the features block
        self.target_layer = self._find_target_layer()
        
        # Register hooks to capture gradients and activations
        self._register_hooks()
    
    def _find_target_layer(self) -> nn.Module:
        """
        Find the target layer for Grad-CAM - the last conv layer before pooling.
        
        For Grad-CAM, we need a convolutional layer that outputs spatial feature maps.
        The backbone structure is: features (conv layers) -> avgpool -> flatten -> classifier
        We need to hook the last Conv2d layer in the features block.
        
        Returns:
            The target layer for Grad-CAM (last Conv2d in backbone.features)
        """
        # Get the features block
        if hasattr(self.model.backbone, '__iter__'):
            features = list(self.model.backbone.children())[0]
        else:
            features = self.model.backbone
        
        # Find the last Conv2d layer
        target_layer = None
        for module in reversed(list(features.modules())):
            if isinstance(module, nn.Conv2d):
                target_layer = module
                break
        
        if target_layer is None:
            raise ValueError("Could not find Conv2d layer in model")
        
        return target_layer
    
    def _register_hooks(self):
        """
        Register forward and backward hooks to capture activations and gradients.
        
        Forward hook: Captures feature maps (activations) from the target layer
        Backward hook: Captures gradients of the target layer's output
        
        These hooks are called automatically during forward and backward passes.
        """
        # Forward hook to capture activations
        def forward_hook(module, input, output):
            """
            Called during forward pass to capture feature maps.
            
            Args:
                module: The layer being hooked
                input: Input to the layer
                output: Output from the layer (feature maps)
            """
            self.activations = output.detach()  # Detach to avoid gradient tracking
        
        # Backward hook to capture gradients
        def backward_hook(module, grad_input, grad_output):
            """
            Called during backward pass to capture gradients.
            
            Args:
                module: The layer being hooked
                grad_input: Gradients w.r.t. input
                grad_output: Gradients w.r.t. output
            """
            self.gradients = grad_output[0].detach()  # Detach to avoid gradient tracking
        
        # Register hooks on the target layer
        handle_forward = self.target_layer.register_forward_hook(forward_hook)
        handle_backward = self.target_layer.register_full_backward_hook(backward_hook)
        
        # Store handles to prevent garbage collection
        self.hook_handles = [handle_forward, handle_backward]
    
    def generate_cam(
        self,
        input_tensor: torch.Tensor,
        target_class: Optional[int] = None
    ) -> np.ndarray:
        """
        Generate Grad-CAM heatmap for the input image.
        
        Args:
            input_tensor: Preprocessed image tensor (1, 3, H, W)
            target_class: Target class index (None for predicted class)
        
        Returns:
            Heatmap as numpy array (H, W) with values in [0, 1]
        """
        # Move input to device
        input_tensor = input_tensor.to(self.device)
        
        # Reset gradients and activations
        self.gradients = None
        self.activations = None
        
        # Temporarily enable gradients for frozen backbone parameters
        # This is necessary for Grad-CAM to compute gradients
        original_requires_grad = {}
        for name, param in self.model.named_parameters():
            original_requires_grad[name] = param.requires_grad
            param.requires_grad = True
        
        try:
            # Forward pass to get predictions and capture activations
            output = self.model(input_tensor)
            
            # Determine target class (use predicted class if not specified)
            if target_class is None:
                target_class = output.argmax(dim=1).item()
            
            # Zero gradients to avoid accumulation
            self.model.zero_grad()
            
            # Backward pass to compute gradients w.r.t. target class
            # Create a one-hot tensor for the target class
            one_hot = torch.zeros_like(output)
            one_hot[0, target_class] = 1.0
            
            # Compute gradients: d(output)/d(activations)
            output.backward(gradient=one_hot)
            
            # Verify we captured gradients and activations
            if self.gradients is None or self.activations is None:
                raise RuntimeError("Failed to capture gradients or activations")
            
            # Compute Grad-CAM weights
            # Weight each feature map by the mean gradient of that map
            # This gives importance to feature maps that strongly influence the prediction
            gradients = self.gradients[0]  # Shape: (C, H, W)
            activations = self.activations[0]  # Shape: (C, H, W)
            
            # Global average pooling of gradients to get weights for each channel
            weights = torch.mean(gradients, dim=(1, 2))  # Shape: (C,)
            
            # Compute weighted combination of feature maps
            # Multiply each feature map by its corresponding weight and sum
            cam = torch.zeros(activations.shape[1:], dtype=torch.float32, device=self.device)
            for i, w in enumerate(weights):
                cam += w * activations[i]
            
            # Apply ReLU to keep only positive contributions
            # Negative values are likely to be noise or irrelevant features
            cam = F.relu(cam)
            
            # Normalize to [0, 1] range
            cam_min = cam.min()
            cam_max = cam.max()
            if cam_max - cam_min > 0:
                cam = (cam - cam_min) / (cam_max - cam_min)
            
            # Convert to numpy array
            cam = cam.cpu().numpy()
            
            return cam
        finally:
            # Restore original requires_grad settings
            for name, param in self.model.named_parameters():
                if name in original_requires_grad:
                    param.requires_grad = original_requires_grad[name]
    
    def resize_heatmap(
        self,
        heatmap: np.ndarray,
        target_size: Tuple[int, int]
    ) -> np.ndarray:
        """
        Resize heatmap to match original image dimensions.
        
        Args:
            heatmap: Heatmap array (H, W)
            target_size: Target size (width, height)
        
        Returns:
            Resized heatmap
        """
        # Convert to uint8 for OpenCV resize
        heatmap_uint8 = (heatmap * 255).astype(np.uint8)
        
        # Resize using bilinear interpolation
        heatmap_resized = cv2.resize(
            heatmap_uint8,
            target_size,
            interpolation=cv2.INTER_LINEAR
        )
        
        # Normalize back to [0, 1]
        heatmap_resized = heatmap_resized.astype(np.float32) / 255.0
        
        return heatmap_resized
    
    def apply_colormap(self, heatmap: np.ndarray) -> np.ndarray:
        """
        Apply colormap to heatmap for visualization.
        
        Args:
            heatmap: Heatmap array (H, W) with values in [0, 1]
        
        Returns:
            Colored heatmap (H, W, 3) in RGB format
        """
        # Convert to uint8 for colormap
        heatmap_uint8 = (heatmap * 255).astype(np.uint8)
        
        # Apply JET colormap (blue=cold, red=hot)
        # OpenCV uses BGR format, so we convert to RGB later
        heatmap_colored = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
        
        # Convert BGR to RGB
        heatmap_colored = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)
        
        return heatmap_colored
    
    def create_overlay(
        self,
        original_image: np.ndarray,
        heatmap: np.ndarray,
        alpha: float = 0.4
    ) -> np.ndarray:
        """
        Create overlay of heatmap on original image.
        
        Args:
            original_image: Original image array (H, W, 3) in RGB format
            heatmap: Colored heatmap (H, W, 3) in RGB format
            alpha: Transparency factor for heatmap (0-1)
        
        Returns:
            Overlay image (H, W, 3) in RGB format
        """
        # Ensure both images have the same dtype
        original_image = original_image.astype(np.float32)
        heatmap = heatmap.astype(np.float32)
        
        # Blend images: overlay = alpha * heatmap + (1 - alpha) * original
        overlay = alpha * heatmap + (1 - alpha) * original_image
        
        # Clip values to valid range and convert to uint8
        overlay = np.clip(overlay, 0, 255).astype(np.uint8)
        
        return overlay
    
    def generate_visualization(
        self,
        image_path: str,
        input_tensor: torch.Tensor,
        output_dir: str = "uploads/heatmaps"
    ) -> dict:
        """
        Generate complete Grad-CAM visualization (heatmap and overlay).
        
        Args:
            image_path: Path to the original image
            input_tensor: Preprocessed image tensor (1, 3, H, W)
            output_dir: Directory to save visualizations
        
        Returns:
            Dictionary with paths to saved images:
            {
                'heatmap_path': str,
                'overlay_path': str
            }
        """
        # Load original image for overlay
        original_image = Image.open(image_path).convert('RGB')
        original_array = np.array(original_image)
        original_size = original_image.size[::-1]  # (height, width)
        
        # Generate Grad-CAM heatmap
        heatmap = self.generate_cam(input_tensor)
        
        # Resize heatmap to match original image size
        heatmap_resized = self.resize_heatmap(heatmap, original_image.size)
        
        # Apply colormap to heatmap
        heatmap_colored = self.apply_colormap(heatmap_resized)
        
        # Create overlay on original image
        overlay = self.create_overlay(original_array, heatmap_colored)
        
        # Generate unique filename for this analysis
        image_id = str(uuid.uuid4())[:8]
        base_name = Path(image_path).stem
        
        # Ensure output directory exists
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save heatmap
        heatmap_path = output_path / f"{base_name}_{image_id}_heatmap.png"
        Image.fromarray(heatmap_colored).save(heatmap_path)
        
        # Save overlay
        overlay_path = output_path / f"{base_name}_{image_id}_overlay.png"
        Image.fromarray(overlay).save(overlay_path)
        
        return {
            'heatmap_path': str(heatmap_path),
            'overlay_path': str(overlay_path)
        }


def get_gradcam_generator(model: nn.Module, device: str = 'cuda') -> GradCAMGenerator:
    """
    Factory function to create a Grad-CAM generator.
    
    Args:
        model: The EfficientNet-B2 model
        device: Device to run computations on
    
    Returns:
        Configured GradCAMGenerator instance
    """
    return GradCAMGenerator(model, device)
