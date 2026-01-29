from typing import List
from ..schema.blueprint import HelixBlueprint
from ..core.materializer import GeminiMaterializer

class DomainAdapter:
    """
    Handles Phase 4: Domain Transfer.
    
    Facilitates bulk conversion of datasets between semantic domains.
    Common Use Cases:
    - Sim-to-Real: Convert gameplay/synthetic data to photorealistic.
    - Day-to-Night: Re-relight scenes for autonomy training.
    - Sketch-to-Image: Convert wireframes to product mockups.
    """
    
    DOMAINS = {
        "sim_to_real": "Photorealistic, 8k, Unreal Engine 5 render, highly detailed",
        "day_to_night": "Nighttime, dark environment, streetlights, high ISO, noise",
        "real_to_sim": "Video game graphic style, low poly, GTA V style, simulated",
        "sketch": "Pencil sketch, architectural drawing, monochromatic",
        "thermal": "Thermal infrared camera, heat map signature, military imaging",
        "snow": "Heavy snowstorm, whiteout, winter conditions, frozen"
    }
    
    def adapt_dataset(self, blueprints: List[HelixBlueprint], target_domain: str) -> List[HelixBlueprint]:
        """
        Adapts a list of Blueprints to a target domain WITHOUT materializing immediately.
        Returns modified blueprints ready for processing.
        """
        if target_domain not in self.DOMAINS:
            # Allow custom string if not in preset
            domain_prompt = target_domain
        else:
            domain_prompt = self.DOMAINS[target_domain]
            
        adapted_blueprints = []
        
        for bp in blueprints:
            # We clone/modify the blueprint to exist in the new domain
            # Ideally we deepcopy, but here we assume single-pass usage
            
            # The 'Aura' is the soul of the image style.
            bp.metadata.aura = f"{domain_prompt} (Domain Transferred)"
            
            # We append the constraint to the scene description
            bp.metadata.scene_description = f"{bp.metadata.scene_description}. Render style: {domain_prompt}."
            
            adapted_blueprints.append(bp)
            
        return adapted_blueprints

    def materialize_domain_transfer(self, blueprint: HelixBlueprint, target_domain: str, output_path: str):
        """
        Immediate materialization helper for single assets.
        """
        materializer = GeminiMaterializer()
        
        # Apply domain
        if target_domain in self.DOMAINS:
            domain_prompt = self.DOMAINS[target_domain]
        else:
            domain_prompt = target_domain
            
        blueprint.metadata.aura = f"{domain_prompt}"
        blueprint.metadata.scene_description = f"{blueprint.metadata.scene_description}. Style: {domain_prompt}."
        
        # Generate
        image_data = materializer.materialize(blueprint)
        
        with open(output_path, 'wb') as f:
            f.write(image_data)
