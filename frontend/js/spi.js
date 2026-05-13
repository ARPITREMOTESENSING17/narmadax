/**
 * spi.js — IMDTools SPI Calculator
 * Handles Standard SPI and AI (Narmada Basin) sections
 */

// ── State ──────────────────────────────────────────────────────────
let currentScale    = 6;
let currentScaleAI  = 12;
let currentCacheKey = null;
let currentAICacheKey = null;
let selectedAnalysis = 'interpretation';
let spiChart = null;
let aiChart  = null;

// ── Scale hints (WMO) ──────────────────────────────────────────────
const SCALE_HINTS = {
  1:  'SPI-1: Short-term drought, soil moisture, crop stress',
  3:  'SPI-3: Seasonal drought, agriculture (Kharif/Rabi)',
  6:  'SPI-6: Seasonal to medium-term moisture conditions',
  9:  'SPI-9: Inter-seasonal, agriculture + other sectors',
  12: 'SPI-12: Hydrological drought, reservoir + groundwater',
  24: 'SPI-24: Long-term drought, multi-year analysis',
};

// ── Tab switching ──────────────────────────────────────────────────
function switchTab(tab) {
  document.getElementById('content-standard').classList.remove('active');
  document.getElementById('content-ai').classList.remove('active');
  document.getElementById('tab-standard').className = 'tab';
  document.getElementById('tab-ai').className = 'tab';

  document.getElementById(`content-${tab}`).classList.add('active');
  if (tab === 'standard') {
    document.getElementById('tab-standard').className = 'tab active-standard';
  } else {
    document.getElementById('tab-ai').className = 'tab active-ai';
    checkOllamaStatus();
  }
}

// ── Scale selection ────────────────────────────────────────────────
function setScale(n, el) {
  currentScale = n;
  document.querySelectorAll('#scaleGrid .scale-btn')
    .forEach(b => b.classList.remove('active'));
  el.classList.add('active');
  document.getElementById('scaleHint').textContent = SCALE_HINTS[n];
}

function setScaleAI(n, el) {
  currentScaleAI = n;
  document.querySelectorAll('#scaleGridAI .scale-btn')
    .forEach(b => {
      b.classList.remove('active', 'active-ai-btn');
    });
  el.classList.add('active', 'active-ai-btn');
}

// ── File selection ─────────────────────────────────────────────────
function onFileSelect(input) {
  const name = input.files[0]?.name || 'No file selected';
  document.getElementById('fileName').textContent = name;
}

function onFileSelectAI(input) {
  const name = input.files[0]?.name || 'No file selected';
  document.getElementById('fileNameAI').textContent = name;
}

// ── Analysis type ──────────────────────────────────────────────────
function selectAnalysis(type, el) {
  selectedAnalysis = type;
  document.querySelectorAll('.analysis-btn')
    .forEach(b => b.classList.remove('selected'));
  el.classList.add('selected');

  // Show/hide Q&A section
  const qaSection = document.getElementById('qaSection');
  if (qaSection) {
    qaSection.style.display = type === 'qa' ? 'block' : 'none';
  }
}

// ── Status helpers ─────────────────────────────────────────────────
function setStatus(id, msg, type) {
  const el = document.getElementById(id);
  el.className = `status ${type}`;
  el.innerHTML = msg;
}

function clearStatus(id) {
  const el = document.getElementById(id);
  el.className = 'status';
  el.textContent = '';
}

