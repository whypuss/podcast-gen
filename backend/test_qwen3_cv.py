#!/usr/bin/env python3
"""test_qwen3_cv.py — 測試 Qwen3 TTS CustomVoice generate_custom_voice"""
import sys
sys.path.insert(0, '/Users/whypuss/.kimaki/projects/podcast-gen/backend')

import torch
import time
from qwen3_tts_engine import Qwen3TTSEngine, DEFAULT_MALE, DEFAULT_FEMALE

print(f"Loading Qwen3 TTS CustomVoice (CPU, float32)...")
engine = Qwen3TTSEngine(device="cpu", dtype=torch.float32)
success = engine.load()
print(f"Loaded: {success}")
if not success:
    sys.exit(1)

print(f"\nMale speaker:   {engine.male_speaker}")
print(f"Female speaker: {engine.female_speaker}")

test_text = "你好，這是一個測試音頻，我想讓你知道這個新聲音模型的效果很不錯。"

# Test male
print(f"\n[1] 生成男聲...")
t0 = time.time()
audio_m = engine.generate(test_text, speaker="male")
t1 = time.time()
if audio_m is not None:
    out_m = "/tmp/test_male.wav"
    import soundfile as sf
    sf.write(out_m, audio_m, engine.sample_rate)
    print(f"✅ 男聲成功！{len(audio_m)} samples ({len(audio_m)/engine.sample_rate:.1f}s) @ {engine.sample_rate}Hz, 耗時 {t1-t0:.1f}s")
    print(f"   → {out_m}")
else:
    print(f"❌ 男聲失敗")

# Test female
print(f"\n[2] 生成女聲...")
t0 = time.time()
audio_f = engine.generate(test_text, speaker="female")
t1 = time.time()
if audio_f is not None:
    out_f = "/tmp/test_female.wav"
    import soundfile as sf
    sf.write(out_f, audio_f, engine.sample_rate)
    print(f"✅ 女聲成功！{len(audio_f)} samples ({len(audio_f)/engine.sample_rate:.1f}s) @ {engine.sample_rate}Hz, 耗時 {t1-t0:.1f}s")
    print(f"   → {out_f}")
else:
    print(f"❌ 女聲失敗")
