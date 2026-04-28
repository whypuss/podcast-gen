"""
script_parser.py — 解析 podcast 腳本，分離發言人 + 音色標籤

格式：
  [男] 你好，我係阿明。                    → 男默認音色
  [男:uncle_fu] 你好，我係阿明。           → 指定 uncle_fu
  [女] 我係阿紅。                          → 女默認音色
  [女:serena] 我係阿紅。                   → 指定 serena

輸出：
  [
    {"speaker": "male",   "voice": "uncle_fu", "text": "你好，我係阿明。"},
    {"speaker": "female", "voice": "serena",   "text": "我係阿紅。"},
  ]
"""

import re
from typing import Literal

Segment = dict  # {"speaker": "male"|"female", "voice": str, "text": str}

# Qwen3 CustomVoice 音色（用於校驗）
MALE_VOICES   = {"uncle_fu", "dylan", "eric"}
FEMALE_VOICES = {"vivian", "serena", "ono_anna"}

# 預設音色
DEFAULT_MALE_VOICE   = "uncle_fu"
DEFAULT_FEMALE_VOICE = "vivian"

# 標籤關鍵字
MALE_KEYWORDS   = {"男", "m", "male", "man", "boy"}
FEMALE_KEYWORDS = {"女", "f", "female", "woman", "girl"}


def parse_script(
    script: str,
    default_male_voice: str = DEFAULT_MALE_VOICE,
    default_female_voice: str = DEFAULT_FEMALE_VOICE,
) -> list[Segment]:
    """
    解析 podcast 腳本，返回段落列表。

    支援標籤格式：
      [男]           → male, 預設音色
      [男:uncle_fu]  → male, 指定音色
      [女]           → female, 預設音色
      [女:serena]    → female, 指定音色
      [M] [F] [Male] [Female] → 同上

    無標籤的段落預設為 male。
    """
    lines = script.strip().split("\n")
    segments: list[Segment] = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 匹配 [tag] 或 [tag:voice] 開頭的段落
        pattern = r"^\[([^\]:]+)(?::([^\]]+))?\]\s*(.*)$"
        match = re.match(pattern, line, re.IGNORECASE)

        if match:
            tag   = match.group(1).strip().lower()
            voice = match.group(2)
            text  = match.group(3).strip() if match.group(3) else ""
        else:
            tag   = ""
            voice = None
            text  = line

        speaker, detected_voice = _detect_speaker_and_voice(tag, voice)
        if speaker == "male":
            used_voice = detected_voice or default_male_voice
        else:
            used_voice = detected_voice or default_female_voice

        if text:
            segments.append({
                "speaker": speaker,
                "voice":   used_voice,
                "text":    text,
            })

    return segments


def _detect_speaker_and_voice(
    tag: str,
    voice: str | None,
) -> tuple[Literal["male", "female"], str | None]:
    """
    根據 tag 關鍵字判定 speaker，
    voice 參數優先，否則根據 speaker 返回 None（使用預設）。
    """
    # voice 參數直接校驗
    if voice:
        v = voice.strip().lower()
        if v in MALE_VOICES:
            return ("male", v)
        if v in FEMALE_VOICES:
            return ("female", v)
        # 無效音色名，忽略
        voice = None

    # tag 關鍵字判定 speaker
    tag_lower = tag.lower()
    if tag_lower in MALE_KEYWORDS:
        return ("male", voice)
    if tag_lower in FEMALE_KEYWORDS:
        return ("female", voice)

    # 部分匹配
    if any(k in tag_lower for k in MALE_KEYWORDS):
        return ("male", voice)
    if any(k in tag_lower for k in FEMALE_KEYWORDS):
        return ("female", voice)

    # 無法判定 → male
    return ("male", voice)