// ── Render SPI chart ───────────────────────────────────────────────
function renderChart(containerId, chartData, scale) {
  const canvas = document.getElementById(containerId);
  if (!canvas) return;

  if (containerId === 'spiChart' && spiChart) {
    spiChart.destroy(); spiChart = null;
  }
  if (containerId === 'aiSpiChart' && aiChart) {
    aiChart.destroy(); aiChart = null;
  }

  const labels = chartData.labels;
  const spiVals = chartData.spi;
  const colors  = chartData.colors;

  const chart = new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: `SPI-${scale}`,
        data: spiVals,
        backgroundColor: colors,
        borderWidth: 0,
        borderRadius: 1,
      }, {
        label: 'Zero line',
        data: labels.map(() => 0),
        type: 'line',
        borderColor: '#ffffff33',
        borderWidth: 1,
        pointRadius: 0,
        tension: 0,
      }, {
        label: 'Drought threshold (-1.0)',
        data: labels.map(() => -1.0),
        type: 'line',
        borderColor: '#FDD835aa',
        borderWidth: 1,
        borderDash: [4, 4],
        pointRadius: 0,
        tension: 0,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => {
              const v = ctx.raw;
              if (v === null || v === undefined) return 'No data';
              const cat = getSPICategory(v);
              return `SPI-${scale}: ${v?.toFixed(2)} — ${cat}`;
            }
          }
        }
      },
      scales: {
        x: {
          ticks: {
            color: '#64748b',
            font: { size: 9 },
            maxTicksLimit: 20,
            maxRotation: 45,
          },
          grid: { color: '#1e2d4033' }
        },
        y: {
          ticks: { color: '#64748b', font: { size: 10 } },
          grid: { color: '#1e2d4066' },
          min: -3,
          max:  3,
        }
      }
    }
  });

  if (containerId === 'spiChart') spiChart = chart;
  else aiChart = chart;
}

function getSPICategory(v) {
  if (v >= 2.0)  return 'Extremely Wet';
  if (v >= 1.5)  return 'Severely Wet';
  if (v >= 1.0)  return 'Moderately Wet';
  if (v >= -1.0) return 'Near Normal';
  if (v >= -1.5) return 'Moderate Drought';
  if (v >= -2.0) return 'Severe Drought';
  return 'Extreme Drought';
}

// ── Render results panel ───────────────────────────────────────────
function renderResults(data, panelId, chartId, isAI = false) {
  const s = data.statistics;
  const accent = isAI ? 'var(--accent-a)' : 'var(--accent-s)';

  // Build decade table rows
  let decadeRows = '';
  const decades = s.decade_drought_freq || {};
  for (const [dec, freq] of Object.entries(decades)) {
    const w = Math.min(freq, 100);
    decadeRows += `
      <tr>
        <td>${dec}</td>
        <td>
          <span class="freq-bar" style="width:${w}px;"></span>
          ${freq}%
        </td>
      </tr>`;
  }

  document.getElementById(panelId).innerHTML = `
    <!-- Stats -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">Mean SPI</div>
        <div class="stat-value" style="color:${s.mean_spi < 0 ? '#EF6C00' : '#42A5F5'}">
          ${s.mean_spi?.toFixed(2)}
        </div>
        <div class="stat-sub">SPI-${data.scale}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Drought Months</div>
        <div class="stat-value" style="color:#FDD835">${s.drought_months}</div>
        <div class="stat-sub">${s.drought_pct}% of record</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Extreme Drought</div>
        <div class="stat-value" style="color:#B71C1C">${s.extreme_drought_months}</div>
        <div class="stat-sub">SPI ≤ -2.0 months</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Longest Spell</div>
        <div class="stat-value" style="color:${accent}">${s.longest_drought_spell}</div>
        <div class="stat-sub">consecutive months</div>
      </div>
    </div>

    <!-- Chart -->
    <div class="chart-wrap">
      <canvas id="${chartId}"></canvas>
    </div>

    <!-- Info row -->
    <div style="display:flex;gap:16px;margin-bottom:12px;font-size:11px;color:var(--muted)">
      <span>📍 ${data.point.lat}°N, ${data.point.lon}°E</span>
      <span>📅 Reference: ${data.ref_period}</span>
      <span>📊 ${data.n_years} years | ${data.n_points} grid points</span>
    </div>

    <!-- Decade table -->
    <div class="card" style="margin-bottom:0">
      <div class="card-title">Drought Frequency by Decade</div>
      <table class="decade-table">
        <thead>
          <tr><th>Decade</th><th>Drought Frequency (%)</th></tr>
        </thead>
        <tbody>${decadeRows || '<tr><td colspan="2" style="color:var(--muted)">Not enough data</td></tr>'}</tbody>
      </table>
    </div>

    <!-- Export -->
    <div class="export-bar">
      <button class="btn btn-outline"
              onclick="exportSPI('${data.cache_key}')">
        ↓ Export CSV
      </button>
    </div>
  `;

  // Render chart after DOM update
  setTimeout(() => renderChart(chartId, data.chart, data.scale), 50);
}

