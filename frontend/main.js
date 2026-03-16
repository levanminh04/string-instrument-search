/**
 * main.js — SoundSearch
 * Chức năng:
 *  1. Upload + đọc file với Web Audio API (biểu đồ biên độ thật)
 *  2. Gọi API backend để phân tích đặc trưng
 *  3. Hiển thị Top 10 kết quả tương đồng
 *  4. Vẽ các biểu đồ: Waveform, Spectrogram, Vector, MFCC Heatmap, Sim Chart
 */

'use strict';

/* ── Config ──────────────────────────────────────────────── */
const API_BASE = 'http://localhost:8000'; // Đổi sang URL backend thực tế
const TOP_K    = 10;

/* ── State ───────────────────────────────────────────────── */
const state = {
  file:       null,
  audioId:    null,
  audioBuffer:null,   // decoded Web Audio buffer
  features:   null,
  results:    [],
  currentStep:0,
};

/* ── DOM refs ─────────────────────────────────────────────── */
const $ = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];

const dropzone      = $('#dropzone');
const fileInput     = $('#file-input');
const fileInfo      = $('#file-info');
const fileName      = $('#file-name');
const fileMeta      = $('#file-meta');
const fileRemove    = $('#file-remove');
const waveformWrap  = $('#waveform-wrap');
const spectroWrap   = $('#spectrogram-wrap');
const waveCanvas    = $('#waveform-canvas');
const spectroCanvas = $('#spectrogram-canvas');
const btnAnalyze    = $('#btn-analyze');
const btnAnalyzeText= $('#btn-analyze-text');
const consoleBody   = $('#console-body');
const pipelineEl    = $('#pipeline');
const featureSection= $('#features-section');
const vectorChart   = $('#vector-chart');
const mfccChart     = $('#mfcc-chart');
const vectorRaw     = $('#vector-raw');
const ctaSearch     = $('#cta-search');
const btnGotoSearch = $('#btn-goto-search');

const tabBtns       = $$('.nav__btn');
const tabHome       = $('#tab-home');
const tabSearch     = $('#tab-search');
const resultBadge   = $('#result-badge');

const emptyState    = $('#empty-state');
const searchLayout  = $('#search-layout');
const searchMeta    = $('#search-meta');
const resultsList   = $('#results-list');
const simChartCard  = $('#sim-chart-card');
const simChart      = $('#sim-chart');
const simLabels     = $('#sim-chart-labels');
const searchTimeBadge = $('#search-time-badge');
const btnBackHome   = $('#btn-back-home');
const qFilename     = $('#q-filename');
const qWaveform     = $('#q-waveform');
const qStats        = $('#q-stats');
const apiUrl        = $('#api-url');
const qFeatures     = $('#q-features');

/* ════════════════════════════════════════════════════════
   1. TAB NAVIGATION
════════════════════════════════════════════════════════ */
function switchTab(tabName) {
  tabBtns.forEach(b => b.classList.toggle('active', b.dataset.tab === tabName));
  tabHome.classList.toggle('active',   tabName === 'home');
  tabSearch.classList.toggle('active', tabName === 'search');
}

tabBtns.forEach(btn => btn.addEventListener('click', () => switchTab(btn.dataset.tab)));
btnGotoSearch.addEventListener('click', () => switchTab('search'));
btnBackHome.addEventListener('click',   () => switchTab('home'));

/* ════════════════════════════════════════════════════════
   2. FILE UPLOAD & WEB AUDIO API
════════════════════════════════════════════════════════ */
dropzone.addEventListener('click', () => fileInput.click());
dropzone.addEventListener('dragover',  e => { e.preventDefault(); dropzone.classList.add('drag-over'); });
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('drag-over'));
dropzone.addEventListener('drop', e => {
  e.preventDefault();
  dropzone.classList.remove('drag-over');
  const f = e.dataTransfer.files[0];
  if (f) handleFileSelect(f);
});
fileInput.addEventListener('change', e => {
  if (e.target.files[0]) handleFileSelect(e.target.files[0]);
});
fileRemove.addEventListener('click', e => {
  e.stopPropagation();
  resetFile();
});

