/**
 * AUDIO SEARCH ENGINE - CORE LOGIC (Multi-Vector Optimized)
 */

// UI Elements
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const resultsList = document.getElementById('results-list');
const terminalLogs = document.getElementById('terminal-body');
const searchTimeBadge = document.getElementById('search-time');
const eqBoard = document.getElementById('eq-board');

// Metadata & Inspector Elements
const inputFilename = document.getElementById('input-filename');
const inputMetadata = document.getElementById('input-metadata');
const inputDuration = document.getElementById('input-duration');
const inputPlayerCard = document.getElementById('input-player-card');
const inputCardActions = document.getElementById('input-card-actions');
const btnRawInspector = document.getElementById('btn-raw-inspector');
const rawInspectorCard = document.getElementById('raw-inspector-card');
const btnCloseRaw = document.getElementById('btn-close-raw');
const rawDataList = document.getElementById('raw-data-list');
const playInputBtn = document.getElementById('play-input-btn');

// State
let currentResults = [];
let currentQueryData = null;
let currentAudio = null;
let currentPlayingBtn = null;
let inputAudioObjectUrl = null;

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    logToTerminal("System initialized. Multi-Vector Engine Ready.", 500);
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
    resultsList.innerHTML = '<div class="searching-spinner"><i class="fa-solid fa-compact-disc fa-spin fa-3x"></i><p>Extracting Multi-Vector Features...</p></div>';
    rawInspectorCard.classList.add('hidden');

    // Setup input player
    if (inputAudioObjectUrl) URL.revokeObjectURL(inputAudioObjectUrl);
    inputAudioObjectUrl = URL.createObjectURL(file);
    inputPlayerCard.classList.remove('hidden');
    inputCardActions.classList.remove('hidden');

    // Log
    await logToTerminal(`[Sys] Analyzing: ${file.name}`, 100);
    await logToTerminal(`[DSP] Separation: Pitch (3D) & Timbre (18D)...`, 200);

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
        currentQueryData = data.query;

        await logToTerminal(`[DSP] Feature extraction complete. RMS: ${data.query.rms_mean.toFixed(4)}`, 200);
        await logToTerminal(`[DB] Filter-and-Rank Search executed.`, 300);
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
    inputDuration.innerText = queryData.extract_sec;
    const m = queryData.metadata;
    if (m) {
        inputMetadata.innerText = `${m.instrument} / ${m.pitch} / ${m.dynamics} / ${m.technique}${m.string_id && m.string_id !== 'Unknown' ? ' / String ' + m.string_id : ''}`;
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
                        <div class="inst-text">${res.instrument} / ${res.pitch || '?'} / ${res.dynamics || '?'} / ${res.technique || '?'}${res.string_id ? ' / String ' + res.string_id : ''}</div>
                    </div>
                    <div class="match-score ${rankClass}">${simPercent}%</div>
                </div>
                <div class="sim-bar-bg"><div class="sim-bar-fill" style="width: ${simPercent}%"></div></div>
            </div>
        `;
    });
    resultsList.innerHTML = html;

    if (currentResults.length > 0) {
        const inVec = [...currentQueryData.pitch_vector, ...currentQueryData.timbre_vector];
        const outVec = [...currentResults[0].pitch_vector, ...currentResults[0].timbre_vector];
        renderFullEQBoard(inVec, outVec);
    }
}

function renderFullEQBoard(inVec, outVec) {
    if (!inVec || inVec.length < 21) return;

    let html = `
        <div class="text-muted text-sm mb-3">
            <i class="fa-solid fa-circle-info"></i> Hiển thị <b>Z-Score</b>. 
            Mô hình Multi-Vector: Pitch (Euclidean) + Timbre (Cosine).
        </div>
    `;

    // 1. PITCH PILLAR (3D)
    html += `<div class="eq-category"><div class="category-title"><i class="fa-solid fa-music"></i> Pitch Pillar (Exact Match)</div>`;
    html += genRow('Fundamental Pitch (F0)', inVec[0], outVec[0]);
    html += `</div>`;

    // 2. TIMBRE PILLAR - MFCC MEAN (10D)
    html += `<div class="eq-category"><div class="category-title"><i class="fa-solid fa-fingerprint"></i> Timbre: Spectral Envelope (MFCC)</div>`;
    for (let i = 0; i < 10; i++) {
        html += genRow(`MFCC Mean ${i + 1}`, inVec[1 + i], outVec[1 + i]);
    }
    html += `</div>`;

    // 3. TIMBRE PILLAR - TEXTURE (8D)
    html += `<div class="eq-category"><div class="category-title"><i class="fa-solid fa-braille"></i> Timbre: Texture & contrast</div>`;
    for (let i = 0; i < 4; i++) {
        html += genRow(`Spectral Contrast B${i + 1}`, inVec[11 + i], outVec[11 + i]);
    }
    for (let i = 0; i < 4; i++) {
        html += genRow(`MFCC Std ${i + 1}`, inVec[15 + i], outVec[15 + i]);
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

// --- Raw Inspector Logic ---
btnRawInspector.addEventListener('click', () => {
    if (!currentQueryData) return;
    rawInspectorCard.classList.remove('hidden');
    renderRawInspector();
});

btnCloseRaw.addEventListener('click', () => rawInspectorCard.classList.add('hidden'));

function renderRawInspector() {
    const q = currentQueryData;
    let html = `
        <table style="width: 100%; border-collapse: collapse; color: #ffc107;">
            <tr style="border-bottom: 1px solid rgba(255, 193, 7, 0.2);">
                <th style="text-align: left; padding: 4px;">Feature</th>
                <th style="text-align: right; padding: 4px;">Raw Value</th>
            </tr>
            <tr><td style="padding: 4px;">RMS Mean (Energy)</td><td style="text-align: right; color: #fff;">${q.rms_mean.toFixed(6)}</td></tr>
            <tr><td style="padding: 4px;">F0 MIDI (Pitch)</td><td style="text-align: right; color: #fff;">${q.raw_pitch[0].toFixed(2)}</td></tr>
            <tr style="background: rgba(255, 255, 255, 0.05);"><td colspan="2" style="padding: 4px; font-weight: bold;">MFCC Mean (C1-C10)</td></tr>
    `;
    
    q.raw_timbre.slice(0, 10).forEach((val, i) => {
        html += `<tr><td style="padding: 4px; padding-left: 15px;">MFCC C${i+1}</td><td style="text-align: right; color: #fff;">${val.toFixed(4)}</td></tr>`;
    });

    html += `<tr style="background: rgba(255, 255, 255, 0.05);"><td colspan="2" style="padding: 4px; font-weight: bold;">Spectral Contrast (B1-B4)</td></tr>`;
    q.raw_timbre.slice(10, 14).forEach((val, i) => {
        html += `<tr><td style="padding: 4px; padding-left: 15px;">Contrast B${i+1}</td><td style="text-align: right; color: #fff;">${val.toFixed(4)}</td></tr>`;
    });

    html += `</table>`;
    rawDataList.innerHTML = html;
}

// --- Playback Logic ---
playInputBtn.addEventListener('click', () => {
    if (inputAudioObjectUrl) playAudio(inputAudioObjectUrl, playInputBtn);
});

function selectResult(index) {
    document.querySelectorAll('.match-card').forEach(c => c.classList.remove('active'));
    document.getElementById(`result-card-${index}`).classList.add('active');
    const inVec = [...currentQueryData.pitch_vector, ...currentQueryData.timbre_vector];
    const outVec = [...currentResults[index].pitch_vector, ...currentResults[index].timbre_vector];
    renderFullEQBoard(inVec, outVec);
}

function playAudio(url, btn) {
    const icon = btn.querySelector('i');

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

    if (currentAudio) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
        if (currentPlayingBtn) {
            currentPlayingBtn.querySelector('i').className = 'fa-solid fa-play';
        }
    }

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

async function logToTerminal(msg, delay = 0) {
    const line = document.createElement('div');
    line.innerHTML = `> ${msg}`;
    terminalLogs.appendChild(line);
    terminalLogs.scrollTop = terminalLogs.scrollHeight;
    if (delay > 0) await new Promise(r => setTimeout(r, delay));
}
