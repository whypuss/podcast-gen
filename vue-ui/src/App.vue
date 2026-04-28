<script setup lang="ts">
import { ref, computed } from 'vue'

const API_BASE = 'http://100.77.249.63:5174'

// ── 音色定義 ────────────────────────────────────────────────────────────────
const MALE_VOICES = [
  { id: 'uncle_fu', label: 'Uncle Fu — 沉穩大叔' },
  { id: 'dylan',    label: 'Dylan — 京腔青年' },
  { id: 'eric',     label: 'Eric — 活潑四川' },
]

const FEMALE_VOICES = [
  { id: 'vivian',   label: 'Vivian — 亮麗女聲' },
  { id: 'serena',   label: 'Serena — 溫柔女生' },
  { id: 'ono_anna', label: 'Ono Anna — 日語女聲' },
]

// ── 預設腳本 ────────────────────────────────────────────────────────────────
const SAMPLE_SCRIPT = `[男] 大家好，歡迎收聽今天的 Podcast。
[女] 你好！今天我們來聊聊旅遊話題。
[男] 最近我去了一趟日本東京，行程非常充實。
[女] 東京呀！我也想去的，有什麼必去的地方推薦嗎？`

// ── 狀態 ───────────────────────────────────────────────────────────────────
const script      = ref(SAMPLE_SCRIPT)
const maleVoice   = ref('uncle_fu')
const femaleVoice = ref('vivian')
const language    = ref('mandarin')
const speed       = ref(1.0)
const loading     = ref(false)
const modelReady  = ref<boolean | null>(null)  // null = checking
const modelError  = ref('')
const result      = ref<any>(null)

// ── 計算 ───────────────────────────────────────────────────────────────────
const audioUrl = computed(() => {
  if (!result.value?.output_path) return null
  const fname = result.value.output_path.split('/').pop()
  return `${API_BASE}/download/${fname}`
})

// ── 發音性別說明文字 ──────────────────────────────────────────────────────
function voiceOf(seg: any) {
  if (seg.speaker === 'male') {
    const v = MALE_VOICES.find(v => v.id === seg.voice)
    return v ? v.label : seg.voice
  } else {
    const v = FEMALE_VOICES.find(v => v.id === seg.voice)
    return v ? v.label : seg.voice
  }
}

// ── 鉤子 ───────────────────────────────────────────────────────────────────
async function checkModel() {
  try {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 8000)
    const r = await fetch(`${API_BASE}/models/status`, { signal: controller.signal })
    clearTimeout(timeout)
    const text = await r.text()
    console.log('[API] /models/status status:', r.status, 'body:', text.slice(0, 200))
    const d = JSON.parse(text)
    modelReady.value = d.loaded
    modelError.value = d.error || ''
  } catch (e: any) {
    console.error('[API] /models/status error:', e)
    modelReady.value = false
    if (e.name === 'AbortError') {
      modelError.value = '請求超時，請檢查網絡連接'
    } else {
      modelError.value = '無法連接後端：' + (e.message || String(e))
    }
  }
}

checkModel()

