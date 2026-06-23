/* app.js — DataPull frontend logic */
"use strict";

// ── State ──────────────────────────────────────────────────────────────────
let allRecords = [];
let charts     = {};

// ── Ambient background particles ──────────────────────────────────────────
(function initCanvas() {
  const canvas = document.getElementById("bgCanvas");
  const ctx    = canvas.getContext("2d");
  let W, H, particles;

  function resize() {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }

  function makeParticles(n) {
    return Array.from({ length: n }, () => ({
      x:  Math.random() * W,
      y:  Math.random() * H,
      r:  Math.random() * 1.2 + 0.3,
      vx: (Math.random() - 0.5) * 0.25,
      vy: (Math.random() - 0.5) * 0.25,
      a:  Math.random() * 0.5 + 0.1,
    }));
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    particles.forEach(p => {
      p.x += p.vx; p.y += p.vy;
      if (p.x < 0) p.x = W; if (p.x > W) p.x = 0;
      if (p.y < 0) p.y = H; if (p.y > H) p.y = 0;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(91,127,255,${p.a})`;
      ctx.fill();
    });
    requestAnimationFrame(draw);
  }

  resize();
  particles = makeParticles(80);
  window.addEventListener("resize", () => { resize(); particles = makeParticles(80); });
  draw();
})();

// ── Navigation ─────────────────────────────────────────────────────────────
document.querySelectorAll(".nav-item").forEach(btn => {
  btn.addEventListener("click", () => {
    const id = btn.dataset.panel;
    document.querySelectorAll(".nav-item").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById("panel-" + id).classList.add("active");
    if (id === "history") loadHistory();
  });
});

// ── Status indicator ───────────────────────────────────────────────────────
function setStatus(state, text) {
  const dot  = document.getElementById("statusDot");
  const span = document.getElementById("statusText");
  dot.className  = "status-dot " + state;
  span.textContent = text;
}

// ── Toast ──────────────────────────────────────────────────────────────────
let toastTimer;
function toast(msg) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("show"), 2800);
}

// ── Quick URL ──────────────────────────────────────────────────────────────
function setUrl(url) {
  document.getElementById("urlInput").value = url;
}

// ── Progress log ───────────────────────────────────────────────────────────
function logLine(msg, type = "info") {
  const log = document.getElementById("progressLog");
  const d   = document.createElement("div");
  d.className   = "log-line log-" + type;
  d.textContent = msg;
  log.innerHTML = "";
  log.appendChild(d);
}

function setProgress(pct) {
  document.getElementById("progressBar").style.width = pct + "%";
}

// ── Main scrape flow ───────────────────────────────────────────────────────
async function runScrape() {
  const url = document.getElementById("urlInput").value.trim();
  if (!url) { toast("Enter a URL first."); return; }

  const btn = document.getElementById("runBtn");
  btn.disabled = true;
  btn.querySelector(".btn-text").textContent = "Scraping…";
  setStatus("busy", "Scraping…");

  const progressWrap = document.getElementById("progressWrap");
  progressWrap.style.display = "block";
  setProgress(0);

  // Simulated pipeline steps
  const steps = [
    [10,  "Sending HTTP GET request…",             "info"],
    [25,  "Response 200 OK — parsing HTML tree",    "success"],
    [45,  "Located quote containers via div.quote", "success"],
    [60,  "Extracting text, author, and tag fields…","info"],
    [72,  "Loading into Pandas DataFrame…",         "info"],
    [82,  "Cleaning: dedup, normalize, fill nulls", "info"],
    [91,  "Computing derived columns…",             "info"],
    [96,  "Running sentiment classifier…",          "info"],
  ];

  for (const [pct, msg, type] of steps) {
    await sleep(260);
    setProgress(pct);
    logLine(msg, type);
  }

  try {
    const res  = await fetch("/api/scrape", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ url }),
    });
    const data = await res.json();

    if (!res.ok) throw new Error(data.error || "Server error");

    await sleep(200);
    setProgress(100);
    logLine(`Done — ${data.stats.total} records in ${data.session.elapsed_ms} ms`, "success");

    allRecords = data.records;
    updateMetrics(data.stats, data.session.elapsed_ms);
    renderTable(allRecords);
    renderCharts(data.stats);

    document.getElementById("metrics").style.opacity = "1";
    document.getElementById("exportRow").style.display = "flex";
    setStatus("ready", "Ready");
    toast(`Scraped ${data.stats.total} records`);

  } catch (err) {
    logLine("Error: " + err.message, "warn");
    setStatus("error", "Error");
    toast("Scrape failed: " + err.message);
  } finally {
    btn.disabled = false;
    btn.querySelector(".btn-text").textContent = "Scrape";
  }
}

// ── Metrics ────────────────────────────────────────────────────────────────
function updateMetrics(stats, ms) {
  document.getElementById("mRecords").textContent = stats.total;
  document.getElementById("mAvgLen").textContent  = stats.avg_length + " ch";
  document.getElementById("mPos").textContent     = stats.sentiment.positive;
  document.getElementById("mNeg").textContent     = stats.sentiment.negative;
  document.getElementById("mTime").textContent    = ms + " ms";
}

// ── Table ──────────────────────────────────────────────────────────────────
function renderTable(records) {
  const body = document.getElementById("tableBody");
  document.getElementById("tableCount").textContent = records.length + " records";
  if (!records.length) {
    body.innerHTML = '<tr><td colspan="6" class="table-empty">No records matched.</td></tr>';
    return;
  }
  body.innerHTML = records.map((r, i) => {
    const sc = r.sentiment === "positive" ? "badge-green"
             : r.sentiment === "negative" ? "badge-red" : "badge-amber";
    const short = r.text.length > 72 ? r.text.slice(0, 72) + "…" : r.text;
    return `<tr>
      <td class="mono" style="color:var(--text-muted)">${i + 1}</td>
      <td class="text-cell" title="${escHtml(r.text)}">${escHtml(short)}</td>
      <td>${escHtml(r.author)}</td>
      <td style="color:var(--text-muted);font-size:12px">${escHtml(r.tags)}</td>
      <td><span class="badge ${sc}">${r.sentiment}</span></td>
      <td class="mono">${r.length}</td>
    </tr>`;
  }).join("");
}

function filterTable() {
  const q = document.getElementById("tableSearch").value.toLowerCase();
  const filtered = allRecords.filter(r =>
    r.text.toLowerCase().includes(q) ||
    r.author.toLowerCase().includes(q) ||
    r.tags.toLowerCase().includes(q)
  );
  renderTable(filtered);
}

// ── Charts ─────────────────────────────────────────────────────────────────
function renderCharts(stats) {
  document.getElementById("chartsEmpty").classList.remove("visible");

  const GRID_COLOR = "rgba(255,255,255,0.06)";
  const TICK_COLOR = "#6b7280";

  if (charts.sent) charts.sent.destroy();
  charts.sent = new Chart(document.getElementById("sentChart"), {
    type: "doughnut",
    data: {
      labels: ["Positive", "Neutral", "Negative"],
      datasets: [{
        data: [stats.sentiment.positive, stats.sentiment.neutral, stats.sentiment.negative],
        backgroundColor: ["rgba(74,222,128,0.8)", "rgba(107,114,128,0.6)", "rgba(248,113,113,0.8)"],
        borderColor: ["#4ade80", "#6b7280", "#f87171"],
        borderWidth: 1,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false, cutout: "62%",
      plugins: {
        legend: { position: "bottom", labels: { color: TICK_COLOR, boxWidth: 10, font: { size: 11 } } },
      },
    },
  });

  if (charts.author) charts.author.destroy();
  const authors = stats.top_authors.slice(0, 8);
  charts.author = new Chart(document.getElementById("authorChart"), {
    type: "bar",
    data: {
      labels: authors.map(a => a.name.split(" ").slice(-1)[0]),
      datasets: [{
        label: "Quotes",
        data:  authors.map(a => a.count),
        backgroundColor: "rgba(91,127,255,0.7)",
        borderColor:     "#5b7fff",
        borderWidth: 1,
        borderRadius: 4,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: GRID_COLOR }, ticks: { color: TICK_COLOR, font: { size: 10 } } },
        y: { beginAtZero: true, grid: { color: GRID_COLOR }, ticks: { color: TICK_COLOR, stepSize: 1 } },
      },
    },
  });

  if (charts.len) charts.len.destroy();
  charts.len = new Chart(document.getElementById("lenChart"), {
    type: "bar",
    data: {
      labels: ["< 40", "40–79", "80–119", "120–159", "160+"],
      datasets: [{
        label: "Records",
        data:  stats.length_bins,
        backgroundColor: "rgba(167,139,250,0.65)",
        borderColor:     "#a78bfa",
        borderWidth: 1,
        borderRadius: 4,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: GRID_COLOR }, ticks: { color: TICK_COLOR } },
        y: { beginAtZero: true, grid: { color: GRID_COLOR }, ticks: { color: TICK_COLOR, stepSize: 1 } },
      },
    },
  });
}

// ── History ────────────────────────────────────────────────────────────────
async function loadHistory() {
  const list = document.getElementById("historyList");
  try {
    const res  = await fetch("/api/history");
    const data = await res.json();
    if (!data.length) {
      list.innerHTML = '<div class="history-empty">No history yet.</div>';
      return;
    }
    list.innerHTML = [...data].reverse().map(s => `
      <div class="history-item">
        <div class="history-num">${s.id}</div>
        <div class="history-url">${escHtml(s.url)}</div>
        <div class="history-meta">${s.elapsed_ms} ms · ${new Date(s.scraped_at).toLocaleTimeString()}</div>
        <div class="history-badge">${s.records} records</div>
      </div>
    `).join("");
  } catch {
    list.innerHTML = '<div class="history-empty">Could not load history.</div>';
  }
}

// ── Export ─────────────────────────────────────────────────────────────────
function exportData(fmt) {
  window.location.href = "/api/export/" + fmt;
}

// ── Helpers ────────────────────────────────────────────────────────────────
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function escHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ── Init ───────────────────────────────────────────────────────────────────
setStatus("ready", "Ready");
document.getElementById("chartsEmpty").classList.add("visible");
