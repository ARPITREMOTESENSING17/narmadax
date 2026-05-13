// ============================================================
//  APP STATE
// ============================================================
let currentFileId    = null;
let currentFileType  = null;
let currentNDays     = null;
let currentStartDate = null;

// ============================================================
//  CALENDAR STATE
// ============================================================
let _calResolve    = null;
let _calViewYear   = null;
let _calViewMonth  = null;
let _calValidStart = null;   // first available Date
let _calValidEnd   = null;   // last  available Date
let _rangeFrom     = null;   // selected From Date
let _rangeTo       = null;   // selected To   Date
let _hoverDate     = null;   // live hover preview
let _pickingStep   = 'from'; // 'from' | 'to' | 'done'
let _calShowAll    = false;

const MONTHS = ['January','February','March','April','May','June',
                'July','August','September','October','November','December'];
const DOW    = ['Su','Mo','Tu','We','Th','Fr','Sa'];

// ============================================================
//  INJECT CALENDAR MODAL (runs once on page load)
// ============================================================
(function injectCalendar() {
  if (document.getElementById('imd-cal-overlay')) return;

  // ── Styles ──────────────────────────────────────────────
  const style = document.createElement('style');
  style.textContent = `
    #imd-cal-overlay {
      display:none; position:fixed; inset:0;
      background:rgba(15,30,60,0.35);
      z-index:9999; align-items:center; justify-content:center;
    }
    #imd-cal-overlay.open { display:flex; }

    #imd-cal-box {
      background:#ffffff; border:1px solid #dde3ed;
      border-radius:16px; width:380px;
      box-shadow:0 12px 48px rgba(0,40,100,0.15);
      font-family:'JetBrains Mono',monospace;
      overflow:hidden; animation:calIn .18s ease;
    }
    @keyframes calIn { from{transform:scale(0.9);opacity:0;} to{transform:scale(1);opacity:1;} }

    /* header */
    #imd-cal-header {
      background:#f8fafc; padding:16px 20px 12px;
      border-bottom:1px solid #dde3ed;
    }
    #imd-cal-header h3 {
      margin:0 0 10px; font-size:13px; font-weight:700;
      color:#00d4ff; letter-spacing:1px; text-transform:uppercase;
    }

    /* from / to pills */
    #imd-cal-range-pills { display:flex; gap:8px; align-items:center; }
    .cal-pill {
      flex:1; padding:8px 10px; border-radius:8px;
      border:1px solid #dde3ed; background:#f0f4f8;
      font-size:11px; transition:all .2s;
    }
    .cal-pill .pill-label {
      font-size:9px; color:#8a95a3;
      text-transform:uppercase; letter-spacing:.8px; margin-bottom:3px;
    }
    .cal-pill .pill-val { color:#8a95a3; font-size:12px; }
    .cal-pill.active {
      border-color:#0066ff; background:rgba(0,102,255,0.07);
      box-shadow:0 0 0 3px rgba(0,102,255,0.12);
    }
    .cal-pill.from-filled .pill-val { color:#22d3a0; }
    .cal-pill.to-filled   .pill-val { color:#0d9e74; }
    .cal-arrow { color:#c8d2e0; font-size:20px; flex-shrink:0; }

    /* year strip */
    #imd-cal-year-row {
      display:none; gap:6px; padding:8px 16px;
      flex-wrap:wrap; border-bottom:1px solid #dde3ed; background:#111827;
    }
    .imd-cal-yr-btn {
      padding:3px 10px; border-radius:5px; cursor:pointer;
      border:1px solid #dde3ed; background:transparent;
      color:#8a95a3; font-family:inherit; font-size:11px; transition:all .15s;
    }
    .imd-cal-yr-btn:hover { border-color:#0066ff; color:#0066ff; }
    .imd-cal-yr-btn.active {
      background:rgba(0,102,255,0.08); border-color:#0066ff; color:#0066ff;
    }

    /* month nav */
    #imd-cal-nav {
      display:flex; align-items:center; justify-content:space-between;
      padding:10px 16px; border-bottom:1px solid #dde3ed;
    }
    #imd-cal-nav button {
      background:transparent; border:1px solid #dde3ed; border-radius:6px;
      color:#1a2332; width:32px; height:32px; cursor:pointer;
      font-size:18px; display:flex; align-items:center; justify-content:center;
      transition:all .15s;
    }
    #imd-cal-nav button:hover { background:rgba(0,102,255,0.08); border-color:#0066ff; }
    #imd-cal-nav button:disabled { opacity:.3; cursor:not-allowed; }
    #imd-cal-month-label { font-size:13px; font-weight:600; color:#1a2332; }

    /* grid */
    #imd-cal-grid {
      display:grid; grid-template-columns:repeat(7,1fr);
      gap:1px; padding:10px 12px 6px;
    }
    .imd-cal-dow {
      text-align:center; font-size:9px; color:#8a95a3;
      padding:4px 0; text-transform:uppercase; letter-spacing:.5px;
    }
    .imd-cal-day {
      position:relative; text-align:center; padding:7px 2px;
      font-size:12px; cursor:pointer; color:#1a2332;
      border-radius:6px; user-select:none;
    }
    .imd-cal-day:hover:not(.disabled):not(.empty) {
      background:rgba(0,102,255,0.08);
    }
    .imd-cal-day.empty   { cursor:default; }
    .imd-cal-day.disabled { color:#c8d2e0 !important; cursor:not-allowed; }

    /* range band */
    .imd-cal-day.in-range {
      background:rgba(0,102,255,0.10); border-radius:0; color:#1a2332;
    }
    .imd-cal-day.in-range-preview {
      background:rgba(0,102,255,0.05); border-radius:0; color:#4a6080;
    }

    /* endpoints */
    .imd-cal-day.range-from {
      background:#22d3a0 !important; border-radius:6px 0 0 6px;
      color:#003322 !important; font-weight:700;
      box-shadow:0 0 12px rgba(34,211,160,0.45);
    }
    .imd-cal-day.range-to {
      background:#38bdf8 !important; border-radius:0 6px 6px 0;
      color:#001e33 !important; font-weight:700;
      box-shadow:0 0 12px rgba(56,189,248,0.45);
    }
    .imd-cal-day.range-from.range-to {
      border-radius:6px !important; background:#0066ff !important;
      color:#fff !important; box-shadow:0 0 14px rgba(0,102,255,0.5);
    }
    /* hover-preview "to" highlight */
    .imd-cal-day.hover-to {
      background:#38bdf8 !important; border-radius:0 6px 6px 0;
      color:#001e33 !important; font-weight:700;
      box-shadow:0 0 12px rgba(56,189,248,0.3);
    }

    .imd-cal-day .day-idx {
      display:block; font-size:7px; color:#0066ff;
      margin-top:1px; line-height:1; opacity:.7;
    }
    .range-from .day-idx,
    .range-to   .day-idx,
    .hover-to   .day-idx { color:rgba(0,0,0,0.5); opacity:1; }

    /* step hint */
    #imd-cal-step-hint {
      text-align:center; padding:7px 16px;
      font-size:11px; color:#64748b;
      border-top:1px solid #dde3ed; background:#f8fafc;
    }
    #imd-cal-step-hint span { color:#0066ff; font-weight:600; }

    /* summary */
    #imd-cal-summary {
      padding:10px 16px; background:rgba(0,212,255,0.04);
      border-top:1px solid #dde3ed; font-size:11px;
      color:#4a5568; line-height:1.9; display:none;
    }
    #imd-cal-summary.show { display:block; }
    #imd-cal-summary strong { color:#1a2332; }
    #imd-cal-summary .sum-days { color:#0066ff; font-size:14px; font-weight:700; }

    /* all-days toggle */
    #imd-cal-all-row {
      display:none; align-items:center; gap:10px;
      padding:8px 16px; border-top:1px solid #dde3ed;
      font-size:11px; color:#4a5568;
    }
    #imd-cal-all-row label {
      cursor:pointer; display:flex; align-items:center; gap:6px;
    }
    #imd-cal-all-check {
      accent-color:#0066ff; width:14px; height:14px; cursor:pointer;
    }

    /* footer */
    #imd-cal-footer {
      display:flex; gap:8px; padding:12px 16px;
      justify-content:space-between; border-top:1px solid #dde3ed;
    }
    #imd-cal-clear {
      padding:8px 14px; border-radius:7px;
      border:1px solid #dde3ed; background:transparent;
      color:#8a95a3; font-family:inherit; font-size:11px;
      cursor:pointer; transition:all .15s;
    }
    #imd-cal-clear:hover { border-color:#ef4444; color:#ef4444; }
    .cal-footer-right { display:flex; gap:8px; }
    #imd-cal-cancel {
      padding:8px 16px; border-radius:7px;
      border:1px solid #dde3ed; background:transparent;
      color:#8a95a3; font-family:inherit; font-size:12px;
      cursor:pointer; transition:all .15s;
      text-transform:uppercase; letter-spacing:.5px;
    }
    #imd-cal-cancel:hover { border-color:#ef4444; color:#ef4444; }
    #imd-cal-confirm {
      padding:8px 20px; border-radius:7px; border:none;
      background:#0066ff; color:#fff; font-family:inherit;
      font-size:12px; cursor:pointer;
      text-transform:uppercase; letter-spacing:.5px;
      font-weight:700; transition:all .15s;
    }
    #imd-cal-confirm:hover:not(:disabled) {
      background:#0055dd; box-shadow:0 4px 16px rgba(0,102,255,0.4);
    }
    #imd-cal-confirm:disabled {
      background:#eef2f7; color:#b0b8c4; cursor:not-allowed;
    }
  `;
  document.head.appendChild(style);

  // ── HTML ────────────────────────────────────────────────
  document.body.insertAdjacentHTML('beforeend', `
  <div id="imd-cal-overlay">
    <div id="imd-cal-box">

      <div id="imd-cal-header">
        <h3 id="imd-cal-title">📅 Select Date Range</h3>
        <div id="imd-cal-range-pills">
          <div class="cal-pill" id="pill-from">
            <div class="pill-label">📗 From</div>
            <div class="pill-val" id="pill-from-val">Select start date</div>
          </div>
          <span class="cal-arrow">→</span>
          <div class="cal-pill" id="pill-to">
            <div class="pill-label">📘 To</div>
            <div class="pill-val" id="pill-to-val">Select end date</div>
          </div>
        </div>
      </div>

      <div id="imd-cal-year-row"></div>

      <div id="imd-cal-nav">
        <button id="imd-cal-prev">&#8249;</button>
        <span id="imd-cal-month-label"></span>
        <button id="imd-cal-next">&#8250;</button>
      </div>

      <div id="imd-cal-grid"></div>

      <div id="imd-cal-step-hint">
        Click to select <span id="hint-step">start</span> date
      </div>

      <div id="imd-cal-summary">
        <div>From <strong id="sum-from">—</strong> → <strong id="sum-to">—</strong></div>
        <div>
          <span class="sum-days" id="sum-days">—</span> days &nbsp;
          <span style="color:#8a95a3;font-size:10px;" id="sum-idx"></span>
        </div>
      </div>

      <div id="imd-cal-all-row">
        <label>
          <input type="checkbox" id="imd-cal-all-check">
          Select entire dataset (all <span id="all-n-days">—</span> days)
        </label>
      </div>

      <div id="imd-cal-footer">
        <button id="imd-cal-clear">✕ Clear</button>
        <div class="cal-footer-right">
          <button id="imd-cal-cancel">Cancel</button>
          <button id="imd-cal-confirm" disabled>Confirm Range</button>
        </div>
      </div>

    </div>
  </div>`);

  // ── Wire Events ──────────────────────────────────────────
  document.getElementById('imd-cal-prev').addEventListener('click', () => {
    _calViewMonth--;
    if (_calViewMonth < 0) { _calViewMonth = 11; _calViewYear--; }
    _renderCal();
  });
  document.getElementById('imd-cal-next').addEventListener('click', () => {
    _calViewMonth++;
    if (_calViewMonth > 11) { _calViewMonth = 0; _calViewYear++; }
    _renderCal();
  });
  document.getElementById('imd-cal-cancel').addEventListener('click',
    () => _closeCal(null));
  document.getElementById('imd-cal-clear').addEventListener('click',
    _clearRange);
  document.getElementById('imd-cal-overlay').addEventListener('click', e => {
    if (e.target.id === 'imd-cal-overlay') _closeCal(null);
  });
  document.getElementById('imd-cal-all-check').addEventListener('change', function () {
    if (this.checked) {
      _rangeFrom   = new Date(_calValidStart);
      _rangeTo     = new Date(_calValidEnd);
      _pickingStep = 'done';
      _updatePills();
      _updateSummary();
      _renderCal();
      document.getElementById('imd-cal-confirm').disabled = false;
    } else {
      _clearRange();
    }
  });
  document.getElementById('imd-cal-confirm').addEventListener('click', () => {
    if (_rangeFrom && _rangeTo) {
      _closeCal({
        from:      _rangeFrom,
        to:        _rangeTo,
        fromIndex: _dateToIdx(_rangeFrom),
        toIndex:   _dateToIdx(_rangeTo),
        isAll:     document.getElementById('imd-cal-all-check').checked
      });
    }
  });
})();

