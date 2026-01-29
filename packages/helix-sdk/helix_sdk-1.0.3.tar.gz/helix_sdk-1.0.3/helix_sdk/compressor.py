"""
HELIX Batch Compressor
======================
Efficiently compress entire directories of images into HELIX format.
Designed for AI training data preprocessing.
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import json

sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class CompressionStats:
    """Statistics from a compression run"""
    total_files: int = 0
    successful: int = 0
    failed: int = 0
    original_bytes: int = 0
    compressed_bytes: int = 0
    elapsed_seconds: float = 0
    
    @property
    def compression_ratio(self) -> float:
        if self.compressed_bytes == 0:
            return 0
        return self.original_bytes / self.compressed_bytes
    
    @property
    def space_saved_bytes(self) -> int:
        return self.original_bytes - self.compressed_bytes
    
    @property
    def space_saved_percent(self) -> float:
        if self.original_bytes == 0:
            return 0
        return (self.space_saved_bytes / self.original_bytes) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_files": self.total_files,
            "successful": self.successful,
            "failed": self.failed,
            "original_bytes": self.original_bytes,
            "original_mb": round(self.original_bytes / (1024*1024), 2),
            "compressed_bytes": self.compressed_bytes,
            "compressed_mb": round(self.compressed_bytes / (1024*1024), 2),
            "compression_ratio": round(self.compression_ratio, 2),
            "space_saved_percent": round(self.space_saved_percent, 1),
            "elapsed_seconds": round(self.elapsed_seconds, 2),
            "files_per_second": round(self.successful / max(self.elapsed_seconds, 0.001), 1)
        }


class BatchCompressor:
    """
    Compress directories of images into HELIX format.
    
    🚀 Perfect for AI training data:
    - 100TB ImageNet -> ~10TB HELIX
    - Parallel processing for speed
    - Progress tracking
    - Resume on failure
    
    Usage:
        compressor = BatchCompressor()
        stats = compressor.compress_directory(
            input_dir="/data/imagenet/train/",
            output_dir="/data/imagenet_hlx/"
        )
        print(f"Compressed {stats.total_files} files, saved {stats.space_saved_percent}%")
    """
    
    # Supported input formats
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif'}
    
    def __init__(self, 
                 workers: int = 4,
                 use_v2_format: bool = True,
                 progress_callback: Optional[Callable] = None):
        """
        Initialize BatchCompressor.
        
        Args:
            workers: Number of parallel compression threads
            use_v2_format: Use cross-platform v2 format (recommended)
            progress_callback: Optional callback(completed, total, stats)
        """
        self.workers = workers
        self.use_v2_format = use_v2_format
        self.progress_callback = progress_callback
        
        self._pipeline = None
        
        print(f"[HELIX Compressor] Initialized: workers={workers}, format=v{'2' if use_v2_format else '1'}")
    
    def _get_pipeline(self):
        """Lazy-load the HELIX pipeline"""
        if self._pipeline is None:
            from src.core.pipeline import HelixPipeline
            self._pipeline = HelixPipeline()
        return self._pipeline
    
    def compress_directory(self,
                           input_dir: str,
                           output_dir: str,
                           preserve_structure: bool = True,
                           overwrite: bool = False,
                           extensions: Optional[set] = None) -> CompressionStats:
        """
        Compress all images in a directory to HELIX format.
        
        Args:
            input_dir: Source directory with images
            output_dir: Destination for .hlx files
            preserve_structure: Keep subdirectory structure
            overwrite: Overwrite existing .hlx files
            extensions: Custom set of extensions to include
            
        Returns:
            CompressionStats with results
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        
        if not input_path.exists():
            raise ValueError(f"Input directory does not exist: {input_dir}")
        
        # Create output directory
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Find all image files
        valid_exts = extensions or self.SUPPORTED_FORMATS
        image_files = []
        
        for ext in valid_exts:
            image_files.extend(input_path.glob(f"**/*{ext}"))
            image_files.extend(input_path.glob(f"**/*{ext.upper()}"))
        
        image_files = sorted(set(image_files))
        
        print(f"[HELIX Compressor] Found {len(image_files)} images to compress")
        
        if not image_files:
            return CompressionStats()
        
        # Compress in parallel
        stats = CompressionStats(total_files=len(image_files))
        start_time = time.time()
        
        completed = 0
        
        def compress_single(img_path: Path) -> tuple:
            """Compress a single image, returns (success, orig_size, compressed_size)"""
            try:
                # Calculate output path
                if preserve_structure:
                    rel_path = img_path.relative_to(input_path)
                    out_path = output_path / rel_path.with_suffix('.hlx')
                else:
                    out_path = output_path / (img_path.stem + '.hlx')
                
                # Skip if exists and not overwriting
                if out_path.exists() and not overwrite:
                    orig_size = img_path.stat().st_size
                    comp_size = out_path.stat().st_size
                    return (True, orig_size, comp_size, "skipped")
                
                # Ensure output directory exists
                out_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Get original size
                orig_size = img_path.stat().st_size
                
                # Compress
                pipeline = self._get_pipeline()
                
                if self.use_v2_format:
                    # v2: Use cross-platform format
                    self._compress_v2(str(img_path), str(out_path))
                else:
                    # v1: Standard encrypted format
                    pipeline.process_asset(str(img_path), str(out_path))
                
                # Get compressed size
                comp_size = out_path.stat().st_size
                
                return (True, orig_size, comp_size, "compressed")
                
            except Exception as e:
                print(f"[WARN] Failed to compress {img_path}: {e}")
                return (False, 0, 0, str(e))
        
        # Process files
        if self.workers <= 1:
            # Single-threaded
            for img_path in image_files:
                success, orig, comp, status = compress_single(img_path)
                if success:
                    stats.successful += 1
                    stats.original_bytes += orig
                    stats.compressed_bytes += comp
                else:
                    stats.failed += 1
                
                completed += 1
                if self.progress_callback:
                    self.progress_callback(completed, len(image_files), stats)
        else:
            # Multi-threaded
            with ThreadPoolExecutor(max_workers=self.workers) as executor:
                futures = {executor.submit(compress_single, p): p for p in image_files}
                
                for future in as_completed(futures):
                    success, orig, comp, status = future.result()
                    if success:
                        stats.successful += 1
                        stats.original_bytes += orig
                        stats.compressed_bytes += comp
                    else:
                        stats.failed += 1
                    
                    completed += 1
                    if self.progress_callback:
                        self.progress_callback(completed, len(image_files), stats)
        
        stats.elapsed_seconds = time.time() - start_time
        
        # Print summary
        self._print_summary(stats)
        
        # Save stats to output directory
        stats_path = output_path / "compression_stats.json"
        with open(stats_path, 'w') as f:
            json.dump(stats.to_dict(), f, indent=2)
        
        return stats
    
    def _compress_v2(self, input_path: str, output_path: str):
        """Compress to v2 (cross-platform) format"""
        import cv2
        
        pipeline = self._get_pipeline()
        
        # First, create v1 blueprint
        temp_v1_path = output_path + ".tmp"
        pipeline.process_asset(input_path, temp_v1_path)
        
        # Load the blueprint
        from src.schema.blueprint import HelixBlueprint
        blueprint = HelixBlueprint.load(temp_v1_path)
        
        # Generate preview
        from src.core.preview_generator import preview_generator
        from src.core.hlx_codec import encode_v2
        
        img = cv2.imread(input_path)
        preview_bytes = preview_generator.generate(img)
        
        # Encode as v2
        hlx_v2_data = encode_v2(blueprint.to_dict(), preview_bytes)
        
        # Write to output
        with open(output_path, 'wb') as f:
            f.write(hlx_v2_data)
        
        # Cleanup temp file
        if os.path.exists(temp_v1_path):
            os.remove(temp_v1_path)
    
    def _print_summary(self, stats: CompressionStats):
        """Print compression summary"""
        print("\n" + "=" * 50)
        print("🧬 HELIX COMPRESSION COMPLETE")
        print("=" * 50)
        print(f"Files processed: {stats.total_files}")
        print(f"Successful: {stats.successful}")
        print(f"Failed: {stats.failed}")
        print(f"Original size: {stats.original_bytes / (1024*1024):.1f} MB")
        print(f"Compressed size: {stats.compressed_bytes / (1024*1024):.1f} MB")
        print(f"Compression ratio: {stats.compression_ratio:.1f}x")
        print(f"Space saved: {stats.space_saved_percent:.1f}%")
        print(f"Time elapsed: {stats.elapsed_seconds:.1f}s")
        print(f"Speed: {stats.successful / max(stats.elapsed_seconds, 0.001):.1f} files/sec")
        print("=" * 50 + "\n")
    
    def compress_file(self, input_path: str, output_path: str) -> Dict[str, Any]:
        """
        Compress a single file.
        
        Returns:
            Dict with original_size, compressed_size, ratio
        """
        original_size = os.path.getsize(input_path)
        
        if self.use_v2_format:
            self._compress_v2(input_path, output_path)
        else:
            pipeline = self._get_pipeline()
            pipeline.process_asset(input_path, output_path)
        
        compressed_size = os.path.getsize(output_path)
        
        return {
            "input": input_path,
            "output": output_path,
            "original_size": original_size,
            "compressed_size": compressed_size,
            "ratio": round(original_size / compressed_size, 2) if compressed_size > 0 else 0,
            "saved_percent": round((1 - compressed_size / original_size) * 100, 1) if original_size > 0 else 0
        }
    
    def estimate_compression(self, 
                            input_dir: str, 
                            sample_size: int = 10) -> Dict[str, Any]:
        """
        Estimate compression ratio by sampling files.
        
        Args:
            input_dir: Directory to analyze
            sample_size: Number of files to sample
            
        Returns:
            Dict with estimated_ratio, estimated_output_size, etc.
        """
        import tempfile
        import random
        
        input_path = Path(input_dir)
        
        # Find image files
        image_files = []
        for ext in self.SUPPORTED_FORMATS:
            image_files.extend(input_path.glob(f"**/*{ext}"))
        
        if not image_files:
            return {"error": "No image files found"}
        
        # Sample files
        sample_files = random.sample(image_files, min(sample_size, len(image_files)))
        
        total_original = 0
        total_compressed = 0
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for img_path in sample_files:
                out_path = os.path.join(tmpdir, f"{img_path.stem}.hlx")
                
                try:
                    result = self.compress_file(str(img_path), out_path)
                    total_original += result["original_size"]
                    total_compressed += result["compressed_size"]
                except Exception as e:
                    print(f"[WARN] Sample compression failed: {e}")
        
        if total_compressed == 0:
            return {"error": "Could not compress sample files"}
        
        ratio = total_original / total_compressed
        
        # Estimate full directory
        all_original_size = sum(f.stat().st_size for f in image_files)
        estimated_output = all_original_size / ratio
        
        return {
            "sample_files": len(sample_files),
            "total_files": len(image_files),
            "sample_original_mb": round(total_original / (1024*1024), 2),
            "sample_compressed_mb": round(total_compressed / (1024*1024), 2),
            "estimated_ratio": round(ratio, 2),
            "total_original_mb": round(all_original_size / (1024*1024), 2),
            "estimated_output_mb": round(estimated_output / (1024*1024), 2),
            "estimated_savings_mb": round((all_original_size - estimated_output) / (1024*1024), 2),
            "estimated_savings_percent": round((1 - 1/ratio) * 100, 1)
        }
