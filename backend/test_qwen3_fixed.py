#!/usr/bin/env python3
"""test_qwen3_fixed.py"""
import sys
sys.path.insert(0, '/Users/whypuss/.kimaki/projects/podcast-gen/backend')

import torch
from qwen3_tts_engine import Qwen3TTSEngine

print("Loading Qwen3 TTS (CPU, float32)...")
engine = Qwen3TTSEngine(device="cpu", dtype=torch.float32)
success = engine.load()
print(f"Loaded: {success}")
if success:
    print("Testing male voice generation...")
    audio = engine.generate("你好，這是一個測試。", speaker="male", language="Chinese")
    print(f"Male: {'✅' if audio is not None else '❌'} len={len(audio) if audio is not None else 0}")
    print("Testing female voice generation...")
    audio2 = engine.generate("你好，這是一個測試。", speaker="female", language="Chinese")
    print(f"Female: {'✅' if audio2 is not None else '❌'} len={len(audio2) if audio2 is not None else 0}")
