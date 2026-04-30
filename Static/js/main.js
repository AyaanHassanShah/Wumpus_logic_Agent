// static/js/main.js
// ─────────────────────────────────────────────────────────────
// Wumpus Logic Agent — Frontend Controller
//
// Responsibilities
// ────────────────
// • Communicate with the Flask REST API (fetch/POST)
// • Render the grid and update cell states
// • Display percepts, metrics, and KB resolution log
// • Drive Auto-Step / Auto-Run modes
// ─────────────────────────────────────────────────────────────

"use strict";

// ── Module state ─────────────────────────────────────────────
let gameId     = null;   // current session ID
let runTimer   = null;   // setInterval handle for Auto-Run

// ── API helpers ───────────────────────────────────────────────

/**
 * POST to a Flask API endpoint and return the parsed JSON response.
 * @param {string} endpoint
 * @param {object} body
 * @returns {Promise<object>}
 */
async function apiPost(endpoint, body = {}) {
  const response = await fetch(endpoint, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify(body),
  });
  return response.json();
}

// ── Public actions (called by HTML event handlers) ────────────

/** Initialise a new game with the currently selected grid size. */
async function newGame() {
  stopRun();
  const rows = parseInt(document.getElementById("inp-rows").value, 10);
  const cols = parseInt(document.getElementById("inp-cols").value, 10);

  const data = await apiPost("/api/new", { rows, cols });
  gameId = data.game_id;

  clearOverlay();
  renderState(data.state);
  setMsg("Agent initialised at (0,0). Click adjacent cells or use AUTO controls.", "info");
}

/** Move the agent to cell (r, c) — triggered by clicking a grid cell. */
async function moveTo(r, c) {
  if (!gameId) return;
  const state = await apiPost("/api/move", { game_id: gameId, r, c });
  renderState(state);
  checkTerminal(state);
}

/** Let the KB agent decide and execute one step. */
async function autoStep() {
  if (!gameId) return;
  const state = await apiPost("/api/auto_step", { game_id: gameId });
  renderState(state);
  checkTerminal(state);
}

/** Toggle Auto-Run: repeatedly call autoStep every 700 ms. */
function autoRun() {
  if (!gameId) return;
  if (runTimer) { stopRun(); return; }

  document.getElementById("btn-run").textContent = "⏹ STOP RUN";
  runTimer = setInterval(async () => {
    const state = await apiPost("/api/auto_step", { game_id: gameId });
    renderState(state);
    if (!state.alive || state.won) stopRun();
    checkTerminal(state);
  }, 700);
}

/** Stop the Auto-Run timer and reset the button label. */
function stopRun() {
  if (runTimer) { clearInterval(runTimer); runTimer = null; }
  document.getElementById("btn-run").textContent = "⚡⚡ AUTO RUN";
}

/** Reveal the true positions of all hazards and gold on the grid. */
async function revealTruth() {
  if (!gameId) return;
  const truth = await apiPost("/api/reveal", { game_id: gameId });

  // Overlay pit icons
  for (const [r, c] of truth.pits) {
    const cell = getCellEl(r, c);
    if (cell && !cell.classList.contains("agent")) {
      cell.classList.add("danger");
      cell.querySelector(".cell-icon").textContent = "🕳️";
    }
  }

  // Overlay Wumpus icon
  if (truth.wumpus) {
    const [r, c] = truth.wumpus;
    const cell = getCellEl(r, c);
    if (cell && !cell.classList.contains("agent")) {
      cell.classList.add("danger");
      cell.querySelector(".cell-icon").textContent = "👹";
    }
  }

  // Overlay Gold icon
  const [gr, gc] = truth.gold;
  const goldCell = getCellEl(gr, gc);
  if (goldCell) goldCell.querySelector(".cell-icon").textContent = "🏆";

  setMsg("Truth revealed — 🕳️ Pit  👹 Wumpus  🏆 Gold", "warn");
}

// ── Rendering ─────────────────────────────────────────────────

/**
 * Full render pass from a GameState dict returned by the API.
 * @param {object} state
 */
function renderState(state) {
  if (!state || state.error) {
    setMsg(state?.error ?? "Unknown error from server.", "err");
    return;
  }

  ensureGrid(state.rows, state.cols);
  updateCells(state);
  updatePercepts(state.percepts);
  updateMetrics(state);
  appendLog(state);
  updateKBProof(state.log);
}

