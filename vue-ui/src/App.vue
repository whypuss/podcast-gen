<script setup lang="ts">
import { ref, computed } from 'vue'

const API_BASE = 'http://100.77.249.63:5174'

// ── 音色定義 ────────────────────────────────────────────────────────────────
const MALE_VOICES = [
  { id: 'uncle_fu', label: 'Uncle Fu', sub: '沉穩大叔' },
  { id: 'dylan',    label: 'Dylan',    sub: '京腔青年' },
  { id: 'eric',     label: 'Eric',     sub: '活潑四川' },
]

const FEMALE_VOICES = [
  { id: 'vivian',   label: 'Vivian',   sub: '亮麗女聲' },
  { id: 'serena',   label: 'Serena',   sub: '溫柔女生' },
  { id: 'ono_anna', label: 'Ono Anna', sub: '日語女聲' },
]

// ── 預設腳本 ────────────────────────────────────────────────────────────────
const SAMPLE_SCRIPT = `[男] 大家好，歡迎收聽今天的 Podcast。
[女] 你好！今天我們來聊聊旅遊話題。
[男] 最近我去了一趟日本東京，行程非常充實。
[女] 東京呀！我也想去的，有什麼必去的地方推薦嗎？`

// ── 狀態 ───────────────────────────────────────────────────────────────────
const script       = ref(SAMPLE_SCRIPT)
const maleVoice    = ref('uncle_fu')
const femaleVoice  = ref('vivian')
const language     = ref('mandarin')
const speed        = ref(1.0)
const loading      = ref(false)
const modelReady   = ref<boolean | null>(null)
const modelError   = ref('')
const result       = ref<any>(null)
const jobId        = ref<string | null>(null)
const pollTimer    = ref<number | null>(null)

// ── 計算 ───────────────────────────────────────────────────────────────────
const audioUrl = computed(() => {
  if (!result.value?.output_path) return null
  const fname = result.value.output_path.split('/').pop()
  return `${API_BASE}/download/${fname}`
})

function voiceOf(seg: any) {
  if (seg.speaker === 'male') {
    return MALE_VOICES.find(v => v.id === seg.voice)?.sub ?? seg.voice
  }
  return FEMALE_VOICES.find(v => v.id === seg.voice)?.sub ?? seg.voice
}

// ── 鉤子 ───────────────────────────────────────────────────────────────────
async function checkModel() {
  try {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 8000)
    const r = await fetch(`${API_BASE}/models/status`, { signal: controller.signal })
    clearTimeout(timeout)
    const d = JSON.parse(await r.text())
    modelReady.value = d.loaded
    modelError.value = d.error || ''
  } catch (e: any) {
    modelReady.value = false
    modelError.value = e.name === 'AbortError' ? '請求超時，請檢查網絡連接' : '無法連接後端'
  }
}
checkModel()

