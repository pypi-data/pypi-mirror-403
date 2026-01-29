import cv2
import base64
import os
import numpy as np
from typing import List
from ..schema.blueprint import HelixBlueprint, Anchor

class VideoMaterializer:
    """
    Materializes Video from HELIX Blueprints.
    
    Current V1 Logic:
    - Reconstructs video from 'video_keyframe' anchors.
    - If 'freedom.fps' is set, tries to match original playback speed by holding frames.
    - Does NOT currently perform interpolation or AI frame generation (Tier 3 features).
    """
    
    def materialize(self, blueprint: HelixBlueprint, output_path: str = "output.mp4") -> bytes:
        """
        Reconstruct video file. Returns bytes of the MP4 file.
        Note: OpenCV writes to file directly. We will write to a temp file then read bytes.
        """
        if blueprint.metadata.modality != "video":
            raise ValueError(f"Invalid modality for VideoMaterializer: {blueprint.metadata.modality}")
            
        # Sort anchors by timestamp
        keyframes = sorted(
            [a for a in blueprint.anchors if a.type == "video_keyframe"],
            key=lambda x: x.timestamp_start or 0
        )
        
        if not keyframes:
            raise ValueError("No video keyframes found in blueprint.")
            
        # Determine Video Props
        original_dims = blueprint.metadata.original_dims
        width, height = original_dims if original_dims and original_dims[0] > 0 else (1280, 720) # Fallback
        
        fps = float(blueprint.freedom.get("fps", 24.0))
        sample_interval = float(blueprint.freedom.get("sample_interval", 1.0))
        
        # Setup Video Writer
        # FourCC: 'mp4v' for mp4
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        
        # Write to temp file first because cv2 needs a filename
        temp_file = output_path
        out = cv2.VideoWriter(temp_file, fourcc, fps, (width, height))
        
        if not out.isOpened():
            # Try MJPG/avi as fallback if codecs are missing
            temp_file = output_path.replace(".mp4", ".avi")
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            out = cv2.VideoWriter(temp_file, fourcc, fps, (width, height))
            
        # Rendering Loop
        frames_per_keyframe = int(fps * sample_interval)
        if frames_per_keyframe < 1: frames_per_keyframe = 1
        
        for kf in keyframes:
            if not kf.data:
                continue
                
            # Decode Frame
            nparr = np.frombuffer(base64.b64decode(kf.data), np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                print(f"Warning: Failed to decode frame {kf.id}")
                continue
                
            # Resize if needed to match video dims
            if img.shape[1] != width or img.shape[0] != height:
                img = cv2.resize(img, (width, height))
            
            # Write 'Hold' Frames to fill time
            for _ in range(frames_per_keyframe):
                out.write(img)
                
        out.release()
        
        # Read back purely to satisfy the 'return bytes' interface if needed
        # But usually we just leave the file.
        # For compatibility with CLI that expects to write the bytes itself, 
        # we read it.
        
        with open(temp_file, 'rb') as f:
            video_bytes = f.read()
            
        # Clean up is handled by caller (who overwrites) or we just return bytes
        # The CLI currently does `with open(output_path, 'wb')`. 
        # So we should return the bytes.
        
        return video_bytes
