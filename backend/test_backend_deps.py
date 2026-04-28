#!/usr/bin/env python3
"""test_backend_deps.py"""
import sys
sys.path.insert(0, '/Users/whypuss/.kimaki/projects/podcast-gen/backend')

# Test all imports
try:
    import uvicorn
    import fastapi
    import torch
    import soundfile
    print("✅ All backend deps OK")
    print(f"  torch: {torch.__version__}, device: {torch.get_device_name(0) if torch.cuda.is_available() else 'cpu'}")
except Exception as e:
    print(f"❌ {e}")
    sys.exit(1)

# Test FastAPI app loads
try:
    from main import app
    print("✅ FastAPI app loaded")
except Exception as e:
    print(f"❌ FastAPI app failed: {e}")
    sys.exit(1)

# Test Qwen3 TTS engine
try:
    from qwen3_tts_engine import Qwen3TTSEngine
    import torch
    eng = Qwen3TTSEngine(device="cpu", dtype=torch.float32)
    ok = eng.load()
    print(f"✅ Qwen3 TTS loaded: {ok}")
except Exception as e:
    print(f"❌ Qwen3 TTS: {e}")
    sys.exit(1)

print("\nAll checks passed!")
