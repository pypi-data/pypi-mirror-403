import cv2
import numpy as np

class SaliencyExtractor:
    def __init__(self):
        # We can use StaticSaliencySpectralResidual or FineGrained
        try:
            self.saliency = cv2.saliency.StaticSaliencySpectralResidual_create()
        except AttributeError:
            print("Warning: cv2.saliency not available. Ensure opencv-contrib-python is installed if needed.")
            self.saliency = None

    def compute_saliency(self, image: np.ndarray) -> np.ndarray:
        """
        Compute saliency map for the input image.
        Returns a float32 probability map (0.0-1.0).
        """
        if self.saliency is None:
            # Fallback or dummy implementation if module missing
            # In production, this should fail loudly or use a different method
            # Per spec: If no high-saliency regions detected, encoding must abort.
            # Here we return a zero map which should trigger failure upstream.
             print("❌ Saliency extraction unavailable (cv2.saliency missing).")
             h, w = image.shape[:2]
             return np.zeros((h, w), dtype=np.float32)

        start = cv2.getTickCount()
        success, saliency_map = self.saliency.computeSaliency(image)
        
        if success:
            # Normalize to 0-1 range float32
            saliency_map = saliency_map.astype("float32")
            min_val, max_val, _, _ = cv2.minMaxLoc(saliency_map)
            
            if max_val > min_val:
                saliency_map = (saliency_map - min_val) / (max_val - min_val)
            else:
                saliency_map.fill(0.0)
                
            return saliency_map
        else:
            return np.zeros(image.shape[:2], dtype=np.float32)

    def get_salient_regions(self, image: np.ndarray) -> np.ndarray:
        """
        Get binary mask of salient regions. 
        Note: Currently returns probability map, thresholding handled by caller or here if needed.
        """
        # For compatibility, we'll return the probability map but maybe threshold it?
        # Actually, let's stick to the spec which mentions confidence scores.
        # But existing pipeline expects a mask? Let's check pipeline usage.
        # Pipeline: saliency_map = self.saliency_extractor.get_salient_regions(image)
        # It doesn't seem to use it deeply yet (just stores it).
        return self.compute_saliency(image)
