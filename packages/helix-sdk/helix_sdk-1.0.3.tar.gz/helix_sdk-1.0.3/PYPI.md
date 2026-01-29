# HELIX SDK

Semantic image compression for AI training. Convert images into compact blueprints containing identity-critical information for regeneration at any resolution.

## What's New in 1.0.2

- **🌐 Remote Mode** - Use HELIX via API without heavy local dependencies
- **📦 Lightweight Install** - Core package now only requires `httpx`, `numpy`, `pillow`
- **🏢 Data Center Ready** - Perfect for cloud storage and on-demand materialization

## Features

- **10-20x compression** - Store blueprints, not pixels
- **On-demand materialization** - Reconstruct at 256p to 8K from same file
- **Infinite variants** - Generate augmentation variants per image
- **ML-ready loaders** - PyTorch-compatible Dataset and DataLoader
- **Remote or Local** - Use API or run locally with full models

## Installation

```bash
# Lightweight (Remote Mode - recommended for most users)
pip install helix-sdk

# With local processing (requires Gemini API key)
pip install helix-sdk[local]

# With PyTorch support
pip install helix-sdk[ml]
```

## Quick Start

### Remote Mode (Recommended)

```python
from helix_sdk import HelixSDK

# Connect to HELIX API (no local models needed!)
sdk = HelixSDK(base_url="https://api.helix-codec.dev")

# Compress - sends image to API, receives .hlx
result = sdk.compress("image.jpg", "image.hlx")

# Materialize at any resolution
sdk.materialize("image.hlx", "output.png", resolution="4K")
```

### Local Mode

```python
from helix_sdk import HelixSDK

# Use local models (requires pip install helix-sdk[local])
sdk = HelixSDK(mode="local", api_key="your-gemini-key")

sdk.compress("image.jpg", "image.hlx")
sdk.materialize("image.hlx", "output.png", resolution="4K")
```

## ML Training

```python
from helix_sdk import HelixDataset, HelixLoader

# Works with both local and remote mode!
dataset = HelixDataset(
    "/data/hlx/", 
    target_resolution="512p",
    base_url="https://api.helix-codec.dev"  # Optional: use API
)

loader = HelixLoader(dataset, batch_size=64, num_workers=4)

for batch in loader:
    model.train_step(batch)
```

## API Reference

### HelixSDK

```python
HelixSDK(
    api_key=None,           # Gemini API key (for local mode)
    base_url=None,          # HELIX API URL (enables remote mode)
    mode="auto",            # "auto", "local", or "remote"
    default_resolution="1080p"
)
```

| Method | Description |
|--------|-------------|
| `compress(input, output)` | Compress image to HLX |
| `materialize(input, output, resolution)` | Reconstruct from HLX |
| `compress_directory(in_dir, out_dir)` | Batch compression |
| `get_info(hlx_path)` | Get HLX metadata |

### HelixDataset

```python
HelixDataset(
    path="/data/hlx/",
    target_resolution="512p",
    enable_variants=True,
    cache_materializations=True,
    base_url=None,          # Optional: enable remote mode
    api_key=None
)
```

### BatchCompressor

```python
from helix_sdk import BatchCompressor

compressor = BatchCompressor(workers=8)
stats = compressor.compress_directory("/images/", "/hlx/")
```

## CLI

```bash
helix compress image.jpg
helix materialize image.hlx -r 4K
helix batch /images/ /output/ -w 8
helix info image.hlx
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `HELIX_API_URL` | Default API URL for remote mode |
| `GEMINI_API_KEY` | Gemini API key for local mode |

## Benchmarks

| Metric | Value |
|--------|-------|
| Compression Ratio | 10-20x |
| Identity Match (SSIM) | 98.7% |
| Materialization Time | ~3s |

## Requirements

- Python >= 3.10
- For local mode: Gemini API key (`GEMINI_API_KEY`)
- For remote mode: HELIX API access (`HELIX_API_URL`)

## License

MIT
