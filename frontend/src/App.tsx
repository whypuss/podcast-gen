import { createSignal, Show, For } from "solid-js";

const API_BASE = "http://localhost:8765";

interface SegmentResult {
  speaker: string;
  text: string;
  audio_path: string | null;
  success: boolean;
}

interface GenerateResponse {
  job_id: string;
  segments: SegmentResult[];
  output_path: string | null;
  success: boolean;
  error: string | null;
}

const SAMPLE_SCRIPT = `[男] 你好，我係阿明，今日我哋傾下行山嘅話題。
[女] 你好阿明！我係阿紅，最近天氣涼爽，真係行山嘅好時機。
[男] 係呀！你最近去咗邊度行山？
[女] 我上星期去咗梧桐寨，行咗麥理浩徑第三段，風景好正。
[男] 聽落都好正喎！下次我一齊去。`;

export default function App() {
  const [script, setScript] = createSignal(SAMPLE_SCRIPT);
  const [language, setLanguage] = createSignal("cantonese");
  const [speed, setSpeed] = createSignal(1.0);
  const [loading, setLoading] = createSignal(false);
  const [result, setResult] = createSignal<GenerateResponse | null>(null);
  const [modelStatus, setModelStatus] = createSignal<{ loaded: boolean; error?: string }>({ loaded: false });
  const [downloading, setDownloading] = createSignal(false);

  // 檢查模型狀態
  async function checkModel() {
    try {
      const r = await fetch(`${API_BASE}/models/status`);
      const data = await r.json();
      setModelStatus({ loaded: data.loaded, error: data.error });
    } catch {
      setModelStatus({ loaded: false, error: "無法連接後端（請確保後端運行中）" });
    }
  }

  // 初次載入時檢查
  checkModel();

  async function handleGenerate() {
    setLoading(true);
    setResult(null);
    try {
      const r = await fetch(`${API_BASE}/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          script: script(),
          language: language(),
          speed: speed(),
        }),
      });
      const data: GenerateResponse = await r.json();
      setResult(data);
    } catch (e: any) {
      setResult({
        job_id: "error",
        segments: [],
        output_path: null,
        success: false,
        error: e?.message || "請求失敗",
      });
    } finally {
      setLoading(false);
    }
  }

  const audioUrl = () => result()?.output_path
    ? `${API_BASE}/download/${result()!.output_path!.split("/").pop()}`
    : null;

  return (
    <div style={styles.root}>
      <header style={styles.header}>
        <h1 style={styles.title}>🎙️ Podcast Gen</h1>
        <p style={styles.subtitle}>本地 TTS · 中文 + 粵語 · 男女聲</p>
      </header>

      {/* 模型狀態 */}
      <div style={styles.statusBar}>
        <Show when={modelStatus().loaded} fallback={
          <span style={styles.statusError}>
            ⚠️ TTS 模型未就緒 — {modelStatus().error || "請先下載模型"}
          </span>
        }>
          <span style={styles.statusOk}>✅ TTS 模型已就緒</span>
        </Show>
      </div>

      <main style={styles.main}>
        {/* 左欄：編輯器 */}
        <section style={styles.editorSection}>
          <label style={styles.label}>📝 Podcast 腳本</label>
          <textarea
            style={styles.textarea}
            value={script()}
            onInput={(e) => setScript(e.currentTarget.value)}
            rows={16}
            placeholder="[男] 文字內容&#10;[女] 文字內容"
            spellcheck={false}
          />
          <div style={styles.hint}>
            格式：<code>[男]</code> 或 <code>[女]</code> 開頭一行，代表發言人
          </div>

          {/* 設定 */}
          <div style={styles.controls}>
            <label style={styles.controlItem}>
              語言：
              <select
                value={language()}
                onChange={(e) => setLanguage(e.currentTarget.value)}
                style={styles.select}
              >
                <option value="cantonese">粵語</option>
                <option value="mandarin">普通話</option>
              </select>
            </label>

            <label style={styles.controlItem}>
              語速：{speed().toFixed(1)}x
              <input
                type="range"
                min="0.5"
                max="2.0"
                step="0.1"
                value={speed()}
                onInput={(e) => setSpeed(parseFloat(e.currentTarget.value))}
                style={styles.range}
              />
            </label>

            <button
              style={{
                ...styles.btn,
                opacity: loading() ? 0.6 : 1,
                cursor: loading() ? "not-allowed" : "pointer",
              }}
              onClick={handleGenerate}
              disabled={loading()}
            >
              {loading() ? "🔄 生成中..." : "🎙️ 生成 Podcast"}
            </button>
          </div>
        </section>

        {/* 右欄：結果 */}
        <section style={styles.resultSection}>
          <Show when={result()}>
            <div style={styles.resultHeader}>
              <span style={result()!.success ? styles.badgeOk : styles.badgeError}>
                {result()!.success ? "✅ 成功" : "❌ 失敗"}
              </span>
              <span style={styles.jobId}>Job #{result()!.job_id}</span>
            </div>

            {/* 最終音頻 */}
            <Show when={result()!.output_path && audioUrl()}>
              <div style={styles.audioWrap}>
                <label style={styles.label}>🎧 完整 Podcast</label>
                <audio controls src={audioUrl()!} style={styles.audioPlayer}>
                  你的瀏覽器不支援音頻播放
                </audio>
                <a
                  href={audioUrl()!}
                  download
                  style={styles.downloadLink}
                >
                  ⬇️ 下載 MP3
                </a>
              </div>
            </Show>

            {/* 錯誤 */}
            <Show when={result()!.error}>
              <div style={styles.errorBox}>{result()!.error}</div>
            </Show>

            {/* 分段列表 */}
            <div style={styles.segments}>
              <label style={styles.label}>📋 分段結果</label>
              <For each={result()!.segments}>
                {(seg, i) => (
                  <div style={{
                    ...styles.segItem,
                    border-left: seg.speaker === "male" ? "3px solid #4a9eff" : "3px solid #ff6b9d",
                  }}>
                    <span style={styles.segSpeaker}>
                      {seg.speaker === "male" ? "👨 男" : "👩 女"}
                    </span>
                    <span style={styles.segText}>{seg.text}</span>
                    <Show when={seg.success}>
                      <a
                        href={`${API_BASE}/download/${seg.audio_path!.split("/").pop()}`}
                        target="_blank"
                        style={styles.segPlay}
                      >
                        ▶️
                      </a>
                    </Show>
                    <Show when={!seg.success}>
                      <span style={styles.segFail}>❌</span>
                    </Show>
                  </div>
                )}
              </For>
            </div>
          </Show>

          {/* 空狀態 */}
          <Show when={!result()}>
            <div style={styles.emptyState}>
              <p>👆 填入腳本，點「生成 Podcast」</p>
            </div>
          </Show>
        </section>
      </main>
    </div>
  );
}

// ── 樣式（行內，無需 CSS 檔）──────────────────────────────────

const styles: Record<string, React.CSSProperties> = {
  root: {
    fontFamily: "system-ui, -apple-system, sans-serif",
    minHeight: "100vh",
    background: "#0f1117",
    color: "#e0e0e0",
    padding: "0",
    margin: "0",
  },
  header: {
    background: "#1a1d27",
    padding: "24px 32px",
    borderBottom: "1px solid #2a2d3a",
  },
  title: {
    fontSize: "24px",
    fontWeight: "700",
    margin: "0 0 4px 0",
    color: "#fff",
  },
  subtitle: {
    fontSize: "13px",
    color: "#888",
    margin: "0",
  },
  statusBar: {
    padding: "10px 32px",
    background: "#1a1d27",
    borderBottom: "1px solid #2a2d3a",
    fontSize: "13px",
  },
  statusOk: { color: "#4ade80" },
  statusError: { color: "#f97316" },
  main: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "0",
    minHeight: "calc(100vh - 120px)",
  },
  editorSection: {
    padding: "24px 32px",
    borderRight: "1px solid #2a2d3a",
  },
  resultSection: {
    padding: "24px 32px",
    background: "#13151f",
  },
  label: {
    display: "block",
    fontSize: "13px",
    fontWeight: "600",
    color: "#aaa",
    marginBottom: "8px",
    marginTop: "16px",
  },
  textarea: {
    width: "100%",
    background: "#1a1d27",
    border: "1px solid #2a2d3a",
    borderRadius: "8px",
    color: "#e0e0e0",
    fontSize: "14px",
    fontFamily: "monospace",
    padding: "12px",
    resize: "vertical",
    boxSizing: "border-box",
    outline: "none",
  },
  hint: {
    fontSize: "12px",
    color: "#666",
    marginTop: "6px",
  },
  controls: {
    display: "flex",
    flexWrap: "wrap",
    gap: "16px",
    alignItems: "center",
    marginTop: "20px",
  },
  controlItem: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    fontSize: "13px",
    color: "#aaa",
  },
  select: {
    background: "#1a1d27",
    border: "1px solid #2a2d3a",
    borderRadius: "6px",
    color: "#e0e0e0",
    padding: "4px 8px",
    fontSize: "13px",
  },
  range: {
    accentColor: "#4a9eff",
    width: "100px",
  },
  btn: {
    background: "#4a9eff",
    border: "none",
    borderRadius: "8px",
    color: "#fff",
    fontSize: "14px",
    fontWeight: "600",
    padding: "10px 20px",
    transition: "opacity 0.2s",
  },
  resultHeader: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    marginBottom: "16px",
  },
  badgeOk: {
    background: "#1a3a2a",
    color: "#4ade80",
    padding: "4px 10px",
    borderRadius: "20px",
    fontSize: "13px",
    fontWeight: "600",
  },
  badgeError: {
    background: "#3a1a1a",
    color: "#f87171",
    padding: "4px 10px",
    borderRadius: "20px",
    fontSize: "13px",
    fontWeight: "600",
  },
  jobId: {
    fontSize: "12px",
    color: "#666",
    fontFamily: "monospace",
  },
  audioWrap: {
    marginBottom: "8px",
  },
  audioPlayer: {
    width: "100%",
    height: "40px",
    marginBottom: "8px",
  },
  downloadLink: {
    display: "inline-block",
    background: "#4ade80",
    color: "#000",
    padding: "6px 14px",
    borderRadius: "6px",
    textDecoration: "none",
    fontSize: "13px",
    fontWeight: "600",
  },
  errorBox: {
    background: "#3a1a1a",
    color: "#f87171",
    padding: "12px",
    borderRadius: "8px",
    fontSize: "13px",
    marginBottom: "16px",
  },
  segments: {
    marginTop: "8px",
  },
  segItem: {
    display: "flex",
    alignItems: "flex-start",
    gap: "8px",
    padding: "8px 12px",
    background: "#1a1d27",
    borderRadius: "6px",
    marginBottom: "6px",
    fontSize: "13px",
  },
  segSpeaker: {
    fontWeight: "600",
    minWidth: "40px",
    fontSize: "12px",
  },
  segText: {
    flex: 1,
    color: "#ccc",
  },
  segPlay: {
    fontSize: "12px",
    textDecoration: "none",
    padding: "2px 6px",
  },
  segFail: {
    fontSize: "12px",
  },
  emptyState: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    height: "200px",
    color: "#444",
    fontSize: "14px",
  },
};
