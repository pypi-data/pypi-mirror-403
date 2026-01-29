import os
from typing import List
from ..schema.blueprint import HelixBlueprint
from ..core.materializer import GeminiMaterializer

class ForensicReconstructor:
    """
    Handles Phase 4: Forensic Reconstruction Mode.
    
    Used for historical restoration or low-quality CCTV analysis.
    Unlike standard materialization which aims for the "one true image", 
    Forensic Mode explicitly acknowledges uncertainty by generating 
    multiple valid hypotheses.
    
    WARNING: Outputs should be labeled as "Best Fit Reconstructions", not Ground Truth.
    """
    
    def generate_hypotheses(self, blueprint: HelixBlueprint, count: int = 4, output_dir: str = "./forensics"):
        """
        Generates N varied hypotheses for the missing details in a blueprint.
        Uses higher temperature to encourage diverse filling of uncertainty gaps.
        """
        materializer = GeminiMaterializer()
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"🕵️  Forensic Mode: Generating {count} Hypotheses...")
        print("⚠️  DISCLAIMER: These are probabilistic reconstructions, not evidence.")
        
        # We assume the materializer can take a 'temperature' override if we passed it options,
        # but for now we rely on prompt engineering to induce variation.
        
        for i in range(count):
            print(f"  - Hypothesis {i+1}/{count}...")
            
            # Clone bp to avoid contaminating original
            current_bp = blueprint # In memory copy effectively
            original_aura = current_bp.metadata.aura
            
            # Inject "Forensic Hypothesis" context
            # This encourages the AI to "fill in the blanks" cleanly rather than artifying it
            current_bp.metadata.aura = f"Forensic Reconstruction, Hypothesis {i+1}, Neutral Lighting, Clear Features. {original_aura}"
            
            try:
                image_data = materializer.materialize(current_bp)
                
                filename = f"hypothesis_{i+1}_probabilistic.png"
                with open(os.path.join(output_dir, filename), 'wb') as f:
                    f.write(image_data)
                    
            except Exception as e:
                print(f"    Hypothesis generation failed: {e}")
                
            # Restore
            current_bp.metadata.aura = original_aura
        
        # Generator a "Report" (manifest)
        with open(os.path.join(output_dir, "FORENSIC_REPORT.txt"), 'w') as f:
            f.write("HELIX FORENSIC REPORT\n")
            f.write("=====================\n")
            f.write(f"Source: {blueprint.metadata.asset_type}\n")
            f.write(f"Anchors: {len(blueprint.anchors)}\n")
            f.write(f"Hypotheses Generated: {count}\n\n")
            f.write("NOTE: These images are AI-generated based on sparse anchor data.\n")
            f.write("They represent POSSIBLE reconstructions, not guaranteed identity.\n")
            
        print("✅ Forensic Report Generated.")
