import os
import glob
import json
import logging
from typing import Optional, Callable, List, Tuple
from pathlib import Path

# Try importing torch/PIL, but don't fail if missing (wrapper usage)
try:
    import torch
    from torch.utils.data import Dataset
    from PIL import Image
    HAS_TORCH = True
except ImportError:
    Dataset = object
    HAS_TORCH = False

from src.core.materializer import GeminiMaterializer
from src.schema.blueprint import HelixBlueprint

logger = logging.getLogger("HelixDataset")

class HelixDataset(Dataset):
    """
    A PyTorch Dataset wrapper for Project HELIX (.hlx) blueprints.
    
    Features:
    - Loads .hlx files directly.
    - Caches materialized images to disk to avoid re-generating (API cost/latency).
    - Supports on-the-fly Variant Generation with 'context' injection.
    
    Usage:
        dataset = HelixDataset(
            root_dir="./my_blueprints",
            cache_dir="./my_cache",
            context="cyberpunk style",
            variants_per_image=1  # >1 means we generate N variants per blueprint
        )
        loader = DataLoader(dataset, batch_size=32)
    """

    def __init__(
        self,
        root_dir: str,
        cache_dir: str = "./helix_cache",
        transform: Optional[Callable] = None,
        context: Optional[str] = None,
        variants_per_image: int = 1,
        force_regenerate: bool = False
    ):
        if not HAS_TORCH:
            raise ImportError("PyTorch is not installed. Please pip install torch torchvision.")

        self.root_dir = root_dir
        self.cache_dir = cache_dir
        self.transform = transform
        self.context = context
        self.variants_per_image = variants_per_image
        self.force_regenerate = force_regenerate
        
        self.materializer = GeminiMaterializer()
        
        # Find all .hlx files
        self.hlx_files = sorted(glob.glob(os.path.join(root_dir, "**/*.hlx"), recursive=True))
        if not self.hlx_files:
            logger.warning(f"No .hlx files found in {root_dir}")
            
        # Ensure cache exists
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Index the dataset
        # We map index -> (hlx_path, variant_index)
        self.index_map: List[Tuple[str, int]] = []
        for hlx_path in self.hlx_files:
            for v_idx in range(variants_per_image):
                self.index_map.append((hlx_path, v_idx))

    def __len__(self):
        return len(self.index_map)

    def __getitem__(self, idx):
        hlx_path, variant_idx = self.index_map[idx]
        
        # Determine cache key/filename
        # structure: {stem}_v{idx}_{context_hash}.png
        stem = Path(hlx_path).stem
        context_str = self.context.replace(" ", "_") if self.context else "original"
        cache_filename = f"{stem}_v{variant_idx}_{context_str}.png"
        cache_path = os.path.join(self.cache_dir, cache_filename)
        
        # Check cache
        if os.path.exists(cache_path) and not self.force_regenerate:
            try:
                image = Image.open(cache_path).convert("RGB")
                if self.transform:
                    image = self.transform(image)
                return image
            except Exception as e:
                logger.warning(f"Corrupt cache at {cache_path}, regenerating. Error: {e}")
        
        # Materialize (Slow path)
        try:
            # Load Blueprint
            with open(hlx_path, 'r') as f:
                data = json.load(f)
                blueprint = HelixBlueprint.from_dict(data)
            
            # Apply Context / Variant Logic
            if self.context:
                # Modifying metadata for this generation
                blueprint.metadata.aura = f"{self.context} (Variant {variant_idx})"
                blueprint.metadata.scene_description = f"{blueprint.metadata.scene_description}. Style: {self.context}"
            else:
                # If no context, but multiple variants, we rely on the materializer's temperature
                # to create slight variations, or we could inject a "Variant N" seed.
                # For now, Gemini's temperature 0.6 does the job.
                pass

            # Call Materializer (Blocking API call)
            logger.info(f"Materializing {stem} variant {variant_idx}...")
            image_data = self.materializer.materialize(blueprint)
            
            # Save to Cache
            with open(cache_path, 'wb') as f:
                f.write(image_data)
            
            # Load as PIL
            image = Image.open(cache_path).convert("RGB")
            
            if self.transform:
                image = self.transform(image)
                
            return image
            
        except Exception as e:
            logger.error(f"Failed to materialize {hlx_path}: {e}")
            # Return a blank tensor or error? Standard is create error.
            raise e
