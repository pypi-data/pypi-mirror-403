import numpy as np
from typing import List, Tuple, Dict
from ..schema.blueprint import Anchor
import base64
import cv2

# Import HELIX constants
from ..core.constants import (
    BACKGROUND_MAX_DIMENSION, BACKGROUND_JPEG_QUALITY,
    FACE_MAX_DIMENSION, FACE_JPEG_QUALITY,
    HAAR_SCALE_FACTOR, HAAR_MIN_NEIGHBORS, HAAR_MIN_SIZE
)

# Try to import face_recognition, but make it optional
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("WARNING: face_recognition not installed. Using OpenCV fallback for face detection.")

class AnchorExtractor:
    """
    Fallback anchor extractor using OpenCV.
    Used when Gemini extraction is unavailable.
    """
    
    def __init__(self):
        # Load OpenCV's pre-trained face cascade
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

    def extract_anchors(self, image: np.ndarray, image_path: str = None) -> List[Anchor]:
        """
        Extract identity anchors from the image.
        Uses face_recognition if available, otherwise falls back to OpenCV.
        Also creates a background anchor for hybrid reconstruction.
        """
        anchors = []

        if FACE_RECOGNITION_AVAILABLE:
            anchors = self._extract_with_face_recognition(image)
        else:
            anchors = self._extract_with_opencv(image)

        # Add background anchor for hybrid mode
        bg_anchor = self._create_background_anchor(image)
        anchors.insert(0, bg_anchor)

        return anchors
    
    def _create_background_anchor(self, image: np.ndarray) -> Anchor:
        """
        Create full-image background anchor at high quality for 8K support.
        [QUALITY] Increased to max 4096px and quality 82 for crisp reconstruction.
        """
        import hashlib
        h, w = image.shape[:2]
        
        # Resize if too large - uses HELIX constant for max dimension
        scale = min(BACKGROUND_MAX_DIMENSION / w, BACKGROUND_MAX_DIMENSION / h)
        if scale < 1.0:
            new_w = int(w * scale)
            new_h = int(h * scale)
            bg_img = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        else:
            bg_img = image
        
        # Use HELIX constant for JPEG quality
        _, bg_buf = cv2.imencode('.jpg', bg_img, [cv2.IMWRITE_JPEG_QUALITY, BACKGROUND_JPEG_QUALITY])
        bg_b64 = base64.b64encode(bg_buf).decode('utf-8')
        content_hash = hashlib.sha256(bg_b64.encode()).hexdigest()
        
        return Anchor(
            id="background_full",
            type="background",
            bbox=(0, w, h, 0),
            data=bg_b64,
            content_hash=content_hash,
            semantic_label="background",
            confidence=1.0
        )

    def _extract_with_face_recognition(self, image: np.ndarray) -> List[Anchor]:
        """Extract faces using face_recognition library"""
        anchors = []
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_image)

        for i, (top, right, bottom, left) in enumerate(face_locations):
            face_crop = image[top:bottom, left:right]
            
            # Resize crop if too large - uses HELIX constant
            h_crop, w_crop = face_crop.shape[:2]
            if w_crop > FACE_MAX_DIMENSION or h_crop > FACE_MAX_DIMENSION:
                scale = min(FACE_MAX_DIMENSION / w_crop, FACE_MAX_DIMENSION / h_crop)
                new_w = int(w_crop * scale)
                new_h = int(h_crop * scale)
                face_crop = cv2.resize(face_crop, (new_w, new_h), interpolation=cv2.INTER_AREA)

            # Use HELIX constant for JPEG quality
            retval, buffer = cv2.imencode('.jpg', face_crop, [cv2.IMWRITE_JPEG_QUALITY, FACE_JPEG_QUALITY])
            jpg_as_text = base64.b64encode(buffer).decode('utf-8')

            anchor = Anchor(
                id=f"face_{i}_{int(top)}_{int(left)}",
                type="face",
                bbox=(top, right, bottom, left),
                data=jpg_as_text,
                semantic_label="face",
                confidence=1.0
            )
            anchors.append(anchor)

        return anchors

    def _extract_with_opencv(self, image: np.ndarray) -> List[Anchor]:
        """Extract faces using OpenCV Haar Cascade (fallback)"""
        anchors = []
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Use HELIX constants for Haar cascade parameters
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=HAAR_SCALE_FACTOR,
            minNeighbors=HAAR_MIN_NEIGHBORS,
            minSize=HAAR_MIN_SIZE
        )

        for i, (x, y, w, h) in enumerate(faces):
            # Convert to (top, right, bottom, left) format
            # [FIX] Explicit cast to int() for JSON serialization
            top, right, bottom, left = int(y), int(x + w), int(y + h), int(x)
            
            face_crop = image[top:bottom, left:right]

            # Resize crop if too large - uses HELIX constant
            h_crop, w_crop = face_crop.shape[:2]
            if w_crop > FACE_MAX_DIMENSION or h_crop > FACE_MAX_DIMENSION:
                scale = min(FACE_MAX_DIMENSION / w_crop, FACE_MAX_DIMENSION / h_crop)
                new_w = int(w_crop * scale)
                new_h = int(h_crop * scale)
                face_crop = cv2.resize(face_crop, (new_w, new_h), interpolation=cv2.INTER_AREA)

            # Use HELIX constant for JPEG quality
            retval, buffer = cv2.imencode('.jpg', face_crop, [cv2.IMWRITE_JPEG_QUALITY, FACE_JPEG_QUALITY])
            jpg_as_text = base64.b64encode(buffer).decode('utf-8')

            anchor = Anchor(
                id=f"face_{i}_{top}_{left}",
                type="face",
                bbox=(top, right, bottom, left),
                data=jpg_as_text,
                semantic_label="face",
                confidence=0.85  # Lower confidence for Haar cascade
            )
            anchors.append(anchor)

        return anchors
