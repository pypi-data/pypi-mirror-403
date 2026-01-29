import unittest
import sys
import os
sys.path.append(os.getcwd())
from src.core.mesh_builder import MeshBuilder
from src.schema.blueprint import Anchor, Mesh
import math

class TestMeshBuilder(unittest.TestCase):
    def setUp(self):
        self.builder = MeshBuilder()

    def test_build_mesh_simple(self):
        # Create 2 anchors
        # Image size 100x100
        # Anchor 1 at (10, 10) center
        # Anchor 2 at (90, 90) center
        
        # Bbox: top, right, bottom, left
        # A1 center(10, 10): top=5, bottom=15, left=5, right=15 -> w=10, h=10
        a1 = Anchor(id="a1", type="face", bbox=(5, 15, 15, 5)) 
        
        # A2 center(90, 90): top=85, bottom=95, left=85, right=95 -> w=10, h=10
        a2 = Anchor(id="a2", type="face", bbox=(85, 95, 95, 85))

        anchors = [a1, a2]
        dims = (100, 100) # h, w

        mesh = self.builder.build_mesh(anchors, dims)
        
        # Verify Centroid
        # (10+90)/2 = 50, (10+90)/2 = 50
        # Normalized: 50/100, 50/100 = 0.5, 0.5
        self.assertAlmostEqual(mesh.centroid[0], 0.5)
        self.assertAlmostEqual(mesh.centroid[1], 0.5)

        # Verify Constraints for A1
        # Centroid is at (50, 50). A1 at (10, 10).
        # dx = 10-50 = -40, dy = 10-50 = -40
        # dist = sqrt(1600+1600) = sqrt(3200) = 56.568
        # Diagonal of 100x100 = 141.42
        # norm_dist = 56.568 / 141.42 = 0.4
        
        c1 = mesh.constraints["a1"]
        expected_dist = math.sqrt(3200) / math.sqrt(20000)
        self.assertAlmostEqual(c1["dist_to_c"], expected_dist)
        
        # Angle: atan2(-40, -40) = -3pi/4 (approx -2.356)
        self.assertAlmostEqual(c1["angle_c"], math.atan2(-40, -40))
        
        # Aspect Ratio: 10/10 = 1.0
        self.assertAlmostEqual(c1["aspect_ratio"], 1.0)

    def test_empty_anchors(self):
        mesh = self.builder.build_mesh([], (100, 100))
        self.assertIsNone(mesh.centroid)
        self.assertEqual(len(mesh.constraints), 0)

if __name__ == '__main__':
    unittest.main()