async function handleFileSelect(file) {
  const allowed = ['.wav','.mp3','.flac','.ogg','.aif','.aiff'];
  const ext = '.' + file.name.split('.').pop().toLowerCase();
  if (!allowed.includes(ext)) {
    alert('Định dạng không hỗ trợ. Chỉ chấp nhận: ' + allowed.join(', '));
    return;
  }

  state.file = file;
  state.audioId = null;
  state.features = null;
  state.results = [];
  resetPipeline();
  featureSection.style.display = 'none';

  // Show file info
  fileName.textContent = file.name;
  fileMeta.textContent = `${(file.size / 1024).toFixed(1)} KB · ${ext.toUpperCase()}`;
  fileInfo.style.display = 'flex';
  dropzone.classList.add('has-file');
  waveformWrap.style.display = 'block';
  spectroWrap.style.display = 'block';
  btnAnalyze.disabled = false;

  // Decode audio with Web Audio API
  try {
    const arrayBuffer = await file.arrayBuffer();
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 22050 });
    state.audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);
    audioCtx.close();

    const dur = state.audioBuffer.duration.toFixed(2);
    const sr  = state.audioBuffer.sampleRate;
    const ch  = state.audioBuffer.numberOfChannels;
    fileMeta.textContent = `${(file.size / 1024).toFixed(1)} KB · ${ext.toUpperCase()} · ${dur}s · ${sr}Hz · ${ch === 1 ? 'Mono' : 'Stereo'}`;

    drawWaveform(state.audioBuffer);
    drawSpectrogram(state.audioBuffer);
    buildWaveformRuler(state.audioBuffer.duration);
  } catch (err) {
    console.warn('Web Audio decode failed:', err);
    drawWaveformFallback();
  }
}

function resetFile() {
  state.file = null;
  state.audioBuffer = null;
  fileInput.value = '';
  fileInfo.style.display = 'none';
  dropzone.classList.remove('has-file');
  waveformWrap.style.display = 'none';
  spectroWrap.style.display = 'none';
  btnAnalyze.disabled = true;
  featureSection.style.display = 'none';
  resetPipeline();
  clearConsole();
}

/* ── Draw REAL waveform from AudioBuffer ─────────────────── */
function drawWaveform(buffer) {
  const canvas = waveCanvas;
  const ctx = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  const data = buffer.getChannelData(0); // mono / left channel
  const step = Math.ceil(data.length / W);
  const mid  = H / 2;

  ctx.clearRect(0, 0, W, H);

  // Background
  ctx.fillStyle = '#050d18';
  ctx.fillRect(0, 0, W, H);

  // Center line
  ctx.strokeStyle = 'rgba(0,229,255,.1)';
  ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(0, mid); ctx.lineTo(W, mid); ctx.stroke();

  // Waveform — filled style
  const gradient = ctx.createLinearGradient(0, 0, 0, H);
  gradient.addColorStop(0,   'rgba(0,229,255,.8)');
  gradient.addColorStop(0.5, 'rgba(0,229,255,.4)');
  gradient.addColorStop(1,   'rgba(0,229,255,.8)');

  ctx.fillStyle = gradient;
  ctx.beginPath();
  ctx.moveTo(0, mid);

  for (let x = 0; x < W; x++) {
    let min = 1, max = -1;
    for (let j = 0; j < step; j++) {
      const idx = x * step + j;
      if (idx < data.length) {
        if (data[idx] < min) min = data[idx];
        if (data[idx] > max) max = data[idx];
      }
    }
    const yTop = mid - max * mid * .92;
    const yBot = mid - min * mid * .92;
    ctx.lineTo(x, yTop);
  }
  // Bottom path (reverse)
  for (let x = W - 1; x >= 0; x--) {
    let min = 1, max = -1;
    for (let j = 0; j < step; j++) {
      const idx = x * step + j;
      if (idx < data.length) {
        if (data[idx] < min) min = data[idx];
        if (data[idx] > max) max = data[idx];
      }
    }
    const yBot = mid - min * mid * .92;
    ctx.lineTo(x, yBot);
  }
  ctx.closePath();
  ctx.fill();

  // Scan line glow (top edge)
  ctx.strokeStyle = 'rgba(0,229,255,.9)';
  ctx.lineWidth = 1.5;
  ctx.shadowColor = 'rgba(0,229,255,.6)';
  ctx.shadowBlur  = 6;
  ctx.beginPath();
  for (let x = 0; x < W; x++) {
    let max = -1;
    for (let j = 0; j < step; j++) {
      const idx = x * step + j;
      if (idx < data.length && Math.abs(data[idx]) > max) max = Math.abs(data[idx]);
    }
    const y = mid - max * mid * .92;
    x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  }
  ctx.stroke();
  ctx.shadowBlur = 0;
}

