"""
HELIX Secure .hlx Codec
=======================
Encrypts and signs blueprint data so only HELIX can read/write .hlx files.

📱 CROSS-PLATFORM COMPATIBILITY (v2 Format):
HLX v2 files are ALSO valid JPEG files! Any app can display the preview.
HELIX-aware apps can unlock the full blueprint for 4K/8K materialization.

v1 File Structure (Legacy):
- 4 bytes: Magic header "HLX\x00"
- 2 bytes: Version (uint16)
- 32 bytes: HMAC-SHA256 signature
- 16 bytes: AES-GCM nonce
- 16 bytes: AES-GCM auth tag
- N bytes: Encrypted payload (MessagePack binary)

v2 File Structure (Cross-Platform):
- Complete JPEG image (viewable by ANY app)
- 16 bytes: HELIX marker "HELIX_DATA_START"
- 4 bytes: Payload size (uint32)
- Encrypted blueprint (same as v1 payload section)

Security:
- AES-256-GCM for authenticated encryption
- HMAC-SHA256 for tamper detection on header
- Unique nonce per encode
"""

import os
import json
import struct
import hashlib
import hmac
from typing import Dict, Any, Tuple, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import msgpack

# HELIX Secret Key - In production, load from secure vault/env
# This is derived from a master secret. Change this in production!
_HELIX_MASTER_SECRET = os.getenv("HELIX_SECRET_KEY", "HELIX_DEFAULT_SECRET_KEY_CHANGE_ME_IN_PROD")
_KEY = hashlib.sha256(_HELIX_MASTER_SECRET.encode()).digest()  # 32 bytes for AES-256
_HMAC_KEY = hashlib.sha256((_HELIX_MASTER_SECRET + "_HMAC").encode()).digest()

# v1 Format constants
MAGIC_HEADER = b"HLX\x00"
FORMAT_VERSION = 1

# v2 Format constants (Cross-Platform)
HELIX_MARKER = b"HELIX_DATA_START"  # 16 bytes - marks start of HELIX data in JPEG
FORMAT_VERSION_V2 = 2


class HLXCodecError(Exception):
    """Base error for HLX codec operations"""
    pass


class HLXTamperingError(HLXCodecError):
    """Raised when tampering is detected"""
    pass


class HLXVersionError(HLXCodecError):
    """Raised when version is incompatible"""
    pass


# =============================================================================
# V1 FORMAT (Legacy - Encrypted Binary)
# =============================================================================

def encode(blueprint_dict: Dict[str, Any]) -> bytes:
    """
    Encode a blueprint dictionary into encrypted .hlx bytes (v1 format).
    
    Args:
        blueprint_dict: Blueprint as dictionary (from asdict(blueprint))
        
    Returns:
        Encrypted binary .hlx data
    """
    # 1. Serialize to MessagePack (binary, not JSON)
    payload = msgpack.packb(blueprint_dict, use_bin_type=True)
    
    # 2. Encrypt with AES-256-GCM
    nonce = os.urandom(16)  # 128-bit nonce
    aesgcm = AESGCM(_KEY)
    encrypted = aesgcm.encrypt(nonce, payload, None)
    
    # encrypted includes the auth tag (last 16 bytes)
    auth_tag = encrypted[-16:]
    ciphertext = encrypted[:-16]
    
    # 3. Build header
    header = MAGIC_HEADER + struct.pack(">H", FORMAT_VERSION)
    
    # 4. Sign header + nonce + tag with HMAC
    to_sign = header + nonce + auth_tag
    signature = hmac.new(_HMAC_KEY, to_sign, hashlib.sha256).digest()
    
    # 5. Assemble file: header | signature | nonce | tag | ciphertext
    hlx_data = header + signature + nonce + auth_tag + ciphertext
    
    return hlx_data


