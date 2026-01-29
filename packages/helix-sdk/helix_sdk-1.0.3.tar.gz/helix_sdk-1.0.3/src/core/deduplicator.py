from typing import List, Tuple
from ..schema.blueprint import HelixBlueprint, Anchor

class SemanticDeduplicator:
    """
    Handles Phase 3: Dataset Deduplication.
    
    Identifies if two blueprints represent the "same" scene/identity, even if 
    pixel data differs slightly (e.g., compression artifacts, minor noise).
    
    Logic:
    - Compares Identity Anchors (Faces, Logos).
    - If Identity Anchors match (hashes identical or highly similar), treat as duplicate.
    - Allows collapsing 1000 frames of a video or burst shot into 1 Master Blueprint + 999 Variants.
    """
    
    def __init__(self, threshold: float = 0.9):
        self.threshold = threshold

    def compute_similarity(self, bp1: HelixBlueprint, bp2: HelixBlueprint) -> float:
        """
        Compute semantic similarity (0.0 - 1.0) between two blueprints.
        """
        # 1. Compare Modality
        if bp1.metadata.modality != bp2.metadata.modality:
            return 0.0
            
        # 2. Compare Anchors
        # We assume Anchors are the ground truth of identity.
        anchors1 = {a.content_hash for a in bp1.anchors if a.type != 'background'}
        anchors2 = {a.content_hash for a in bp2.anchors if a.type != 'background'}
        
        if not anchors1 or not anchors2:
            # Fallback to metadata aura if no distinct anchors (unlikely for valid blueprints)
            return 1.0 if bp1.metadata.aura == bp2.metadata.aura else 0.0
            
        intersection = anchors1.intersection(anchors2)
        union = anchors1.union(anchors2)
        
        iou = len(intersection) / len(union)
        return iou

    def is_duplicate(self, bp1: HelixBlueprint, bp2: HelixBlueprint) -> bool:
        """Returns True if blueprints are semantically identical."""
        sim = self.compute_similarity(bp1, bp2)
        return sim >= self.threshold
