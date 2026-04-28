#!/usr/bin/env python3
"""test_qwen3_load.py"""
import sys
sys.path.insert(0, '/Users/whypuss/.kimaki/projects/podcast-gen/backend')

import torch
from qwen3_tts_engine import Qwen3TTSEngine

print("Loading Qwen3 TTS (CPU, float32)... this will download ~1.8GB on first run...")
engine = Qwen3TTSEngine(device="cpu", dtype=torch.float32)
success = engine.load()
print(f"Loaded: {success}")
if success:
    print("Testing generation...")
    audio = engine.generate("你好，這是一個測試。", speaker="male", language="Chinese")
    print(f"Generated: {audio is not None}, len={len(audio) if audio is not None else 0}")
