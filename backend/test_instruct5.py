#!/usr/bin/env python3
"""test_instruct_cantonese_v2.py"""
import sys
sys.path.insert(0, '/Users/whypuss/.kimaki/projects/podcast-gen/backend')

import torch
import soundfile as sf
import time
from qwen_tts import Qwen3TTSModel

print("Loading model...")
model = Qwen3TTSModel.from_pretrained(
    "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice",
    device_map="cpu",
    torch_dtype=torch.float32,
)

cantonese_text = "你好，今日食咗飯未呀？"

print(f"\n=== Test 1: Cantonese with instruct → uncle_fu ===")
print(f"Text: {cantonese_text}")
print(f"Instruct: 用標準粵語（廣東話）說話，語氣親切自然")

t0 = time.time()
result = model.generate_custom_voice(
    text=cantonese_text,
    speaker="uncle_fu",
    language="Chinese",
    instruct="用標準粵語（廣東話）說話，語氣親切自然",
)
t1 = time.time()
print(f"  Time: {t1-t0:.1f}s")

if result is not None:
    wavs = result[0] if isinstance(result, tuple) else result
    print(f"  Shape: {wavs.shape}, sr: 24000")
    sf.write("/tmp/test_cantonese_instruct.wav", wavs, 24000)
    print(f"  ✅ Saved: /tmp/test_cantonese_instruct.wav")
else:
    print(f"  ❌ No output")

print(f"\n=== Test 2: Baseline (no instruct) → uncle_fu ===")
t0 = time.time()
result2 = model.generate_custom_voice(
    text=cantonese_text,
    speaker="uncle_fu",
    language="Chinese",
)
t1 = time.time()
print(f"  Time: {t1-t0:.1f}s")

if result2 is not None:
    wavs2 = result2[0] if isinstance(result2, tuple) else result2
    sf.write("/tmp/test_cantonese_no_instruct.wav", wavs2, 24000)
    print(f"  ✅ Saved: /tmp/test_cantonese_no_instruct.wav")
else:
    print(f"  ❌ No output")
