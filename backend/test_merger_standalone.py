#!/usr/bin/env python3
"""test_merger_standalone.py"""
import sys
sys.path.insert(0, '/Users/whypuss/.kimaki/projects/podcast-gen/backend')

import torch
import soundfile as sf
import tempfile
from pathlib import Path
from qwen3_tts_engine import Qwen3TTSEngine
from audio_merger import merge_wav_segments, TEMP_DIR

print("Loading engine...")
eng = Qwen3TTSEngine(device="cpu", dtype=torch.float32)
eng.load()

# Generate 2 short segments
segments = [
    ("male", "大家好，歡迎收聽今天的 Podcast。"),
    ("female", "今天天氣很好，我們來聊天吧。"),
]

job_id = "test_merge"
wav_paths = []

for i, (speaker, text) in enumerate(segments):
    out_wav = TEMP_DIR / f"seg_{job_id}_{i:03d}.wav"
    ok = eng.generate_to_file(text, out_wav, speaker=speaker, language="Chinese")
    if ok:
        wav_paths.append(out_wav)
        info = sf.info(str(out_wav))
        print(f"✅ {speaker}: {out_wav} ({info.samplerate}Hz, {info.subtype}, {info.duration:.2f}s)")
    else:
        print(f"❌ {speaker} failed")

if len(wav_paths) < 2:
    print("Not enough segments"); sys.exit(1)

# Test merge
out_path = TEMP_DIR / "test_merged.mp3"
print(f"\nMerging to {out_path}...")
ok = merge_wav_segments(wav_paths, out_path, gap_seconds=0.3, output_format="mp3")
print(f"Merge result: {'✅' if ok else '❌'}")
if ok and out_path.exists():
    info = sf.info(str(out_path))
    print(f"Output: {info.samplerate}Hz, {info.subtype}, {info.duration:.2f}s, {out_path.stat().st_size} bytes")
