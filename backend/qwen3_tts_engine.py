"""
qwen3_tts_engine.py — Qwen3 TTS 引擎封裝（macOS / CPU 版）

使用官方 qwen-tts 套件
模型：Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice

CustomVoice 內建 9 種音色：
  Male Chinese:   Uncle_Fu（沉穩）, Dylan（京腔年輕）, Eric（四川活潑）
  Female Chinese:  Vivian（亮麗年輕）, Serena（溫柔）
  Male English:    Ryan（有節奏）, Aiden（陽光）
  Female Japanese: Ono_Anna
  Female Korean:   Sohee

使用方式：
  engine = Qwen3TTSEngine()
  engine.load()
  audio = engine.generate("你好，這是測試。", speaker="male")  # → Uncle_Fu
  audio = engine.generate("你好，這是測試。", speaker="female") # → Vivian
"""

import os
import logging
from pathlib import Path
from typing import Literal, Optional

import torch
import soundfile as sf
import numpy as np

from qwen_tts import Qwen3TTSModel

log = logging.getLogger(__name__)


# CustomVoice 內建音色映射
MALE_SPEAKERS = ["Uncle_Fu", "Dylan", "Eric"]
FEMALE_SPEAKERS = ["Vivian", "Serena"]

DEFAULT_MALE = "Uncle_Fu"
DEFAULT_FEMALE = "Vivian"

# 預設語氣指令（可疊加在 speaker 音色上）
MALE_TONE = "，用沉穩有力的語氣朗讀。"
FEMALE_TONE = "，用輕快活潑的語氣朗讀。"


class Qwen3TTSEngine:
    """
    Qwen3 TTS 引擎（CustomVoice 版）。

    運行設備：Mac CPU（torch.float32）
    模型：Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice
    """

    MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"

    def __init__(
        self,
        cache_dir: str | Path | None = None,
        device: str = "cpu",
        dtype: torch.dtype = torch.float32,
        male_speaker: str = DEFAULT_MALE,
        female_speaker: str = DEFAULT_FEMALE,
    ):
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.device = device
        self.dtype = dtype
        self.male_speaker = male_speaker if male_speaker in MALE_SPEAKERS else DEFAULT_MALE
        self.female_speaker = female_speaker if female_speaker in FEMALE_SPEAKERS else DEFAULT_FEMALE

        self._model: Qwen3TTSModel | None = None
        self._loaded = False
        self._sample_rate = 24000

    def load(self) -> bool:
        """下載（如需要）並加載 Qwen3 TTS CustomVoice 模型"""
        try:
            log.info(f"[Qwen3TTS] 加載模型：{self.MODEL_ID}")
            log.info(f"[Qwen3TTS] 設備：{self.device}，dtype：{self.dtype}")

            model_kwargs: dict = {
                "device_map": self.device,
                "dtype": self.dtype,
            }
            if self.device.startswith("cuda"):
                model_kwargs["attn_implementation"] = "flash_attention_2"

            self._model = Qwen3TTSModel.from_pretrained(
                self.MODEL_ID,
                cache_dir=str(self.cache_dir) if self.cache_dir else None,
                **model_kwargs,
            )
            self._loaded = True
            log.info(f"[Qwen3TTS] ✅ 加載成功！")
            log.info(f"[Qwen3TTS]   Male speaker:   {self.male_speaker}")
            log.info(f"[Qwen3TTS]   Female speaker: {self.female_speaker}")
            return True

        except Exception as e:
            log.error(f"[Qwen3TTS] ❌ 加載失敗: {e}")
            self._loaded = False
            return False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    def generate(
        self,
        text: str,
        speaker: Literal["male", "female"] = "male",
        voice: str | None = None,
        tone: str | None = None,
        language: str = "Chinese",
        speed: float = 1.0,
    ) -> np.ndarray | None:
        """
        生成語音。

        Args:
            text:     要合成嘅文字
            speaker:  "male" 或 "female"（決定音色族群）
            voice:    指定音色名（如 "uncle_fu", "dylan", "vivian"），
                      為 None 時使用 speaker 對應的預設音色
            tone:    額外語氣指令（可選），如 "用開心的語氣"
            language: 語言（"Chinese", "English"...）
            speed:   語速倍率（目前內部未完全支援，設為 1.0）

        Returns:
            numpy array (float32, mono)，或 None
        """
        if not self._loaded:
            log.error("[Qwen3TTS] 模型未加載")
            return None

        # voice 參數優先，否則用 speaker 對應預設
        if voice:
            speaker_name = voice
        else:
            speaker_name = self.male_speaker if speaker == "male" else self.female_speaker

        # 組裝 instruct
        instruct = tone if tone else (MALE_TONE if speaker == "male" else FEMALE_TONE)

        try:
            wavs, sr = self._model.generate_custom_voice(
                text=text,
                speaker=speaker_name,
                language=language,
                instruct=instruct,
                non_streaming_mode=True,
            )
            self._sample_rate = sr
            audio = np.array(wavs[0], dtype=np.float32)
            log.debug(
                f"[Qwen3TTS] 生成 {len(audio)} samples "
                f"({len(audio)/sr:.1f}s, voice={speaker_name}): {text[:30]}..."
            )
            return audio

        except Exception as e:
            log.error(f"[Qwen3TTS] 生成失敗: {e}")
            return None

    def generate_to_file(
        self,
        text: str,
        output_path: str | Path,
        speaker: Literal["male", "female"] = "male",
        voice: str | None = None,
        tone: str | None = None,
        language: str = "Chinese",
        speed: float = 1.0,
    ) -> bool:
        """生成並保存為 WAV 文件（24kHz mono）"""
        audio = self.generate(text, speaker=speaker, tone=tone, language=language, speed=speed)
        if audio is None:
            return False

        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            sf.write(str(output_path), audio, self._sample_rate)
            log.debug(f"[Qwen3TTS] 保存: {output_path}")
            return True
        except Exception as e:
            log.error(f"[Qwen3TTS] 保存失敗: {e}")
            return False


# ── 全域實例（lazy load）─────────────────────────────────────────────

_engine: Qwen3TTSEngine | None = None


def get_engine(
    cache_dir: str | Path | None = None,
    device: str = "cpu",
    dtype=torch.float32,
    male_speaker: str = DEFAULT_MALE,
    female_speaker: str = DEFAULT_FEMALE,
) -> Qwen3TTSEngine:
    global _engine
    if _engine is None:
        _engine = Qwen3TTSEngine(
            cache_dir=cache_dir,
            device=device,
            dtype=dtype,
            male_speaker=male_speaker,
            female_speaker=female_speaker,
        )
        _engine.load()
    return _engine