// ============================================================
//  CALENDAR HELPERS
// ============================================================
function _parseDate(str) {
  if (!str) return null;
  str = str.trim();
  if (/^\d{4}-\d{2}-\d{2}$/.test(str)) return new Date(str + 'T00:00:00');
  if (/^\d{8}$/.test(str))
    return new Date(`${str.slice(0,4)}-${str.slice(4,6)}-${str.slice(6,8)}T00:00:00`);
  const d = new Date(str);
  return isNaN(d) ? null : d;
}

function _dateToIdx(d) {
  return Math.round((d - _calValidStart) / 86400000);
}

function _sameDay(a, b) {
  return a && b &&
    a.getFullYear() === b.getFullYear() &&
    a.getMonth()    === b.getMonth()    &&
    a.getDate()     === b.getDate();
}

function _fmtDate(d) {
  if (!d) return '—';
  return `${d.getDate().toString().padStart(2,'0')} ${MONTHS[d.getMonth()].slice(0,3)} ${d.getFullYear()}`;
}

// ── Range logic ──────────────────────────────────────────────
function _clearRange() {
  _rangeFrom = _rangeTo = _hoverDate = null;
  _pickingStep = 'from';
  document.getElementById('imd-cal-all-check').checked = false;
  document.getElementById('imd-cal-confirm').disabled  = true;
  document.getElementById('imd-cal-summary').classList.remove('show');
  _updatePills();
  _renderCal();
}