// ── 生成 ───────────────────────────────────────────────────────────────────
async function generate() {
  loading.value = true
  result.value = null
  try {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 120000) // 2min for TTS
    const r = await fetch(`${API_BASE}/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        script:        script.value,
        language:      language.value,
        speed:         speed.value,
        male_voice:    maleVoice.value,
        female_voice:  femaleVoice.value,
      }),
      signal: controller.signal,
    })
    clearTimeout(timeout)
    const text = await r.text()
    console.log('[API] /generate status:', r.status, 'body:', text.slice(0, 300))
    result.value = JSON.parse(text)
  } catch (e: any) {
    console.error('[API] /generate error:', e)
    result.value = { success: false, error: e?.message || '請求失敗' }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="app">
    <!-- Header -->
    <header class="header">
      <div class="header-inner">
        <h1 class="title">🎙️ Podcast Gen</h1>
        <p class="subtitle">Qwen3-TTS · 中文普通話 / 粵語 · 多音色選擇</p>
      </div>
    </header>

    <!-- Model Status -->
    <div class="status-bar">
      <span v-if="modelReady === true" class="status-ok">✅ TTS 模型已就緒</span>
      <span v-else-if="modelReady === false" class="status-err">⚠️ {{ modelError || '模型載入中...' }}</span>
      <span v-else class="status-check">🔄 連接中...</span>
    </div>

    <!-- Main Layout -->
    <main class="main">
      <!-- 左欄：編輯器 -->
      <section class="panel panel-left">
        <label class="label">📝 Podcast 腳本</label>
        <textarea
          v-model="script"
          class="textarea"
          rows="16"
          placeholder="[男] 文字&#10;[女] 文字&#10;&#10;或指定音色：&#10;[男:uncle_fu] 文字&#10;[女:serena] 文字"
          spellcheck="false"
        ></textarea>

        <!-- 格式說明 -->
        <div class="format-guide">
          <div class="format-title">📖 腳本格式說明</div>
          <table class="format-table">
            <thead>
              <tr><th>格式</th><th>說明</th></tr>
            </thead>
            <tbody>
              <tr>
                <td><code>[男]</code></td>
                <td>男生說話（使用左側選擇的男聲）</td>
              </tr>
              <tr>
                <td><code>[男:音色名]</code></td>
                <td>指定某位男生音色，如 <code>[男:dylan]</code></td>
              </tr>
              <tr>
                <td><code>[女]</code></td>
                <td>女生說話（使用左側選擇的女聲）</td>
              </tr>
              <tr>
                <td><code>[女:音色名]</code></td>
                <td>指定某位女生音色，如 <code>[女:serena]</code></td>
              </tr>
            </tbody>
          </table>

          <div class="voice-ref">
            <div class="voice-ref-title">🎤 可用音色參考</div>
            <div class="voice-group">
              <span class="voice-tag tag-m">男聲</span>
              <code>uncle_fu</code> 沉穩大叔 ·
              <code>dylan</code> 京腔青年 ·
              <code>eric</code> 活潑四川
            </div>
            <div class="voice-group">
              <span class="voice-tag tag-f">女聲</span>
              <code>vivian</code> 亮麗女聲 ·
              <code>serena</code> 溫柔女生 ·
              <code>ono_anna</code> 日語女聲
            </div>
          </div>
        </div>
      </section>

      <!-- 右欄：設定 -->
      <section class="panel panel-right">
        <!-- 音色選擇 -->
        <div class="voice-section">
          <div class="voice-col">
            <label class="label">👨 男聲</label>
            <div class="voice-cards">
              <label
                v-for="v in MALE_VOICES"
                :key="v.id"
                class="voice-card"
                :class="{ active: maleVoice === v.id }"
              >
                <input type="radio" :value="v.id" v-model="maleVoice" class="hidden-radio" />
                <span class="voice-icon">🎙️</span>
                <span class="voice-name">{{ v.label.split(' — ')[0] }}</span>
                <span class="voice-desc">{{ v.label.split(' — ')[1] }}</span>
              </label>
            </div>
          </div>

          <div class="voice-col">
            <label class="label">👩 女聲</label>
            <div class="voice-cards">
              <label
                v-for="v in FEMALE_VOICES"
                :key="v.id"
                class="voice-card"
                :class="{ active: femaleVoice === v.id }"
              >
                <input type="radio" :value="v.id" v-model="femaleVoice" class="hidden-radio" />
                <span class="voice-icon">🎙️</span>
                <span class="voice-name">{{ v.label.split(' — ')[0] }}</span>
                <span class="voice-desc">{{ v.label.split(' — ')[1] }}</span>
              </label>
            </div>
          </div>
        </div>

        <!-- 控制項 -->
        <div class="controls">
          <label class="control-item">
            <span class="control-label">🌐 語言</span>
            <select v-model="language" class="select">
              <option value="mandarin">普通話</option>
              <option value="cantonese">粵語</option>
            </select>
          </label>

          <label class="control-item">
            <span class="control-label">⏱️ 語速 {{ speed.toFixed(1) }}x</span>
            <input
              type="range"
              min="0.5"
              max="2.0"
              step="0.1"
              v-model.number="speed"
              class="range"
            />
          </label>

          <button
            class="btn-generate"
            :disabled="loading || modelReady !== true"
            @click="generate"
          >
            <span v-if="loading">🔄 生成中...</span>
            <span v-else>🎙️ 生成 Podcast</span>
          </button>
        </div>

        <!-- 結果 -->
        <div v-if="result" class="result-area">
          <div class="result-header">
            <span :class="result.success ? 'badge badge-ok' : 'badge badge-err'">
              {{ result.success ? '✅ 成功' : '❌ 失敗' }}
            </span>
            <span class="job-id">Job #{{ result.job_id }}</span>
          </div>

          <!-- 錯誤 -->
          <div v-if="result.error" class="error-box">{{ result.error }}</div>

          <!-- 完整音頻 -->
          <div v-if="result.output_path" class="audio-section">
            <label class="label">🎧 完整 Podcast</label>
            <audio :src="audioUrl!" controls class="audio-player"></audio>
            <a :href="audioUrl!" download class="download-btn">⬇️ 下載 MP3</a>
          </div>

          <!-- 分段列表 -->
          <div class="segments">
            <label class="label">📋 分段結果 ({{ result.segments?.length ?? 0 }} 段)</label>
            <div
              v-for="(seg, i) in result.segments"
              :key="i"
              class="seg-item"
              :style="{ borderLeft: seg.speaker === 'male' ? '3px solid #4a9eff' : '3px solid #ff6b9d' }"
            >
              <span class="seg-speaker">{{ seg.speaker === 'male' ? '👨' : '👩' }}</span>
              <span class="seg-voice">({{ voiceOf(seg) }})</span>
              <span class="seg-text">{{ seg.text }}</span>
              <span v-if="!seg.success" class="seg-fail">❌</span>
              <a
                v-else
                :href="`${API_BASE}/download/${seg.audio_path?.split('/').pop()}`"
                target="_blank"
                class="seg-play"
              >▶</a>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<style>
/* ── Reset & Base ──────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

.app {
  font-family: system-ui, -apple-system, sans-serif;
  background: #0f1117;
  color: #e0e0e0;
  min-height: 100vh;
}

/* ── Header ─────────────────────────────────────────────────────── */
.header {
  background: #1a1d27;
  border-bottom: 1px solid #2a2d3a;
  padding: 20px 32px;
}
.header-inner { max-width: 1400px; margin: 0 auto; }
.title { font-size: 22px; font-weight: 700; color: #fff; }
.subtitle { font-size: 13px; color: #888; margin-top: 2px; }

/* ── Status Bar ────────────────────────────────────────────────── */
.status-bar {
  padding: 10px 32px;
  background: #1a1d27;
  border-bottom: 1px solid #2a2d3a;
  font-size: 13px;
}
.status-ok  { color: #4ade80; }
.status-err { color: #f97316; }
.status-check { color: #60a5fa; }

/* ── Main Layout ───────────────────────────────────────────────── */
.main {
  display: grid;
  grid-template-columns: 1fr 1fr;
  max-width: 1400px;
  margin: 0 auto;
  min-height: calc(100vh - 120px);
}

/* ── Panels ─────────────────────────────────────────────────────── */
.panel { padding: 24px 28px; }
.panel-left { border-right: 1px solid #2a2d3a; }
.panel-right { background: #13151f; }

/* ── Labels ─────────────────────────────────────────────────────── */
.label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #aaa;
  margin-bottom: 8px;
  margin-top: 16px;
}

/* ── Textarea ──────────────────────────────────────────────────── */
.textarea {
  width: 100%;
  background: #1a1d27;
  border: 1px solid #2a2d3a;
  border-radius: 8px;
  color: #e0e0e0;
  font-size: 14px;
  font-family: monospace;
  padding: 12px;
  resize: vertical;
  outline: none;
  line-height: 1.6;
}
.textarea:focus { border-color: #4a9eff; }

/* ── Format Guide ──────────────────────────────────────────────── */
.format-guide {
  margin-top: 16px;
  background: #1a1d27;
  border: 1px solid #2a2d3a;
  border-radius: 8px;
  padding: 14px;
  font-size: 13px;
}
.format-title { font-weight: 600; color: #aaa; margin-bottom: 10px; }
.format-table { width: 100%; border-collapse: collapse; }
.format-table th, .format-table td {
  text-align: left;
  padding: 5px 8px;
  border-bottom: 1px solid #2a2d3a;
}
.format-table th { color: #888; font-weight: 600; }
.format-table code { color: #4ade80; font-size: 12px; background: #0f1117; padding: 1px 5px; border-radius: 4px; }

.voice-ref { margin-top: 12px; }
.voice-ref-title { font-weight: 600; color: #aaa; margin-bottom: 6px; }
.voice-group { font-size: 12px; color: #888; margin-bottom: 4px; }
.voice-group code { color: #4a9eff; font-size: 11px; background: #0f1117; padding: 1px 4px; border-radius: 3px; }
.voice-tag {
  display: inline-block;
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 10px;
  font-weight: 700;
  margin-right: 4px;
}
.tag-m { background: #1a2a3a; color: #4a9eff; }
.tag-f { background: #2a1a2a; color: #ff6b9d; }

/* ── Voice Cards ───────────────────────────────────────────────── */
.voice-section { display: flex; flex-direction: column; gap: 16px; }
.voice-col { }
.voice-cards { display: flex; flex-direction: column; gap: 6px; }
.voice-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  background: #1a1d27;
  border: 1.5px solid #2a2d3a;
  border-radius: 8px;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}
.voice-card:hover { border-color: #555; background: #20232e; }
.voice-card.active { border-color: #4a9eff; background: #1a2a3e; }
.hidden-radio { display: none; }
.voice-icon { font-size: 16px; }
.voice-name { font-weight: 600; font-size: 13px; min-width: 80px; }
.voice-desc { font-size: 12px; color: #888; }

/* ── Controls ──────────────────────────────────────────────────── */
.controls { display: flex; flex-wrap: wrap; gap: 16px; align-items: center; margin-top: 16px; }
.control-item { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #aaa; }
.control-label { white-space: nowrap; }
.select {
  background: #1a1d27;
  border: 1px solid #2a2d3a;
  border-radius: 6px;
  color: #e0e0e0;
  padding: 4px 8px;
  font-size: 13px;
}
.range { accent-color: #4a9eff; width: 100px; }
.btn-generate {
  background: #4a9eff;
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  padding: 10px 22px;
  cursor: pointer;
  transition: opacity 0.2s;
}
.btn-generate:disabled { opacity: 0.5; cursor: not-allowed; }

/* ── Result Area ──────────────────────────────────────────────── */
.result-area { margin-top: 20px; }
.result-header { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.badge { padding: 4px 10px; border-radius: 20px; font-size: 13px; font-weight: 600; }
.badge-ok  { background: #1a3a2a; color: #4ade80; }
.badge-err { background: #3a1a1a; color: #f87171; }
.job-id { font-size: 12px; color: #666; font-family: monospace; }
.error-box {
  background: #3a1a1a;
  color: #f87171;
  padding: 12px;
  border-radius: 8px;
  font-size: 13px;
  margin-bottom: 12px;
}
.audio-section { margin-bottom: 12px; }
.audio-player { width: 100%; height: 40px; margin-top: 4px; }
.download-btn {
  display: inline-block;
  background: #4ade80;
  color: #000;
  padding: 6px 14px;
  border-radius: 6px;
  text-decoration: none;
  font-size: 13px;
  font-weight: 600;
  margin-top: 6px;
}
.segments { margin-top: 8px; }
.seg-item {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 8px 12px;
  background: #1a1d27;
  border-radius: 6px;
  margin-bottom: 5px;
  font-size: 13px;
}
.seg-speaker { font-weight: 600; min-width: 24px; }
.seg-voice { font-size: 11px; color: #888; min-width: 100px; }
.seg-text { flex: 1; color: #ccc; }
.seg-fail { font-size: 12px; }
.seg-play { font-size: 12px; text-decoration: none; padding: 2px 6px; }
</style>
