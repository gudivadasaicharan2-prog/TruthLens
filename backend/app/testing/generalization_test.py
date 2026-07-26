"""
Generalization Testing Pipeline for TruthLens
=============================================
Test model on arbitrary image folders for generalization assessment.
"""

import sys
from pathlib import Path
import json
import csv
import time
from typing import List, Tuple
from PIL import Image
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.training.dataloader import get_default_transforms
from app.training.models import create_model
from app.training.utils import get_device


class GeneralizationDataset(Dataset):
    """
    Dataset for generalization testing on arbitrary image folders.
    """
    
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
    
    def __init__(self, image_folder: str, transform):
        """
        Initialize dataset.
        
        Args:
            image_folder: Path to folder containing images
            transform: Image transforms to apply
        """
        self.image_folder = Path(image_folder)
        self.transform = transform
        
        # Recursively find all supported images
        self.image_paths = self._discover_images()
        
        if len(self.image_paths) == 0:
            raise ValueError(f"No supported images found in {image_folder}")
        
        print(f"[GeneralizationDataset] Found {len(self.image_paths)} images")
    
    def _discover_images(self) -> List[Path]:
        """Recursively discover all supported image files."""
        image_paths = []
        for path in self.image_folder.rglob('*'):
            if path.is_file() and path.suffix.lower() in self.SUPPORTED_FORMATS:
                image_paths.append(path)
        return sorted(image_paths)
    
    def __len__(self) -> int:
        return len(self.image_paths)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, str]:
        """
        Get image and its filename.
        
        Args:
            idx: Index of image
        
        Returns:
            Tuple of (image_tensor, filename)
        """
        image_path = self.image_paths[idx]
        
        # Load image
        image = Image.open(image_path).convert('RGB')
        
        # Apply transforms
        if self.transform:
            image = self.transform(image)
        
        return image, str(image_path.name)


def load_checkpoint(checkpoint_path: str, model: nn.Module, device: torch.device):
    """
    Load model from checkpoint.
    
    Args:
        checkpoint_path: Path to checkpoint file
        model: Model to load weights into
        device: Device to load model on
    
    Returns:
        Checkpoint dictionary
    """
    checkpoint = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(device)
    model.eval()
    print(f"[Generalization] Loaded checkpoint from {checkpoint_path}")
    print(f"  Epoch: {checkpoint['epoch']}")
    print(f"  Score: {checkpoint['score']:.4f}")
    return checkpoint


def run_inference(
    model: nn.Module,
    dataloader: DataLoader,
    device: torch.device,
    class_names: List[str] = ['Real', 'AI']
) -> List[dict]:
    """
    Run batch-based inference on dataset.
    
    Args:
        model: Model to run inference with
        dataloader: DataLoader for images
        device: Device to run inference on
        class_names: List of class names
    
    Returns:
        List of result dictionaries
    """
    results = []
    
    with torch.no_grad():
        for images, filenames in tqdm(dataloader, desc="Running inference"):
            # Start timing
            start_time = time.time()
            
            # Move to device
            images = images.to(device)
            
            # Run inference
            outputs = model(images)
            probabilities = torch.softmax(outputs, dim=1)
            predictions = torch.argmax(outputs, dim=1)
            confidences, _ = torch.max(probabilities, dim=1)
            
            # End timing
            inference_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Process results
            for i in range(len(filenames)):
                result = {
                    'filename': filenames[i],
                    'predicted_class': class_names[predictions[i].item()],
                    'confidence': confidences[i].item(),
                    'probability_real': probabilities[i, 0].item(),
                    'probability_ai': probabilities[i, 1].item(),
                    'inference_time_ms': inference_time / len(filenames)  # Per-image time
                }
                results.append(result)
    
    return results


def save_results_csv(results: List[dict], save_path: str):
    """
    Save results to CSV file.
    
    Args:
        results: List of result dictionaries
        save_path: Path to save CSV
    """
    fieldnames = ['filename', 'predicted_class', 'confidence', 
                  'probability_real', 'probability_ai', 'inference_time_ms']
    
    with open(save_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"[Generalization] Saved results CSV to {save_path}")


def save_summary_json(results: List[dict], save_path: str):
    """
    Save summary statistics to JSON file.
    
    Args:
        results: List of result dictionaries
        save_path: Path to save JSON
    """
    total_images = len(results)
    predicted_real = sum(1 for r in results if r['predicted_class'] == 'Real')
    predicted_ai = sum(1 for r in results if r['predicted_class'] == 'AI')
    avg_confidence = np.mean([r['confidence'] for r in results])
    avg_inference_time = np.mean([r['inference_time_ms'] for r in results])
    
    summary = {
        'total_images': total_images,
        'predicted_real': predicted_real,
        'predicted_ai': predicted_ai,
        'average_confidence': float(avg_confidence),
        'average_inference_time_ms': float(avg_inference_time),
        'percentage_real': float(predicted_real / total_images * 100),
        'percentage_ai': float(predicted_ai / total_images * 100)
    }
    
    with open(save_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"[Generalization] Saved summary JSON to {save_path}")
    return summary


def print_summary(summary: dict):
    """
    Print summary to console.
    
    Args:
        summary: Summary dictionary
    """
    print("\n" + "=" * 80)
    print("GENERALIZATION TEST SUMMARY")
    print("=" * 80)
    print(f"Total Images:           {summary['total_images']}")
    print(f"Predicted Real:         {summary['predicted_real']} ({summary['percentage_real']:.2f}%)")
    print(f"Predicted AI:          {summary['predicted_ai']} ({summary['percentage_ai']:.2f}%)")
    print(f"Average Confidence:     {summary['average_confidence']:.4f}")
    print(f"Average Inference Time: {summary['average_inference_time_ms']:.2f} ms")
    print("=" * 80)


def main():
    """Main generalization testing pipeline."""
    
    # Paths
    checkpoint_path = "experiments/cifake_efficientnet_b4_baseline/checkpoints/latest_checkpoint.pth"
    image_folder = "TruthLensGeneralization"
    output_dir = "experiments/generalization"
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print("TruthLens Generalization Testing Pipeline")
    print("=" * 80)
    
    # Check if image folder exists
    if not Path(image_folder).exists():
        print(f"\n[Error] Image folder not found: {image_folder}")
        print("Please create the folder and add images to test.")
        return
    
    # Get device
    device = get_device()
    
    # Load model
    print("\n[Step 1] Loading model...")
    model = create_model(
        architecture='efficientnet_b4',
        num_classes=2,
        pretrained=False,
        dropout=0.3
    )
    
    # Load checkpoint
    load_checkpoint(checkpoint_path, model, device)
    
    # Get validation transforms
    print("\n[Step 2] Preparing transforms...")
    _, val_transform = get_default_transforms(image_size=224, augment=False)
    
    # Create dataset
    print("\n[Step 3] Loading images from folder...")
    dataset = GeneralizationDataset(image_folder, val_transform)
    
    # Create dataloader
    dataloader = DataLoader(
        dataset,
        batch_size=32,
        shuffle=False,
        num_workers=0,
        pin_memory=False
    )
    
    # Run inference
    print("\n[Step 4] Running inference...")
    results = run_inference(model, dataloader, device)
    
    # Save results
    print("\n[Step 5] Saving results...")
    save_results_csv(results, str(output_path / 'results.csv'))
    summary = save_summary_json(results, str(output_path / 'summary.json'))
    
    # Print summary
    print("\n[Step 6] Final summary...")
    print_summary(summary)
    
    print(f"\n[Generalization] Complete! Results saved to: {output_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()
