#!/usr/bin/env python3
"""test_qwen3_api.py"""
import inspect
from qwen_tts import Qwen3TTSModel

for name in dir(Qwen3TTSModel):
    if 'generate' in name or 'clone' in name or 'design' in name or 'voice' in name:
        attr = getattr(Qwen3TTSModel, name)
        if callable(attr):
            try:
                sig = inspect.signature(attr)
                print(f"{name}{sig}")
            except:
                pass
