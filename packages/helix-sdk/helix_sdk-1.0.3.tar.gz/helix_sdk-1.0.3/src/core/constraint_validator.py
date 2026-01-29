from ..schema.blueprint import Mesh
from typing import List, Tuple

class ConstraintValidator:
    def __init__(self):
        pass

    def validate(self, mesh: Mesh) -> Tuple[bool, List[str]]:
        """
        Validates if the mesh is sufficiently constrained.
        Returns: (is_valid, list_of_errors)
        """
        errors = []
        if mesh.centroid is None:
            # Empty mesh is allowed ONLY if there were no anchors? 
            # But if we have no anchors, Helix might fail reconstruction.
            # For now, let's just warn or allow empty if intent is empty.
            # But technically a mesh without centroid is invalid if it has constraints.
            if len(mesh.constraints) > 0:
                errors.append("Mesh has constraints but no global centroid.")
            
        # Check for under-constrained anchors
        # Rule: Every anchor must have 'dist_to_c', 'angle_c', 'aspect_ratio'
        required_keys = ["dist_to_c", "angle_c", "aspect_ratio"]
        
        for anchor_id, constraints in mesh.constraints.items():
            for key in required_keys:
                if key not in constraints:
                    errors.append(f"Anchor {anchor_id} missing constraint: {key}")
            
            # Check numerical validity
            if constraints.get("aspect_ratio", 1) <= 0:
                errors.append(f"Anchor {anchor_id} has invalid aspect ratio <= 0")

        # System-wide constraint: Need at least 1 anchor for ANY meaningful reconstruction?
        # Manual says "Anchors... act as truth beacons". If no anchors, it's just a hallucination.
        # So we might enforce at least 1 anchor.
        if len(mesh.constraints) == 0:
             # We allow it for now, but strictly speaking it's risky.
             pass

        return len(errors) == 0, errors
