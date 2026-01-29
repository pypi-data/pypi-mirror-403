"""
HELIX Image Enhancement Layers
==============================

Deterministic post-processing that enhances materialized images
WITHOUT AI generation or hallucination risk.

These layers use only:
- Mathematical algorithms (sharpening, contrast)
- Stored anchor data (for detail injection)
- Color palette from blueprint (for color correction)

No external API calls, no randomness, same input = same output.
"""

import cv2
import numpy as np
from typing import Tuple, List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class EnhancementConfig:
    """Configuration for enhancement layers."""
    # Sharpening
    sharpen_enabled: bool = True
    sharpen_strength: float = 1.2  # 0.0 = none, 2.0 = strong
    
    # Contrast
    contrast_enabled: bool = True
    clahe_clip_limit: float = 2.0
    clahe_grid_size: Tuple[int, int] = (8, 8)
    
    # Noise reduction
    denoise_enabled: bool = True
    denoise_strength: int = 5
    
    # Color correction
    color_correction_enabled: bool = True
    
    # Detail injection from anchors
    detail_injection_enabled: bool = True
    detail_blend_strength: float = 0.7
    
    # Resolution enhancement
    upscale_method: str = "lanczos"  # lanczos, cubic, linear


class EnhancementLayers:
    """
    Deterministic image enhancement pipeline.
    
    Improves materialized images using only mathematical operations
    and stored blueprint data - no AI generation.
    """
    
    def __init__(self, config: EnhancementConfig = None):
        self.config = config or EnhancementConfig()
    
    def enhance(
        self,
        image: np.ndarray,
        blueprint: Any = None,
        target_resolution: Tuple[int, int] = None
    ) -> np.ndarray:
        """
        Apply all enhancement layers to an image.
        
        Args:
            image: Input image as numpy array (H, W, C) in BGR format
            blueprint: Optional HelixBlueprint for anchor-based enhancement
            target_resolution: Optional target size (width, height)
            
        Returns:
            Enhanced image as numpy array
        """
        result = image.copy()
        
        # 1. Upscale if target resolution specified
        if target_resolution:
            result = self._upscale(result, target_resolution)
        
        # 2. Denoise (before sharpening)
        if self.config.denoise_enabled:
            result = self._denoise(result)
        
        # 3. Color correction using blueprint palette
        if self.config.color_correction_enabled and blueprint:
            result = self._color_correct(result, blueprint)
        
        # 4. Local contrast enhancement (CLAHE)
        if self.config.contrast_enabled:
            result = self._enhance_contrast(result)
        
        # 5. Edge-aware sharpening
        if self.config.sharpen_enabled:
            result = self._sharpen(result)
        
        # 6. Detail injection from anchor crops
        if self.config.detail_injection_enabled and blueprint:
            result = self._inject_anchor_details(result, blueprint)
        
        return result
    
    def _upscale(self, image: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
        """
        Upscale image to target resolution.
        
        Uses Lanczos interpolation for best quality.
        """
        current_h, current_w = image.shape[:2]
        target_w, target_h = target_size
        
        if current_w >= target_w and current_h >= target_h:
            return image  # Already at or above target size
        
        interpolation = {
            "lanczos": cv2.INTER_LANCZOS4,
            "cubic": cv2.INTER_CUBIC,
            "linear": cv2.INTER_LINEAR,
        }.get(self.config.upscale_method, cv2.INTER_LANCZOS4)
        
        return cv2.resize(image, (target_w, target_h), interpolation=interpolation)
    
    def _denoise(self, image: np.ndarray) -> np.ndarray:
        """
        Remove noise while preserving edges.
        
        Uses bilateral filter for edge-preserving smoothing.
        """
        strength = self.config.denoise_strength
        return cv2.bilateralFilter(image, d=9, sigmaColor=strength*10, sigmaSpace=strength*10)
    
    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance local contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization).
        
        Works on luminance channel only to preserve colors.
        """
        # Convert to LAB color space
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        
        # Apply CLAHE to L channel
        clahe = cv2.createCLAHE(
            clipLimit=self.config.clahe_clip_limit,
            tileGridSize=self.config.clahe_grid_size
        )
        l_enhanced = clahe.apply(l_channel)
        
        # Merge and convert back
        lab_enhanced = cv2.merge([l_enhanced, a_channel, b_channel])
        return cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
    
    def _sharpen(self, image: np.ndarray) -> np.ndarray:
        """
        Edge-aware sharpening using unsharp mask.
        
        Sharpens edges without amplifying noise.
        """
        strength = self.config.sharpen_strength
        
        if strength <= 0:
            return image
        
        # Create Gaussian blur
        blurred = cv2.GaussianBlur(image, (0, 0), 3)
        
        # Unsharp mask: original + strength * (original - blurred)
        sharpened = cv2.addWeighted(image, 1.0 + strength, blurred, -strength, 0)
        
        return np.clip(sharpened, 0, 255).astype(np.uint8)
    
    def _color_correct(self, image: np.ndarray, blueprint: Any) -> np.ndarray:
        """
        Correct colors using the stored color palette from blueprint.
        
        Ensures output colors match the original image's palette.
        """
        # Get color palette from blueprint
        palette = getattr(blueprint.metadata, 'color_palette', None) if hasattr(blueprint, 'metadata') else None
        
        if not palette or len(palette) == 0:
            return image
        
        try:
            # Parse palette colors (hex strings like "#FF5733")
            palette_colors = []
            for color in palette[:5]:  # Use top 5 dominant colors
                if isinstance(color, str) and color.startswith('#'):
                    r = int(color[1:3], 16)
                    g = int(color[3:5], 16)
                    b = int(color[5:7], 16)
                    palette_colors.append((b, g, r))  # BGR
            
            if not palette_colors:
                return image
            
            # Calculate average palette color
            avg_palette = np.mean(palette_colors, axis=0)
            
            # Calculate average image color
            avg_image = np.mean(image, axis=(0, 1))
            
            # Calculate color shift
            shift = avg_palette - avg_image
            
            # Apply subtle color correction (50% strength to avoid over-correction)
            corrected = image.astype(np.float32) + shift * 0.5
            
            return np.clip(corrected, 0, 255).astype(np.uint8)
            
        except Exception:
            return image  # Return original on any error
    
    def _inject_anchor_details(self, image: np.ndarray, blueprint: Any) -> np.ndarray:
        """
        Inject high-resolution details from stored anchor crops.
        
        Uses anchor pixel data to ensure critical regions maintain
        original quality (faces, text, logos).
        """
        anchors = getattr(blueprint, 'anchors', []) if blueprint else []
        
        if not anchors:
            return image
        
        result = image.copy()
        h, w = image.shape[:2]
        
        for anchor in anchors:
            # Get anchor data and bounding box
            data = getattr(anchor, 'data', None)
            bbox = getattr(anchor, 'bbox', None)
            
            if not data or not bbox:
                continue
            
            try:
                # Decode anchor image from base64
                import base64
                import io
                from PIL import Image as PILImage
                
                anchor_bytes = base64.b64decode(data)
                anchor_img = PILImage.open(io.BytesIO(anchor_bytes))
                anchor_arr = np.array(anchor_img)
                
                # Convert RGB to BGR if needed
                if len(anchor_arr.shape) == 3 and anchor_arr.shape[2] == 3:
                    anchor_arr = cv2.cvtColor(anchor_arr, cv2.COLOR_RGB2BGR)
                
                # Get bounding box (top, right, bottom, left)
                top, right, bottom, left = bbox
                
                # Scale bbox to current image size
                # (anchors were captured at original resolution)
                orig_dims = getattr(blueprint.metadata, 'original_dims', (h, w)) if hasattr(blueprint, 'metadata') else (h, w)
                orig_h, orig_w = orig_dims
                
                scale_x = w / orig_w
                scale_y = h / orig_h
                
                left_scaled = int(left * scale_x)
                right_scaled = int(right * scale_x)
                top_scaled = int(top * scale_y)
                bottom_scaled = int(bottom * scale_y)
                
                # Resize anchor to fit new bbox
                target_w = right_scaled - left_scaled
                target_h = bottom_scaled - top_scaled
                
                if target_w > 0 and target_h > 0:
                    anchor_resized = cv2.resize(anchor_arr, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)
                    
                    # Blend with existing content (strength from config)
                    strength = self.config.detail_blend_strength
                    
                    # Get existing region
                    existing = result[top_scaled:bottom_scaled, left_scaled:right_scaled]
                    
                    if existing.shape == anchor_resized.shape:
                        # Blend: result = strength * anchor + (1-strength) * existing
                        blended = cv2.addWeighted(anchor_resized, strength, existing, 1 - strength, 0)
                        result[top_scaled:bottom_scaled, left_scaled:right_scaled] = blended
                        
            except Exception as e:
                # Skip this anchor on any error
                continue
        
        return result


# Resolution presets
RESOLUTION_PRESETS = {
    "256p": (256, 256),
    "512p": (512, 512),
    "720p": (1280, 720),
    "1080p": (1920, 1080),
    "1440p": (2560, 1440),
    "4K": (3840, 2160),
    "8K": (7680, 4320),
}


def enhance_image(
    image: np.ndarray,
    blueprint: Any = None,
    target_resolution: str = None,
    config: EnhancementConfig = None
) -> np.ndarray:
    """
    Convenience function to enhance an image.
    
    Args:
        image: Input image (BGR numpy array)
        blueprint: Optional HelixBlueprint for anchor-based enhancement
        target_resolution: Target resolution string (e.g., "4K", "1080p")
        config: Optional enhancement configuration
        
    Returns:
        Enhanced image
    """
    layers = EnhancementLayers(config)
    
    target_size = None
    if target_resolution:
        target_size = RESOLUTION_PRESETS.get(target_resolution)
    
    return layers.enhance(image, blueprint, target_size)
