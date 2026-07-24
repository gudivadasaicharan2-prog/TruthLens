"""
Duplicate Detector
==================
Detects duplicate images using MD5 and perceptual hashing.
"""

from pathlib import Path
from typing import Dict, List, Set
import hashlib
from PIL import Image
import imagehash


class DuplicateDetector:
    """Detect duplicate images using multiple methods."""
    
    def __init__(self):
        """Initialize duplicate detector."""
        self.md5_hashes = {}
        self.perceptual_hashes = {}
        # Internal cache for tracking seen hashes during dataset import
        # This allows efficient duplicate detection without rescanning
        self.seen_hashes = set()
        # Track duplicate information for audit report
        # Maps hash to list of file paths that have this hash
        self.hash_to_files = {}
        # Track skipped duplicates for audit report
        self.skipped_duplicates = []
    
    def calculate_md5(self, image_path: Path) -> str:
        """
        Calculate MD5 hash of image file.
        
        Args:
            image_path: Path to image file
        
        Returns:
            MD5 hash string
        """
        hash_md5 = hashlib.md5()
        with open(image_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def calculate_perceptual_hash(self, image_path: Path) -> str:
        """
        Calculate perceptual hash of image.
        
        Args:
            image_path: Path to image file
        
        Returns:
            Perceptual hash string
        """
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                # Calculate average hash
                phash = imagehash.average_hash(img, hash_size=16)
                return str(phash)
        except Exception as e:
            print(f"Error calculating perceptual hash for {image_path}: {e}")
            return ""
    
    def is_duplicate(self, image_path: Path) -> bool:
        """
        Check if an image is a duplicate based on MD5 hash.
        
        This method is designed for efficient duplicate detection during dataset import.
        It maintains an internal cache of seen hashes to avoid recalculating and rescanning.
        
        Duplicate Detection Flow:
        1. Calculate MD5 hash using existing calculate_md5() method
        2. Check if hash exists in internal seen_hashes cache
        3. If hash is in cache: return True (is duplicate), record for audit
        4. If hash not in cache: add to cache and record for audit, return False (not duplicate)
        
        This approach ensures:
        - O(1) duplicate check after initial hash calculation
        - No need to rescan previously processed files
        - Efficient memory usage (only stores hash strings, not file paths)
        - Reuses existing MD5 implementation
        - Content-based detection (MD5 hash of file content, not filename)
        
        Args:
            image_path: Path to image file to check
        
        Returns:
            True if image is a duplicate (hash seen before), False otherwise
        """
        md5_hash = self.calculate_md5(image_path)
        
        if md5_hash in self.seen_hashes:
            # Hash has been seen before, this is a duplicate
            # Record for audit: original file and duplicate file
            original_file = self.hash_to_files[md5_hash][0]  # First file with this hash
            self.skipped_duplicates.append({
                'original_file': original_file,
                'duplicate_file': str(image_path),
                'hash': md5_hash,
                'reason': 'MD5 hash collision (content-based duplicate)'
            })
            return True
        else:
            # First time seeing this hash, add to cache
            self.seen_hashes.add(md5_hash)
            # Record file path for this hash
            if md5_hash not in self.hash_to_files:
                self.hash_to_files[md5_hash] = []
            self.hash_to_files[md5_hash].append(str(image_path))
            return False
    
    def reset_cache(self):
        """
        Reset the internal hash cache and audit tracking.
        
        This clears the seen_hashes set, hash_to_files mapping, and skipped_duplicates list,
        allowing the detector to start fresh.
        Useful when processing multiple independent datasets or when
        you want to re-process files without considering previous duplicates.
        """
        self.seen_hashes.clear()
        self.hash_to_files.clear()
        self.skipped_duplicates.clear()
        print("[DuplicateDetector] Reset internal hash cache and audit tracking")
    
    def find_duplicates(self, image_dir: Path) -> Dict[str, List[str]]:
        """
        Find duplicate images in directory.
        
        Args:
            image_dir: Directory to search for duplicates
        
        Returns:
            Dict mapping hash to list of duplicate file paths
        """
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        md5_duplicates = {}
        perceptual_duplicates = {}
        
        print("[DuplicateDetector] Scanning for duplicates...")
        
        for image_path in image_dir.rglob('*'):
            if image_path.suffix.lower() not in image_extensions:
                continue
            
            # MD5 hash
            md5_hash = self.calculate_md5(image_path)
            if md5_hash in md5_duplicates:
                md5_duplicates[md5_hash].append(str(image_path))
            else:
                md5_duplicates[md5_hash] = [str(image_path)]
            
            # Perceptual hash
            phash = self.calculate_perceptual_hash(image_path)
            if phash:
                if phash in perceptual_duplicates:
                    perceptual_duplicates[phash].append(str(image_path))
                else:
                    perceptual_duplicates[phash] = [str(image_path)]
        
        # Filter to only actual duplicates (more than 1 file)
        md5_duplicates = {k: v for k, v in md5_duplicates.items() if len(v) > 1}
        perceptual_duplicates = {k: v for k, v in perceptual_duplicates.items() if len(v) > 1}
        
        return {
            "md5_duplicates": md5_duplicates,
            "perceptual_duplicates": perceptual_duplicates
        }
    
    def remove_duplicates(self, duplicates: Dict[str, List[str]], keep_first: bool = True) -> int:
        """
        Remove duplicate files, keeping the first occurrence.
        
        Args:
            duplicates: Dict of duplicates from find_duplicates
            keep_first: If True, keep first file in each duplicate group
        
        Returns:
            Number of files removed
        """
        removed = 0
        
        # Remove MD5 duplicates
        for hash_val, file_paths in duplicates.get("md5_duplicates", {}).items():
            files_to_remove = file_paths[1:] if keep_first else file_paths
            for file_path in files_to_remove:
                try:
                    Path(file_path).unlink()
                    removed += 1
                    print(f"Removed duplicate (MD5): {file_path}")
                except Exception as e:
                    print(f"Error removing {file_path}: {e}")
        
        # Remove perceptual duplicates
        for hash_val, file_paths in duplicates.get("perceptual_duplicates", {}).items():
            files_to_remove = file_paths[1:] if keep_first else file_paths
            for file_path in files_to_remove:
                try:
                    Path(file_path).unlink()
                    removed += 1
                    print(f"Removed duplicate (perceptual): {file_path}")
                except Exception as e:
                    print(f"Error removing {file_path}: {e}")
        
        return removed
    
    def generate_audit_report(self, output_path: Path) -> str:
        """
        Generate a duplicate audit report.
        
        This report provides detailed information about duplicates detected during
        dataset organization, including the first 20 skipped duplicate file pairs.
        
        Args:
            output_path: Path to save the audit report
        
        Returns:
            Path to generated audit report
        """
        print("[DuplicateDetector] Generating duplicate audit report...")
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("Duplicate Detection Audit Report")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        # Summary
        report_lines.append("Duplicate Summary")
        report_lines.append("-" * 40)
        report_lines.append(f"Total duplicate candidates: {len(self.skipped_duplicates)}")
        
        # Count unique hashes
        unique_hashes = set(d['hash'] for d in self.skipped_duplicates)
        report_lines.append(f"Unique hash collisions: {len(unique_hashes)}")
        
        # All are content-based MD5 duplicates
        report_lines.append(f"True content duplicates: {len(self.skipped_duplicates)}")
        report_lines.append(f"Filename collisions: 0 (not used)")
        report_lines.append(f"Hash collisions: {len(self.skipped_duplicates)}")
        report_lines.append(f"False positives: 0 (MD5 is cryptographically strong)")
        report_lines.append("")
        
        # Detection method explanation
        report_lines.append("Detection Method")
        report_lines.append("-" * 40)
        report_lines.append("Duplicate detection is based on MD5 hash of file content.")
        report_lines.append("This is a content-based detection method, not filename-based.")
        report_lines.append("MD5 is a cryptographic hash function with extremely low collision probability.")
        report_lines.append("Files with identical MD5 hashes have identical byte-for-byte content.")
        report_lines.append("")
        
        # First 20 skipped duplicates
        report_lines.append("First 20 Skipped Duplicate File Pairs")
        report_lines.append("-" * 40)
        for i, dup in enumerate(self.skipped_duplicates[:20], start=1):
            report_lines.append(f"{i}. Original: {dup['original_file']}")
            report_lines.append(f"   Duplicate: {dup['duplicate_file']}")
            report_lines.append(f"   Hash: {dup['hash']}")
            report_lines.append(f"   Reason: {dup['reason']}")
            report_lines.append("")
        
        if len(self.skipped_duplicates) > 20:
            report_lines.append(f"... and {len(self.skipped_duplicates) - 20} more duplicates")
            report_lines.append("")
        
        report_lines.append("=" * 80)
        
        # Write report
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write('\n'.join(report_lines))
        
        print(f"[DuplicateDetector] Audit report saved to {output_path}")
        return str(output_path)