// ═══════════════════════════════════════════════════════════════════
// STANDARD SPI CALCULATION
// ═══════════════════════════════════════════════════════════════════

async function calculateSPI() {
  const fileInput = document.getElementById('csvFile');
  if (!fileInput.files[0]) {
    setStatus('statusStd', '⚠ Please upload a rainfall CSV file', 'warning');
    return;
  }

  const btn = document.getElementById('calcBtn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>Calculating...';
  setStatus('statusStd', '<span class="spinner"></span>Processing...', 'info');

  const formData = new FormData();
  formData.append('file',          fileInput.files[0]);
  formData.append('scale',         currentScale);
  formData.append('ref_start_yr',  document.getElementById('refStart').value);
  formData.append('ref_end_yr',    document.getElementById('refEnd').value);
  formData.append('basin_filter',  document.getElementById('basinFilter').value);

  const lat = document.getElementById('pointLat').value;
  const lon = document.getElementById('pointLon').value;
  if (lat && lon) formData.append('single_point', `${lat},${lon}`);

  try {
    const res  = await fetch('/api/spi/calculate', {
      method: 'POST', body: formData,
      headers: { 'ngrok-skip-browser-warning': 'true' }
    });
    const data = await res.json();

    if (!res.ok) {
      setStatus('statusStd', `❌ ${data.error}`, 'error');
      return;
    }

    if (data.warning) {
      setStatus('statusStd', `⚠ ${data.warning}`, 'warning');
      return;
    }

    currentCacheKey = data.cache_key;
    renderResults(data, 'resultsPanel', 'spiChart', false);
    clearStatus('statusStd');

  } catch (err) {
    setStatus('statusStd', `❌ Error: ${err.message}`, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Calculate SPI';
  }
}

function exportSPI(cacheKey) {
  const a = document.createElement('a');
  a.href = `/api/spi/export/${cacheKey}`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

// ═══════════════════════════════════════════════════════════════════
// AI SPI — NARMADA BASIN
// ═══════════════════════════════════════════════════════════════════

async function checkOllamaStatus() {
  try {
    const res  = await fetch('/api/spi/ai/status', {
      headers: { 'ngrok-skip-browser-warning': 'true' }
    });
    const data = await res.json();

    const dot  = document.getElementById('aiDot');
    const text = document.getElementById('aiStatusText');

    if (data.ollama_running) {
      dot.classList.add('online');
      const models = data.models.length > 0
        ? data.models.join(', ')
        : 'No models pulled yet';
      text.textContent = `Ollama online — Models: ${models}`;
    } else {
      dot.classList.remove('online');
      text.textContent = 'Ollama offline — Run: ollama serve';
    }
  } catch {
    document.getElementById('aiStatusText').textContent =
      'Could not reach Ollama';
  }
}

async function calculateSPIAI() {
  const fileInput = document.getElementById('csvFileAI');
  if (!fileInput.files[0]) {
    setStatus('statusAI', '⚠ Please upload a rainfall CSV file', 'warning');
    return;
  }

  const btn = document.getElementById('calcBtnAI');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>Calculating...';
  setStatus('statusAI', '<span class="spinner"></span>Processing Narmada Basin...', 'info');

  const formData = new FormData();
  formData.append('file',         fileInput.files[0]);
  formData.append('scale',        currentScaleAI);
  formData.append('ref_start_yr', '1951');
  formData.append('ref_end_yr',   '2010');
  formData.append('basin_filter', 'narmada');

  try {
    const res  = await fetch('/api/spi/calculate', {
      method: 'POST', body: formData,
      headers: { 'ngrok-skip-browser-warning': 'true' }
    });
    const data = await res.json();

    if (!res.ok) {
      setStatus('statusAI', `❌ ${data.error}`, 'error');
      return;
    }

    currentAICacheKey = data.cache_key;
    document.getElementById('analyseBtn').disabled = false;

    renderResults(data, 'aiResultsTop', 'aiSpiChart', true);
    clearStatus('statusAI');
    setStatus('statusAI',
      '✅ SPI calculated. Now select analysis type and click Run AI Analysis.',
      'success');

  } catch (err) {
    setStatus('statusAI', `❌ Error: ${err.message}`, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Calculate + Analyse';
  }
}

async function runAIAnalysis() {
  if (!currentAICacheKey) {
    setStatus('statusAI', '⚠ Calculate SPI first', 'warning');
    return;
  }

  const btn = document.getElementById('analyseBtn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>AI is thinking...';

  const outputCard  = document.getElementById('aiOutputCard');
  const outputEl    = document.getElementById('aiOutput');
  const titleEl     = document.getElementById('aiOutputTitle');
  const exportBar   = document.getElementById('aiExportBar');
  const qaSection   = document.getElementById('qaSection');

  const titles = {
    interpretation: '📝 AI Interpretation',
    patterns:       '🔍 Pattern Analysis',
    gde_impact:     '🌿 GDE Impact Assessment',
    qa:             '💬 Q&A',
  };

  titleEl.textContent = titles[selectedAnalysis] || 'AI Analysis';
  outputEl.textContent = '';
  outputEl.classList.add('streaming');
  outputCard.style.display = 'block';
  exportBar.style.display = 'none';
  qaSection.style.display = selectedAnalysis === 'qa' ? 'block' : 'none';

  if (selectedAnalysis === 'qa') {
    btn.disabled = false;
    btn.textContent = 'Run AI Analysis';
    outputEl.classList.remove('streaming');
    outputEl.innerHTML = '<span class="ai-placeholder">Type your question below and press Ask →</span>';
    return;
  }

  const model = document.getElementById('aiModel').value;

  try {
    const res = await fetch('/api/spi/ai/interpret', {
      method:  'POST',
      headers: {
        'Content-Type': 'application/json',
        'ngrok-skip-browser-warning': 'true'
      },
      body: JSON.stringify({
        cache_key:     currentAICacheKey,
        analysis_type: selectedAnalysis,
        model,
      })
    });

    if (!res.ok) {
      const err = await res.json();
      outputEl.textContent = `❌ ${err.error}`;
      outputEl.classList.remove('streaming');
      return;
    }

    // Stream response
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let fullText = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      fullText += chunk;
      outputEl.textContent = fullText;
      outputEl.scrollTop = outputEl.scrollHeight;
    }

    outputEl.classList.remove('streaming');
    exportBar.style.display = 'flex';

  } catch (err) {
    outputEl.textContent = `❌ Error: ${err.message}`;
    outputEl.classList.remove('streaming');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Run AI Analysis';
  }
}

async function sendQuestion() {
  const input    = document.getElementById('qaInput');
  const question = input.value.trim();
  if (!question) return;

  const outputEl  = document.getElementById('aiOutput');
  const model     = document.getElementById('aiModel').value;

  outputEl.textContent = '';
  outputEl.classList.add('streaming');
  input.value = '';

  try {
    const res = await fetch('/api/spi/ai/ask', {
      method:  'POST',
      headers: {
        'Content-Type': 'application/json',
        'ngrok-skip-browser-warning': 'true'
      },
      body: JSON.stringify({
        cache_key: currentAICacheKey,
        question,
        model,
      })
    });

    const reader  = res.body.getReader();
    const decoder = new TextDecoder();
    let fullText  = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      fullText += decoder.decode(value, { stream: true });
      outputEl.textContent = fullText;
      outputEl.scrollTop   = outputEl.scrollHeight;
    }

    outputEl.classList.remove('streaming');
    document.getElementById('aiExportBar').style.display = 'flex';

  } catch (err) {
    outputEl.textContent = `❌ Error: ${err.message}`;
    outputEl.classList.remove('streaming');
  }
}

function copyAIOutput() {
  const text = document.getElementById('aiOutput').textContent;
  navigator.clipboard.writeText(text).then(() => {
    alert('Copied to clipboard!');
  });
}

function downloadAIReport() {
  const text = document.getElementById('aiOutput').textContent;
  const blob = new Blob([text], { type: 'text/plain' });
  const a    = document.createElement('a');
  a.href     = URL.createObjectURL(blob);
  a.download = `Narmada_SPI_AI_Report_${new Date().toISOString().slice(0,10)}.txt`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

// ── Init ───────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  checkOllamaStatus();
});