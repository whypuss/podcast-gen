#!/usr/bin/env python3
"""
download_qwen3_tts.py — 下載 Qwen3-TTS GGUF 模型

模型來源：OpenVoiceOS/qwen3-tts-0.6b-q4-k-m
- qwen3-tts-0.6b-q4-k-m.gguf        ~509 MB（主模型，Q4-K-M 量化）
- qwen3-tts-tokenizer-0.6b-q4-k-m.gguf  ~193 MB（Tokenizer）

運行方法：
  python3 scripts/download_qwen3_tts.py
"""

import urllib.request
import os
from pathlib import Path

MODEL_DIR = Path(__file__).parent.parent / "models" / "qwen3-tts"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODELS = [
    ("qwen3-tts-0.6b-q4-k-m.gguf", "OpenVoiceOS/qwen3-tts-0.6b-q4-k-m"),
    ("qwen3-tts-tokenizer-0.6b-q4-k-m.gguf", "OpenVoiceOS/qwen3-tts-0.6b-q4-k-m"),
]


def download_file(repo: str, out_path: Path):
    url = f"https://huggingface.co/{repo}/resolve/main/{out_path.name}"
    print(f"  ⬇️  {url}")
    print(f"     → {out_path}  ...", end=" ", flush=True)
    try:
        urllib.request.urlretrieve(url, out_path)
        size = out_path.stat().st_size / (1024 * 1024)
        print(f"✅ ({size:.1f} MB)")
    except Exception as e:
        print(f"❌ {e}")
        return False
    return True


def main():
    print("=" * 60)
    print("Qwen3-TTS 模型下載")
    print("=" * 60)
    print(f"\n模型目錄: {MODEL_DIR}\n")

    success = True
    for local_name, repo in MODELS:
        out = MODEL_DIR / local_name
        if out.exists() and out.stat().st_size > 1000:
            print(f"  ⏭️  {local_name} 已存在 ({out.stat().st_size//1024//1024} MB)，跳過")
        else:
            if not download_file(repo, out):
                success = False

    print()
    if success:
        print("✅ 模型下載完成！")
        print(f"\n下一步：")
        print(f"  cd ~/.kimaki/projects/podcast-gen/backend")
        print(f"  python3 -c \"from tts_engine import get_engine; e = get_engine(); print(e.is_loaded)\"")
    else:
        print("❌ 部分模型下載失敗")


if __name__ == "__main__":
    main()