function _updatePills() {
  const pFrom = document.getElementById('pill-from');
  const pTo   = document.getElementById('pill-to');
  pFrom.className = 'cal-pill' +
    (_pickingStep === 'from' ? ' active'      : '') +
    (_rangeFrom              ? ' from-filled' : '');
  pTo.className = 'cal-pill' +
    (_pickingStep === 'to'   ? ' active'      : '') +
    (_rangeTo                ? ' to-filled'   : '');
  document.getElementById('pill-from-val').textContent =
    _rangeFrom ? _fmtDate(_rangeFrom) : 'Select start date';
  document.getElementById('pill-to-val').textContent =
    _rangeTo   ? _fmtDate(_rangeTo)   : 'Select end date';
  document.getElementById('hint-step').textContent =
    _pickingStep === 'from' ? 'start' : 'end';
  document.getElementById('imd-cal-step-hint').style.display =
    _pickingStep === 'done' ? 'none' : 'block';
}

function _updateSummary() {
  if (!_rangeFrom || !_rangeTo) {
    document.getElementById('imd-cal-summary').classList.remove('show');
    return;
  }
  const days = _dateToIdx(_rangeTo) - _dateToIdx(_rangeFrom) + 1;
  document.getElementById('sum-from').textContent = _fmtDate(_rangeFrom);
  document.getElementById('sum-to').textContent   = _fmtDate(_rangeTo);
  document.getElementById('sum-days').textContent = days;
  document.getElementById('sum-idx').textContent  =
    `(Day ${_dateToIdx(_rangeFrom)} → Day ${_dateToIdx(_rangeTo)})`;
  document.getElementById('imd-cal-summary').classList.add('show');
  document.getElementById('imd-cal-confirm').disabled = false;
}

