// stalk. — vanilla JS frontend
const API_BASE = window.location.origin.startsWith("http")
  ? window.location.origin
  : "http://localhost:8000";

// ---------- AUTH ----------
const TOKEN_KEY = "stalk_token";
const USER_KEY  = "stalk_user";
function getToken()   { return localStorage.getItem(TOKEN_KEY); }
function saveAuth(token, username) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, username);
}
function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}
function showAuthOverlay() { document.getElementById("auth-overlay").classList.remove("hidden"); }
function hideAuthOverlay() { document.getElementById("auth-overlay").classList.add("hidden"); }

const state = {
  currentTicker: null,
  currentAnalysis: null,
  conversationHistory: [],
  stockUniverse: [],
  sectorMap: {},
  analyzedStocks: {},
  savedStocks: new Set(),
  activeFilter: "All",
  searchQuery: "",
  searchDebounce: null,
  isLoading: false,
  appLoaded: false,
};

// FILTERS is built dynamically from the universe after load, but we seed with fixed top ones.
const STATIC_FILTERS = ["All", "Saved", "NIFTY50"];
let FILTERS = [...STATIC_FILTERS];

// ---------- INIT ----------
async function init() {
  setupAuthForms();
  const ok = await checkAuth();
  if (ok) await loadApp();
}

async function loadApp() {
  // Guard: don't initialise twice (e.g. if checkAuth + a form both succeed)
  if (state.appLoaded) return;
  state.appLoaded = true;
  await loadStockUniverse();
  await loadSavedStocks();
  renderFilterChips();
  renderStockList();
  setupEventListeners();
  showWelcomeMessage();
}

async function checkAuth() {
  const token = getToken();
  if (!token) { showAuthOverlay(); return false; }
  try {
    const res = await fetch(`${API_BASE}/api/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error();
    const data = await res.json();
    renderUserChip(data.username);
    hideAuthOverlay();
    return true;
  } catch {
    clearAuth();
    showAuthOverlay();
    return false;
  }
}

function renderUserChip(username) {
  // Clean up any stale outside-click listener from a previous session
  if (window._dotMenuHandler) {
    document.removeEventListener("click", window._dotMenuHandler);
    window._dotMenuHandler = null;
  }

  const chip = document.getElementById("user-chip");
  if (!chip) return;
  chip.innerHTML = `
    <div class="dot-menu" id="dot-menu">
      <button class="dot-menu-btn" id="dot-menu-btn" aria-label="Account menu" title="Account">⋮</button>
      <div class="dot-menu-dropdown hidden" id="dot-menu-dropdown">
        <div class="dot-menu-user">@${escapeHtml(username)}</div>
        <button class="dot-menu-item" id="dot-profile-btn">👤 profile</button>
        <button class="dot-menu-item danger" id="dot-logout-btn">👋 logout</button>
      </div>
    </div>
  `;

  const menuBtn  = chip.querySelector("#dot-menu-btn");
  const dropdown = chip.querySelector("#dot-menu-dropdown");

  menuBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    dropdown.classList.toggle("hidden");
  });

  chip.querySelector("#dot-profile-btn").addEventListener("click", () => {
    dropdown.classList.add("hidden");
    showToast(`logged in as @${escapeHtml(username)} ✨`, "info");
  });

  chip.querySelector("#dot-logout-btn").addEventListener("click", () => {
    if (window._dotMenuHandler) {
      document.removeEventListener("click", window._dotMenuHandler);
      window._dotMenuHandler = null;
    }
    clearAuth();
    chip.innerHTML = "";
    state.appLoaded = false;
    state.savedStocks = new Set();
    showAuthOverlay();
  });

  // Close dropdown when clicking anywhere outside
  window._dotMenuHandler = function (e) {
    const menu = document.getElementById("dot-menu");
    if (!menu) {
      document.removeEventListener("click", window._dotMenuHandler);
      window._dotMenuHandler = null;
      return;
    }
    if (!menu.contains(e.target)) dropdown.classList.add("hidden");
  };
  document.addEventListener("click", window._dotMenuHandler);
}

async function loadSavedStocks() {
  const token = getToken();
  if (!token) return;
  try {
    const res = await fetch(`${API_BASE}/api/saved`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return;
    const data = await res.json();
    state.savedStocks = new Set(data.tickers);
  } catch { /* silent — saved list is a nice-to-have */ }
}

async function toggleSave(ticker) {
  const token = getToken();
  if (!token) { showToast("sign in to save stocks ✨", "info"); return; }
  const wasSaved = state.savedStocks.has(ticker);

  // Optimistic update
  if (wasSaved) state.savedStocks.delete(ticker);
  else state.savedStocks.add(ticker);
  renderStockList();

  try {
    if (wasSaved) {
      await fetch(`${API_BASE}/api/saved/${ticker}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
    } else {
      await fetch(`${API_BASE}/api/saved`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ ticker }),
      });
      showToast(`${ticker} saved ⭐`, "success");
    }
  } catch {
    // Revert
    if (wasSaved) state.savedStocks.add(ticker);
    else state.savedStocks.delete(ticker);
    renderStockList();
    showToast("couldn't save that — try again 😬", "error");
  }
}

