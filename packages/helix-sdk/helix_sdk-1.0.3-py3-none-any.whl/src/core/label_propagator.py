import json
from typing import List, Dict, Any
from ..schema.blueprint import HelixBlueprint, Anchor

class LabelPropagator:
    """
    Handles Phase 3: Label Inheritance System.
    
    The core philosophy of HELIX is that Anchors are immutable during materialization.
    Therefore, the semantic labels and bounding boxes from the original Blueprint
    remain valid for all generated variants.
    
    This class generates standard computer vision annotation formats (YOLO, COCO)
    for a materialized batch.
    """
    
    def generate_yolo_labels(self, blueprint: HelixBlueprint, image_width: int, image_height: int) -> List[str]:
        """
        Generate YOLO format labels (class_id center_x center_y width height) normalized.
        Assumes anchors with 'semantic_label' are the classes.
        """
        labels = []
        
        # We need a mapping from semantic_label string to integer ID.
        # Ideally this comes from a global LabelMap, but for now we hash or auto-increment.
        # Let's derive it sorted.
        class_names = sorted(list(set(a.semantic_label for a in blueprint.anchors if a.semantic_label)))
        class_map = {name: i for i, name in enumerate(class_names)}
        
        for anchor in blueprint.anchors:
            if not anchor.bbox or not anchor.semantic_label:
                continue
                
            # bbox is (top, right, bottom, left)
            top, right, bottom, left = anchor.bbox
            
            # YOLO expects center_x, center_y, width, height (normalized 0-1)
            # Ensure we clip to image dims just in case
            
            box_w = (right - left)
            box_h = (bottom - top)
            center_x = left + (box_w / 2)
            center_y = top + (box_h / 2)
            
            norm_cx = center_x / image_width
            norm_cy = center_y / image_height
            norm_w = box_w / image_width
            norm_h = box_h / image_height
            
            class_id = class_map[anchor.semantic_label]
            
            labels.append(f"{class_id} {norm_cx:.6f} {norm_cy:.6f} {norm_w:.6f} {norm_h:.6f}")
            
        return labels

    def generate_coco_annotation(self, blueprint: HelixBlueprint, image_id: int) -> Dict[str, Any]:
        """
        Generate COCO-style annotation dictionary for this blueprint/image.
        """
        annotations = []
        
        for i, anchor in enumerate(blueprint.anchors):
            if not anchor.bbox or not anchor.semantic_label:
                continue
                
            top, right, bottom, left = anchor.bbox
            width = right - left
            height = bottom - top
            
            ann = {
                "id": i + (image_id * 1000), # pseudo unique ID
                "image_id": image_id,
                "category_id": hash(anchor.semantic_label) % 1000, # Simplified
                "bbox": [left, top, width, height], # COCO is [x, y, w, h]
                "area": width * height,
                "iscrowd": 0,
                "segmentation": [] # We don't have segmentation masks yet, just bboxes
            }
            annotations.append(ann)
            
        return annotations
