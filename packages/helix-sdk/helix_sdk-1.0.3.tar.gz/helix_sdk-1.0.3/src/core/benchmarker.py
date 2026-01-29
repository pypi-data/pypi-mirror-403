import os
from typing import List
from ..schema.blueprint import HelixBlueprint
from ..core.materializer import GeminiMaterializer

class AblationBenchmarker:
    """
    Handles Phase 4: Controlled Benchmarking Tools.
    
    Generates scientific test sets for Model Ablation Studies.
    Ensures 'ceteris paribus' (all else equal) by locking the Helix Blueprint's
    Identity and Geometry anchors, while systematically varying strictly ONE variable.
    """
    
    PRESETS = {
        "lighting": ["Natural Light", "Studio Lighting", "Hard Shadows", "Soft Diffuse", "Neon Backlight"],
        "weather": ["Clear Sunny", "Overcast", "Heavy Rain", "Snowstorm", "Foggy"],
        "camera": ["Wide Angle", "Telephoto", "Macro", "Fish Eye", "Bokeh"],
        "time": ["Dawn", "Noon", "Dusk", "Midnight"]
    }
    
    def run_sweep(self, blueprint: HelixBlueprint, variable: str, values: List[str] = None, output_dir: str = "./benchmark_output"):
        """
        Runs a single-variable parameter sweep.
        """
        if not values:
            if variable in self.PRESETS:
                values = self.PRESETS[variable]
            else:
                raise ValueError(f"Unknown variable '{variable}' and no values provided.")
                
        materializer = GeminiMaterializer()
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"📊 Starting Benchmark Sweep for '{variable}' ({len(values)} steps)...")
        
        for val in values:
            print(f"  - Step: {val}")
            
            # Save state
            original_aura = blueprint.metadata.aura
            original_desc = blueprint.metadata.scene_description
            
            # Inject Variable
            # We use a specific scientific phrasing to encourage the model to focus on the constraint
            blueprint.metadata.aura = f"{val} ({variable} test)"
            blueprint.metadata.scene_description = f"{original_desc}. {variable.upper()} CONDITION: {val}."
            
            try:
                image_data = materializer.materialize(blueprint)
                
                # Naming convention: {variable}_{value}.png
                safe_val = val.replace(" ", "_").lower()
                filename = f"sweep_{variable}_{safe_val}.png"
                
                with open(os.path.join(output_dir, filename), 'wb') as f:
                    f.write(image_data)
                    
            except Exception as e:
                print(f"    Failed step {val}: {e}")
                
            # Restore state
            blueprint.metadata.aura = original_aura
            blueprint.metadata.scene_description = original_desc
            
        print("✅ Sweep Complete.")