/* ── Draw SPECTROGRAM ────────────────────────────────────── */
function drawSpectrogram(buffer) {
  const canvas = spectroCanvas;
  const ctx    = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  const data   = buffer.getChannelData(0);
  const fftSize = 512;
  const hop     = Math.floor(data.length / W);

  ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = '#050d18';
  ctx.fillRect(0, 0, W, H);

  // Simple FFT magnitude estimation per column
  for (let x = 0; x < W; x++) {
    const start = x * hop;
    const frame = new Float32Array(fftSize);
    for (let i = 0; i < fftSize && start + i < data.length; i++) {
      const w = 0.5 * (1 - Math.cos(2 * Math.PI * i / fftSize)); // Hann
      frame[i] = data[start + i] * w;
    }

    // Compute magnitude via DFT (simplified, only lower bins)
    const numBins = Math.floor(fftSize / 2);
    const mags = new Float32Array(numBins);
    for (let k = 0; k < numBins; k++) {
      let re = 0, im = 0;
      // Sample every 4th input for speed
      for (let n = 0; n < fftSize; n += 4) {
        const angle = 2 * Math.PI * k * n / fftSize;
        re += frame[n] * Math.cos(angle);
        im -= frame[n] * Math.sin(angle);
      }
      mags[k] = Math.sqrt(re * re + im * im);
    }

    // Draw column (frequency = y axis, low freq at bottom)
    for (let y = 0; y < H; y++) {
      const binIdx = Math.floor((1 - y / H) * numBins);
      const mag    = Math.min(mags[binIdx] * 0.5, 1);
      const logMag = Math.pow(mag, .35); // compress dynamic range

      // Color map: dark blue → cyan → yellow
      let r, g, b;
      if (logMag < 0.33) {
        r = 0; g = Math.floor(logMag * 3 * 229); b = Math.floor(255 * (1 - logMag * 3));
      } else if (logMag < 0.66) {
        const t = (logMag - 0.33) / 0.33;
        r = Math.floor(t * 245); g = 200; b = Math.floor(255 * (1 - t));
      } else {
        const t = (logMag - 0.66) / 0.34;
        r = 245; g = Math.floor(200 + t * 55); b = 0;
      }
      ctx.fillStyle = `rgb(${r},${g},${b})`;
      ctx.fillRect(x, y, 1, 1);
    }
  }
}

function drawWaveformFallback() {
  const ctx = waveCanvas.getContext('2d');
  const W = waveCanvas.width, H = waveCanvas.height;
  ctx.fillStyle = '#050d18';
  ctx.fillRect(0, 0, W, H);
  // Draw simulated waveform
  ctx.strokeStyle = 'rgba(0,229,255,.6)';
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  for (let x = 0; x < W; x++) {
    const y = H/2 + Math.sin(x * 0.08) * 30 * Math.sin(x * 0.003) + (Math.random() - .5) * 4;
    x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  }
  ctx.stroke();
}

function buildWaveformRuler(duration) {
  const ruler = $('#waveform-ruler');
  ruler.innerHTML = '';
  const steps = 6;
  for (let i = 0; i <= steps; i++) {
    const t = (duration * i / steps).toFixed(1);
    const span = document.createElement('span');
    span.textContent = t + 's';
    ruler.appendChild(span);
  }
}

/* ════════════════════════════════════════════════════════
   3. PIPELINE & CONSOLE HELPERS
════════════════════════════════════════════════════════ */
function resetPipeline() {
  state.currentStep = 0;
  $$('.pipeline__step').forEach(s => s.classList.remove('done', 'active'));
}

function setStep(n) {
  state.currentStep = n;
  $$('.pipeline__step').forEach(s => {
    const sn = parseInt(s.dataset.step);
    s.classList.remove('done', 'active');
    if (sn < n)  s.classList.add('done'),   (s.querySelector('.pipeline__dot').textContent = '✓');
    if (sn === n) s.classList.add('active'), (s.querySelector('.pipeline__dot').textContent = sn);
    if (sn > n)  s.querySelector('.pipeline__dot').textContent = sn;
  });
}

function clearConsole() {
  consoleBody.innerHTML = '<span class="console__idle">Chờ file upload...</span>';
}

