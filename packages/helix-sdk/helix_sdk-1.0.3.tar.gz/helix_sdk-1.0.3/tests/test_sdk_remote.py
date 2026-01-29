"""
HELIX SDK Remote Mode Tests
===========================
Tests for remote API functionality in the SDK.
Uses mocks to simulate API responses.
"""

import pytest
import os
import sys
import json
import base64
import tempfile
from unittest.mock import MagicMock, patch
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from helix_sdk import HelixSDK, HelixDataset

class TestSDKRemote:
    """Tests for HelixSDK in Remote Mode."""
    
    @pytest.fixture
    def mock_httpx(self):
        """Mock httpx imports and Client"""
        with patch.dict(sys.modules, {'httpx': MagicMock()}):
            mock_module = sys.modules['httpx']
            mock_client = MagicMock()
            mock_module.Client.return_value.__enter__.return_value = mock_client
            yield mock_client

    def test_remote_initialization(self):
        """SDK should initialize in remote mode when base_url provided."""
        sdk = HelixSDK(base_url="http://test-api.com", verbose=False)
        assert sdk.mode == "remote"
        assert sdk.base_url == "http://test-api.com"
        
        # Check pipeline type
        from helix_sdk.remote import RemotePipeline
        assert isinstance(sdk.pipeline, RemotePipeline)
        
    def test_auto_mode_detection(self):
        """SDK should detect remote mode from base_url."""
        sdk = HelixSDK(base_url="http://api.helix.ai", mode="auto", verbose=False)
        assert sdk.mode == "remote"
        
    def test_dataset_remote_init(self):
        """Dataset should accept base_url."""
        with patch('helix_sdk.dataset.HelixDataset._discover_files'): # Skip file discovery
            dataset = HelixDataset(
                path="dummy", 
                base_url="http://api.helix.ai",
                target_resolution="1080p"
            )
            assert dataset.base_url == "http://api.helix.ai"
            
            # Check materializer
            from helix_sdk.remote import RemoteMaterializer
            assert isinstance(dataset._get_materializer(), RemoteMaterializer)

    @patch('helix_sdk.remote.httpx')
    def test_remote_encoding(self, mock_httpx):
        """Test encoding via remote pipeline."""
        # Setup mock
        mock_client = MagicMock()
        mock_httpx.Client.return_value.__enter__.return_value = mock_client
        
        # Mock Response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "hlx_file_b64": base64.b64encode(b"FAKE_HLX_DATA").decode('utf-8')
        }
        mock_client.post.return_value = mock_response
        
        # Init SDK
        sdk = HelixSDK(base_url="http://test.com", verbose=False)
        
        # Run compress
        # We need a fake input file
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as tmp_in, \
             tempfile.NamedTemporaryFile(delete=False) as tmp_out:
            
            tmp_in.write(b"IMAGE_DATA")
            tmp_in.close()
            tmp_out.close()
            
            try:
                result = sdk.compress(tmp_in.name, tmp_out.name)
                
                assert result.success
                
                # Check API called
                mock_client.post.assert_called_once()
                args, kwargs = mock_client.post.call_args
                assert args[0] == "http://test.com/api/encode/v2"
                assert 'files' in kwargs
                
                # Check output file
                with open(tmp_out.name, 'rb') as f:
                    assert f.read() == b"FAKE_HLX_DATA"
                    
            finally:
                os.unlink(tmp_in.name)
                os.unlink(tmp_out.name)

    @patch('helix_sdk.remote.httpx')
    def test_remote_materialization(self, mock_httpx):
        """Test materialization via remote materializer."""
        # Setup mock
        mock_client = MagicMock()
        mock_httpx.Client.return_value.__enter__.return_value = mock_client
        
        # Mock Response
        mock_response = MagicMock()
        mock_response.status_code = 200
        # API returns image data URI or base64? 
        # RemoteMaterializer expects json with 'image'
        b64_img = base64.b64encode(b"OUTPUT_IMAGE").decode('utf-8')
        mock_response.json.return_value = {
            "image": f"data:image/png;base64,{b64_img}",
            "upgradeMetrics": {"scale": 2}
        }
        mock_client.post.return_value = mock_response
        
        # Init SDK
        sdk = HelixSDK(base_url="http://test.com", verbose=False, cache_materializations=False)
        
        # Mock blueprint decode
        with patch('helix_sdk.core.decode') as mock_decode:
            mock_decode.return_value = {"mock": "blueprint"}
            
            # Need a fake HLX file
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False) as tmp_hlx, \
                 tempfile.NamedTemporaryFile(delete=False) as tmp_out:
                
                tmp_hlx.write(b"HLX_BINARY")
                tmp_hlx.close()
                tmp_out.close()
                
                try:
                    # Mock hlx_codec.encode used in RemoteMaterializer
                    with patch('src.core.hlx_codec.encode', return_value=b"SERIALIZED_BP"):
                        result = sdk.materialize(tmp_hlx.name, tmp_out.name)
                        
                        assert result.success
                        
                        # Check API called
                        mock_client.post.assert_called_once()
                        args, kwargs = mock_client.post.call_args
                        assert args[0] == "http://test.com/api/materialize"
                        
                        # Check output
                        with open(tmp_out.name, 'rb') as f:
                            assert f.read() == b"OUTPUT_IMAGE"
                            
                finally:
                    os.unlink(tmp_hlx.name)
                    os.unlink(tmp_out.name)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
