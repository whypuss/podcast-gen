"""
tts_engine.py — Sherpa-ONNX TTS 引擎封裝

支援：
  - 多發言人 VITS 模型（male / female speaker_id）
  - 普通話 + 粵語
  - 本地 ONNX 推理，無 API
"""

import os
import logging
import sherpa_onnx
import numpy as np
import wave
from pathlib import Path
from typing import Literal

log = logging.getLogger(__name__)


class TTSEngine:
    """
    Sherpa-ONNX TTS 引擎包裝。

    模型目錄結構：
      models/
        model.onnx       # VITS ONNX 模型
        tokens.txt       # token 表
        lexicon.txt      # 發音詞典（可選）
    """

    def __init__(
        self,
        model_dir: str | Path = "models",
        male_speaker: int = 0,
        female_speaker: int = 1,
    ):
        self.model_dir = Path(model_dir)
        self.male_speaker = male_speaker
        self.female_speaker = female_speaker
        self._tts = None
        self._loaded = False
        self._num_speakers = 1

    def load(self) -> bool:
        """初始化 Sherpa-ONNX TTS"""
        model_path = self.model_dir / "model.onnx"
        tokens_path = self.model_dir / "tokens.txt"
        lexicon_path = self.model_dir / "lexicon.txt"

        if not model_path.exists():
            log.error(f"[TTSEngine] model.onnx 未找到: {model_path}")
            return False

        if not tokens_path.exists():
            log.error(f"[TTSEngine] tokens.txt 未找到: {tokens_path}")
            return False

        try:
            log.info("[TTSEngine] 初始化 Sherpa-ONNX...")

            # 構造 VITS 模型配置
            model_cfg = sherpa_onnx.OfflineTtsVitsModelConfig(
                model=str(model_path),
                tokens=str(tokens_path),
                lexicon=str(lexicon_path) if lexicon_path.exists() else "",
            )

            tts_model_cfg = sherpa_onnx.OfflineTtsModelConfig(vits=model_cfg)
            config = sherpa_onnx.OfflineTtsConfig(model=tts_model_cfg)

            self._tts = sherpa_onnx.OfflineTts(config)
            self._num_speakers = getattr(self._tts, "num_speakers", 1)
            self._loaded = True

            log.info(
                f"[TTSEngine] ✅ 加載成功！"
                f" 採樣率={self._tts.sample_rate}Hz, "
                f" 發言人数={self._num_speakers},"
                f" male_sid={self.male_speaker}, female_sid={self.female_speaker}"
            )
            return True

        except Exception as e:
            log.error(f"[TTSEngine] ❌ 加載失敗: {e}")
            self._loaded = False
            return False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def sample_rate(self) -> int:
        if self._tts:
            return self._tts.sample_rate
        return 44100

    @property
    def num_speakers(self) -> int:
        return self._num_speakers

    def generate(
        self,
        text: str,
        speaker: Literal["male", "female"] = "male",
        speed: float = 1.0,
    ) -> np.ndarray | None:
        """
        生成單段音頻。

        Args:
            text:     要合成嘅文字
            speaker:   "male" 或 "female"
            speed:    語速倍率（預設 1.0）

        Returns:
            numpy int16 array，或 None（失敗）
        """
        if not self._loaded:
            log.error("[TTSEngine] 引擎未加載，請先調用 load()")
            return None

        # 單發言人模型：忽略 speaker 參數
        sid = self.male_speaker if self._num_speakers > 1 else 0
        if self._num_speakers > 1:
            sid = self.male_speaker if speaker == "male" else self.female_speaker
            sid = min(sid, self._num_speakers - 1)

        try:
            audio = self._tts.generate(text, sid=sid, speed=speed)

            # sherpa-onnx 回傳 GeneratedAudio，需要轉 numpy
            if hasattr(audio, "numpy"):
                samples = audio.numpy().astype(np.int16)
            elif hasattr(audio, "to_ndarray"):
                samples = audio.to_ndarray().astype(np.int16)
            else:
                log.error(f"[TTSEngine] 無法轉換音頻格式: {type(audio)}")
                return None

            log.debug(
                f"[TTSEngine] 生成 {len(samples)} 採樣 "
                f"(speaker={speaker}, sid={sid}, speed={speed}): {text[:30]}..."
            )
            return samples

        except Exception as e:
            log.error(f"[TTSEngine] 生成失敗: {e}")
            return None

    def generate_to_file(
        self,
        text: str,
        output_path: str | Path,
        speaker: Literal["male", "female"] = "male",
        speed: float = 1.0,
    ) -> bool:
        """生成並直接保存為 WAV 文件"""
        samples = self.generate(text, speaker=speaker, speed=speed)
        if samples is None:
            return False

        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with wave.open(str(output_path), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self.sample_rate)
                wf.writeframes(samples.tobytes())

            log.debug(f"[TTSEngine] 保存: {output_path}")
            return True

        except Exception as e:
            log.error(f"[TTSEngine] 保存失敗: {e}")
            return False


# 全域實例（lazy load）
_engine: TTSEngine | None = None


def get_engine(
    model_dir: str | Path = "models",
    male_speaker: int = 0,
    female_speaker: int = 1,
) -> TTSEngine:
    global _engine
    if _engine is None:
        _engine = TTSEngine(model_dir, male_speaker, female_speaker)
        _engine.load()
    return _engine