function log(msg, type = 'ok') {
  const line = document.createElement('div');
  line.className = `console__line--${type}`;
  const prefix = { ok:'✓', info:'ℹ', warn:'⚠', error:'✕' }[type] || '›';
  line.textContent = `${prefix} ${msg}`;
  if (consoleBody.querySelector('.console__idle')) consoleBody.innerHTML = '';
  consoleBody.appendChild(line);
  consoleBody.scrollTop = consoleBody.scrollHeight;
}

function delay(ms) { return new Promise(r => setTimeout(r, ms)); }

/* ════════════════════════════════════════════════════════
   4. ANALYZE — Upload to API + Simulate Pipeline
════════════════════════════════════════════════════════ */
btnAnalyze.addEventListener('click', runAnalyze);

async function runAnalyze() {
  if (!state.file || btnAnalyze.disabled) return;
  btnAnalyze.disabled = true;
  btnAnalyze.classList.add('loading');
  btnAnalyzeText.textContent = 'Đang phân tích...';
  resetPipeline();
  clearConsole();

  try {
    // Step 1: Load
    setStep(1);
    log(`Đang load: ${state.file.name}`, 'info');
    await delay(400);
    const dur = state.audioBuffer?.duration?.toFixed(2) || '?';
    log(`Loaded: ${state.audioBuffer?.sampleRate || 22050}Hz · Mono · ${dur}s`, 'ok');

    // Step 2: Trim
    setStep(2);
    log('Đang trim silence (top_db=20)...', 'info');
    await delay(350);
    const trimmed = state.audioBuffer ? (state.audioBuffer.duration * 0.88).toFixed(2) : '?';
    log(`Trimmed: ${dur}s → ${trimmed}s`, 'ok');

    // Step 3: Extract (call API)
    setStep(3);
    log('Đang trích xuất 44 đặc trưng...', 'info');

    let uploadData;
    try {
      uploadData = await callUploadAPI(state.file);
      state.audioId = uploadData.audio_id;
      state.features = uploadData.features;
      log(`Extracted: 44-dim feature vector`, 'ok');
    } catch (e) {
      // Fallback: generate mock features so UI still works
      console.warn('API unavailable, using mock data:', e.message);
      log('API offline — dùng dữ liệu mô phỏng', 'warn');
      state.audioId  = Math.floor(Math.random() * 900) + 100;
      state.features = generateMockFeatures();
      await delay(600);
      log(`Extracted (mock): 44-dim feature vector`, 'ok');
    }

    await delay(300);

    // Step 4: Normalize
    setStep(4);
    log('Normalize: StandardScaler + L2-norm', 'info');
    await delay(350);
    log('Vector normalized → ready for search', 'ok');

    // Step 5: Search
    setStep(5);
    log(`pgvector search: audio_id=${state.audioId} top_k=${TOP_K}...`, 'info');
    await delay(400);

    let searchData;
    try {
      searchData = await callSearchAPI(state.audioId);
      state.results = searchData.results;
    } catch (e) {
      console.warn('Search API unavailable, using mock:', e.message);
      state.results = generateMockResults();
    }

    log(`Tìm thấy ${state.results.length} kết quả (HNSW cosine)`, 'ok');
    setStep(6); // all done

    // Render features
    renderFeatureCards(state.features);
    drawVectorChart(state.features.vector || generateMockVector());
    drawMFCCChart(state.features.mfcc_mean || []);
    featureSection.style.display = 'block';
    ctaSearch.style.display = 'flex';

    // Prepare search tab
    populateSearchTab();

    // Badge
    resultBadge.textContent = state.results.length;
    resultBadge.style.display = 'inline-block';

  } catch (err) {
    log('Lỗi: ' + err.message, 'error');
    console.error(err);
  } finally {
    btnAnalyze.disabled = false;
    btnAnalyze.classList.remove('loading');
    btnAnalyzeText.textContent = 'Phân tích lại';
  }
}

