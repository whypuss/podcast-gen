#!/usr/bin/env python3
"""test_instruct_cantonese.py"""
import sys
sys.path.insert(0, '/Users/whypuss/.kimaki/projects/podcast-gen/backend')

import inspect
import torch
from qwen_tts import Qwen3TTSModel

print("Loading model...")
model = Qwen3TTSModel.from_pretrained(
    "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice",
    device="cpu",
    dtype=torch.float32,
)

# 看 generate 和 generate_custom_voice 的完整 signature
sig_generate = inspect.signature(model.generate)
sig_gcv = inspect.signature(model.generate_custom_voice)

print("\ngenerate signature:")
for name, p in sig_generate.parameters.items():
    print(f"  {name}: {p.default}")

print("\ngenerate_custom_voice signature:")
for name, p in sig_gcv.parameters.items():
    print(f"  {name}: {p.default}")

# 測試 generate_custom_voice 是否支援 instruct
print("\n\n=== Test 1: generate_custom_voice without instruct ===")
text = "你好，今日食咗飯未呀？"
try:
    result = model.generate_custom_voice(
        text=text,
        language="Chinese",
        instruct="用標準粵語（廣東話）說話，語氣親切",
    )
    print(f"  ✅ returned: {type(result)}")
except TypeError as e:
    print(f"  ❌ TypeError: {e}")
except Exception as e:
    print(f"  ❌ {type(e).__name__}: {e}")

print("\n=== Test 2: generate with instruct ===")
try:
    result = model.generate(
        text=text,
        language="Chinese",
        instruct="用標準粵語（廣東話）說話",
    )
    print(f"  ✅ returned: {type(result)}")
except TypeError as e:
    print(f"  ❌ TypeError: {e}")
except Exception as e:
    print(f"  ❌ {type(e).__name__}: {e}")
