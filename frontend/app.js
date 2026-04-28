// --- Global State ---
let currentAudio = null;
let currentPlayBtn = null;
let radarChart = null;
let barChart = null;

let currentQueryVector = [];
let currentResults = [];

// --- DOM Elements ---
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const btnUpload = document.getElementById('btn-upload');

const termBody = document.getElementById('terminal-body');
const resultsList = document.getElementById('results-list');
const searchTimeBadge = document.getElementById('search-time');

const inputPlayerCard = document.getElementById('input-player-card');
const inputFilename = document.getElementById('input-filename');
const inputDuration = document.getElementById('input-duration');
const playInputBtn = document.getElementById('play-input-btn');

// --- Helper: Terminal Simulator ---
async function logToTerminal(msg, delayMs = 300) {
    return new Promise((resolve) => {
        setTimeout(() => {
            const line = document.createElement('div');
            line.className = 'log-line';
            line.innerHTML = `> ${msg}`;
            termBody.appendChild(line);
            termBody.scrollTop = termBody.scrollHeight;
            resolve();
        }, delayMs);
    });
}
function clearTerminal() {
    termBody.innerHTML = '';
}

// --- Chart Initialization ---
function initCharts() {
    Chart.defaults.color = '#8690a6';
    Chart.defaults.font.family = "'Fira Code', monospace";

    // 1. Radar Chart
    const ctxRadar = document.getElementById('radarChart').getContext('2d');
    radarChart = new Chart(ctxRadar, {
        type: 'radar',
        data: {
            labels: ['Attack', 'Bass', 'Vibrato', 'Bright', 'Friction', 'Dyn.Var'],
            datasets: [
                {
                    label: 'Input',
                    data: [],
                    backgroundColor: 'rgba(0, 229, 255, 0.4)',
                    borderColor: '#00e5ff',
                    pointBackgroundColor: '#00e5ff',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true
                },
                {
                    label: 'Target',
                    data: [],
                    backgroundColor: 'rgba(162, 56, 255, 0.4)',
                    borderColor: '#a238ff',
                    pointBackgroundColor: '#a238ff',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    tension: 0.3,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    pointLabels: { font: { size: 10 } },
                    ticks: { display: false },
                    suggestedMin: -3,
                    suggestedMax: 3
                }
            },
            plugins: { legend: { display: false } }
        }
    });

    // 2. Bar Chart (Full 37D Grouped Feature Breakdown)
    const ctxBar = document.getElementById('barChart').getContext('2d');
    barChart = new Chart(ctxBar, {
        type: 'bar',
        data: {
            labels: ['Attack', 'MFCC\nMean', 'MFCC\nStd', 'Spectral\nContrast', 'Centroid', 'ZCR', 'RMS\nVar'],
            datasets: [
                {
                    label: 'Input',
                    data: [],
                    backgroundColor: 'rgba(0, 229, 255, 0.8)',
                    borderRadius: 4
                },
                {
                    label: 'Target',
                    data: [],
                    backgroundColor: 'rgba(162, 56, 255, 0.8)',
                    borderRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { grid: { display: false } },
                y: {
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    suggestedMin: -2,
                    suggestedMax: 2
                }
            },
            plugins: { legend: { display: false } }
        }
    });
}
window.onload = initCharts;

// --- Chart Update Logic ---
function extractRadarAxes(vec) {
    if (!vec || vec.length < 37) return [];
    return [vec[0], vec[1], vec[14], vec[34], vec[35], vec[36]];
}
// Gom 37 chiều thành 7 nhóm đại diện (bao phủ 100% vector)
function extractGroupedFeatures(vec) {
    if (!vec || vec.length < 37) return [];
    const avg = (arr) => arr.reduce((s, v) => s + v, 0) / arr.length;
    return [
        vec[0],                        // [0]     Attack Time
        avg(vec.slice(1, 14)),         // [1-13]  MFCC Mean (avg of 13)
        avg(vec.slice(14, 27)),        // [14-26] MFCC Std  (avg of 13)
        avg(vec.slice(27, 34)),        // [27-33] Spectral Contrast (avg of 7)
        vec[34],                       // [34]    Spectral Centroid
        vec[35],                       // [35]    ZCR
        vec[36]                        // [36]    RMS Std
    ];
}

function updateCharts(inputVec, targetVec) {
    // Update Radar
    radarChart.data.datasets[0].data = extractRadarAxes(inputVec);
    radarChart.data.datasets[1].data = extractRadarAxes(targetVec);
    radarChart.update();

    // Update Bar (Full 37D Grouped)
    barChart.data.datasets[0].data = extractGroupedFeatures(inputVec);
    barChart.data.datasets[1].data = extractGroupedFeatures(targetVec);
    barChart.update();
}

// --- Audio Player Logic ---
function playAudio(url, btnElement) {
    if (currentAudio) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
        if (currentPlayBtn) {
            currentPlayBtn.innerHTML = '<i class="fa-solid fa-play"></i>';
            currentPlayBtn.classList.remove('playing');
        }
    }
    if (currentPlayBtn === btnElement) {
        currentPlayBtn = null;
        return;
    }

    currentAudio = new Audio(url);
    currentAudio.play().catch(e => console.error(e));
    btnElement.innerHTML = '<i class="fa-solid fa-stop"></i>';
    btnElement.classList.add('playing');
    currentPlayBtn = btnElement;

    currentAudio.onended = () => {
        btnElement.innerHTML = '<i class="fa-solid fa-play"></i>';
        btnElement.classList.remove('playing');
        currentPlayBtn = null;
    };
}

