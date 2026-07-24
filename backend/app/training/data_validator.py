"""
Data Validator
==============
Validates metadata.csv and dataset integrity before training.
"""

import csv
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import Counter
import json


class DataValidator:
    """
    Validates metadata.csv and dataset integrity before training.
    
    Checks:
    - File existence
    - CSV format validity
    - Required columns
    - Label distribution
    - Split distribution
    - File existence in dataset directory
    - Missing/corrupted files
    """
    
    REQUIRED_COLUMNS = ['file_path', 'label', 'split', 'generator', 'source_dataset']
    VALID_LABELS = ['real', 'ai']
    VALID_SPLITS = ['train', 'val']
    
    def __init__(self, metadata_path: str, dataset_dir: str):
        """
        Initialize data validator.
        
        Args:
            metadata_path: Path to metadata.csv
            dataset_dir: Base directory containing images
        """
        self.metadata_path = Path(metadata_path)
        self.dataset_dir = Path(dataset_dir)
        self.errors = []
        self.warnings = []
        self.stats = {}
    
    def validate(self) -> Dict[str, Any]:
        """
        Run full validation and return results.
        
        Returns:
            Validation results dictionary
        """
        print(f"[DataValidator] Starting validation...")
        print(f"[DataValidator] Metadata path: {self.metadata_path}")
        print(f"[DataValidator] Dataset directory: {self.dataset_dir}")
        
        # Check file existence
        self._check_file_existence()
        
        # Load and validate CSV
        rows = self._load_and_validate_csv()
        
        if rows:
            # Validate columns
            self._validate_columns(rows[0])
            
            # Validate data content
            self._validate_data_content(rows)
            
            # Check file existence in dataset
            self._check_image_files_exist(rows)
            
            # Calculate statistics
            self._calculate_statistics(rows)
        
        # Generate report
        report = self._generate_report()
        
        print(f"[DataValidator] Validation complete")
        print(f"[DataValidator] Errors: {len(self.errors)}")
        print(f"[DataValidator] Warnings: {len(self.warnings)}")
        
        return report
    
    def _check_file_existence(self):
        """Check if metadata file and dataset directory exist."""
        if not self.metadata_path.exists():
            self.errors.append(f"Metadata file not found: {self.metadata_path}")
        
        if not self.dataset_dir.exists():
            self.errors.append(f"Dataset directory not found: {self.dataset_dir}")
    
    def _load_and_validate_csv(self) -> List[Dict[str, str]]:
        """
        Load CSV and validate format.
        
        Returns:
            List of row dictionaries
        """
        rows = []
        
        try:
            with open(self.metadata_path, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rows.append(row)
        except Exception as e:
            self.errors.append(f"Failed to read CSV: {e}")
            return []
        
        if not rows:
            self.errors.append("CSV file is empty")
        
        return rows
    
    def _validate_columns(self, first_row: Dict[str, str]):
        """
        Validate that required columns exist.
        
        Args:
            first_row: First row of CSV
        """
        for col in self.REQUIRED_COLUMNS:
            if col not in first_row:
                self.errors.append(f"Missing required column: {col}")
    
    def _validate_data_content(self, rows: List[Dict[str, str]]):
        """
        Validate data content (labels, splits, etc.).
        
        Args:
            rows: List of row dictionaries
        """
        for idx, row in enumerate(rows, start=1):
            # Validate label
            label = row.get('label', '').lower()
            if label not in self.VALID_LABELS:
                self.errors.append(f"Row {idx}: Invalid label '{label}' (must be one of {self.VALID_LABELS})")
            
            # Validate split
            split = row.get('split', '').lower()
            if split not in self.VALID_SPLITS:
                self.errors.append(f"Row {idx}: Invalid split '{split}' (must be one of {self.VALID_SPLITS})")
            
            # Validate file_path is not empty
            if not row.get('file_path'):
                self.errors.append(f"Row {idx}: Empty file_path")
    
    def _check_image_files_exist(self, rows: List[Dict[str, str]]):
        """
        Check that image files exist in dataset directory.
        
        Args:
            rows: List of row dictionaries
        """
        missing_files = []
        
        for idx, row in enumerate(rows, start=1):
            file_path = row.get('file_path')
            if file_path:
                full_path = self.dataset_dir / file_path
                if not full_path.exists():
                    missing_files.append((idx, file_path))
        
        if missing_files:
            self.errors.append(f"Missing image files: {len(missing_files)}")
            for idx, file_path in missing_files[:10]:  # Show first 10
                self.errors.append(f"  Row {idx}: {file_path}")
            if len(missing_files) > 10:
                self.errors.append(f"  ... and {len(missing_files) - 10} more")
    
    def _calculate_statistics(self, rows: List[Dict[str, str]]):
        """
        Calculate dataset statistics.
        
        Args:
            rows: List of row dictionaries
        """
        self.stats['total_samples'] = len(rows)
        
        # Label distribution
        labels = [row.get('label', '').lower() for row in rows]
        self.stats['label_distribution'] = dict(Counter(labels))
        
        # Split distribution
        splits = [row.get('split', '').lower() for row in rows]
        self.stats['split_distribution'] = dict(Counter(splits))
        
        # Generator distribution (for AI images)
        generators = [row.get('generator', 'unknown') for row in rows if row.get('label', '').lower() == 'ai']
        self.stats['generator_distribution'] = dict(Counter(generators))
        
        # Source dataset distribution
        sources = [row.get('source_dataset', 'unknown') for row in rows]
        self.stats['source_dataset_distribution'] = dict(Counter(sources))
        
        # Label x split distribution
        label_split_dist = {}
        for row in rows:
            label = row.get('label', '').lower()
            split = row.get('split', '').lower()
            key = f"{label}_{split}"
            label_split_dist[key] = label_split_dist.get(key, 0) + 1
        self.stats['label_split_distribution'] = label_split_dist
    
    def _generate_report(self) -> Dict[str, Any]:
        """
        Generate validation report.
        
        Returns:
            Validation report dictionary
        """
        is_valid = len(self.errors) == 0
        
        report = {
            'is_valid': is_valid,
            'metadata_path': str(self.metadata_path),
            'dataset_dir': str(self.dataset_dir),
            'errors': self.errors,
            'warnings': self.warnings,
            'statistics': self.stats
        }
        
        return report
    
    def print_report(self, report: Dict[str, Any]):
        """
        Print validation report in readable format.
        
        Args:
            report: Validation report dictionary
        """
        print("\n" + "=" * 80)
        print("DATA VALIDATION REPORT")
        print("=" * 80)
        
        print(f"\nMetadata Path: {report['metadata_path']}")
        print(f"Dataset Directory: {report['dataset_dir']}")
        print(f"Valid: {report['is_valid']}")
        
        if report['errors']:
            print(f"\nErrors ({len(report['errors'])}):")
            for error in report['errors']:
                print(f"  - {error}")
        
        if report['warnings']:
            print(f"\nWarnings ({len(report['warnings'])}):")
            for warning in report['warnings']:
                print(f"  - {warning}")
        
        if report['statistics']:
            print(f"\nStatistics:")
            stats = report['statistics']
            print(f"  Total samples: {stats.get('total_samples', 0)}")
            
            if 'label_distribution' in stats:
                print(f"  Label distribution:")
                for label, count in stats['label_distribution'].items():
                    print(f"    {label}: {count}")
            
            if 'split_distribution' in stats:
                print(f"  Split distribution:")
                for split, count in stats['split_distribution'].items():
                    print(f"    {split}: {count}")
            
            if 'generator_distribution' in stats:
                print(f"  Generator distribution (AI images):")
                for generator, count in stats['generator_distribution'].items():
                    print(f"    {generator}: {count}")
            
            if 'source_dataset_distribution' in stats:
                print(f"  Source dataset distribution:")
                for source, count in stats['source_dataset_distribution'].items():
                    print(f"    {source}: {count}")
        
        print("\n" + "=" * 80)
    
    def save_report(self, report: Dict[str, Any], output_path: str):
        """
        Save validation report to JSON file.
        
        Args:
            report: Validation report dictionary
            output_path: Path to save report
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"[DataValidator] Saved validation report to {output_path}")