function setupAuthForms() {
  // Tab switching
  document.querySelectorAll(".auth-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".auth-tab").forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      const target = tab.dataset.tab;
      document.getElementById("login-form").classList.toggle("hidden", target !== "login");
      document.getElementById("signup-form").classList.toggle("hidden", target !== "signup");
    });
  });

  // Login form
  const loginForm = document.getElementById("login-form");
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const submitBtn = loginForm.querySelector(".auth-submit");
    const errorEl = document.getElementById("login-error");
    const email    = document.getElementById("login-email").value.trim();
    const password = document.getElementById("login-password").value;

    submitBtn.disabled = true;
    submitBtn.textContent = "signing in…";
    errorEl.classList.add("hidden");
    errorEl.textContent = "";

    try {
      const res = await fetch(`${API_BASE}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "login failed");
      saveAuth(data.token, data.username);
      renderUserChip(data.username);
      hideAuthOverlay();
      await loadApp();
    } catch (err) {
      errorEl.textContent = err.message || "something went wrong 😬";
      errorEl.classList.remove("hidden");
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "let me in 🔓";
    }
  });

  // Signup form
  const signupForm = document.getElementById("signup-form");
  signupForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const submitBtn = signupForm.querySelector(".auth-submit");
    const errorEl  = document.getElementById("signup-error");
    const username = document.getElementById("signup-username").value.trim();
    const email    = document.getElementById("signup-email").value.trim();
    const password = document.getElementById("signup-password").value;

    submitBtn.disabled = true;
    submitBtn.textContent = "creating account…";
    errorEl.classList.add("hidden");
    errorEl.textContent = "";

    try {
      const res = await fetch(`${API_BASE}/api/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, username, password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "signup failed");
      saveAuth(data.token, data.username);
      renderUserChip(data.username);
      hideAuthOverlay();
      await loadApp();
    } catch (err) {
      errorEl.textContent = err.message || "something went wrong 😬";
      errorEl.classList.remove("hidden");
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "create account ✨";
    }
  });
}

async function loadStockUniverse() {
  try {
    const res = await fetch(`${API_BASE}/api/universe`);
    if (!res.ok) throw new Error("Universe load failed");
    const data = await res.json();
    state.stockUniverse = data.stocks || [];
    state.sectorMap = data.sectors || {};
    const meta = document.getElementById("browser-meta");
    const sectorCount = Object.keys(state.sectorMap).length;
    meta.textContent = `${data.total} stocks across ${sectorCount} sectors`;
    // Build filter list: All + Saved + NIFTY50 + unique sectors (sorted)
    const sectors = [...new Set(state.stockUniverse.map((s) => s.sector).filter(Boolean))].sort();
    FILTERS = ["All", "Saved", "NIFTY50", ...sectors];
  } catch (e) {
    console.error(e);
    showToast("can't load the stock list rn — backend ghosted us 👻", "error");
  }
}

// ---------- FILTERS ----------
function filterLabel(f) {
  if (f === "Saved") return "⭐ Saved";
  return f;
}

function renderFilterChips() {
  const c = document.getElementById("browser-filters");
  c.innerHTML = FILTERS.map(
    (f) =>
      `<button class="filter-chip ${state.activeFilter === f ? "active" : ""}" data-filter="${f}">${filterLabel(f)}</button>`
  ).join("");
  c.querySelectorAll(".filter-chip").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.activeFilter = btn.dataset.filter;
      renderFilterChips();
      renderStockList();
    });
  });
}

function applyFilter(stock) {
  const f = state.activeFilter;
  if (f === "All") return true;
  if (f === "Saved") return state.savedStocks.has(stock.ticker);
  if (f === "NIFTY50") return stock.index === "NIFTY50";
  return stock.sector === f; // Dynamic sector match
}

function applySearch(stock, q) {
  if (!q) return true;
  const ql = q.toLowerCase();
  return (
    stock.ticker.toLowerCase().includes(ql) ||
    stock.company_name.toLowerCase().includes(ql)
  );
}

