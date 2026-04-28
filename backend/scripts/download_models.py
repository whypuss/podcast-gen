#!/usr/bin/env python3
"""
download_models.py — 自動下載 sherpa-onnx TTS 模型

支援的模型：
  1. vits-melo-tts-zh_en  — 普通話 + 英文（多發言人）
  2. vits-cantonese       — 粵語（待確認 HuggingFace 上具體模型名）

用法：
  uv run python scripts/download_models.py
"""

import os
import sys
import urllib.request
from pathlib import Path

# 模型列表（sherpa-onnx 官方 HuggingFace）
MODELS = {
    "vits-melo-tts-zh_en": {
        "repo": "ZhouAndroid/sherpa-onnx-vits-melo-tts-zh_en",
        "files": ["model.onnx", "tokens.txt"],
        "description": "普通話 + 英文，多發言人 VITS",
    },
}

MODEL_DIR = Path(__file__).parent.parent / "backend" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def download_file(hf_path: str, out_path: Path, repo: str):
    """從 HuggingFace Hub 下載文件（不需要 hf_hub）"""
    url = f"https://huggingface.co/{repo}/resolve/main/{hf_path}"
    print(f"  ⬇️  {hf_path}...", end=" ", flush=True)
    try:
        urllib.request.urlretrieve(url, out_path)
        size = out_path.stat().st_size / (1024 * 1024)
        print(f"✅ ({size:.1f} MB)")
    except Exception as e:
        print(f"❌ {e}")
        sys.exit(1)


def main():
    print("=" * 60)
    print("Podcast Gen — 模型下載工具")
    print("=" * 60)
    print(f"\n模型將安裝至: {MODEL_DIR}\n")

    for key, info in MODELS.items():
        print(f"\n📦 {info['description']}")
        print(f"   Repo: {info['repo']}")
        for fname in info["files"]:
            out = MODEL_DIR / fname
            if out.exists():
                print(f"  ⏭️  {fname} 已存在，跳過")
            else:
                download_file(fname, out, info["repo"])

    print(f"\n✅ 模型下載完成！")
    print(f"   模型目錄: {MODEL_DIR}")
    print(f"\n下一步：")
    print(f"  1. 確認 backend/models/ 下有 model.onnx 和 tokens.txt")
    print(f"  2. uv run python backend/main.py 啟動後端")
    print(f"  3. npm run dev 啟動前端")


if __name__ == "__main__":
    main()
