"""
TruthLens Dataset Manager
========================
Main module for automatic dataset management.
"""

from pathlib import Path
from typing import Dict, List, Optional
import json
import csv
from datetime import datetime

from .downloaders import (
    FFHQDownloader, COCODownloader, OpenImagesDownloader,
    GenImageDownloader, FaceForensicsDownloader, DFDCDownloader
)
from .organizers import DatasetOrganizer


class DatasetManager:
    """Main dataset manager for TruthLens."""
    
    def __init__(self, base_dir: str = "TruthLensDataset", resize_size: tuple = (512, 512)):
        """
        Initialize dataset manager.
        
        Args:
            base_dir: Base directory for TruthLensDataset
            resize_size: Target size for image resizing
        """
        self.base_dir = Path(base_dir)
        self.resize_size = resize_size
        self.organizer = DatasetOrganizer(base_dir, resize_size)
        
        # Dataset downloader mapping
        self.downloaders = {
            "ffhq": FFHQDownloader,
            "coco": COCODownloader,
            "openimages": OpenImagesDownloader,
            "genimage": GenImageDownloader,
            "faceforensics": FaceForensicsDownloader,
            "dfdc": DFDCDownloader
        }
    
    def setup_structure(self) -> None:
        """Create TruthLens dataset directory structure."""
        self.organizer.create_structure()
    
    def download_dataset(self, dataset_name: str) -> Dict[str, any]:
        """
        Download a specific dataset.
        
        Args:
            dataset_name: Name of dataset to download
        
        Returns:
            Dict with download results
        """
        dataset_name = dataset_name.lower()
        
        if dataset_name not in self.downloaders:
            raise ValueError(f"Unknown dataset: {dataset_name}. Available: {list(self.downloaders.keys())}")
        
        downloader_class = self.downloaders[dataset_name]
        downloader = downloader_class(str(self.base_dir), self.resize_size)
        
        print(f"[DatasetManager] Downloading {dataset_name}...")
        results = downloader.download()
        
        return results
    
    def download_all(self) -> Dict[str, List[Dict]]:
        """
        Download all available datasets.
        
        Returns:
            Dict with results for all datasets
        """
        results = {}
        
        for dataset_name in self.downloaders.keys():
            print(f"\n[DatasetManager] Processing {dataset_name}...")
            try:
                result = self.download_dataset(dataset_name)
                results[dataset_name] = result
            except Exception as e:
                print(f"[DatasetManager] Error downloading {dataset_name}: {e}")
                results[dataset_name] = {"error": str(e)}
        
        return results
    
    def organize_imported_dataset(self, source_dir: str, content_type: str,
                                   category: str = None, generator: str = None) -> Dict[str, any]:
        """
        Organize an imported dataset into TruthLens structure.
        
        Args:
            source_dir: Source directory containing images
            content_type: "real" or "ai"
            category: Category for real images
            generator: Generator for AI images
        
        Returns:
            Dict with organization results
        """
        source_path = Path(source_dir)
        if not source_path.exists():
            raise ValueError(f"Source directory does not exist: {source_dir}")
        
        return self.organizer.organize_dataset(source_path, content_type, category, generator)
    
    def clean_dataset(self, directory: str = None) -> Dict[str, any]:
        """
        Clean dataset by removing duplicates and corrupted files.
        
        Args:
            directory: Directory to clean (uses base_dir if None)
        
        Returns:
            Dict with cleaning results
        """
        target_dir = Path(directory) if directory else self.base_dir
        return self.organizer.clean_dataset(target_dir)
    
    def get_statistics(self) -> Dict[str, any]:
        """
        Generate dataset statistics.
        
        Returns:
            Dict with dataset statistics
        """
        print("[DatasetManager] Generating statistics...")
        
        stats = {
            "total_files": 0,
            "by_content_type": {"real": 0, "ai": 0},
            "by_category": {},
            "by_generator": {},
            "by_source": {}
        }
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        
        # Count files in images directory
        images_dir = self.base_dir / "images"
        if images_dir.exists():
            for content_type in ["real", "ai"]:
                content_dir = images_dir / content_type
                if content_dir.exists():
                    for image_path in content_dir.rglob('*'):
                        if image_path.suffix.lower() in image_extensions:
                            stats["total_files"] += 1
                            stats["by_content_type"][content_type] += 1
                            
                            # Get category or generator from path
                            path_parts = image_path.relative_to(content_dir).parts
                            if path_parts:
                                key = path_parts[0]
                                if content_type == "real":
                                    stats["by_category"][key] = stats["by_category"].get(key, 0) + 1
                                else:
                                    stats["by_generator"][key] = stats["by_generator"].get(key, 0) + 1
        
        # Count files in videos directory
        videos_dir = self.base_dir / "videos"
        if videos_dir.exists():
            for content_type in ["real", "ai"]:
                content_dir = videos_dir / content_type
                if content_dir.exists():
                    for video_path in content_dir.rglob('*'):
                        if video_path.suffix.lower() in {'.mp4', '.avi', '.mov', '.mkv'}:
                            stats["total_files"] += 1
                            stats["by_content_type"][content_type] += 1
        
        return stats
    
    def generate_benchmark_csv(self, output_path: str = "benchmark.csv") -> str:
        """
        Generate benchmark.csv file.
        
        Args:
            output_path: Path to save benchmark.csv
        
        Returns:
            Path to generated file
        """
        print(f"[DatasetManager] Generating benchmark.csv...")
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['filename', 'label', 'content_type', 'generator', 'source_dataset'])
            
            # Process images
            images_dir = self.base_dir / "images"
            if images_dir.exists():
                for content_type in ["real", "ai"]:
                    content_dir = images_dir / content_type
                    if content_dir.exists():
                        for image_path in content_dir.rglob('*'):
                            if image_path.suffix.lower() in image_extensions:
                                # Extract metadata from path
                                path_parts = image_path.relative_to(content_dir).parts
                                category_or_generator = path_parts[0] if path_parts else "unknown"
                                source_dataset = self._infer_source_dataset(image_path.name)
                                
                                label = content_type  # real or ai
                                generator = category_or_generator if content_type == "ai" else ""
                                category = category_or_generator if content_type == "real" else ""
                                
                                writer.writerow([
                                    image_path.name,
                                    label,
                                    content_type,
                                    generator,
                                    source_dataset
                                ])
        
        print(f"[DatasetManager] benchmark.csv saved to {output_file}")
        return str(output_file)
    
    def _infer_source_dataset(self, filename: str) -> str:
        """
        Infer source dataset from filename.
        
        Args:
            filename: Image filename
        
        Returns:
            Inferred source dataset name
        """
        filename_lower = filename.lower()
        
        # Heuristics for source detection
        if "ffhq" in filename_lower:
            return "FFHQ"
        elif "coco" in filename_lower:
            return "COCO"
        elif "openimages" in filename_lower:
            return "OpenImages"
        elif "midjourney" in filename_lower:
            return "GenImage"
        elif "sdxl" in filename_lower:
            return "GenImage"
        elif "faceforensics" in filename_lower:
            return "FaceForensics++"
        elif "dfdc" in filename_lower:
            return "DFDC"
        else:
            return "unknown"
    
    def generate_report(self, output_dir: str = "reports") -> Dict[str, str]:
        """
        Generate dataset report (JSON and CSV).
        
        Args:
            output_dir: Directory to save reports
        
        Returns:
            Dict with paths to generated reports
        """
        print(f"[DatasetManager] Generating dataset reports...")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Get statistics
        stats = self.get_statistics()
        stats["generated_at"] = datetime.now().isoformat()
        
        # Generate JSON report
        json_path = output_path / "dataset_report.json"
        with open(json_path, 'w') as f:
            json.dump(stats, f, indent=2)
        
        # Generate CSV report
        csv_path = output_path / "dataset_report.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['metric', 'value'])
            writer.writerow(['total_files', stats['total_files']])
            writer.writerow(['real_files', stats['by_content_type']['real']])
            writer.writerow(['ai_files', stats['by_content_type']['ai']])
            
            for category, count in stats['by_category'].items():
                writer.writerow([f'category_{category}', count])
            
            for generator, count in stats['by_generator'].items():
                writer.writerow([f'generator_{generator}', count])
        
        print(f"[DatasetManager] Reports saved to {output_path}")
        
        return {
            "json_report": str(json_path),
            "csv_report": str(csv_path)
        }
    
    def full_pipeline(self, datasets: List[str] = None) -> Dict[str, any]:
        """
        Run full dataset management pipeline.
        
        Args:
            datasets: List of datasets to process (None for all)
        
        Returns:
            Dict with pipeline results
        """
        print("[DatasetManager] Starting full pipeline...")
        
        results = {
            "structure_created": False,
            "datasets_downloaded": {},
            "datasets_cleaned": {},
            "statistics": {},
            "reports": {}
        }
        
        # Create structure
        self.setup_structure()
        results["structure_created"] = True
        
        # Download datasets
        if datasets:
            for dataset in datasets:
                try:
                    download_result = self.download_dataset(dataset)
                    results["datasets_downloaded"][dataset] = download_result
                except Exception as e:
                    results["datasets_downloaded"][dataset] = {"error": str(e)}
        else:
            results["datasets_downloaded"] = self.download_all()
        
        # Clean datasets
        clean_result = self.clean_dataset()
        results["datasets_cleaned"] = clean_result
        
        # Generate statistics
        stats = self.get_statistics()
        results["statistics"] = stats
        
        # Generate reports
        reports = self.generate_report()
        results["reports"] = reports
        
        # Generate benchmark CSV
        benchmark_csv = self.generate_benchmark_csv()
        results["benchmark_csv"] = benchmark_csv
        
        print("[DatasetManager] Pipeline complete!")
        return results
