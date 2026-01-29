"""
HELIX SDK Core Module
=====================

The unified entry point for the HELIX SDK.
Provides high-level APIs for compression, materialization, and dataset management.

Usage:
    from helix_sdk import HelixSDK
    
    sdk = HelixSDK(api_key="your-gemini-key")
    sdk.compress_image("photo.jpg", "photo.hlx")
    sdk.materialize("photo.hlx", "output.png", resolution="4K")
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import time

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class Resolution(Enum):
    """Supported output resolutions for materialization."""
    RES_256P = "256p"
    RES_512P = "512p"  
    RES_720P = "720p"
    RES_1080P = "1080p"
    RES_1440P = "1440p"
    RES_4K = "4K"
    RES_8K = "8K"
    
    @classmethod
    def from_string(cls, s: str) -> "Resolution":
        """Convert string to Resolution enum."""
        mapping = {
            "256p": cls.RES_256P,
            "512p": cls.RES_512P,
            "720p": cls.RES_720P,
            "1080p": cls.RES_1080P,
            "1440p": cls.RES_1440P,
            "4k": cls.RES_4K,
            "4K": cls.RES_4K,
            "8k": cls.RES_8K,
            "8K": cls.RES_8K,
        }
        return mapping.get(s, cls.RES_1080P)


class HLXFormat(Enum):
    """HLX file format versions."""
    V1 = "v1"  # Standard format
    V2 = "v2"  # Cross-platform (valid JPEG wrapper)


@dataclass
class CompressionResult:
    """Result of compressing a single file."""
    input_path: str
    output_path: str
    input_size: int
    output_size: int
    compression_ratio: float
    success: bool
    error: Optional[str] = None
    processing_time_ms: int = 0
    anchors_detected: int = 0
    format_version: str = "v1"


@dataclass 
class MaterializationResult:
    """Result of materializing an HLX file."""
    input_path: str
    output_path: str
    target_resolution: str
    output_width: int
    output_height: int
    success: bool
    error: Optional[str] = None
    processing_time_ms: int = 0
    ai_enhanced: bool = False


@dataclass
class BatchStats:
    """Statistics for batch operations."""
    files_processed: int = 0
    files_failed: int = 0
    total_input_bytes: int = 0
    total_output_bytes: int = 0
    total_time_seconds: float = 0
    errors: List[str] = field(default_factory=list)
    
    @property
    def compression_ratio(self) -> float:
        if self.total_output_bytes == 0:
            return 0
        return self.total_input_bytes / self.total_output_bytes
    
    @property
    def space_saved_percent(self) -> float:
        if self.total_input_bytes == 0:
            return 0
        return (1 - self.total_output_bytes / self.total_input_bytes) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "files_processed": self.files_processed,
            "files_failed": self.files_failed,
            "total_input_bytes": self.total_input_bytes,
            "total_output_bytes": self.total_output_bytes,
            "compression_ratio": round(self.compression_ratio, 2),
            "space_saved_percent": round(self.space_saved_percent, 2),
            "total_time_seconds": round(self.total_time_seconds, 2)
        }


class HelixSDK:
    """
    Main HELIX SDK class.
    
    Provides high-level APIs for:
    - Image compression to HLX format
    - Materialization at any resolution
    - Batch processing
    - Dataset management
    
    Example:
        sdk = HelixSDK(api_key="your-gemini-key")
        
        # Compress single file
        result = sdk.compress("photo.jpg", "photo.hlx")
        
        # Materialize at 4K
        result = sdk.materialize("photo.hlx", "photo_4k.png", resolution="4K")
        
        # Batch compress directory
        stats = sdk.compress_directory("./images/", "./hlx_output/")
    """
    
    VERSION = "1.0.0"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        mode: str = "auto",  # "auto", "local", "remote"
        default_format: HLXFormat = HLXFormat.V2,
        default_resolution: Resolution = Resolution.RES_1080P,
        cache_materializations: bool = True,
        verbose: bool = True
    ):
        """
        Initialize the HELIX SDK.
        
        Args:
            api_key: Gemini API key. If not provided, reads from GEMINI_API_KEY env var.
            base_url: URL of HELIX API (e.g., "http://localhost:8000") for remote mode.
            mode: "local" (use local models), "remote" (use API), or "auto" (detect).
            default_format: Default HLX format for compression (V1 or V2).
            default_resolution: Default resolution for materialization.
            cache_materializations: Whether to cache materialized images.
            verbose: Whether to print progress messages.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.base_url = base_url or os.getenv("HELIX_API_URL")
        self.mode = mode.lower()
        self.default_format = default_format
        self.default_resolution = default_resolution
        self.cache_materializations = cache_materializations
        self.verbose = verbose
        
        # Lazy-load components
        self._pipeline = None
        self._materializer = None
        self._cache: Dict[str, bytes] = {}
        
        # Determine actual mode
        if self.mode == "auto":
            if self.base_url:
                self.mode = "remote"
            else:
                self.mode = "local"
                
        if self.verbose:
            print(f"[HELIX SDK v{self.VERSION}] Initialized ({self.mode} mode)")
            if self.mode == "remote":
                print(f"[HELIX SDK] Connected to {self.base_url}")
            elif self.api_key:
                print(f"[HELIX SDK] API key configured ({'*' * 8}...{self.api_key[-4:]})")
            else:
                print("[HELIX SDK] WARNING: No API key - running in mock mode")
    
    @property
    def pipeline(self):
        """Lazy-load the compression pipeline."""
        if self._pipeline is None:
            if self.mode == "remote":
                from helix_sdk.remote import RemotePipeline
                if not self.base_url:
                    raise ValueError("base_url is required for remote mode")
                self._pipeline = RemotePipeline(self.base_url, self.api_key)
            else:
                from src.core.pipeline import HelixPipeline
                self._pipeline = HelixPipeline()
        return self._pipeline
    
    @property
    def materializer(self):
        """Lazy-load the materializer."""
        if self._materializer is None:
            if self.mode == "remote":
                from helix_sdk.remote import RemoteMaterializer
                if not self.base_url:
                    raise ValueError("base_url is required for remote mode")
                self._materializer = RemoteMaterializer(self.base_url, self.api_key)
            else:
                from src.core.materializer import GeminiMaterializer
                self._materializer = GeminiMaterializer(api_key=self.api_key)
        return self._materializer
    
    def compress(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        format_version: HLXFormat = None,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> CompressionResult:
        """
        Compress an image to HLX format.
        
        Args:
            input_path: Path to input image (jpg, png, webp).
            output_path: Path for output HLX file. If None, uses input path + .hlx extension.
            format_version: HLX format version (V1 or V2). Defaults to SDK default.
            progress_callback: Optional callback for progress updates.
            
        Returns:
            CompressionResult with compression statistics.
        """
        start_time = time.time()
        format_version = format_version or self.default_format
        
        # Validate input
        input_path = Path(input_path)
        if not input_path.exists():
            return CompressionResult(
                input_path=str(input_path),
                output_path="",
                input_size=0,
                output_size=0,
                compression_ratio=0,
                success=False,
                error=f"Input file not found: {input_path}"
            )
        
        # Determine output path
        if output_path is None:
            output_path = input_path.with_suffix(".hlx")
        else:
            output_path = Path(output_path)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            if progress_callback:
                progress_callback("Loading image...")
            
            # Get input size
            input_size = input_path.stat().st_size
            
            if progress_callback:
                progress_callback("Extracting anchors...")
            
            # Use file-based pipeline API
            # First, process to create the blueprint file
            temp_blueprint_path = output_path.with_suffix('.temp.hlx')
            self.pipeline.process_asset(str(input_path), str(temp_blueprint_path))
            
            if progress_callback:
                progress_callback("Encoding HLX...")
            
            # Now read the blueprint and encode to proper format
            from src.core.hlx_codec import encode, decode, encode_v2
            
            # Load the blueprint
            with open(temp_blueprint_path, 'rb') as f:
                blueprint_data = f.read()
            blueprint = decode(blueprint_data)
            
            # Read original image for stitching data
            with open(input_path, "rb") as f:
                image_bytes = f.read()
            
            # Encode to requested format
            if format_version == HLXFormat.V2:
                hlx_data = encode_v2(blueprint, image_bytes)
            else:
                hlx_data = encode(blueprint)
            
            if progress_callback:
                progress_callback("Saving HLX file...")
            
            # Write output
            with open(output_path, "wb") as f:
                f.write(hlx_data)
            
            # Clean up temp file
            if temp_blueprint_path.exists():
                temp_blueprint_path.unlink()
            
            output_size = output_path.stat().st_size
            processing_time = int((time.time() - start_time) * 1000)
            
            # Count anchors
            anchors_count = len(blueprint.anchors) if hasattr(blueprint, 'anchors') else 0
            
            if self.verbose:
                ratio = input_size / output_size if output_size > 0 else 0
                print(f"[HELIX] Compressed: {input_path.name} → {output_path.name}")
                print(f"        {input_size/1024:.1f}KB → {output_size/1024:.1f}KB ({ratio:.1f}x)")
            
            return CompressionResult(
                input_path=str(input_path),
                output_path=str(output_path),
                input_size=input_size,
                output_size=output_size,
                compression_ratio=input_size / output_size if output_size > 0 else 0,
                success=True,
                processing_time_ms=processing_time,
                anchors_detected=anchors_count,
                format_version=format_version.value
            )
            
        except Exception as e:
            return CompressionResult(
                input_path=str(input_path),
                output_path=str(output_path),
                input_size=input_path.stat().st_size if input_path.exists() else 0,
                output_size=0,
                compression_ratio=0,
                success=False,
                error=str(e),
                processing_time_ms=int((time.time() - start_time) * 1000)
            )
    
    def materialize(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        resolution: Union[str, Resolution] = None,
        use_ai_enhancement: bool = True,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> MaterializationResult:
        """
        Materialize an HLX file to an image.
        
        Args:
            input_path: Path to HLX file.
            output_path: Path for output image. If None, uses input path + resolution + .png.
            resolution: Target resolution (e.g., "4K", "1080p"). Defaults to SDK default.
            use_ai_enhancement: Whether to use AI for enhancement.
            progress_callback: Optional callback for progress updates.
            
        Returns:
            MaterializationResult with output details.
        """
        start_time = time.time()
        
        # Normalize resolution
        if resolution is None:
            resolution = self.default_resolution
        if isinstance(resolution, str):
            resolution = Resolution.from_string(resolution)
        
        resolution_str = resolution.value
        
        # Validate input
        input_path = Path(input_path)
        if not input_path.exists():
            return MaterializationResult(
                input_path=str(input_path),
                output_path="",
                target_resolution=resolution_str,
                output_width=0,
                output_height=0,
                success=False,
                error=f"Input file not found: {input_path}"
            )
        
        # Determine output path
        if output_path is None:
            output_path = input_path.with_suffix(f".{resolution_str}.png")
        else:
            output_path = Path(output_path)
        
        try:
            if progress_callback:
                progress_callback("Loading HLX blueprint...")
            
            # Load blueprint
            from src.core.hlx_codec import decode
            with open(input_path, "rb") as f:
                hlx_data = f.read()
            
            blueprint = decode(hlx_data)
            
            if progress_callback:
                progress_callback(f"Materializing at {resolution_str}...")
            
            # Check cache
            cache_key = f"{input_path}:{resolution_str}"
            if self.cache_materializations and cache_key in self._cache:
                image_bytes = self._cache[cache_key]
                ai_enhanced = False
            else:
                # Materialize
                image_bytes = self.materializer.materialize(
                    blueprint=blueprint,
                    target_resolution=resolution_str
                )
                
                if self.cache_materializations:
                    self._cache[cache_key] = image_bytes
                
                ai_enhanced = not self.materializer.mock_mode
            
            if progress_callback:
                progress_callback("Saving output...")
            
            # Write output
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(image_bytes)
            
            # Get dimensions
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(image_bytes))
            width, height = img.size
            
            processing_time = int((time.time() - start_time) * 1000)
            
            if self.verbose:
                print(f"[HELIX] Materialized: {input_path.name} → {output_path.name}")
                print(f"        Resolution: {width}x{height} ({resolution_str})")
            
            return MaterializationResult(
                input_path=str(input_path),
                output_path=str(output_path),
                target_resolution=resolution_str,
                output_width=width,
                output_height=height,
                success=True,
                processing_time_ms=processing_time,
                ai_enhanced=ai_enhanced
            )
            
        except Exception as e:
            return MaterializationResult(
                input_path=str(input_path),
                output_path=str(output_path),
                target_resolution=resolution_str,
                output_width=0,
                output_height=0,
                success=False,
                error=str(e),
                processing_time_ms=int((time.time() - start_time) * 1000)
            )
    
    def compress_directory(
        self,
        input_dir: str,
        output_dir: str,
        recursive: bool = True,
        extensions: List[str] = None,
        format_version: HLXFormat = None,
        workers: int = 4,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> BatchStats:
        """
        Compress all images in a directory to HLX format.
        
        Args:
            input_dir: Directory containing images.
            output_dir: Directory for output HLX files.
            recursive: Whether to process subdirectories.
            extensions: File extensions to process. Defaults to ['.jpg', '.jpeg', '.png', '.webp'].
            format_version: HLX format version.
            workers: Number of parallel workers.
            progress_callback: Callback(current, total, filename) for progress updates.
            
        Returns:
            BatchStats with compression statistics.
        """
        extensions = extensions or ['.jpg', '.jpeg', '.png', '.webp']
        format_version = format_version or self.default_format
        
        input_dir = Path(input_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Find all images
        if recursive:
            files = [f for f in input_dir.rglob("*") if f.suffix.lower() in extensions]
        else:
            files = [f for f in input_dir.glob("*") if f.suffix.lower() in extensions]
        
        stats = BatchStats()
        start_time = time.time()
        
        if self.verbose:
            print(f"[HELIX] Found {len(files)} images to compress")
        
        for i, input_file in enumerate(files):
            # Calculate relative output path
            rel_path = input_file.relative_to(input_dir)
            output_file = output_dir / rel_path.with_suffix(".hlx")
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            if progress_callback:
                progress_callback(i + 1, len(files), input_file.name)
            
            result = self.compress(
                input_path=str(input_file),
                output_path=str(output_file),
                format_version=format_version
            )
            
            if result.success:
                stats.files_processed += 1
                stats.total_input_bytes += result.input_size
                stats.total_output_bytes += result.output_size
            else:
                stats.files_failed += 1
                if result.error:
                    stats.errors.append(f"{input_file.name}: {result.error}")
        
        stats.total_time_seconds = time.time() - start_time
        
        if self.verbose:
            print(f"[HELIX] Batch complete: {stats.files_processed}/{len(files)} files")
            print(f"        Compression: {stats.compression_ratio:.1f}x ({stats.space_saved_percent:.1f}% saved)")
        
        return stats
    
    def get_info(self, hlx_path: str) -> Dict[str, Any]:
        """
        Get information about an HLX file.
        
        Args:
            hlx_path: Path to HLX file.
            
        Returns:
            Dictionary with blueprint metadata.
        """
        from src.core.hlx_codec import decode
        
        with open(hlx_path, "rb") as f:
            hlx_data = f.read()
        
        blueprint = decode(hlx_data)
        
        return {
            "file_size": len(hlx_data),
            "original_dimensions": blueprint.metadata.original_dims if hasattr(blueprint.metadata, 'original_dims') else None,
            "anchors_count": len(blueprint.anchors) if hasattr(blueprint, 'anchors') else 0,
            "mesh_constraints": len(blueprint.mesh.constraints) if hasattr(blueprint.mesh, 'constraints') else 0,
            "scene_description": blueprint.metadata.scene_description if hasattr(blueprint.metadata, 'scene_description') else None,
            "aura": blueprint.metadata.aura if hasattr(blueprint.metadata, 'aura') else None,
        }
    
    def clear_cache(self):
        """Clear the materialization cache."""
        self._cache.clear()
        if self.verbose:
            print("[HELIX] Cache cleared")
    
    @staticmethod
    def get_supported_formats() -> Dict[str, Any]:
        """Get information about supported file formats."""
        return {
            "input_formats": [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"],
            "output_formats": [".hlx"],
            "hlx_versions": ["v1", "v2"],
            "resolutions": [r.value for r in Resolution],
            "recommended_format": "v2",
            "recommended_resolution": "1080p"
        }


# Convenience function for quick access
def create_sdk(api_key: Optional[str] = None, verbose: bool = True) -> HelixSDK:
    """
    Create a new HELIX SDK instance.
    
    Args:
        api_key: Gemini API key (optional, reads from env).
        verbose: Whether to print progress messages.
        
    Returns:
        Configured HelixSDK instance.
    """
    return HelixSDK(api_key=api_key, verbose=verbose)


# Module exports
__all__ = [
    "HelixSDK",
    "Resolution",
    "HLXFormat",
    "CompressionResult",
    "MaterializationResult",
    "BatchStats",
    "create_sdk"
]
