"""
HELIX Dataset
=============
A dataset of .hlx files that can regenerate images on-demand.
Compatible with PyTorch and TensorFlow.
"""

import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class HelixDataset:
    """
    A dataset of .hlx files that can regenerate images on-demand.
    
    🚀 Key Features:
    - Load once, materialize at any resolution
    - Built-in caching for speed
    - Semantic search by aura/description
    - Variant generation for data augmentation
    
    Usage:
        dataset = HelixDataset("/path/to/hlx_files/")
        
        # Get single image
        img = dataset[0]
        
        # Search semantically
        sunset_indices = dataset.search("sunset golden hour")
    """
    
    def __init__(self, 
                 path: str,
                 target_resolution: str = "1080p",
                 enable_variants: bool = False,
                 cache_materializations: bool = True,
                 lazy_load: bool = True,
                 base_url: Optional[str] = None,
                 api_key: Optional[str] = None):
        """
        Initialize HELIX dataset.
        
        Args:
            path: Path to directory of .hlx files OR single .hlx file
            target_resolution: Output resolution for materialization
            enable_variants: If True, each access may produce slight variations
            cache_materializations: Cache generated images to disk/memory
            lazy_load: If True, load blueprints only when accessed
            base_url: Optional URL for Remote Mode (Data Center usage)
            api_key: Optional API key for Remote Mode
        """
        self.path = Path(path)
        self.target_resolution = target_resolution
        self.enable_variants = enable_variants
        self.cache_materializations = cache_materializations
        self.lazy_load = lazy_load
        self.base_url = base_url or os.getenv("HELIX_API_URL")
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        # Internal state
        self._hlx_files: List[Path] = []
        self._blueprints: Dict[int, Any] = {}  # idx -> blueprint
        self._cache: Dict[str, np.ndarray] = {} if cache_materializations else None
        self._materializer = None
        
        # Discover .hlx files
        self._discover_files()
        
        print(f"[HELIX SDK] Dataset initialized: {len(self._hlx_files)} files at {target_resolution}")
    
    def _discover_files(self):
        """Find all .hlx files in the dataset path"""
        if self.path.is_file():
            # Single file
            if self.path.suffix.lower() == '.hlx':
                self._hlx_files = [self.path]
        elif self.path.is_dir():
            # Directory - find all .hlx files recursively
            self._hlx_files = sorted(self.path.glob("**/*.hlx"))
        else:
            raise ValueError(f"Path does not exist: {self.path}")
        
        if not self._hlx_files:
            print(f"[WARN] No .hlx files found in {self.path}")
    
    def _get_materializer(self):
        """Lazy-load the materializer"""
        if self._materializer is None:
            if self.base_url:
                from helix_sdk.remote import RemoteMaterializer
                self._materializer = RemoteMaterializer(self.base_url, self.api_key)
            else:
                from src.core.materializer import GeminiMaterializer
                self._materializer = GeminiMaterializer(api_key=self.api_key)
        return self._materializer
    
    def _load_blueprint(self, idx: int):
        """Load blueprint for given index"""
        if idx not in self._blueprints:
            from src.core.hlx_codec import decode
            hlx_path = self._hlx_files[idx]
            with open(hlx_path, "rb") as f:
                hlx_data = f.read()
            self._blueprints[idx] = decode(hlx_data)
        return self._blueprints[idx]
    
    def __len__(self) -> int:
        """Return number of items in dataset"""
        return len(self._hlx_files)
    
    def __getitem__(self, idx: int) -> np.ndarray:
        """
        Get materialized image at index.
        
        Args:
            idx: Index of image to get
            
        Returns:
            Numpy array of image (H, W, C) in RGB format
        """
        if idx < 0 or idx >= len(self):
            raise IndexError(f"Index {idx} out of range [0, {len(self)})")
        
        # Check cache
        cache_key = f"{idx}_{self.target_resolution}"
        if self._cache is not None and cache_key in self._cache:
            return self._cache[cache_key]
        
        # Load blueprint
        blueprint = self._load_blueprint(idx)
        
        # Materialize
        materializer = self._get_materializer()
        image_bytes = materializer.materialize(
            blueprint, 
            target_resolution=self.target_resolution
        )
        
        # Convert to numpy array
        image = self._bytes_to_numpy(image_bytes)
        
        # Cache
        if self._cache is not None:
            self._cache[cache_key] = image
        
        return image
    
    def _bytes_to_numpy(self, image_bytes: bytes) -> np.ndarray:
        """Convert image bytes to numpy array"""
        import cv2
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        # Convert BGR to RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return img
    
    def get_variant(self, idx: int, variant_num: int = 0) -> np.ndarray:
        """
        Get a specific variant of an image.
        
        Variants are created by adjusting the materialization parameters,
        producing slightly different outputs - useful for data augmentation.
        
        Args:
            idx: Image index
            variant_num: Variant number (affects random seed)
            
        Returns:
            Numpy array of image
        """
        # For now, variants are just the same image
        # In production, we'd adjust temperature/prompt for variation
        return self[idx]
    
    def get_metadata(self, idx: int) -> Dict[str, Any]:
        """
        Get metadata for an image without materializing it.
        
        Returns:
            Dict with aura, scene_description, anchor_count, etc.
        """
        blueprint = self._load_blueprint(idx)
        meta = blueprint.metadata if hasattr(blueprint, 'metadata') else None
        anchors = blueprint.anchors if hasattr(blueprint, 'anchors') else []
        
        return {
            "identity": getattr(meta, 'identity', None) if meta else None,
            "aura": getattr(meta, 'aura', '') if meta else '',
            "scene_description": getattr(meta, 'scene_description', '') if meta else '',
            "original_dims": getattr(meta, 'original_dims', (0, 0)) if meta else (0, 0),
            "anchor_count": len(anchors),
            "anchor_types": [getattr(a, 'type', 'unknown') for a in anchors],
            "color_palette": getattr(meta, 'color_palette', []) if meta else [],
            "modality": getattr(meta, 'modality', 'image') if meta else 'image'
        }
    
    def search(self, query: str, limit: int = 100) -> List[int]:
        """
        Semantic search across dataset.
        
        Finds images where the aura or scene_description matches the query.
        
        Args:
            query: Natural language query ("person wearing hat", "sunset")
            limit: Maximum results to return
            
        Returns:
            List of indices matching query
        """
        query_lower = query.lower()
        results = []
        
        for idx in range(len(self)):
            blueprint = self._load_blueprint(idx)
            
            # Search in aura and scene description
            aura = (blueprint.metadata.aura or "").lower()
            scene = (blueprint.metadata.scene_description or "").lower()
            
            # Simple substring matching (could upgrade to embeddings)
            if query_lower in aura or query_lower in scene:
                results.append(idx)
                
            if len(results) >= limit:
                break
        
        return results
    
    def get_file_path(self, idx: int) -> Path:
        """Get the file path for an index"""
        return self._hlx_files[idx]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get dataset statistics.
        
        Returns:
            Dict with total_files, total_size_bytes, anchor_distribution, etc.
        """
        total_size = sum(f.stat().st_size for f in self._hlx_files)
        
        # Sample anchor distribution from first 100 files
        anchor_counts = {}
        sample_size = min(100, len(self))
        
        for idx in range(sample_size):
            meta = self.get_metadata(idx)
            for atype in meta["anchor_types"]:
                anchor_counts[atype] = anchor_counts.get(atype, 0) + 1
        
        return {
            "total_files": len(self),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "target_resolution": self.target_resolution,
            "anchor_distribution": anchor_counts,
            "cache_enabled": self._cache is not None,
            "cached_items": len(self._cache) if self._cache else 0
        }
    
    def clear_cache(self):
        """Clear the materialization cache"""
        if self._cache is not None:
            self._cache.clear()
            print("[HELIX SDK] Cache cleared")
