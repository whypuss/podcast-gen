#!/usr/bin/env python3
"""test_instruct_engine.py"""
import sys
sys.path.insert(0, '/Users/whypuss/.kimaki/projects/podcast-gen/backend')

import inspect
import torch
from qwen3_tts_engine import Qwen3TTSEngine

print("Loading engine...")
engine = Qwen3TTSEngine(device="cpu", dtype=torch.float32)
engine.load()

# 看 engine.generate 的 signature
sig = inspect.signature(engine.generate)
print(f"\nengine.generate signature:")
for name, p in sig.parameters.items():
    print(f"  {name}: {p.default}")

# 看 qwen_tts generate_custom_voice signature
from qwen_tts import Qwen3TTSModel
sig2 = inspect.signature(Qwen3TTSModel.generate_custom_voice)
print(f"\nQwen3TTSModel.generate_custom_voice signature:")
for name, p in sig2.parameters.items():
    print(f"  {name}: {p.default}")