function highlight(text, q) {
  if (!q) return escapeHtml(text);
  const ql = q.toLowerCase();
  const lower = text.toLowerCase();
  const idx = lower.indexOf(ql);
  if (idx === -1) return escapeHtml(text);
  return (
    escapeHtml(text.slice(0, idx)) +
    "<mark>" +
    escapeHtml(text.slice(idx, idx + q.length)) +
    "</mark>" +
    escapeHtml(text.slice(idx + q.length))
  );
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

// ---------- STOCK LIST ----------
function renderStockList() {
  const container = document.getElementById("stock-list-container");
  const q = state.searchQuery;

  let filtered = state.stockUniverse.filter((s) => applyFilter(s) && applySearch(s, q));

  // Sort: analyzed (with status) first, then alphabetical by name
  filtered.sort((a, b) => {
    const aAn = state.analyzedStocks[a.ticker] ? 1 : 0;
    const bAn = state.analyzedStocks[b.ticker] ? 1 : 0;
    if (aAn !== bAn) return bAn - aAn;
    return a.company_name.localeCompare(b.company_name);
  });

  if (filtered.length === 0) {
    const isSavedFilter = state.activeFilter === "Saved";
    container.innerHTML = isSavedFilter
      ? `<div style="padding:32px 16px;text-align:center;color:var(--text-muted);font-size:13px;">no saved stocks yet 🌟<br><span style="font-size:11px;opacity:0.7;">tap ☆ next to any stock to save it</span></div>`
      : `<div style="padding:32px 16px;text-align:center;color:var(--text-muted);font-size:13px;">no matches found 🫥<br><span style="font-size:11px;opacity:0.7;">try a different vibe</span></div>`;
    return;
  }

  // Group by sector if not searching/filtering specifically
  const showGroups = !q && (state.activeFilter === "All" || state.activeFilter === "NIFTY50");
  let html = "";

  if (showGroups) {
    const groups = {};
    filtered.forEach((s) => {
      groups[s.sector] = groups[s.sector] || [];
      groups[s.sector].push(s);
    });
    Object.keys(groups).sort().forEach((sector) => {
      html += `<div class="sector-header">${escapeHtml(sector)}</div>`;
      groups[sector].forEach((s) => {
        html += stockItemHtml(s, q);
      });
    });
  } else {
    filtered.forEach((s) => {
      html += stockItemHtml(s, q);
    });
  }

  container.innerHTML = html;
  container.querySelectorAll(".stock-item").forEach((el) => {
    el.addEventListener("click", () => {
      selectStock(el.dataset.ticker);
      // Close mobile drawer on selection
      document.getElementById("stock-browser").classList.remove("open");
      document.getElementById("mobile-backdrop").classList.remove("visible");
    });
  });

  // Star buttons — stop propagation so click doesn't also selectStock
  container.querySelectorAll(".save-star-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      toggleSave(btn.dataset.ticker);
    });
  });
}

function stockItemHtml(s, q) {
  const analyzed = state.analyzedStocks[s.ticker];
  const isActive = state.currentTicker === s.ticker;
  const isSaved = state.savedStocks.has(s.ticker);
  let statusDot = "";
  if (analyzed) {
    const color = analyzed.status?.color || "blue";
    statusDot = `<span class="status-dot status-${color}" title="${escapeHtml(analyzed.status?.status || "")}"></span>`;
  }
  return `
    <div class="stock-item ${isActive ? "active" : ""}" data-ticker="${escapeHtml(s.ticker)}">
      <div class="stock-item-main">
        <span class="stock-name">${highlight(s.company_name, q)}</span>
        <span class="stock-ticker">${highlight(s.ticker, q)}</span>
      </div>
      <div class="stock-item-meta">
        <span class="sector-tag">${escapeHtml(s.sector)}</span>
        ${statusDot}
        ${analyzed ? `<span class="status-mini">${escapeHtml(analyzed.status?.status || "")}</span>` : ""}
        <button class="save-star-btn ${isSaved ? "saved" : ""}" data-ticker="${escapeHtml(s.ticker)}" title="${isSaved ? "Unsave" : "Save"}" type="button">${isSaved ? "★" : "☆"}</button>
      </div>
    </div>
  `;
}

// ---------- SELECT STOCK / ANALYZE ----------
async function selectStock(ticker, forceRefresh = false) {
  if (!ticker) return;
  state.currentTicker = ticker;
  dismissWelcomeHero();
  renderStockList();

  // Cache hit — scroll to the existing card if already rendered, otherwise render it now
  if (!forceRefresh && state.analyzedStocks[ticker]) {
    state.currentAnalysis = state.analyzedStocks[ticker];
    const existing = chatWindow().querySelector(`.chat-analysis-wrapper[data-ticker="${ticker}"]`);
    if (existing) {
      existing.scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }
    renderAnalysisCard(state.currentAnalysis);
    addAssistantMessage(`showing ${state.currentAnalysis.company_name} analysis ☕ — ask me anything.`, "default");
    return;
  }

  // Force refresh — remove the old card for this ticker so the fresh one lands at the bottom
  if (forceRefresh) {
    chatWindow().querySelectorAll(`.chat-analysis-wrapper[data-ticker="${ticker}"]`).forEach((el) => el.remove());
  }

  showSkeletonLoader(ticker);
  state.isLoading = true;

  try {
    const res = await fetch(`${API_BASE}/api/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ticker }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Error ${res.status}`);
    }
    const data = await res.json();
    state.analyzedStocks[ticker] = data;
    state.currentAnalysis = data;
    renderAnalysisCard(data);
    renderStockList();
    const pose = data.status?.high_conviction ? "excited" : "default";
    addAssistantMessage(`tea spilled on ${data.company_name} ☕ — ask me anything, i've got receipts.`, pose);
  } catch (e) {
    console.error(e);
    removeSkeletonLoader();
    showToast(e.message || "analysis failed 💔", "error");
    addAssistantMessage(`couldn't pull up ${ticker} 💀 — ${e.message}`, "sad");
  } finally {
    state.isLoading = false;
  }
}