// --- Upload Logic ---
dropZone.addEventListener('click', () => fileInput.click());
btnUpload.addEventListener('click', (e) => { e.stopPropagation(); fileInput.click(); });

dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) handleFile(e.target.files[0]);
});

async function handleFile(file) {
    if (!file.name.endsWith('.wav')) {
        alert('Format not supported. Please upload .wav');
        return;
    }

    // Reset UI
    clearTerminal();
    btnUpload.disabled = true;
    inputPlayerCard.classList.add('hidden');
    resultsList.innerHTML = '';
    searchTimeBadge.classList.add('hidden');

    // Terminal sequence
    await logToTerminal(`[System] Initializing SonarStudio Engine...`, 100);
    await logToTerminal(`[IO] Uploading ${file.name} to memory...`, 300);

    const formData = new FormData();
    formData.append('file', file);

    try {
        await logToTerminal(`[API] Waiting for Backend response...`, 200);

        // Let's pretend it takes a bit to parse so user can read terminal
        const [response] = await Promise.all([
            fetch('/api/search', { method: 'POST', body: formData }),
            new Promise(r => setTimeout(r, 600)) // Artificial delay
        ]);

        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Server error');

        await logToTerminal(`[DSP] Extracted ${data.query.extract_sec}s window.`, 200);
        await logToTerminal(`[Math] Normalized vectors via Z-Score.`, 200);
        await logToTerminal(`[DB] Executing pgvector Cosine L2 distance...`, 300);
        await logToTerminal(`[Sys] Found ${data.search_results.length} matches in ${data.timing.db_search_ms}ms!`, 100);

        // Render UI
        renderInputInfo(data.query);
        currentQueryVector = data.query.feature_vector;
        currentResults = data.search_results;

        renderResults();

        // Show Search Time
        searchTimeBadge.innerHTML = `<i class="fa-solid fa-bolt"></i> ${data.timing.db_search_ms}ms`;
        searchTimeBadge.classList.remove('hidden');

    } catch (err) {
        await logToTerminal(`<span style="color:#ff5f56">[Error] ${err.message}</span>`, 0);
    } finally {
        btnUpload.disabled = false;
        await logToTerminal(`> Ready.`, 500);
    }
}

function renderInputInfo(queryData) {
    inputFilename.innerText = queryData.file_name;
    inputDuration.innerText = queryData.extract_sec;
    inputPlayerCard.classList.remove('hidden');
    playInputBtn.onclick = () => playAudio(queryData.audio_url, playInputBtn);
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
                        <div class="inst-text">${res.instrument} / ${res.pitch || '?'} / ${res.dynamics || '?'} / ${res.technique || '?'}</div>
                    </div>
                    <div class="match-score ${rankClass}">${simPercent}%</div>
                </div>
                <!-- Sim Bar -->
                <div class="sim-bar-bg">
                    <div class="sim-bar-fill" style="width: ${simPercent}%"></div>
                </div>
            </div>
        `;
    });
    resultsList.innerHTML = html;

    // Vẽ biểu đồ cho Top 1 ban đầu
    if (currentResults.length > 0) {
        updateCharts(currentQueryVector, currentResults[0].feature_vector);
    }
}

// Bấm vào Result Card nào thì Đè viền Active và Cập nhật Biểu đồ
window.selectResult = function (index) {
    // Remove active class from all
    document.querySelectorAll('.match-card').forEach(c => c.classList.remove('active'));
    // Add active to selected
    document.getElementById(`result-card-${index}`).classList.add('active');

    // Update Chart dynamically
    updateCharts(currentQueryVector, currentResults[index].feature_vector);
}
