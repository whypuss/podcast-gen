#!/usr/bin/env python3
"""test_generate_debug.py"""
import sys
sys.path.insert(0, '/Users/whypuss/.kimaki/projects/podcast-gen/backend')

import torch
import soundfile as sf
import subprocess
import uuid
from pathlib import Path
from qwen3_tts_engine import Qwen3TTSEngine
from audio_merger import TEMP_DIR

# Load engine
eng = Qwen3TTSEngine(device="cpu", dtype=torch.float32)
eng.load()

# Generate 2 segments
segments = [
    ("male", "大家好，歡迎收聽今天的 Podcast。"),
    ("female", "很高興和你見面，今天天氣很不錯。"),
]

job_id = uuid.uuid4().hex[:8]
wav_paths = []

for i, (speaker, text) in enumerate(segments):
    out_wav = TEMP_DIR / f"seg_{job_id}_{i:03d}.wav"
    ok = eng.generate_to_file(text, out_wav, speaker=speaker, language="Chinese")
    if ok:
        wav_paths.append(out_wav)
        print(f"✅ {speaker}: {out_wav}")
    else:
        print(f"❌ {speaker} failed")

# Check the WAV files
print("\n--- Segment info ---")
for p in wav_paths:
    info = sf.info(str(p))
    print(f"{p.name}: {info.samplerate}Hz, {info.subtype}, {info.duration:.2f}s, channels={info.channels}")

# Try FFmpeg concat manually
print("\n--- FFmpeg concat test ---")
concat_file = TEMP_DIR / f"test_concat_{job_id}.txt"
with open(concat_file, "w") as f:
    for p in wav_paths:
        f.write(f"file '{p}'\n")
print(f"Concat file:\n{concat_file.read_text()}")

cmd = [
    "ffmpeg", "-y",
    "-f", "concat,separate", "-safe", "0",
    "-i", str(concat_file),
    "-ar", "44100",
    "-ac", "2",
    "-codec:a", "pcm_s16le",
    str(TEMP_DIR / f"test_output_{job_id}.wav"),
]
print(f"Running: {' '.join(cmd)}")
result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
print(f"Return: {result.returncode}")
if result.returncode != 0:
    print(f"STDERR: {result.stderr[-1000:]}")
else:
    print("✅ FFmpeg concat succeeded")
    out = TEMP_DIR / f"test_output_{job_id}.wav"
    info = sf.info(str(out))
    print(f"Output: {info.samplerate}Hz, {info.subtype}, {info.duration:.2f}s")