function chatWindow() { return document.getElementById("chat-window"); }

// ---------- ANALYSIS CARD ----------
function renderAnalysisCard(data) {
  // Remove skeleton for this ticker (if still present)
  removeSkeletonLoader();

  // Wrap the card so we can find it later by ticker
  const wrapper = document.createElement("div");
  wrapper.className = "chat-analysis-wrapper";
  wrapper.dataset.ticker = data.ticker;

  const card = document.createElement("div");
  card.className = "analysis-card";
  card.innerHTML = `
    <div class="card-header">
      <div class="card-title">
        <span class="company-name">${escapeHtml(data.company_name)}</span>
        <span class="ticker-chip">${escapeHtml(data.ticker)}</span>
        ${data.sector ? `<span class="sector-tag">${escapeHtml(data.sector)}</span>` : ""}
      </div>
      <button class="refresh-btn" id="refresh-btn">🔄 re-stalk</button>
    </div>

    <div class="price-row">
      <span class="current-price">${formatINR(data.current_price)}</span>
      <div class="price-changes">
        ${renderPriceChangeBadge(data.price_changes?.change_1d, "1D")}
        ${renderPriceChangeBadge(data.price_changes?.change_1w, "1W")}
        ${renderPriceChangeBadge(data.price_changes?.change_1m, "1M")}
        ${data.price_changes?.change_ytd != null ? renderPriceChangeBadge(data.price_changes.change_ytd, "YTD") : ""}
        ${infoBtn("priceChanges")}
      </div>
    </div>

    ${render52wBar(data.current_price, data.low_52w, data.high_52w)}

    <div class="status-row">
      <span class="status-badge status-${data.status.color}">
        ${escapeHtml(data.status.emoji)} ${escapeHtml(data.status.status)}
        ${infoBtn("status")}
      </span>
      ${data.status.high_conviction ? `<span class="conviction-badge">🔥 High Conviction ${infoBtn("conviction")}</span>` : ""}
      ${data.rsi != null ? `<span class="rsi-chip rsi-${getRsiClass(data.rsi)}">RSI: ${data.rsi.toFixed(1)} ${infoBtn("rsi")}</span>` : ""}
    </div>

    <div class="score-row">
      <div class="score-pill">
        <div class="score-label-row">
          <span class="score-label">Trend</span>
          ${infoBtn("trend")}
        </div>
        <span class="score-value">${data.trend.trend_score}/3</span>
      </div>
      <div class="score-pill">
        <div class="score-label-row">
          <span class="score-label">Fundamentals</span>
          ${infoBtn("fundamentals")}
        </div>
        <span class="score-value">${data.fundamentals_summary.fundamental_score}/3</span>
      </div>
      <div class="score-pill">
        <div class="score-label-row">
          <span class="score-label">${escapeHtml(data.trend.conviction_flag || "Volume")}</span>
          ${infoBtn("volume")}
        </div>
        <span class="score-value">${(data.trend.volume_ratio || 0).toFixed(2)}x</span>
      </div>
    </div>

    <div class="divider"></div>

    <div class="range-row">
      <div class="buy-zone">
        <span class="zone-label">🟢 dip zone ${infoBtn("dipZone")}</span>
        <span class="zone-range">${formatINR(data.buy_range.lower)} – ${formatINR(data.buy_range.upper)}</span>
        <span class="zone-sub">${escapeHtml(data.buy_range.label || "")}</span>
      </div>
      <div class="sell-zone">
        <span class="zone-label">🔴 exit zone ${infoBtn("exitZone")}</span>
        <span class="zone-range">${formatINR(data.sell_range.lower)} – ${formatINR(data.sell_range.upper)}</span>
        <span class="zone-sub">${escapeHtml(data.sell_range.label || "")}</span>
      </div>
    </div>

    <div class="divider"></div>

    <div class="why-card">
      <span class="why-heading">the receipts</span>
      <ul class="why-bullets">
        ${(data.why_card.why_bullets || []).map((b) => `<li>${escapeHtml(b)}</li>`).join("")}
      </ul>
      <p class="analyst-note">${escapeHtml(data.why_card.analyst_note || "")}</p>
      <span class="confidence-badge conf-${(data.why_card.confidence || "Medium").toLowerCase()}">
        ${escapeHtml(data.why_card.confidence || "Medium")} Confidence
      </span>
    </div>

    <div class="fundamentals-toggle">
      <button class="toggle-btn" id="toggle-fund">deep dive ▾</button>
      <div class="fundamentals-detail hidden" id="fund-detail">
        ${renderFundamentalsDetail(data.fundamentals_summary)}
      </div>
    </div>

    ${
      data.data_warnings && data.data_warnings.length > 0
        ? `<div class="warnings-strip">${data.data_warnings
            .map((w) => renderWarningChip(w, { kind: "strip" }))
            .join("")}</div>`
        : ""
    }

    <div class="disclaimer">not SEBI registered • not financial advice • just vibes 🫶 do your own research</div>
  `;

  wrapper.appendChild(card);
  chatWindow().appendChild(wrapper);
  scrollToBottom();

  // Wire up handlers
  card.querySelector("#refresh-btn").addEventListener("click", () => selectStock(data.ticker, true));
  const toggle = card.querySelector("#toggle-fund");
  toggle.addEventListener("click", () => {
    const detail = card.querySelector("#fund-detail");
    const hidden = detail.classList.toggle("hidden");
    toggle.textContent = hidden ? "deep dive ▾" : "less detail ▴";
  });

  // Info popovers
  card.querySelectorAll(".info-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      showInfoPopover(btn);
    });
  });

  // Expandable warnings
  card.querySelectorAll(".warning-expandable").forEach((wrap) => {
    const btn = wrap.querySelector(".warning-summary");
    const detail = wrap.querySelector(".warning-detail");
    const chevron = wrap.querySelector(".warning-chevron");
    if (btn && detail) {
      btn.addEventListener("click", () => {
        const opened = !detail.classList.toggle("hidden");
        chevron.textContent = opened ? "▴" : "▾";
        wrap.classList.toggle("open", opened);
      });
    }
  });
}

