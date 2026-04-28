"""
audio_merger.py — FFmpeg 合併音頻片段

功能：
  - 接收多個 WAV 片段路徑
  - 加入間距（silence padding）
  - 合併為單一 MP3/WAV 文件
  - 可選加載背景音樂（BGM）
"""

import subprocess
import logging
import uuid
import wave
from pathlib import Path
from typing import Literal
import numpy as np

log = logging.getLogger(__name__)

TEMP_DIR = Path("/tmp/podcast-gen")
TEMP_DIR.mkdir(exist_ok=True, parents=True)

OUTPUT_SAMPLE_RATE = 44100
OUTPUT_CHANNELS = 2


def merge_wav_segments(
    segment_paths: list[str | Path],
    output_path: str | Path,
    gap_seconds: float = 0.3,
    bgm_path: str | Path | None = None,
    bgm_volume: float = 0.15,
    output_format: Literal["mp3", "wav"] = "mp3",
) -> bool:
    """
    合併多個 WAV 片段為一個音頻文件（44.1kHz stereo）。

    流程：
    1. 每個片段轉換為 44.1kHz stereo PCM S16LE WAV
    2. 生成 44.1kHz stereo 靜音段
    3. 拼接：segment + silence + segment + silence + ...
    4. 如果有 BGM，混合人聲和 BGM
    5. 輸出 MP3 或 WAV
    """
    if not segment_paths:
        log.error("[AudioMerger] 沒有片段可合併")
        return False

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    valid_paths = [Path(p) for p in segment_paths if Path(p).exists()]
    if not valid_paths:
        log.error("[AudioMerger] 沒有有效片段")
        return False

    job_id = uuid.uuid4().hex[:8]
    normalized_dir = TEMP_DIR / f"norm_{job_id}"
    normalized_dir.mkdir(exist_ok=True)

    try:
        # Step 1: 標準化每個片段（轉為 44100Hz stereo PCM S16LE）
        normalized_paths = []
        for i, p in enumerate(valid_paths):
            norm_path = normalized_dir / f"seg_{i:03d}.wav"
            ok = _convert_to_standard(str(p), str(norm_path))
            if ok:
                normalized_paths.append(norm_path)
            else:
                log.warning(f"[AudioMerger] 片段標準化失敗: {p}")

        if not normalized_paths:
            log.error("[AudioMerger] 所有片段標準化失敗")
            return False

        # Step 2: 生成靜音段
        silence_wav = normalized_dir / "silence.wav"
        _make_silence_wav(gap_seconds, str(silence_wav))

        # Step 3: 構建 concat 輸入文件（segment + silence + segment + ...）
        concat_txt = normalized_dir / "concat.txt"
        with open(concat_txt, "w", encoding="utf-8") as f:
            for norm_path in normalized_paths:
                f.write(f"file '{norm_path}'\n")
                if gap_seconds > 0:
                    f.write(f"file '{silence_wav}'\n")

        # Step 4: FFmpeg concat → 中間檔
        merged_intermediate = normalized_dir / "merged.wav"
        ok = _ffmpeg_concat(str(concat_txt), str(merged_intermediate))
        if not ok:
            return False

        # Step 5: 如果有 BGM，混合人聲和 BGM
        if bgm_path and Path(bgm_path).exists():
            ok = _mix_with_bgm(
                str(merged_intermediate),
                str(bgm_path),
                str(output_path),
                bgm_volume,
                output_format,
            )
        else:
            ok = _encode_output(
                str(merged_intermediate),
                str(output_path),
                output_format,
            )

        return ok

    except Exception as e:
        log.error(f"[AudioMerger] 合併失敗: {e}")
        return False
    finally:
        # 清理臨時標準化目錄
        import shutil
        if normalized_dir.exists():
            shutil.rmtree(normalized_dir, ignore_errors=True)


def _convert_to_standard(input_path: str, output_path: str) -> bool:
    """用 FFmpeg 將任意格式音頻轉換為 44100Hz stereo PCM S16LE"""
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-ar", "44100",
        "-ac", "2",
        "-codec:a", "pcm_s16le",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        log.warning(f"[_convert_to_standard] FFmpeg 失敗: {result.stderr[-300:]}")
        return False
    return True


def _make_silence_wav(duration: float, output_path: str):
    """用 Python 生成靜音 WAV（44100Hz stereo PCM S16LE）"""
    num_samples = int(OUTPUT_SAMPLE_RATE * duration)
    # 靜音：全零 samples
    silent = np.zeros((num_samples, OUTPUT_CHANNELS), dtype=np.int16)
    with wave.open(output_path, "wb") as wf:
        wf.setnchannels(OUTPUT_CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(OUTPUT_SAMPLE_RATE)
        wf.writeframes(silent.tobytes())


def _ffmpeg_concat(concat_txt: str, output_path: str) -> bool:
    """用 FFmpeg concat demuxer 合併多個音頻檔"""
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_txt,
        "-codec:a", "pcm_s16le",
        output_path,
    ]
    log.info(f"[_ffmpeg_concat] {' '.join(cmd[:6])} ...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        log.error(f"[_ffmpeg_concat] FFmpeg concat 失敗: {result.stderr[-500:]}")
        return False
    log.info(f"[_ffmpeg_concat] ✅ concat 完成: {output_path}")
    return True


def _encode_output(input_path: str, output_path: str, fmt: str) -> bool:
    """將 WAV 編碼為 MP3 或保持 WAV"""
    if fmt == "mp3":
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-codec:a", "libmp3lame",
            "-b:a", "128k",
            output_path,
        ]
    else:
        cmd = ["ffmpeg", "-y", "-i", input_path, output_path]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        log.error(f"[_encode_output] FFmpeg 編碼失敗: {result.stderr[-300:]}")
        return False
    log.info(f"[_encode_output] ✅ 輸出完成: {output_path}")
    return True


def _mix_with_bgm(
    speech_path: str,
    bgm_path: str,
    output_path: str,
    bgm_volume: float,
    fmt: str,
) -> bool:
    """混合人聲和背景音樂"""
    if fmt == "mp3":
        codec = ["-codec:a", "libmp3lame", "-b:a", "128k"]
    else:
        codec = ["-codec:a", "pcm_s16le"]

    w_speech = round((1.0 - bgm_volume) * 1.0, 2)
    w_bgm = round(bgm_volume * 1.0, 2)

    cmd = [
        "ffmpeg", "-y",
        "-i", speech_path,
        "-i", bgm_path,
        "-filter_complex",
        f"[0:a][1:a]amix=inputs=2:duration=longest:dropout_transition=0:weights={w_speech} {w_bgm}[a]",
        "-map", "[a]",
        "-ar", "44100",
        "-ac", "2",
        *codec,
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        log.error(f"[_mix_with_bgm] BGM 混合失敗: {result.stderr[-500:]}")
        return False
    log.info(f"[_mix_with_bgm] ✅ BGM 混合完成: {output_path}")
    return True
