"""
main.py — Podcast Gen FastAPI 後端

接口：
  POST /generate      — 接收腳本，返回生成的音頻文件路徑
  GET  /models/status  — 查看模型加載狀態
  GET  /health         — 健康檢查
"""

import os
import logging
import uuid
import asyncio
import threading
from pathlib import Path
from typing import Optional

import torch

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager

from qwen3_tts_engine import Qwen3TTSEngine, get_engine
from script_parser import parse_script
from audio_merger import merge_wav_segments, TEMP_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """後台執行緒預加載模型，server 啟動後立即接受請求。"""
    def _load():
        try:
            eng = get_engine(device="cpu", dtype=torch.float32)
            log.info(f"[Startup] 模型已就緒: {eng.is_loaded}")
        except Exception as e:
            log.error(f"[Startup] 模型加載失敗: {e}")

    thread = threading.Thread(target=_load, daemon=True)
    thread.start()
    log.info("[Startup] 模型後台加載中，server 已就緒接受請求...")
    yield  # server 在此運行
    # shutdown
    global _engine
    _engine = None


app = FastAPI(title="Podcast Gen API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 全域引擎實例 ────────────────────────────────────────────
OUTPUT_DIR = Path("/tmp/podcast-gen/outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

_engine: Optional[Qwen3TTSEngine] = None

# 語言映射（API language → Qwen3 TTS language）
LANG_MAP = {
    "mandarin": "Chinese",
    "cantonese": "Chinese",
    "english": "English",
    "japanese": "Japanese",
    "korean": "Korean",
    "chinese": "Chinese",
}


def get_tts_engine() -> Qwen3TTSEngine:
    global _engine
    if _engine is None:
        _engine = get_engine(device="cpu", dtype=torch.float32)
        if not _engine.is_loaded:
            raise RuntimeError("Qwen3 TTS 模型加載失敗")
    return _engine


# ── 請求模型 ────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    script: str
    language: str = "mandarin"  # "mandarin"
    speed: float = 1.0
    bgm_path: Optional[str] = None
    bgm_volume: float = 0.15
    # 預設音色（UI 選擇）
    male_voice: str = "uncle_fu"
    female_voice: str = "vivian"


class SegmentResult(BaseModel):
    speaker: str
    text: str
    audio_path: Optional[str]
    success: bool


class GenerateResponse(BaseModel):
    job_id: str
    segments: list[SegmentResult]
    output_path: Optional[str]
    success: bool
    error: Optional[str] = None


# ── 接口 ────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/models/status")
def models_status():
    try:
        eng = get_tts_engine()
        return {
            "engine": "Qwen3-TTS-12Hz-0.6B-CustomVoice",
            "loaded": eng.is_loaded,
            "sample_rate": eng.sample_rate,
            "male_speaker": eng.male_speaker,
            "female_speaker": eng.female_speaker,
            "device": "cpu",
        }
    except Exception as e:
        return {"loaded": False, "error": str(e)}


@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    """
    接收 podcast 腳本，生成分段音頻並合併。
    """
    job_id = uuid.uuid4().hex[:8]
    log.info(f"[Job {job_id}] 開始處理，語言={req.language}")

    try:
        eng = get_tts_engine()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS 引擎初始化失敗: {e}")

    # 解析腳本
    parsed = parse_script(
        req.script,
        default_male_voice=req.male_voice,
        default_female_voice=req.female_voice,
    )
    if not parsed:
        raise HTTPException(status_code=400, detail="腳本解析失敗或為空")

    log.info(f"[Job {job_id}] 解析到 {len(parsed)} 個段落")

    # 粵語 instruct
    lang_key = req.language.lower()
    tone = None
    if lang_key == "cantonese":
        tone = "用標準粵語（廣東話）說話，語氣親切自然"

    # 逐段生成 WAV
    segment_results: list[SegmentResult] = []
    wav_paths: list[Path] = []

    for i, seg in enumerate(parsed):
        out_wav = TEMP_DIR / f"seg_{job_id}_{i:03d}.wav"
        ok = eng.generate_to_file(
            text=seg["text"],
            output_path=out_wav,
            speaker=seg["speaker"],
            voice=seg["voice"],              # 指定音色（如有）
            tone=tone,
            language=LANG_MAP.get(lang_key, "Chinese"),
            speed=req.speed,
        )
        segment_results.append(
            SegmentResult(
                speaker=seg["speaker"],
                text=seg["text"],
                audio_path=str(out_wav) if ok else None,
                success=ok,
            )
        )
        if ok:
            wav_paths.append(out_wav)

        # 每段之間有短暫延遲，避免資源競爭
        await asyncio.sleep(0.2)

    if not wav_paths:
        return GenerateResponse(
            job_id=job_id,
            segments=segment_results,
            output_path=None,
            success=False,
            error="所有段落生成失敗",
        )

    # 合併音頻（必须在清理分段之前）
    output_file = OUTPUT_DIR / f"podcast_{job_id}.mp3"
    merge_ok = merge_wav_segments(
        segment_paths=wav_paths,
        output_path=output_file,
        bgm_path=req.bgm_path,
        bgm_volume=req.bgm_volume,
        output_format="mp3",
    )

    # 清理臨時分段 WAV
    for p in wav_paths:
        p.unlink(missing_ok=True)

    log.info(f"[Job {job_id}] 完成，輸出={output_file if merge_ok else '失敗'}")

    return GenerateResponse(
        job_id=job_id,
        segments=segment_results,
        output_path=str(output_file) if merge_ok else None,
        success=merge_ok,
        error=None if merge_ok else "合併失敗",
    )


@app.get("/download/{filename}")
def download(filename: str):
    """下載已生成的音頻文件"""
    safe_name = os.path.basename(filename)
    file_path = OUTPUT_DIR / safe_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(
        path=file_path,
        media_type="audio/mpeg",
        filename=safe_name,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765, reload=True)