// ── Render calendar ──────────────────────────────────────────
function _renderCal() {
  const yr = _calViewYear, mo = _calViewMonth;
  document.getElementById('imd-cal-month-label').textContent =
    `${MONTHS[mo]} ${yr}`;

  // prev / next guards
  const firstOfMo = new Date(yr, mo, 1);
  const lastOfMo  = new Date(yr, mo + 1, 0);
  document.getElementById('imd-cal-prev').disabled =
    !!(_calValidStart && lastOfMo  < _calValidStart);
  document.getElementById('imd-cal-next').disabled =
    !!(_calValidEnd   && firstOfMo > _calValidEnd);

  // year strip
  if (_calValidStart && _calValidEnd) {
    const sy    = _calValidStart.getFullYear();
    const ey    = _calValidEnd.getFullYear();
    const years = Array.from({ length: ey - sy + 1 }, (_, i) => sy + i);
    const yearRow = document.getElementById('imd-cal-year-row');
    yearRow.innerHTML = years.map(y =>
      `<button class="imd-cal-yr-btn${y === yr ? ' active' : ''}"
               data-y="${y}">${y}</button>`
    ).join('');
    yearRow.style.display = years.length > 1 ? 'flex' : 'none';
    yearRow.querySelectorAll('.imd-cal-yr-btn').forEach(b =>
      b.addEventListener('click', () => {
        _calViewYear = +b.dataset.y; _renderCal();
      })
    );
  }

  // build day cells
  const grid      = document.getElementById('imd-cal-grid');
  grid.innerHTML  = DOW.map(d =>
    `<div class="imd-cal-dow">${d}</div>`).join('');

  const startDow = new Date(yr, mo, 1).getDay();
  const daysInMo = new Date(yr, mo + 1, 0).getDate();

  for (let i = 0; i < startDow; i++)
    grid.insertAdjacentHTML('beforeend',
      '<div class="imd-cal-day empty"></div>');

  for (let d = 1; d <= daysInMo; d++) {
    const date       = new Date(yr, mo, d);
    const isDisabled =
      (_calValidStart && date < _calValidStart) ||
      (_calValidEnd   && date > _calValidEnd);
    const idx = (!isDisabled && _calValidStart) ? _dateToIdx(date) : null;

    const isFrom    = !!(  _rangeFrom && _sameDay(date, _rangeFrom));
    const isTo      = !!(_rangeTo   && _sameDay(date, _rangeTo));
    const inRange   = !!(
      _rangeFrom && _rangeTo && date > _rangeFrom && date < _rangeTo);

    const classes = ['imd-cal-day',
      isDisabled ? 'disabled'   : '',
      isFrom     ? 'range-from' : '',
      isTo       ? 'range-to'   : '',
      inRange    ? 'in-range'   : ''
    ].filter(Boolean).join(' ');

    grid.insertAdjacentHTML('beforeend', `
      <div class="${classes}"
           data-ts="${date.getTime()}"
           data-disabled="${!!isDisabled}">
        ${d}
        ${idx !== null
          ? `<span class="day-idx">D${idx}</span>`
          : ''}
      </div>`);
  }

  // ── Events — KEY FIX: hover updates classes in-place, no DOM rebuild ──
  const allDayEls = Array.from(
    grid.querySelectorAll('.imd-cal-day:not(.empty)'));

  function applyHoverClasses() {
    allDayEls.forEach(el => {
      if (el.dataset.disabled === 'true') return;
      const d = new Date(+el.dataset.ts);

      // in-range preview band
      const showPreview = _pickingStep === 'to' && _rangeFrom && _hoverDate;
      const previewLo   = showPreview
        ? (_hoverDate >= _rangeFrom ? _rangeFrom : _hoverDate) : null;
      const previewHi   = showPreview
        ? (_hoverDate >= _rangeFrom ? _hoverDate : _rangeFrom) : null;
      el.classList.toggle('in-range-preview',
        !!(previewLo && previewHi && d > previewLo && d < previewHi));

      // hover-to highlight on the hovered cell itself
      el.classList.toggle('hover-to',
        !!(_pickingStep === 'to' && _hoverDate && _sameDay(d, _hoverDate)));
    });
  }

  allDayEls.forEach(el => {
    if (el.dataset.disabled === 'true') return;
    const date = new Date(+el.dataset.ts);

    el.addEventListener('mouseenter', () => {
      if (_pickingStep !== 'to') return;
      _hoverDate = date;
      applyHoverClasses();   // ← class update only, NO _renderCal() call
    });

    el.addEventListener('mouseleave', () => {
      if (_pickingStep !== 'to') return;
      _hoverDate = null;
      applyHoverClasses();
    });

    el.addEventListener('click', () => {
      document.getElementById('imd-cal-all-check').checked = false;

      if (_pickingStep === 'from' || _pickingStep === 'done') {
        // Start new selection
        _rangeFrom   = date;
        _rangeTo     = null;
        _hoverDate   = null;
        _pickingStep = 'to';
        document.getElementById('imd-cal-confirm').disabled = true;
        document.getElementById('imd-cal-summary').classList.remove('show');
        _updatePills();
        _renderCal();              // full rebuild only on FROM click

      } else {
        // Finish selection
        if (date < _rangeFrom) { _rangeTo = _rangeFrom; _rangeFrom = date; }
        else                   { _rangeTo = date; }
        _hoverDate   = null;
        _pickingStep = 'done';
        _updatePills();
        _updateSummary();
        _renderCal();              // full rebuild to lock in final state
      }
    });
  });
}

