#!/usr/bin/env python3
"""test_qwen3_support.py"""
from transformers import AutoConfig
import transformers

model_id = "Qwen/Qwen3-TTS-12Hz-0.6B-Base"
print(f"Testing Qwen3 TTS support in transformers {transformers.__version__}...")
try:
    config = AutoConfig.from_pretrained(model_id, trust_remote_code=True)
    print(f"✅ Model type: {config.model_type}")
    print(f"✅ Vocab size: {config.vocab_size}")
except Exception as e:
    print(f"❌ {type(e).__name__}: {e}")
