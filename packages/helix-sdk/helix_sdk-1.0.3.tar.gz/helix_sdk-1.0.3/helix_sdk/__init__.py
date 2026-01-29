"""
HELIX SDK - AI-Powered Image Compression
=========================================

Train smarter, not harder. Compress AI training data 10x.

Quick Start:
    from helix_sdk import HelixSDK
    
    sdk = HelixSDK()
    sdk.compress("photo.jpg", "photo.hlx")
    sdk.materialize("photo.hlx", "output.png", resolution="4K")

For ML/AI Training:
    from helix_sdk import HelixDataset, HelixLoader
    
    dataset = HelixDataset("/data/hlx/", target_resolution="512p")
    loader = HelixLoader(dataset, batch_size=64)
    
    for batch in loader:
        model.train(batch)

Documentation: http://your-server/docs/sdk
"""

__version__ = "1.0.3"
__author__ = "HELIX Team"

# Core SDK class
from helix_sdk.core import (
    HelixSDK,
    Resolution,
    HLXFormat,
    CompressionResult,
    MaterializationResult,
    BatchStats,
    create_sdk
)

# Dataset and Loader for ML
from helix_sdk.dataset import HelixDataset
from helix_sdk.loader import HelixLoader

# Batch compression
from helix_sdk.compressor import BatchCompressor

# Module exports
__all__ = [
    # Core
    "HelixSDK",
    "Resolution", 
    "HLXFormat",
    "CompressionResult",
    "MaterializationResult",
    "BatchStats",
    "create_sdk",
    # ML/AI
    "HelixDataset",
    "HelixLoader",
    # Batch
    "BatchCompressor",
    # Version
    "__version__",
]