def decode(hlx_data: bytes) -> Dict[str, Any]:
    """
    Decode encrypted .hlx bytes into a blueprint dictionary.
    Handles both v1 (binary) and v2 (JPEG+data) formats.
    
    Args:
        hlx_data: Encrypted .hlx binary data
        
    Returns:
        Blueprint as dictionary (ready for HelixBlueprint.from_dict())
        
    Raises:
        HLXTamperingError: If file has been tampered with
        HLXVersionError: If version is incompatible
        HLXCodecError: For other decode errors
    """
    # Check for v2 format first (JPEG with embedded data)
    if is_hlx_v2(hlx_data):
        blueprint_dict, _ = decode_v2(hlx_data)
        return blueprint_dict
    
    # v1 format (original encrypted binary)
    if len(hlx_data) < 70:  # Minimum size: 4+2+32+16+16
        raise HLXCodecError("Invalid .hlx file: too small")
    
    # 1. Parse header
    if hlx_data[:4] != MAGIC_HEADER:
        raise HLXCodecError("Invalid .hlx file: bad magic header")
    
    version = struct.unpack(">H", hlx_data[4:6])[0]
    if version > FORMAT_VERSION:
        raise HLXVersionError(f"Unsupported .hlx version: {version}")
    
    # 2. Extract components
    signature = hlx_data[6:38]      # 32 bytes
    nonce = hlx_data[38:54]         # 16 bytes
    auth_tag = hlx_data[54:70]      # 16 bytes
    ciphertext = hlx_data[70:]      # rest
    
    # 3. Verify HMAC signature (tamper detection)
    header = hlx_data[:6]
    to_verify = header + nonce + auth_tag
    expected_sig = hmac.new(_HMAC_KEY, to_verify, hashlib.sha256).digest()
    
    if not hmac.compare_digest(signature, expected_sig):
        raise HLXTamperingError("❌ HELIX Security: File tampering detected! Signature mismatch.")
    
    # 4. Decrypt
    try:
        aesgcm = AESGCM(_KEY)
        encrypted_with_tag = ciphertext + auth_tag
        payload = aesgcm.decrypt(nonce, encrypted_with_tag, None)
    except Exception as e:
        raise HLXTamperingError(f"❌ HELIX Security: Decryption failed. File may be corrupted or tampered. {e}")
    
    # 5. Deserialize from MessagePack
    try:
        blueprint_dict = msgpack.unpackb(payload, raw=False)
    except Exception as e:
        raise HLXCodecError(f"Failed to deserialize blueprint: {e}")
    
    return blueprint_dict


def is_hlx_file(data: bytes) -> bool:
    """Check if data is an HLX file (v1 or v2 format)"""
    return data[:4] == MAGIC_HEADER or is_hlx_v2(data)


# =============================================================================
# V2 FORMAT (Cross-Platform - JPEG + Encrypted Data)
# =============================================================================

def is_hlx_v2(data: bytes) -> bool:
    """Check if data is a v2 HLX file (JPEG with embedded HELIX data)"""
    # v2 files are valid JPEGs with our marker appended
    # JPEG files start with 0xFFD8
    if len(data) < 20:
        return False
    
    is_jpeg = data[:2] == b'\xff\xd8'
    has_marker = HELIX_MARKER in data
    
    return is_jpeg and has_marker


def encode_v2(blueprint_dict: Dict[str, Any], preview_image: bytes) -> bytes:
    """
    📱 CROSS-PLATFORM: Encode blueprint with embedded JPEG preview.
    
    The resulting .hlx file is ALSO a valid JPEG!
    - Any app (Photos, Gallery, Preview) sees the preview image
    - HELIX-aware apps unlock the full blueprint for 4K/8K materialization
    
    Args:
        blueprint_dict: Blueprint as dictionary
        preview_image: JPEG bytes of preview image (1080p recommended)
        
    Returns:
        .hlx file that is ALSO a valid JPEG
        
    Technical trick:
        Most image viewers stop reading at JPEG EOI marker (0xFFD9).
        We append our data AFTER the complete JPEG, so it's invisible to
        standard viewers but accessible to HELIX.
    """
    # 1. Verify preview is valid JPEG
    if not preview_image.startswith(b'\xff\xd8'):
        raise ValueError("Preview must be JPEG format (starts with 0xFFD8)")
    
    # Ensure JPEG ends properly (should have EOI marker 0xFFD9)
    # Note: Some JPEGs have data after EOI, that's fine
    
    # 2. Encrypt the blueprint (reuse v1 encryption logic)
    encrypted_blueprint = _encrypt_blueprint(blueprint_dict)
    
    # 3. Build our payload section
    # Format: MARKER | SIZE (4 bytes) | ENCRYPTED_DATA
    payload_size = struct.pack(">I", len(encrypted_blueprint))
    helix_section = HELIX_MARKER + payload_size + encrypted_blueprint
    
    # 4. Append to preview image
    # The result is: VALID_JPEG + HELIX_MARKER + SIZE + ENCRYPTED_DATA
    hlx_data = preview_image + helix_section
    
    print(f"[HLX v2] Created cross-platform file: {len(preview_image)} preview + {len(helix_section)} data")
    
    return hlx_data


