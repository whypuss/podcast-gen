#!/usr/bin/env python3
"""test_cantonese_gen.py — 測試粵語合成"""
import sys
sys.path.insert(0, '/Users/whypuss/.kimaki/projects/podcast-gen/backend')

import torch
from qwen3_tts_engine import Qwen3TTSEngine

print("Loading...")
engine = Qwen3TTSEngine(device="cpu", dtype=torch.float32)
if not engine.load():
    print("Load failed"); sys.exit(1)

cantonese_text = "你好，我今日好開心，想同你分享一下。"

# language=None（預設）
print(f"\n[Test 1] language=None (default)")
audio1 = engine.generate(cantonese_text, speaker="male", language=None)
if audio1:
    import soundfile as sf
    sf.write("/tmp/test_lang_none.wav", audio1, engine.sample_rate)
    print(f"  ✅ {len(audio1)} samples, saved")
else:
    print("  ❌")

# language="Chinese"
print(f"\n[Test 2] language=Chinese")
audio2 = engine.generate(cantonese_text, speaker="male", language="Chinese")
if audio2:
    import soundfile as sf
    sf.write("/tmp/test_lang_chinese.wav", audio2, engine.sample_rate)
    print(f"  ✅ {len(audio2)} samples, saved")
else:
    print("  ❌")

# language="Cantonese"
print(f"\n[Test 3] language=Cantonese")
audio3 = engine.generate(cantonese_text, speaker="male", language="Cantonese")
if audio3:
    import soundfile as sf
    sf.write("/tmp/test_lang_cantonese.wav", audio3, engine.sample_rate)
    print(f"  ✅ {len(audio3)} samples, saved")
else:
    print("  ❌")