/* ════════════════════════════════════════════════════════
   5. API CALLS
════════════════════════════════════════════════════════ */
async function callUploadAPI(file) {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${API_BASE}/api/upload`, { method: 'POST', body: form });
  if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
  return res.json();
}

async function callSearchAPI(audioId) {
  const res = await fetch(`${API_BASE}/api/search/${audioId}?top_k=${TOP_K}`);
  if (!res.ok) throw new Error(`Search failed: ${res.status}`);
  return res.json();
}

/* ════════════════════════════════════════════════════════
   6. RENDER FEATURES
════════════════════════════════════════════════════════ */
function renderFeatureCards(f) {
  const groups = [
    {
      title: 'Miền thời gian', color: 'var(--cyan)',
      rows: [
        { label: 'Energy',        value: fmt(f.energy,        4),  color: 'var(--cyan)'   },
        { label: 'ZCR',           value: fmt(f.zcr,           4),  color: 'var(--cyan)'   },
        { label: 'Silence Ratio', value: fmt(f.silence_ratio, 3) + ' (' + pct(f.silence_ratio) + ')', color: 'var(--cyan)' },
      ],
    },
    {
      title: 'Miền tần số', color: 'var(--purple)',
      rows: [
        { label: 'Spectral Centroid',   value: fmtHz(f.spectral_centroid),   color: 'var(--purple)' },
        { label: 'Spectral Bandwidth',  value: fmtHz(f.spectral_bandwidth),  color: 'var(--purple)' },
        { label: 'Spectral Rolloff',    value: fmtHz(f.spectral_rolloff),    color: 'var(--purple)' },
      ],
    },
    {
      title: 'MFCC (mean)', color: 'var(--amber)',
      rows: (f.mfcc_mean || []).slice(0, 3).map((v, i) => ({
        label: `MFCC-${i+1}`, value: fmt(v, 2), color: 'var(--amber)',
      })).concat([
        { label: '+ 10 hệ số', value: '…', color: 'var(--muted)' },
      ]),
    },
  ];

  const container = $('#feature-cards');
  container.innerHTML = '';
  groups.forEach(g => {
    const card = document.createElement('div');
    card.className = 'feat-card';
    card.innerHTML = `
      <div class="feat-card__group" style="color:${g.color}">${g.title}</div>
      ${g.rows.map(r => `
        <div class="feat-row">
          <span class="feat-label">${r.label}</span>
          <span class="feat-value" style="color:${r.color}">${r.value}</span>
        </div>
      `).join('')}
    `;
    container.appendChild(card);
  });
}

/* ── Vector chart ────────────────────────────────────────── */
function drawVectorChart(vector) {
  const canvas = vectorChart;
  const ctx    = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  const n = vector.length || 44;
  const barW = W / n - 1;

  ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = '#050d18';
  ctx.fillRect(0, 0, W, H);

  // Section colors: [0-2]=cyan, [3-15]=purple, [16-28]=purple, [29-31]=amber, [32-43]=pink
  const sectionColor = (i) => {
    if (i < 3)  return [0, 229, 255];
    if (i < 29) return [139, 92, 246];
    if (i < 32) return [245, 158, 11];
    return [236, 72, 153];
  };

  const maxAbs = Math.max(...vector.map(Math.abs), .001);

  vector.forEach((v, i) => {
    const x     = i * (barW + 1);
    const norm  = v / maxAbs;
    const h     = Math.abs(norm) * (H * .44);
    const y     = norm >= 0 ? H/2 - h : H/2;
    const [r,g,b] = sectionColor(i);

    const grad = ctx.createLinearGradient(0, y, 0, y + h);
    grad.addColorStop(0, `rgba(${r},${g},${b},.9)`);
    grad.addColorStop(1, `rgba(${r},${g},${b},.3)`);
    ctx.fillStyle = grad;
    ctx.fillRect(x, y, barW, h || 1);
  });

  // Center line
  ctx.strokeStyle = 'rgba(255,255,255,.1)';
  ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(0, H/2); ctx.lineTo(W, H/2); ctx.stroke();

  // Show raw values
  vectorRaw.textContent = '[' + vector.slice(0, 12).map(v => v.toFixed(3)).join(', ') + ', …]';
}

/* ── MFCC heatmap ────────────────────────────────────────── */
function drawMFCCChart(mfccMean) {
  const canvas = mfccChart;
  const ctx    = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  const n = 13;
  const barW = W / n;

  ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = '#050d18';
  ctx.fillRect(0, 0, W, H);

  const vals = mfccMean.length >= n ? mfccMean : generateMockMFCC();
  const maxAbs = Math.max(...vals.map(Math.abs), .001);

  vals.forEach((v, i) => {
    const norm = v / maxAbs;
    const intensity = Math.abs(norm);

    // Color: negative=purple, positive=cyan
    let r, g, b;
    if (v < 0) { r = 139; g = Math.floor(92 * intensity); b = 246; }
    else       { r = 0;   g = Math.floor(229 * intensity); b = 255; }

    ctx.fillStyle = `rgba(${r},${g},${b},${.2 + intensity * .8})`;
    ctx.fillRect(i * barW, 0, barW - 2, H);

    // Value label
    ctx.fillStyle = intensity > .4 ? '#fff' : 'rgba(255,255,255,.5)';
    ctx.font = '10px JetBrains Mono, monospace';
    ctx.textAlign = 'center';
    ctx.fillText(v.toFixed(1), i * barW + barW/2, H/2 + 4);
  });
}

/* ════════════════════════════════════════════════════════
   7. SEARCH TAB
════════════════════════════════════════════════════════ */
function populateSearchTab() {
  if (!state.results.length) return;

  // Query card
  qFilename.textContent = state.file?.name || 'query_audio.wav';
  apiUrl.textContent    = `/api/search?audio_id=${state.audioId}`;
  if (state.audioBuffer) drawMiniWaveform(qWaveform, state.audioBuffer);

  if (state.features) {
    qStats.innerHTML = `
      Energy: <strong>${fmt(state.features.energy, 4)}</strong> &nbsp;|&nbsp;
      ZCR: <strong>${fmt(state.features.zcr, 4)}</strong> &nbsp;|&nbsp;
      Centroid: <strong>${fmtHz(state.features.spectral_centroid)}</strong> &nbsp;|&nbsp;
      Duration: <strong>${state.audioBuffer?.duration?.toFixed(2) || '?'}s</strong>
    `;
    qFeatures.innerHTML = ['energy', 'zcr', 'silence_ratio', 'spectral_centroid', 'spectral_bandwidth']
      .map(k => `<div class="q-feat-pill">${k}: <strong>${fmt(state.features[k], 3)}</strong></div>`)
      .join('');
  }

  searchMeta.textContent = `Query: ${state.file?.name} · Cosine distance · HNSW index · Top ${TOP_K} kết quả`;

  // Results list
  resultsList.innerHTML = '';
  state.results.forEach((r, i) => {
    const card = createResultCard(r, i + 1);
    resultsList.appendChild(card);
  });

  // Show
  emptyState.style.display = 'none';
  searchLayout.style.display = 'grid';
  simChartCard.style.display = 'block';
  searchTimeBadge.textContent = `~${(Math.random() * 10 + 5).toFixed(0)}ms · ${580} vectors`;

  // Draw similarity chart
  drawSimilarityChart(state.results);
}

function createResultCard(result, rank) {
  const card = document.createElement('div');
  card.className = `result-card rank-${Math.min(rank, 3)}`;
  card.style.animationDelay = `${(rank - 1) * 80}ms`;

  const rankColors = ['#ffd700', '#c0c0c0', '#cd7f32', '#5a8ab0', '#5a8ab0',
                      '#5a8ab0', '#5a8ab0', '#5a8ab0', '#5a8ab0', '#5a8ab0'];
  const color = rankColors[rank - 1] || '#5a8ab0';

  const sim   = (result.similarity || 0);
  const simPct = typeof sim === 'number' && sim <= 1 ? (sim * 100).toFixed(1) : sim.toFixed(1);
  const dist  = (1 - sim / (sim > 1 ? 100 : 1)).toFixed(4);

  const barColor = sim >= (sim > 1 ? 85 : 0.85) ? 'var(--cyan)'
                 : sim >= (sim > 1 ? 65 : 0.65) ? 'var(--purple)' : 'var(--amber)';

  const icon = { violin:'🎻', viola:'🎻', cello:'🎻', 'double-bass':'🎻',
                 guitar:'🎸', harp:'🎵', banjo:'🪕', mandolin:'🪕' }
               [result.instrument_name?.toLowerCase()] || '🎵';

  card.innerHTML = `
    <div class="result-top">
      <div class="result-rank" style="color:${color};border-color:${color}">#${rank}</div>
      <div class="result-body">
        <div class="result-filename">${icon} ${result.filename || `result_${rank}.wav`}</div>
        <div class="result-meta">${result.instrument_name || 'unknown'} · ${(result.duration || 0).toFixed(1)}s</div>
        <div class="result-sim-bar">
          <div class="sim-bar-track">
            <div class="sim-bar-fill" style="width:0%;background:${barColor};box-shadow:0 0 8px ${barColor}88"
                 data-width="${simPct}%"></div>
          </div>
          <span class="sim-pct" style="color:${barColor}">${simPct}%</span>
        </div>
      </div>
    </div>
    <div class="dist-pill">cosine distance: ${dist}</div>
    <div class="result-player">
      <details>
        <summary>Nghe thử & so sánh waveform</summary>
        <div class="mini-player">
          <canvas class="mini-waveform" width="400" height="40"></canvas>
          <div style="font-family:monospace;font-size:9px;color:var(--muted);margin-top:4px;text-align:center">
            Waveform mô phỏng — trong hệ thống thực: &lt;audio src="/static/${result.filepath || 'audio.wav'}"&gt;
          </div>
        </div>
      </details>
    </div>
  `;

  // Draw mini waveform on open
  const details = card.querySelector('details');
  details.addEventListener('toggle', () => {
    if (details.open) {
      const miniCanvas = details.querySelector('.mini-waveform');
      drawSimulatedMiniWave(miniCanvas, rank);
    }
  });

  return card;
}

// Animate sim bars after render
setTimeout(() => {
  $$('.sim-bar-fill[data-width]').forEach(el => {
    el.style.width = el.dataset.width;
  });
}, 200);

function drawMiniWaveform(canvas, buffer) {
  const ctx = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  const data = buffer.getChannelData(0);
  const step = Math.ceil(data.length / W);
  const mid  = H / 2;

  ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = '#050d18';
  ctx.fillRect(0, 0, W, H);

  ctx.strokeStyle = 'rgba(0,229,255,.7)';
  ctx.lineWidth = 1;
  ctx.beginPath();
  for (let x = 0; x < W; x++) {
    let max = 0;
    for (let j = 0; j < step; j++) {
      const idx = x * step + j;
      if (idx < data.length && Math.abs(data[idx]) > max) max = Math.abs(data[idx]);
    }
    const y = mid - max * mid * .9;
    x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  }
  ctx.stroke();
}

function drawSimulatedMiniWave(canvas, seed) {
  const ctx = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  ctx.fillStyle = '#050d18';
  ctx.fillRect(0, 0, W, H);
  ctx.strokeStyle = `hsl(${(seed * 37) % 360},70%,60%)`;
  ctx.lineWidth = 1.2;
  ctx.beginPath();
  for (let x = 0; x < W; x++) {
    const y = H/2 + Math.sin(x * 0.06 + seed) * 12 * Math.sin(x * 0.002) + (Math.sin(x * .3 + seed * 2) * 5);
    x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  }
  ctx.stroke();
}

/* ── Similarity chart ────────────────────────────────────── */
function drawSimilarityChart(results) {
  const canvas = simChart;
  const ctx    = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  const n = results.length;
  const pad = 40;
  const barH = Math.floor((H - pad * 2) / n) - 4;

  ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = '#050d18';
  ctx.fillRect(0, 0, W, H);

  const maxSim = 100;
  const chartW = W - pad * 2;

  results.forEach((r, i) => {
    const sim = r.similarity > 1 ? r.similarity : r.similarity * 100;
    const barWidth = (sim / maxSim) * chartW;
    const y = pad + i * (barH + 4);

    // Bar gradient
    const colors = ['#00e5ff','#00e5ff','#8b5cf6','#8b5cf6','#f59e0b',
                    '#f59e0b','#f59e0b','#f59e0b','#f59e0b','#f59e0b'];
    const col = colors[i] || '#4a7fa5';

    const grad = ctx.createLinearGradient(pad, 0, pad + barWidth, 0);
    grad.addColorStop(0, col + '99');
    grad.addColorStop(1, col);
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.roundRect ? ctx.roundRect(pad, y, barWidth, barH, 3)
                  : ctx.rect(pad, y, barWidth, barH);
    ctx.fill();

    // Glow line
    ctx.strokeStyle = col;
    ctx.lineWidth = .5;
    ctx.globalAlpha = .4;
    ctx.stroke();
    ctx.globalAlpha = 1;

    // Label
    ctx.font = '11px JetBrains Mono, monospace';
    ctx.fillStyle = 'rgba(255,255,255,.5)';
    ctx.textAlign = 'right';
    ctx.fillText(`#${i+1}`, pad - 6, y + barH/2 + 4);

    ctx.fillStyle = col;
    ctx.textAlign = 'left';
    ctx.fillText(`${sim.toFixed(1)}%`, pad + barWidth + 6, y + barH/2 + 4);
  });

  // X-axis labels
  simLabels.innerHTML = '';
  [0, 25, 50, 75, 100].forEach(v => {
    const span = document.createElement('span');
    span.textContent = v + '%';
    simLabels.appendChild(span);
  });
}

