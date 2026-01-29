import cv2
import os
import numpy as np
from src.extractors.video_extractor import VideoAnchorExtractor
from src.core.video_materializer import VideoMaterializer

def generate_test_video(filename, width=640, height=480, fps=24, duration=2):
    """Generate a simple moving circle video"""
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, fps, (width, height))
    
    if not out.isOpened():
        print("Fallback to avi")
        filename = filename.replace(".mp4", ".avi")
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        out = cv2.VideoWriter(filename, fourcc, fps, (width, height))
        
    frames = int(fps * duration)
    
    for i in range(frames):
        img = np.zeros((height, width, 3), np.uint8)
        # Move a circle
        x = int((i / frames) * width)
        y = height // 2
        cv2.circle(img, (x, y), 50, (0, 255, 0), -1)
        out.write(img)
        
    out.release()
    return filename

def test_video_flow():
    input_video = "test_video.mp4"
    output_hlx = "test_video.hlx"
    output_recon = "reconstructed_test_video.mp4"
    
    # 1. Generate
    print("Generating video...")
    real_input = generate_test_video(input_video)
    print(f"Generated {real_input}")
    
    # 2. Encode
    print("Encoding...")
    try:
        extractor = VideoAnchorExtractor(sample_interval_sec=0.5) # Fast sampling
        blueprint = extractor.extract(real_input)
        blueprint.save(output_hlx)
        print(f"Saved {output_hlx} with {len(blueprint.anchors)} keyframes")
    except Exception as e:
        print(f"Encode failed: {e}")
        return

    # 3. Materialize
    print("Materializing...")
    try:
        materializer = VideoMaterializer()
        _ = materializer.materialize(blueprint, output_path=output_recon)
        
        if os.path.exists(output_recon) and os.path.getsize(output_recon) > 0:
            print(f"✅ SUCCESS: Reconstructed {output_recon}")
        else:
            print("❌ FAILURE: Output file missing or empty")
            
    except Exception as e:
        print(f"Materialize failed: {e}")

    # Cleanup
    # if os.path.exists(real_input): os.remove(real_input)
    # if os.path.exists(output_hlx): os.remove(output_hlx)
    # if os.path.exists(output_recon): os.remove(output_recon)

if __name__ == "__main__":
    test_video_flow()
