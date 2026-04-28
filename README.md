# Podcast Gen — 本地 TTS Podcast 生成器

## 技術棧

| 層面 | 技術 |
|------|------|
| TTS 引擎 | qwen3 tts（本地推理） |
| 後端 | Python FastAPI |
| 前端 | SolidJS + Vite |
| 桌面封裝 | Tauri |
| 音頻處理 | FFmpeg |

## 功能目標

- 輸入 AI 寫嘅 podcast 腳本（帶 [男] [女] 角色標籤）
- 自動分辨角色，分配不同語音性別
- 中文（普通話）+ 粵語 TTS
- 輸出高質量 podcast 音頻（MP3/WAV）

## 腳本格式

```
[男] 你好，我係阿明。
[女] 我係阿紅，今日我哋傾下行山嘅話題。
[男] 好呀，你最近去咗邊度行山？
```

## 項目結構

```
podcast-gen/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── qwen3_tts_engine.py  # Qwen3 TTS 封裝
│   ├── script_parser.py     # 腳本解析（[男][女] 標籤）
│   ├── audio_merger.py      # FFmpeg 合併音頻片段
│   ├── models/              # ONNX 模型文件
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── ScriptEditor.tsx
│   │   │   ├── AudioPlayer.tsx
│   │   │   └── GeneratePanel.tsx
│   │   └── styles/
│   └── vite.config.ts
└── scripts/
    └── download_models.sh   # 模型下載腳本
```

## 運行

```bash
# 後端
cd backend
uv pip install -r requirements.txt
uv run uvicorn main:app --reload --port 8765

# 前端
cd frontend
npm install
npm run dev
```
