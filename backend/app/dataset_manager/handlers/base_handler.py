"""
Base Dataset Handler
====================
Abstract base class for dataset organization handlers.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import csv
import shutil
from collections import defaultdict

from ..organizers import DuplicateDetector, CorruptionDetector


class BaseDatasetHandler(ABC):
    """
    Abstract base class for dataset organization handlers.
    
    Provides common functionality for organizing datasets into TruthLens structure.
    Subclasses implement dataset-specific logic for structure detection and mapping.
    """
    
    def __init__(
        self,
        source_dir: str,
        target_dir: str = "TruthLensDataset",
        force: bool = False
    ):
        """
        Initialize dataset handler.
        
        Args:
            source_dir: Path to source dataset directory
            target_dir: Target TruthLensDataset directory
            force: Force overwrite existing data
        """
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir)
        self.force = force
        self.duplicate_detector = DuplicateDetector()
        self.corruption_detector = CorruptionDetector()
        
        # Statistics
        self.stats = {
            "total_images_processed": 0,
            "total_images_copied": 0,
            "duplicates_skipped": 0,
            "corrupted_skipped": 0,
            "failed_copies": 0,
            "by_split": {"train": 0, "val": 0},
            "by_label": {"real": 0, "ai": 0},
            "by_generator": defaultdict(lambda: {"train": 0, "val": 0})
        }
    
    @abstractmethod
    def detect_structure(self) -> Dict[str, any]:
        """
        Detect the structure of the source dataset.
        
        Returns:
            Dict with detected structure information
        """
        pass
    
    @abstractmethod
    def map_sample_metadata(self, sample_path: Path, context: Dict) -> Dict[str, str]:
        """
        Map a sample to its metadata.
        
        Args:
            sample_path: Path to the sample file
            context: Additional context from structure detection
        
        Returns:
            Dict with metadata fields: label, generator, split, source_dataset
        """
        pass
    
    @abstractmethod
    def get_source_dataset_name(self) -> str:
        """
        Get the source dataset name.
        
        Returns:
            Source dataset identifier
        """
        pass
    
    def validate_target_directory(self) -> Dict[str, any]:
        """
        Validate target directory before organization.
        
        Returns:
            Dict with validation results
        """
        print(f"[{self.__class__.__name__}] Validating target directory...")
        
        result = {
            "valid": True,
            "existing_data": False,
            "existing_files": 0,
            "warnings": []
        }
        
        if not self.target_dir.exists():
            print("  Target directory does not exist, will be created")
            return result
        
        images_dir = self.target_dir / "images"
        if images_dir.exists():
            image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
            existing_files = sum(1 for f in images_dir.rglob('*') if f.suffix.lower() in image_extensions)
            
            if existing_files > 0:
                result["existing_data"] = True
                result["existing_files"] = existing_files
                
                if not self.force:
                    result["valid"] = False
                    result["warnings"].append(
                        f"Target directory contains {existing_files} existing images. "
                        "Use --force flag to overwrite or specify a different target directory."
                    )
                    print(f"  WARNING: Found {existing_files} existing images in target directory")
                    print("  Use --force flag to overwrite or specify a different target directory")
                else:
                    result["warnings"].append(
                        f"Target directory contains {existing_files} existing images. "
                        "Proceeding with --force flag (may overwrite existing data)."
                    )
                    print(f"  WARNING: Found {existing_files} existing images, proceeding with --force flag")
        
        return result
    
    def get_target_path(self, metadata: Dict[str, str]) -> Path:
        """
        Get target path for a sample based on metadata.
        
        Args:
            metadata: Sample metadata dict
        
        Returns:
            Target path for the sample
        """
        label = metadata['label']
        split = metadata['split']
        generator = metadata.get('generator', '')
        
        if label == 'real':
            return self.target_dir / "images" / "real" / split
        else:
            if generator:
                return self.target_dir / "images" / "ai" / generator / split
            else:
                return self.target_dir / "images" / "ai" / "unknown" / split
    
    def copy_sample(
        self,
        source_path: Path,
        target_path: Path,
        metadata: Dict[str, str],
        sample_index: int = 0,
        total_samples: int = 0
    ) -> bool:
        """
        Copy a sample to target directory with validation.
        
        Validation Flow:
        1. Duplicate Detection: Uses DuplicateDetector.is_duplicate() which:
           - Calculates MD5 hash using existing calculate_md5() method
           - Checks internal cache of seen hashes (O(1) lookup)
           - Returns True if hash seen before (duplicate), False otherwise
           - Adds new hashes to cache for future checks
        2. Corruption Detection: Uses CorruptionDetector.is_corrupted() which:
           - Verifies file can be opened and loaded by PIL
           - Checks file size and existence
           - Returns True if corrupted, False otherwise
        
        Args:
            source_path: Source file path
            target_path: Target directory path
            metadata: Sample metadata
            sample_index: Current sample index for logging
            total_samples: Total samples for logging
        
        Returns:
            True if copied successfully, False otherwise
        """
        label = metadata.get('label', 'unknown')
        split = metadata.get('split', 'unknown')
        
        print(f"[{self.__class__.__name__}] Processing sample {sample_index}/{total_samples}")
        print(f"  Source: {source_path}")
        print(f"  Label: {label}")
        print(f"  Split: {split}")
        print(f"  Target: {target_path}")
        
        # Check for duplicates using MD5 hash cache
        try:
            if self.duplicate_detector.is_duplicate(source_path):
                self.stats["duplicates_skipped"] += 1
                print(f"  Result: SKIPPED (duplicate)")
                return False
        except Exception as e:
            print(f"  ERROR: Duplicate detection failed: {e}")
            import traceback
            traceback.print_exc()
            self.stats["failed_copies"] += 1
            return False
        
        # Check for corruption using PIL verification
        try:
            if self.corruption_detector.is_corrupted(source_path):
                self.stats["corrupted_skipped"] += 1
                print(f"  Result: SKIPPED (corrupted)")
                return False
        except Exception as e:
            print(f"  ERROR: Corruption detection failed: {e}")
            import traceback
            traceback.print_exc()
            self.stats["failed_copies"] += 1
            return False
        
        # Create target directory
        try:
            target_path.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            print(f"  ERROR: Permission denied creating directory {target_path}: {e}")
            self.stats["failed_copies"] += 1
            return False
        except OSError as e:
            print(f"  ERROR: Failed to create directory {target_path}: {e}")
            self.stats["failed_copies"] += 1
            return False
        
        # Handle name conflicts
        target_file = target_path / source_path.name
        counter = 1
        try:
            while target_file.exists():
                stem = source_path.stem
                suffix = source_path.suffix
                target_file = target_path / f"{stem}_{counter}{suffix}"
                counter += 1
        except Exception as e:
            print(f"  ERROR: Name conflict handling failed: {e}")
            self.stats["failed_copies"] += 1
            return False
        
        # Copy file
        try:
            shutil.copy2(source_path, target_file)
            self.stats["total_images_copied"] += 1
            print(f"  Result: COPIED successfully")
            return True
        except PermissionError as e:
            print(f"  ERROR: Permission denied copying {source_path.name}: {e}")
            self.stats["failed_copies"] += 1
        except OSError as e:
            if e.errno == 28:
                print(f"  ERROR: No disk space left while copying {source_path.name}")
                self.stats["failed_copies"] += 1
            else:
                print(f"  ERROR: OS error copying {source_path.name}: {e}")
                self.stats["failed_copies"] += 1
        except Exception as e:
            print(f"  ERROR: Unexpected error copying {source_path.name}: {e}")
            import traceback
            traceback.print_exc()
            self.stats["failed_copies"] += 1
        
        return False
    
    def generate_metadata_csv(self, samples: List[Dict[str, str]]) -> str:
        """
        Generate metadata.csv from sample list.
        
        Args:
            samples: List of sample metadata dicts
        
        Returns:
            Path to generated metadata.csv
        """
        metadata_path = self.target_dir / "metadata.csv"
        
        with open(metadata_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['file_path', 'label', 'generator', 'split', 'source_dataset'])
            
            for sample in samples:
                writer.writerow([
                    sample['file_path'],
                    sample['label'],
                    sample.get('generator', ''),
                    sample['split'],
                    sample['source_dataset']
                ])
        
        print(f"[{self.__class__.__name__}] Generated metadata.csv with {len(samples)} entries")
        return str(metadata_path)
    
    def validate_metadata(self, metadata_path: str = "metadata.csv") -> Dict[str, any]:
        """
        Validate generated metadata.csv.
        
        Args:
            metadata_path: Path to metadata.csv file
        
        Returns:
            Dict with validation results
        """
        print(f"[{self.__class__.__name__}] Validating metadata.csv...")
        
        metadata_file = Path(metadata_path)
        if not metadata_file.exists():
            return {
                "valid": False,
                "error": f"Metadata file not found: {metadata_path}"
            }
        
        result = {
            "valid": True,
            "total_entries": 0,
            "missing_files": [],
            "invalid_labels": [],
            "invalid_splits": [],
            "duplicate_entries": [],
            "warnings": []
        }
        
        valid_labels = {"real", "ai"}
        valid_splits = {"train", "val"}
        seen_entries = set()
        
        try:
            with open(metadata_file, 'r', newline='') as f:
                reader = csv.DictReader(f)
                
                for row_num, row in enumerate(reader, start=2):
                    result["total_entries"] += 1
                    
                    entry_key = (row.get('file_path'), row.get('label'), row.get('split'))
                    if entry_key in seen_entries:
                        result["duplicate_entries"].append({
                            "row": row_num,
                            "file_path": row.get('file_path'),
                            "reason": "Duplicate entry"
                        })
                    seen_entries.add(entry_key)
                    
                    file_path = self.target_dir / row.get('file_path', '')
                    if not file_path.exists():
                        result["missing_files"].append({
                            "row": row_num,
                            "file_path": row.get('file_path'),
                            "reason": "File does not exist"
                        })
                    
                    label = row.get('label', '').lower()
                    if label not in valid_labels:
                        result["invalid_labels"].append({
                            "row": row_num,
                            "file_path": row.get('file_path'),
                            "label": label,
                            "reason": f"Invalid label, must be one of {valid_labels}"
                        })
                    
                    split = row.get('split', '').lower()
                    if split not in valid_splits:
                        result["invalid_splits"].append({
                            "row": row_num,
                            "file_path": row.get('file_path'),
                            "split": split,
                            "reason": f"Invalid split, must be one of {valid_splits}"
                        })
        
        except Exception as e:
            return {
                "valid": False,
                "error": f"Error reading metadata file: {e}"
            }
        
        if result["missing_files"] or result["invalid_labels"] or result["invalid_splits"]:
            result["valid"] = False
        
        if result["duplicate_entries"]:
            result["warnings"].append(f"Found {len(result['duplicate_entries'])} duplicate entries")
        
        print(f"  Total entries: {result['total_entries']}")
        print(f"  Missing files: {len(result['missing_files'])}")
        print(f"  Invalid labels: {len(result['invalid_labels'])}")
        print(f"  Invalid splits: {len(result['invalid_splits'])}")
        print(f"  Duplicate entries: {len(result['duplicate_entries'])}")
        print(f"  Valid: {result['valid']}")
        
        return result
    
    def generate_summary_report(self) -> str:
        """
        Generate summary report of organization process.
        
        Returns:
            Path to generated report file
        """
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append(f"{self.__class__.__name__} Organization Report")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        report_lines.append("Source Directory:")
        report_lines.append(f"  {self.source_dir}")
        report_lines.append("")
        
        report_lines.append("Target Directory:")
        report_lines.append(f"  {self.target_dir}")
        report_lines.append("")
        
        report_lines.append("Statistics:")
        report_lines.append(f"  Total images processed: {self.stats['total_images_processed']}")
        report_lines.append(f"  Total images copied: {self.stats['total_images_copied']}")
        report_lines.append(f"  Duplicates skipped: {self.stats['duplicates_skipped']}")
        report_lines.append(f"  Corrupted skipped: {self.stats['corrupted_skipped']}")
        report_lines.append(f"  Failed copies: {self.stats['failed_copies']}")
        report_lines.append("")
        
        report_lines.append("By Split:")
        report_lines.append(f"  Train: {self.stats['by_split']['train']}")
        report_lines.append(f"  Val: {self.stats['by_split']['val']}")
        report_lines.append("")
        
        report_lines.append("By Label:")
        report_lines.append(f"  Real: {self.stats['by_label']['real']}")
        report_lines.append(f"  AI: {self.stats['by_label']['ai']}")
        report_lines.append("")
        
        if self.stats['by_generator']:
            report_lines.append("By Generator:")
            for generator, splits in self.stats['by_generator'].items():
                report_lines.append(f"  {generator}:")
                report_lines.append(f"    Train: {splits['train']}")
                report_lines.append(f"    Val: {splits['val']}")
            report_lines.append("")
        
        report_lines.append("=" * 80)
        
        output_file = self.target_dir / f"{self.get_source_dataset_name()}_organization_report.txt"
        with open(output_file, 'w') as f:
            f.write('\n'.join(report_lines))
        
        print(f"[{self.__class__.__name__}] Report saved to {output_file}")
        return str(output_file)
    
    def organize(self) -> Dict[str, any]:
        """
        Run complete organization process.
        
        Returns:
            Dict with organization results
        """
        print(f"[{self.__class__.__name__}] Starting dataset organization...")
        
        # Reset duplicate detector cache for fresh organization
        try:
            self.duplicate_detector.reset_cache()
        except Exception as e:
            print(f"[{self.__class__.__name__}] ERROR: Failed to reset duplicate cache: {e}")
            import traceback
            traceback.print_exc()
        
        # Validate source directory
        try:
            if not self.source_dir.exists():
                raise ValueError(f"Source directory does not exist: {self.source_dir}")
            print(f"[{self.__class__.__name__}] Source directory validated: {self.source_dir}")
        except Exception as e:
            print(f"[{self.__class__.__name__}] ERROR: Source directory validation failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": "Source directory validation failed",
                "exception": str(e),
                "source_dir": str(self.source_dir)
            }
        
        # Validate target directory
        try:
            target_validation = self.validate_target_directory()
            if not target_validation["valid"]:
                print(f"[{self.__class__.__name__}] Target directory validation failed")
                return {
                    "success": False,
                    "error": "Target directory validation failed",
                    "validation": target_validation,
                    "source_dir": str(self.source_dir),
                    "target_dir": str(self.target_dir)
                }
            print(f"[{self.__class__.__name__}] Target directory validated: {self.target_dir}")
        except Exception as e:
            print(f"[{self.__class__.__name__}] ERROR: Target directory validation failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": "Target directory validation failed",
                "exception": str(e),
                "source_dir": str(self.source_dir),
                "target_dir": str(self.target_dir)
            }
        
        # Detect structure
        structure = None
        try:
            print(f"[{self.__class__.__name__}] Detecting dataset structure...")
            structure = self.detect_structure()
            print(f"[{self.__class__.__name__}] Structure detection completed")
            print(f"  Samples detected: {len(structure.get('samples', []))}")
            
            if not structure.get('samples'):
                print(f"[{self.__class__.__name__}] No samples found")
                return {
                    "success": False,
                    "error": "No samples found",
                    "source_dir": str(self.source_dir)
                }
        except Exception as e:
            print(f"[{self.__class__.__name__}] ERROR: Structure detection failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": "Structure detection failed",
                "exception": str(e),
                "source_dir": str(self.source_dir)
            }
        
        # Process samples
        samples_metadata = []
        total_samples = len(structure['samples'])
        print(f"[{self.__class__.__name__}] Starting sample processing...")
        print(f"  Total samples to process: {total_samples}")
        
        for idx, sample_info in enumerate(structure['samples'], start=1):
            try:
                source_path = sample_info['path']
                print(f"\n[{self.__class__.__name__}] === Sample {idx}/{total_samples} ===")
                
                # Map metadata
                try:
                    metadata = self.map_sample_metadata(source_path, structure)
                    print(f"  Mapped metadata: label={metadata.get('label')}, split={metadata.get('split')}, generator={metadata.get('generator')}")
                except Exception as e:
                    print(f"  ERROR: Metadata mapping failed: {e}")
                    import traceback
                    traceback.print_exc()
                    self.stats["failed_copies"] += 1
                    continue
                
                # Get target path
                try:
                    target_path = self.get_target_path(metadata)
                    print(f"  Target path: {target_path}")
                except Exception as e:
                    print(f"  ERROR: Target path calculation failed: {e}")
                    import traceback
                    traceback.print_exc()
                    self.stats["failed_copies"] += 1
                    continue
                
                # Copy sample
                try:
                    if self.copy_sample(source_path, target_path, metadata, idx, total_samples):
                        # Update statistics
                        self.stats["total_images_processed"] += 1
                        self.stats["by_split"][metadata['split']] += 1
                        self.stats["by_label"][metadata['label']] += 1
                        
                        if metadata['label'] == 'ai' and metadata.get('generator'):
                            self.stats["by_generator"][metadata['generator']][metadata['split']] += 1
                        
                        # Add relative path to metadata
                        relative_path = target_path / source_path.name
                        metadata['file_path'] = str(relative_path.relative_to(self.target_dir))
                        samples_metadata.append(metadata)
                        print(f"  Statistics updated: total_processed={self.stats['total_images_processed']}, copied={self.stats['total_images_copied']}")
                    else:
                        print(f"  Sample not copied (skipped or failed)")
                except Exception as e:
                    print(f"  ERROR: Copy sample failed: {e}")
                    import traceback
                    traceback.print_exc()
                    self.stats["failed_copies"] += 1
                    
            except Exception as e:
                print(f"[{self.__class__.__name__}] ERROR: Processing sample {idx} failed: {e}")
                print(f"  Sample path: {sample_info.get('path')}")
                print(f"  Handler: {self.__class__.__name__}")
                import traceback
                traceback.print_exc()
                self.stats["failed_copies"] += 1
                continue
        
        print(f"\n[{self.__class__.__name__}] Sample processing completed")
        print(f"  Total samples processed: {len(samples_metadata)}")
        print(f"  Total samples expected: {total_samples}")
        
        # Generate duplicate audit report
        audit_report_path = None
        try:
            print(f"[{self.__class__.__name__}] Generating duplicate audit report...")
            audit_report_path = self.duplicate_detector.generate_audit_report(
                self.target_dir / "duplicate_audit_report.txt"
            )
            print(f"[{self.__class__.__name__}] Duplicate audit report generated: {audit_report_path}")
        except Exception as e:
            print(f"[{self.__class__.__name__}] ERROR: Duplicate audit report generation failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Generate metadata CSV
        metadata_path = None
        try:
            print(f"[{self.__class__.__name__}] Generating metadata CSV...")
            metadata_path = self.generate_metadata_csv(samples_metadata)
            print(f"[{self.__class__.__name__}] Metadata CSV generated: {metadata_path}")
        except Exception as e:
            print(f"[{self.__class__.__name__}] ERROR: Metadata CSV generation failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Validate metadata
        metadata_validation = None
        try:
            if metadata_path:
                print(f"[{self.__class__.__name__}] Validating metadata...")
                metadata_validation = self.validate_metadata(metadata_path)
                print(f"[{self.__class__.__name__}] Metadata validation completed")
        except Exception as e:
            print(f"[{self.__class__.__name__}] ERROR: Metadata validation failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Generate summary report
        report_path = None
        try:
            print(f"[{self.__class__.__name__}] Generating summary report...")
            report_path = self.generate_summary_report()
            print(f"[{self.__class__.__name__}] Summary report generated: {report_path}")
        except Exception as e:
            print(f"[{self.__class__.__name__}] ERROR: Summary report generation failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Print final summary
        print(f"\n{'='*80}")
        print(f"[{self.__class__.__name__}] FINAL ORGANIZATION SUMMARY")
        print(f"{'='*80}")
        print(f"Expected samples: {total_samples}")
        print(f"Processed samples: {len(samples_metadata)}")
        print(f"Copied AI: {self.stats['by_label']['ai']}")
        print(f"Copied REAL: {self.stats['by_label']['real']}")
        print(f"Skipped duplicates: {self.stats['duplicates_skipped']}")
        print(f"Skipped corrupted: {self.stats['corrupted_skipped']}")
        print(f"Failed copies: {self.stats['failed_copies']}")
        print(f"{'='*80}\n")
        
        return {
            "success": True,
            "source_dir": str(self.source_dir),
            "target_dir": str(self.target_dir),
            "source_dataset": self.get_source_dataset_name(),
            "statistics": dict(self.stats),
            "metadata_csv": metadata_path,
            "metadata_validation": metadata_validation,
            "summary_report": report_path,
            "duplicate_audit_report": audit_report_path,
            "target_validation": target_validation,
            "structure": structure
        }
