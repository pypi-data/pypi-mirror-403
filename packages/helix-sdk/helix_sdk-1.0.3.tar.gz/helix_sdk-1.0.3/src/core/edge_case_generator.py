import os
from typing import List
from ..schema.blueprint import HelixBlueprint
from ..core.materializer import GeminiMaterializer

class EdgeCaseGenerator:
    """
    Handles Phase 3: Synthetic Edge Case Generation.
    
    Automates the creation of "Disaster" and "Corner Case" datasets for ML robustness checking.
    Leverages Helix's "Remix" capability to inject specific degradation contexts.
    """
    
    ADVERSARIAL_CONTEXTS = [
        "Extreme Low Light, Underexposed, Noisy",
        "Blinding Lens Flare, Overexposed, Washed Out",
        "Heavy Rain, Water Droplets on Lens, Blur",
        "Thick Fog, Low Contrast, Hazy",
        "Motion Blur, Shaking Camera, Unfocused",
        "Pixelated, Compression Artifacts, JPEG",
        "Partially Occluded by dust",
        "Snowstorm, Whiteout conditions"
    ]
    
    def generate_robustness_suite(self, blueprint: HelixBlueprint, output_dir: str):
        """
        Generates a full suite of edge cases for a given blueprint.
        """
        materializer = GeminiMaterializer()
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        print(f"⚠️  Generating {len(self.ADVERSARIAL_CONTEXTS)} Edge Cases using HELIX...")
        
        for i, context in enumerate(self.ADVERSARIAL_CONTEXTS):
            print(f"  - Injecting Failure Mode: {context}")
            
            # Temporary Metadata Injection
            original_aura = blueprint.metadata.aura
            original_desc = blueprint.metadata.scene_description
            
            blueprint.metadata.aura = f"{context} (Edge Case {i})"
            blueprint.metadata.scene_description = f"{original_desc}. CONDITION: {context}"
            
            # Materialize
            try:
                # Assuming prompt-based manipulation works via the materializer's internal prompting
                image_data = materializer.materialize(blueprint)
                
                # Save
                filename = f"robustness_{i}_{context.split(',')[0].replace(' ', '_')}.png"
                with open(os.path.join(output_dir, filename), 'wb') as f:
                    f.write(image_data)
                    
            except Exception as e:
                print(f"    Failed to generate edge case {context}: {e}")
                
            # Restore Metadata (Critical!)
            blueprint.metadata.aura = original_aura
            blueprint.metadata.scene_description = original_desc
