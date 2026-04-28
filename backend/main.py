"""
main.py — Podcast Gen FastAPI 後端

接口：
  POST /generate      — 接收腳本，立即返回 job_id，生成在後台執行
  GET  /jobs/{job_id} — 查詢 job 狀態與結果
  GET  /models/status  — 查看模型加載狀態
  GET  /health         — 健康檢查
"""

import os
import logging
import uuid
import asyncio
import threading
import time
import concurrent.futures
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
    yield
    global _engine
    _engine = None


app = FastAPI(title="Podcast Gen API", version="2.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 全域引擎實例 ────────────────────────────────────────────
OUTPUT_DIR = Path("/tmp/podcast-gen/outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

_engine: Optional[Qwen3TTSEngine] = None

# 語言映射
LANG_MAP = {
    "mandarin":  "Chinese",
    "cantonese": "Chinese",
    "english":   "English",
    "japanese":  "Japanese",
    "korean":    "Korean",
    "chinese":   "Chinese",
}


def get_tts_engine() -> Qwen3TTSEngine:
    global _engine
    if _engine is None:
        _engine = get_engine(device="cpu", dtype=torch.float32)
        if not _engine.is_loaded:
            raise RuntimeError("Qwen3 TTS 模型加載失敗")
    return _engine


# ── Job 佇列（thread-safe）───────────────────────────────────────────

class JobState:
    DONE    = "done"
    RUNNING = "running"
    FAILED  = "failed"

class Job:
    def __init__(self, job_id: str):
        self.id       = job_id
        self.status   = JobState.RUNNING
        self.result   = None
        self.error    = None
        self.created_at = time.time()

_jobs: dict[str, Job] = {}
_jobs_lock = threading.Lock()

# 執行緒池，避免過多並發
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="tts-")


def _run_generate(job_id: str, req_dict: dict):
    """在執行緒池中執行 TTS 生成（blocking）。"""
    job = _jobs.get(job_id)
    if job is None:
        return

    try:
        eng = get_tts_engine()
    except Exception as e:
        job.status = JobState.FAILED
        job.error  = f"TTS 引擎初始化失敗: {e}"
        return

    # 解析腳本
    parsed = parse_script(
        req_dict["script"],
        default_male_voice=req_dict["male_voice"],
        default_female_voice=req_dict["female_voice"],
    )
    if not parsed:
        job.status = JobState.FAILED
        job.error  = "腳本解析失敗或為空"
        return

    log.info(f"[Job {job_id}] 解析到 {len(parsed)} 個段落，開始生成...")

    lang_key = req_dict["language"].lower()
    tone     = None
    if lang_key == "cantonese":
        tone = "用標準粵語（廣東話）說話，語氣親切自然"

    # 逐段生成
    wav_paths = []
    segment_results = []

    for i, seg in enumerate(parsed):
        out_wav = TEMP_DIR / f"seg_{job_id}_{i:03d}.wav"
        ok = eng.generate_to_file(
            text     = seg["text"],
            output_path = out_wav,
            speaker  = seg["speaker"],
            voice    = seg["voice"],
            tone     = tone,
            language = LANG_MAP.get(lang_key, "Chinese"),
            speed    = req_dict["speed"],
        )
        segment_results.append({
            "speaker":    seg["speaker"],
            "text":       seg["text"],
            "audio_path": str(out_wav) if ok else None,
            "success":    ok,
        })
        if ok:
            wav_paths.append(out_wav)

    if not wav_paths:
        job.status = JobState.FAILED
        job.error  = "所有段落生成失敗"
        return

    # 合併
    output_file = OUTPUT_DIR / f"podcast_{job_id}.mp3"
    merge_ok = merge_wav_segments(
        segment_paths = wav_paths,
        output_path  = output_file,
        bgm_path     = req_dict.get("bgm_path"),
        bgm_volume   = req_dict.get("bgm_volume", 0.15),
        output_format = "mp3",
    )

    # 清理臨時分段
    for p in wav_paths:
        p.unlink(missing_ok=True)

    job.result = {
        "job_id":      job_id,
        "segments":    segment_results,
        "output_path": str(output_file) if merge_ok else None,
        "success":     merge_ok,
        "error":       None if merge_ok else "合併失敗",
    }
    job.status = JobState.DONE
    log.info(f"[Job {job_id}] 完成: {'成功' if merge_ok else '失敗'}")


# ── 請求模型 ────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    script:       str
    language:     str  = "mandarin"
    speed:        float = 1.0
    bgm_path:     Optional[str] = None
    bgm_volume:   float = 0.15
    male_voice:   str   = "uncle_fu"
    female_voice: str   = "vivian"


# ── 接口 ────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/models/status")
def models_status():
    try:
        eng = get_tts_engine()
        return {
            "engine":       "Qwen3-TTS-12Hz-0.6B-CustomVoice",
            "loaded":       eng.is_loaded,
            "sample_rate":  eng.sample_rate,
            "male_speaker": eng.male_speaker,
            "female_speaker": eng.female_speaker,
            "device":        "cpu",
        }
    except Exception as e:
        return {"loaded": False, "error": str(e)}


@app.post("/generate")
async def generate(req: GenerateRequest):
    """
    立即返回 job_id，實際生成在後台執行。
    前端輪詢 GET /jobs/{job_id} 直到 status === 'done' 或 'failed'。
    """
    job_id = uuid.uuid4().hex[:8]
    job = Job(job_id)
    with _jobs_lock:
        _jobs[job_id] = job

    req_dict = req.model_dump()

    # 提交到執行緒池（非阻塞）
    _executor.submit(_run_generate, job_id, req_dict)

    return {"job_id": job_id, "status": "running"}


@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    """輪詢介面：前端定期查詢 job 狀態。"""
    with _jobs_lock:
        job = _jobs.get(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Job 不存在")

    if job.status == JobState.RUNNING:
        return {"job_id": job_id, "status": "running"}
    elif job.status == JobState.DONE:
        return {"job_id": job_id, "status": "done", **job.result}
    else:
        return {"job_id": job_id, "status": "failed", "error": job.error}


@app.get("/download/{filename}")
def download(filename: str):
    """下載已生成的音頻文件。"""
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
