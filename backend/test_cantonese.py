#!/usr/bin/env python3
"""test_cantonese.py"""
import sys
sys.path.insert(0, '/Users/whypuss/.kimaki/projects/podcast-gen/backend')

import torch
from qwen3_tts_engine import Qwen3TTSEngine

print("Loading Qwen3 TTS...")
engine = Qwen3TTSEngine(device="cpu", dtype=torch.float32)
success = engine.load()
if not success:
    print("Load failed"); sys.exit(1)

# 測試不同 language 值
test_phrases = {
    "Cantonese": "你好，我今日好開心，想同你分享一下。",
    "Chinese": "你好，我今日好開心，想同你分享一下。",
    "Mandarin": "你好，我今天很开心，想和你分享一下。",
}

for lang, text in test_phrases.items():
    print(f"\n[{lang}] text={text}")
    audio = engine.generate(text, speaker="male", language=lang)
    if audio is not None:
        import soundfile as sf
        sf.write(f"/tmp/test_{lang.lower()}.wav", audio, engine.sample_rate)
        print(f"  ✅ {len(audio)} samples ({len(audio)/engine.sample_rate:.1f}s)")
    else:
        print(f"  ❌ failed")
