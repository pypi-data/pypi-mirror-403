import unittest
from unittest.mock import MagicMock
import sys
import os

# Ensure src is importable
sys.path.append(os.getcwd())

# 1. MOCK NUMPY
# We need a mock that allows indexing and has shape
class MockArray:
    def __init__(self, shape=(100, 100, 3)):
        self.shape = shape
    def __getitem__(self, key):
        return MockArray((10, 10, 3)) # Return smaller crop
    def __mul__(self, other):
        return self
    def __sub__(self, other):
        return self
    def __truediv__(self, other):
        return self
    def astype(self, t):
        return self

np_mock = MagicMock()
np_mock.ndarray = MockArray
np_mock.uint8 = "uint8"
np_mock.float32 = "float32"
np_mock.zeros.return_value = MockArray()
np_mock.ones.return_value = MockArray()

sys.modules['numpy'] = np_mock

# 2. MOCK CV2 & FACE_RECOGNITION
cv2_mock = MagicMock()
cv2_mock.imread.return_value = MockArray((100, 100, 3))
cv2_mock.cvtColor.return_value = MockArray((100, 100, 3))
cv2_mock.imencode.return_value = (True, b'fake_jpg_buffer')
cv2_mock.COLOR_BGR2RGB = 1
cv2_mock.THRESH_BINARY = 0
cv2_mock.THRESH_OTSU = 0
cv2_mock.threshold.return_value = (0, MockArray())
cv2_mock.getTickCount.return_value = 0
cv2_mock.minMaxLoc.return_value = (0.0, 1.0, (0,0), (10,10)) # min, max, minLoc, maxLoc

saliency_mock = MagicMock()
cv2_mock.saliency.StaticSaliencySpectralResidual_create.return_value = saliency_mock
saliency_mock.computeSaliency.return_value = (True, MockArray())

sys.modules['cv2'] = cv2_mock

fr_mock = MagicMock()
fr_mock.face_locations.return_value = [(10, 50, 60, 20)] #(top, right, bottom, left)
sys.modules['face_recognition'] = fr_mock

# 3. Import System Under Test
# We need to make sure we can import even if imports inside modules fail, 
# but since we mocked sys.modules, imports of numpy/cv2 inside pipeline will get our mocks.
# We also need to add current dir to path
sys.path.append(os.getcwd())

from src.core.pipeline import HelixPipeline

class TestHelixPhase1(unittest.TestCase):
    def setUp(self):
        self.pipeline = HelixPipeline()
        with open("test_dummy.jpg", "wb") as f:
            f.write(b"fake image data")

    def tearDown(self):
        if os.path.exists("test_dummy.jpg"):
            os.remove("test_dummy.jpg")
        if os.path.exists("test_output.hlx"):
            os.remove("test_output.hlx")

    def test_pipeline_flow(self):
        """Test the full pipeline flow with mocks"""
        output_path = "test_output.hlx"
        self.pipeline.process_asset("test_dummy.jpg", output_path)
        
        self.assertTrue(os.path.exists(output_path))
        
        # HLX files are now binary (msgpack). Just verify it can be loaded.
        file_size = os.path.getsize(output_path)
        self.assertGreater(file_size, 0)
        print(f"Blueprint saved successfully: {file_size} bytes")

if __name__ == '__main__':
    unittest.main()
