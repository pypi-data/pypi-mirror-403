"""
HELIX Preview Generator
=======================
Generates the universal preview layer for cross-platform HLX v2 compatibility.

The preview is a standard JPEG that ANY app can display, while the full
HELIX blueprint enables 4K/8K materialization.
"""

import cv2
import numpy as np
import os
from typing import Optional


class PreviewGenerator:
    """
    Generates the universal preview layer for cross-platform compatibility.
    
    Usage:
        generator = PreviewGenerator()
        preview_jpeg = generator.generate(image, blueprint)
    """
    
    # Preview size (balance between quality and file size)
    PREVIEW_MAX_DIM = 1920  # 1080p-ish
    PREVIEW_JPEG_QUALITY = 75  # Good quality, small size
    
    # Optional watermark settings
    WATERMARK_ENABLED = os.getenv("HELIX_WATERMARK_PREVIEW", "false").lower() == "true"
    
    def generate(self, image: np.ndarray, 
                 aura: str = None,
                 add_watermark: bool = None) -> bytes:
        """
        Generate preview image for cross-platform compatibility.
        
        Args:
            image: Original image as numpy array (BGR format from OpenCV)
            aura: Optional aura description (for future metadata embedding)
            add_watermark: Override for watermark setting
            
        Returns:
            JPEG bytes ready for HLX v2 encoding
        """
        # Resize to preview size
        preview = self._resize_for_preview(image)
        
        # Optional: Add subtle HELIX watermark
        should_watermark = add_watermark if add_watermark is not None else self.WATERMARK_ENABLED
        if should_watermark:
            preview = self._add_watermark(preview)
        
        # Encode to JPEG
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, self.PREVIEW_JPEG_QUALITY]
        success, buffer = cv2.imencode('.jpg', preview, encode_params)
        
        if not success:
            raise ValueError("Failed to encode preview as JPEG")
        
        preview_bytes = buffer.tobytes()
        
        print(f"[PREVIEW] Generated {len(preview_bytes)} byte preview "
              f"({preview.shape[1]}x{preview.shape[0]}) "
              f"{'with watermark' if should_watermark else ''}")
        
        return preview_bytes
    
    def _resize_for_preview(self, image: np.ndarray) -> np.ndarray:
        """Resize maintaining aspect ratio to fit within preview dimensions"""
        h, w = image.shape[:2]
        
        # Calculate scale to fit within max dimensions
        scale = min(self.PREVIEW_MAX_DIM / w, self.PREVIEW_MAX_DIM / h)
        
        if scale >= 1.0:
            return image  # Don't upscale - preview should be <= original
        
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        # Use INTER_AREA for downscaling (best quality)
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        return resized
    
    def _add_watermark(self, image: np.ndarray) -> np.ndarray:
        """Add subtle HELIX watermark to indicate this is a preview"""
        h, w = image.shape[:2]
        
        # Create a copy to avoid modifying original
        output = image.copy()
        
        # Add small "HELIX" text in bottom-right corner
        text = "HELIX"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = max(0.3, min(w, h) / 2000)  # Scale with image size
        thickness = max(1, int(font_scale * 2))
        
        # Get text size
        (text_w, text_h), baseline = cv2.getTextSize(text, font, font_scale, thickness)
        
        # Position: bottom-right with padding
        padding = 10
        x = w - text_w - padding
        y = h - padding
        
        # Draw with slight transparency effect (dark outline + white text)
        cv2.putText(output, text, (x+1, y+1), font, font_scale, (0, 0, 0), thickness + 1)
        cv2.putText(output, text, (x, y), font, font_scale, (255, 255, 255), thickness)
        
        return output
    
    @staticmethod
    def generate_simple(image: np.ndarray, 
                        max_dim: int = 1920, 
                        quality: int = 75) -> bytes:
        """
        Simple static method for quick preview generation.
        
        Args:
            image: Image as numpy array
            max_dim: Maximum dimension for preview
            quality: JPEG quality (0-100)
            
        Returns:
            JPEG bytes
        """
        h, w = image.shape[:2]
        scale = min(max_dim / w, max_dim / h)
        
        if scale < 1.0:
            new_w = int(w * scale)
            new_h = int(h * scale)
            image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        success, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, quality])
        
        if not success:
            raise ValueError("Failed to encode preview")
        
        return buffer.tobytes()


# Singleton instance for easy import
preview_generator = PreviewGenerator()