// ---------- INFO POPOVER ----------
function showInfoPopover(anchorBtn) {
  // Close any existing popover first
  closeInfoPopover();

  const key = anchorBtn.dataset.info;
  const text = INFO_TEXTS[key];
  if (!text) return;

  const pop = document.createElement("div");
  pop.className = "info-popover";
  pop.id = "active-info-popover";
  pop.innerHTML = `
    <button class="info-popover-close" aria-label="close">×</button>
    <div class="info-popover-body">${escapeHtml(text).replace(/\n/g, "<br/>")}</div>
  `;
  document.body.appendChild(pop);

  // Position above-or-below the anchor button
  const r = anchorBtn.getBoundingClientRect();
  const popW = 280;
  const popH = pop.offsetHeight;
  let left = r.left + r.width / 2 - popW / 2;
  left = Math.max(12, Math.min(left, window.innerWidth - popW - 12));
  let top = r.top - popH - 10;
  if (top < 12) top = r.bottom + 10; // flip below if not enough space above
  pop.style.left = `${left}px`;
  pop.style.top = `${top}px`;

  pop.querySelector(".info-popover-close").addEventListener("click", closeInfoPopover);
  // Click outside to close (next tick so the opening click doesn't close it)
  setTimeout(() => {
    document.addEventListener("click", outsideClickClose, { once: true });
  }, 0);
}

function outsideClickClose(e) {
  const pop = document.getElementById("active-info-popover");
  if (pop && !pop.contains(e.target) && !e.target.classList.contains("info-btn")) {
    closeInfoPopover();
  } else if (pop) {
    document.addEventListener("click", outsideClickClose, { once: true });
  }
}

function closeInfoPopover() {
  const pop = document.getElementById("active-info-popover");
  if (pop) pop.remove();
}

function renderFundamentalsDetail(fund) {
  const d = fund.details || {};
  const peStr = d.pe_ratio != null ? Number(d.pe_ratio).toFixed(1) : "N/A";
  const pbStr = d.pb_ratio != null ? Number(d.pb_ratio).toFixed(2) : "N/A";
  const roeStr = d.roe_value != null ? `${Number(d.roe_value).toFixed(1)}%` : null;
  const deStr = d.debt_to_equity_value != null ? Number(d.debt_to_equity_value).toFixed(2) : null;
  const roeDisplay = roeStr ? `${escapeHtml(d.roe_status || "")} <span class="fund-actual">(${roeStr})</span>` : escapeHtml(d.roe_status || "N/A");
  const deDisplay = deStr ? `${escapeHtml(d.debt_status || "")} <span class="fund-actual">(${deStr})</span>` : escapeHtml(d.debt_status || "N/A");
  return `
    <div class="fund-grid">
      <div class="fund-item">
        <span class="fund-label">ROE</span>
        <span class="fund-value ${d.roe_status === "Strong(>15%)" ? "positive" : ""}">${roeDisplay}</span>
      </div>
      <div class="fund-item">
        <span class="fund-label">Debt/Equity</span>
        <span class="fund-value ${d.debt_status === "Low(<1)" ? "positive" : ""}">${deDisplay}</span>
      </div>
      <div class="fund-item">
        <span class="fund-label">P/E Ratio</span>
        <span class="fund-value">${peStr}</span>
      </div>
      <div class="fund-item">
        <span class="fund-label">P/B Ratio</span>
        <span class="fund-value">${pbStr}</span>
      </div>
      <div class="fund-item">
        <span class="fund-label">Earnings Growth</span>
        <span class="fund-value ${d.earnings_growth === "Positive" ? "positive" : d.earnings_growth === "Negative" ? "negative" : ""}">${escapeHtml(d.earnings_growth || "N/A")}</span>
      </div>
    </div>
    ${
      fund.red_flags && fund.red_flags.length > 0
        ? `<div class="red-flags">${fund.red_flags.map((f) => renderWarningChip(f, { kind: "flag" })).join("")}</div>`
        : ""
    }
  `;
}