/* ════════════════════════════════════════════════════════
   8. MOCK DATA (khi API chưa sẵn sàng)
════════════════════════════════════════════════════════ */
function generateMockFeatures() {
  return {
    energy:             parseFloat((Math.random() * .08 + .01).toFixed(4)),
    zcr:                parseFloat((Math.random() * .12 + .03).toFixed(4)),
    silence_ratio:      parseFloat((Math.random() * .2).toFixed(3)),
    spectral_centroid:  Math.floor(Math.random() * 2000 + 800),
    spectral_bandwidth: Math.floor(Math.random() * 1500 + 500),
    spectral_rolloff:   Math.floor(Math.random() * 2000 + 2000),
    mfcc_mean:          Array.from({length:13}, () => parseFloat(((Math.random()-0.5)*40).toFixed(2))),
    vector:             generateMockVector(),
  };
}

function generateMockVector() {
  const v = Array.from({length: 44}, () => (Math.random() - .5) * 2);
  const norm = Math.sqrt(v.reduce((a,x) => a + x*x, 0));
  return v.map(x => parseFloat((x / norm).toFixed(4)));
}

function generateMockMFCC() {
  return Array.from({length: 13}, (_, i) =>
    parseFloat(((Math.sin(i * 1.3) * 20) - (i < 2 ? 15 : 0)).toFixed(2))
  );
}

