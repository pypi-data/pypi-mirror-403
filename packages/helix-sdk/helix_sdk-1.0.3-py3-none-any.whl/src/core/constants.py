"""
HELIX Constants Configuration
=============================
Central configuration for all HELIX processing parameters.
Ensures deterministic encoding with consistent quality settings.
"""

import os

# =============================================================================
# QUALITY SETTINGS (Trade-off: Higher = Better Quality, Larger Files)
# =============================================================================

# Background anchor settings
BACKGROUND_MAX_DIMENSION = 4096  # Max width/height for background (4096 for 8K support)
BACKGROUND_JPEG_QUALITY = 82     # JPEG quality for background (0-100)

# Face anchor settings  
FACE_MAX_DIMENSION = 620         # Max width/height for face crops
FACE_JPEG_QUALITY = 80           # JPEG quality for face crops (0-100)

# Output materialization settings
OUTPUT_JPEG_QUALITY = 92         # Final output JPEG quality (0-100)
OUTPUT_FORMAT = 'JPEG'           # Output format: 'JPEG' or 'PNG'

# =============================================================================
# DETECTION SETTINGS (Affect consistency)
# =============================================================================

# OpenCV Haar Cascade settings (for deterministic detection)
HAAR_SCALE_FACTOR = 1.1          # Scale factor for multi-scale detection
HAAR_MIN_NEIGHBORS = 5           # Min neighbors for face candidate
HAAR_MIN_SIZE = (30, 30)         # Minimum face size in pixels

# =============================================================================
# VERIFICATION SETTINGS
# =============================================================================

# Face position drift tolerance (0.0 - 1.0, where 0.15 = 15%)
VERIFICATION_DRIFT_TOLERANCE = 0.15

# =============================================================================
# EXTRACTION MODE
# =============================================================================

# Force extraction mode: 'auto', 'gemini', 'opencv'
# 'auto' = Use Gemini if available, fallback to OpenCV
# 'gemini' = Only use Gemini (fail if unavailable)
# 'opencv' = Only use OpenCV (deterministic, no API calls)
EXTRACTION_MODE = os.getenv('HELIX_EXTRACTION_MODE', 'opencv')

# =============================================================================
# AI MODEL SETTINGS
# =============================================================================

# Gemini model for extraction
GEMINI_EXTRACTION_MODEL = 'gemini-2.0-flash'

# Gemini model for materialization enhancement
GEMINI_MATERIALIZE_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')

# Temperature for AI generation (lower = more deterministic)
AI_TEMPERATURE = 0.3

# =============================================================================
# ENCRYPTION SETTINGS
# =============================================================================

# HLX format version
HLX_FORMAT_VERSION = 1

# Magic header
HLX_MAGIC_HEADER = b"HLX\x00"

# =============================================================================
# COMPRESSION TARGETS (Reference only - not enforced)
# =============================================================================

# Target compression ratio (informational)
TARGET_COMPRESSION_RATIO = 6  # ~6x compression for good quality/size balance

# Maximum acceptable output size relative to input
MAX_OUTPUT_RATIO = 1.0  # Output should never exceed original size