// ---------- HELPERS ----------
function render52wBar(current, low, high) {
  if (low == null || high == null || high <= low) return "";
  const range = high - low;
  const pct = Math.max(0, Math.min(100, ((current - low) / range) * 100));
  const nearHigh = pct >= 80;
  const nearLow = pct <= 20;
  const markerClass = nearHigh ? "marker-high" : nearLow ? "marker-low" : "";
  return `
    <div class="range-52w-wrap">
      <div class="range-52w-labels">
        <span class="range-52w-label">52W Low ${formatINR(low)}</span>
        <span class="range-52w-center-label">${pct.toFixed(0)}% of range</span>
        <span class="range-52w-label">52W High ${formatINR(high)}</span>
      </div>
      <div class="range-52w-bar">
        <div class="range-52w-fill" style="width:${pct.toFixed(1)}%"></div>
        <div class="range-52w-marker ${markerClass}" style="left:${pct.toFixed(1)}%"></div>
      </div>
    </div>
  `;
}

function formatINR(price) {
  if (price == null || price === undefined) return "N/A";
  try {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2,
    }).format(price);
  } catch {
    return `₹${Number(price).toFixed(2)}`;
  }
}

function getRsiClass(rsi) {
  if (rsi >= 70) return "overbought";
  if (rsi <= 30) return "oversold";
  return "neutral";
}

function renderPriceChangeBadge(change, label) {
  if (change == null) return "";
  const sign = change >= 0 ? "+" : "";
  const cls = change >= 0 ? "positive" : "negative";
  return `<span class="change-badge ${cls}">${label}: ${sign}${change.toFixed(2)}%</span>`;
}

function showSkeletonLoader(ticker) {
  removeSkeletonLoader(); // clear any stale skeleton first
  const skeleton = document.createElement("div");
  skeleton.id = "analysis-skeleton";
  skeleton.className = "chat-analysis-wrapper";
  if (ticker) skeleton.dataset.ticker = ticker;
  skeleton.innerHTML = `
    <div class="analysis-card skeleton-card">
      <div class="skeleton skeleton-title"></div>
      <div class="skeleton skeleton-price"></div>
      <div class="skeleton skeleton-badge"></div>
      <div class="skeleton skeleton-row"></div>
      <div class="skeleton skeleton-row"></div>
      <div class="skeleton skeleton-row"></div>
    </div>
  `;
  chatWindow().appendChild(skeleton);
  scrollToBottom();
}

function removeSkeletonLoader() {
  const el = document.getElementById("analysis-skeleton");
  if (el) el.remove();
}

// ---------- CHAT ----------
function showWelcomeMessage() {
  const container = document.getElementById("analysis-card-container");
  container.innerHTML = `
    <div class="welcome-hero" id="welcome-hero">
      <img class="hero-stalky" src="/assets/stalky-full.png" alt="stalky"
           onerror="this.outerHTML='<div class=&quot;hero-stalky fallback-emoji&quot;>👀</div>'" />
      <div class="hero-text">
        <h2>hey, i'm <span class="hero-name">stalky</span> 👋</h2>
        <p>your low-key market BFF. study. analyze. invest. repeat.<br/>tap a stock on the left or just spill what's on your mind.</p>
        <div class="hero-pills">
          <span class="hero-pill active">${state.stockUniverse.length} stocks</span>
          <span class="hero-pill">NSE only</span>
          <span class="hero-pill">end-of-day prices</span>
        </div>
      </div>
    </div>
  `;
  addAssistantMessage(
    `yo 👋 pick a stock from the watchlist or ask me anything. i've got receipts on ${state.stockUniverse.length} NSE names — just don't ask me to predict the future, that's not my vibe.`,
    "wink"
  );
}

function dismissWelcomeHero() {
  const hero = document.getElementById("welcome-hero");
  if (hero) hero.remove();
}

const BOT_NAME = "stalky";
const BOT_EMOJI = "👀";

// ---------- INFO POPOVERS ----------
// One-liners that appear when the user clicks the (i) next to a metric.
const INFO_TEXTS = {
  status: "stalk.'s overall verdict on where this stock stands.\n• In-Form 🔥 — strong trend + healthy fundamentals\n• On-Track ✅ — solid fundamentals, partial trend\n• Off-Track ⚠️ — weak fundamentals, mixed trend\n• Out-of-Form ❄️ — broken trend or critical red flag",
  rsi: "Relative Strength Index (14-day). Momentum oscillator from 0–100.\n• ≥ 70 — overbought (often due for a pullback)\n• ≤ 30 — oversold (often due for a bounce)\n• 30–70 — neutral",
  trend: "Trend score 0–3. Counts how many of these are true:\n• price > 1-week avg (5-day SMA)\n• price > 30-day avg (21-day SMA)\n• price > 52-week avg (252-day SMA)\nHigher = stronger uptrend hierarchy.",
  fundamentals: "Fundamental score 0–3. +1 each if:\n• Debt/Equity < 1\n• Return on Equity > 15%\n• Earnings growth positive\n'Unknown' values neither add nor subtract.",
  volume: "Yesterday's volume vs 30-day average.\n• > 2.0x — High Conviction (institutional interest possible)\n• 1.0–2.0x — Normal\n• < 1.0x — Below average",
  dipZone: "Where signals suggest accumulation interest. Built from VWAP-30 and EMA-200 support levels (±2%). Not a buy recommendation — just where the data clusters.",
  exitZone: "Where signals suggest profit-taking pressure. Built from the upper Bollinger band (20,2σ) and the 52-week high. Not a sell recommendation — just where supply tends to appear.",
  priceChanges: "Percentage price change over each window — 1 day, 1 week (5 trading days), 1 month (21 trading days), YTD (year-to-date from Jan 1).",
  conviction: "🔥 High Conviction fires when yesterday's volume is over 2× the 30-day average — strong signal that whatever happened wasn't random.",
};

