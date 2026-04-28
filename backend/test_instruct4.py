#!/usr/bin/env python3
"""test_instruct_cantonese_direct.py"""
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
instruct_cantonese = "用標準粵語（廣東話）說話，語氣親切自然"

print(f"\n=== Test 1: Cantonese with instruct (Chinese) ===")
print(f"Text: {cantonese_text}")
print(f"Instruct: {instruct_cantonese}")

t0 = time.time()
result = model.generate_custom_voice(
    text=cantonese_text,
    speaker="male",
    language="Chinese",
    instruct=instruct_cantonese,
)
t1 = time.time()
print(f"  Time: {t1-t0:.1f}s")
print(f"  Result type: {type(result)}")

if result is not None:
    wavs = result[0] if isinstance(result, tuple) else result
    print(f"  Wavs shape: {wavs.shape if hasattr(wavs, 'shape') else len(wavs)}")
    sf.write("/tmp/test_cantonese_instruct.wav", wavs, 24000)
    print(f"  ✅ Saved to /tmp/test_cantonese_instruct.wav")
else:
    print(f"  ❌ No audio output")

print(f"\n=== Test 2: Without instruct (baseline Chinese) ===")
t0 = time.time()
result2 = model.generate_custom_voice(
    text=cantonese_text,
    speaker="male",
    language="Chinese",
)
t1 = time.time()
print(f"  Time: {t1-t0:.1f}s")

if result2 is not None:
    wavs2 = result2[0] if isinstance(result2, tuple) else result2
    sf.write("/tmp/test_cantonese_no_instruct.wav", wavs2, 24000)
    print(f"  ✅ Saved to /tmp/test_cantonese_no_instruct.wav")
else:
    print(f"  ❌ No audio output")