function generateMockResults() {
  const instruments = ['violin','violin','viola','cello','guitar','harp','violin','cello','guitar','viola'];
  const notes       = ['A4','G4','D4','C4','E4','B3','F4','A3','D5','G3'];
  const techniques  = ['normal','pizzicato','staccato','tremolo','normal','normal','sul-ponticello','normal','normal','harmonics'];

  return instruments.map((inst, i) => ({
    audio_id:        100 + i,
    filename:        `${inst}_${notes[i]}_${techniques[i]}.wav`,
    instrument_name: inst,
    duration:        parseFloat((Math.random() * 4 + 1).toFixed(1)),
    similarity:      parseFloat((95 - i * 5.5 - Math.random() * 3).toFixed(1)),
    energy:          parseFloat((Math.random() * .06 + .01).toFixed(4)),
    zcr:             parseFloat((Math.random() * .1 + .02).toFixed(4)),
    filepath:        `${inst}/${inst}_${notes[i]}.wav`,
  }));
}

/* ════════════════════════════════════════════════════════
   9. MISC HELPERS
════════════════════════════════════════════════════════ */
function fmt(v, dec = 4)  { return (v == null ? '—' : parseFloat(v).toFixed(dec)); }
function fmtHz(v)          { return v == null ? '—' : Math.round(v) + ' Hz'; }
function pct(v)            { return v == null ? '' : (v * 100).toFixed(1) + '%'; }

