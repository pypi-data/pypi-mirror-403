"""
HELIX Loader
============
PyTorch-compatible DataLoader for HELIX datasets.
Supports parallel materialization and variant generation.
"""

import os
import sys
from pathlib import Path
from typing import Iterator, Optional, List, Callable, Any
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

sys.path.insert(0, str(Path(__file__).parent.parent))

from .dataset import HelixDataset


class HelixLoader:
    """
    PyTorch-compatible DataLoader for HELIX datasets.
    
    🚀 Key Features:
    - Parallel materialization (multiple workers)
    - Variant generation (N different versions per image)
    - Shuffling and batching
    - Prefetching for speed
    
    Usage (PyTorch-style):
        dataset = HelixDataset("/data/training_hlx/")
        loader = HelixLoader(dataset, batch_size=32, num_workers=4)
        
        for batch in loader:
            # batch is (B, H, W, C) numpy array
            images = torch.from_numpy(batch).permute(0, 3, 1, 2)
            model(images)
    
    Usage (with variants):
        loader = HelixLoader(dataset, batch_size=32, variants_per_image=3)
        
        for batch in loader:
            # Each epoch gets different variants!
            pass
    """
    
    def __init__(self,
                 dataset: HelixDataset,
                 batch_size: int = 32,
                 shuffle: bool = True,
                 num_workers: int = 4,
                 variants_per_image: int = 1,
                 drop_last: bool = False,
                 transform: Optional[Callable] = None,
                 prefetch_factor: int = 2):
        """
        Initialize HELIX DataLoader.
        
        Args:
            dataset: HelixDataset instance
            batch_size: Images per batch
            shuffle: Randomize order each epoch
            num_workers: Parallel materialization threads
            variants_per_image: Generate N variants per image (for augmentation)
            drop_last: Drop incomplete final batch
            transform: Optional transform function(img) -> img
            prefetch_factor: How many batches to prefetch
        """
        self.dataset = dataset
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.num_workers = num_workers
        self.variants_per_image = variants_per_image
        self.drop_last = drop_last
        self.transform = transform
        self.prefetch_factor = prefetch_factor
        
        # Internal state
        self._epoch = 0
        self._indices: List[int] = []
        
        print(f"[HELIX Loader] Initialized: batch={batch_size}, workers={num_workers}, variants={variants_per_image}")
    
    def __len__(self) -> int:
        """Number of batches per epoch"""
        total_samples = len(self.dataset) * self.variants_per_image
        if self.drop_last:
            return total_samples // self.batch_size
        return (total_samples + self.batch_size - 1) // self.batch_size
    
    def __iter__(self) -> Iterator[np.ndarray]:
        """Iterate over batches"""
        # Build index list (with variants)
        self._indices = []
        for idx in range(len(self.dataset)):
            for variant in range(self.variants_per_image):
                self._indices.append((idx, variant))
        
        # Shuffle if enabled
        if self.shuffle:
            np.random.shuffle(self._indices)
        
        # Batch and yield
        batch_start = 0
        while batch_start < len(self._indices):
            batch_end = min(batch_start + self.batch_size, len(self._indices))
            
            # Skip incomplete batch if drop_last
            if self.drop_last and (batch_end - batch_start) < self.batch_size:
                break
            
            batch_indices = self._indices[batch_start:batch_end]
            batch = self._materialize_batch(batch_indices)
            
            yield batch
            
            batch_start = batch_end
        
        self._epoch += 1
    
    def _materialize_batch(self, indices: List[tuple]) -> np.ndarray:
        """
        Materialize a batch of images, potentially in parallel.
        
        Args:
            indices: List of (dataset_idx, variant_num) tuples
            
        Returns:
            Numpy array of shape (batch_size, H, W, C)
        """
        if self.num_workers <= 1:
            # Single-threaded
            images = [self._materialize_single(idx, var) for idx, var in indices]
        else:
            # Multi-threaded
            images = [None] * len(indices)
            
            with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
                future_to_pos = {
                    executor.submit(self._materialize_single, idx, var): pos
                    for pos, (idx, var) in enumerate(indices)
                }
                
                for future in as_completed(future_to_pos):
                    pos = future_to_pos[future]
                    try:
                        images[pos] = future.result()
                    except Exception as e:
                        print(f"[WARN] Error materializing index {indices[pos]}: {e}")
                        # Return blank image on error
                        images[pos] = np.zeros((512, 512, 3), dtype=np.uint8)
        
        # Stack into batch
        # Note: images may have different sizes - resize to first image's size
        if images:
            target_shape = images[0].shape
            for i, img in enumerate(images):
                if img.shape != target_shape:
                    import cv2
                    images[i] = cv2.resize(img, (target_shape[1], target_shape[0]))
        
        batch = np.stack(images, axis=0)
        
        return batch
    
    def _materialize_single(self, idx: int, variant: int) -> np.ndarray:
        """Materialize a single image"""
        if variant > 0:
            img = self.dataset.get_variant(idx, variant)
        else:
            img = self.dataset[idx]
        
        # Apply transform if provided
        if self.transform is not None:
            img = self.transform(img)
        
        return img


# Convenience function for one-line creation
def create_loader(path: str, 
                  batch_size: int = 32,
                  target_resolution: str = "1080p",
                  num_workers: int = 4,
                  **kwargs) -> HelixLoader:
    """
    Convenience function to create a HelixLoader in one line.
    
    Usage:
        loader = create_loader("/data/hlx/", batch_size=64)
        for batch in loader:
            train(batch)
    """
    dataset = HelixDataset(path, target_resolution=target_resolution)
    return HelixLoader(dataset, batch_size=batch_size, num_workers=num_workers, **kwargs)
