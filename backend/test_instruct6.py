#!/usr/bin/env python3
"""test_instruct_cantonese_v3.py"""
import sys
sys.path.insert(0, '/Users/whypuss/.kimaki/projects/podcast-gen/backend')

import torch
import soundfile as sf
import time
import numpy as np
from qwen_tts import Qwen3TTSModel

print("Loading model...")
model = Qwen3TTSModel.from_pretrained(
    "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice",
    device_map="cpu",
    torch_dtype=torch.float32,
)

cantonese_text = "你好，今日食咗飯未呀？"

print(f"\n=== Test 1: Cantonese with instruct ===")
t0 = time.time()
result = model.generate_custom_voice(
    text=cantonese_text,
    speaker="uncle_fu",
    language="Chinese",
    instruct="用標準粵語（廣東話）說話，語氣親切自然",
)
t1 = time.time()

# Handle both tuple and non-tuple returns
if isinstance(result, tuple):
    audio = result[0]
else:
    audio = result

if audio is not None:
    if isinstance(audio, list):
        audio = audio[0]
    audio_np = np.array(audio)
    print(f"  Time: {t1-t0:.1f}s, dtype={audio_np.dtype}, shape={audio_np.shape}")
    sf.write("/tmp/test_cantonese_instruct.wav", audio_np, 24000)
    print(f"  ✅ Saved: /tmp/test_cantonese_instruct.wav")
else:
    print(f"  ❌ No output")

print(f"\n=== Test 2: No instruct (baseline) ===")
t0 = time.time()
result2 = model.generate_custom_voice(
    text=cantonese_text,
    speaker="uncle_fu",
    language="Chinese",
)
t1 = time.time()

if isinstance(result2, tuple):
    audio2 = result2[0]
else:
    audio2 = result2

if audio2 is not None:
    if isinstance(audio2, list):
        audio2 = audio2[0]
    audio2_np = np.array(audio2)
    print(f"  Time: {t1-t0:.1f}s, dtype={audio2_np.dtype}, shape={audio2_np.shape}")
    sf.write("/tmp/test_cantonese_no_instruct.wav", audio2_np, 24000)
    print(f"  ✅ Saved: /tmp/test_cantonese_no_instruct.wav")
else:
    print(f"  ❌ No output")
