from typing import List, Tuple, Dict, Any
import hashlib
from ..schema.blueprint import HelixBlueprint, Anchor

class BlueprintValidator:
    """
    Validates HELIX blueprints against specification rules (Section 5.1).
    Ensures integrity before materialization.
    """
    
    SUPPORTED_VERSIONS = ["2.0", "3.0"]
    
    def validate(self, blueprint: HelixBlueprint) -> Tuple[bool, List[str]]:
        """
        Run all validation checks.
        Returns: (is_valid, list_of_errors)
        """
        errors = []
        
        # 1. Version Check
        if blueprint.version not in self.SUPPORTED_VERSIONS:
            errors.append(f"Unsupported schema version: {blueprint.version}")
            
        # 2. Anchor Integrity
        for idx, anchor in enumerate(blueprint.anchors):
            anchor_errors = self._validate_anchor(anchor, idx)
            errors.extend(anchor_errors)
            
        # 3. Mesh Consistency
        if blueprint.mesh:
            mesh_errors = self._validate_mesh(blueprint)
            errors.extend(mesh_errors)
            
        # 4. Freedom Field Conflicts
        freedom_errors = self._validate_freedom_conflicts(blueprint)
        errors.extend(freedom_errors)
            
        return len(errors) == 0, errors

    def _validate_anchor(self, anchor: Anchor, idx: int) -> List[str]:
        errors = []
        
        # Check ID uniqueness (global check needed, but local check here for format)
        if not anchor.id:
            errors.append(f"Anchor at index {idx} missing ID")
            
        # Verify content hash if data exists
        if anchor.data and anchor.content_hash:
            computed_hash = hashlib.sha256(anchor.data.encode()).hexdigest()
            if computed_hash != anchor.content_hash:
                errors.append(f"Integrity failure: Anchor {anchor.id} content hash mismatch")
                
        # Confidence threshold (redundant check but good for safety)
        if anchor.confidence < 0.85:
            errors.append(f"Anchor {anchor.id} below confidence threshold (0.85)")
            
        return errors

    def _validate_mesh(self, blueprint: HelixBlueprint) -> List[str]:
        errors = []
        mesh = blueprint.mesh
        
        # Check referencing
        anchor_ids = {a.id for a in blueprint.anchors}
        
        if mesh.constraints:
            for aid in mesh.constraints.keys():
                if aid not in anchor_ids:
                    errors.append(f"Mesh constraint references unknown anchor: {aid}")
                    
        return errors

    def _validate_freedom_conflicts(self, blueprint: HelixBlueprint) -> List[str]:
        """
        Check if freedom fields conflict with hard constraints.
        Example: Freedom 'lighting_direction' vs Hard Constraint 'lighting_fixed'
        """
        errors = []
        freedom_keys = set(blueprint.freedom.keys())
        
        # Check against hard constraints
        hard_constraints = set(blueprint.constraints.get("hard", []))
        
        # Define conflict pairs (simple heuristic for now)
        conflict_map = {
            "lighting_direction": "lighting_fixed",
            "background_texture": "background_fixed",
            "color_palette": "color_locked"
        }
        
        for free_key, constraint_key in conflict_map.items():
            if free_key in freedom_keys and constraint_key in hard_constraints:
                errors.append(f"Conflict: Freedom '{free_key}' contradicts hard constraint '{constraint_key}'")
                
        return errors
