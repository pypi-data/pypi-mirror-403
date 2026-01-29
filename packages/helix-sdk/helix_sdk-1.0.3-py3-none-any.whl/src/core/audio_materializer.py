import base64
import os
from ..schema.blueprint import HelixBlueprint

class AudioMaterializer:
    """
    Materializes Audio from HELIX Blueprints.
    
    For Phase 2 (Audio Support), we currently rely on the 'background_spectral' anchor
    which contains the full (or compressed) audio data.
    
    Future versions will support 'Stitching' spectral slices (Voice) onto 
    generative backgrounds (Ambience), similar to the Image V4 pipeline.
    """
    
    def materialize(self, blueprint: HelixBlueprint) -> bytes:
        """
        Reconstruct audio bytes from blueprint.
        """
        if blueprint.metadata.modality != "audio":
            raise ValueError(f"Invalid modality for AudioMaterializer: {blueprint.metadata.modality}")
            
        # 1. Find Background Anchor (The Canvas)
        bg_anchor = next((a for a in blueprint.anchors if a.type == "background_spectral"), None)
        
        if not bg_anchor or not bg_anchor.data:
            # Fallback: Check for any anchor with data if background is missing
            # In a real scenario, we might generate silence if missing.
            raise ValueError("Blueprint missing 'background_spectral' anchor with data.")
            
        # 2. Decode Data
        try:
            audio_data = base64.b64decode(bg_anchor.data)
        except Exception as e:
            raise ValueError(f"Failed to decode audio data: {e}")
            
        # 3. (Future) Overlay Spectral Anchors
        # If we had separate voice anchors, we would mix them here (pydub/ffmpeg).
        # For now, we return the base background layer which is the full audio.
        
        return audio_data