def decode_v2(hlx_data: bytes) -> Tuple[Dict[str, Any], bytes]:
    """
    Decode v2 .hlx file, extracting both blueprint and preview.
    
    Args:
        hlx_data: v2 HLX file data (JPEG + HELIX section)
        
    Returns:
        Tuple of (blueprint_dict, preview_jpeg_bytes)
        
    Raises:
        HLXCodecError: If format is invalid
        HLXTamperingError: If blueprint data is tampered
    """
    # Find HELIX marker
    marker_pos = hlx_data.find(HELIX_MARKER)
    
    if marker_pos == -1:
        raise HLXCodecError("Not a v2 HLX file: HELIX marker not found")
    
    # Extract preview (everything before marker)
    preview_image = hlx_data[:marker_pos]
    
    # Extract payload size
    size_start = marker_pos + len(HELIX_MARKER)
    payload_size = struct.unpack(">I", hlx_data[size_start:size_start+4])[0]
    
    # Extract encrypted blueprint
    data_start = size_start + 4
    encrypted_blueprint = hlx_data[data_start:data_start + payload_size]
    
    # Decrypt blueprint
    blueprint_dict = _decrypt_blueprint(encrypted_blueprint)
    
    print(f"[HLX v2] Decoded: {len(preview_image)} preview + {payload_size} blueprint data")
    
    return blueprint_dict, preview_image


def extract_preview(hlx_data: bytes) -> bytes:
    """
    📱 Extract JUST the preview image (for quick display without decryption).
    
    This is what non-HELIX apps will see when opening the file.
    Useful for generating thumbnails quickly.
    
    Args:
        hlx_data: HLX file data (must be v2 format)
        
    Returns:
        JPEG bytes of the preview image
        
    Raises:
        HLXCodecError: If not a v2 file
    """
    if not is_hlx_v2(hlx_data):
        raise HLXCodecError("Cannot extract preview: Not a v2 HLX file (no embedded preview)")
    
    marker_pos = hlx_data.find(HELIX_MARKER)
    return hlx_data[:marker_pos]


def get_format_version(hlx_data: bytes) -> int:
    """
    Detect the format version of an HLX file.
    
    Returns:
        1 for v1 (encrypted binary)
        2 for v2 (JPEG + encrypted data)
        0 for unknown/invalid
    """
    if is_hlx_v2(hlx_data):
        return 2
    elif hlx_data[:4] == MAGIC_HEADER:
        return 1
    else:
        return 0


# =============================================================================
# INTERNAL ENCRYPTION HELPERS
# =============================================================================

def _encrypt_blueprint(blueprint_dict: Dict[str, Any]) -> bytes:
    """Internal: Encrypt blueprint to bytes (used by both v1 and v2)"""
    # Serialize to MessagePack
    payload = msgpack.packb(blueprint_dict, use_bin_type=True)
    
    # Encrypt with AES-256-GCM
    nonce = os.urandom(16)
    aesgcm = AESGCM(_KEY)
    encrypted = aesgcm.encrypt(nonce, payload, None)
    
    # Build signed package: nonce + encrypted_with_tag
    auth_tag = encrypted[-16:]
    ciphertext = encrypted[:-16]
    
    # Create signature
    to_sign = nonce + auth_tag
    signature = hmac.new(_HMAC_KEY, to_sign, hashlib.sha256).digest()
    
    # Package: signature (32) + nonce (16) + tag (16) + ciphertext
    return signature + nonce + auth_tag + ciphertext


def _decrypt_blueprint(encrypted_data: bytes) -> Dict[str, Any]:
    """Internal: Decrypt blueprint from bytes (used by both v1 and v2)"""
    if len(encrypted_data) < 64:  # 32 + 16 + 16 minimum
        raise HLXCodecError("Encrypted data too small")
    
    # Extract components
    signature = encrypted_data[:32]
    nonce = encrypted_data[32:48]
    auth_tag = encrypted_data[48:64]
    ciphertext = encrypted_data[64:]
    
    # Verify signature
    to_verify = nonce + auth_tag
    expected_sig = hmac.new(_HMAC_KEY, to_verify, hashlib.sha256).digest()
    
    if not hmac.compare_digest(signature, expected_sig):
        raise HLXTamperingError("❌ HELIX Security: Blueprint tampering detected!")
    
    # Decrypt
    try:
        aesgcm = AESGCM(_KEY)
        encrypted_with_tag = ciphertext + auth_tag
        payload = aesgcm.decrypt(nonce, encrypted_with_tag, None)
    except Exception as e:
        raise HLXTamperingError(f"❌ HELIX Security: Decryption failed. {e}")
    
    # Deserialize
    try:
        return msgpack.unpackb(payload, raw=False)
    except Exception as e:
        raise HLXCodecError(f"Failed to deserialize blueprint: {e}")

