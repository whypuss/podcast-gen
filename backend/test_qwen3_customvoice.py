#!/usr/bin/env python3
"""test_qwen3_customvoice.py"""
import sys
sys.path.insert(0, '/Users/whypuss/.kimaki/projects/podcast-gen/backend')

import torch
from qwen3_tts_engine import Qwen3TTSEngine

print("Loading Qwen3 TTS CustomVoice (CPU)...")
engine = Qwen3TTSEngine(device="cpu", dtype=torch.float32)
success = engine.load()
print(f"Loaded: {success}")
if success:
    print("Testing male voice (VoiceDesign)...")
    audio = engine.generate("你好，這是一個測試。", speaker="male", language="Chinese")
    print(f"Male: {'✅' if audio is not None else '❌'} len={len(audio) if audio is not None else 0}")
    if audio is not None:
        import soundfile as sf
        sf.write("/tmp/test_male.wav", audio, 24000)
        print("✅ Saved /tmp/test_male.wav")