function infoBtn(key) {
  return `<button class="info-btn" data-info="${key}" aria-label="info" type="button">i</button>`;
}

// ---------- EXPANDABLE WARNINGS ----------
// Each entry: matcher tested against warning text -> step-by-step manual check.
const WARNING_GUIDES = [
  {
    match: /pledg/i,
    title: "How to check promoter pledging manually",
    steps: [
      "Open <strong>screener.in</strong> and search the stock — the Promoter Pledging % shows on the main page.",
      "Or go to <strong>nseindia.com</strong> → Equities → Shareholding Pattern → look for 'Shares Pledged'.",
      "On <strong>BSE India</strong>: bseindia.com → Corp Information → Pledged Shares.",
      "Rule of thumb — pledging above ~30% is a red flag; above 50% is serious risk.",
    ],
  },
  {
    match: /auditor/i,
    title: "How to verify auditor changes manually",
    steps: [
      "Search the company on <strong>nseindia.com</strong> → Announcements → look for 'Resignation of Auditor'.",
      "Cross-check on <strong>screener.in</strong> annual reports section for any mid-year auditor change.",
      "Read the resignation letter — vague reasons like 'pre-occupation' or 'commercial differences' are sus.",
      "Check if the new auditor is a tier-1 firm (Deloitte, KPMG, EY, PwC, BSR) or a smaller one.",
    ],
  },
  {
    match: /data may be delayed|latest price/i,
    title: "How to verify the latest price",
    steps: [
      "Open <strong>nseindia.com</strong> and search the ticker — that's the source of truth for end-of-day prices.",
      "Or use <strong>screener.in</strong> / <strong>moneycontrol.com</strong> — both update within minutes of NSE close.",
      "If our price differs by more than 2% from NSE's, the yfinance feed is lagging — re-check after 30 min.",
    ],
  },
  {
    match: /fundamental data|incomplete/i,
    title: "How to fill in missing fundamentals",
    steps: [
      "<strong>screener.in</strong> has the cleanest free view of ROE, P/E, debt/equity, profit growth.",
      "<strong>tijori.in</strong> for sector comparisons.",
      "<strong>tickertape.in</strong> shows analyst-style scorecards for free.",
      "For deep filings, the company's annual report on <strong>bseindia.com</strong> is the original source.",
    ],
  },
];

function _findGuide(text) {
  return WARNING_GUIDES.find((g) => g.match.test(text)) || null;
}

function renderWarningChip(text, options = {}) {
  const { kind = "flag" } = options; // "flag" or "strip"
  const guide = _findGuide(text);
  if (!guide) {
    return kind === "flag"
      ? `<span class="flag-item">⚠️ ${escapeHtml(text)}</span>`
      : escapeHtml(text);
  }
  const stepsHtml = guide.steps.map((s) => `<li>${s}</li>`).join("");
  return `
    <div class="warning-expandable ${kind}-expandable">
      <button class="warning-summary" type="button">
        <span class="warning-summary-text">⚠️ ${escapeHtml(text)}</span>
        <span class="warning-chevron">▾</span>
      </button>
      <div class="warning-detail hidden">
        <div class="warning-detail-title">${escapeHtml(guide.title)}</div>
        <ol class="warning-steps">${stepsHtml}</ol>
      </div>
    </div>
  `;
}
const BOT_POSES = {
  default: "/assets/stalky.png",
  thinking: "/assets/stalky-thinking.png",
  excited: "/assets/stalky-excited.png",
  sad: "/assets/stalky-sad.png",
  wink: "/assets/stalky-wink.png",
  full: "/assets/stalky-full.png",
};

function botAvatarHtml(pose = "default", extraClass = "") {
  const src = BOT_POSES[pose] || BOT_POSES.default;
  return `
    <div class="bot-avatar ${extraClass}">
      <img src="${src}" alt="stalky"
           onerror="this.parentElement.classList.add('fallback'); this.replaceWith(document.createTextNode('${BOT_EMOJI}'));" />
    </div>
  `;
}

function addUserMessage(text) {
  const w = document.getElementById("chat-window");
  const wrap = document.createElement("div");
  wrap.className = "chat-bubble user";
  wrap.innerHTML = `
    <div class="bubble-content">${escapeHtml(text)}</div>
    <span class="timestamp">${nowTime()}</span>
  `;
  w.appendChild(wrap);
  scrollToBottom();
}

