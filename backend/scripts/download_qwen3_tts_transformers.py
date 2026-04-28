#!/usr/bin/env python3
"""
download_qwen3_tts_transformers.py — 用 huggingface-cli 下載 Qwen3 TTS 模型

模型：Qwen/Qwen3-TTS-12Hz-0.6B-Base
大小：model.safetensors ~1.8GB

運行方法：
  huggingface-cli download Qwen/Qwen3-TTS-12Hz-0.6B-Base \
    --local-dir ~/.cache/huggingface/hub/models--Qwen--Qwen3-TTS-12Hz-0.6B-Base

  或用 Python：
  python3 scripts/download_qwen3_tts_transformers.py
"""

import os
import sys

HF_MODEL = "Qwen/Qwen3-TTS-12Hz-0.6B-Base"
CACHE_DIR = os.path.expanduser("~/.cache/huggingface/hub")

print("=" * 60)
print("Qwen3 TTS 模型下載")
print("=" * 60)
print(f"\n模型：{HF_MODEL}")
print(f"大小：~1.8GB")
print(f"快取目錄：{CACHE_DIR}")
print("\n使用方法：")
print(f"  huggingface-cli download {HF_MODEL} --local-dir {CACHE_DIR}/models--Qwen--Qwen3-TTS-12Hz-0.6B-Base")
print()
print("或確認模型已下載後，繼續運行：")
print(f"  python3 -c \"from transformers import AutoModelForCausalLM; print('ok')\"")