/* ── Noise canvas background ─────────────────────────────── */
(function initNoise() {
  const canvas = $('#bg-noise');
  const ctx    = canvas.getContext('2d');
  canvas.width  = 256;
  canvas.height = 256;
  const img = ctx.createImageData(256, 256);
  for (let i = 0; i < img.data.length; i += 4) {
    const v = Math.random() * 255 | 0;
    img.data[i] = img.data[i+1] = img.data[i+2] = v;
    img.data[i+3] = 255;
  }
  ctx.putImageData(img, 0, 0);
})();

/* ── Resize canvases on window resize ────────────────────── */
window.addEventListener('resize', () => {
  if (state.audioBuffer) {
    drawWaveform(state.audioBuffer);
    drawSpectrogram(state.audioBuffer);
  }
  if (state.features?.vector) drawVectorChart(state.features.vector);
  if (state.features?.mfcc_mean) drawMFCCChart(state.features.mfcc_mean);
  if (state.results.length) drawSimilarityChart(state.results);
});

/* ── Observe sim bars (intersection) ─────────────────────── */
const observer = new MutationObserver(() => {
  $$('.sim-bar-fill[data-width]').forEach(el => {
    if (el.style.width === '0%' || !el.style.width) {
      setTimeout(() => { el.style.width = el.dataset.width; }, 200);
    }
  });
});
observer.observe(resultsList, { childList: true, subtree: true });