// ── Open / Close ─────────────────────────────────────────────
function _openCalendar({ title = 'Select Date Range', showAll = false } = {}) {
  return new Promise(resolve => {
    _calResolve  = resolve;
    _rangeFrom   = _rangeTo = _hoverDate = null;
    _pickingStep = 'from';

    document.getElementById('imd-cal-title').textContent         = `📅 ${title}`;
    document.getElementById('imd-cal-confirm').disabled          = true;
    document.getElementById('imd-cal-confirm').textContent       = 'Confirm Range';
    document.getElementById('imd-cal-summary').classList.remove('show');
    document.getElementById('imd-cal-all-check').checked         = false;
    document.getElementById('imd-cal-all-row').style.display     = showAll ? 'flex' : 'none';
    document.getElementById('all-n-days').textContent            = currentNDays || '—';

    _calViewYear  = _calValidStart
      ? _calValidStart.getFullYear() : new Date().getFullYear();
    _calViewMonth = _calValidStart
      ? _calValidStart.getMonth()    : new Date().getMonth();

    _updatePills();
    _renderCal();
    document.getElementById('imd-cal-overlay').classList.add('open');
  });
}

function _closeCal(result) {
  document.getElementById('imd-cal-overlay').classList.remove('open');
  _hoverDate = null;
  if (_calResolve) { _calResolve(result); _calResolve = null; }
}

