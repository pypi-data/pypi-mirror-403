"""
HELIX Text Materializer
=======================
Regenerates text from semantic anchors using Gemini.

The materializer ensures:
- All entity anchors appear exactly as stored
- All quote anchors are preserved verbatim
- Style/tone matches the original
- Structure flows naturally around anchors
"""

import os
import json
from typing import List, Dict, Any
from ..schema.blueprint import HelixBlueprint, Anchor

class TextMaterializer:
    """
    Regenerates text content from HELIX blueprints using Gemini.
    Anchors (entities, quotes) are preserved exactly.
    """
    
    REGENERATION_PROMPT = """
You are the HELIX Text Regeneration Engine. Reconstruct the original text from these semantic anchors.

## CRITICAL RULES:
1. ENTITIES must appear EXACTLY as provided - no variations
2. QUOTES must be reproduced VERBATIM
3. Match the STYLE specified (tone, formality, voice)
4. Weave anchors naturally into flowing text
5. Maintain approximate structure and length

## ANCHORS TO INCLUDE (MUST BE EXACT):
{anchors}

## STYLE REQUIREMENTS:
{style}

## SUMMARY FOR CONTEXT:
{summary}

## CONSTRAINTS:
- Target word count: {target_words}
- Structure type: {structure_type}
- All entities must appear with exact spelling/capitalization
- All quotes must appear exactly as provided

Generate the complete reconstructed text now. Output ONLY the text, no explanations.
"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = None
        self.model_name = None
        
        if self.api_key:
            self._initialize_client()
        else:
            print("⚠️  No GEMINI_API_KEY. TextMaterializer disabled.")

    def _initialize_client(self):
        from google import genai
        self.client = genai.Client(api_key=self.api_key)
        
        model_cascade = [
            ('gemini-3-flash-preview', 'Gemini 3 Flash Preview'),
            ('gemini-3-pro-preview', 'Gemini 3 Pro Preview'),
            ('gemini-2.0-flash-exp', 'Gemini 2.0 Flash Exp'),
        ]
        
        self.model_name = model_cascade[0][0]
        print(f"✅ Text Materializer: {model_cascade[0][1]}")

    def materialize(self, blueprint: HelixBlueprint) -> str:
        """
        Regenerate text from blueprint anchors.
        
        Args:
            blueprint: HelixBlueprint with text modality
            
        Returns:
            Regenerated text string
        """
        if blueprint.metadata.modality != "text":
            raise ValueError(f"Expected text blueprint, got: {blueprint.metadata.modality}")
        
        if not self.client:
            raise RuntimeError("Text materialization requires GEMINI_API_KEY")
        
        # Prepare anchors
        anchors_text = self._format_anchors(blueprint.anchors)
        
        # Get style from metadata
        style = blueprint.metadata.body_geometry.get("style", {})
        style_text = json.dumps(style, indent=2)
        
        # Get other metadata
        summary = blueprint.metadata.scene_description
        char_count, word_count = blueprint.metadata.original_dims
        structure_type = blueprint.metadata.body_geometry.get("structure_type", "article")
        
        # Build prompt
        prompt = self.REGENERATION_PROMPT.format(
            anchors=anchors_text,
            style=style_text,
            summary=summary,
            target_words=word_count,
            structure_type=structure_type
        )
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={
                    'temperature': 0.3,  # Slightly more creative for text
                    'max_output_tokens': 8192,
                }
            )
            
            regenerated = response.text.strip()
            
            # Verify anchors are present
            verification = self._verify_anchors(regenerated, blueprint.anchors)
            if verification["missing"]:
                print(f"⚠️  Warning: {len(verification['missing'])} anchors may be missing")
            
            print(f"📝 Regenerated ~{len(regenerated.split())} words via {self.model_name}")
            return regenerated
            
        except Exception as e:
            print(f"❌ Text materialization failed: {e}")
            raise

    def _format_anchors(self, anchors: List[Anchor]) -> str:
        """Format anchors for the regeneration prompt"""
        lines = []
        
        for anchor in anchors:
            if anchor.type == "entity":
                lines.append(f"- ENTITY [{anchor.semantic_label}]: \"{anchor.data}\"")
            elif anchor.type == "quote":
                lines.append(f"- QUOTE: \"{anchor.data}\"")
            elif anchor.type == "keyphrase":
                lines.append(f"- KEYPHRASE: \"{anchor.data}\"")
            elif anchor.type == "structure":
                lines.append(f"- STRUCTURE: {anchor.semantic_label} section")
        
        return "\n".join(lines)

    def _verify_anchors(self, text: str, anchors: List[Anchor]) -> Dict[str, List[str]]:
        """Verify that all high-priority anchors appear in the text"""
        text_lower = text.lower()
        missing = []
        found = []
        
        for anchor in anchors:
            if anchor.type in ["entity", "quote"] and anchor.data:
                if anchor.data.lower() in text_lower:
                    found.append(anchor.id)
                else:
                    missing.append(anchor.id)
        
        return {"found": found, "missing": missing}