async function generate() {
  loading.value = true
  result.value = null
  jobId.value  = null

  try {
    // Step 1: 立即提交 job
    const submit = await fetch(`${API_BASE}/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        script:       script.value,
        language:     language.value,
        speed:        speed.value,
        male_voice:   maleVoice.value,
        female_voice: femaleVoice.value,
      }),
    })
    const meta = JSON.parse(await submit.text())
    jobId.value = meta.job_id
    if (!jobId.value) throw new Error('無 job_id')

    // Step 2: 輪詢 job 狀態
    const poll = async () => {
      try {
        const r = await fetch(`${API_BASE}/jobs/${jobId.value}`)
        const data = JSON.parse(await r.text())
        if (data.status === 'done') {
          result.value = data
          loading.value = false
          if (pollTimer.value) clearInterval(pollTimer.value)
        } else if (data.status === 'failed') {
          result.value = { success: false, error: data.error }
          loading.value = false
          if (pollTimer.value) clearInterval(pollTimer.value)
        }
        // else: still running, keep polling
      } catch (e) {
        // 輪詢出錯，繼續試
      }
    }

    // 立即查一次，之後每 3 秒
    await poll()
    pollTimer.value = window.setInterval(poll, 3000)

  } catch (e: any) {
    result.value = { success: false, error: e?.message || '提交失敗' }
    loading.value = false
  }
}
</script>

<template>
  <div class="app">

    <!-- Header -->
    <header class="header">
      <div class="header-inner">
        <div class="header-icon">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2a3 3 0 0 1 3 3v7a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3Z"/>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
            <line x1="12" x2="12" y1="19" y2="22"/>
          </svg>
        </div>
        <div>
          <h1 class="title">Podcast Gen</h1>
          <p class="subtitle">Qwen3-TTS · 普通話 / 粵語 · 多音色</p>
        </div>
      </div>
    </header>

    <!-- Model Status -->
    <div class="status-bar">
      <div v-if="modelReady === true" class="status status-ok">
        <span class="dot dot-green"></span> TTS 模型已就緒
      </div>
      <div v-else-if="modelReady === false" class="status status-err">
        <span class="dot dot-orange"></span> {{ modelError || '模型載入中...' }}
      </div>
      <div v-else class="status status-check">
        <span class="dot dot-gray"></span> 連接中...
      </div>
    </div>

    <!-- Main -->
    <main class="main">

      <!-- 左欄：腳本 -->
      <section class="panel panel-left">
        <div class="section-label">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/></svg>
          Podcast 腳本
        </div>
        <textarea
          v-model="script"
          class="textarea"
          rows="10"
          placeholder="[男] 文字&#10;[女] 文字&#10;&#10;或指定音色：&#10;[男:uncle_fu] 文字&#10;[女:serena] 文字"
          spellcheck="false"
        ></textarea>

        <!-- 格式說明 -->
        <details class="format-guide">
          <summary>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
            腳本格式說明
          </summary>
          <div class="guide-body">
            <table class="guide-table">
              <thead><tr><th>格式</th><th>說明</th></tr></thead>
              <tbody>
                <tr><td><code>[男]</code></td><td>男生說話（左側選擇的男聲）</td></tr>
                <tr><td><code>[男:音色名]</code></td><td>指定男聲，如 <code>[男:dylan]</code></td></tr>
                <tr><td><code>[女]</code></td><td>女生說話（左側選擇的女聲）</td></tr>
                <tr><td><code>[女:音色名]</code></td><td>指定女聲，如 <code>[女:serena]</code></td></tr>
              </tbody>
            </table>
            <div class="voice-ref">
              <div class="ref-row">
                <span class="ref-tag tag-m">男</span>
                <code>uncle_fu</code> 沉穩大叔 ·
                <code>dylan</code> 京腔青年 ·
                <code>eric</code> 活潑四川
              </div>
              <div class="ref-row">
                <span class="ref-tag tag-f">女</span>
                <code>vivian</code> 亮麗女聲 ·
                <code>serena</code> 溫柔女生 ·
                <code>ono_anna</code> 日語女聲
              </div>
            </div>
          </div>
        </details>
      </section>

      <!-- 右欄：設定 -->
      <section class="panel panel-right">

        <!-- 男聲選擇 -->
        <div class="voice-group">
          <div class="section-label">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M20 21a8 8 0 1 0-16 0"/></svg>
            男聲
          </div>
          <div class="voice-cards">
            <label
              v-for="v in MALE_VOICES"
              :key="v.id"
              class="voice-card"
              :class="{ active: maleVoice === v.id }"
            >
              <input type="radio" :value="v.id" v-model="maleVoice" class="hidden-radio" />
              <div class="card-icon card-icon-m">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M20 21a8 8 0 1 0-16 0"/></svg>
              </div>
              <div class="card-text">
                <span class="card-name">{{ v.label }}</span>
                <span class="card-sub">{{ v.sub }}</span>
              </div>
              <div v-if="maleVoice === v.id" class="card-check">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
              </div>
            </label>
          </div>
        </div>

        <!-- 女聲選擇 -->
        <div class="voice-group">
          <div class="section-label">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M20 21a8 8 0 1 0-16 0"/></svg>
            女聲
          </div>
          <div class="voice-cards">
            <label
              v-for="v in FEMALE_VOICES"
              :key="v.id"
              class="voice-card"
              :class="{ active: femaleVoice === v.id }"
            >
              <input type="radio" :value="v.id" v-model="femaleVoice" class="hidden-radio" />
              <div class="card-icon card-icon-f">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M20 21a8 8 0 1 0-16 0"/></svg>
              </div>
              <div class="card-text">
                <span class="card-name">{{ v.label }}</span>
                <span class="card-sub">{{ v.sub }}</span>
              </div>
              <div v-if="femaleVoice === v.id" class="card-check">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
              </div>
            </label>
          </div>
        </div>

        <!-- 控制項 -->
        <div class="controls">

          <div class="control-row">
            <label class="control-label">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" x2="22" y1="12" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
              語言
            </label>
            <select v-model="language" class="select">
              <option value="mandarin">普通話</option>
              <option value="cantonese">粵語</option>
            </select>
          </div>

          <div class="control-row">
            <label class="control-label">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              語速 {{ speed.toFixed(1) }}x
            </label>
            <input type="range" min="0.5" max="2.0" step="0.1" v-model.number="speed" class="range" />
          </div>

        </div>

        <!-- 生成按鈕 -->
        <button class="btn-generate" :disabled="loading || modelReady !== true" @click="generate">
          <svg v-if="!loading" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>
          <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="spin"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>
          {{ loading ? '生成中...' : '生成 Podcast' }}
        </button>

        <!-- 結果 -->
        <div v-if="result" class="result-area">

          <div class="result-header">
            <div v-if="result.success" class="badge badge-ok">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
              成功
            </div>
            <div v-else class="badge badge-err">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" x2="6" y1="6" y2="18"/><line x1="6" x2="18" y1="6" y2="18"/></svg>
              失敗
            </div>
            <span class="job-id">Job #{{ result.job_id }}</span>
          </div>

          <div v-if="result.error" class="error-box">{{ result.error }}</div>

          <div v-if="result.output_path" class="audio-block">
            <div class="audio-label">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>
              完整 Podcast
            </div>
            <audio :src="audioUrl!" controls class="audio-player"></audio>
            <a :href="audioUrl!" download class="btn-download">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/></svg>
              下載 MP3
            </a>
          </div>

          <div v-if="result.segments?.length" class="segments-block">
            <div class="audio-label">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" x2="21" y1="6" y2="6"/><line x1="8" x2="21" y1="12" y2="12"/><line x1="8" x2="21" y1="18" y2="18"/><line x1="3" x2="3.01" y1="6" y2="6"/><line x1="3" x2="3.01" y1="12" y2="12"/><line x1="3" x2="3.01" y1="18" y2="18"/></svg>
              分段結果 ({{ result.segments.length }} 段)
            </div>
            <div
              v-for="(seg, i) in result.segments"
              :key="i"
              class="seg-item"
              :class="seg.speaker === 'male' ? 'seg-m' : 'seg-f'"
            >
              <div class="seg-meta">
                <div class="seg-avatar" :class="seg.speaker === 'male' ? 'avatar-m' : 'avatar-f'">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M20 21a8 8 0 1 0-16 0"/></svg>
                </div>
                <span class="seg-voice">{{ voiceOf(seg) }}</span>
                <a
                  v-if="seg.success"
                  :href="`${API_BASE}/download/${seg.audio_path?.split('/').pop()}`"
                  target="_blank"
                  class="seg-play"
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                </a>
                <span v-else class="seg-fail">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" x2="9" y1="9" y2="15"/><line x1="9" x2="15" y1="9" y2="15"/></svg>
                </span>
              </div>
              <div class="seg-text">{{ seg.text }}</div>
            </div>
          </div>

        </div>
      </section>
    </main>
  </div>
</template>

<style>
/* ── iOS System Font Variables ─────────────────────────────────────────── */
:root {
  --ios-bg:       #f2f2f7;
  --ios-card:     #ffffff;
  --ios-border:   rgba(0,0,0,0.06);
  --ios-text:     #1c1c1e;
  --ios-text-2:   #3c3c43;
  --ios-text-3:   #8e8e93;
  --ios-blue:     #007aff;
  --ios-green:    #34c759;
  --ios-red:      #ff3b30;
  --ios-orange:   #ff9500;
  --ios-pink:     #ff2d55;
  --ios-purple:   #af52de;
  --ios-shadow:   0 1px 3px rgba(0,0,0,0.08);
  --ios-radius:   12px;
  --ios-radius-sm: 8px;
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'SF Pro Display', sans-serif;
  font-size: 16px;
  color-scheme: light;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

.app {
  background: var(--ios-bg);
  min-height: 100vh;
  color: var(--ios-text);
}

/* ── Header ──────────────────────────────────────────────────────────── */
.header {
  background: var(--ios-card);
  border-bottom: 1px solid var(--ios-border);
  padding: 16px 20px;
  position: sticky;
  top: 0;
  z-index: 10;
}
.header-inner {
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 12px;
}
.header-icon {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, var(--ios-blue), var(--ios-purple));
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}
.title {
  font-size: 20px;
  font-weight: 700;
  color: var(--ios-text);
  letter-spacing: -0.3px;
}
.subtitle {
  font-size: 12px;
  color: var(--ios-text-3);
  margin-top: 1px;
}

/* ── Status Bar ─────────────────────────────────────────────────────── */
.status-bar {
  padding: 10px 20px;
  background: var(--ios-card);
  border-bottom: 1px solid var(--ios-border);
}
.status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}
.dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}
.dot-green  { background: var(--ios-green); }
.dot-orange { background: var(--ios-orange); }
.dot-gray   { background: var(--ios-text-3); }
.status-ok  { color: var(--ios-green); }
.status-err { color: var(--ios-orange); }
.status-check { color: var(--ios-text-3); }

/* ── Main Layout ─────────────────────────────────────────────────────── */
.main {
  display: grid;
  grid-template-columns: 1fr 1fr;
  max-width: 900px;
  margin: 0 auto;
  min-height: calc(100vh - 120px);
}

/* ── Panels ──────────────────────────────────────────────────────────── */
.panel {
  padding: 20px;
}
.panel-left {
  background: var(--ios-bg);
  border-right: 1px solid var(--ios-border);
}
.panel-right {
  background: var(--ios-card);
}

/* ── Section Label ───────────────────────────────────────────────────── */
.section-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--ios-text-2);
  margin-bottom: 10px;
  margin-top: 4px;
  color: var(--ios-text-3);
}
.section-label svg { color: var(--ios-text-3); }

/* ── Textarea ───────────────────────────────────────────────────────── */
.textarea {
  width: 100%;
  background: var(--ios-card);
  border: 1px solid var(--ios-border);
  border-radius: var(--ios-radius);
  color: var(--ios-text);
  font-size: 14px;
  font-family: 'SF Mono', ui-monospace, monospace;
  padding: 12px;
  resize: vertical;
  outline: none;
  line-height: 1.7;
  box-shadow: var(--ios-shadow);
  transition: border-color 0.2s;
}
.textarea:focus {
  border-color: var(--ios-blue);
}

/* ── Format Guide ────────────────────────────────────────────────────── */
.format-guide {
  margin-top: 12px;
  background: var(--ios-card);
  border: 1px solid var(--ios-border);
  border-radius: var(--ios-radius);
  overflow: hidden;
  box-shadow: var(--ios-shadow);
}
.format-guide summary {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 11px 14px;
  font-size: 13px;
  font-weight: 500;
  color: var(--ios-text-3);
  cursor: pointer;
  user-select: none;
  list-style: none;
}
.format-guide summary::-webkit-details-marker { display: none; }
.format-guide summary::after { content: '▶'; font-size: 9px; color: var(--ios-text-3); margin-left: auto; transition: transform 0.2s; }
.format-guide[open] summary::after { transform: rotate(90deg); }
.guide-body { padding: 4px 14px 14px; }
.guide-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.guide-table th, .guide-table td { text-align: left; padding: 5px 4px; border-bottom: 1px solid var(--ios-border); }
.guide-table th { color: var(--ios-text-3); font-weight: 500; }
.guide-table code { color: var(--ios-blue); background: rgba(0,122,255,0.08); padding: 1px 5px; border-radius: 4px; font-size: 11px; }
.voice-ref { margin-top: 10px; }
.ref-row { font-size: 12px; color: var(--ios-text-3); margin-bottom: 4px; }
.ref-row code { color: var(--ios-blue); background: rgba(0,122,255,0.08); padding: 1px 4px; border-radius: 3px; font-size: 11px; }
.ref-tag {
  display: inline-block;
  font-size: 10px;
  font-weight: 600;
  padding: 1px 5px;
  border-radius: 4px;
  margin-right: 4px;
}
.tag-m { background: rgba(0,122,255,0.12); color: var(--ios-blue); }
.tag-f { background: rgba(255,45,85,0.12); color: var(--ios-pink); }

/* ── Voice Cards ─────────────────────────────────────────────────────── */
.voice-group { margin-bottom: 20px; }
.voice-cards { display: flex; flex-direction: column; gap: 6px; }
.voice-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: var(--ios-card);
  border: 1.5px solid var(--ios-border);
  border-radius: var(--ios-radius);
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s;
  box-shadow: var(--ios-shadow);
}
.voice-card:hover { border-color: rgba(0,122,255,0.4); }
.voice-card.active { border-color: var(--ios-blue); background: rgba(0,122,255,0.04); }
.hidden-radio { display: none; }
.card-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.card-icon-m { background: rgba(0,122,255,0.1); color: var(--ios-blue); }
.card-icon-f { background: rgba(255,45,85,0.1); color: var(--ios-pink); }
.card-text { display: flex; flex-direction: column; gap: 1px; flex: 1; }
.card-name { font-size: 14px; font-weight: 600; color: var(--ios-text); }
.card-sub  { font-size: 12px; color: var(--ios-text-3); }
.card-check {
  width: 22px;
  height: 22px;
  background: var(--ios-blue);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

/* ── Controls ───────────────────────────────────────────────────────── */
.controls { display: flex; flex-direction: column; gap: 12px; margin: 16px 0; }
.control-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.control-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 500;
  color: var(--ios-text-2);
  white-space: nowrap;
  color: var(--ios-text-3);
}
.select {
  background: var(--ios-bg);
  border: 1px solid var(--ios-border);
  border-radius: var(--ios-radius-sm);
  color: var(--ios-text);
  padding: 6px 10px;
  font-size: 14px;
  outline: none;
  font-family: inherit;
}
.range {
  flex: 1;
  accent-color: var(--ios-blue);
  height: 4px;
  cursor: pointer;
}

/* ── Generate Button ─────────────────────────────────────────────────── */
.btn-generate {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: var(--ios-blue);
  border: none;
  border-radius: var(--ios-radius);
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  padding: 14px;
  cursor: pointer;
  transition: opacity 0.2s, transform 0.1s;
  font-family: inherit;
  letter-spacing: -0.2px;
}
.btn-generate:active { transform: scale(0.98); }
.btn-generate:disabled { opacity: 0.45; cursor: not-allowed; }
.spin { animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Result ──────────────────────────────────────────────────────────── */
.result-area { margin-top: 20px; }
.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
}
.badge-ok  { background: rgba(52,199,89,0.12); color: var(--ios-green); }
.badge-err { background: rgba(255,59,48,0.12); color: var(--ios-red); }
.job-id { font-size: 12px; color: var(--ios-text-3); font-family: monospace; }
.error-box {
  background: rgba(255,59,48,0.08);
  color: var(--ios-red);
  padding: 12px;
  border-radius: var(--ios-radius);
  font-size: 13px;
  margin-bottom: 12px;
}

/* ── Audio Block ─────────────────────────────────────────────────────── */
.audio-block { margin-bottom: 16px; }
.audio-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--ios-text-3);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.audio-player {
  width: 100%;
  height: 40px;
  border-radius: var(--ios-radius);
  accent-color: var(--ios-blue);
}
.btn-download {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  margin-top: 8px;
  padding: 7px 14px;
  background: var(--ios-bg);
  border: 1px solid var(--ios-border);
  border-radius: var(--ios-radius-sm);
  color: var(--ios-blue);
  font-size: 13px;
  font-weight: 500;
  text-decoration: none;
  transition: background 0.2s;
}
.btn-download:hover { background: rgba(0,122,255,0.06); }

/* ── Segments ────────────────────────────────────────────────────────── */
.segments-block { }
.seg-item {
  background: var(--ios-bg);
  border-radius: var(--ios-radius);
  padding: 10px 12px;
  margin-bottom: 6px;
  border-left: 3px solid transparent;
}
.seg-m { border-left-color: var(--ios-blue); }
.seg-f { border-left-color: var(--ios-pink); }
.seg-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}
.seg-avatar {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.avatar-m { background: rgba(0,122,255,0.12); color: var(--ios-blue); }
.avatar-f { background: rgba(255,45,85,0.12); color: var(--ios-pink); }
.seg-voice { font-size: 12px; color: var(--ios-text-3); flex: 1; }
.seg-play {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: var(--ios-blue);
  color: #fff;
  border-radius: 50%;
  text-decoration: none;
}
.seg-fail { color: var(--ios-red); display: flex; align-items: center; }
.seg-text { font-size: 14px; color: var(--ios-text); line-height: 1.5; }

/* ── Mobile ──────────────────────────────────────────────────────────── */
@media (max-width: 640px) {
  .main { grid-template-columns: 1fr; }
  .panel-left { border-right: none; border-bottom: 1px solid var(--ios-border); }
  .header { padding: 12px 16px; }
  .panel { padding: 16px; }
  .textarea { font-size: 13px; min-height: 140px; }
  .voice-cards { gap: 5px; }
  .btn-generate { padding: 12px; }
}
</style>