// ============================================================
//  CORE APP FUNCTIONS
// ============================================================

async function mintempUploadFile() {
  const fileInput = document.getElementById('fileInput');
  const statusDiv = document.getElementById('uploadStatus');

  if (!fileInput.files[0]) {
    statusDiv.innerHTML = '<p style="color:red;">Please select a file</p>';
    return;
  }

  const formData = new FormData();
  formData.append('file', fileInput.files[0]);
  statusDiv.innerHTML = '<p>Processing file...</p>';

  try {
    const response = await fetch('/api/mintemp/upload', {
      method: 'POST',
      headers: { 'ngrok-skip-browser-warning': 'true' },
      body: formData
    });
    const data = await response.json();

    if (response.ok) {
      currentFileId    = data.file_id;
      currentFileType  = data.file_type;
      currentNDays     = data.n_days;
      currentStartDate = _parseDate(data.start_date);

      // Set calendar valid range
      _calValidStart = currentStartDate;
      if (_calValidStart && currentNDays) {
        _calValidEnd = new Date(_calValidStart);
        _calValidEnd.setDate(_calValidEnd.getDate() + currentNDays - 1);
      }

      mintempDisplayResults(data);
      statusDiv.innerHTML = '<p style="color:green;">File processed successfully!</p>';

      if (data.file_type === 'imd_mintemp') {
        statusDiv.innerHTML +=
          `<p style="color:#0d9e74;">📅 ${currentNDays} days · ` +
          `${_fmtDate(_calValidStart)} → ${_fmtDate(_calValidEnd)}</p>`;
      }
    } else {
      statusDiv.innerHTML = `<p style="color:red;">Error: ${data.error}</p>`;
    }
  } catch (error) {
    statusDiv.innerHTML = `<p style="color:red;">Error: ${error.message}</p>`;
  }
}

