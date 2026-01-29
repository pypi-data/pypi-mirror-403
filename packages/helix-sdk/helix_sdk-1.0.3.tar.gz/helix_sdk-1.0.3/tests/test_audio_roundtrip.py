import os
import wave
import struct
import math
from src.extractors.audio_extractor import AudioAnchorExtractor
from src.core.audio_materializer import AudioMaterializer

def generate_sine_wave(filename, duration=1.0, freq=440.0):
    """Generate a simple sine wave wav file"""
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        
        for i in range(n_samples):
            value = int(32767.0 * math.sin(2 * math.pi * freq * i / sample_rate))
            data = struct.pack('<h', value)
            wav_file.writeframesraw(data)

def test_roundtrip():
    input_file = "test_audio.wav"
    output_hlx = "test_audio.hlx"
    
    # 1. Generate Input
    generate_sine_wave(input_file)
    original_size = os.path.getsize(input_file)
    print(f"Generated test audio: {input_file} ({original_size} bytes)")
    
    # 2. Extract (Encode)
    extractor = AudioAnchorExtractor()
    blueprint = extractor.extract(input_file)
    blueprint.save(output_hlx)
    print(f"Encoded to HLX: {output_hlx}")
    
    # 3. Materialize (Decode)
    materializer = AudioMaterializer()
    reconstructed_bytes = materializer.materialize(blueprint)
    
    # 4. Verify Content
    with open(input_file, 'rb') as f:
        original_bytes = f.read()
        
    if original_bytes == reconstructed_bytes:
        print("✅ SUCCESS: Perfect Reconstruction Verified!")
    else:
        print("❌ FAILURE: Bytes mismatch.")
        print(f"Original: {len(original_bytes)}, Reconstructed: {len(reconstructed_bytes)}")
        
    # Cleanup
    if os.path.exists(input_file): os.remove(input_file)
    if os.path.exists(output_hlx): os.remove(output_hlx)

if __name__ == "__main__":
    test_roundtrip()
