"""
test_model.py — 測試 sherpa-onnx TTS 模型

運行方法：
  uv run python scripts/test_model.py
"""

import sherpa_onnx
import numpy as np
import wave
import os

# 測試路徑（可改為你的實際模型路徑）
MODEL_PATHS = [
    # ttsEngine 現有模型（單發言人）
    "/Users/whypuss/ttsEngine/app/src/main/assets/zhoCN/model.onnx",
    "/Users/whypuss/ttsEngine/app/src/main/assets/zhoCN/tokens.txt",
    "/Users/whypuss/ttsEngine/app/src/main/assets/zhoCN/lexicon.txt",
]

def test_model(model_path: str, tokens_path: str, lexicon_path: str):
    print(f"\n測試模型: {model_path}")

    if not os.path.exists(model_path):
        print(f"  ❌ model.onnx 不存在")
        return

    if not os.path.exists(tokens_path):
        print(f"  ❌ tokens.txt 不存在")
        return

    try:
        config = sherpa_onnx.OfflineTtsConfig(
            model=sherpa_onnx.OfflineTtsModelConfig(
                vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                    model=model_path,
                    lexicon=lexicon_path,
                    tokens=tokens_path,
                )
            )
        )

        tts = sherpa_onnx.OfflineTts(config)
        print(f"  ✅ 加載成功")
        print(f"     採樣率: {tts.sample_rate} Hz")
        print(f"     發言人数: {getattr(tts, 'num_speakers', 1)}")

        # 測試生成
        test_text = "你好，這是一個測試音頻。"
        audio = tts.generate(test_text, sid=0, speed=1.0)

        # 轉為 numpy
        arr = audio.numpy().astype(np.int16)

        out_path = "/tmp/test_output.wav"
        with wave.open(out_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(tts.sample_rate)
            wf.writeframes(arr.tobytes())

        print(f"  ✅ 生成成功: {out_path} ({len(arr)} samples, {len(arr)/tts.sample_rate:.1f}s)")
        return tts

    except Exception as e:
        print(f"  ❌ 失敗: {e}")
        return None


if __name__ == "__main__":
    # 測試現有模型
    m, t, l = MODEL_PATHS
    test_model(m, t, l)
