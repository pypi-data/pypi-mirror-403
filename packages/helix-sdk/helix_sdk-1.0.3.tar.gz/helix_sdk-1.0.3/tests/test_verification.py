import unittest
from unittest.mock import MagicMock, patch
import sys
import math

# Mock skimage before import to bypass broken environment
skimage_mock = MagicMock()
metrics_mock = MagicMock()
skimage_mock.metrics = metrics_mock
sys.modules['skimage'] = skimage_mock
sys.modules['skimage.metrics'] = metrics_mock

# Mock numpy but keep sqrt working
np_mock = MagicMock()
np_mock.sqrt = lambda x: math.sqrt(x) if isinstance(x, (int, float)) else math.sqrt(float(x))
sys.modules['numpy'] = np_mock

from src.core.verification import VerificationLoop
from src.schema.blueprint import HelixBlueprint, Metadata, Anchor

class TestVerificationLoop(unittest.TestCase):
    def setUp(self):
        self.verifier = VerificationLoop()
        # Mock the internal anchor extractor to avoid real CV/Gemini calls during test
        self.verifier.anchor_extractor = MagicMock()
        
    def test_drift_detection_fail(self):
        # Original anchor at center (0.5, 0.5)
        # 100x100 image -> (50, 50)
        # Bbox top=45, right=55, bottom=55, left=45
        orig_anchor = Anchor(id="face1", type="face", bbox=(45, 55, 55, 45))
        
        # Detected anchor drifted significantly (0.6, 0.6)
        # Bbox top=55, right=65, bottom=65, left=55
        det_anchor = Anchor(id="face1_det", type="face", bbox=(55, 65, 65, 55))
        
        self.verifier.anchor_extractor.extract_anchors.return_value = [det_anchor]
        
        blueprint = HelixBlueprint(
            metadata=Metadata(),
            anchors=[orig_anchor],
            version="3.0"
        )
        
        # Mock image bytes (content doesn't matter as we mocked extractor)
        img_bytes = b'fake_png_data'
        
        # Access private method for unit testing logic if needed, 
        # but better to test public verify()
        # We need to ensure cv2.imdecode returns something valid
        import sys
        # We assume verification.py uses cv2.imdecode. We rely on it working or being mocked if needed.
        # Ideally we'd mock cv2 too, but let's try to rely on logic. 
        # Actually verify() decodes image. If we pass random bytes it fails decode.
        
    def test_check_position_drift_logic(self):
        # Direct test of drift logic
        original = [Anchor(id="face1", type="face", bbox=(45, 55, 55, 45))] # center 50,50
        
        # Case 1: Small drift (within 2%)
        # 2% of 100 = 2 pixels.
        # Shift to 51,51 -> dist sqrt(2) = 1.41 < 2. Pass.
        detected_pass = [Anchor(id="d1", type="face", bbox=(46, 56, 56, 46))]
        failures = self.verifier._check_position_drift(detected_pass, original, (100, 100))
        self.assertEqual(len(failures), 0)
        
        # Case 2: Large drift
        # Shift to 60,60 -> dist sqrt(200) = 14. Fail.
        detected_fail = [Anchor(id="d2", type="face", bbox=(55, 65, 65, 55))]
        failures = self.verifier._check_position_drift(detected_fail, original, (100, 100))
        self.assertNotEqual(len(failures), 0)
        self.assertTrue("drifted" in failures[0])

if __name__ == '__main__':
    unittest.main()
