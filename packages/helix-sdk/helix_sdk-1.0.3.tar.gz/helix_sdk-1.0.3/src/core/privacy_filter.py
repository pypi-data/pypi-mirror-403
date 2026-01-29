import copy
from ..schema.blueprint import HelixBlueprint, Anchor

class PrivacyFilter:
    """
    Handles Phase 3: Privacy Layer.
    
    Anonymizes Blueprints by stripping sensitive pixel data from Identity Anchors
    while preserving their geometry (bbox) and semantic role.
    
    Result: 
    The Materializer will "hallucinate" a generic/synthetic replacement 
    for the missing data that fits the scene context and mesh, 
    effectively performing a "Deepfake Swap" to a non-existent person.
    """
    
    SENSITIVE_TYPES = {'face', 'license_plate', 'text', 'signature', 'iris'}
    
    def anonymize(self, blueprint: HelixBlueprint) -> HelixBlueprint:
        """
        Returns a new Blueprint with sensitive anchors scrubbed.
        """
        # Deep copy to protect original
        safe_bp = copy.deepcopy(blueprint)
        
        privacy_edits = 0
        
        for anchor in safe_bp.anchors:
            if anchor.type in self.SENSITIVE_TYPES:
                # STRIP PIXEL DATA
                # This forces the AI to generate a synthetic filler based on 
                # context + bbox, rather than reconstructing the real person.
                anchor.data = None 
                anchor.content_hash = "ANONYMIZED"
                
                # Optional: Update label to indicate synthesis required
                anchor.semantic_label = f"synthetic_{anchor.type}"
                
                privacy_edits += 1
                
        if privacy_edits > 0:
            safe_bp.metadata.aura += " [PRIVACY SAFE MODE]"
            safe_bp.metadata.scene_description += ". (Use generic/synthetic identities for all people)"
            
        return safe_bp
