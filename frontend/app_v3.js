/**
 * AUDIO SEARCH ENGINE - CORE LOGIC (v23D Optimized)
 */

// UI Elements
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const resultsList = document.getElementById('results-list');
const terminalLogs = document.getElementById('terminal-body');
const searchTimeBadge = document.getElementById('search-time');
const eqBoard = document.getElementById('eq-board');

// Metadata Elements
const inputFilename = document.getElementById('input-filename');
const inputMetadata = document.getElementById('input-metadata');

// State
let currentResults = [];
let currentQueryVector = null;
let currentAudio = null;
let currentPlayingBtn = null;

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    logToTerminal("System initialized. Awaiting 23D acoustic input...", 500);
});

// --- Upload Logic ---
dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('drag-over'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) handleFile(e.target.files[0]);
});

async function handleFile(file) {
    if (!file.type.startsWith('audio/')) return alert('Please upload an audio file.');

    // Clear UI
    resultsList.innerHTML = '<div class="searching-spinner"><i class="fa-solid fa-compact-disc fa-spin fa-3x"></i><p>Extracting 23D Features...</p></div>';

    // Log
    await logToTerminal(`[Sys] Analyzing: ${file.name}`, 100);
    await logToTerminal(`[DSP] Initializing librosa.pyin for F0 estimation...`, 200);

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/search', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();

        if (data.error) throw new Error(data.error);

        currentResults = data.search_results;
        currentQueryVector = data.query.feature_vector;

        await logToTerminal(`[DSP] Extracted 23D Vector (Optimized).`, 200);
        await logToTerminal(`[DB] Executing pgvector Exact Cosine Match...`, 300);
        await logToTerminal(`[Sys] Located ${currentResults.length} matches in ${data.timing.total_api_ms}ms!`, 100);

        searchTimeBadge.innerText = `${data.timing.total_api_ms}ms`;
        searchTimeBadge.classList.remove('hidden');

        renderInputInfo(data.query);
        renderResults();

    } catch (err) {
        logToTerminal(`[Err] ${err.message}`, 0);
        resultsList.innerHTML = `<div class="error-state text-danger"><i class="fa-solid fa-circle-exclamation"></i> ${err.message}</div>`;
    }
}

function renderInputInfo(queryData) {
    inputFilename.innerText = queryData.file_name;
    const m = queryData.metadata;
    if (m) {
        inputMetadata.innerText = `${m.instrument} / ${m.pitch} / ${m.dynamics} / ${m.technique}`;
    } else {
        inputMetadata.innerText = "";
    }
}

function renderResults() {
    let html = '';
    currentResults.forEach((res, index) => {
        const simPercent = (res.similarity * 100).toFixed(1);
        let rankClass = index === 0 ? 'score-high' : 'score-mid';
        let crown = index === 0 ? '<i class="fa-solid fa-crown text-gold"></i>' : `#${index + 1}`;

        html += `
            <div class="match-card ${index === 0 ? 'active' : ''}" id="result-card-${index}" onclick="selectResult(${index})">
                <div class="match-header">
                    <button class="btn-play" onclick="playAudio('${res.audio_url}', this); event.stopPropagation();"><i class="fa-solid fa-play"></i></button>
                    <div class="match-info">
                        <h4>${crown} ${res.file_name}</h4>
                        <div class="inst-text">${res.instrument} / ${res.pitch || '?'} / ${res.dynamics || '?'} / ${res.technique || '?'} / String: ${res.string_id || '?'}</div>
                    </div>
                    <div class="match-score ${rankClass}">${simPercent}%</div>
                </div>
                <div class="sim-bar-bg"><div class="sim-bar-fill" style="width: ${simPercent}%"></div></div>
            </div>
        `;
    });
    resultsList.innerHTML = html;

    if (currentResults.length > 0) {
        renderFullEQBoard(currentQueryVector, currentResults[0].feature_vector);
    }
}

