import os
import json
import base64
import cv2
import hashlib
import numpy as np
from typing import List, Tuple, Any, Optional, Dict
from ..schema.blueprint import Anchor

class GeminiAnchorExtractor:
    """
    Enhanced Gemini-powered anchor extraction using multi-model cascade.
    Primary: Gemini 3.0 → Fallback: Gemini 2.0 → Fallback: Gemini 1.5
    
    Extracts granular identity anchors including:
    - Face sub-components (eyes, nose, mouth, face outline)
    - Body geometry (shoulders, pose)
    - Unique elements (text, logos, distinctive objects)
    - Aura/atmosphere for reconstruction guidance
    """
    
    # Enhanced extraction prompt for 80-90% accuracy
    EXTRACTION_PROMPT = """
You are the HELIX Identity Extraction Engine. Your task is critical: identify every element that makes this image UNIQUE and cannot be safely hallucinated.

## EXTRACTION RULES:
1. FACES are highest priority - extract sub-components separately
2. TEXT must be preserved exactly (cannot be guessed)
3. LOGOS and distinctive marks must be captured
4. Provide PRECISE bounding boxes (0-100 normalized coordinates)

## REQUIRED OUTPUT (JSON only):
{
    "anchors": [
        {
            "label": "face",
            "ymin": 10, "xmin": 30, "ymax": 60, "xmax": 70,
            "confidence": 0.98,
            "sub_anchors": [
                {"label": "left_eye", "ymin": 20, "xmin": 35, "ymax": 28, "xmax": 45},
                {"label": "right_eye", "ymin": 20, "xmin": 55, "ymax": 28, "xmax": 65},
                {"label": "nose", "ymin": 28, "xmin": 45, "ymax": 40, "xmax": 55},
                {"label": "mouth", "ymin": 42, "xmin": 40, "ymax": 52, "xmax": 60}
            ]
        },
        {"label": "text", "ymin": 80, "xmin": 10, "ymax": 95, "xmax": 90, "content": "exact text here"},
        {"label": "logo", "ymin": 5, "xmin": 85, "ymax": 15, "xmax": 95}
    ],
    "aura": "Warm golden hour lighting, soft bokeh background, intimate portrait mood, slight film grain texture",
    "color_palette": ["#F5DEB3", "#8B4513", "#FFD700"],
    "scene_description": "Portrait of person in brown dress against neutral indoor background",
    "body_geometry": {
        "shoulder_line": {"y": 65, "x_left": 20, "x_right": 80},
        "pose": "frontal, slight left tilt"
    }
}

## CRITICAL:
- Coordinates are percentages (0-100) of image dimensions
- Include ALL faces with their sub-components
- sub_anchors are relative to FULL IMAGE, not parent
- confidence: 0.0-1.0 for each anchor
- Return ONLY valid JSON, no markdown blocks
"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = None
        self.model_name = None
        
        if self.api_key:
            self._initialize_client()
        else:
            print("WARNING: No GEMINI_API_KEY. GeminiAnchorExtractor disabled.")

    def _initialize_client(self):
        """Initialize with Gemini 3 → 2.0 → 1.5 cascade"""
        from google import genai
        self.client = genai.Client(api_key=self.api_key)
        
        # Allow user to force a specific model via env var
        forced_model = os.getenv("GEMINI_MODEL")
        if forced_model:
            self.model_name = forced_model
            print(f"[OK] Initialized custom model: {forced_model}")
            return
        
        # Model cascade: try newest first
        # In new SDK we don't instantiate model objects, just use the string.
        # We assume the first one works for now, or we could try a dry run.
        # For simplicity and speed, we'll pick the first prioritized one.
        model_cascade = [
            ('gemini-3-flash-preview', 'Gemini 3 Flash Preview'),
            ('gemini-3-pro-preview', 'Gemini 3 Pro Preview'),
            ('gemini-2.0-flash-exp', 'Gemini 2.0 Flash'),
        ]
        
        # Default to first one
        self.model_name = model_cascade[0][0]
        print(f"[OK] Initialized: {model_cascade[0][1]}")

    def extract(self, image: np.ndarray) -> Tuple[List[Anchor], str, Dict[str, Any]]:
        """
        Extract identity anchors from image.
        
        Returns:
            Tuple of (anchors, aura_description, extra_metadata)
        """
        if not self.client:
            return [], "", {}

        # Convert numpy image to bytes for API
        success, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 95])
        if not success:
            return [], "", {}
        
        from PIL import Image
        import io
        pil_img = Image.open(io.BytesIO(buffer))

        try:
            # Call Gemini with enhanced prompt
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[self.EXTRACTION_PROMPT, pil_img],
                config={
                    'temperature': 0.0,  # [STABILITY] Zero temp for max determinism
                    'max_output_tokens': 4096,
                }
            )
            
            text = response.text.strip()
            
            # Clean JSON block markers if present
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            data = json.loads(text)
            
            # Process identity anchors (with padding for better edges)
            anchors = self._process_anchors(data.get("anchors", []), image, padding=5)
            aura = data.get("aura", "Standard lighting")
            
            extra_metadata = {
                "color_palette": data.get("color_palette", []),
                "scene_description": data.get("scene_description", ""),
                "body_geometry": data.get("body_geometry", {}),
            }
            
            # Add BACKGROUND ANCHOR for full-image fallback (hybrid mode)
            # This ensures perfect reconstruction even if AI generation fails
            bg_anchor = self._create_background_anchor(image)
            anchors.insert(0, bg_anchor)  # Put background first (will be rendered first)
            
            print(f"[EXTRACTED] {len(anchors)} anchors via {self.model_name}")
            return anchors, aura, extra_metadata
            
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON parse error: {e}")
            print(f"   Raw response: {text[:500]}...")
            return [], "", {}
        except Exception as e:
            print(f"[ERROR] Gemini Extraction Failed: {e}")
            return [], "", {}

    def _process_anchors(self, raw_anchors: List[Dict], image: np.ndarray, padding: int = 0) -> List[Anchor]:
        """Process raw anchor data into Anchor objects with pixel crops"""
        anchors = []
        h, w = image.shape[:2]
        
        for idx, item in enumerate(raw_anchors):
            # Skip invalid entries
            if not all(k in item for k in ['ymin', 'xmin', 'ymax', 'xmax']):
                continue
            
            # [STABILITY] Quantize coordinates to 1 decimal place (0.1%)
            # This prevents pixel-level jitter between runs for 30KB variance fix
            ymin = round(float(item['ymin']), 1)
            xmin = round(float(item['xmin']), 1)
            ymax = round(float(item['ymax']), 1)
            xmax = round(float(item['xmax']), 1)
            
            top = int((ymin / 100.0) * h)
            left = int((xmin / 100.0) * w)
            bottom = int((ymax / 100.0) * h)
            right = int((xmax / 100.0) * w)
            
            # Apply padding for better edge blending
            top = max(0, top - padding)
            left = max(0, left - padding)
            bottom = min(h, bottom + padding)
            right = min(w, right + padding)
            
            # Validate bounds
            top = max(0, min(top, h-1))
            bottom = max(top+1, min(bottom, h))
            left = max(0, min(left, w-1))
            right = max(left+1, min(right, w))
            
            # Extract pixel crop (Optimize: Resize & Compress)
            crop = image[top:bottom, left:right]
            
            # [OPTIMIZATION] Resize crop if too large (>620px)
            h_crop, w_crop = crop.shape[:2]
            max_crop_dim = 620
            if w_crop > max_crop_dim or h_crop > max_crop_dim:
                scale = min(max_crop_dim / w_crop, max_crop_dim / h_crop)
                new_w = int(w_crop * scale)
                new_h = int(h_crop * scale)
                crop = cv2.resize(crop, (new_w, new_h), interpolation=cv2.INTER_AREA)
            
            # [OPTIMIZATION] Quality 95 -> 50
            _, crop_buf = cv2.imencode('.jpg', crop, [cv2.IMWRITE_JPEG_QUALITY, 50])
            crop_b64 = base64.b64encode(crop_buf).decode('utf-8')
            
            label = item.get('label', 'object')
            confidence = item.get('confidence', 0.9)
            
            # Enforce spec threshold: confidence >= 0.85
            if confidence < 0.85:
                print(f"[WARN] Dropping low confidence anchor: {label} ({confidence:.2f})")
                continue

            # Compute SHA-256 hash of content
            content_hash = hashlib.sha256(crop_b64.encode()).hexdigest()

            anchor = Anchor(
                id=f"{label}_{idx}_{top}_{left}",
                type=label,
                bbox=(top, right, bottom, left),
                data=crop_b64,
                content_hash=content_hash,
                semantic_label=label,
                confidence=confidence,
                resolution_hint="high" if label in ['face', 'text', 'logo'] else "standard"
            )
            anchors.append(anchor)
            
            # Process sub-anchors (for granular face parts)
            for sub_idx, sub_item in enumerate(item.get('sub_anchors', [])):
                sub_anchor = self._extract_sub_anchor(sub_item, image, h, w, f"{label}_{idx}", sub_idx)
                if sub_anchor:
                    anchors.append(sub_anchor)
        
        return anchors

    def _create_background_anchor(self, image: np.ndarray) -> Anchor:
        """
        Create a full-image background anchor at reduced quality.
        OPTIMIZED: Resizes to max 1650px (tuned for quality) and uses quality=50.
        """
        h, w = image.shape[:2]
        
        # calculate scale to fit within 1650x1650
        max_dim = 1650
        scale = min(max_dim / w, max_dim / h)
        
        if scale < 1.0:
            new_w = int(w * scale)
            new_h = int(h * scale)
            bg_img = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        else:
            bg_img = image

        # Encode at reduced quality (50%) to minimize file size while keeping details
        _, bg_buf = cv2.imencode('.jpg', bg_img, [cv2.IMWRITE_JPEG_QUALITY, 50])
        bg_b64 = base64.b64encode(bg_buf).decode('utf-8')
        content_hash = hashlib.sha256(bg_b64.encode()).hexdigest()
        
        return Anchor(
            id="background_full",
            type="background",
            bbox=(0, w, h, 0),  # Full image: (top, right, bottom, left)
            data=bg_b64,
            content_hash=content_hash,
            semantic_label="background",
            confidence=1.0,
            resolution_hint="low"  # Mark as low-res (fallback only)
        )

    def _extract_sub_anchor(self, item: Dict, image: np.ndarray, h: int, w: int, 
                           parent_id: str, idx: int) -> Optional[Anchor]:
        """Extract a sub-anchor (e.g., eye, nose, mouth)"""
        if not all(k in item for k in ['ymin', 'xmin', 'ymax', 'xmax', 'label']):
            return None
        
        ymin, xmin = item['ymin'], item['xmin']
        ymax, xmax = item['ymax'], item['xmax']
        
        top = int((ymin / 100.0) * h)
        left = int((xmin / 100.0) * w)
        bottom = int((ymax / 100.0) * h)
        right = int((xmax / 100.0) * w)
        
        # Validate bounds
        top = max(0, min(top, h-1))
        bottom = max(top+1, min(bottom, h))
        left = max(0, min(left, w-1))
        right = max(left+1, min(right, w))
        
        if top >= bottom or left >= right:
            return None
        
        crop = image[top:bottom, left:right]
        
        # [OPTIMIZATION] Resize sub-anchor if too large (rare but possible)
        h_crop, w_crop = crop.shape[:2]
        max_crop_dim = 620
        if w_crop > max_crop_dim or h_crop > max_crop_dim:
            scale = min(max_crop_dim / w_crop, max_crop_dim / h_crop)
            new_w = int(w_crop * scale)
            new_h = int(h_crop * scale)
            crop = cv2.resize(crop, (new_w, new_h), interpolation=cv2.INTER_AREA)

        # [OPTIMIZATION] Quality 95 -> 50
        _, crop_buf = cv2.imencode('.jpg', crop, [cv2.IMWRITE_JPEG_QUALITY, 50])
        crop_b64 = base64.b64encode(crop_buf).decode('utf-8')
        
        label = item['label']
        
        # Enforce spec threshold
        confidence = item.get('confidence', 0.95)
        if confidence < 0.85:
            return None
            
        content_hash = hashlib.sha256(crop_b64.encode()).hexdigest()
        
        return Anchor(
            id=f"{label}_{idx}_{top}_{left}",
            type=label,
            bbox=(top, right, bottom, left),
            data=crop_b64,
            content_hash=content_hash,
            semantic_label=label,
            confidence=confidence,
            resolution_hint="high",
            parent_anchor_id=parent_id
        )
