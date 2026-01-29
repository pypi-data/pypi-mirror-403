"""
HELIX Text Anchor Extractor
===========================
Extracts semantic identity anchors from text using Gemini.

Anchors include:
- Key entities (names, places, dates)
- Critical phrases (quotes, technical terms)
- Structural markers (sections, tone shifts)
- Style fingerprint (formality, voice, sentiment)
"""

import os
import json
import hashlib
from typing import List, Dict, Any, Tuple
from ..schema.blueprint import Anchor, Metadata, Mesh, HelixBlueprint

class TextAnchorExtractor:
    """
    Extracts semantic anchors from text content using Gemini.
    These anchors represent the "identity" that cannot be hallucinated.
    """
    
    EXTRACTION_PROMPT = """
You are the HELIX Text Identity Extraction Engine. Extract the CRITICAL semantic anchors from this text.

## EXTRACTION RULES:
1. ENTITIES are highest priority - exact names, dates, numbers CANNOT be guessed
2. QUOTES must be preserved exactly
3. STRUCTURE matters - section boundaries, tone shifts
4. Capture STYLE - formality level, voice, sentiment

## REQUIRED OUTPUT (JSON only):
{
    "anchors": [
        {"type": "entity", "content": "exact entity text", "label": "person|place|org|date|number", "position": 0},
        {"type": "quote", "content": "exact quoted text", "speaker": "who said it", "position": 50},
        {"type": "keyphrase", "content": "critical term or phrase", "importance": "high|medium", "position": 100},
        {"type": "structure", "label": "intro|body|conclusion|list|heading", "position": 0, "length": 50}
    ],
    "style": {
        "formality": "formal|neutral|casual",
        "tone": "informative|persuasive|narrative|technical",
        "voice": "first_person|third_person|passive",
        "sentiment": "positive|neutral|negative"
    },
    "summary": "1-2 sentence semantic summary of the content",
    "word_count": 500,
    "structure_type": "article|email|story|documentation|conversation"
}

## CRITICAL:
- Position is approximate character offset
- Include ALL named entities precisely
- Quotes must be EXACT - no paraphrasing
- Return ONLY valid JSON, no markdown blocks
"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = None
        self.model_name = None
        
        if self.api_key:
            self._initialize_client()
        else:
            print("⚠️  No GEMINI_API_KEY. TextAnchorExtractor disabled.")

    def _initialize_client(self):
        from google import genai
        self.client = genai.Client(api_key=self.api_key)
        
        model_cascade = [
            ('gemini-3-flash-preview', 'Gemini 3 Flash Preview'),
            ('gemini-3-pro-preview', 'Gemini 3 Pro Preview'),
            ('gemini-2.0-flash-exp', 'Gemini 2.0 Flash Exp'),
        ]
        
        # Default to first one
        self.model_name = model_cascade[0][0]
        print(f"✅ Text Extractor: {model_cascade[0][1]}")

    def extract(self, text: str) -> HelixBlueprint:
        """
        Extract anchors from text and return a HelixBlueprint.
        
        Args:
            text: The input text to compress
            
        Returns:
            HelixBlueprint with text anchors
        """
        if not self.client:
            raise RuntimeError("Text extraction requires GEMINI_API_KEY")
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[self.EXTRACTION_PROMPT, f"\n\nTEXT TO ANALYZE:\n{text}"],
                config={
                    'temperature': 0.1,
                    'max_output_tokens': 4096,
                }
            )
            
            result_text = response.text.strip()
            
            # Clean JSON
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            data = json.loads(result_text)
            
            # Build anchors
            anchors = self._process_anchors(data.get("anchors", []), text)
            
            # Build metadata
            style = data.get("style", {})
            metadata = Metadata(
                modality="text",
                asset_type="text",
                original_dims=(len(text), data.get("word_count", 0)),  # (char_count, word_count)
                checksum=hashlib.md5(text.encode()).hexdigest(),
                aura=f"{style.get('tone', 'neutral')} {style.get('formality', 'neutral')}",
                scene_description=data.get("summary", ""),
                body_geometry={
                    "style": style,
                    "structure_type": data.get("structure_type", "article")
                }
            )
            
            # Build simple mesh (no geometric constraints for text)
            mesh = Mesh()
            
            blueprint = HelixBlueprint(
                metadata=metadata,
                anchors=anchors,
                mesh=mesh,
                constraints={"hard": ["preserve_entities", "preserve_quotes"], "soft": ["maintain_tone"]},
                freedom={"paraphrase": "non_anchor_sections", "length": "within_20_percent"},
                version="3.0"
            )
            
            print(f"📝 Extracted {len(anchors)} text anchors via {self.model_name}")
            return blueprint
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse error: {e}")
            raise
        except Exception as e:
            print(f"❌ Text extraction failed: {e}")
            raise

    def _process_anchors(self, raw_anchors: List[Dict], original_text: str) -> List[Anchor]:
        """Convert raw anchor data to Anchor objects"""
        anchors = []
        
        for idx, item in enumerate(raw_anchors):
            anchor_type = item.get("type", "keyphrase")
            content = item.get("content", "")
            position = item.get("position", 0)
            
            # Compute content hash
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            # For text, bbox represents (start_pos, end_pos, 0, 0)
            end_pos = position + len(content)
            
            anchor = Anchor(
                id=f"{anchor_type}_{idx}_{position}",
                type=anchor_type,
                bbox=(position, end_pos, 0, 0),  # (start, end, unused, unused)
                data=content,  # Store actual text, not base64 for text modality
                content_hash=content_hash,
                semantic_label=item.get("label", anchor_type),
                confidence=0.95 if anchor_type in ["entity", "quote"] else 0.85,
                resolution_hint="high" if anchor_type in ["entity", "quote"] else "standard"
            )
            anchors.append(anchor)
        
        return anchors
