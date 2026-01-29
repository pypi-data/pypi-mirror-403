import cv2
import base64
import os
import hashlib
from datetime import datetime
from ..schema.blueprint import HelixBlueprint, Anchor, Metadata, Mesh

class VideoAnchorExtractor:
    """
    Extracts Temporal Keyframes from Video files.
    
    Approach:
    - Samples the video at a fixed interval (e.g. 1 FPS).
    - Stores each sample as a 'keyframe' anchor with efficient compression.
    - Preserves temporal metadata (timestamps) for reconstruction.
    """
    
    def __init__(self, sample_interval_sec: float = 1.0):
        self.sample_interval = sample_interval_sec
        
    def extract(self, video_path: str) -> HelixBlueprint:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
            
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Failed to open video: {video_path}")
            
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if fps <= 0: fps = 24.0 # default fallback
        
        duration = frame_count / fps
        
        anchors = []
        
        # Sampling Loop
        current_frame = 0
        frame_interval = int(fps * self.sample_interval)
        if frame_interval < 1: frame_interval = 1
        
        while True:
            cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            ret, frame = cap.read()
            if not ret:
                break
                
            # Compress Keyframe
            # We use JPEG with quality 60 for "Draft" anchors, or 80 for standard
            _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
            b64_data = base64.b64encode(buffer).decode('utf-8')
            frame_hash = hashlib.sha256(b64_data.encode()).hexdigest()
            
            timestamp = current_frame / fps
            
            anchor = Anchor(
                id=f"frame_{current_frame}",
                type="video_keyframe",
                timestamp_start=timestamp,
                timestamp_end=timestamp + self.sample_interval,
                data=b64_data,
                content_hash=frame_hash,
                resolution_hint="standard"
            )
            anchors.append(anchor)
            
            current_frame += frame_interval
            
            if current_frame >= frame_count:
                break
                
        cap.release()
        
        metadata = Metadata(
            modality="video",
            asset_type="mp4/avi/mov",
            original_dims=(width, height),
            checksum=anchors[0].content_hash if anchors else "",
            scene_description=f"Video sequence, {duration:.2f}s, {len(anchors)} keyframes.",
            aura="Temporal Sequence"
        )
        
        # We store FPS in the freedom field for reconstruction
        freedom_params = {
            "fps": fps,
            "sample_interval": self.sample_interval
        }
        
        return HelixBlueprint(
            metadata=metadata,
            anchors=anchors,
            mesh=Mesh(),
            freedom=freedom_params
        )
