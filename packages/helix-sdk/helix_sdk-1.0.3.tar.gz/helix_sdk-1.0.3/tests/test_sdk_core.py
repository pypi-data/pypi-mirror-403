"""
HELIX SDK Core Tests
====================
Tests for HelixSDK, HelixDataset, and HelixLoader functionality.
"""

import pytest
import os
import sys
import tempfile
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestHelixSDK:
    """Tests for the main HelixSDK class."""
    
    def test_sdk_initialization_no_key(self):
        """SDK should initialize in mock mode without API key."""
        # Temporarily remove API key
        old_key = os.environ.pop("GEMINI_API_KEY", None)
        try:
            from helix_sdk import HelixSDK
            sdk = HelixSDK(verbose=False)
            assert sdk.api_key is None
        finally:
            if old_key:
                os.environ["GEMINI_API_KEY"] = old_key
    
    def test_sdk_initialization_with_key(self):
        """SDK should configure with API key."""
        from helix_sdk import HelixSDK
        sdk = HelixSDK(api_key="test-key-12345", verbose=False)
        assert sdk.api_key == "test-key-12345"
    
    def test_resolution_enum(self):
        """Resolution enum should parse strings correctly."""
        from helix_sdk import Resolution
        
        assert Resolution.from_string("1080p") == Resolution.RES_1080P
        assert Resolution.from_string("4K") == Resolution.RES_4K
        assert Resolution.from_string("4k") == Resolution.RES_4K
        assert Resolution.from_string("unknown") == Resolution.RES_1080P  # default
    
    def test_hlx_format_enum(self):
        """HLX format enum values should be correct."""
        from helix_sdk import HLXFormat
        
        assert HLXFormat.V1.value == "v1"
        assert HLXFormat.V2.value == "v2"
    
    def test_supported_formats(self):
        """SDK should return supported format info."""
        from helix_sdk import HelixSDK
        
        formats = HelixSDK.get_supported_formats()
        assert ".jpg" in formats["input_formats"]
        assert ".hlx" in formats["output_formats"]
        assert "v1" in formats["hlx_versions"]
        assert "v2" in formats["hlx_versions"]
    
    def test_compress_nonexistent_file(self):
        """Compress should return error for nonexistent file."""
        from helix_sdk import HelixSDK
        
        sdk = HelixSDK(verbose=False)
        result = sdk.compress("/nonexistent/path/image.jpg")
        
        assert result.success is False
        assert "not found" in result.error.lower()
    
    def test_materialize_nonexistent_file(self):
        """Materialize should return error for nonexistent file."""
        from helix_sdk import HelixSDK
        
        sdk = HelixSDK(verbose=False)
        result = sdk.materialize("/nonexistent/path/image.hlx")
        
        assert result.success is False
        assert "not found" in result.error.lower()
    
    def test_compression_result_dataclass(self):
        """CompressionResult should have all expected fields."""
        from helix_sdk import CompressionResult
        
        result = CompressionResult(
            input_path="/test/input.jpg",
            output_path="/test/output.hlx",
            input_size=1024000,
            output_size=102400,
            compression_ratio=10.0,
            success=True
        )
        
        assert result.compression_ratio == 10.0
        assert result.success is True
    
    def test_batch_stats_calculations(self):
        """BatchStats should calculate ratios correctly."""
        from helix_sdk import BatchStats
        
        stats = BatchStats(
            files_processed=10,
            total_input_bytes=10_000_000,  # 10MB
            total_output_bytes=1_000_000    # 1MB
        )
        
        assert stats.compression_ratio == 10.0
        assert stats.space_saved_percent == 90.0


class TestHelixDataset:
    """Tests for HelixDataset functionality."""
    
    def test_dataset_empty_dir(self):
        """Dataset should handle empty directory gracefully."""
        from helix_sdk import HelixDataset
        
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset = HelixDataset(tmpdir)
            assert len(dataset) == 0
    
    def test_dataset_nonexistent_path(self):
        """Dataset should raise error for nonexistent path."""
        from helix_sdk import HelixDataset
        
        with pytest.raises(ValueError):
            HelixDataset("/nonexistent/path/")
    
    def test_dataset_index_out_of_range(self):
        """Dataset should raise IndexError for invalid index."""
        from helix_sdk import HelixDataset
        
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset = HelixDataset(tmpdir)
            with pytest.raises(IndexError):
                _ = dataset[0]


class TestHelixLoader:
    """Tests for HelixLoader functionality."""
    
    def test_loader_len_calculation(self):
        """Loader should calculate correct number of batches."""
        from helix_sdk import HelixDataset, HelixLoader
        
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset = HelixDataset(tmpdir)
            loader = HelixLoader(dataset, batch_size=10)
            assert len(loader) == 0  # Empty dataset
    
    def test_loader_with_variants(self):
        """Loader should multiply samples by variants."""
        from helix_sdk import HelixDataset, HelixLoader
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock dataset with controlled length
            dataset = HelixDataset(tmpdir)
            # Manually add some paths for testing
            dataset._hlx_files = [Path(tmpdir) / f"test_{i}.hlx" for i in range(10)]
            
            loader = HelixLoader(dataset, batch_size=10, variants_per_image=3)
            # 10 files * 3 variants = 30 samples, 30 / 10 batch_size = 3 batches
            assert len(loader) == 3


class TestIntegration:
    """Integration tests requiring actual files."""
    
    @pytest.mark.skipif(
        not os.path.exists("tests/fixtures/sample.jpg"),
        reason="Test fixture not found"
    )
    def test_full_encode_decode_cycle(self):
        """Test encoding an image and decoding it back."""
        from helix_sdk import HelixSDK
        
        sdk = HelixSDK(verbose=False)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = "tests/fixtures/sample.jpg"
            hlx_path = Path(tmpdir) / "sample.hlx"
            output_path = Path(tmpdir) / "sample_out.png"
            
            # Compress
            compress_result = sdk.compress(input_path, str(hlx_path))
            assert compress_result.success
            assert hlx_path.exists()
            
            # Materialize
            mat_result = sdk.materialize(str(hlx_path), str(output_path))
            assert mat_result.success
            assert output_path.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
