"""
HELIX SDK CLI
Command-line interface for quick compression and materialization.
"""

import argparse
import sys
from pathlib import Path


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="helix",
        description="HELIX SDK - AI-powered semantic image compression",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  helix compress photo.jpg                 # Compress to photo.hlx
  helix compress photo.jpg -o custom.hlx   # Custom output path
  helix materialize photo.hlx -r 4K        # Materialize at 4K
  helix info photo.hlx                     # Show HLX file info
  helix batch /images/ /hlx/ -w 8          # Batch compress with 8 workers
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Compress command
    compress_parser = subparsers.add_parser("compress", help="Compress image to HLX")
    compress_parser.add_argument("input", help="Input image path")
    compress_parser.add_argument("-o", "--output", help="Output HLX path")
    compress_parser.add_argument("-f", "--format", choices=["v1", "v2"], default="v2",
                                  help="HLX format version (default: v2)")
    
    # Materialize command
    mat_parser = subparsers.add_parser("materialize", help="Reconstruct image from HLX")
    mat_parser.add_argument("input", help="Input HLX path")
    mat_parser.add_argument("-o", "--output", help="Output image path")
    mat_parser.add_argument("-r", "--resolution", default="1080p",
                             choices=["256p", "512p", "720p", "1080p", "1440p", "4K", "8K"],
                             help="Target resolution (default: 1080p)")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Show HLX file information")
    info_parser.add_argument("input", help="HLX file path")
    
    # Batch command
    batch_parser = subparsers.add_parser("batch", help="Batch compress directory")
    batch_parser.add_argument("input_dir", help="Input directory")
    batch_parser.add_argument("output_dir", help="Output directory")
    batch_parser.add_argument("-w", "--workers", type=int, default=4,
                               help="Number of parallel workers (default: 4)")
    batch_parser.add_argument("-r", "--recursive", action="store_true",
                               help="Process subdirectories")
    
    # Version command
    parser.add_argument("-v", "--version", action="store_true", help="Show version")
    
    args = parser.parse_args()
    
    if args.version:
        from helix_sdk import __version__
        print(f"HELIX SDK v{__version__}")
        return 0
    
    if not args.command:
        parser.print_help()
        return 0
    
    # Import SDK lazily
    from helix_sdk import HelixSDK, HLXFormat
    
    sdk = HelixSDK(verbose=True)
    
    if args.command == "compress":
        format_version = HLXFormat.V2 if args.format == "v2" else HLXFormat.V1
        result = sdk.compress(args.input, args.output, format_version=format_version)
        
        if result.success:
            print(f"\n✅ Compressed successfully!")
            print(f"   Input:  {result.input_size / 1024:.1f} KB")
            print(f"   Output: {result.output_size / 1024:.1f} KB")
            print(f"   Ratio:  {result.compression_ratio:.1f}x")
            print(f"   Saved:  {result.output_path}")
            return 0
        else:
            print(f"\n❌ Compression failed: {result.error}")
            return 1
            
    elif args.command == "materialize":
        result = sdk.materialize(args.input, args.output, resolution=args.resolution)
        
        if result.success:
            print(f"\n✅ Materialized successfully!")
            print(f"   Resolution: {result.output_width}x{result.output_height}")
            print(f"   AI Enhanced: {result.ai_enhanced}")
            print(f"   Saved: {result.output_path}")
            return 0
        else:
            print(f"\n❌ Materialization failed: {result.error}")
            return 1
            
    elif args.command == "info":
        try:
            info = sdk.get_info(args.input)
            print(f"\n📄 HLX File Info: {args.input}")
            print(f"   Size: {info['file_size'] / 1024:.1f} KB")
            if info.get('original_dimensions'):
                print(f"   Original: {info['original_dimensions']}")
            print(f"   Anchors: {info.get('anchors_count', 0)}")
            print(f"   Mesh Constraints: {info.get('mesh_constraints', 0)}")
            if info.get('scene_description'):
                print(f"   Scene: {info['scene_description'][:80]}...")
            return 0
        except Exception as e:
            print(f"\n❌ Error reading file: {e}")
            return 1
            
    elif args.command == "batch":
        stats = sdk.compress_directory(
            args.input_dir,
            args.output_dir,
            recursive=args.recursive,
            workers=args.workers
        )
        
        print(f"\n📦 Batch Compression Complete!")
        print(f"   Processed: {stats.files_processed}")
        print(f"   Failed: {stats.files_failed}")
        print(f"   Compression: {stats.compression_ratio:.1f}x")
        print(f"   Space Saved: {stats.space_saved_percent:.1f}%")
        print(f"   Time: {stats.total_time_seconds:.1f}s")
        return 0
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
