import math
from typing import List, Tuple
from ..schema.blueprint import Anchor, Mesh

class MeshBuilder:
    def __init__(self):
        pass

    def build_mesh(self, anchors: List[Anchor], image_dims: Tuple[int, int]) -> Mesh:
        """
        Builds a structural mesh from the given anchors.
        Calculates a global centroid and relative vectors for each anchor.
        
        Args:
            anchors: List of detected anchors.
            image_dims: (height, width) of the original image.
        """
        if not anchors:
            return Mesh()

        h, w = image_dims
        # Function to get center of an anchor
        def get_center(bbox):
            # bbox is (top, right, bottom, left)
            top, right, bottom, left = bbox
            cy = (top + bottom) / 2.0
            cx = (left + right) / 2.0
            return cx, cy

        # 1. Calculate Global Centroid
        total_cx, total_cy = 0.0, 0.0
        centers = []
        for anchor in anchors:
            cx, cy = get_center(anchor.bbox)
            centers.append((cx, cy))
            total_cx += cx
            total_cy += cy
        
        n = len(anchors)
        global_cx = total_cx / n
        global_cy = total_cy / n

        # Normalize centroid (0-1 range)
        norm_centroid = (global_cx / w, global_cy / h)

        # 2. Calculate Constraints for each anchor
        # We use a normalized coordinate system for robustness
        # Max distance for normalization (diagonal)
        diag = math.sqrt(w*w + h*h)

        constraints = {}

        for anchor, (cx, cy) in zip(anchors, centers):
            # Distance to centroid
            dx = cx - global_cx
            dy = cy - global_cy
            dist = math.sqrt(dx*dx + dy*dy)
            norm_dist = dist / diag
            
            # Angle (radians)
            angle = math.atan2(dy, dx)

            # Aspect Ratio of the anchor itself
            top, right, bottom, left = anchor.bbox
            anchor_w = right - left
            anchor_h = bottom - top
            aspect_ratio = anchor_w / anchor_h if anchor_h > 0 else 0

            constraints[anchor.id] = {
                "dist_to_c": norm_dist,
                "angle_c": angle,
                "aspect_ratio": aspect_ratio
            }

        return Mesh(
            centroid=norm_centroid,
            constraints=constraints
        )
