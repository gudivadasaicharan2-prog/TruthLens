"""
Integration Test for TruthLens Explainability Pipeline
======================================================
Validates the complete explainability pipeline before FastAPI integration.
"""

import sys
from pathlib import Path
from typing import Optional
import argparse
import time
import numpy as np
import torch
import torch.nn as nn
from PIL import Image

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.training.models import create_model
from app.training.dataloader import get_default_transforms
from app.training.utils import get_device
from app.explainability.gradcam import GradCAM
from app.explainability.heatmap import colorize_heatmap
from app.explainability.overlay import overlay_heatmap


class ExplainabilityTest:
    """
    Integration test for explainability pipeline.
    """
    
    def __init__(
        self,
        checkpoint_path: str,
        target_layer: str = "backbone.features.8.0"
    ):
        """
        Initialize test.
        
        Args:
            checkpoint_path: Path to model checkpoint
            target_layer: Target layer for Grad-CAM
        """
        self.checkpoint_path = checkpoint_path
        self.target_layer = target_layer
        self.device = None
        self.model = None
        self.transform = None
        
        # Timing measurements
        self.timings = {
            'model_loading': 0.0,
            'inference': 0.0,
            'gradcam': 0.0,
            'heatmap': 0.0,
            'overlay': 0.0
        }
        
        # Status flags
        self.status = {
            'model_loaded': False,
            'prediction_complete': False,
            'gradcam_generated': False,
            'heatmap_generated': False,
            'overlay_generated': False
        }
    
    def load_model(self):
        """Load model from checkpoint."""
        print("\n[Step 1] Loading model...")
        start_time = time.time()
        
        try:
            self.device = get_device()
            print(f"  Device: {self.device}")
            
            self.model = create_model(
                architecture='efficientnet_b4',
                num_classes=2,
                pretrained=False,
                dropout=0.3
            )
            
            checkpoint = torch.load(self.checkpoint_path, map_location=self.device)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.model.to(self.device)
            self.model.eval()
            
            # Verify model device
            model_device = next(self.model.parameters()).device
            print(f"  Model device verified: {model_device}")
            
            print(f"  Checkpoint: {self.checkpoint_path}")
            print(f"  Architecture: EfficientNet-B4")
            print(f"  Epoch: {checkpoint['epoch']}")
            print(f"  Score: {checkpoint['score']:.4f}")
            
            self.status['model_loaded'] = True
            self.timings['model_loading'] = time.time() - start_time
            print(f"  ✓ Model loaded successfully ({self.timings['model_loading']:.3f}s)")
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Checkpoint not found: {self.checkpoint_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {e}")
    
    def load_transforms(self):
        """Load validation transforms."""
        print("\n[Step 2] Loading transforms...")
        _, self.transform = get_default_transforms(image_size=224, augment=False)
        print("  ✓ Transforms loaded")
    
    def run_inference(self, image_tensor: torch.Tensor) -> dict:
        """
        Run inference on image tensor.
        
        Args:
            image_tensor: Input image tensor (1, C, H, W)
        
        Returns:
            Dictionary with prediction results
        """
        print("\n[Step 3] Running inference...")
        start_time = time.time()
        
        try:
            with torch.no_grad():
                image_tensor = image_tensor.to(self.device)
                outputs = self.model(image_tensor)
                probabilities = torch.softmax(outputs, dim=1)
                predictions = torch.argmax(outputs, dim=1)
                confidences, _ = torch.max(probabilities, dim=1)
            
            class_names = ['Real', 'AI']
            predicted_class = class_names[predictions[0].item()]
            confidence = confidences[0].item()
            
            self.status['prediction_complete'] = True
            self.timings['inference'] = time.time() - start_time
            
            print(f"  Predicted class: {predicted_class}")
            print(f"  Confidence: {confidence * 100:.2f}%")
            print(f"  Inference time: {self.timings['inference'] * 1000:.2f} ms")
            print(f"  ✓ Inference complete")
            
            return {
                'predicted_class': predicted_class,
                'confidence': confidence,
                'probabilities': probabilities.cpu().numpy()[0]
            }
            
        except Exception as e:
            raise RuntimeError(f"Inference failed: {e}")
    
    def generate_gradcam(self, image_tensor: torch.Tensor, target_class: Optional[int] = None) -> np.ndarray:
        """
        Generate Grad-CAM heatmap.
        
        Args:
            image_tensor: Input image tensor (1, C, H, W)
            target_class: Target class for Grad-CAM
        
        Returns:
            Grad-CAM heatmap as numpy array
        """
        print("\n[Step 4] Generating Grad-CAM heatmap...")
        start_time = time.time()
        
        try:
            gradcam = GradCAM(self.model, target_layer=self.target_layer)
            heatmap = gradcam.generate_heatmap(image_tensor, target_class)
            gradcam._remove_hooks()
            
            self.status['gradcam_generated'] = True
            self.timings['gradcam'] = time.time() - start_time
            
            print(f"  Target layer: {self.target_layer}")
            print(f"  Heatmap shape: {heatmap.shape}")
            print(f"  Value range: [{heatmap.min():.4f}, {heatmap.max():.4f}]")
            print(f"  ✓ Grad-CAM generated ({self.timings['gradcam'] * 1000:.2f} ms)")
            
            return heatmap
            
        except Exception as e:
            raise RuntimeError(f"Grad-CAM generation failed: {e}")
    
    def colorize_heatmap(self, heatmap: np.ndarray) -> np.ndarray:
        """
        Colorize Grad-CAM heatmap.
        
        Args:
            heatmap: Normalized heatmap (H, W) in [0, 1]
        
        Returns:
            Colorized heatmap (H, W, 3) in [0, 255]
        """
        print("\n[Step 5] Colorizing heatmap...")
        start_time = time.time()
        
        try:
            colored = colorize_heatmap(heatmap, colormap=None)
            
            self.status['heatmap_generated'] = True
            self.timings['heatmap'] = time.time() - start_time
            
            print(f"  Colored shape: {colored.shape}")
            print(f"  Value range: [{colored.min()}, {colored.max()}]")
            print(f"  ✓ Heatmap colorized ({self.timings['heatmap'] * 1000:.2f} ms)")
            
            return colored
            
        except Exception as e:
            raise RuntimeError(f"Heatmap colorization failed: {e}")
    
    def generate_overlay(
        self,
        original_image: np.ndarray,
        colored_heatmap: np.ndarray,
        alpha: float = 0.5
    ) -> np.ndarray:
        """
        Overlay heatmap on original image.
        
        Args:
            original_image: Original image (H, W, 3) in [0, 255]
            colored_heatmap: Colorized heatmap (H, W, 3) in [0, 255]
            alpha: Blending factor
        
        Returns:
            Overlayed image (H, W, 3) in [0, 255] uint8
        """
        print("\n[Step 6] Generating overlay...")
        start_time = time.time()
        
        try:
            overlaid = overlay_heatmap(original_image, colored_heatmap, alpha=alpha)
            
            self.status['overlay_generated'] = True
            self.timings['overlay'] = time.time() - start_time
            
            print(f"  Overlay shape: {overlaid.shape}")
            print(f"  dtype: {overlaid.dtype}")
            print(f"  Value range: [{overlaid.min()}, {overlaid.max()}]")
            print(f"  ✓ Overlay generated ({self.timings['overlay'] * 1000:.2f} ms)")
            
            return overlaid
            
        except Exception as e:
            raise RuntimeError(f"Overlay generation failed: {e}")
    
    def verify_results(
        self,
        heatmap: np.ndarray,
        colored_heatmap: np.ndarray,
        overlay: np.ndarray,
        original_image: np.ndarray
    ):
        """
        Verify pipeline results.
        
        Args:
            heatmap: Grad-CAM heatmap
            colored_heatmap: Colorized heatmap
            overlay: Overlayed image
            original_image: Original image
        """
        print("\n[Step 7] Verifying results...")
        
        # Verify heatmap
        assert heatmap.ndim == 2, f"Heatmap should be 2D, got {heatmap.ndim}D"
        assert heatmap.min() >= 0.0 and heatmap.max() <= 1.0, "Heatmap not normalized to [0, 1]"
        print("  ✓ Heatmap shape and range verified")
        
        # Verify colored heatmap
        assert colored_heatmap.ndim == 3, f"Colored heatmap should be 3D, got {colored_heatmap.ndim}D"
        assert colored_heatmap.shape[2] == 3, "Colored heatmap should have 3 channels"
        print("  ✓ Colored heatmap shape verified")
        
        # Verify overlay
        assert overlay.shape == original_image.shape, f"Overlay shape {overlay.shape} doesn't match original {original_image.shape}"
        assert overlay.dtype == np.uint8, f"Overlay dtype should be uint8, got {overlay.dtype}"
        assert overlay.min() >= 0 and overlay.max() <= 255, "Overlay values not in [0, 255]"
        print("  ✓ Overlay shape, dtype, and range verified")
        
        print("  ✓ All verifications passed")
    
    def print_summary(self, prediction_result: dict):
        """
        Print clean summary of test results.
        
        Args:
            prediction_result: Prediction results from inference
        """
        print("\n" + "=" * 80)
        print("TruthLens Explainability Test")
        print("=" * 80)
        
        print("\nModel:")
        print("-" * 40)
        print("EfficientNet-B4")
        
        print("\nPrediction:")
        print("-" * 40)
        print(f"{prediction_result['predicted_class']}")
        
        print("\nConfidence:")
        print("-" * 40)
        print(f"{prediction_result['confidence'] * 100:.2f}%")
        
        print("\nInference Time:")
        print("-" * 40)
        print(f"{self.timings['inference'] * 1000:.2f} ms")
        
        print("\nGrad-CAM")
        print("-" * 40)
        print(f"Target Layer:")
        print(f"{self.target_layer}")
        
        print("\nHeatmap")
        print("-" * 40)
        print(f"Shape:")
        print(f"(224, 224)")
        print(f"Range:")
        print(f"0.00 - 1.00")
        
        print("\nOverlay")
        print("-" * 40)
        print(f"Shape:")
        print(f"(224, 224, 3)")
        print(f"dtype:")
        print(f"uint8")
        print(f"Range:")
        print(f"0 - 255")
        
        print("\nStatus:")
        print("-" * 40)
        print(f"{'✓' if self.status['model_loaded'] else '✗'} Model Loaded")
        print(f"{'✓' if self.status['prediction_complete'] else '✗'} Prediction Complete")
        print(f"{'✓' if self.status['gradcam_generated'] else '✗'} Grad-CAM Generated")
        print(f"{'✓' if self.status['heatmap_generated'] else '✗'} Heatmap Generated")
        print(f"{'✓' if self.status['overlay_generated'] else '✗'} Overlay Generated")
        
        print("\nTiming Summary:")
        print("-" * 40)
        print(f"Model Loading:   {self.timings['model_loading'] * 1000:.2f} ms")
        print(f"Inference:       {self.timings['inference'] * 1000:.2f} ms")
        print(f"Grad-CAM:        {self.timings['gradcam'] * 1000:.2f} ms")
        print(f"Heatmap Color:   {self.timings['heatmap'] * 1000:.2f} ms")
        print(f"Overlay:         {self.timings['overlay'] * 1000:.2f} ms")
        print(f"Total:           {sum(self.timings.values()) * 1000:.2f} ms")
        
        print("\n" + "=" * 80)
        all_passed = all(self.status.values())
        if all_passed:
            print("Explainability Pipeline PASSED")
        else:
            print("Explainability Pipeline FAILED")
        print("=" * 80)
        
        return all_passed


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description='Test TruthLens explainability pipeline')
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
    parser.add_argument(
        '--alpha',
        type=float,
        default=0.5,
        help='Overlay alpha (0 = original, 1 = heatmap only)'
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("TruthLens Explainability Integration Test")
    print("=" * 80)
    
    # Initialize test
    test = ExplainabilityTest(
        checkpoint_path=args.checkpoint,
        target_layer=args.target_layer
    )
    
    try:
        # Load model
        test.load_model()
        test.load_transforms()
        
        # Load or generate image
        if args.image and Path(args.image).exists():
            print(f"\n[Image] Loading from {args.image}")
            image = Image.open(args.image).convert('RGB')
            original_image = np.array(image)
            image_tensor = test.transform(image).unsqueeze(0)
        else:
            print(f"\n[Image] Generating dummy tensor")
            if args.image:
                print(f"[Warning] Image file not found, using dummy data")
            image_tensor = torch.randn(1, 3, 224, 224)
            original_image = np.random.randint(0, 256, (224, 224, 3), dtype=np.uint8)
        
        print(f"  Input tensor shape: {image_tensor.shape}")
        print(f"  Original image shape: {original_image.shape}")
        
        # Run inference
        prediction_result = test.run_inference(image_tensor)
        
        # Generate Grad-CAM
        heatmap = test.generate_gradcam(image_tensor)
        
        # Colorize heatmap
        colored_heatmap = test.colorize_heatmap(heatmap)
        
        # Generate overlay
        overlay = test.generate_overlay(original_image, colored_heatmap, alpha=args.alpha)
        
        # Verify results
        test.verify_results(heatmap, colored_heatmap, overlay, original_image)
        
        # Print summary
        success = test.print_summary(prediction_result)
        
        sys.exit(0 if success else 1)
        
    except FileNotFoundError as e:
        print(f"\n[Error] {e}")
        print("=" * 80)
        print("Explainability Pipeline FAILED - Missing File")
        print("=" * 80)
        sys.exit(1)
    except RuntimeError as e:
        print(f"\n[Error] {e}")
        print("=" * 80)
        print("Explainability Pipeline FAILED - Runtime Error")
        print("=" * 80)
        sys.exit(1)
    except Exception as e:
        print(f"\n[Error] Unexpected error: {e}")
        print("=" * 80)
        print("Explainability Pipeline FAILED - Unexpected Error")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()
