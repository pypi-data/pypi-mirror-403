import unittest
from src.core.blueprint_validator import BlueprintValidator
from src.schema.blueprint import HelixBlueprint, Metadata, Anchor, Mesh

class TestBlueprintValidator(unittest.TestCase):
    def setUp(self):
        self.validator = BlueprintValidator()
        self.metadata = Metadata(modality="image", asset_type="image", created_at="2024-01-01T00:00:00")
        self.anchors = [
            Anchor(id="a1", type="face", bbox=(0, 10, 10, 0), content_hash="hash123", confidence=0.9)
        ]
        self.mesh = Mesh(constraints={"a1": {"locked": True}})
        
    def test_valid_blueprint(self):
        bp = HelixBlueprint(
            metadata=self.metadata,
            anchors=self.anchors,
            mesh=self.mesh,
            version="3.0",
            constraints={"hard": ["a1_locked"], "soft": []},
            freedom={"background": "free"}
        )
        is_valid, errors = self.validator.validate(bp)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_invalid_version(self):
        bp = HelixBlueprint(self.metadata, self.anchors, version="1.0")
        is_valid, errors = self.validator.validate(bp)
        self.assertFalse(is_valid)
        self.assertIn("Unsupported schema version: 1.0", errors)

    def test_low_confidence_anchor(self):
        bad_anchor = Anchor(id="a2", type="face", bbox=(0,10,10,0), confidence=0.5)
        bp = HelixBlueprint(self.metadata, [bad_anchor], version="3.0")
        is_valid, errors = self.validator.validate(bp)
        # Should detect low confidence
        self.assertFalse(is_valid)
        self.assertTrue(any("below confidence" in e for e in errors))

    def test_freedom_conflict(self):
        # Conflict: Freedom 'lighting_direction' vs Hard 'lighting_fixed'
        bp = HelixBlueprint(
            self.metadata, self.anchors, version="3.0",
            constraints={"hard": ["lighting_fixed"]},
            freedom={"lighting_direction": "any"}
        )
        is_valid, errors = self.validator.validate(bp)
        self.assertFalse(is_valid)
        self.assertTrue(any("Conflict" in e for e in errors))

if __name__ == '__main__':
    unittest.main()