function mintempDisplayResults(data) {
  document.getElementById('resultsSection').style.display = 'block';
  document.getElementById('ncols').textContent     = data.metadata.ncols;
  document.getElementById('nrows').textContent     = data.metadata.nrows;
  document.getElementById('cellsize').textContent  = data.metadata.cellsize;
  document.getElementById('xll').textContent       = data.metadata.xllcorner.toFixed(4);
  document.getElementById('yll').textContent       = data.metadata.yllcorner.toFixed(4);

  const stats = data.statistics_first_day || data.statistics;

  document.getElementById('min').textContent    = stats.min    ? stats.min.toFixed(2)    : 'N/A';
  document.getElementById('max').textContent    = stats.max    ? stats.max.toFixed(2)    : 'N/A';
  document.getElementById('mean').textContent   = stats.mean   ? stats.mean.toFixed(2)   : 'N/A';
  document.getElementById('median').textContent = stats.median ? stats.median.toFixed(2) : 'N/A';
  document.getElementById('std').textContent    = stats.std    ? stats.std.toFixed(2)    : 'N/A';
  document.getElementById('count').textContent  = stats.count  ? stats.count.toLocaleString() : 'N/A';

  if (data.extent) {
    document.getElementById('xmin').textContent = data.extent.xmin.toFixed(4);
    document.getElementById('xmax').textContent = data.extent.xmax.toFixed(4);
    document.getElementById('ymin').textContent = data.extent.ymin.toFixed(4);
    document.getElementById('ymax').textContent = data.extent.ymax.toFixed(4);
  } else {
    const xmax = data.metadata.xllcorner + data.metadata.ncols * data.metadata.cellsize;
    const ymax = data.metadata.yllcorner + data.metadata.nrows * data.metadata.cellsize;
    document.getElementById('xmin').textContent = data.metadata.xllcorner.toFixed(4);
    document.getElementById('xmax').textContent = xmax.toFixed(4);
    document.getElementById('ymin').textContent = data.metadata.yllcorner.toFixed(4);
    document.getElementById('ymax').textContent = ymax.toFixed(4);
  }

  // Show geoportal button after file loaded
  const btn = document.getElementById('geoportal-btn');
  if (btn) {
    btn.style.display = 'flex';
    btn.href = '/geoportal.html?file_id=' + data.file_id +
               '&file_type=' + data.file_type +
               '&n_days=' + (data.n_days || 0) +
               '&start_date=' + (data.start_date || '');
  }
}

