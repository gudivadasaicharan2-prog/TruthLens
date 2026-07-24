"""
TruthLens Dataset Manager CLI
============================
Command-line interface for dataset management.
"""

import argparse
import sys
import json
from pathlib import Path

from .dataset_manager import DatasetManager
from .benchmark_builder import BenchmarkBuilder
from .tiny_genimage_organizer import TinyGenImageOrganizer
from .handlers import TinyGenImageHandler, CIFAKEHandler


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="TruthLens Dataset Manager - Automatic dataset management for AI detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download a specific dataset
  python -m app.dataset_manager.cli --dataset genimage
  
  # Download all datasets
  python -m app.dataset_manager.cli --all
  
  # Organize imported dataset
  python -m app.dataset_manager.cli --organize /path/to/images --content-type real --category portrait
  
  # Organize Tiny GenImage dataset
  python -m app.dataset_manager.cli --organize-tiny-genimage /path/to/tiny-genimage
  
  # Organize Tiny GenImage dataset with force overwrite
  python -m app.dataset_manager.cli --organize-tiny-genimage /path/to/tiny-genimage --force
  
  # Organize CIFAKE dataset
  python -m app.dataset_manager.cli --organize-cifake /path/to/cifake
  
  # Organize CIFAKE dataset with force overwrite
  python -m app.dataset_manager.cli --organize-cifake /path/to/cifake --force
  
  # Clean dataset
  python -m app.dataset_manager.cli --clean
  
  # Build benchmark
  python -m app.dataset_manager.cli --build-benchmark --samples 100
  
  # Full pipeline
  python -m app.dataset_manager.cli --full-pipeline --datasets ffhq genimage
        """
    )
    
    # Dataset options
    parser.add_argument('--dataset', type=str, help='Dataset to download (ffhq, coco, openimages, genimage, faceforensics, dfdc)')
    parser.add_argument('--all', action='store_true', help='Download all available datasets')
    
    # Organization options
    parser.add_argument('--organize', type=str, help='Path to source directory to organize')
    parser.add_argument('--organize-tiny-genimage', type=str, help='Path to Tiny GenImage dataset to organize')
    parser.add_argument('--organize-cifake', type=str, help='Path to CIFAKE dataset to organize')
    parser.add_argument('--force', action='store_true', help='Force overwrite existing data in target directory')
    parser.add_argument('--content-type', type=str, choices=['real', 'ai'], help='Content type (real or ai)')
    parser.add_argument('--category', type=str, help='Category for real images (portrait, landscape, object, document, screenshot)')
    parser.add_argument('--generator', type=str, help='Generator for AI images (midjourney, sdxl, adm, glide)')
    
    # Cleaning options
    parser.add_argument('--clean', action='store_true', help='Clean dataset (remove duplicates and corrupted files)')
    parser.add_argument('--clean-dir', type=str, help='Directory to clean (default: TruthLensDataset)')
    
    # Statistics options
    parser.add_argument('--stats', action='store_true', help='Generate dataset statistics')
    
    # Report options
    parser.add_argument('--report', action='store_true', help='Generate dataset reports')
    parser.add_argument('--report-dir', type=str, default='reports', help='Report output directory')
    
    # Benchmark options
    parser.add_argument('--build-benchmark', action='store_true', help='Build benchmark dataset')
    parser.add_argument('--benchmark-categories', type=str, nargs='+', help='Categories for benchmark')
    parser.add_argument('--samples', type=int, default=100, help='Samples per category for benchmark')
    parser.add_argument('--split-ratio', type=float, default=0.8, help='Train/validation split ratio')
    
    # Full pipeline
    parser.add_argument('--full-pipeline', action='store_true', help='Run full dataset management pipeline')
    parser.add_argument('--datasets', type=str, nargs='+', help='Datasets for full pipeline')
    
    # Global options
    parser.add_argument('--base-dir', type=str, default='TruthLensDataset', help='Base directory for TruthLensDataset')
    parser.add_argument('--resize-size', type=int, nargs=2, default=[512, 512], help='Target resize size (width height)')
    parser.add_argument('--output', type=str, help='Output file path')
    
    args = parser.parse_args()
    
    # Initialize dataset manager
    resize_size = tuple(args.resize_size) if args.resize_size else (512, 512)
    manager = DatasetManager(args.base_dir, resize_size)
    
    try:
        # Download dataset
        if args.dataset:
            print(f"\n[CLI] Downloading dataset: {args.dataset}")
            result = manager.download_dataset(args.dataset)
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(result, f, indent=2, default=str)
            else:
                print(json.dumps(result, indent=2, default=str))
        
        # Download all datasets
        elif args.all:
            print("\n[CLI] Downloading all datasets...")
            results = manager.download_all()
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(results, f, indent=2, default=str)
            else:
                print(json.dumps(results, indent=2, default=str))
        
        # Organize dataset
        elif args.organize:
            print(f"\n[CLI] Organizing dataset from {args.organize}")
            if not args.content_type:
                print("[CLI] Error: --content-type required for --organize")
                sys.exit(1)
            
            result = manager.organize_imported_dataset(
                args.organize,
                args.content_type,
                args.category,
                args.generator
            )
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(result, f, indent=2, default=str)
            else:
                print(json.dumps(result, indent=2, default=str))
        
        # Organize Tiny GenImage dataset
        elif args.organize_tiny_genimage:
            print(f"\n[CLI] Organizing Tiny GenImage dataset from {args.organize_tiny_genimage}")
            organizer = TinyGenImageOrganizer(args.organize_tiny_genimage, args.base_dir, force=args.force)
            result = organizer.organize()
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(result, f, indent=2, default=str)
            else:
                print(json.dumps(result, indent=2, default=str))
        
        # Organize CIFAKE dataset
        elif args.organize_cifake:
            print(f"\n[CLI] Organizing CIFAKE dataset from {args.organize_cifake}")
            handler = CIFAKEHandler(args.organize_cifake, args.base_dir, force=args.force)
            result = handler.organize()
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(result, f, indent=2, default=str)
            else:
                print(json.dumps(result, indent=2, default=str))
        
        # Clean dataset
        elif args.clean:
            print(f"\n[CLI] Cleaning dataset...")
            result = manager.clean_dataset(args.clean_dir)
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(result, f, indent=2, default=str)
            else:
                print(json.dumps(result, indent=2, default=str))
        
        # Generate statistics
        elif args.stats:
            print("\n[CLI] Generating statistics...")
            stats = manager.get_statistics()
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(stats, f, indent=2, default=str)
            else:
                print(json.dumps(stats, indent=2, default=str))
        
        # Generate reports
        elif args.report:
            print(f"\n[CLI] Generating reports in {args.report_dir}...")
            reports = manager.generate_report(args.report_dir)
            print(json.dumps(reports, indent=2, default=str))
        
        # Build benchmark
        elif args.build_benchmark:
            print("\n[CLI] Building benchmark dataset...")
            builder = BenchmarkBuilder(args.base_dir)
            result = builder.build_benchmark(
                categories=args.benchmark_categories,
                samples_per_category=args.samples,
                split_ratio=args.split_ratio
            )
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(result, f, indent=2, default=str)
            else:
                print(json.dumps(result, indent=2, default=str))
        
        # Full pipeline
        elif args.full_pipeline:
            print("\n[CLI] Running full pipeline...")
            result = manager.full_pipeline(args.datasets)
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(result, f, indent=2, default=str)
            else:
                print(json.dumps(result, indent=2, default=str))
        
        else:
            parser.print_help()
    
    except Exception as e:
        print(f"[CLI] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