/**
 * Build the grid DOM if it doesn't match the current dimensions.
 */
function ensureGrid(rows, cols) {
  const grid = document.getElementById("grid");
  if (grid.querySelectorAll(".cell").length === rows * cols) return;

  grid.style.gridTemplateColumns = `repeat(${cols}, 62px)`;
  grid.innerHTML = "";

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const cell = document.createElement("div");
      cell.className = "cell unknown";
      cell.dataset.r = r;
      cell.dataset.c = c;
      cell.innerHTML = `
        <div class="cell-icon">?</div>
        <div class="cell-coord">${r},${c}</div>
      `;
      cell.addEventListener("click", () => moveTo(r, c));
      grid.appendChild(cell);
    }
  }
}

/**
 * Update every cell's CSS class and icon based on state.cell_states.
 */
function updateCells(state) {
  const ICONS = {
    agent:   "🤖",
    danger:  "💥",
    safe:    "✓",
    visited: "",
    unknown: "?",
  };

  for (let r = 0; r < state.rows; r++) {
    for (let c = 0; c < state.cols; c++) {
      const cell   = getCellEl(r, c);
      if (!cell) continue;
      const status = state.cell_states[`${r},${c}`] ?? "unknown";
      cell.className = `cell ${status}`;
      cell.querySelector(".cell-icon").textContent = ICONS[status] ?? "?";
    }
  }
}

/** Render percept badges in the right panel. */
function updatePercepts(percepts) {
  const container = document.getElementById("percept-badges");
  container.innerHTML = "";

  if (!percepts || percepts.length === 0) {
    container.innerHTML = '<div class="badge none">NONE</div>';
    return;
  }

  for (const p of percepts) {
    const badge = document.createElement("div");
    badge.className = `badge ${p.toLowerCase()}`;
    badge.textContent = p.toUpperCase();
    container.appendChild(badge);
  }
}

/** Update the metrics dashboard (right panel + header strip). */
function updateMetrics(state) {
  const visitedCount = state.visited_count ?? 0;

  setText("metric-steps",   state.inference_steps);
  setText("metric-last",    state.last_steps);
  setText("metric-visited", visitedCount);
  setText("metric-pos",     JSON.stringify(state.agent));

  // Header strip
  setText("hdr-steps",   state.inference_steps);
  setText("hdr-visited", visitedCount);
  setText("hdr-status",
    !state.alive ? "DEAD" :
    state.won    ? "WON"  : "ACTIVE"
  );
}

/** Prepend a new entry to the scrollable resolution log. */
function appendLog(state) {
  if (!state.message) return;

  const log   = document.getElementById("log");
  const entry = document.createElement("div");
  const cls   =
    !state.alive                                          ? "bad"  :
    state.was_safe_query && state.message.includes("✓")  ? "good" : "info";

  entry.className = `entry ${cls}`;
  entry.textContent = `› ${state.message}`;
  log.prepend(entry);

  // Update the centre message box
  const msgType =
    !state.alive ? "err" :
    state.won    ? "ok"  :
    state.was_safe_query ? "ok" : "info";
  setMsg(state.message, msgType);
}

/** Show the KB proof trace in the right panel. */
function updateKBProof(lines) {
  if (!lines || lines.length === 0) return;
  const el = document.getElementById("kb-proof");
  el.innerHTML = lines.map(l => `<div>${escapeHtml(l)}</div>`).join("");
}

// ── Terminal state handling ───────────────────────────────────

function checkTerminal(state) {
  if (!state.alive) showOverlay("AGENT DEAD 💀", "lose");
  else if (state.won) showOverlay("GOLD FOUND! 🏆", "win");
}

function showOverlay(text, cls) {
  stopRun();
  const el = document.getElementById("overlay-msg");
  el.textContent = text;
  el.className   = `show ${cls} pulsing`;
}

function clearOverlay() {
  document.getElementById("overlay-msg").className = "";
}

// ── DOM utilities ─────────────────────────────────────────────

function getCellEl(r, c) {
  return document.querySelector(`.cell[data-r="${r}"][data-c="${c}"]`);
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function setMsg(text, type = "info") {
  const el = document.getElementById("msg-display");
  if (!el) return;
  el.className  = `msg-box ${type}`;
  el.textContent = text;
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}
