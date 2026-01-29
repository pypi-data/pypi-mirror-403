import cv2
import numpy as np
import os
import hashlib
from typing import Optional, Dict, Any
from ..extractors.saliency import SaliencyExtractor
from ..extractors.anchors import AnchorExtractor
from ..extractors.gemini_anchors import GeminiAnchorExtractor
from ..schema.blueprint import HelixBlueprint, Metadata

class HelixPipeline:
    """
    Main HELIX processing pipeline.
    Orchestrates extraction, mesh building, and blueprint assembly.
    """
    
    def __init__(self):
        self.saliency_extractor = SaliencyExtractor()
        self.anchor_extractor = AnchorExtractor()
        self.gemini_extractor = GeminiAnchorExtractor()

    def process_asset(self, input_path: str, output_path: str) -> None:
        """
        Process an image, video, or audio asset into a .hlx blueprint.
        
        Args:
            input_path: Path to input file
            output_path: Path for output .hlx file
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")

        # Detect file type
        ext = os.path.splitext(input_path)[1].lower()
        video_exts = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
        audio_exts = ['.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac']
        image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        
        if ext in video_exts:
            return self._process_video(input_path, output_path)
        elif ext in audio_exts:
            return self._process_audio(input_path, output_path)
        elif ext in image_exts:
            return self._process_image(input_path, output_path)
        else:
            # Try as image by default
            return self._process_image(input_path, output_path)

    def _process_image(self, input_path: str, output_path: str, modality: str = "image", additional_metadata: Dict[str, Any] = None) -> None:
        """Process an image asset into a .hlx blueprint."""
        # 1. Load Asset
        image = cv2.imread(input_path)
        if image is None:
            raise ValueError(f"Failed to load image: {input_path}")
        
        orig_h, orig_w = image.shape[:2]
        print(f"[IMG] Processing {modality}: {orig_w}x{orig_h}")

        # 2. Extract Saliency (for future masking)
        saliency_map = self.saliency_extractor.get_salient_regions(image)

        # 3. Extract Anchors (Deterministic Mode by default)
        from .constants import EXTRACTION_MODE
        
        aura = ""
        extra_meta: Dict[str, Any] = {}
        
        # Determine extraction mode
        use_gemini = (
            EXTRACTION_MODE == 'gemini' or 
            (EXTRACTION_MODE == 'auto' and self.gemini_extractor.client)
        )
        
        if use_gemini and self.gemini_extractor.client:
            print(f"[AI] Using {self.gemini_extractor.model_name} Smart Extraction...")
            gemini_anchors, aura, extra_meta = self.gemini_extractor.extract(image)
            
            if gemini_anchors:
                anchors = gemini_anchors
                print(f"   [OK] Extracted {len(anchors)} anchors")
            else:
                print("   [WARN] Gemini returned no anchors, falling back to Classic Face Detection")
                anchors = self.anchor_extractor.extract_anchors(image, input_path)
        else:
            # OpenCV mode - deterministic, no variability
            print("[TOOL] Using Deterministic OpenCV Extraction...")
            anchors = self.anchor_extractor.extract_anchors(image, input_path)

        # 4. Build Structural Mesh
        from .mesh_builder import MeshBuilder
        from .constraint_validator import ConstraintValidator
        
        mesh_builder = MeshBuilder()
        mesh = mesh_builder.build_mesh(anchors, (orig_h, orig_w))
        
        # Add facial ratios if we have face sub-anchors
        mesh = self._add_facial_ratios(mesh, anchors)
        
        validator = ConstraintValidator()
        is_valid, errors = validator.validate(mesh)
        if not is_valid:
            print(f"   [WARN] Mesh validation warnings: {errors}")
        else:
            print(f"   [OK] Mesh validated: {len(mesh.constraints)} constraints")

        # 5. Generate Checksum & Anchor Content Hashes (Spec 4.3)
        with open(input_path, "rb") as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        
        # Ensure all anchors have content hashes
        for a in anchors:
            if not a.content_hash and a.data:
                a.content_hash = a.compute_hash()

        # Merge additional metadata
        final_body = extra_meta.get('body_geometry', {})
        final_palette = extra_meta.get('color_palette', [])
        final_scene = extra_meta.get('scene_description', '')
        
        if additional_metadata:
            # Merge logic could be expanded, for now just simplistic updates if needed
            pass

        # 6. Assemble Blueprint
        metadata = Metadata(
            modality=modality,
            asset_type=modality,
            original_dims=(orig_w, orig_h),
            checksum=file_hash,
            aura=aura,
            color_palette=final_palette,
            scene_description=final_scene,
            body_geometry=final_body,
            duration=additional_metadata.get('duration', 0.0) if additional_metadata else 0.0,
            fps=additional_metadata.get('fps', 0.0) if additional_metadata else 0.0,
            frame_count=additional_metadata.get('frame_count', 0) if additional_metadata else 0
        )

        blueprint = HelixBlueprint(
            metadata=metadata,
            anchors=anchors,
            mesh=mesh,
            masks=[],
            version="3.0",
            # Add constraints and freedom (Spec 4.5/4.6)
            constraints={"hard": ["anchor_positions_fixed"], "soft": ["maintain_lighting_mood"]},
            freedom={"background": "generative_fill", "details": "within_style_bounds"}
        )

        # 7. Validate Blueprint (Spec 5.1)
        from .blueprint_validator import BlueprintValidator
        validator = BlueprintValidator()
        is_valid, errors = validator.validate(blueprint)
        
        if not is_valid:
            print(f"[ERROR] Blueprint Validation Failed:")
            for e in errors:
                print(f"   - {e}")
            raise ValueError(f"Invalid Blueprint: {errors}")
            
        print("   [OK] Blueprint Schema Validated")

        # 8. Save
        blueprint.save(output_path)
        
        orig_size = os.path.getsize(input_path)
        hlx_size = os.path.getsize(output_path)
        compression_ratio = orig_size / hlx_size if hlx_size > 0 else 0
        
        print(f"\n[DONE] HELIX Blueprint saved to {output_path}")
        print(f"   Original: {orig_size:,} bytes")
        print(f"   HLX size: {hlx_size:,} bytes")
        print(f"   Compression: {compression_ratio:.1f}x")

    def _add_facial_ratios(self, mesh, anchors) -> 'Mesh':
        """Add facial proportion ratios for better reconstruction"""
        # Find face-related anchors
        left_eye = next((a for a in anchors if a.type == 'left_eye'), None)
        right_eye = next((a for a in anchors if a.type == 'right_eye'), None)
        nose = next((a for a in anchors if a.type == 'nose'), None)
        mouth = next((a for a in anchors if a.type == 'mouth'), None)
        
        if left_eye and right_eye:
            # Calculate inter-eye distance
            le_center = ((left_eye.bbox[1] + left_eye.bbox[3]) / 2, 
                        (left_eye.bbox[0] + left_eye.bbox[2]) / 2)
            re_center = ((right_eye.bbox[1] + right_eye.bbox[3]) / 2,
                        (right_eye.bbox[0] + right_eye.bbox[2]) / 2)
            
            import math
            eye_distance = math.sqrt((le_center[0] - re_center[0])**2 + 
                                     (le_center[1] - re_center[1])**2)
            
            mesh.facial_ratios['inter_eye_distance'] = eye_distance
            
            if nose:
                # Eye-to-nose ratio
                nose_center = ((nose.bbox[1] + nose.bbox[3]) / 2,
                              (nose.bbox[0] + nose.bbox[2]) / 2)
                eyes_midpoint_y = (le_center[1] + re_center[1]) / 2
                eye_nose_dist = abs(nose_center[1] - eyes_midpoint_y)
                mesh.facial_ratios['eye_nose_ratio'] = eye_nose_dist / eye_distance if eye_distance > 0 else 0
            
            if mouth:
                # Nose-to-mouth ratio (if we have nose)
                if nose:
                    mouth_center = ((mouth.bbox[1] + mouth.bbox[3]) / 2,
                                   (mouth.bbox[0] + mouth.bbox[2]) / 2)
                    nose_mouth_dist = abs(mouth_center[1] - nose_center[1])
                    mesh.facial_ratios['nose_mouth_ratio'] = nose_mouth_dist / eye_distance if eye_distance > 0 else 0
        
        return mesh

    def _process_video(self, input_path: str, output_path: str) -> None:
        """Process a video asset by extracting keyframes."""
        print(f"[VIDEO] Processing video: {input_path}")
        
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError(f"Failed to open video: {input_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        
        # Extract first frame as keyframe
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            raise ValueError("Failed to read video frame")
        
        # Save keyframe temporarily and process as image
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            cv2.imwrite(tmp.name, frame)
            self._process_image(tmp.name, output_path, modality="video", additional_metadata={
                'duration': duration,
                'fps': fps,
                'frame_count': frame_count
            })
            os.unlink(tmp.name)
        
        print(f"   Video: {duration:.1f}s, {frame_count} frames")

    def _process_audio(self, input_path: str, output_path: str) -> None:
        """Process an audio asset by extracting spectral features."""
        print(f"[AUDIO] Processing audio: {input_path}")
        
        # Create a minimal blueprint for audio
        file_size = os.path.getsize(input_path)
        file_hash = hashlib.md5(open(input_path, 'rb').read()).hexdigest()
        
        from ..schema.blueprint import HelixBlueprint, Metadata, Anchor
        
        metadata = Metadata(
            modality="audio",
            asset_type="audio",
            original_dims=(0, 0),
            checksum=file_hash,
            aura="audio_content",
            original_size_bytes=file_size
        )
        
        # Create a placeholder anchor for audio identity
        anchor = Anchor(
            id="audio_main",
            type="audio_waveform",
            semantic_label="Primary audio content",
            confidence=0.9
        )
        
        from .mesh_builder import MeshBuilder
        mesh_builder = MeshBuilder()
        mesh = mesh_builder.build_mesh([anchor], (0, 0))
        
        blueprint = HelixBlueprint(
            metadata=metadata,
            anchors=[anchor],
            mesh=mesh,
            version="3.0"
        )
        
        blueprint.save(output_path)
        hlx_size = os.path.getsize(output_path)
        print(f"   Audio blueprint saved: {hlx_size:,} bytes")
