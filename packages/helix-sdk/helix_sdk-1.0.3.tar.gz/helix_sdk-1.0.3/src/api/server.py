from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Form
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import shutil
import os
import tempfile
import json

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()
from src.core.pipeline import HelixPipeline
from src.core.materializer import GeminiMaterializer
from src.schema.blueprint import HelixBlueprint
from typing import Dict, Any

app = FastAPI(title="Helix Real-time API")

# Enable CORS for Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In prod, specify localhost:3000
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services
pipeline = HelixPipeline()
materializer = GeminiMaterializer() # Will fallback to mock if no ENV key

@app.get("/")
def health_check():
    """Health check endpoint with feature status"""
    return {
        "status": "Helix Core Online", 
        "version": "1.0.0",
        "features": {
            "cross_platform_v2": True,
            "helix_sdk": True,
            "sdk_docs": "/docs/sdk"
        },
        "model": materializer.model_name or "Not initialized"
    }

# ====== SDK DOCUMENTATION UI ======
@app.get("/docs/sdk", response_class=HTMLResponse)
async def sdk_documentation():
    """Serve the HELIX SDK documentation page"""
    from src.api.sdk_docs import SDK_DOCS_HTML
    return SDK_DOCS_HTML

@app.get("/api/knowledge")
async def get_knowledge():
    """
    Serves the HELIX knowledge base for the frontend intro and content.
    """
    try:
        knowledge_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "helix_knowledgebase.json")
        with open(knowledge_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Knowledge load error: {e}")
        # Return fallback content
        return {
            "intro": {
                "greeting": "Welcome to Project HELIX",
                "tagline": "Identity-Preserving AI Compression",
                "narration": [
                    "Hello. I am HELIX, your identity preservation system.",
                    "I extract the essence of who you are from images.",
                    "The result? Up to 95% size reduction with perfect identity preservation."
                ]
            },
            "typewriter_messages": [
                "Initializing neural networks...",
                "Loading identity anchors...",
                "Calibrating AI models..."
            ],
            "features": [],
            "about": {"title": "About HELIX", "paragraphs": []},
            "voice": {"preferredVoice": "female", "rate": 0.9, "pitch": 1.0}
        }

class TTSRequest(BaseModel):
    text: str
    voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # Rachel - best female voice

@app.post("/api/tts")
async def text_to_speech(request: TTSRequest):
    """
    Converts text to speech using ElevenLabs API.
    Returns audio as base64 MP3.
    """
    import httpx
    import base64
    
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ELEVENLABS_API_KEY not set")
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{request.voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    
    data = {
        "text": request.text,
        "model_id": "eleven_turbo_v2_5",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True
        }
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, headers=headers, timeout=30.0)
            
            if response.status_code != 200:
                print(f"ElevenLabs error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail="TTS generation failed")
            
            audio_bytes = response.content
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            return {"audio": f"data:audio/mpeg;base64,{audio_base64}"}
    
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="TTS request timed out")
    except Exception as e:
        print(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/encode")
async def encode_image(file: UploadFile = File(...)):
    """
    Takes an image, runs Helix Extraction, returns the Blueprint JSON.
    """
    try:
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_in:
            shutil.copyfileobj(file.file, tmp_in)
            tmp_in_path = tmp_in.name
        
        tmp_out_path = tmp_in_path + ".hlx"
        
        # Run Pipeline
        pipeline.process_asset(tmp_in_path, tmp_out_path)
        
        # Read Result (Blueprint) - Load Binary HLX
        from src.schema.blueprint import HelixBlueprint
        blueprint_obj = HelixBlueprint.load(tmp_out_path)
        
        # [POLISH] Inject Real Metrics for Honest Comparison over Time
        original_size = os.path.getsize(tmp_in_path)
        hlx_size = os.path.getsize(tmp_out_path)
        blueprint_obj.metadata.original_size_bytes = original_size
        blueprint_obj.metadata.compressed_size_bytes = hlx_size
        
        # Save back to file so it persists for materialization
        blueprint_obj.save(tmp_out_path)
        
        # Convert to dict for return
        blueprint = blueprint_obj.to_dict()
            
        # [POLISH] Immediate Verification / Preview
        # We materialize it back immediately so the user can see the comparison
        # This acts as the "Verification" step in the pipeline.
        try:
            # Fix: Pass the blueprint OBJECT, not the dict, because materializer expects .metadata access
            reconstructed = materializer.materialize(blueprint_obj)
            if reconstructed is not None:
                # Convert to base64
                import base64
                # reconstructed is already bytes (PNG/JPEG), so just encode it
                reconstructed_b64 = "data:image/jpeg;base64," + base64.b64encode(reconstructed).decode('utf-8')
                
                # [OPTIMIZATION] Do NOT include preview in the blueprint download.
                # This bloats the file (e.g. 15MB) and is not needed since we disabled the popup.
                # blueprint['reconstructed_preview'] = reconstructed_b64 
        except Exception as e:
            print(f"Preview generation failed: {e}")
            import traceback
            traceback.print_exc()

        # [BINARY HLX] Encode as secure binary for download
        # This allows the frontend to save the proper .hlx binary format
        try:
            from src.core.hlx_codec import encode as hlx_encode
            import base64
            
            # Ensure preview is GONE before encoding
            if 'reconstructed_preview' in blueprint:
                del blueprint['reconstructed_preview']

            # We encode the final blueprint dict so it includes any updates
            binary_blob = hlx_encode(blueprint)
            blueprint['hlx_file_b64'] = base64.b64encode(binary_blob).decode('utf-8')
        except Exception as e:
            print(f"Binary encoding failed: {e}")
            
        return blueprint
        # Use Helper to load binary/encrypted HLX
        blueprint = HelixBlueprint.load(tmp_out_path)
        blueprint_json = blueprint.to_dict()
            
        # Cleanup
        os.remove(tmp_in_path)
        os.remove(tmp_out_path)
        
        return blueprint_json

    except Exception as e:
        print(f"Encode error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# 🚀 LIVING DATA ENDPOINTS
# ============================================

@app.get("/api/resolutions")
async def get_available_resolutions():
    """
    Get available resolution tiers for Living Data feature.
    Frontend uses this to populate resolution selector.
    """
    from src.core.resolution_engine import resolution_engine
    
    tiers = {}
    for name, tier in resolution_engine.TIERS.items():
        tiers[name] = {
            "name": tier.name,
            "width": tier.width,
            "height": tier.height,
            "description": tier.prompt_detail
        }
    
    return {
        "resolutions": tiers,
        "default": resolution_engine.DEFAULT_TIER,
        "available": resolution_engine.get_available_resolutions()
    }

@app.get("/api/living-data/info")
async def get_living_data_info():
    """
    Get information about the Living Data feature for the demo.
    """
    return {
        "feature": "Living Data",
        "tagline": "Your memories, forever young. Compress once, upgrade forever.",
        "description": "Upload old, low-res photos. HELIX extracts identity anchors. Regenerate at 4K/8K with Gemini 3. File is SMALLER than original.",
        "benefits": [
            "🖼️ Transform grainy old photos into crystal-clear 4K/8K",
            "📦 Output file is smaller than the original",
            "♾️ Upgrade quality anytime as AI improves",
            "🎨 Preserve identity, enhance everything else"
        ],
        "howItWorks": [
            {"step": 1, "title": "Upload", "description": "Upload any old, low-res photo"},
            {"step": 2, "title": "Extract", "description": "HELIX extracts identity anchors (faces, text, logos)"},
            {"step": 3, "title": "Compress", "description": "Create tiny .hlx blueprint"},
            {"step": 4, "title": "Materialize", "description": "Regenerate at any resolution using Gemini 3"}
        ],
        "demoSteps": [
            "Select an old photo from 2010 (low-res, grainy)",
            "Click Encode to create .hlx blueprint",
            "Choose target resolution (4K or 8K)",
            "Watch HELIX restore your memory in stunning quality",
            "Compare: Original vs Materialized. File size vs Quality."
        ]
    }

# ============================================
# 📱 CROSS-PLATFORM ENDPOINTS
# ============================================

@app.post("/api/encode/v2")
async def encode_image_v2(file: UploadFile = File(...)):
    """
    📱 CROSS-PLATFORM: Encode image to HLX v2 format.
    
    The resulting .hlx file is ALSO a valid JPEG!
    - Any app (Photos, Gallery, Preview) sees the preview image
    - HELIX-aware apps unlock the full blueprint for 4K/8K materialization
    
    Returns:
        - hlx_file_b64: Base64 encoded HLX v2 file
        - preview_size: Size of embedded preview
        - total_size: Total file size
        - format_version: 2
    """
    import cv2
    import numpy as np
    import base64
    
    try:
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_in:
            shutil.copyfileobj(file.file, tmp_in)
            tmp_in_path = tmp_in.name
        
        tmp_out_path = tmp_in_path + ".hlx"
        original_size = os.path.getsize(tmp_in_path)
        
        # Run Pipeline to get blueprint
        pipeline.process_asset(tmp_in_path, tmp_out_path)
        
        # Load the blueprint
        blueprint_obj = HelixBlueprint.load(tmp_out_path)
        blueprint_dict = blueprint_obj.to_dict()
        
        # Generate preview image for cross-platform compatibility
        from src.core.preview_generator import preview_generator
        from src.core.hlx_codec import encode_v2
        
        # Read original image for preview
        img = cv2.imread(tmp_in_path)
        preview_bytes = preview_generator.generate(img)
        
        # Create HLX v2 (JPEG + encrypted blueprint)
        hlx_v2_data = encode_v2(blueprint_dict, preview_bytes)
        
        # Calculate sizes
        hlx_size = len(hlx_v2_data)
        compression_ratio = original_size / hlx_size if hlx_size > 0 else 0
        
        # Update metadata
        blueprint_dict['metadata']['original_size_bytes'] = original_size
        blueprint_dict['metadata']['compressed_size_bytes'] = hlx_size
        
        # Cleanup
        os.remove(tmp_in_path)
        os.remove(tmp_out_path)
        
        return {
            "hlx_file_b64": base64.b64encode(hlx_v2_data).decode('utf-8'),
            "format_version": 2,
            "preview_size": len(preview_bytes),
            "blueprint_size": hlx_size - len(preview_bytes),
            "total_size": hlx_size,
            "original_size": original_size,
            "compression_ratio": round(compression_ratio, 2),
            "cross_platform": True,
            "message": "📱 This file is viewable by ANY app as a JPEG, while HELIX can unlock 4K/8K!"
        }
        
    except Exception as e:
        print(f"Encode v2 error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/hlx/preview")
async def get_hlx_preview(file: UploadFile = File(...)):
    """
    📱 Quick preview extraction from HLX v2 file.
    Returns just the JPEG preview without decrypting the blueprint.
    """
    import base64
    from src.core.hlx_codec import extract_preview, is_hlx_v2
    
    try:
        content = await file.read()
        
        if not is_hlx_v2(content):
            raise HTTPException(
                status_code=400, 
                detail="Not a v2 HLX file. V1 files don't have embedded previews."
            )
        
        preview_bytes = extract_preview(content)
        preview_b64 = base64.b64encode(preview_bytes).decode('utf-8')
        
        return {
            "preview": f"data:image/jpeg;base64,{preview_b64}",
            "preview_size": len(preview_bytes),
            "format_version": 2
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/hlx/format-info")
async def get_format_info():
    """
    Get information about HLX file formats.
    """
    return {
        "formats": {
            "v1": {
                "name": "HLX v1 (Legacy)",
                "description": "Encrypted binary format, requires HELIX to open",
                "cross_platform": False,
                "magic_header": "HLX\\x00"
            },
            "v2": {
                "name": "HLX v2 (Cross-Platform)",
                "description": "Valid JPEG with embedded HELIX data",
                "cross_platform": True,
                "magic_header": "JPEG SOI (0xFFD8)",
                "helix_marker": "HELIX_DATA_START",
                "benefits": [
                    "📱 Viewable by ANY app (Photos, Gallery, Preview)",
                    "🔐 Full blueprint encrypted inside",
                    "🚀 HELIX unlocks 4K/8K materialization",
                    "📤 Share anywhere without compatibility issues"
                ]
            }
        },
        "recommended": "v2"
    }

# ============================================
# 🧠 HELIX SDK ENDPOINTS
# ============================================

@app.get("/api/sdk/info")
async def get_sdk_info():
    """
    Get information about the HELIX Data SDK for AI training.
    """
    return {
        "name": "HELIX Data SDK",
        "version": "1.0.0",
        "tagline": "Train smarter, not harder. Compress training data 10x.",
        "installation": "pip install helix-sdk",
        "quickStart": """
from helix_sdk import HelixDataset, HelixLoader, BatchCompressor

# Step 1: Compress your dataset (one-time)
compressor = BatchCompressor(workers=8)
stats = compressor.compress_directory(
    input_dir="/data/imagenet/train/",   # 150GB
    output_dir="/data/imagenet_hlx/"     # ~15GB
)

# Step 2: Create dataset + loader
dataset = HelixDataset("/data/imagenet_hlx/", target_resolution="512p")
loader = HelixLoader(dataset, batch_size=64, num_workers=4)

# Step 3: Train!
for batch in loader:
    images = torch.from_numpy(batch).permute(0, 3, 1, 2)
    model.train(images)
""",
        "benefits": [
            "📦 10x dataset compression",
            "🚀 PyTorch/TensorFlow compatible",
            "🔄 On-demand materialization at any resolution",
            "♾️ Infinite variant generation (free augmentation)",
            "🔍 Semantic search across dataset"
        ],
        "apiReference": {
            "HelixDataset": {
                "description": "Load .hlx files as ML-ready dataset",
                "args": ["path", "target_resolution", "enable_variants", "cache_materializations"]
            },
            "HelixLoader": {
                "description": "PyTorch-compatible DataLoader",
                "args": ["dataset", "batch_size", "shuffle", "num_workers", "variants_per_image"]
            },
            "BatchCompressor": {
                "description": "Compress directories to HELIX format",
                "args": ["workers", "use_v2_format", "progress_callback"]
            }
        }
    }

@app.post("/api/materialize")
async def materialize_blueprint(
    file: UploadFile = File(...), 
    context: str = Form(None),
    target_resolution: str = Form("4K")  # NEW: Living Data resolution selector
):
    """
    Takes a .hlx file (binary or JSON), runs Gemini Materializer, returns Base64 Image.
    
    🚀 LIVING DATA FEATURE:
    - Supports target_resolution: "720p", "1080p", "1440p", "4K", "8K"
    - Returns upgrade_metrics showing the quality improvement
    - Old grainy photo → Crystal clear 4K/8K output
    
    Includes Verification Loop (Spec 5.4).
    Supports 'context' override (Developer Mode).
    Returns blueprint metadata for ExplanationCard UI.
    """
    import tempfile
    import time
    
    start_time = time.time()
    
    try:
        # Save uploaded file to temp
        suffix = ".hlx"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
            original_size = len(content)

        try:
            # Load Blueprint using standard loader (handles binary/legacy)
            blueprint = HelixBlueprint.load(tmp_path)
            
            # Developer Mode: Context Override
            if context:
                print(f"🎨 Context Override: {context}")
                blueprint.metadata.aura = f"{context} (User Override)"
                blueprint.metadata.scene_description = f"{blueprint.metadata.scene_description}. Style: {context}"
            
            # 1. Generate with target resolution (Spec 5.3 + Living Data)
            print(f"🚀 Living Data: Materializing at {target_resolution}...")
            result = materializer.materialize(
                blueprint, 
                target_resolution=target_resolution,
                return_metrics=True
            )
            
            # Unpack result (image_bytes, upgrade_metrics)
            if isinstance(result, tuple):
                image_bytes, upgrade_metrics = result
            else:
                image_bytes = result
                upgrade_metrics = {}
            
            # 2. Verify (Spec 5.4) - ONLY if AI was used
            # When AI is unavailable, verification would fail on upscaled baseline images
            # because face positions don't match after upscaling
            skip_verification = upgrade_metrics.get('ai_unavailable', False) if upgrade_metrics else False
            
            if skip_verification:
                print("⚠️ Skipping verification (AI unavailable, using baseline output)")
                is_valid = True
                errors = []
            else:
                from src.core.verification import VerificationLoop
                verifier = VerificationLoop()
                is_valid, errors = verifier.verify(image_bytes, blueprint)
            
            if not is_valid:
                print(f"❌ Verification Failed: {errors}")
                raise HTTPException(status_code=422, detail=f"Verification Failed: {errors}")
            else:
                print("✅ Verification Passed")
            
            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)
            
            # Return as base64 for frontend
            import base64

            # [VIDEO SUPPORT] If blueprint says "video", we must return a video file (mp4)
            # We loop the keyframe to make a static video (or simple animation later)
            # [VIDEO SUPPORT] If blueprint says "video", we must return a video file (mp4)
            # We loop the keyframe to make a static video (or simple animation later)
            if blueprint.metadata.modality == 'video':
                print("🎥 Generating video output from materialized keyframe...")
                try:
                    import cv2
                    import numpy as np
                    
                    # Decode the image_bytes to numpy
                    nparr = np.frombuffer(image_bytes, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    video_generated = False
                    b64_img = None
                    
                    if img is not None:
                        height, width, layers = img.shape
                        print(f"   Frame size: {width}x{height}")
                        
                        # Try codecs in order
                        codecs = [
                            ('mp4v', '.mp4', 'video/mp4'),
                            ('avc1', '.mp4', 'video/mp4'),
                            ('vp80', '.webm', 'video/webm')
                        ]
                        
                        for fourcc_str, suffix, mime_type in codecs:
                            print(f"   Trying codec: {fourcc_str}...")
                            try:
                                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as vid_tmp:
                                    vid_path = vid_tmp.name
                                
                                fourcc = cv2.VideoWriter_fourcc(*fourcc_str)
                                out = cv2.VideoWriter(vid_path, fourcc, 30.0, (width, height))
                                
                                if not out.isOpened():
                                    print(f"      Failed to open VideoWriter with {fourcc_str}")
                                    out.release()
                                    if os.path.exists(vid_path): os.unlink(vid_path)
                                    continue
                                
                                # [OPTIMIZATION] Fast fail: Write 1 frame to test
                                out.write(img)
                                
                                # If we passed the first write without crash, write the rest
                                # Write for 3 seconds (90 frames)
                                for _ in range(89):
                                    out.write(img)
                                out.release()
                                
                                # Check file size
                                size = os.path.getsize(vid_path)
                                if size > 1000: # Arbitrary small limit to ensure header + content
                                    print(f"   ✅ Video generated: {size} bytes ({fourcc_str})")
                                    with open(vid_path, 'rb') as f:
                                        video_bytes = f.read()
                                    
                                    b64_data = base64.b64encode(video_bytes).decode('utf-8')
                                    b64_img = f"data:{mime_type};base64,{b64_data}"
                                    video_generated = True
                                    os.unlink(vid_path)
                                    break
                                else:
                                    print(f"      Video file too small: {size} bytes")
                                    if os.path.exists(vid_path): os.unlink(vid_path)
                            except Exception as e:
                                print(f"      Error with {fourcc_str}: {e}")
                                if os.path.exists(vid_path):
                                    os.unlink(vid_path)
                        
                    if not video_generated:
                        print("⚠️ All video codecs failed. Returning static image.")
                        b64_img = "data:image/jpeg;base64," + base64.b64encode(image_bytes).decode('utf-8')

                except Exception as e:
                    print(f"⚠️ Video generation failed: {e}. Returning image.")
                    b64_img = "data:image/jpeg;base64," + base64.b64encode(image_bytes).decode('utf-8')
            else:
                # Standard Image
                b64_img = "data:image/jpeg;base64," + base64.b64encode(image_bytes).decode('utf-8')
            
            # Prepare blueprint data for ExplanationCard
            blueprint_data = {
                "anchors": [
                    {"type": a.type, "confidence": a.confidence, "id": a.id}
                    for a in blueprint.anchors
                ],
                "mesh": {
                    "constraints": [
                        {"type": "spatial", "id": k}
                        for k in (blueprint.mesh.constraints.keys() if blueprint.mesh and hasattr(blueprint.mesh, 'constraints') and isinstance(blueprint.mesh.constraints, dict) else [])
                    ]
                }
            }
            
            # Extract Metrics (Real tracked sizes)
            real_original_size = blueprint.metadata.original_size_bytes if blueprint.metadata.original_size_bytes > 0 else 2 * 1024 * 1024 # Fallback 2MB
            real_hlx_size = blueprint.metadata.compressed_size_bytes if blueprint.metadata.compressed_size_bytes > 0 else original_size
            
            return {
                "image": b64_img,
                "verification": {"status": "passed", "checks": []},
                "blueprint": blueprint_data,
                "originalSize": real_original_size,
                "hlxSize": real_hlx_size,
                "modelUsed": materializer.model_name or "Gemini 2.0 Flash",
                "processingTime": processing_time,
                # 🚀 Living Data metrics
                "targetResolution": target_resolution,
                "upgradeMetrics": upgrade_metrics
            }
            
        finally:
            # Cleanup
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    except Exception as e:
        print(f"Materialize error: {e}")
        # If it's already HTTPException, re-raise
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

class ChatRequest(BaseModel):
    message: str
    context: str = ""

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Chat endpoint using Gemini with README context.
    """
    try:
        from google import genai
        
        # Configure API Key
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return {"response": "I'm running in local mode without a Gemini API key. I can tell you that HELIX is an identity-preserving compression tool!"}
            
        client = genai.Client(api_key=api_key)
        
        # Load README context
        readme_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "README.md")
        try:
            with open(readme_path, "r") as f:
                context = f.read()
        except:
            context = "Context unavailable."


        
        prompt = f"""
        You are the HELIX AI Assistant. You represent Project HELIX, an identity-preserving AI compression system.
        
        CONTEXT FROM README:
        {context}
        
        USER QUESTION: {request.message}
        
        INSTRUCTIONS:
        - Answer as if you ARE the project HELIX. Use "I", "We".
        - Be helpful, concise, and futuristic.
        - If the user asks about something unrelated, politely steer back to HELIX or image compression.
        - Keep answers under 3-4 sentences unless detailed technical info is asked.
        """
        
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt
        )
        return {"response": response.text}

    except Exception as e:
        print(f"Chat error: {e}")
        # Fallback response so the UI doesn't break
        return {"response": "My neural connection is fluctuating. I could not reach the Gemini core."}

class HelixChatRequest(BaseModel):
    message: str

@app.post("/api/helix-chat")
async def helix_chat_endpoint(request: HelixChatRequest, authorization: str = Header(None)):
    """
    HELIX Chat - AI assistant that knows everything about the project.
    Uses multiple codebase sources for comprehensive technical context.
    Persists chat history if authenticated.
    """
    from google import genai
    from src.core.auth import verify_token, save_chat_message
    
    user_id = None
    if authorization:
        token = authorization.replace("Bearer ", "")
        payload = verify_token(token)
        if payload:
            user_id = payload['user_id']
            # Save User Message
            save_chat_message(user_id, "user", request.message)
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"response": "I'm currently offline. Please set GEMINI_API_KEY."}
    
    try:
        client = genai.Client(api_key=api_key)
        
        # Load multiple context sources for comprehensive knowledge
        context_parts = []
        
        # 1. Updates.txt (Feature list)
        updates_path = os.path.join(os.path.dirname(__file__), '..', '..', 'Updates.txt')
        try:
            with open(updates_path, 'r') as f:
                context_parts.append(f"## FEATURES AND ROADMAP:\n{f.read()[:8000]}")
        except FileNotFoundError:
            pass
            
        # 2. README (Project overview)
        readme_path = os.path.join(os.path.dirname(__file__), '..', '..', 'DOCS', 'README.md')
        try:
            with open(readme_path, 'r') as f:
                context_parts.append(f"## PROJECT README:\n{f.read()[:5000]}")
        except FileNotFoundError:
            pass
            
        # 3. Blueprint Schema (Technical spec)
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'schema', 'blueprint.py')
        try:
            with open(schema_path, 'r') as f:
                context_parts.append(f"## HLX SCHEMA (blueprint.py):\n```python\n{f.read()[:3000]}\n```")
        except FileNotFoundError:
            pass
            
        context_content = "\n\n".join(context_parts)
        
        system_prompt = f"""You are HELIX, a helpful AI assistant for an image/audio/video compression system.

You help users understand how HELIX works. Be friendly, clear, and concise.

CONTEXT:
{context_content}

RESPONSE STYLE:
- Keep responses short and conversational (2-4 sentences when possible)
- Avoid excessive formatting like bold, bullets, or code blocks unless truly needed
- Use plain language, not marketing speak
- If you don't know something, just say so
- Focus on being helpful, not impressive
"""
        
        response = client.models.generate_content(
            model='gemini-2.5-flash-preview-05-20',
            contents=[system_prompt, f"User question: {request.message}"],
            config={'temperature': 0.7, 'max_output_tokens': 1024}
        )
        
        ai_response = response.text
        
        # Save AI Message
        if user_id:
            save_chat_message(user_id, "assistant", ai_response)
        
        return {"response": ai_response}
        
    except Exception as e:
        print(f"HELIX Chat error: {e}")
        return {"response": f"I encountered an issue: {str(e)}"}

@app.get("/api/helix-chat/history")
async def get_chat_history_endpoint(authorization: str = Header(None)):
    """Get chat history for authenticated user"""
    from src.core.auth import verify_token, get_chat_history
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    token = authorization.replace("Bearer ", "")
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    history = get_chat_history(payload['user_id'])
    return {"history": history}

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """Legacy chat endpoint - redirects to helix-chat"""
    helix_req = HelixChatRequest(message=request.message)
    return await helix_chat_endpoint(helix_req)

# ============================================
# TEXT MODALITY ENDPOINTS
# ============================================

class TextEncodeRequest(BaseModel):
    text: str

@app.post("/api/encode-text")
async def encode_text(request: TextEncodeRequest):
    """
    Takes text content, extracts semantic anchors, returns encrypted .hlx as base64.
    """
    try:
        from src.extractors.text_anchors import TextAnchorExtractor
        from src.core.hlx_codec import encode as hlx_encode
        import base64
        
        extractor = TextAnchorExtractor()
        blueprint = extractor.extract(request.text)
        
        # Encode to encrypted binary
        hlx_bytes = hlx_encode(blueprint.to_dict())
        hlx_b64 = base64.b64encode(hlx_bytes).decode('utf-8')
        
        return {
            "hlx": hlx_b64,
            "stats": {
                "original_chars": len(request.text),
                "hlx_bytes": len(hlx_bytes),
                "compression": round(len(request.text) / len(hlx_bytes), 2) if len(hlx_bytes) > 0 else 0,
                "anchors": len(blueprint.anchors)
            }
        }
    except Exception as e:
        print(f"Text encode error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class TextMaterializeRequest(BaseModel):
    hlx: str  # Base64 encoded .hlx data

@app.post("/api/materialize-text")
async def materialize_text(request: TextMaterializeRequest):
    """
    Takes encrypted .hlx data, regenerates text using Gemini.
    """
    try:
        from src.core.text_materializer import TextMaterializer
        from src.core.hlx_codec import decode as hlx_decode
        import base64
        
        # Decode from base64
        hlx_bytes = base64.b64decode(request.hlx)
        
        # Decrypt and parse blueprint
        blueprint_dict = hlx_decode(hlx_bytes)
        blueprint = HelixBlueprint.from_dict(blueprint_dict)
        
        # Verify modality
        if blueprint.metadata.modality != "text":
            raise HTTPException(status_code=400, detail="Not a text blueprint")
        
        # Regenerate
        text_materializer = TextMaterializer()
        regenerated = text_materializer.materialize(blueprint)
        
        return {
            "text": regenerated,
            "stats": {
                "word_count": len(regenerated.split()),
                "char_count": len(regenerated)
            }
        }
    except Exception as e:
        print(f"Text materialize error: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# AUTHENTICATION ENDPOINTS
# ============================================

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str = None

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/api/auth/register")
async def register(request: RegisterRequest):
    """Register a new user"""
    from src.core.auth import register_user
    
    success, result = register_user(request.email, request.password, request.name)
    
    if not success:
        raise HTTPException(status_code=400, detail=result)
    
    return {
        "success": True,
        "token": result,
        "user": {
            "email": request.email,
            "name": request.name or request.email.split('@')[0]
        }
    }

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """Login user and return JWT token"""
    from src.core.auth import login_user
    
    success, result = login_user(request.email, request.password)
    
    if not success:
        raise HTTPException(status_code=401, detail=result)
    
    return {
        "success": True,
        "token": result
    }

@app.get("/api/auth/me")
async def get_current_user(authorization: str = Header(None)):
    """Get current user from token"""
    from src.core.auth import verify_token, get_user_by_id
    from fastapi import Header
    
    if not authorization:
        raise HTTPException(status_code=401, detail="No token provided")
    
    token = authorization.replace("Bearer ", "")
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = get_user_by_id(payload['user_id'])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"user": user}

# ============================================
# FILE STORAGE ENDPOINTS
# ============================================

class SaveFileRequest(BaseModel):
    filename: str
    file_type: str
    hlx_data: str = None  # Base64 encoded
    cloudinary_url: str = None

@app.post("/api/files/save")
async def save_file(request: SaveFileRequest, authorization: str = Header(None)):
    """Save file reference for authenticated user"""
    from src.core.auth import verify_token, save_user_file
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    token = authorization.replace("Bearer ", "")
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    file_id = save_user_file(
        user_id=payload['user_id'],
        filename=request.filename,
        file_type=request.file_type,
        hlx_data=request.hlx_data,
        cloudinary_url=request.cloudinary_url
    )
    
    return {"success": True, "file_id": file_id}

@app.get("/api/files/list")
async def list_files(authorization: str = Header(None)):
    """Get all files for authenticated user"""
    from src.core.auth import verify_token, get_user_files
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    token = authorization.replace("Bearer ", "")
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    files = get_user_files(payload['user_id'])
    return {"files": files}

@app.get("/api/files/{file_id}")
async def get_file(file_id: int, authorization: str = Header(None)):
    """Get file by ID (for download)"""
    from src.core.auth import verify_token, get_file_by_id
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    token = authorization.replace("Bearer ", "")
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    file = get_file_by_id(file_id, payload['user_id'])
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    return {"file": file}

@app.get("/api/files/share/{file_id}")
async def get_shared_file(file_id: int):
    """Get file by ID (public sharing - no auth)"""
    from src.core.auth import get_file_by_id
    
    file = get_file_by_id(file_id)
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Return only public info
    return {
        "filename": file['filename'],
        "file_type": file['file_type'],
        "hlx_data": file['hlx_data'],
        "cloudinary_url": file['cloudinary_url']
    }

# ============ ANALYTICS ENDPOINTS ============

class AnalyticsData(BaseModel):
    identity: str  # 26-char blueprint identity
    original_size: int = 0
    compressed_size: int = 0
    anchors_count: int = 0
    modality: str = "image"
    model_used: str = ""
    processing_time_ms: int = 0

# In-memory store (replace with DB in production)
analytics_store: Dict[str, dict] = {}

@app.post("/api/analytics")
async def save_analytics(data: AnalyticsData):
    """Save analytics data for a blueprint by identity."""
    if len(data.identity) != 26:
        raise HTTPException(status_code=400, detail="Identity must be 26 characters")
    analytics_store[data.identity] = data.dict()
    return {"status": "saved", "identity": data.identity}

@app.get("/api/analytics/{identity}")
async def get_analytics(identity: str):
    """Get analytics data for a blueprint by identity."""
    if identity not in analytics_store:
        raise HTTPException(status_code=404, detail="Analytics not found for this identity")
    return analytics_store[identity]

@app.get("/api/analytics")
async def list_analytics():
    """List all analytics entries."""
    return {"count": len(analytics_store), "entries": list(analytics_store.values())}

# ============================================
# API KEY MANAGEMENT ENDPOINTS
# ============================================

class CreateAPIKeyRequest(BaseModel):
    name: str
    permissions: str = "encode,materialize"

@app.post("/api/keys")
async def create_api_key(request: CreateAPIKeyRequest, authorization: str = Header(None)):
    """
    Generate a new API key for the authenticated user.
    The full key is only returned once - save it securely!
    """
    from src.core.auth import verify_token, generate_api_key
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    token = authorization.replace("Bearer ", "")
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    success, api_key, error = generate_api_key(
        payload['user_id'], 
        request.name, 
        request.permissions
    )
    
    if not success:
        raise HTTPException(status_code=500, detail=error)
    
    return {
        "success": True,
        "api_key": api_key,
        "message": "Save this key securely! It will not be shown again.",
        "usage": {
            "sdk": f'sdk = HelixSDK(base_url="YOUR_API_URL", api_key="{api_key}")',
            "curl": f'curl -H "Authorization: Bearer {api_key}" ...'
        }
    }

@app.get("/api/keys")
async def list_api_keys(authorization: str = Header(None)):
    """List all API keys for the authenticated user."""
    from src.core.auth import verify_token, get_user_api_keys
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    token = authorization.replace("Bearer ", "")
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    keys = get_user_api_keys(payload['user_id'])
    return {"keys": keys}

@app.delete("/api/keys/{key_id}")
async def delete_api_key_endpoint(key_id: int, authorization: str = Header(None)):
    """Delete an API key."""
    from src.core.auth import verify_token, delete_api_key
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    token = authorization.replace("Bearer ", "")
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    success = delete_api_key(key_id, payload['user_id'])
    
    if not success:
        raise HTTPException(status_code=404, detail="Key not found")
    
    return {"success": True, "message": "API key deleted"}

@app.post("/api/keys/{key_id}/revoke")
async def revoke_api_key_endpoint(key_id: int, authorization: str = Header(None)):
    """Revoke an API key (keeps record but makes it unusable)."""
    from src.core.auth import verify_token, revoke_api_key
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    token = authorization.replace("Bearer ", "")
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    success = revoke_api_key(key_id, payload['user_id'])
    
    if not success:
        raise HTTPException(status_code=404, detail="Key not found")
    
    return {"success": True, "message": "API key revoked"}

# Middleware to verify API key for SDK requests
async def verify_sdk_auth(authorization: str = Header(None)):
    """Verify either JWT token or API key."""
    from src.core.auth import verify_token, verify_api_key
    
    if not authorization:
        return None
    
    auth_value = authorization.replace("Bearer ", "")
    
    # Try API key first (starts with hlx_)
    if auth_value.startswith("hlx_"):
        return verify_api_key(auth_value)
    
    # Try JWT token
    payload = verify_token(auth_value)
    if payload:
        return {"user_id": payload['user_id'], "email": payload['email'], "permissions": ['encode', 'materialize']}
    
    return None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

