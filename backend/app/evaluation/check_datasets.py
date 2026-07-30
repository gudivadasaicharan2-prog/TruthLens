"""
Dataset Verification Utility for TruthLens Evaluation
===================================================
Verifies evaluation datasets and generates status reports.
"""

import sys
from pathlib import Path
import json
from typing import Dict, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Supported image formats
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}


def count_images_recursive(folder_path: Path) -> int:
    """
    Count images recursively in a folder.
    
    Args:
        folder_path: Path to folder to scan
    
    Returns:
        Number of supported images found
    """
    if not folder_path.exists():
        return 0
    
    count = 0
    for path in folder_path.rglob('*'):
        if path.is_file() and path.suffix.lower() in SUPPORTED_FORMATS:
            count += 1
    
    return count


def check_dataset(dataset_name: str, dataset_type: str, base_path: Path) -> Dict:
    """
    Check status of a single dataset.
    
    Args:
        dataset_name: Name of dataset
        dataset_type: Type of dataset ('ai' or 'real')
        base_path: Base path to evaluation folder
    
    Returns:
        Dictionary with dataset status
    """
    dataset_path = base_path / dataset_name.lower()
    content_folder = dataset_path / dataset_type
    
    exists = dataset_path.exists() and content_folder.exists()
    num_images = count_images_recursive(content_folder) if exists else 0
    
    status = "Present" if exists and num_images > 0 else "Missing"
    
    return {
        'name': dataset_name,
        'type': dataset_type,
        'status': status,
        'exists': exists,
        'num_images': num_images,
        'path': str(content_folder)
    }


def load_datasets_metadata(metadata_path: Path) -> List[Dict]:
    """
    Load datasets metadata from JSON file.
    
    Args:
        metadata_path: Path to datasets.json
    
    Returns:
        List of dataset metadata
    """
    if not metadata_path.exists():
        return []
    
    with open(metadata_path, 'r') as f:
        data = json.load(f)
    
    return data.get('datasets', [])


def update_datasets_metadata(metadata_path: Path, results: List[Dict]):
    """
    Update datasets metadata with current status.
    
    Args:
        metadata_path: Path to datasets.json
        results: List of dataset check results
    """
    # Load existing metadata
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            data = json.load(f)
    else:
        data = {'datasets': []}
    
    # Update with current results
    for result in results:
        for dataset in data['datasets']:
            if dataset['name'] == result['name']:
                dataset['status'] = 'present' if result['exists'] and result['num_images'] > 0 else 'pending'
                dataset['downloaded'] = result['exists'] and result['num_images'] > 0
                dataset['num_images'] = result['num_images']
                break
    
    # Save updated metadata
    with open(metadata_path, 'w') as f:
        json.dump(data, f, indent=2)


def print_report(results: List[Dict]):
    """
    Print dataset status report.
    
    Args:
        results: List of dataset check results
    """
    print("=" * 80)
    print("TruthLens Evaluation Dataset Report")
    print("=" * 80)
    print()
    
    for result in results:
        print(f"{result['name']}")
        print(f"Status: {result['status']}")
        print(f"Images: {result['num_images']}")
        print()
    
    print("=" * 80)


def main():
    """Main dataset verification routine."""
    # Paths
    base_path = Path("TruthLensDataset/evaluation")
    metadata_path = base_path / "metadata" / "datasets.json"
    
    # Dataset configurations
    datasets = [
        {"name": "GenImage", "type": "ai"},
        {"name": "DiffusionDB", "type": "ai"},
        {"name": "COCO", "type": "real"},
        {"name": "RAISE", "type": "real"}
    ]
    
    # Check each dataset
    results = []
    for dataset in datasets:
        result = check_dataset(dataset['name'], dataset['type'], base_path)
        results.append(result)
    
    # Print report
    print_report(results)
    
    # Update metadata
    update_datasets_metadata(metadata_path, results)
    
    print(f"Metadata updated: {metadata_path}")


if __name__ == "__main__":
    main()
