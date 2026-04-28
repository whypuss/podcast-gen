#!/usr/bin/env python3
"""inspect_lang.py"""
import sys
sys.path.insert(0, '/Users/whypuss/.kimaki/projects/podcast-gen/backend')

import torch
from qwen_tts import Qwen3TTSModel

model = Qwen3TTSModel.from_pretrained(
    "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice",
    device_map="cpu",
    dtype=torch.float32,
)

# 看 generate_custom_voice 的 signature
import inspect
sig = inspect.signature(model.generate_custom_voice)
print("generate_custom_voice signature:")
print(sig)

# 看 model config
print("\nModel config keys:")
if hasattr(model, 'config'):
    for k in dir(model.config):
        if not k.startswith('_'):
            print(f"  {k}")
