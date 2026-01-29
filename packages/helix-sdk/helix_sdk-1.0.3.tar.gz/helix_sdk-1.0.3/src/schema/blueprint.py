from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import json
import hashlib

@dataclass
class Metadata:
    """Metadata for the original asset"""
    identity: str = field(default_factory=lambda: __import__('secrets').token_urlsafe(19)[:26])  # 26-char unique ID
    modality: str = "image"  # image | audio | text (per spec Section 6)
    asset_type: str = "image"
    original_dims: tuple = (0, 0)
    checksum: str = ""
    aura: str = ""  # Mood/style description for reconstruction
    color_palette: List[str] = field(default_factory=list)  # Dominant colors
    scene_description: str = ""  # Overall scene context
    body_geometry: Dict[str, Any] = field(default_factory=dict)  # Pose/body info
    original_size_bytes: int = 0  # True original size for honest comparison
    compressed_size_bytes: int = 0  # HLX file size for honest comparison
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())  # ISO 8601 per spec
    duration: float = 0.0 # Video/Audio duration in seconds
    fps: float = 0.0      # Video frames per second
    frame_count: int = 0  # Video total frames

@dataclass
class Anchor:
    """
    Identity anchor - a region that cannot be hallucinated without loss of meaning.
    Stores actual pixel crops for critical elements.
    Per spec Section 4.3: Never invent or hallucinate anchors.
    """
    id: str
    type: str  # 'face', 'left_eye', 'right_eye', 'nose', 'mouth', 'text', 'logo', 'object', 'spectral_slice'
    bbox: Optional[tuple] = None  # (top, right, bottom, left) - For Images
    timestamp_start: Optional[float] = None  # Seconds (start) - For Audio/Video
    timestamp_end: Optional[float] = None    # Seconds (end) - For Audio/Video
    data: Optional[str] = None  # Base64 encoded pixel crop OR audio snippet
    content_hash: str = ""  # SHA-256 hash of data
    semantic_label: Optional[str] = None
    confidence: float = 0.0
    resolution_hint: str = "standard"  # 'high' | 'standard' | 'low'
    parent_anchor_id: Optional[str] = None  # For hierarchical anchors (face→eye)
    
    def compute_hash(self) -> str:
        """Compute SHA-256 hash of anchor pixel data"""
        if self.data:
            return hashlib.sha256(self.data.encode()).hexdigest()
        return ""

@dataclass
class Mesh:
    """
    Structural mesh encoding geometric relationships between anchors.
    Prevents AI from warping proportions during reconstruction.
    """
    # Normalized global centroid (x, y) where 0.0-1.0
    centroid: Optional[Tuple[float, float]] = None
    # Map of anchor_id -> {distance_to_centroid, angle, aspect_ratio}
    constraints: Dict[str, Dict[str, float]] = field(default_factory=dict)
    # Adjacency graph for spatial relationships
    adjacency: List[Any] = field(default_factory=list)
    # Facial landmark triangulation (for face anchors)
    facial_ratios: Dict[str, float] = field(default_factory=dict)

@dataclass
class HelixBlueprint:
    """
    The DNA Blueprint (.hlx) - compact representation for image reconstruction.
    Contains identity anchors, structural mesh, and reconstruction hints.
    Per spec Section 2.2: .hlx stores instructions for regeneration, not content.
    """
    metadata: Metadata
    anchors: List[Anchor]
    mesh: Mesh = field(default_factory=Mesh)
    # Constraints per spec Section 4.5
    constraints: Dict[str, List[str]] = field(default_factory=lambda: {"hard": [], "soft": []})
    # Freedom fields per spec Section 4.6
    freedom: Dict[str, Any] = field(default_factory=dict)
    masks: List[Any] = field(default_factory=list)
    version: str = "3.0"  # Updated for spec compliance

    def to_json(self) -> str:
        """Legacy JSON export (for debugging only)"""
        return json.dumps(asdict(self), indent=2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HelixBlueprint':
        """Reconstruct blueprint from dictionary"""
        # Reconstruct objects from dicts
        meta_data = data.get('metadata', {})
        # Handle tuple conversion for original_dims
        if 'original_dims' in meta_data and isinstance(meta_data['original_dims'], list):
            meta_data['original_dims'] = tuple(meta_data['original_dims'])
        meta = Metadata(**meta_data)
        
        # Convert anchor bbox tuples
        raw_anchors = data.get('anchors', [])
        anchors = []
        for a in raw_anchors:
            if 'bbox' in a and a['bbox'] is not None and isinstance(a['bbox'], list):
                a['bbox'] = tuple(a['bbox'])
            # Ensure safe defaults if keys missing (though dataclass handles defaults, dict plumbing might not)
            anchors.append(Anchor(**a))
        
        mesh_data = data.get('mesh', {})
        if 'centroid' in mesh_data and isinstance(mesh_data['centroid'], list):
            mesh_data['centroid'] = tuple(mesh_data['centroid'])
        mesh = Mesh(**mesh_data)
        
        return cls(
            metadata=meta,
            anchors=anchors,
            mesh=mesh,
            constraints=data.get('constraints', {"hard": [], "soft": []}),
            freedom=data.get('freedom', {}),
            masks=data.get('masks', []),
            version=data.get('version', "3.0")
        )

    @classmethod
    def from_json(cls, json_str: str) -> 'HelixBlueprint':
        """Legacy JSON import (for debugging only)"""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def save(self, path: str):
        """
        Save blueprint to encrypted .hlx file.
        Only HELIX can read/write this format.
        """
        from ..core.hlx_codec import encode
        hlx_data = encode(self.to_dict())
        with open(path, 'wb') as f:
            f.write(hlx_data)

    @classmethod
    def load(cls, path: str) -> 'HelixBlueprint':
        """
        Load blueprint from encrypted .hlx file.
        Raises HLXTamperingError if file has been modified.
        """
        from ..core.hlx_codec import decode, is_hlx_file, HLXCodecError
        
        with open(path, 'rb') as f:
            data = f.read()
        
        # Check if it's the new encrypted format or legacy JSON
        if is_hlx_file(data):
            blueprint_dict = decode(data)
            return cls.from_dict(blueprint_dict)
        else:
            # Legacy JSON fallback (for old .hlx files)
            print("⚠️  Warning: Loading legacy unencrypted .hlx file")
            return cls.from_json(data.decode('utf-8'))

    def get_anchor_count_by_type(self) -> Dict[str, int]:
        """Get counts of each anchor type"""
        counts = {}
        for anchor in self.anchors:
            counts[anchor.type] = counts.get(anchor.type, 0) + 1
        return counts

    def get_face_anchors(self) -> List[Anchor]:
        """Get all face-related anchors"""
        face_types = ['face', 'left_eye', 'right_eye', 'nose', 'mouth', 'face_outline']
        return [a for a in self.anchors if a.type in face_types]

    def get_high_priority_anchors(self) -> List[Anchor]:
        """Get anchors marked as high resolution"""
        return [a for a in self.anchors if a.resolution_hint == 'high']