function addAssistantMessage(text, pose = "default") {
  const w = document.getElementById("chat-window");
  const wrap = document.createElement("div");
  wrap.className = "chat-bubble assistant";
  wrap.innerHTML = `
    ${botAvatarHtml(pose)}
    <div class="bubble-content">
      <div class="bot-name">${BOT_NAME}</div>
      <div class="bot-text">${escapeHtml(text)}</div>
      <span class="timestamp">${nowTime()}</span>
    </div>
  `;
  w.appendChild(wrap);
  scrollToBottom();
}

function showTypingIndicator() {
  removeTypingIndicator();
  const w = document.getElementById("chat-window");
  const d = document.createElement("div");
  d.className = "typing-bubble";
  d.id = "typing-indicator";
  d.innerHTML = `
    ${botAvatarHtml("thinking", "talking")}
    <div class="typing-indicator"><span></span><span></span><span></span></div>
  `;
  w.appendChild(d);
  scrollToBottom();
}

function removeTypingIndicator() {
  const t = document.getElementById("typing-indicator");
  if (t) t.remove();
}

function scrollToBottom() {
  const c = document.getElementById("content-scroll");
  c.scrollTop = c.scrollHeight;
}

function nowTime() {
  const d = new Date();
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function detectTickerFromMessage(text, universe) {
  const upper = text.toUpperCase();
  const sorted = [...universe].sort((a, b) => b.ticker.length - a.ticker.length);
  for (const s of sorted) {
    if (s.ticker === "^NSEI") continue;
    const re = new RegExp(`\\b${s.ticker.replace(/[-&]/g, "\\$&")}\\b`);
    if (re.test(upper)) return s.ticker;
  }
  return null;
}

async function sendMessage(text) {
  if (!text || !text.trim()) return;
  text = text.trim();
  addUserMessage(text);
  document.getElementById("chat-input").value = "";

  // Heuristic: if the message is just a ticker / stock name without a question, treat as analyze
  const ticker = detectTickerFromMessage(text, state.stockUniverse);
  const isQuestion = /\?|how|why|what|explain|compare|tell|should|when|where|which/i.test(text);
  if (ticker && !isQuestion && text.length < 30) {
    await selectStock(ticker);
    return;
  }

  showTypingIndicator();
  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: text,
        context_ticker: state.currentTicker,
        conversation_history: state.conversationHistory.slice(-10),
      }),
    });
    if (!res.ok) throw new Error(`Chat error ${res.status}`);
    const data = await res.json();
    removeTypingIndicator();
    addAssistantMessage(data.response);
    state.conversationHistory.push({ role: "user", content: text });
    state.conversationHistory.push({ role: "assistant", content: data.response });
    if (data.ticker_detected && data.ticker_detected !== state.currentTicker) {
      // Soft auto-pull: only if user clearly named a different stock
      if (ticker === data.ticker_detected) {
        await selectStock(data.ticker_detected);
      }
    }
  } catch (e) {
    console.error(e);
    removeTypingIndicator();
    showToast("chat broke 😭 — check if the backend is alive", "error");
  }
}

// ---------- EVENT LISTENERS ----------
function setupEventListeners() {
  // Search input with debounce + clear button
  const searchInput = document.getElementById("stock-search-input");
  const clearBtn = document.getElementById("search-clear");
  searchInput.addEventListener("input", (e) => {
    const q = e.target.value;
    state.searchQuery = q;
    clearBtn.classList.toggle("visible", q.length > 0);
    clearTimeout(state.searchDebounce);
    state.searchDebounce = setTimeout(() => {
      renderStockList();
    }, 300);
  });
  clearBtn.addEventListener("click", () => {
    searchInput.value = "";
    state.searchQuery = "";
    clearBtn.classList.remove("visible");
    renderStockList();
  });

  // Send button + Enter
  document.getElementById("send-btn").addEventListener("click", () => {
    sendMessage(document.getElementById("chat-input").value);
  });
  document.getElementById("chat-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(e.target.value);
    }
  });

  // Quick chips
  document.querySelectorAll(".quick-chips .chip").forEach((c) => {
    c.addEventListener("click", () => sendMessage(c.dataset.msg));
  });

  // Mobile drawer
  const browser = document.getElementById("stock-browser");
  const backdrop = document.getElementById("mobile-backdrop");
  document.getElementById("mobile-toggle").addEventListener("click", () => {
    browser.classList.toggle("open");
    backdrop.classList.toggle("visible");
  });
  backdrop.addEventListener("click", () => {
    browser.classList.remove("open");
    backdrop.classList.remove("visible");
  });
}

// ---------- TOAST ----------
function showToast(message, type = "error") {
  const c = document.getElementById("toast-container");
  const t = document.createElement("div");
  t.className = `toast ${type}`;
  t.textContent = message;
  c.appendChild(t);
  setTimeout(() => {
    t.style.opacity = "0";
    t.style.transition = "opacity 0.25s";
    setTimeout(() => t.remove(), 250);
  }, 4000);
}

// ---------- BOOT ----------
document.addEventListener("DOMContentLoaded", init);