function renderFullEQBoard(inVec, outVec) {
    if (!inVec || inVec.length < 23) return;

    let html = `
        <div class="text-muted text-sm mb-3">
            <i class="fa-solid fa-circle-info"></i> Hiển thị giá trị chuẩn hóa <b>Z-Score</b>. 
            Hệ thống 23D tối ưu hóa cho nhạc cụ dây (TinySOL).
        </div>
    `;

    // Mapping dựa trên backend/features/extractor.py:
    // [0-9]:   MFCC Mean C1-C10
    // [10-12]: F0 MIDI x3
    // [13]:    RMS Mean
    // [14-17]: Spectral Contrast B1-B4
    // [18-21]: MFCC Std C1-C4
    // [22]:    Attack Time

    // 1. TEMPORAL & ENERGY
    html += `<div class="eq-category"><div class="category-title"><i class="fa-solid fa-clock"></i> Temporal & Energy</div>`;
    html += genRow('Attack Time', inVec[22], outVec[22]);
    html += genRow('RMS Mean (Energy)', inVec[13], outVec[13]);
    html += genRow('Fundamental Pitch (F0)', inVec[10], outVec[10]);
    html += `</div>`;

    // 2. MFCC MEAN (Timbre)
    html += `<div class="eq-category"><div class="category-title"><i class="fa-solid fa-chart-bar"></i> MFCC Mean (C1 - C10)</div>`;
    for (let i = 0; i < 10; i++) {
        html += genRow(`MFCC Mean ${i + 1}`, inVec[i], outVec[i]);
    }
    html += `</div>`;

    // 3. TEXTURE & HARMONY
    html += `<div class="eq-category"><div class="category-title"><i class="fa-solid fa-wave-square"></i> Texture & Harmony</div>`;
    for (let i = 0; i < 4; i++) {
        html += genRow(`MFCC Std ${i + 1}`, inVec[18 + i], outVec[18 + i]);
    }
    for (let i = 0; i < 4; i++) {
        html += genRow(`Spectral Contrast B${i + 1}`, inVec[14 + i], outVec[14 + i]);
    }
    html += `</div>`;

    eqBoard.innerHTML = html;
}

function genRow(label, inVal, outVal) {
    const getBarCSS = (val) => {
        const width = Math.min(Math.abs(val) * 14.28, 50);
        return val >= 0 ? `left: 50%; width: ${width}%` : `right: 50%; width: ${width}%`;
    };
    const divergeClass = Math.abs(inVal - outVal) > 0.8 ? 'fill-diverge' : '';

    return `
        <div class="eq-row">
            <div class="eq-label">${label}</div>
            <div class="eq-bar-wrapper">
                <div class="eq-center-line"></div>
                <div class="eq-track"><div class="eq-fill fill-input" style="${getBarCSS(inVal)}"></div></div>
                <div class="eq-track"><div class="eq-fill fill-target ${divergeClass}" style="${getBarCSS(outVal)}"></div></div>
            </div>
            <div class="eq-values">
                <span class="text-cyan">${inVal > 0 ? '+' + inVal.toFixed(2) : inVal.toFixed(2)}</span>
                <span class="text-purple">${outVal > 0 ? '+' + outVal.toFixed(2) : outVal.toFixed(2)}</span>
            </div>
        </div>
    `;
}

// Helper Utilities
async function logToTerminal(msg, delay = 0) {
    const line = document.createElement('div');
    line.innerHTML = `> ${msg}`;
    terminalLogs.appendChild(line);
    terminalLogs.scrollTop = terminalLogs.scrollHeight;
    if (delay > 0) await new Promise(r => setTimeout(r, delay));
}

function selectResult(index) {
    document.querySelectorAll('.match-card').forEach(c => c.classList.remove('active'));
    document.getElementById(`result-card-${index}`).classList.add('active');
    renderFullEQBoard(currentQueryVector, currentResults[index].feature_vector);
}

function playAudio(url, btn) {
    const icon = btn.querySelector('i');

    // Nếu đang phát chính bài này -> Tạm dừng
    if (currentAudio && currentPlayingBtn === btn) {
        if (!currentAudio.paused) {
            currentAudio.pause();
            icon.className = 'fa-solid fa-play';
        } else {
            currentAudio.play();
            icon.className = 'fa-solid fa-volume-high';
        }
        return;
    }

    // Nếu đang phát bài khác -> Dừng bài đó, reset icon
    if (currentAudio) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
        if (currentPlayingBtn) {
            currentPlayingBtn.querySelector('i').className = 'fa-solid fa-play';
        }
    }

    // Phát bài mới
    icon.className = 'fa-solid fa-spinner fa-spin';
    currentAudio = new Audio(url);
    currentPlayingBtn = btn;

    currentAudio.play();
    currentAudio.onplaying = () => icon.className = 'fa-solid fa-volume-high';
    currentAudio.onended = () => {
        icon.className = 'fa-solid fa-play';
        currentAudio = null;
        currentPlayingBtn = null;
    };
    currentAudio.onerror = () => {
        alert("Lỗi khi phát âm thanh.");
        icon.className = 'fa-solid fa-circle-exclamation';
    };
}
