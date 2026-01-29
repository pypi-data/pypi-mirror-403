"""
HELIX Resolution Engine
========================
Handles intelligent resolution scaling for the "Living Data" feature.
Enables photos to be materialized at any resolution - from 1080p to 8K.

Key concept: Store small, render BIG.
"""

from typing import Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ResolutionTier:
    """Configuration for a resolution tier"""
    name: str
    width: int
    height: int
    prompt_detail: str
    temperature: float = 0.5  # Higher = more creative hallucination


class ResolutionEngine:
    """
    Handles intelligent resolution scaling for Living Data feature.
    
    Usage:
        engine = ResolutionEngine()
        tier = engine.get_tier("4K")
        prompt = engine.build_enhancement_prompt(blueprint, "4K")
    """
    
    # Resolution tiers from consumer to professional
    TIERS: Dict[str, ResolutionTier] = {
        "720p": ResolutionTier(
            name="720p HD",
            width=1280,
            height=720,
            prompt_detail="HD quality, clean and sharp",
            temperature=0.3
        ),
        "1080p": ResolutionTier(
            name="1080p Full HD",
            width=1920,
            height=1080,
            prompt_detail="Full HD quality, crisp details, balanced",
            temperature=0.4
        ),
        "1440p": ResolutionTier(
            name="1440p 2K",
            width=2560,
            height=1440,
            prompt_detail="2K clarity, fine textures visible",
            temperature=0.45
        ),
        "4K": ResolutionTier(
            name="4K Ultra HD",
            width=3840,
            height=2160,
            prompt_detail="ultra sharp 4K professional photography, pore-level skin detail, individual hair strands",
            temperature=0.5
        ),
        "8K": ResolutionTier(
            name="8K Cinema",
            width=7680,
            height=4320,
            prompt_detail="8K cinematic masterpiece, hyper-detailed textures, museum-quality print resolution",
            temperature=0.6
        )
    }
    
    # Default tier for materialization
    DEFAULT_TIER = "4K"
    
    def get_tier(self, resolution: str) -> ResolutionTier:
        """Get resolution tier by name, defaults to 4K if not found"""
        return self.TIERS.get(resolution, self.TIERS[self.DEFAULT_TIER])
    
    def get_available_resolutions(self) -> list:
        """Get list of available resolution names"""
        return list(self.TIERS.keys())
    
    def calculate_upgrade_factor(self, 
                                  original_size: Tuple[int, int], 
                                  target: str) -> dict:
        """
        Calculate how much we're improving the image.
        
        Args:
            original_size: (width, height) of original image
            target: Target resolution tier name
            
        Returns:
            Dict with upgrade metrics
        """
        tier = self.get_tier(target)
        orig_w, orig_h = original_size
        
        # Calculate pixel counts
        original_pixels = orig_w * orig_h
        target_pixels = tier.width * tier.height
        
        # Calculate scale factor
        scale = (target_pixels / original_pixels) ** 0.5 if original_pixels > 0 else 1.0
        
        # Determine original resolution tier name
        original_tier = self._detect_resolution_tier(original_size)
        
        return {
            "scale_factor": round(scale, 2),
            "original_resolution": original_tier,
            "target_resolution": tier.name,
            "original_pixels": original_pixels,
            "target_pixels": target_pixels,
            "pixel_increase": f"{(target_pixels / max(original_pixels, 1)):.1f}x",
            "improvement_description": self._describe_improvement(original_tier, tier.name)
        }
    
    def _detect_resolution_tier(self, size: Tuple[int, int]) -> str:
        """Detect approximate resolution tier of an image"""
        w, h = size
        pixels = w * h
        
        if pixels < 500_000:
            return "SD (Low)"
        elif pixels < 1_000_000:
            return "720p"
        elif pixels < 2_500_000:
            return "1080p"
        elif pixels < 5_000_000:
            return "1440p"
        elif pixels < 12_000_000:
            return "4K"
        else:
            return "8K+"
    
    def _describe_improvement(self, original: str, target: str) -> str:
        """Generate human-readable improvement description"""
        improvements = {
            ("SD (Low)", "4K"): "🚀 Massive upgrade! Your grainy old photo becomes crystal-clear 4K.",
            ("SD (Low)", "8K"): "🚀🚀 EXTREME upgrade! From potato quality to cinema-grade 8K!",
            ("720p", "4K"): "📈 Great upgrade! HD to Ultra HD - 4x more detail.",
            ("720p", "8K"): "📈📈 Huge upgrade! HD to 8K cinema quality.",
            ("1080p", "4K"): "✨ Quality boost! Full HD to 4K - noticeably sharper.",
            ("1080p", "8K"): "✨✨ Major boost! Full HD to 8K print quality.",
            ("1440p", "4K"): "🔍 Fine refinement. 2K to 4K - subtle but noticeable.",
            ("4K", "8K"): "🔬 Professional upgrade. 4K to 8K for large prints.",
        }
        
        key = (original, target)
        return improvements.get(key, f"Upgrading from {original} to {target}")
    
    def build_enhancement_prompt(self, 
                                  aura: str,
                                  scene_description: str,
                                  target: str,
                                  original_size: Tuple[int, int] = None) -> str:
        """
        Build the mega-prompt for quality enhancement.
        
        Args:
            aura: Mood/atmosphere description from blueprint
            scene_description: Scene context from blueprint
            target: Target resolution tier name
            original_size: Original image dimensions (for context)
            
        Returns:
            Detailed prompt for Gemini materialization
        """
        tier = self.get_tier(target)
        
        # Calculate upgrade context if original size provided
        upgrade_context = ""
        if original_size:
            metrics = self.calculate_upgrade_factor(original_size, target)
            upgrade_context = f"""
        UPGRADE CONTEXT:
        - Original: {metrics['original_resolution']} ({original_size[0]}x{original_size[1]})
        - Target: {tier.name} ({tier.width}x{tier.height})
        - Scale: {metrics['scale_factor']}x
        - This is a {metrics['pixel_increase']} pixel increase!
        """
        
        prompt = f"""
        ═══════════════════════════════════════════════════════════════
        🧬 HELIX LIVING DATA RESTORATION ENGINE - {tier.name}
        ═══════════════════════════════════════════════════════════════
        
        MISSION: Transform a low-resolution input into a {tier.prompt_detail}.
        {upgrade_context}
        
        ═══════════════════════════════════════════════════════════════
        🎯 CRITICAL RESTORATION RULES
        ═══════════════════════════════════════════════════════════════
        
        1. ❌ PIXEL PRESERVATION IS FORBIDDEN
           - The input pixels are BLURRY GARBAGE from compression
           - Do NOT copy them. RE-IMAGINE them.
           
        2. 👤 FACE RESTORATION (HIGHEST PRIORITY)
           - Input faces are blurry approximations
           - Reconstruct: pore-level skin texture, individual eyelashes
           - Sharp iris detail, natural skin tones
           - Preserve IDENTITY but enhance QUALITY
           
        3. 🌳 TEXTURE HALLUCINATION
           - Green smudge → Detailed leaves with veins
           - Gray patch → Textured concrete or fabric
           - Blurry background → Sharp, contextually appropriate detail
           
        4. 🌊 ARTIFACT REMOVAL
           - Remove ALL JPEG blocking artifacts
           - Smooth noise while preserving real detail
           - No halos around edges
        
        ═══════════════════════════════════════════════════════════════
        🎨 SCENE CONTEXT
        ═══════════════════════════════════════════════════════════════
        
        AURA/MOOD: {aura or 'Natural, balanced lighting'}
        SCENE: {scene_description or 'General scene reconstruction'}
        
        Maintain this exact mood while upgrading quality.
        
        ═══════════════════════════════════════════════════════════════
        📐 OUTPUT REQUIREMENTS
        ═══════════════════════════════════════════════════════════════
        
        Resolution: {tier.width}x{tier.height} ({tier.name})
        Quality: {tier.prompt_detail}
        
        OUTPUT: A crystal clear, professional-grade photograph that looks
        like it was shot yesterday on the best camera available.
        
        ═══════════════════════════════════════════════════════════════
        """
        
        return prompt
    
    def get_target_dimensions(self, 
                               original_size: Tuple[int, int], 
                               target: str,
                               maintain_aspect: bool = True) -> Tuple[int, int]:
        """
        Calculate target output dimensions.
        
        Args:
            original_size: Original (width, height)
            target: Target resolution tier
            maintain_aspect: If True, maintain original aspect ratio
            
        Returns:
            Target (width, height)
        """
        tier = self.get_tier(target)
        
        if not maintain_aspect:
            return (tier.width, tier.height)
        
        orig_w, orig_h = original_size
        orig_aspect = orig_w / orig_h if orig_h > 0 else 1.0
        
        # Fit within target tier dimensions while maintaining aspect
        target_aspect = tier.width / tier.height
        
        if orig_aspect > target_aspect:
            # Original is wider - fit to width
            out_w = tier.width
            out_h = int(tier.width / orig_aspect)
        else:
            # Original is taller - fit to height
            out_h = tier.height
            out_w = int(tier.height * orig_aspect)
        
        return (out_w, out_h)


# Singleton instance for easy import
resolution_engine = ResolutionEngine()
