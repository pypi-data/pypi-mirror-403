"""
HELIX SDK Remote Module
=======================
Enables use of HELIX features via API instead of local heavy models.
"""

import os
import io
import base64
import json
import time
from typing import Optional, Dict, Any, Tuple, Union, List
from pathlib import Path

# Try to import httpx
try:
    import httpx
except ImportError:
    httpx = None

from .core import CompressionResult, MaterializationResult

class RemoteError(Exception):
    pass

class RemotePipeline:
    """
    Remote implementation of HelixPipeline.
    Compresses images by sending them to the HELIX API.
    """
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        if not httpx:
            raise ImportError("httpx is required for Remote Mode. Install with: pip install httpx")
            
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = 300.0  # 5 minutes for large files
    
    def process_asset(self, input_path: str, output_path: str) -> None:
        """
        Compress image via API.
        Mimics HelixPipeline.process_asset signature.
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
            
        url = f"{self.base_url}/api/encode/v2"
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        # Prepare file upload
        files = {
            'file': (os.path.basename(input_path), open(input_path, 'rb'), 'application/octet-stream')
        }
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=headers, files=files)
                
            if response.status_code != 200:
                raise RemoteError(f"API Error ({response.status_code}): {response.text}")
                
            data = response.json()
            
            # Check for HLX data
            if 'hlx_file_b64' not in data:
                raise RemoteError("API response missing 'hlx_file_b64'")
                
            # Decode and write to file
            hlx_bytes = base64.b64decode(data['hlx_file_b64'])
            
            with open(output_path, 'wb') as f:
                f.write(hlx_bytes)
                
        except httpx.RequestError as e:
            raise RemoteError(f"Connection failed: {str(e)}")
        except Exception as e:
            raise RemoteError(f"Remote processing failed: {str(e)}")
        finally:
             files['file'][1].close()

class RemoteMaterializer:
    """
    Remote implementation of GeminiMaterializer.
    Materializes images by sending blueprint to HELIX API.
    """
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        if not httpx:
            raise ImportError("httpx is required for Remote Mode. Install with: pip install httpx")
            
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = 120.0  # 2 minutes for generation
        self.mock_mode = False # Remote is never "mock" in the local sense, API might be mock though
        self.model_name = "Remote API"

    def materialize(self, 
                    blueprint: Any,
                    target_resolution: str = "4K",
                    return_metrics: bool = False) -> Union[bytes, Tuple[bytes, Dict[str, Any]]]:
        """
        Materialize using API.
        Mimics GeminiMaterializer.materialize signature.
        """
        url = f"{self.base_url}/api/materialize"
        
        # Serialize blueprint to HLX format for upload
        # We need to send it as a file
        from src.core.hlx_codec import encode
        try:
            # Check if blueprint is a dict or object
            if hasattr(blueprint, 'to_dict'):
                bp_dict = blueprint.to_dict()
            else:
                bp_dict = blueprint
                
            hlx_bytes = encode(bp_dict)
            
        except Exception as e:
            raise ValueError(f"Failed to serialize blueprint: {e}")
            
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        # Form data
        data = {
            'target_resolution': target_resolution
        }
        
        files = {
            'file': ('blueprint.hlx', io.BytesIO(hlx_bytes), 'application/x-helix')
        }
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=headers, data=data, files=files)
                
            if response.status_code != 200:
                raise RemoteError(f"API Error ({response.status_code}): {response.text}")
            
            resp_data = response.json()
            
            # Extract image
            if 'image' not in resp_data:
                raise RemoteError("API response missing 'image'")
                
            # Image is base64 data URI
            img_uri = resp_data['image']
            if ',' in img_uri:
                img_b64 = img_uri.split(',')[1]
            else:
                img_b64 = img_uri
                
            img_bytes = base64.b64decode(img_b64)
            
            if return_metrics:
                # API returns upgradeMetrics
                metrics = resp_data.get('upgradeMetrics', {})
                return img_bytes, metrics
            
            return img_bytes
            
        except httpx.RequestError as e:
            raise RemoteError(f"Connection failed: {str(e)}")
        except Exception as e:
            raise RemoteError(f"Remote materialization failed: {str(e)}")