async function mintempExportData(format) {
  if (!currentFileId) { alert('Please upload a file first'); return; }

  try {
    let url, filename;

    if (currentFileType === 'imd_mintemp') {
      if (format !== 'csv') {
        alert('For multi-day files, only CSV export is available');
        return;
      }

      const result = await _openCalendar({
        title:   'Select Export Date Range',
        showAll: true
      });
      if (!result) return; // user cancelled

      if (result.isAll) {
        if (!confirm(
          `Export all ${currentNDays} days? This may produce a very large file.`
        )) return;
        url      = `/api/mintemp/export/${currentFileId}/csv_all`;
        filename = `${currentFileId}_all_days.csv`;
      } else {
        url =
          `/api/mintemp/export/${currentFileId}/csv_range` +
          `?from=${result.fromIndex}&to=${result.toIndex}`;
        filename =
          `${currentFileId}_` +
          `${result.from.toISOString().slice(0,10)}_to_` +
          `${result.to.toISOString().slice(0,10)}.csv`;
      }

    } else {
      // Single-grid file
      const ext = { csv:'csv', geotiff:'tif', ascii:'asc', stats:'_stats.csv' };
      url      = `/api/mintemp/export/${currentFileId}/${format}`;
      filename = `${currentFileId}.${ext[format]}`;
    }

    // Direct download — no fetch, no blob, no memory limit
    const a = document.createElement('a');
    a.href     = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  } catch (err) {
    alert('Error: ' + err.message);
  }
}

async function mintempQueryPoint() {
  if (!currentFileId) { alert('Please upload a file first'); return; }

  const lon = parseFloat(document.getElementById('longitude').value);
  const lat = parseFloat(document.getElementById('latitude').value);
  if (isNaN(lon) || isNaN(lat)) {
    alert('Please enter valid coordinates');
    return;
  }

  try {
    if (currentFileType === 'imd_mintemp') {
      // Open calendar for date range selection
      const result = await _openCalendar({
        title:   'Select Date Range to Query',
        showAll: false
      });
      if (!result) return;

      const response = await fetch(
        `/api/mintemp/timeseries/${currentFileId}`, {
          method:  'POST',
          headers: { 'Content-Type': 'application/json', 'ngrok-skip-browser-warning': 'true' },
          body:    JSON.stringify({
            longitude: lon,
            latitude:  lat,
            from_day:  result.fromIndex,
            to_day:    result.toIndex
          })
        }
      );
      const data = await response.json();

      if (response.ok) {
        const values  = data.time_series
          .map(d => d.mintemp_c)
          .filter(v => v !== null);
        const total   = values.reduce((a, b) => a + b, 0);
        const avg     = values.length ? total / values.length : 0;
        const max     = values.length ? Math.max(...values)   : 0;
        const nDays   = result.toIndex - result.fromIndex + 1;

        document.getElementById('pointResult').innerHTML = `
          <p><strong>📍 ${lon}°E, ${lat}°N</strong></p>
          <p>📅 ${_fmtDate(result.from)} → ${_fmtDate(result.to)}
             <em>(${nDays} days)</em></p>
          <hr style="border-color:#dde3ed;margin:8px 0;">
          <p>Avg min temp : <strong>${total.toFixed(2)} °C</strong></p>
          <p>Min daily    : ${avg.toFixed(2)} °C</p>
          <p>Max daily    : ${max.toFixed(2)} °C</p>
          <p>Days < 0°C   : ${values.filter(v => v < 0).length} / ${nDays}</p>
        `;
      } else {
        alert('Error: ' + data.error);
      }

    } else {
      // Single-grid file
      const response = await fetch(
        `/api/mintemp/timeseries/${currentFileId}`, {
          method:  'POST',
          headers: { 'Content-Type': 'application/json', 'ngrok-skip-browser-warning': 'true' },
          body:    JSON.stringify({ longitude: lon, latitude: lat })
        }
      );
      const data = await response.json();
      document.getElementById('pointResult').innerHTML = response.ok
        ? (data.value !== null
            ? `<p><strong>Value at (${lon}, ${lat}):</strong>
               ${data.value.toFixed(2)}</p>`
            : `<p style="color:orange;">No data at this location</p>`)
        : `<p style="color:red;">${data.error}</p>`;
    }
  } catch (err) {
    alert('Error: ' + err.message);
  }
}