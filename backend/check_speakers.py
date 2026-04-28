#!/usr/bin/env python3
"""check_speakers.py"""
import sys
sys.path.insert(0, '/Users/whypuss/.kimaki/projects/podcast-gen/backend')

import torch
from qwen_tts import Qwen3TTSModel

m = Qwen3TTSModel.from_pretrained(
    "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice",
    device_map="cpu",
    torch_dtype=torch.float32,
)
print(f"Model loaded. Speakers supported by generate_custom_voice:")
import inspect
src = inspect.getsource(m.generate_custom_voice)
# Find supported speakers from validation
for line in src.split('\n'):
    if 'Supported:' in line or 'supported' in line.lower():
        print(line.strip())
