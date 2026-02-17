// SkyModderAI - Frontend JavaScript
// Handles mod list analysis, UI updates, and Stripe checkout

const PLUGIN_LIMIT_WARN = 253;
let currentUserTier = (typeof window.__USER_TIER__ !== 'undefined' ? window.__USER_TIER__ : 'free');
let aiChatEnabled = false;
let platformCapabilities = {};
let currentReport = '';
let currentSuggestedOrder = [];
let currentAnalysisData = null;
let lastAnalysisSummary = null;

// DOM Elements
const elements = {
    modListInput: document.getElementById('mod-list-input'),
    analyzeBtn: document.getElementById('analyze-btn'),
    clearBtn: document.getElementById('clear-btn'),
    pasteBtn: document.getElementById('paste-btn'),
    sampleBtn: document.getElementById('sample-btn'),
    modCount: document.getElementById('mod-count'),
    modCountDetail: document.getElementById('mod-count-detail'),
    pluginLimitWarning: document.getElementById('plugin-limit-warning'),
    resultsPanel: document.getElementById('results-panel'),
    loadingOverlay: document.getElementById('loading-overlay'),
    conflictsContainer: document.getElementById('conflicts-container'),
    errorCount: document.getElementById('error-count'),
    warningCount: document.getElementById('warning-count'),
    infoCount: document.getElementById('info-count'),
    exportBtn: document.getElementById('export-btn'),
    downloadReportBtn: document.getElementById('download-report-btn'),
    downloadReportJsonBtn: document.getElementById('download-report-json-btn'),
    newAnalysisBtn: document.getElementById('new-analysis-btn'),
    gameSelect: document.getElementById('game-select'),
    filterErrors: document.getElementById('filter-errors'),
    filterWarnings: document.getElementById('filter-warnings'),
    filterInfo: document.getElementById('filter-info'),
    loadOrderSection: document.getElementById('load-order-section'),
    copyLoadOrderBtn: document.getElementById('copy-load-order-btn'),
    applyLoadOrderBtn: document.getElementById('apply-load-order-btn'),
    pluginLimitBanner: document.getElementById('plugin-limit-banner'),
    proUpgradeBtn: document.getElementById('pro-upgrade-btn'),
    modSearchInput: document.getElementById('mod-search-input'),
    modSearchResults: document.getElementById('mod-search-results'),
    chatSection: document.getElementById('chat-section'),
    chatMessages: document.getElementById('chat-messages'),
    chatForm: document.getElementById('chat-form'),
    chatInput: document.getElementById('chat-input'),
    chatSendBtn: document.getElementById('chat-send-btn'),
    chatUpgradeCta: document.getElementById('chat-upgrade-cta'),
    fixGuideSection: document.getElementById('fix-guide-section'),
    fixGuideContent: document.getElementById('fix-guide-content')
};

let modSearchTimeout = null;
let recommendationsTimeout = null;
let inputMatchTimeout = null;
let inputMatchRequestSeq = 0;
/** Games list from /api/games (includes nexus_slug) for Nexus links in search. */
let supportedGames = [];
/** User system specs (from API or localStorage). Sent with analyze for AI context. */
let currentSpecs = {};
/** Fix Guide: live step-by-step document that updates as you chat. Pro feature. */
let fixGuideSteps = [];
let fixGuideMeta = { game: '', gameName: '', date: '' };

function hasPaidAccess(tier) {
    return tier === 'pro' || tier === 'pro_plus' || tier === 'claw';
}

/**
 * Mod lookup: search database and show matches; click to add to list.
 */
async function runModSearch() {
    const inputEl = document.getElementById('mod-search-input');
    const resultsEl = document.getElementById('mod-search-results');
    const clearBtn = document.getElementById('mod-search-clear');
    if (!inputEl || !resultsEl) return;
    const q = (inputEl.value || '').trim();
    if (clearBtn) clearBtn.classList.toggle('hidden', !q);
    if (q.length < 1) {
        resultsEl.classList.add('hidden');
        resultsEl.innerHTML = '';
        return;
    }
    resultsEl.classList.remove('hidden');
    resultsEl.innerHTML = '<div class="mod-search-loading">Searching…</div>';
    const gameSelect = document.getElementById('game-select');
    const versionSelect = document.getElementById('masterlist-version');
    const game = (gameSelect && gameSelect.value) ? gameSelect.value : 'skyrimse';
    const version = (versionSelect && versionSelect.value) ? versionSelect.value : '';
    const params = new URLSearchParams({ q, game, limit: '25' });
    if (version) params.set('version', version);
    try {
        const res = await fetch(`/api/mod-search?${params.toString()}`);
        const data = await res.json().catch(() => ({ matches: [], web_suggestions: [] }));
        const matches = Array.isArray(data.matches) ? data.matches : [];
        const webSuggestions = Array.isArray(data.web_suggestions) ? data.web_suggestions : [];
        resultsEl.innerHTML = '';
        if (matches.length === 0 && webSuggestions.length === 0) {
            resultsEl.innerHTML = `<div class="mod-search-no-results">No mods found for "${q.replace(/"/g, '&quot;')}" in this game. Try a different term or check spelling. Pro users get web search fallback.</div>`;
            resultsEl.classList.remove('hidden');
            return;
        }
        const gameObj = supportedGames.find(g => g.id === game);
        const nexusSlug = gameObj?.nexus_slug || 'skyrimspecialedition';
        const nexusBase = `https://www.nexusmods.com/games/${nexusSlug}/mods?keyword=`;

        let rowIndex = 0;
        matches.forEach((name) => {
            const row = document.createElement('div');
            row.className = 'mod-search-item mod-search-row';
            row.dataset.index = String(rowIndex++);
            row.dataset.modName = name;
            const label = document.createElement('span');
            label.className = 'mod-search-name';
            label.textContent = name;
            function addModToList() {
                const listInput = document.getElementById('mod-list-input');
                if (listInput) {
                    const prefix = listInput.value.trim() ? '\n' : '';
                    listInput.value += prefix + '*' + name;
                    updateModCounter();
                }
                resultsEl.classList.add('hidden');
                inputEl.value = '';
                if (clearBtn) clearBtn.classList.add('hidden');
            }
            label.addEventListener('mousedown', (e) => { e.preventDefault(); addModToList(); });
            row.addEventListener('click', (e) => {
                if (!e.target.closest('.mod-search-nexus')) {
                    e.preventDefault();
                    addModToList();
                }
            });
            row.appendChild(label);
            const nexusLink = document.createElement('a');
            nexusLink.href = nexusBase + encodeURIComponent(name);
            nexusLink.target = '_blank';
            nexusLink.rel = 'noopener noreferrer';
            nexusLink.className = 'mod-search-nexus';
            nexusLink.textContent = 'Nexus';
            nexusLink.addEventListener('click', (e) => e.stopPropagation());
            row.appendChild(nexusLink);
            resultsEl.appendChild(row);
        });

        if (webSuggestions.length > 0) {
            const sep = document.createElement('div');
            sep.className = 'mod-search-section-divider';
            sep.textContent = 'Web suggestions (from Nexus & search)';
            resultsEl.appendChild(sep);
            webSuggestions.forEach((item) => {
                const row = document.createElement('div');
                row.className = 'mod-search-item mod-search-row mod-search-web';
                row.dataset.index = String(rowIndex++);
                row.dataset.modName = item.name || '';
                const label = document.createElement('span');
                label.className = 'mod-search-name';
                label.textContent = item.name || '';
                function addModToList() {
                    const listInput = document.getElementById('mod-list-input');
                    if (listInput && item.name) {
                        const prefix = listInput.value.trim() ? '\n' : '';
                        listInput.value += prefix + '*' + item.name;
                        updateModCounter();
                    }
                    resultsEl.classList.add('hidden');
                    inputEl.value = '';
                    if (clearBtn) clearBtn.classList.add('hidden');
                }
                label.addEventListener('mousedown', (e) => { e.preventDefault(); addModToList(); });
                row.addEventListener('click', (e) => {
                    if (!e.target.closest('a')) { e.preventDefault(); addModToList(); }
                });
                row.appendChild(label);
                const link = document.createElement('a');
                link.href = item.url || (nexusBase + encodeURIComponent(item.name || ''));
                link.target = '_blank';
                link.rel = 'noopener noreferrer';
                link.className = 'mod-search-nexus';
                link.textContent = 'Open';
                link.addEventListener('click', (e) => e.stopPropagation());
                row.appendChild(link);
                resultsEl.appendChild(row);
            });
        }
        resultsEl.classList.remove('hidden');
    } catch (e) {
        console.error('Mod search error:', e);
        resultsEl.classList.add('hidden');
    }
}

/**
 * Load supported games into the game selector.
 */
async function loadGames() {
    try {
        const response = await fetch('/api/games');
        if (!response.ok) return;
        const data = await response.json();
        if (!data.games || !elements.gameSelect) return;
        supportedGames = data.games;
        const currentGame = elements.gameSelect.value;
        const validIds = new Set(data.games.map(g => g.id));
        const gameToSelect = validIds.has(currentGame) ? currentGame : (data.default || 'skyrimse');
        elements.gameSelect.innerHTML = '';
        data.games.forEach(g => {
            const opt = document.createElement('option');
            opt.value = g.id;
            opt.textContent = g.name;
            if (g.id === gameToSelect) opt.selected = true;
            elements.gameSelect.appendChild(opt);
        });
        const masterlistVersionSelect = document.getElementById('masterlist-version');
        const gameVersionSelect = document.getElementById('game-version');
        if (masterlistVersionSelect) loadMasterlistVersions(gameToSelect).then(versions => populateMasterlistVersionSelect(masterlistVersionSelect, versions));
        if (gameVersionSelect) loadGameVersions(gameToSelect).then(data => populateGameVersionSelect(gameVersionSelect, data));
    } catch (e) {
        console.error('Failed to load games:', e);
    }
}

/**
 * Fetch game executable versions (Skyrim 1.5.97 vs 1.6.640, etc.).
 */
async function loadGameVersions(gameId) {
    try {
        const res = await fetch(`/api/games/${encodeURIComponent(gameId)}/game-versions`);
        if (!res.ok) return { versions: {}, default: '' };
        const data = await res.json();
        return { versions: data.versions || {}, default: data.default || '' };
    } catch (e) {
        return { versions: {}, default: '' };
    }
}

let cachedGameVersions = {};  // gameId -> { versions, default }

function populateGameVersionSelect(selectEl, { versions, default: defaultVer }) {
    if (!selectEl) return;
    const game = document.getElementById('game-select')?.value || 'skyrimse';
    cachedGameVersions[game] = { versions: versions || {}, default: defaultVer };
    selectEl.innerHTML = '<option value="">Not specified</option>';
    Object.entries(versions || {}).forEach(([ver, info]) => {
        const opt = document.createElement('option');
        opt.value = ver;
        let label = info.name;
        if (info.recommended) label += ' ⭐ (Recommended)';
        else if (info.common) label += ' ⭐';
        opt.textContent = label;
        selectEl.appendChild(opt);
    });
    if (defaultVer && selectEl.querySelector(`option[value="${defaultVer}"]`)) {
        selectEl.value = defaultVer;
    }
    updateGameVersionInfo();
}

function updateGameVersionInfo() {
    const gameVersionSelect = document.getElementById('game-version');
    const infoEl = document.getElementById('game-version-info');
    if (!gameVersionSelect || !infoEl) return;
    const ver = gameVersionSelect.value;
    if (!ver) {
        infoEl.classList.add('hidden');
        infoEl.innerHTML = '';
        return;
    }
    const game = document.getElementById('game-select')?.value || 'skyrimse';
    const info = cachedGameVersions[game]?.versions?.[ver];
    if (!info) {
        infoEl.classList.add('hidden');
        return;
    }
    let html = `<strong>${info.name}</strong>`;
    if (info.date) html += ` — ${info.date}`;
    if (info.notes) html += `. ${info.notes}`;
    if (info.skse) html += ` <span class="hint">(${info.skse})</span>`;
    if (info.f4se) html += ` <span class="hint">(${info.f4se})</span>`;
    if (info.fose) html += ` <span class="hint">(${info.fose})</span>`;
    if (info.nvse) html += ` <span class="hint">(${info.nvse})</span>`;
    if (info.obse) html += ` <span class="hint">(${info.obse})</span>`;
    if (info.sfse) html += ` <span class="hint">(${info.sfse})</span>`;
    if (info.warning) {
            html += ` <span class="game-version-warning-hint">${info.warning}</span>`;
    }
    infoEl.innerHTML = html;
    infoEl.classList.remove('hidden');
}

/**
 * Fetch available masterlist versions for a game (for version picking).
 */
async function loadMasterlistVersions(gameId) {
    try {
        const res = await fetch(`/api/games/${encodeURIComponent(gameId)}/masterlist-versions`);
        if (!res.ok) return { versions: [], latest: '' };
        const data = await res.json();
        return { versions: data.versions || [], latest: data.latest || '' };
    } catch (e) {
        return { versions: [], latest: '' };
    }
}

function populateMasterlistVersionSelect(selectEl, { versions, latest }) {
    if (!selectEl) return;
    selectEl.innerHTML = '<option value="">Latest</option>';
    (versions || []).forEach(v => {
        const opt = document.createElement('option');
        opt.value = v;
        opt.textContent = v + (v === latest ? ' (current)' : '');
        selectEl.appendChild(opt);
    });
}

/**
 * Check user's current tier from the server.
 */
async function checkUserTier() {
    try {
        const response = await fetch('/api/platform-capabilities');
        if (!response.ok) throw new Error(`HTTP error ${response.status}`);
        const data = await response.json();
        currentUserTier = data.tier || currentUserTier;
        aiChatEnabled = !!data.ai_chat_enabled;
        platformCapabilities = data || {};
        initGameFolderScan();
    } catch (error) {
        console.error('Failed to check user tier:', error);
        try {
            const fallback = await fetch('/api/check-tier');
            if (fallback.ok) {
                const data = await fallback.json();
                currentUserTier = data.tier || currentUserTier;
                aiChatEnabled = !!data.ai_chat_enabled;
                platformCapabilities = data || {};
                initGameFolderScan();
            }
        } catch (e2) {
            console.error('Tier fallback failed:', e2);
        }
    }
}

/**
 * Parse mod names from the mod list textarea (plugins.txt / MO2 format).
 */
function parseModListFromTextarea() {
    const el = document.getElementById('mod-list-input');
    if (!el || !el.value.trim()) return [];
    const lines = el.value.split('\n');
    const mods = [];
    for (const line of lines) {
        const t = line.trim();
        if (!t || t.startsWith('#')) continue;
        let name = t.replace(/^[+\-*]\s*/, '').trim();
        if (name.includes('/') || name.includes('\\')) name = name.split(/[/\\]/).pop();
        if (name && /\.(esp|esm|esl)$/i.test(name)) mods.push(name);
    }
    return [...new Set(mods)];
}

/**
 * Live normalize/match preview for messy mod list input.
 * Uses backend parser + LOOT fuzzy/search matching so typos still get useful candidates.
 */
async function refreshInputMatchPreview(options = {}) {
    const applyFormatted = !!options.applyFormatted;
    const silent = !!options.silent;
    const inputEl = document.getElementById('mod-list-input');
    const gameSelect = document.getElementById('game-select');
    const panel = document.getElementById('input-match-preview');
    const summaryEl = document.getElementById('input-match-summary');
    const listEl = document.getElementById('input-match-list');
    const actionBtn = document.getElementById('auto-format-btn');
    if (!inputEl || !gameSelect || !panel || !summaryEl || !listEl) return;

    const text = (inputEl.value || '').trim();
    if (!text) {
        panel.classList.add('hidden');
        listEl.innerHTML = '';
        summaryEl.textContent = '';
        return;
    }
    const reqId = ++inputMatchRequestSeq;
    if (actionBtn && applyFormatted) actionBtn.disabled = true;
    try {
        const res = await fetch('/api/modlist/normalize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ game: gameSelect.value || 'skyrimse', mod_list: text })
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            if (!silent) alert(data.error || 'Could not parse mod list.');
            return;
        }
        if (reqId !== inputMatchRequestSeq) return; // stale response
        const entries = data.entries || [];
        const summary = data.summary || {};
        const total = summary.total || entries.length || 0;
        const exact = summary.exact || 0;
        const fuzzy = summary.fuzzy || 0;
        const searched = summary.search || 0;
        const unknown = summary.unknown || 0;
        summaryEl.textContent = `${exact}/${total} exact, ${fuzzy} fuzzy, ${searched} search, ${unknown} unknown`;
        panel.classList.toggle('hidden', entries.length === 0);
        listEl.innerHTML = entries.slice(0, 120).map((e) => {
            const badge = escapeHtml(e.match_type || 'unknown');
            const targetName = escapeHtml(e.normalized || e.original || '');
            const original = escapeHtml(e.original || '');
            const title = e.original && e.normalized && e.original !== e.normalized
                ? `${original} -> ${targetName}`
                : targetName;
            const link = escapeHtml(e.nexus_url || '#');
            const alt = (e.suggestions || []).slice(0, 3).map(escapeHtml).join(' · ');
            const hint = alt ? `<span class="hint">${alt}</span>` : '';
            return `<div class="input-match-row">
                <span class="match-badge ${badge}">${badge}</span>
                <a class="match-line" href="${link}" target="_blank" rel="noopener noreferrer" title="${title}">${targetName}</a>
                ${hint}
            </div>`;
        }).join('');
        if (applyFormatted && data.normalized_text) {
            inputEl.value = data.normalized_text;
            updateModCounter();
            showActionFeedback('Auto-formatted list with best-effort matches. Review unknown lines in Match preview.');
        }
    } catch (_) {
        if (!silent) alert('Could not fetch live matches. Try again.');
    } finally {
        if (actionBtn && applyFormatted) actionBtn.disabled = false;
    }
}

/**
 * Fetch and display mod recommendations (live as you add mods).
 */
async function fetchAndShowRecommendations() {
    const strip = document.getElementById('recommendations-strip');
    const cards = document.getElementById('recommendations-cards');
    const warningsEl = document.getElementById('recommendations-warnings');
    const gameSelect = document.getElementById('game-select');
    const listInput = elements.modListInput;
    if (!strip || !cards || !gameSelect) return;
    const mods = parseModListFromTextarea();
    const modListText = listInput ? (listInput.value || '').trim() : '';
    if (mods.length === 0 && !modListText) {
        strip.classList.add('hidden');
        cards.innerHTML = '';
        if (warningsEl) warningsEl.innerHTML = '';
        return;
    }
    try {
        const payload = {
            game: gameSelect.value,
            mod_list: mods,
            mod_list_text: modListText,
            specs: getCurrentSpecs(),
            limit: 8
        };
        const res = await fetch('/api/recommendations', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json().catch(() => ({}));
        const recs = data.recommendations || [];
        const warnings = data.warnings || [];
        if (recs.length === 0 && warnings.length === 0) {
            strip.classList.add('hidden');
            return;
        }
        strip.classList.remove('hidden');
        // Render dynamic warnings (plugin limit, system strain)
        if (warningsEl) {
            if (warnings.length === 0) {
                warningsEl.innerHTML = '';
                warningsEl.classList.add('hidden');
            } else {
                warningsEl.classList.remove('hidden');
                warningsEl.innerHTML = warnings.map(w => {
                    const link = w.link_url ? `<a href="${escapeHtml(w.link_url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(w.link_title || 'Learn more')}</a>` : '';
                    const extra = w.link_extra ? ` <a href="${escapeHtml(w.link_extra.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(w.link_extra.title)}</a>` : '';
                    return `<div class="mod-warning mod-warning-${escapeHtml(w.severity || 'info')}">${escapeHtml(w.message)} ${link}${extra}</div>`;
                }).join('');
            }
        }
        const catLabel = (c) => (c || '').charAt(0).toUpperCase() + (c || '').slice(1);
        cards.innerHTML = recs.map(r => `
            <div class="mod-preview-card" data-mod-name="${escapeHtml(r.name)}">
                ${r.category ? `<span class="mod-preview-tag mod-preview-tag-${escapeHtml(r.category)}">${escapeHtml(catLabel(r.category))}</span>` : ''}
                <a href="${escapeHtml(r.nexus_url || '#')}" target="_blank" rel="noopener noreferrer" title="${escapeHtml(r.name)}">
                    <img src="${escapeHtml(r.image_url || '/static/icons/mod-placeholder.svg')}" alt="" loading="lazy">
                    <span class="mod-preview-name">${escapeHtml(r.name)}</span>
                    <span class="mod-preview-reason">${escapeHtml(r.reason || '')}</span>
                </a>
                <button type="button" class="mod-preview-add" title="Add to list" aria-label="Add ${escapeHtml(r.name)} to list">+</button>
            </div>
        `).join('');
        cards.querySelectorAll('.mod-preview-add').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const card = btn.closest('.mod-preview-card');
                const name = card?.dataset?.modName;
                if (name && elements.modListInput) {
                    const prefix = elements.modListInput.value.trim() ? '\n' : '';
                    elements.modListInput.value += prefix + '*' + name;
                    updateModCounter();
                }
            });
        });
    } catch (e) {
        strip.classList.add('hidden');
    }
}

/**
 * Update the mod counter and show/hide free tier / plugin limit warnings.
 */
function updateModCounter() {
    if (!elements.modListInput || !elements.modCount) return;

    const text = elements.modListInput.value;
    const lines = text.split('\n')
        .filter(line => line.trim() && !line.startsWith('#'))
        .length;

    elements.modCount.textContent = lines === 0 ? '0 mods' : `${lines} mods`;

    // Only show "X enabled / Y total" when we have a recent analysis and the list isn't empty
    if (elements.modCountDetail) {
        if (lines === 0) {
            lastAnalysisSummary = null; // clear stale summary when list is cleared
        }
        if (lastAnalysisSummary && lastAnalysisSummary.enabled_count != null && lines > 0) {
            elements.modCountDetail.textContent = `${lastAnalysisSummary.enabled_count} enabled / ${lastAnalysisSummary.mod_count} total`;
            elements.modCountDetail.classList.remove('hidden');
        } else {
            elements.modCountDetail.classList.add('hidden');
        }
    }

    if (elements.pluginLimitWarning) {
        if (lines > 0 && lastAnalysisSummary && lastAnalysisSummary.enabled_count >= PLUGIN_LIMIT_WARN) {
            elements.pluginLimitWarning.textContent = lastAnalysisSummary.plugin_limit_warning || `${lastAnalysisSummary.enabled_count} enabled — approaching 255 plugin limit.`;
            elements.pluginLimitWarning.classList.remove('hidden');
        } else {
            elements.pluginLimitWarning.classList.add('hidden');
        }
    }

    // Live recommendations: debounce fetch when mod list changes
    clearTimeout(recommendationsTimeout);
    recommendationsTimeout = setTimeout(fetchAndShowRecommendations, 600);

    // Live parse/match preview for user input.
    clearTimeout(inputMatchTimeout);
    inputMatchTimeout = setTimeout(() => refreshInputMatchPreview({ silent: true }), 700);
}

/**
 * Scan system using browser APIs (CPU cores, RAM, GPU, resolution).
 * Fills the specs form with detected values. VRAM cannot be detected — user must enter.
 */
async function scanSystem() {
    const btn = document.getElementById('scan-system-btn');
    const statusEl = document.getElementById('scan-system-status');
    const specsDetails = document.getElementById('specs-details');
    const cpuEl = document.getElementById('specs-cpu');
    const gpuEl = document.getElementById('specs-gpu');
    const ramEl = document.getElementById('specs-ram');
    const vramEl = document.getElementById('specs-vram');
    const resEl = document.getElementById('specs-resolution');

    if (!btn || !statusEl) return;
    btn.disabled = true;
    statusEl.textContent = 'Scanning…';

    const detected = { cpu: null, gpu: null, ram_gb: null, vram_gb: null, resolution: null };
    const parts = [];

    // CPU cores (all browsers)
    const cores = navigator.hardwareConcurrency;
    if (cores) {
        detected.cpu = `${cores} cores`;
        parts.push(`CPU: ${cores} cores`);
    }

    // RAM (Chrome, some others — returns 4, 8, 16, etc.)
    const ram = navigator.deviceMemory;
    if (ram) {
        detected.ram_gb = String(ram);
        parts.push(`RAM: ${ram} GB`);
    }

    // Resolution
    if (typeof screen !== 'undefined' && screen.width && screen.height) {
        detected.resolution = `${screen.width}x${screen.height}`;
        parts.push(`Display: ${screen.width}×${screen.height}`);
    }

    // GPU via WebGPU (Chrome, Edge, Safari 17+)
    try {
        if (navigator.gpu) {
            const adapter = await navigator.gpu.requestAdapter();
            if (adapter) {
                let gpuName = null;
                let info = null;
                if (adapter.info) {
                    info = adapter.info;
                } else if (typeof adapter.requestAdapterInfo === 'function') {
                    info = await adapter.requestAdapterInfo();
                }
                if (info) {
                    gpuName = info.device || info.description || info.architecture || null;
                }
                if (gpuName) {
                    detected.gpu = gpuName;
                    parts.push(`GPU: ${gpuName}`);
                }
            }
        }
    } catch (_) {
        // WebGPU may be blocked or unavailable
    }

    // Fill form
    if (cpuEl && detected.cpu) cpuEl.value = detected.cpu;
    if (gpuEl && detected.gpu) gpuEl.value = detected.gpu;
    if (ramEl && detected.ram_gb) ramEl.value = detected.ram_gb;
    if (resEl && detected.resolution) resEl.value = detected.resolution;
    // VRAM: cannot be detected — leave blank

    if (specsDetails && !specsDetails.open) specsDetails.open = true;

    const count = [detected.cpu, detected.gpu, detected.ram_gb, detected.resolution].filter(Boolean).length;
    if (count > 0) {
        statusEl.textContent = `Detected ${count} value(s). Add VRAM manually if needed.`;
        currentSpecs = { ...currentSpecs, ...Object.fromEntries(Object.entries(detected).filter(([, v]) => v)) };
    } else {
        statusEl.textContent = 'Could not detect specs in this browser. Try Steam System Info paste.';
    }

    btn.disabled = false;
}

/**
 * Get current specs from form or stored (currentSpecs).
 */
function getCurrentSpecs() {
    const cpu = document.getElementById('specs-cpu');
    const gpu = document.getElementById('specs-gpu');
    const ram = document.getElementById('specs-ram');
    const vram = document.getElementById('specs-vram');
    const res = document.getElementById('specs-resolution');
    const fromForm = {};
    if (cpu && cpu.value.trim()) fromForm.cpu = cpu.value.trim();
    if (gpu && gpu.value.trim()) fromForm.gpu = gpu.value.trim();
    if (ram && ram.value.trim()) fromForm.ram_gb = ram.value.trim();
    if (vram && vram.value.trim()) fromForm.vram_gb = vram.value.trim();
    if (res && res.value.trim()) fromForm.resolution = res.value.trim();
    return Object.keys(fromForm).length > 0 ? fromForm : currentSpecs;
}

/**
 * Load specs into form and currentSpecs.
 */
async function loadSpecs() {
    try {
        const r = await fetch('/api/specs');
        const data = await r.json().catch(() => ({}));
        let specs = data.specs || {};
        if (Object.keys(specs).length === 0 && localStorage) {
            try {
                const stored = localStorage.getItem('modcheck_specs');
                if (stored) specs = JSON.parse(stored);
            } catch (_) {}
        }
        currentSpecs = specs;
        const cpu = document.getElementById('specs-cpu');
        const gpu = document.getElementById('specs-gpu');
        const ram = document.getElementById('specs-ram');
        const vram = document.getElementById('specs-vram');
        const res = document.getElementById('specs-resolution');
        if (cpu) cpu.value = specs.cpu || '';
        if (gpu) gpu.value = specs.gpu || '';
        if (ram) ram.value = specs.ram_gb || '';
        if (vram) vram.value = specs.vram_gb || '';
        if (res) res.value = specs.resolution || '';
    } catch (_) {}
}

/**
 * Save specs (form or Steam paste) to API and/or localStorage.
 */
async function saveSpecs() {
    const steamEl = document.getElementById('specs-steam-paste');
    const statusEl = document.getElementById('specs-status');
    const btn = document.getElementById('specs-save-btn');
    const steam = steamEl && steamEl.value.trim();
    let body = {};
    if (steam) {
        body = { steam_paste: steam };
    } else {
        body = {
            cpu: (document.getElementById('specs-cpu') || {}).value?.trim(),
            gpu: (document.getElementById('specs-gpu') || {}).value?.trim(),
            ram_gb: (document.getElementById('specs-ram') || {}).value?.trim(),
            vram_gb: (document.getElementById('specs-vram') || {}).value?.trim(),
            resolution: (document.getElementById('specs-resolution') || {}).value?.trim()
        };
        body = Object.fromEntries(Object.entries(body).filter(([, v]) => v));
    }
    if (Object.keys(body).length === 0) {
        if (statusEl) statusEl.textContent = 'Enter specs or paste Steam System Info.';
        return;
    }
    if (btn) btn.disabled = true;
    if (statusEl) statusEl.textContent = 'Saving…';
    try {
        const r = await fetch('/api/specs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        const data = await r.json().catch(() => ({}));
        currentSpecs = data.specs || {};
        if (steamEl) steamEl.value = '';
        if (statusEl) statusEl.textContent = 'Saved.';
        if (localStorage && currentSpecs) {
            try { localStorage.setItem('modcheck_specs', JSON.stringify(currentSpecs)); } catch (_) {}
        }
    } catch (e) {
        if (statusEl) statusEl.textContent = 'Failed to save.';
    } finally {
        if (btn) btn.disabled = false;
    }
}

/**
 * Render system impact HTML including heaviest mods ranking (free for all tiers).
 */
function renderSystemImpact(si) {
    if (!si) return '';
    let html = '<div class="system-impact-stats">';
    html += `<div class="system-impact-stat"><span class="label">Complexity</span><span class="value complexity-${si.complexity || 'low'}">${escapeHtml(si.complexity_label || 'Low')}</span></div>`;
    const vram = Number(si.estimated_vram_gb ?? 0);
    html += `<div class="system-impact-stat"><span class="label">Estimated VRAM</span><span class="value">~${vram % 1 === 0 ? vram : vram.toFixed(1)} GB</span></div>`;
    if (si.heavy_mod_count > 0) {
        html += `<div class="system-impact-stat"><span class="label">Heavy mods</span><span class="value">${si.heavy_mod_count}</span></div>`;
    }
    html += '</div>';
    if (si.recommendation) {
        html += `<p class="system-impact-recommendation">${escapeHtml(si.recommendation)}</p>`;
    }
    const ranking = si.impact_ranking || si.heavy_mods || [];
    if (ranking.length > 0) {
        html += '<h5>Heaviest mods (most impact first)</h5><div class="system-impact-ranking-scroll"><ol class="system-impact-ranking-list">';
        ranking.forEach((m) => {
            html += `<li class="system-impact-item"><span class="impact-badge impact-${m.impact}">${escapeHtml(m.impact)}</span> ${escapeHtml(m.name)} <span class="hint">(${escapeHtml(m.category)})</span></li>`;
        });
        html += '</ol></div>';
    }
    return html;
}

/**
 * Fix Guide — live step-by-step document that updates as you chat. Pro only.
 */
function buildFixGuideFromAnalysis(data) {
    fixGuideSteps = [];
    const gameNames = { skyrimse: 'Skyrim SE', skyrim: 'Skyrim LE', skyrimvr: 'Skyrim VR', oblivion: 'Oblivion', fallout3: 'Fallout 3', falloutnv: 'Fallout New Vegas', fallout4: 'Fallout 4', starfield: 'Starfield' };
    fixGuideMeta = {
        game: data.game || 'skyrimse',
        gameName: gameNames[data.game] || (data.data_source || 'Skyrim SE').replace(/LOOT masterlist\s*\(([^)]+)\).*/, '$1'),
        date: new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
    };
    const summary = data.summary || {};
    const errCount = summary.errors || 0;
    const warnCount = summary.warnings || 0;
    const infoCount = summary.info || 0;
    fixGuideSteps.push({ type: 'intro', content: `Analysis for ${fixGuideMeta.gameName} — ${fixGuideMeta.date}. ${data.enabled_count || 0} mods enabled.` });
    if (errCount + warnCount + infoCount === 0) {
        fixGuideSteps.push({ type: 'step', content: 'No issues found. Your load order looks good.' });
    } else {
        if (errCount > 0) fixGuideSteps.push({ type: 'step', severity: 'error', content: `${errCount} error(s) to fix — missing requirements, incompatibilities. Address these first.` });
        if (warnCount > 0) fixGuideSteps.push({ type: 'step', severity: 'warning', content: `${warnCount} warning(s) — load order, patches, dirty edits.` });
        if (infoCount > 0) fixGuideSteps.push({ type: 'step', severity: 'info', content: `${infoCount} info message(s) from LOOT — check if they apply.` });
        const errors = (data.conflicts?.errors || []);
        errors.forEach((c, i) => {
            fixGuideSteps.push({ type: 'fix', severity: 'error', mod: c.affected_mod, message: stripMarkdown(c.message || ''), action: stripMarkdown(c.suggested_action || ''), id: `err-${i}` });
        });
        const warnings = (data.conflicts?.warnings || []);
        warnings.forEach((c, i) => {
            fixGuideSteps.push({ type: 'fix', severity: 'warning', mod: c.affected_mod, message: stripMarkdown(c.message || ''), action: stripMarkdown(c.suggested_action || ''), id: `warn-${i}` });
        });
    }
    if (data.suggested_load_order && data.suggested_load_order.length > 0) {
        fixGuideSteps.push({ type: 'step', content: 'Apply the suggested load order below (copy as plugins.txt or use Apply in the app).' });
    }
    renderFixGuide();
}

function stripMarkdown(s) {
    if (!s) return '';
    return String(s).replace(/\*\*/g, '').replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');
}

function addStepToFixGuide(step) {
    fixGuideSteps.push(step);
    renderFixGuide();
}

function renderFixGuide() {
    if (!elements.fixGuideContent) return;
    const isPro = hasPaidAccess(currentUserTier);
    if (!isPro || fixGuideSteps.length === 0) {
        if (elements.fixGuideSection) elements.fixGuideSection.classList.add('hidden');
        return;
    }
    if (elements.fixGuideSection) elements.fixGuideSection.classList.remove('hidden');
    let html = '';
    let stepNum = 0;
    fixGuideSteps.forEach((s) => {
        if (s.type === 'intro') {
            html += `<div class="fix-guide-intro">${escapeHtml(s.content)}</div>`;
        } else if (s.type === 'step') {
            stepNum++;
            const sev = s.severity ? ` fix-guide-step-${s.severity}` : '';
            html += `<div class="fix-guide-step${sev}"><span class="fix-guide-num">${stepNum}</span><div class="fix-guide-step-body">${escapeHtml(s.content)}</div></div>`;
        } else if (s.type === 'fix') {
            stepNum++;
            html += `<div class="fix-guide-fix fix-guide-fix-${s.severity}" data-fix-id="${escapeHtml(s.id || '')}">
                <span class="fix-guide-num">${stepNum}</span>
                <div class="fix-guide-fix-body">
                    ${s.mod ? `<strong>${escapeHtml(s.mod)}</strong>: ` : ''}${escapeHtml(s.message || '')}
                    ${s.action ? `<p class="fix-guide-action">→ ${escapeHtml(s.action)}</p>` : ''}
                </div>
                <label class="fix-guide-check"><input type="checkbox" class="fix-guide-resolved"> Resolved</label>
            </div>`;
        } else if (s.type === 'ai') {
            stepNum++;
            const parseMd = (window.marked && typeof marked.parse === 'function') ? (s) => marked.parse(s) : (window.marked && typeof marked === 'function') ? (s) => marked(s) : (s) => s;
            const body = parseMd ? (() => { try { return parseMd(s.content); } catch(_) { return escapeHtml(s.content); } })() : escapeHtml(s.content);
            html += `<div class="fix-guide-ai-step">
                <span class="fix-guide-num">${stepNum}</span>
                <div class="fix-guide-ai-body">
                    ${s.question ? `<p class="fix-guide-question">You asked: ${escapeHtml(s.question)}</p>` : ''}
                    <div class="fix-guide-ai-reply">${body}</div>
                </div>
            </div>`;
        }
    });
    elements.fixGuideContent.innerHTML = html;
    elements.fixGuideContent.querySelectorAll('.fix-guide-resolved').forEach(cb => {
        cb.addEventListener('change', () => renderFixGuide());
    });
    updateFixGuidePreview();
}

function updateFixGuidePreview() {
    const preview = document.getElementById('fix-guide-preview');
    const summaryEl = document.getElementById('fix-guide-preview-summary');
    const isPro = hasPaidAccess(currentUserTier);
    if (!preview || !summaryEl || !isPro || fixGuideSteps.length === 0) {
        if (preview) preview.classList.add('hidden');
        return;
    }
    const stepCount = fixGuideSteps.filter(s => s.type !== 'intro').length;
    const firstStep = fixGuideSteps.find(s => s.type === 'step' || s.type === 'fix' || s.type === 'ai');
    const raw = firstStep ? (firstStep.content || firstStep.message || '') : (fixGuideSteps[0]?.content || '');
    const previewText = raw.slice(0, 70) + (raw.length > 70 ? '…' : '');
    summaryEl.textContent = stepCount > 0 ? ` — ${stepCount} step${stepCount !== 1 ? 's' : ''}. ${previewText}` : ` ${previewText}`;
    preview.classList.remove('hidden');
}

function scrollToFixGuide() {
    const section = document.getElementById('fix-guide-section');
    if (section) section.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function downloadFixGuideHTML() {
    if (!hasPaidAccess(currentUserTier)) {
        window.location.href = '/signup-pro';
        return;
    }
    const html = buildFixGuideHTMLForDownload();
    const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `modcheck-fix-guide-${(fixGuideMeta.date || '').replace(/\s/g, '-') || 'report'}.html`;
    a.click();
    URL.revokeObjectURL(a.href);
}

function buildFixGuideHTMLForDownload() {
    const resolvedIds = new Set();
    const content = elements.fixGuideContent;
    if (content) {
        content.querySelectorAll('.fix-guide-resolved:checked').forEach(cb => {
            const el = cb.closest('[data-fix-id]');
            if (el && el.dataset.fixId) resolvedIds.add(el.dataset.fixId);
        });
    }
    const steps = fixGuideSteps.map(s => ({ ...s, resolved: s.id && resolvedIds.has(s.id) }));
    const parseMd = (window.marked && typeof marked.parse === 'function') ? (s) => marked.parse(s) : (window.marked && typeof marked === 'function') ? (s) => marked(s) : (s) => s;
    let body = '';
    let n = 0;
    steps.forEach(s => {
        if (s.type === 'intro') body += `<div class="fg-intro">${escapeHtml(s.content)}</div>`;
        else if (s.type === 'step') { n++; body += `<div class="fg-step"><span class="fg-num">${n}</span>${escapeHtml(s.content)}</div>`; }
        else if (s.type === 'fix') {
            n++;
            const done = s.resolved ? ' fg-done' : '';
            body += `<div class="fg-fix fg-${s.severity}${done}"><span class="fg-num">${n}</span><strong>${escapeHtml(s.mod || '')}</strong>: ${escapeHtml(s.message || '')}${s.action ? `<p class="fg-action">→ ${escapeHtml(s.action)}</p>` : ''}</div>`;
        } else if (s.type === 'ai') {
            n++;
            const reply = parseMd ? (() => { try { return parseMd(s.content); } catch(_) { return escapeHtml(s.content); } })() : escapeHtml(s.content);
            body += `<div class="fg-ai"><span class="fg-num">${n}</span>${s.question ? `<p class="fg-q">You asked: ${escapeHtml(s.question)}</p>` : ''}<div class="fg-reply">${reply}</div></div>`;
        }
    });
    return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SkyModderAI Fix Guide — ${escapeHtml(fixGuideMeta.gameName)}</title>
<style>
:root{--bg:#0a0e27;--card:#0c1220;--text:#e8eef4;--muted:#8b9cb4;--accent:#00d4e8;--err:#ef4444;--warn:#f59e0b;}
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:var(--text);line-height:1.6;padding:2rem;max-width:720px;margin:0 auto;}
h1{font-size:1.75rem;margin-bottom:0.5rem;color:var(--accent);}
.fg-meta{color:var(--muted);font-size:0.9rem;margin-bottom:2rem;}
.fg-intro{background:var(--card);padding:1rem;border-radius:8px;margin-bottom:1rem;border-left:4px solid var(--accent);}
.fg-step,.fg-fix,.fg-ai{padding:1rem;margin-bottom:0.75rem;border-radius:8px;background:var(--card);display:flex;gap:1rem;}
.fg-num{flex-shrink:0;width:28px;height:28px;background:var(--accent);color:var(--bg);border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-weight:700;font-size:0.9rem;}
.fg-fix.fg-error{border-left:4px solid var(--err);}
.fg-fix.fg-warning{border-left:4px solid var(--warn);}
.fg-fix.fg-done{opacity:0.7;}
.fg-action{margin-top:0.5rem;color:var(--muted);font-size:0.95rem;}
.fg-ai .fg-reply{margin-top:0.5rem;}
.fg-q{color:var(--muted);font-size:0.9rem;margin-bottom:0.25rem;}
@media print{body{background:#fff;color:#111;} .fg-intro,.fg-step,.fg-fix,.fg-ai{background:#f8f8f8;border-color:#333;}}
</style>
</head>
<body>
<h1>SkyModderAI Fix Guide</h1>
<p class="fg-meta">${escapeHtml(fixGuideMeta.gameName)} — ${escapeHtml(fixGuideMeta.date)}</p>
${body}
</body>
</html>`;
}

function printFixGuide() {
    if (!hasPaidAccess(currentUserTier)) {
        window.location.href = '/signup-pro';
        return;
    }
    const win = window.open('', '_blank');
    win.document.write(buildFixGuideHTMLForDownload());
    win.document.close();
    win.focus();
    setTimeout(() => { win.print(); win.close(); }, 250);
}

/**
 * Build Nexus Mods search URL for a mod name and game slug.
 */
function nexusSearchUrl(nexusGameSlug, modName) {
    if (!nexusGameSlug || !modName) return null;
    const slug = nexusGameSlug.replace(/[^a-z0-9]/gi, '') || 'skyrimspecialedition';
    const q = encodeURIComponent(String(modName).trim());
    return `https://www.nexusmods.com/games/${slug}/mods?keyword=${q}`;
}

/**
 * Create a DOM section for conflicts of a given severity.
 * @param {string} title - Section title (e.g., "Errors")
 * @param {string} type - Severity class (error/warning/info)
 * @param {Array} conflicts - List of conflict objects
 * @param {string} [nexusGameSlug] - Nexus game slug for "View on Nexus" links
 * @returns {HTMLElement} The constructed section
 */
const CONFLICT_TYPE_LABELS = {
    missing_requirement: 'Missing requirement',
    incompatible: 'Incompatible',
    load_order_violation: 'Load order',
    dirty_edits: 'Dirty edits',
    patch_available: 'Patch available',
    cross_game: 'Wrong game',
    info: 'Suggestion',
    unknown_mod: 'Unknown mod'
};

function createConflictsSection(title, type, conflicts, nexusGameSlug) {
    const section = document.createElement('div');
    section.className = `conflicts-section ${type}`;
    section.dataset.severity = type;

    const header = document.createElement('h4');
    header.textContent = title;
    section.appendChild(header);

    conflicts.forEach(conflict => {
        const item = document.createElement('div');
        item.className = `conflict-item ${type}`;

        const typeKey = conflict.type || '';
        const typeLabel = CONFLICT_TYPE_LABELS[typeKey] || typeKey;
        const badgeWrap = document.createElement('div');
        badgeWrap.className = 'conflict-badges';
        if (typeLabel) {
            const badge = document.createElement('span');
            badge.className = 'conflict-type-badge';
            badge.textContent = typeLabel;
            badgeWrap.appendChild(badge);
        }
        if (conflict.related_mod) {
            const related = document.createElement('span');
            related.className = 'conflict-related-badge';
            related.textContent = '↔ ' + conflict.related_mod;
            related.title = 'Related mod';
            badgeWrap.appendChild(related);
        }
        if (badgeWrap.children.length) item.appendChild(badgeWrap);

        const message = document.createElement('p');
        message.className = 'conflict-message';
        const parseMd = (window.marked && typeof marked.parse === 'function') ? (s) => marked.parse(s) : (window.marked && typeof marked === 'function') ? (s) => marked(s) : null;
        if (parseMd) {
            try {
                message.innerHTML = parseMd(conflict.message || '');
            } catch (_) {
                message.textContent = conflict.message || '';
            }
        } else {
            message.textContent = conflict.message || '';
        }
        item.appendChild(message);

        if (conflict.suggested_action) {
            const action = document.createElement('div');
            action.className = 'conflict-action';
            if (parseMd) {
                try {
                    action.innerHTML = parseMd(conflict.suggested_action);
                } catch (_) {
                    action.textContent = conflict.suggested_action;
                }
            } else {
                action.textContent = conflict.suggested_action;
            }
            item.appendChild(action);
        }

        const modName = conflict.affected_mod;
        if (modName) item.dataset.affectedMod = modName;
        if (conflict.related_mod) item.dataset.relatedMod = conflict.related_mod;

        const isPro = hasPaidAccess(currentUserTier);
        if (isPro) {
            const checkWrap = document.createElement('label');
            checkWrap.className = 'conflict-resolved-check';
            checkWrap.innerHTML = '<input type="checkbox" class="conflict-resolved-cb"> Resolved';
            item.appendChild(checkWrap);
        }

        const links = conflict.links || [];
        if (links.length > 0) {
            const linkWrap = document.createElement('div');
            linkWrap.className = 'conflict-links';
            links.forEach(link => {
                const a = document.createElement('a');
                a.href = link.url || '#';
                a.target = '_blank';
                a.rel = 'noopener noreferrer';
                a.className = 'conflict-link';
                a.textContent = link.title || 'Link';
                linkWrap.appendChild(a);
            });
            item.appendChild(linkWrap);
        } else {
            const nexusUrl = nexusGameSlug && modName ? nexusSearchUrl(nexusGameSlug, modName) : null;
            if (nexusUrl) {
                const nexusLink = document.createElement('a');
                nexusLink.href = nexusUrl;
                nexusLink.target = '_blank';
                nexusLink.rel = 'noopener noreferrer';
                nexusLink.className = 'nexus-link';
                nexusLink.textContent = 'View on Nexus';
                item.appendChild(nexusLink);
            }
        }

        section.appendChild(item);
    });

    return section;
}

/**
 * Show loading overlay and disable analyze button.
 */
function showLoading() {
    if (elements.loadingOverlay) {
        elements.loadingOverlay.classList.remove('hidden');
    } else {
        // Fallback: disable button and show loading text
        if (elements.analyzeBtn) {
            elements.analyzeBtn.disabled = true;
            elements.analyzeBtn.textContent = 'Analyzing...';
        }
    }
}

/**
 * Hide loading overlay and re-enable analyze button.
 */
function hideLoading() {
    if (elements.loadingOverlay) {
        elements.loadingOverlay.classList.add('hidden');
    } else {
        if (elements.analyzeBtn) {
            elements.analyzeBtn.disabled = false;
            elements.analyzeBtn.textContent = 'Analyze Now';
        }
    }
}

let isAnalyzing = false;

/**
 * Send mod list to server for analysis and display results.
 */
async function analyzeModList() {
    if (isAnalyzing) return;
    if (!elements.modListInput) {
        console.error('ModCheck: mod list textarea not found');
        return;
    }

    const modList = elements.modListInput.value.trim();
    // No minimum mod count: 1 or 2 mods (or any number) is fine.
    if (!modList) {
        alert('Please enter at least one mod (e.g. paste a list, use Sample, or add mods from search).');
        return;
    }

    isAnalyzing = true;
    showLoading();
    if (elements.resultsPanel) elements.resultsPanel.classList.add('hidden');

    const game = elements.gameSelect ? elements.gameSelect.value : 'skyrimse';
    const masterlistVersionEl = document.getElementById('masterlist-version');
    const gameVersionEl = document.getElementById('game-version');
    const masterlistVersion = (masterlistVersionEl && masterlistVersionEl.value) ? masterlistVersionEl.value : '';
    const gameVersion = (gameVersionEl && gameVersionEl.value) ? gameVersionEl.value : '';

    try {
        const body = { mod_list: modList, game };
        if (masterlistVersion) body.masterlist_version = masterlistVersion;
        if (gameVersion) body.game_version = gameVersion;
        const specs = getCurrentSpecs();
        if (Object.keys(specs).length > 0) body.specs = specs;
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            alert(error.error || 'Analysis failed');
            hideLoading();
            isAnalyzing = false;
            return;
        }
        {
            const data = await response.json();
            if (!elements.conflictsContainer) return;

        elements.resultsPanel?.classList.remove('limit-reached');

        // Ensure conflict arrays exist (defensive for API response shape)
        const errors = data.conflicts?.errors ?? [];
        const warnings = data.conflicts?.warnings ?? [];
        const info = data.conflicts?.info ?? [];

        // Clear previous results and results search (fresh analysis = fresh view)
        elements.conflictsContainer.innerHTML = '';
        const resultsSearchInput = document.getElementById('results-search-input');
        if (resultsSearchInput) { resultsSearchInput.value = ''; }
        const resultsSearchClear = document.getElementById('results-search-clear');
        if (resultsSearchClear) resultsSearchClear.classList.add('hidden');

        const nexusSlug = data.nexus_game_slug || 'skyrimspecialedition';
        if (errors.length) {
            elements.conflictsContainer.appendChild(
                createConflictsSection('Errors', 'error', errors, nexusSlug)
            );
        }
        if (warnings.length) {
            elements.conflictsContainer.appendChild(
                createConflictsSection('Warnings', 'warning', warnings, nexusSlug)
            );
        }
        if (info.length) {
            elements.conflictsContainer.appendChild(
                createConflictsSection('Info', 'info', info, nexusSlug)
            );
        }

        if (errors.length === 0 && warnings.length === 0 && info.length === 0) {
            elements.conflictsContainer.innerHTML = '<p class="no-conflicts">No issues found. Your load order looks good.</p>';
        }

        const gameVersionWarn = data.game_version_warning;
        if (gameVersionWarn && gameVersionWarn.message) {
            const warnBox = document.createElement('div');
            warnBox.className = 'game-version-warning-banner';
            warnBox.innerHTML = `<strong>Version note:</strong> ${escapeHtml(gameVersionWarn.message)}` +
                (gameVersionWarn.link ? ` <a href="${escapeHtml(gameVersionWarn.link)}" target="_blank" rel="noopener">Downgrade patcher</a>` : '');
            elements.conflictsContainer.insertBefore(warnBox, elements.conflictsContainer.firstChild);
        }

        const thingsToVerify = data.things_to_verify || [];
        if (thingsToVerify.length > 0) {
            const verifyBox = document.createElement('div');
            verifyBox.className = 'things-to-verify-box';
            verifyBox.innerHTML = '<h4>Things to verify on your PC</h4><p class="hint">We can\'t see your system. The masterlist suggests checking:</p><ul></ul>';
            const ul = verifyBox.querySelector('ul');
            thingsToVerify.forEach(t => {
                const li = document.createElement('li');
                li.textContent = t;
                ul.appendChild(li);
            });
            elements.conflictsContainer.appendChild(verifyBox);
        }

        const dataSource = data.data_source || '';
        const masterlistVerDisplay = data.masterlist_version || 'latest';
        if (dataSource) {
            const footer = document.createElement('p');
            footer.className = 'results-data-source hint';
            const gameForRefresh = data.game || (elements.gameSelect && elements.gameSelect.value) || 'skyrimse';
            footer.innerHTML = `Data: ${dataSource}${masterlistVerDisplay !== 'latest' ? ` (branch ${masterlistVerDisplay})` : ' (latest)'}. Mod search uses the same data. <button type="button" class="link-button" id="refresh-masterlist-btn" data-game="${gameForRefresh}">Refresh data</button>`;
            elements.conflictsContainer.appendChild(footer);
            const refreshBtn = document.getElementById('refresh-masterlist-btn');
            if (refreshBtn) {
                refreshBtn.addEventListener('click', async () => {
                    refreshBtn.disabled = true;
                    refreshBtn.textContent = 'Refreshing…';
                    try {
                        const r = await fetch('/api/refresh-masterlist', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ game: refreshBtn.getAttribute('data-game') }) });
                        const j = await r.json().catch(() => ({}));
                        if (r.ok && j.success) refreshBtn.textContent = 'Refreshed';
                        else refreshBtn.textContent = 'Refresh data';
                    } catch (e) { refreshBtn.textContent = 'Refresh data'; }
                    refreshBtn.disabled = false;
                });
            }
        }

        // Update summary counts
        const summary = data.summary ?? {};
        if (elements.errorCount) elements.errorCount.textContent = summary.errors ?? errors.length;
        if (elements.warningCount) elements.warningCount.textContent = summary.warnings ?? warnings.length;
        if (elements.infoCount) elements.infoCount.textContent = summary.info ?? info.length;

        if (data.user_tier) currentUserTier = data.user_tier;
        currentReport = data.ai_context || data.report;
        currentSuggestedOrder = data.suggested_load_order || [];
        currentAnalysisData = data;
        lastAnalysisSummary = {
            mod_count: data.mod_count,
            enabled_count: data.enabled_count,
            plugin_limit_warning: data.plugin_limit_warning || null
        };

        if (hasPaidAccess(currentUserTier)) {
            buildFixGuideFromAnalysis(data);
        }

        const systemImpactSection = document.getElementById('system-impact-section');
        const systemImpactContent = document.getElementById('system-impact-content');
        const systemImpact = data.system_impact;
        if (systemImpactSection) {
            if (systemImpact) {
                systemImpactSection.classList.remove('hidden');
                systemImpactContent?.classList.remove('hidden');
                systemImpactContent.innerHTML = renderSystemImpact(systemImpact);
            } else {
                systemImpactSection.classList.add('hidden');
            }
        }

        if (elements.loadOrderSection) {
            const hasLoadOrder = currentSuggestedOrder.length > 0;
            elements.loadOrderSection.classList.toggle('hidden', !hasLoadOrder);
            const actionsWrap = document.getElementById('load-order-actions-wrap');
            if (actionsWrap) actionsWrap.classList.remove('hidden');
        }
        // Export (copy/download report) is free for everyone — your analysis, your data
        const exportWrap = document.getElementById('export-buttons-wrap');
        const exportProCta = document.getElementById('export-pro-cta');
        if (exportWrap) exportWrap.classList.remove('hidden');
        if (exportProCta) exportProCta.classList.add('hidden');
        if (elements.pluginLimitBanner) {
            if (data.plugin_limit_warning) {
                elements.pluginLimitBanner.textContent = data.plugin_limit_warning;
                elements.pluginLimitBanner.classList.remove('hidden');
            } else {
                elements.pluginLimitBanner.classList.add('hidden');
            }
        }

        // Mod warnings (plugin limit, VRAM, system strain) with fix links
        const modWarningsSection = document.getElementById('mod-warnings-section');
        const modWarnings = data.mod_warnings || [];
        if (modWarningsSection) {
            if (modWarnings.length > 0) {
                modWarningsSection.classList.remove('hidden');
                modWarningsSection.innerHTML = modWarnings.map(w => {
                    const link = w.link_url ? `<a href="${escapeHtml(w.link_url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(w.link_title || 'How to fix')}</a>` : '';
                    const extra = w.link_extra ? ` <a href="${escapeHtml(w.link_extra.url || '#')}" target="_blank" rel="noopener noreferrer">${escapeHtml(w.link_extra.title || 'More')}</a>` : '';
                    return `<div class="mod-warning mod-warning-${w.severity || 'info'}"><span>${escapeHtml(w.message || '')}</span>${link ? ` — ${link}` : ''}${extra}</div>`;
                }).join('');
            } else {
                modWarningsSection.classList.add('hidden');
                modWarningsSection.innerHTML = '';
            }
        }

        applyConflictFilters();
        updateModCounter();

        const canChat = hasPaidAccess(currentUserTier) && aiChatEnabled;
        if (elements.chatSection) elements.chatSection.classList.toggle('hidden', !canChat);
        if (canChat && elements.chatMessages) {
            elements.chatMessages.innerHTML = '';
            appendChatMessage('assistant', "Hi! I'm here to help with your load order. Ask me about any conflict above, how to fix it, or what to do next. I have your full analysis—just ask.");
        }
        if (elements.chatUpgradeCta) {
            elements.chatUpgradeCta.classList.toggle('hidden', canChat);
            const upgradeText = document.getElementById('chat-upgrade-text');
            if (upgradeText) {
                const total = (summary?.errors || 0) + (summary?.warnings || 0) + (summary?.info || 0);
                if (hasPaidAccess(currentUserTier)) {
                    upgradeText.textContent = 'Your paid tier includes AI chat—set OPENAI_API_KEY to enable.';
                } else if (total > 0) {
                    upgradeText.textContent = `Found ${total} issue${total === 1 ? '' : 's'}. Get Pro to chat with our AI—ask questions, get step-by-step help.`;
                } else {
                    upgradeText.textContent = 'Get Pro to unlock AI chat, Live Fix Guide, and save mod lists.';
                }
            }
        }
        const analysisFeedbackPanel = document.getElementById('analysis-feedback-panel');
        if (analysisFeedbackPanel) analysisFeedbackPanel.classList.remove('hidden');
        trackClientActivity('analyze_success', {
            game: data.game || game,
            mod_count: data.mod_count || 0,
            enabled_count: data.enabled_count || 0,
            errors: summary?.errors || 0,
            warnings: summary?.warnings || 0,
        });
        if (elements.resultsPanel) {
            elements.resultsPanel.classList.remove('hidden');
            elements.resultsPanel.scrollIntoView({ behavior: 'smooth' });
        }
        }
    } catch (error) {
        console.error('Analysis error:', error);
        alert('Analysis failed. Please check your connection and try again.');
    } finally {
        isAnalyzing = false;
        hideLoading();
    }
}

/**
 * Append a message to the chat UI. Optionally include mod preview cards and top picks by category.
 */
function appendChatMessage(role, text, modPreviews, topPicks) {
    if (!elements.chatMessages) return;
    const div = document.createElement('div');
    div.className = `chat-msg chat-msg-${role}`;
    const p = document.createElement('div');
    p.className = 'chat-msg-body';
    const parseMd = (window.marked && typeof marked.parse === 'function') ? (s) => marked.parse(s) : (window.marked && typeof marked === 'function') ? (s) => marked(s) : (s) => s;
    p.innerHTML = role === 'assistant' ? parseMd(String(text || '')) : escapeHtml(String(text || ''));
    div.appendChild(p);
    if (role === 'assistant') {
        if (topPicks && typeof topPicks === 'object' && Object.keys(topPicks).length > 0) {
            const picksSection = document.createElement('div');
            picksSection.className = 'chat-top-picks';
            const catLabels = { utility: 'Utility', design: 'Design', fun: 'Fun', environmental: 'Environmental' };
            for (const [cat, items] of Object.entries(topPicks)) {
                if (!items || !items.length) continue;
                const label = catLabels[cat] || cat;
                const catDiv = document.createElement('div');
                catDiv.className = 'chat-top-picks-category';
                catDiv.innerHTML = `<p class="chat-top-picks-label">${escapeHtml(label)}</p><div class="chat-mod-previews chat-top-picks-cards"></div>`;
                const cards = catDiv.querySelector('.chat-top-picks-cards');
                const catTag = (r) => r.category ? `<span class="mod-preview-tag mod-preview-tag-${escapeHtml(r.category)}">${escapeHtml((r.category || '').charAt(0).toUpperCase() + (r.category || '').slice(1))}</span>` : '';
                cards.innerHTML = items.slice(0, 2).map(r => `
                    <div class="mod-preview-card" data-mod-name="${escapeHtml(r.name)}">
                        ${catTag(r)}
                        <a href="${escapeHtml(r.nexus_url || '#')}" target="_blank" rel="noopener noreferrer" title="${escapeHtml(r.name)}">
                            <img src="${escapeHtml(r.image_url || '/static/icons/mod-placeholder.svg')}" alt="" loading="lazy">
                            <span class="mod-preview-name">${escapeHtml(r.name)}</span>
                            <span class="mod-preview-reason">${escapeHtml(r.reason || '')}</span>
                        </a>
                        <button type="button" class="mod-preview-add" title="Add to list" aria-label="Add to list">+</button>
                    </div>
                `).join('');
                _bindModPreviewAddButtons(cards);
                picksSection.appendChild(catDiv);
            }
            if (picksSection.children.length) div.appendChild(picksSection);
        }
        if (modPreviews && modPreviews.length > 0) {
            const previewsDiv = document.createElement('div');
            previewsDiv.className = 'chat-mod-previews';
            const catTag = (r) => r.category ? `<span class="mod-preview-tag mod-preview-tag-${escapeHtml(r.category)}">${escapeHtml((r.category || '').charAt(0).toUpperCase() + (r.category || '').slice(1))}</span>` : '';
            previewsDiv.innerHTML = modPreviews.map(r => `
                <div class="mod-preview-card" data-mod-name="${escapeHtml(r.name)}">
                    ${catTag(r)}
                    <a href="${escapeHtml(r.nexus_url || '#')}" target="_blank" rel="noopener noreferrer" title="${escapeHtml(r.name)}">
                        <img src="${escapeHtml(r.image_url || '/static/icons/mod-placeholder.svg')}" alt="" loading="lazy">
                        <span class="mod-preview-name">${escapeHtml(r.name)}</span>
                        <span class="mod-preview-reason">${escapeHtml(r.reason || '')}</span>
                    </a>
                    <button type="button" class="mod-preview-add" title="Add to list" aria-label="Add to list">+</button>
                </div>
            `).join('');
            _bindModPreviewAddButtons(previewsDiv);
            div.appendChild(previewsDiv);
        }
    }
    elements.chatMessages.appendChild(div);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

function _bindModPreviewAddButtons(container) {
    if (!container) return;
    container.querySelectorAll('.mod-preview-add').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            const name = btn.closest('.mod-preview-card')?.dataset?.modName;
            if (name && elements.modListInput) {
                const prefix = elements.modListInput.value.trim() ? '\n' : '';
                elements.modListInput.value += prefix + '*' + name;
                updateModCounter();
            }
        });
    });
}

/**
 * Send a message to the AI chat (Pro only).
 */
async function sendChatMessage(e) {
    e.preventDefault();
    const input = elements.chatInput;
    const btn = elements.chatSendBtn;
    const msg = input?.value?.trim();
    if (!msg || !elements.chatMessages) return;
    input.value = '';
    appendChatMessage('user', msg);
    if (btn) btn.disabled = true;
    try {
        const gameSelect = document.getElementById('game-select');
        const game = (gameSelect && gameSelect.value) ? gameSelect.value : 'skyrimse';
        const modList = parseModListFromTextarea();
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg, context: currentReport || '', game, mod_list: modList })
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            appendChatMessage('assistant', data.error || 'Something went wrong.');
            return;
        }
        appendChatMessage('assistant', data.reply || 'No response.', data.recommended_mods || [], data.top_picks || {});
        addStepToFixGuide({ type: 'ai', content: data.reply_for_fix_guide || data.reply || '', question: msg });
    } catch (err) {
        appendChatMessage('assistant', 'Network error. Try again.');
    } finally {
        if (btn) btn.disabled = false;
    }
}

/**
 * Open checkout modal (frictionless: email only, no signup).
 */
function openCheckoutModal() {
    const modal = document.getElementById('checkout-modal');
    if (modal) {
        modal.classList.remove('hidden');
        modal.setAttribute('aria-hidden', 'false');
    }
}

/**
 * Close checkout modal.
 */
function closeCheckoutModal() {
    const modal = document.getElementById('checkout-modal');
    if (modal) {
        modal.classList.add('hidden');
        modal.setAttribute('aria-hidden', 'true');
    }
}

function showActionFeedback(message) {
    const feedback = document.getElementById('action-feedback');
    if (feedback) {
        feedback.textContent = message;
        window.setTimeout(() => {
            if (feedback.textContent === message) {
                feedback.textContent = '';
            }
        }, 3500);
        return;
    }
    alert(message);
}

function trackClientActivity(eventType, eventData = {}) {
    fetch('/api/activity/track', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_type: eventType, event_data: eventData })
    }).catch(() => {});
}

function initAnalysisFeedbackPanel() {
    const panel = document.getElementById('analysis-feedback-panel');
    const status = document.getElementById('analysis-feedback-status');
    const feedbackText = document.getElementById('analysis-feedback-text');
    if (!panel) return;
    panel.querySelectorAll('.analysis-rating-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const rating = parseInt(btn.dataset.rating, 10);
            if (!rating) return;
            if (status) status.textContent = 'Sending…';
            try {
                const res = await fetch('/api/satisfaction/survey', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        rating,
                        feedback_text: (feedbackText?.value || '').trim(),
                        context: {
                            game: elements.gameSelect?.value || 'skyrimse',
                            mod_count: lastAnalysisSummary?.mod_count || 0,
                            enabled_count: lastAnalysisSummary?.enabled_count || 0,
                        }
                    })
                });
                const data = await res.json().catch(() => ({}));
                if (res.ok && data.success) {
                    if (status) status.textContent = 'Thanks for helping improve the tool.';
                    trackClientActivity('analysis_feedback_submit', { rating });
                } else if (status) {
                    status.textContent = data.error || 'Could not send rating.';
                }
            } catch (e) {
                if (status) status.textContent = 'Could not send rating right now.';
            }
        });
    });
}

function initFeedbackModal() {
    const fab = document.getElementById('feedback-fab');
    const modal = document.getElementById('feedback-modal');
    const closeBtn = document.getElementById('feedback-modal-close');
    const cancelBtn = document.getElementById('feedback-modal-cancel');
    const backdrop = document.getElementById('feedback-modal-backdrop');
    const submitBtn = document.getElementById('feedback-submit-btn');
    const typeEl = document.getElementById('feedback-type');
    const catEl = document.getElementById('feedback-category');
    const contentEl = document.getElementById('feedback-content');
    const statusEl = document.getElementById('feedback-status');
    if (!fab || !modal || !submitBtn) return;

    function openModal() {
        modal.classList.remove('hidden');
        modal.setAttribute('aria-hidden', 'false');
        if (statusEl) statusEl.textContent = '';
    }
    function closeModal() {
        modal.classList.add('hidden');
        modal.setAttribute('aria-hidden', 'true');
    }
    fab.addEventListener('click', openModal);
    [closeBtn, cancelBtn, backdrop].filter(Boolean).forEach(el => el.addEventListener('click', closeModal));

    submitBtn.addEventListener('click', async () => {
        const content = (contentEl?.value || '').trim();
        if (content.length < 5) {
            if (statusEl) statusEl.textContent = 'Please add a little more detail.';
            return;
        }
        submitBtn.disabled = true;
        if (statusEl) statusEl.textContent = 'Sending…';
        try {
            const res = await fetch('/api/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    type: typeEl?.value || 'feedback',
                    category: catEl?.value || 'general',
                    content,
                    context: {
                        current_tab: document.querySelector('.main-tab.active')?.dataset?.tab || 'analyze',
                        game: elements.gameSelect?.value || 'skyrimse',
                    }
                })
            });
            const data = await res.json().catch(() => ({}));
            if (res.ok && data.success) {
                if (statusEl) statusEl.textContent = 'Thanks. Feedback submitted.';
                if (contentEl) contentEl.value = '';
                trackClientActivity('feedback_modal_submit', { type: typeEl?.value || 'feedback' });
                setTimeout(closeModal, 600);
            } else if (statusEl) {
                statusEl.textContent = data.error || 'Could not submit feedback.';
            }
        } catch (e) {
            if (statusEl) statusEl.textContent = 'Network error.';
        } finally {
            submitBtn.disabled = false;
        }
    });
}

/**
 * Submit checkout form: email → Stripe, no account required first.
 */
async function submitCheckout(event) {
    event.preventDefault();
    const input = document.getElementById('checkout-email');
    const btn = document.getElementById('checkout-submit-btn');
    if (!input || !input.value.trim() || !input.value.includes('@')) {
        alert('Please enter a valid email.');
        return;
    }
    const email = input.value.trim();
    if (btn) {
        btn.disabled = true;
        btn.textContent = 'Redirecting…';
    }
    try {
        const response = await fetch('/api/create-checkout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(data.error || `Checkout failed (${response.status})`);
        }
        if (data.checkout_url) {
            window.location.href = data.checkout_url;
        } else {
            throw new Error('Missing checkout URL');
        }
    } catch (err) {
        console.error('Checkout error:', err);
        alert(err.message || 'Checkout failed. Please try again.');
        if (btn) {
            btn.disabled = false;
            btn.textContent = 'Continue to checkout';
        }
    }
}

/**
 * Initiate Pro upgrade: show checkout modal (no prompt, no signup gate).
 */
function upgradeToPro() {
    openCheckoutModal();
}

/**
 * Show/hide conflict sections and items based on filter checkboxes and search.
 * Search is available to all tiers (basic UX).
 */
function applyConflictFilters() {
    const showErrors = elements.filterErrors ? elements.filterErrors.checked : true;
    const showWarnings = elements.filterWarnings ? elements.filterWarnings.checked : true;
    const showInfo = elements.filterInfo ? elements.filterInfo.checked : true;
    const searchEl = document.getElementById('results-search-input');
    const searchQuery = (searchEl && searchEl.value || '').trim().toLowerCase();
    const countEl = document.getElementById('results-search-count');
    const clearBtn = document.getElementById('results-search-clear');
    if (clearBtn) clearBtn.classList.toggle('hidden', !searchQuery);

    if (!elements.conflictsContainer) return;

    let totalBySeverity = 0;  // items in severity-visible sections
    let visibleItems = 0;

    elements.conflictsContainer.querySelectorAll('.conflicts-section[data-severity]').forEach(section => {
        const sev = section.dataset.severity;
        const sectionVisible = (sev === 'error' && showErrors) || (sev === 'warning' && showWarnings) || (sev === 'info' && showInfo);
        let visibleCount = 0;
        const items = section.querySelectorAll('.conflict-item');
        if (sectionVisible) totalBySeverity += items.length;
        items.forEach(item => {
            const matchesSearch = !searchQuery || (item.textContent && item.textContent.toLowerCase().includes(searchQuery));
            const show = sectionVisible && matchesSearch;
            item.classList.toggle('hidden', !show);
            if (show) { visibleCount++; visibleItems++; }
        });
        section.classList.toggle('hidden', !sectionVisible || visibleCount === 0);
    });

    // Filter system impact ranking list (heaviest mods)
    const systemImpactSection = document.getElementById('system-impact-section');
    let totalImpactItems = 0;
    let visibleImpactItems = 0;
    if (systemImpactSection && !systemImpactSection.classList.contains('hidden')) {
        const impactItems = systemImpactSection.querySelectorAll('.system-impact-item');
        totalImpactItems = impactItems.length;
        impactItems.forEach(item => {
            const matchesSearch = !searchQuery || (item.textContent && item.textContent.toLowerCase().includes(searchQuery));
            item.classList.toggle('hidden', !matchesSearch);
            if (matchesSearch) visibleImpactItems++;
        });
    }
    visibleItems += visibleImpactItems;
    const totalSearchable = totalBySeverity + totalImpactItems;

    // Update search count and no-matches message
    const noMatchesEl = document.getElementById('results-search-no-matches');
    if (searchQuery) {
        if (countEl && totalSearchable > 0) {
            countEl.textContent = visibleItems === totalSearchable
                ? `${totalSearchable} result${totalSearchable === 1 ? '' : 's'}`
                : `Showing ${visibleItems} of ${totalSearchable} result${totalSearchable === 1 ? '' : 's'}`;
        }
        if (visibleItems === 0 && totalSearchable > 0) {
            if (!noMatchesEl) {
                const msg = document.createElement('p');
                msg.id = 'results-search-no-matches';
                msg.className = 'results-search-no-matches hint';
                msg.textContent = `No results match "${searchQuery}". Try different keywords or clear the search.`;
                elements.conflictsContainer.appendChild(msg);
            }
        } else if (noMatchesEl) noMatchesEl.remove();
    } else {
        if (countEl) countEl.textContent = '';
        if (noMatchesEl) noMatchesEl.remove();
    }
}

/**
 * Copy suggested load order as plugins.txt (one plugin per line with * prefix).
 */
function copyLoadOrderAsPluginsTxt() {
    if (!currentSuggestedOrder.length) {
        alert('No suggested load order available. Run analysis first.');
        return;
    }
    const text = currentSuggestedOrder.map(name => '*' + name).join('\n');
    navigator.clipboard.writeText(text).then(() => {
        if (elements.copyLoadOrderBtn) {
            const orig = elements.copyLoadOrderBtn.textContent;
            elements.copyLoadOrderBtn.textContent = 'Copied!';
            setTimeout(() => { elements.copyLoadOrderBtn.textContent = orig; }, 2000);
        }
    }).catch(() => alert('Failed to copy.'));
}

/**
 * Apply suggested load order to the textarea (plugins.txt format).
 */
function applyLoadOrder() {
    if (!currentSuggestedOrder.length || !elements.modListInput) return;
    if (!window.confirm('Replace your current mod list with the suggested load order?')) return;
    elements.modListInput.value = currentSuggestedOrder.map(name => '*' + name).join('\n');
    updateModCounter();
}

/**
 * Download current report as .txt file.
 */
function downloadReport() {
    if (!currentReport) {
        alert('No report to download. Run analysis first.');
        return;
    }
    const game = currentAnalysisData?.game || (elements.gameSelect && elements.gameSelect.value) || 'unknown';
    const summary = currentAnalysisData?.summary || {};
    const lines = [
        `SkyModderAI Analysis Report`,
        `Date: ${new Date().toISOString()}`,
        `Game: ${game}`,
        `Total Mods: ${currentAnalysisData?.mod_count ?? 'unknown'}`,
        `Errors: ${summary.errors ?? 'unknown'} | Warnings: ${summary.warnings ?? 'unknown'} | Info: ${summary.info ?? 'unknown'}`,
        '',
        currentReport,
    ];
    if (currentSuggestedOrder.length > 0) {
        lines.push('', 'Suggested Load Order (* = enabled):');
        lines.push(...currentSuggestedOrder.map((name) => `*${name}`));
    }
    const blob = new Blob([lines.join('\n')], { type: 'text/plain' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `modcheck-report-${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    URL.revokeObjectURL(a.href);
}

/**
 * Download analysis payload as JSON for tooling/history pipelines.
 */
function downloadReportJson() {
    if (!currentAnalysisData) {
        alert('No report JSON available. Run analysis first.');
        return;
    }
    const payload = {
        exported_at: new Date().toISOString(),
        report_text: currentReport || '',
        suggested_load_order: currentSuggestedOrder || [],
        analysis: currentAnalysisData,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `modcheck-report-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
}

/**
 * Paste from clipboard into mod list.
 */
async function pasteFromClipboard() {
    if (!elements.modListInput) return;
    try {
        const text = await navigator.clipboard.readText();
        elements.modListInput.value = text;
        updateModCounter();
    } catch (e) {
        alert('Could not read clipboard. Paste with Ctrl+V into the text area.');
    }
}

/**
 * Load a game-specific sample mod list (typical base + DLC + common first downloads; some may conflict to show utility).
 */
async function loadSampleList() {
    const gameSelect = document.getElementById('game-select');
    const game = (gameSelect && gameSelect.value) ? gameSelect.value : 'skyrimse';
    const modListInput = document.getElementById('mod-list-input');
    const sampleBtn = document.getElementById('sample-btn');
    if (!modListInput) return;
    const origText = sampleBtn ? sampleBtn.textContent : '';
    if (sampleBtn) {
        sampleBtn.disabled = true;
        sampleBtn.textContent = 'Loading…';
    }
    try {
        const res = await fetch(`/api/sample-mod-list?game=${encodeURIComponent(game)}`);
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            alert(data.error || `Could not load sample (${res.status}). Try again.`);
            return;
        }
        const modList = (data.mod_list != null) ? String(data.mod_list) : '';
        modListInput.value = modList;
        updateModCounter();
        if (modList.length === 0) {
            alert(`No sample list for "${game}". Try another game.`);
        }
    } catch (e) {
        console.error('Failed to load sample:', e);
        alert('Could not load sample list. Check your connection and try again.');
    } finally {
        if (sampleBtn) {
            sampleBtn.disabled = false;
            sampleBtn.textContent = origText || 'Sample';
        }
    }
}

/**
 * Copy current report to clipboard.
 */
function copyReport() {
    if (!currentReport) {
        alert('No report to copy.');
        return;
    }
    navigator.clipboard.writeText(currentReport)
        .then(() => {
            if (elements.exportBtn) {
                const originalText = elements.exportBtn.textContent;
                elements.exportBtn.textContent = 'Copied!';
                setTimeout(() => { elements.exportBtn.textContent = originalText; }, 2000);
            }
        })
        .catch(err => {
            console.error('Clipboard error:', err);
            alert('Failed to copy to clipboard.');
        });
}

// -------------------------------------------------------------------
// Event Listeners
// -------------------------------------------------------------------
if (elements.modListInput) {
    elements.modListInput.addEventListener('input', updateModCounter);
}
const autoFormatBtn = document.getElementById('auto-format-btn');
if (autoFormatBtn) {
    autoFormatBtn.addEventListener('click', () => refreshInputMatchPreview({ applyFormatted: true }));
}
const refreshMatchesBtn = document.getElementById('refresh-matches-btn');
if (refreshMatchesBtn) {
    refreshMatchesBtn.addEventListener('click', () => refreshInputMatchPreview({ silent: false }));
}

(function setupModSearch() {
    const inputEl = document.getElementById('mod-search-input');
    const resultsEl = document.getElementById('mod-search-results');
    const clearBtn = document.getElementById('mod-search-clear');
    if (!inputEl || !resultsEl) return;
    inputEl.addEventListener('input', () => {
        clearTimeout(modSearchTimeout);
        modSearchTimeout = setTimeout(runModSearch, 220);
    });
    inputEl.addEventListener('blur', () => {
        setTimeout(() => {
            if (!resultsEl.contains(document.activeElement) && !clearBtn?.contains(document.activeElement)) resultsEl.classList.add('hidden');
        }, 180);
    });
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            inputEl.value = '';
            inputEl.focus();
            resultsEl.classList.add('hidden');
            resultsEl.innerHTML = '';
            clearBtn.classList.add('hidden');
        });
    }
    inputEl.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            inputEl.blur();
            resultsEl.classList.add('hidden');
            return;
        }
        const rows = resultsEl.querySelectorAll('.mod-search-row[data-mod-name]');
        if (rows.length === 0) return;
        const current = resultsEl.querySelector('.mod-search-row.highlighted');
        let idx = current ? parseInt(current.dataset.index, 10) : -1;
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            idx = Math.min(idx + 1, rows.length - 1);
            rows.forEach(r => r.classList.remove('highlighted'));
            rows[idx].classList.add('highlighted');
            rows[idx].scrollIntoView({ block: 'nearest' });
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            idx = Math.max(idx - 1, 0);
            rows.forEach(r => r.classList.remove('highlighted'));
            rows[idx].classList.add('highlighted');
            rows[idx].scrollIntoView({ block: 'nearest' });
        } else if (e.key === 'Enter' && current) {
            e.preventDefault();
            const name = current.dataset.modName;
            if (name) {
                const listInput = document.getElementById('mod-list-input');
                if (listInput) {
                    const prefix = listInput.value.trim() ? '\n' : '';
                    listInput.value += prefix + '*' + name;
                    updateModCounter();
                }
                resultsEl.classList.add('hidden');
                inputEl.value = '';
                if (clearBtn) clearBtn.classList.add('hidden');
            }
        }
    });
})();
document.addEventListener('keydown', (e) => {
    if (e.key === '/' && !e.ctrlKey && !e.metaKey && !e.altKey) {
        const target = e.target;
        if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) return;
        e.preventDefault();
        // When results are visible, focus results search; otherwise mod search
        const resultsPanel = document.getElementById('results-panel');
        const resultsSearchInput = document.getElementById('results-search-input');
        const modSearchInput = document.getElementById('mod-search-input');
        if (resultsPanel && !resultsPanel.classList.contains('hidden') && resultsSearchInput) {
            resultsSearchInput.focus();
        } else if (modSearchInput) {
            modSearchInput.focus();
        }
    }
    if (e.key === 'Escape') {
        const resultsSearchInput = document.getElementById('results-search-input');
        if (resultsSearchInput && document.activeElement === resultsSearchInput) {
            resultsSearchInput.value = '';
            resultsSearchInput.blur();
            applyConflictFilters();
            const clearBtn = document.getElementById('results-search-clear');
            if (clearBtn) clearBtn.classList.add('hidden');
        }
    }
});
document.addEventListener('click', (e) => {
    const resultsEl = document.getElementById('mod-search-results');
    const inputEl = document.getElementById('mod-search-input');
    if (resultsEl && inputEl && !resultsEl.contains(e.target) && e.target !== inputEl) {
        resultsEl.classList.add('hidden');
    }
});

if (elements.clearBtn) {
    elements.clearBtn.addEventListener('click', () => {
        lastAnalysisSummary = null; // so "X enabled / Y total" and plugin limit warning reset
        if (elements.modListInput) {
            elements.modListInput.value = '';
            updateModCounter();
        }
        if (elements.resultsPanel) {
            elements.resultsPanel.classList.add('hidden');
        }
    });
}

const analyzeForm = document.getElementById('analyze-form');
if (analyzeForm) {
    analyzeForm.addEventListener('submit', (e) => {
        e.preventDefault();
        analyzeModList();
    });
}
// Direct click handler as fallback (form submit can be unreliable in some setups)
if (elements.analyzeBtn) {
    elements.analyzeBtn.addEventListener('click', (e) => {
        e.preventDefault();
        analyzeModList();
    });
}

if (elements.exportBtn) {
    elements.exportBtn.addEventListener('click', copyReport);
}

if (elements.newAnalysisBtn) {
    elements.newAnalysisBtn.addEventListener('click', () => {
        if (elements.resultsPanel) {
            elements.resultsPanel.classList.add('hidden');
        }
        if (elements.modListInput) {
            elements.modListInput.focus();
        }
    });
}

const specsSaveBtn = document.getElementById('specs-save-btn');
if (specsSaveBtn) {
    specsSaveBtn.addEventListener('click', saveSpecs);
}
const scanSystemBtn = document.getElementById('scan-system-btn');
if (scanSystemBtn) {
    scanSystemBtn.addEventListener('click', scanSystem);
}
loadSpecs();
if (elements.pasteBtn) {
    elements.pasteBtn.addEventListener('click', pasteFromClipboard);
}
const shareLinkBtn = document.getElementById('share-link-btn');
if (shareLinkBtn) shareLinkBtn.addEventListener('click', copyShareLink);

// -------------------------------------------------------------------
// Game folder scan (Pro) — AI analyzes Data folder, plugins, structure
// -------------------------------------------------------------------
const GAME_FOLDER_KEY_FILES = ['plugins.txt', 'loadorder.txt', 'modlist.txt', 'Skyrim.ini', 'SkyrimPrefs.ini', 'Fallout4.ini', 'Starfield.ini'];
const GAME_FOLDER_PLUGIN_EXT = ['.esm', '.esp', '.esl'];
const GAME_FOLDER_MAX_FILES = 5000;
const GAME_FOLDER_MAX_TREE_DEPTH = 4;
const GAME_FOLDER_MAX_TREE_ITEMS = 200;

async function collectFilesFromDirectoryHandle(handle, path = '', files = []) {
    if (files.length >= GAME_FOLDER_MAX_FILES) return files;
    for await (const entry of handle.values()) {
        const fullPath = path ? `${path}/${entry.name}` : entry.name;
        if (entry.kind === 'file') {
            files.push({ path: fullPath, file: await entry.getFile() });
        } else if (entry.kind === 'directory') {
            await collectFilesFromDirectoryHandle(entry, fullPath, files);
        }
    }
    return files;
}

function buildFolderTree(files) {
    const tree = {};
    for (const { path } of files) {
        const parts = path.split(/[/\\]/);
        let cur = tree;
        for (let i = 0; i < Math.min(parts.length, GAME_FOLDER_MAX_TREE_DEPTH); i++) {
            const p = parts[i];
            if (!cur[p]) cur[p] = i < GAME_FOLDER_MAX_TREE_DEPTH - 1 ? {} : '…';
            cur = cur[p];
            if (typeof cur === 'string') break;
        }
    }
    const lines = [];
    function walk(obj, indent) {
        const keys = Object.keys(obj).sort();
        for (const k of keys.slice(0, 50)) {
            const v = obj[k];
            lines.push(indent + k + (typeof v === 'object' ? '/' : ''));
            if (lines.length >= GAME_FOLDER_MAX_TREE_ITEMS) return;
            if (typeof v === 'object' && v !== null) walk(v, indent + '  ');
        }
    }
    walk(tree, '');
    return lines.join('\n');
}

async function processGameFolderFiles(files) {
    const keyFilesContent = {};
    const plugins = [];
    const treePaths = [];
    for (const { path, file } of files) {
        const name = path.split(/[/\\]/).pop().toLowerCase();
        const lowerPath = path.toLowerCase();
        if (GAME_FOLDER_KEY_FILES.some(k => name === k.toLowerCase())) {
            try {
                const text = await file.text();
                keyFilesContent[path] = text.slice(0, 8000);
            } catch (_) {}
        }
        if (GAME_FOLDER_PLUGIN_EXT.some(ext => lowerPath.endsWith(ext))) {
            plugins.push(path.replace(/^.*[/\\]/, ''));
        }
        treePaths.push(path);
    }
    const tree = buildFolderTree(files.map(f => ({ path: f.path })));
    return { tree, keyFilesContent, plugins: [...new Set(plugins)].sort(), fileCount: files.length };
}

async function scanGameFolderWithPayload(payload) {
    const gameSelect = document.getElementById('game-select');
    const game = (gameSelect && gameSelect.value) ? gameSelect.value : 'skyrimse';
    const res = await fetch('/api/scan-game-folder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...payload, game })
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || `Scan failed (${res.status})`);
    return data;
}

async function runGameFolderScan(files) {
    const statusEl = document.getElementById('game-folder-scan-status');
    const resultsEl = document.getElementById('game-folder-scan-results');
    const proCta = document.getElementById('game-folder-scan-pro-cta');
    if (!statusEl || !resultsEl) return;
    proCta?.classList.add('hidden');
    statusEl.classList.remove('hidden');
    statusEl.textContent = 'Processing folder…';
    resultsEl.classList.add('hidden');
    try {
        const payload = await processGameFolderFiles(files);
        statusEl.textContent = 'AI analyzing…';
        const data = await scanGameFolderWithPayload(payload);
        statusEl.textContent = '';
        statusEl.classList.add('hidden');
        resultsEl.classList.remove('hidden');
        resultsEl.innerHTML = (data.report || data.findings || 'No issues found.').replace(/\n/g, '<br>');
        if (data.plugins_found && elements.modListInput) {
            const asPlugins = data.plugins_found.map(p => (p.startsWith('*') || p.startsWith('+') ? p : '*' + p)).join('\n');
            if (!elements.modListInput.value.trim()) {
                elements.modListInput.value = asPlugins;
                updateModCounter();
            }
        }
    } catch (err) {
        if (err.message && err.message.includes('Pro')) {
            proCta?.classList.remove('hidden');
            statusEl.textContent = '';
        } else {
            statusEl.textContent = err.message || 'Scan failed.';
        }
    }
}

let gameFolderScanInitialized = false;

function initGameFolderScan() {
    const dropZone = document.getElementById('game-folder-drop-zone');
    const browseBtn = document.getElementById('game-folder-browse-btn');
    const fileInput = document.getElementById('game-folder-input');
    const proCta = document.getElementById('game-folder-scan-pro-cta');
    const statusEl = document.getElementById('game-folder-scan-status');
    if (!dropZone || !fileInput) return;

    function updateTierUi() {
        const isPro = hasPaidAccess(currentUserTier);
        dropZone.classList.toggle('game-folder-drop-disabled', !isPro);
        dropZone.setAttribute('aria-disabled', isPro ? 'false' : 'true');
        if (browseBtn) browseBtn.disabled = !isPro;
        if (proCta) proCta.classList.toggle('hidden', isPro);
        if (!isPro && statusEl) {
            statusEl.classList.remove('hidden');
            statusEl.textContent = 'Pro required for folder scan. Upgrade to enable this button.';
        } else if (isPro && statusEl && statusEl.textContent.includes('Pro required')) {
            statusEl.textContent = '';
            statusEl.classList.add('hidden');
        }
    }

    const handleFiles = async (fileList) => {
        if (!hasPaidAccess(currentUserTier)) {
            proCta?.classList.remove('hidden');
            return;
        }
        if (!fileList || fileList.length === 0) return;
        const files = [];
        const arr = Array.isArray(fileList) ? fileList : Array.from(fileList);
        for (let i = 0; i < arr.length; i++) {
            const f = arr[i];
            if (f instanceof File) {
                files.push({ path: f.webkitRelativePath || f.name || `file_${i}`, file: f });
            } else if (f && typeof f.getFile === 'function') {
                try {
                    const file = await f.getFile();
                    files.push({ path: f.name || file?.name || `file_${i}`, file: file || f });
                } catch (_) { /* skip */ }
            }
        }
        if (files.length === 0) return;
        await runGameFolderScan(files);
    };

    async function openFolderPicker() {
        if (!hasPaidAccess(currentUserTier)) {
            proCta?.classList.remove('hidden');
            return;
        }
        // Prefer native directory picker when available; fallback to webkitdirectory input.
        if (window.showDirectoryPicker) {
            try {
                const handle = await window.showDirectoryPicker({ mode: 'read' });
                const files = await collectFilesFromDirectoryHandle(handle);
                await runGameFolderScan(files.map(f => ({ path: f.path, file: f.file })));
                return;
            } catch (_) {
                // User canceled or browser denied; fallback to file input.
            }
        }
        fileInput.click();
    }

    if (!gameFolderScanInitialized) {
        dropZone.addEventListener('click', openFolderPicker);
        if (browseBtn) browseBtn.addEventListener('click', (e) => { e.stopPropagation(); openFolderPicker(); });
        dropZone.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openFolderPicker(); } });
        dropZone.addEventListener('dragover', (e) => { e.preventDefault(); e.stopPropagation(); dropZone.classList.add('game-folder-drop-active'); });
        dropZone.addEventListener('dragleave', () => dropZone.classList.remove('game-folder-drop-active'));
        dropZone.addEventListener('drop', async (e) => {
            if (!hasPaidAccess(currentUserTier)) {
                proCta?.classList.remove('hidden');
                return;
            }
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove('game-folder-drop-active');
            const items = e.dataTransfer?.items;
            if (items && items.length > 0) {
                const item = items[0];
                if (item.getAsFileSystemHandle) {
                    try {
                        const handle = await item.getAsFileSystemHandle();
                        if (handle?.kind === 'directory') {
                            const files = await collectFilesFromDirectoryHandle(handle);
                            await runGameFolderScan(files.map(f => ({ path: f.path, file: f.file })));
                            return;
                        }
                    } catch (_) {}
                }
                const files = [];
                for (let i = 0; i < items.length; i++) {
                    const f = items[i].getAsFile?.();
                    if (f) files.push(f);
                }
                if (files.length > 0) {
                    const withPath = files.map(f => ({ path: f.webkitRelativePath || f.name, file: f }));
                    if (!withPath.some(f => (f.path || '').includes('/'))) {
                        statusEl?.classList.remove('hidden');
                        if (statusEl) statusEl.textContent = 'Your browser selected files, not a folder tree. Choose the top-level folder or use drag/drop.';
                    }
                    await runGameFolderScan(withPath);
                } else {
                    alert('Drop a folder (not individual files). Or use "click to browse" to select the folder.');
                }
            }
        });
        fileInput.addEventListener('change', async (e) => {
            const fileList = e.target.files;
            if (fileList?.length) await handleFiles(Array.from(fileList));
            fileInput.value = '';
        });
        gameFolderScanInitialized = true;
    }

    updateTierUi();
}
if (elements.sampleBtn) {
    elements.sampleBtn.addEventListener('click', loadSampleList);
}
const saveListBtn = document.getElementById('save-list-btn');
const loadSavedSelect = document.getElementById('load-saved-list');
const SAVED_LISTS_KEY = 'modcheck_saved_lists';
function getSavedLists() {
    try {
        const raw = localStorage.getItem(SAVED_LISTS_KEY);
        return raw ? JSON.parse(raw) : {};
    } catch (_) { return {}; }
}
function saveListToStorage() {
    if (!hasPaidAccess(currentUserTier)) {
        window.location.href = '/signup-pro';
        return;
    }
    const list = elements.modListInput?.value?.trim();
    if (!list) { alert('No mod list to save.'); return; }
    const name = prompt('Name this list (e.g. "Skyrim 2024 build"):');
    if (!name || !name.trim()) return;
    const saved = getSavedLists();
    saved[name.trim()] = { list, game: elements.gameSelect?.value || 'skyrimse', savedAt: new Date().toISOString() };
    try {
        localStorage.setItem(SAVED_LISTS_KEY, JSON.stringify(saved));
        populateLoadSavedSelect();
        alert('Saved.');
    } catch (e) { alert('Could not save.'); }
}
function populateLoadSavedSelect() {
    if (!loadSavedSelect) return;
    const saved = getSavedLists();
    const keys = Object.keys(saved).sort();
    loadSavedSelect.innerHTML = '<option value="">Load saved…</option>';
    keys.forEach(k => {
        const opt = document.createElement('option');
        opt.value = k;
        opt.textContent = k;
        loadSavedSelect.appendChild(opt);
    });
}
function loadSavedList() {
    const key = loadSavedSelect?.value;
    if (!key) return;
    const saved = getSavedLists();
    const item = saved[key];
    if (!item || !item.list) { alert('List not found.'); return; }
    if (elements.modListInput) {
        elements.modListInput.value = item.list;
        updateModCounter();
    }
    if (item.game && elements.gameSelect) elements.gameSelect.value = item.game;
    loadSavedSelect.value = '';
}
if (saveListBtn) saveListBtn.addEventListener('click', saveListToStorage);
if (loadSavedSelect) {
    loadSavedSelect.addEventListener('change', loadSavedList);
    populateLoadSavedSelect();
}
const importFileBtn = document.getElementById('import-file-btn');
const importFileInput = document.getElementById('import-file-input');
if (importFileBtn && importFileInput) {
    importFileBtn.addEventListener('click', () => importFileInput.click());
    importFileInput.addEventListener('change', async (e) => {
        const file = e.target.files?.[0];
        if (!file || !elements.modListInput) return;
        try {
            const text = await file.text();
            elements.modListInput.value = text;
            updateModCounter();
        } catch (err) {
            alert('Could not read file. Try a .txt file.');
        }
        importFileInput.value = '';
    });
}
if (elements.downloadReportBtn) {
    elements.downloadReportBtn.addEventListener('click', downloadReport);
}
if (elements.downloadReportJsonBtn) {
    elements.downloadReportJsonBtn.addEventListener('click', downloadReportJson);
}
const downloadFixGuideBtn = document.getElementById('download-fix-guide-btn');
const printFixGuideBtn = document.getElementById('print-fix-guide-btn');
if (downloadFixGuideBtn) downloadFixGuideBtn.addEventListener('click', downloadFixGuideHTML);
if (printFixGuideBtn) printFixGuideBtn.addEventListener('click', printFixGuide);
const fixGuidePreviewScroll = document.getElementById('fix-guide-preview-scroll');
if (fixGuidePreviewScroll) fixGuidePreviewScroll.addEventListener('click', scrollToFixGuide);
if (elements.copyLoadOrderBtn) {
    elements.copyLoadOrderBtn.addEventListener('click', copyLoadOrderAsPluginsTxt);
}
if (elements.applyLoadOrderBtn) {
    elements.applyLoadOrderBtn.addEventListener('click', applyLoadOrder);
}

if (elements.chatForm) {
    elements.chatForm.addEventListener('submit', sendChatMessage);
}

[elements.filterErrors, elements.filterWarnings, elements.filterInfo].forEach(el => {
    if (el) el.addEventListener('change', applyConflictFilters);
});

const resultsSearchInput = document.getElementById('results-search-input');
if (resultsSearchInput) {
    resultsSearchInput.addEventListener('input', applyConflictFilters);
    resultsSearchInput.addEventListener('keyup', applyConflictFilters);
}
const resultsSearchClear = document.getElementById('results-search-clear');
if (resultsSearchClear) {
    resultsSearchClear.addEventListener('click', () => {
        if (resultsSearchInput) {
            resultsSearchInput.value = '';
            resultsSearchInput.focus();
            applyConflictFilters();
            resultsSearchClear.classList.add('hidden');
        }
    });
}

if (elements.modListInput) {
    elements.modListInput.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'Enter') {
            e.preventDefault();
            analyzeModList();
        }
    });
}

// -------------------------------------------------------------------
// Main tabs (Analyze | Quick Start | Community)
// -------------------------------------------------------------------
function initMainTabs() {
    const tabs = document.querySelectorAll('.main-tab');
    const panels = document.querySelectorAll('.tab-panel');
    const marketingSections = document.getElementById('marketing-sections');
    const proBtn = document.getElementById('pro-upgrade-btn');
    function updateForTab(target) {
        const isCommunity = target === 'community';
        const isDev = target === 'dev';
        const isPro = (typeof window.__USER_TIER__ !== 'undefined' && hasPaidAccess(window.__USER_TIER__));
        if (marketingSections) marketingSections.classList.toggle('hidden', isCommunity || isDev || isPro);
        if (proBtn) proBtn.classList.toggle('hidden', isCommunity);
    }
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const target = tab.dataset.tab;
            tabs.forEach(t => { t.classList.remove('active'); t.setAttribute('aria-selected', 'false'); });
            panels.forEach(p => {
                const match = p.id === 'panel-' + target;
                p.classList.toggle('active', match);
                p.setAttribute('aria-hidden', !match);
            });
            tab.classList.add('active');
            tab.setAttribute('aria-selected', 'true');
            updateForTab(target);
            if (target === 'community') loadCommunityFeed();
            if (target === 'build-list') initBuildListIfNeeded();
            if (target === 'quickstart') loadQuickstartContent();
            if (target === 'dev') initDevTools();
        });
    });
    updateForTab('analyze');
    document.querySelectorAll('.tab-switch').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const target = btn.dataset.tab;
            const tab = document.querySelector('.main-tab[data-tab="' + target + '"]');
            if (tab) tab.click();
        });
    });
}

// -------------------------------------------------------------------
// Dev Tools (Pro) — AI code analysis, repo/upload/paste
// -------------------------------------------------------------------
let devUploadedFiles = [];
const DEV_SAMPLE_REPORT = `## Runtime compatibility assessment

**Verdict:** Likely to run with minor fixes.

### Dependencies
- **SKSE** — Required. Ensure Address Library is installed for your game version (1.6.640+).
- **PapyrusUtil** — Detected in scripts. Add to requirements in FOMOD or README.

### Papyrus notes
- No obvious race conditions in Event handlers.
- Consider null checks on \`Game.GetPlayer()\` before use in long-running logic.
- \`RegisterForSingleUpdate\` usage looks correct for cleanup.

### Config / structure
- \`meta.ini\` or FOMOD manifest not found — add for proper mod manager support.
- Version compatibility: Scripts target Skyrim SE. No 1.5.97-specific APIs detected.

### Recommendations
1. Add \`meta.ini\` or FOMOD for MO2/Vortex.
2. Document SKSE + Address Library in requirements.
3. Test on a clean save before release.
`;

function initDevTools() {
    if (window.__DEV_TOOLS_INIT__) return;
    window.__DEV_TOOLS_INIT__ = true;

    const analyzeBtn = document.getElementById('dev-analyze-btn');
    const sampleBtn = document.getElementById('dev-sample-btn');
    const dropZone = document.getElementById('dev-drop-zone');
    const fileInput = document.getElementById('dev-file-input');
    const copyBtn = document.getElementById('dev-copy-report-btn');
    const downloadBtn = document.getElementById('dev-download-report-btn');
    const loopSuggestBtn = document.getElementById('dev-loop-suggest-btn');
    const proCta = document.getElementById('dev-pro-cta');

    if (analyzeBtn) analyzeBtn.addEventListener('click', runDevAnalyze);
    if (sampleBtn) sampleBtn.addEventListener('click', showDevSampleReport);
    if (copyBtn) copyBtn.addEventListener('click', copyDevReport);
    if (downloadBtn) downloadBtn.addEventListener('click', downloadDevReport);
    if (loopSuggestBtn) loopSuggestBtn.addEventListener('click', runDevLoopSuggest);

    document.querySelectorAll('.dev-input-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const mode = tab.dataset.mode;
            document.querySelectorAll('.dev-input-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.dev-mode-panel').forEach(p => p.classList.remove('active'));
            tab.classList.add('active');
            const panel = document.getElementById('dev-mode-' + mode);
            if (panel) panel.classList.add('active');
        });
    });

    if (dropZone) {
        dropZone.addEventListener('click', () => fileInput?.click());
        dropZone.addEventListener('dragover', (e) => { e.preventDefault(); e.stopPropagation(); dropZone.classList.add('dev-drop-active'); });
        dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dev-drop-active'));
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dev-drop-active');
            if (e.dataTransfer?.files?.length) handleDevFiles(e.dataTransfer.files);
        });
    }
    if (fileInput) fileInput.addEventListener('change', (e) => { if (e.target.files?.length) handleDevFiles(e.target.files); });

    document.getElementById('panel-dev')?.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            runDevAnalyze();
        }
    });
}

async function runDevLoopSuggest() {
    const isPro = hasPaidAccess(currentUserTier);
    if (!isPro) {
        showDevProCta();
        return;
    }
    const outEl = document.getElementById('dev-loop-output');
    const btn = document.getElementById('dev-loop-suggest-btn');
    const game = (document.getElementById('dev-game-select')?.value || 'skyrimse');
    const objective = (document.getElementById('dev-loop-objective')?.value || '').trim();
    const playstyle = (document.getElementById('dev-loop-playstyle')?.value || '').trim();
    const fpsAvg = Number(document.getElementById('dev-loop-fps')?.value || 0) || 0;
    const crashes = Number(document.getElementById('dev-loop-crashes')?.value || 0) || 0;
    const stutter = Number(document.getElementById('dev-loop-stutter')?.value || 0) || 0;
    const enjoyment = Number(document.getElementById('dev-loop-enjoyment')?.value || 0) || 0;
    if (!outEl) return;
    outEl.classList.remove('hidden');
    outEl.textContent = 'Samson is building your next loop...';
    if (btn) btn.disabled = true;
    try {
        const res = await fetch('/api/dev-loop/suggest', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                game,
                objective,
                playstyle,
                signals: {
                    fps_avg: fpsAvg || undefined,
                    crashes,
                    stutter_events: stutter,
                    enjoyment_score: enjoyment || undefined,
                }
            })
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data.error || 'Could not build dev loop suggestions.');
        const features = (data.feature_ideas || []).map((x, i) => `${i + 1}. ${x}`).join('\n');
        const perf = (data.optimization_actions || []).map((x, i) => `${i + 1}. ${x}`).join('\n');
        const idle = data.idle_conclusion || 'No idle conclusion available.';
        const safety = data.safety?.policy || '';
        outEl.textContent = [
            `Samson Companion Loop — ${data.game || game}`,
            '',
            'Feature ideas:',
            features || '- None',
            '',
            'Optimization actions:',
            perf || '- None',
            '',
            `Idle decision: ${idle}`,
            '',
            `Safety: ${safety}`,
        ].join('\n');
        trackClientActivity('dev_loop_suggest', { game, idle_recommended: !!data.idle_recommended });
    } catch (e) {
        outEl.textContent = e.message || 'Could not build loop suggestions.';
    } finally {
        if (btn) btn.disabled = false;
    }
}

function showDevSampleReport() {
    const resultsEl = document.getElementById('dev-results');
    const reportEl = document.getElementById('dev-report-content');
    const proCta = document.getElementById('dev-pro-cta');
    const isPro = hasPaidAccess(currentUserTier);
    if (!resultsEl || !reportEl) return;
    reportEl.innerHTML = (typeof marked !== 'undefined' ? marked.parse(DEV_SAMPLE_REPORT) : escapeHtml(DEV_SAMPLE_REPORT).replace(/\n/g, '<br>'));
    resultsEl.classList.remove('hidden');
    if (proCta && !isPro) proCta.classList.remove('hidden');
}

function copyDevReport() {
    const reportEl = document.getElementById('dev-report-content');
    if (!reportEl?.textContent) return;
    navigator.clipboard.writeText(reportEl.textContent).then(() => {
        const btn = document.getElementById('dev-copy-report-btn');
        if (btn) { btn.textContent = 'Copied!'; setTimeout(() => { btn.textContent = 'Copy'; }, 1500); }
    }).catch(() => alert('Could not copy.'));
}

function downloadDevReport() {
    const reportEl = document.getElementById('dev-report-content');
    if (!reportEl?.textContent) return;
    const blob = new Blob([reportEl.textContent], { type: 'text/markdown' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'dev-report-' + new Date().toISOString().slice(0, 10) + '.md';
    a.click();
    URL.revokeObjectURL(a.href);
}

function renderDevFileList() {
    const el = document.getElementById('dev-file-list');
    if (!el) return;
    if (devUploadedFiles.length === 0) {
        el.classList.add('hidden');
        el.innerHTML = '';
        return;
    }
    el.classList.remove('hidden');
    el.innerHTML = devUploadedFiles.map((f, i) =>
        `<span class="dev-file-chip" data-index="${i}">${escapeHtml(f.path)} <button type="button" class="dev-file-remove" aria-label="Remove">×</button></span>`
    ).join('');
    el.querySelectorAll('.dev-file-remove').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const i = parseInt(btn.closest('.dev-file-chip')?.dataset.index, 10);
            if (!isNaN(i)) { devUploadedFiles.splice(i, 1); renderDevFileList(); }
        });
    });
}

async function handleDevFiles(fileList) {
    const ext = ['.psc', '.esp', '.esm', '.esl', '.ini', '.json', '.txt', '.md', '.toml', '.yaml', '.yml'];
    const added = [];
    for (let i = 0; i < Math.min(fileList.length, 25); i++) {
        const f = fileList[i];
        const name = (f.name || '').toLowerCase();
        if (!ext.some(e => name.endsWith(e)) && !name.includes('readme') && !name.includes('license')) continue;
        try {
            const text = await f.text();
            added.push({ path: f.webkitRelativePath || f.name, content: text.slice(0, 15000) });
        } catch (_) {}
    }
    devUploadedFiles = [...devUploadedFiles, ...added].slice(0, 25);
    renderDevFileList();
}

async function runDevAnalyze() {
    const isPro = hasPaidAccess(currentUserTier);
    if (!isPro) {
        showDevProCta();
        return;
    }

    const repoInput = document.getElementById('dev-repo-url');
    const pasteInput = document.getElementById('dev-paste-input');
    const activeTab = document.querySelector('.dev-input-tab.active');
    const mode = activeTab?.dataset.mode || 'repo';

    const repoUrl = (repoInput?.value || '').trim();
    const pasteContent = (pasteInput?.value || '').trim();
    const game = (document.getElementById('dev-game-select')?.value || 'skyrimse');
    const hasRepo = repoUrl && repoUrl.includes('github.com');
    const hasFiles = devUploadedFiles.length > 0;
    const hasPaste = pasteContent.length > 20;

    const statusEl = document.getElementById('dev-status');
    const resultsEl = document.getElementById('dev-results');
    const reportEl = document.getElementById('dev-report-content');
    const analyzeBtn = document.getElementById('dev-analyze-btn');
    const proCta = document.getElementById('dev-pro-cta');
    if (!statusEl || !resultsEl || !reportEl) return;

    if (!hasRepo && !hasFiles && !hasPaste) {
        statusEl.textContent = 'Add a repo URL, upload files, or paste code.';
        statusEl.classList.remove('hidden');
        return;
    }

    statusEl.textContent = mode === 'repo' && hasRepo ? 'Fetching repo…' : 'Analyzing…';
    statusEl.classList.remove('hidden');
    resultsEl.classList.add('hidden');
    if (proCta) proCta.classList.add('hidden');
    if (analyzeBtn) analyzeBtn.disabled = true;

    let payload = { game };
    if (hasRepo) {
        payload.repo_url = repoUrl;
    } else if (hasFiles) {
        payload.files = devUploadedFiles;
    } else {
        payload.files = [{ path: 'pasted.txt', content: pasteContent }];
    }

    try {
        const res = await fetch('/api/dev-analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data.error || `Analysis failed (${res.status})`);
        const report = data.report || 'No report generated.';
        reportEl.innerHTML = (typeof marked !== 'undefined' ? marked.parse(report) : escapeHtml(report).replace(/\n/g, '<br>'));
        resultsEl.classList.remove('hidden');
        statusEl.textContent = data.files_analyzed ? `Analyzed ${data.files_analyzed} file(s).` : 'Done.';
    } catch (err) {
        statusEl.textContent = err.message || 'Analysis failed.';
        if (err.message && err.message.includes('Pro')) {
            showDevProCta();
        }
    } finally {
        if (analyzeBtn) analyzeBtn.disabled = false;
    }
}

function showDevProCta() {
    const proCta = document.getElementById('dev-pro-cta');
    const resultsEl = document.getElementById('dev-results');
    const reportEl = document.getElementById('dev-report-content');
    if (proCta) {
        proCta.classList.remove('hidden');
        proCta.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    if (resultsEl && reportEl && !reportEl.textContent.trim()) {
        reportEl.innerHTML = '<p class="dev-cta-placeholder">Pro unlocks AI dev reports. Paste a repo, upload files, or <a href="#" onclick="document.getElementById(\'dev-sample-btn\')?.click(); return false;">view a sample</a>.</p>';
        resultsEl.classList.remove('hidden');
    }
}

// -------------------------------------------------------------------
// Quick Start — dynamic content from /api/quickstart
// -------------------------------------------------------------------
async function loadQuickstartContent() {
    const gameSelect = document.getElementById('quickstart-game');
    const game = (gameSelect && gameSelect.value) ? gameSelect.value : 'skyrimse';
    const firstStepsEl = document.getElementById('quickstart-first-steps-content');
    const modManagersEl = document.getElementById('quickstart-mod-managers');
    const toolsEl = document.getElementById('quickstart-tools');
    const learningEl = document.getElementById('quickstart-learning');
    const firstStepsWrap = document.getElementById('quickstart-first-steps');
    if (!firstStepsEl || !modManagersEl || !toolsEl || !learningEl) return;

    const quickLink = (url, label) => `<a href="${escapeHtml(url || '#')}" target="_blank" rel="noopener" class="quickstart-preview-link">${escapeHtml(label || '')}</a>`;
    try {
        const res = await fetch(`/api/quickstart?game=${encodeURIComponent(game)}`);
        const data = await res.json().catch(() => ({}));
        const g = data.game || {};
        const tools = data.tools || {};
        const modManagers = data.mod_managers || {};
        const learning = data.learning_resources || [];
        const internalLinks = Array.isArray(data.internal_links) ? data.internal_links : [];
        const noobJourney = Array.isArray(data.noob_journey) ? data.noob_journey : [];

        let scriptExtHtml = '';
        if (g.script_ext) {
            scriptExtHtml = `Install ${quickLink(g.script_ext.url, g.script_ext.name)} (${g.name}) if your mods need it. `;
        }
        let patchHtml = '';
        if (g.unofficial_patch) {
            patchHtml = `Install the Unofficial Patch — ${quickLink(g.unofficial_patch.url, g.unofficial_patch.name)}. `;
        }
        const mo2Url = g.mo2_url || (modManagers.mo2 && modManagers.mo2.url);
        const vortexUrl = (modManagers.vortex && modManagers.vortex.url) || '#';
        const mo2Name = (modManagers.mo2 && modManagers.mo2.name) || 'Mod Organizer 2 (MO2)';
        const vortexName = (modManagers.vortex && modManagers.vortex.name) || 'Vortex';
        const osPaths = g.os_plugin_paths || {};
        const windowsPath = osPaths.windows || (g.appdata_path ? `${g.appdata_path}plugins.txt` : '%LOCALAPPDATA%\\...\\plugins.txt');
        const linuxPath = osPaths.linux || 'Use your Proton prefix AppData path and locate plugins.txt';
        const macPath = osPaths.mac || 'Use your VM/CrossOver AppData path and locate plugins.txt';
        firstStepsEl.innerHTML = `<ol>
            <li>Install a mod manager — ${quickLink(mo2Url || '#', mo2Name)} or ${quickLink(vortexUrl, vortexName)}</li>
            <li>${scriptExtHtml || 'Install script extender (SKSE, F4SE, etc.) if your mods need it.'}</li>
            <li>${patchHtml || 'Install the Unofficial Patch for your game.'}</li>
            <li>Add mods one at a time—test as you go</li>
            <li>Run SkyModderAI before you launch the game</li>
        </ol>`;

        if (firstStepsWrap && noobJourney.length > 0) {
            const journeyHtml = noobJourney.map((stepObj) => `<li>${escapeHtml(stepObj.step || '')}</li>`).join('');
            firstStepsEl.innerHTML += `<h4>Most beginner-friendly path</h4><ol>${journeyHtml}</ol>`;
        }

        modManagersEl.innerHTML = `
            <div class="quickstart-card">
                <h4>${quickLink(mo2Url || '#', mo2Name)}</h4>
                <ol>
                    <li>Open ${quickLink(mo2Url || '#', 'Mod Organizer 2')}</li>
                    <li>Look at the right-hand panel—that's your load order (plugins)</li>
                    <li>Right-click the list → <strong>Copy load order to clipboard</strong></li>
                    <li>Paste into ${quickLink('/', 'SkyModderAI Analyze')}</li>
                </ol>
                <p class="hint">Or: Click the puzzle-piece icon (Plugins) and copy from there.</p>
            </div>
            <div class="quickstart-card">
                <h4>${quickLink(vortexUrl, vortexName)}</h4>
                <ol>
                    <li>Open ${quickLink(vortexUrl, 'Vortex')}</li>
                    <li>Go to <strong>Plugins</strong> (or the game's plugin tab)</li>
                    <li>Click the three dots (⋮) → <strong>Export load order</strong></li>
                    <li>Open the exported file, copy its contents, paste into ${quickLink('/', 'SkyModderAI')}</li>
                </ol>
                <p class="hint">Vortex saves to a text file—copy everything in it.</p>
            </div>
            <div class="quickstart-card">
                <h4>No mod manager (plugins.txt)</h4>
                <ol>
                    <li><strong>Windows:</strong> <code>${escapeHtml(windowsPath)}</code></li>
                    <li><strong>Linux/Steam Deck:</strong> <code>${escapeHtml(linuxPath)}</code></li>
                    <li><strong>macOS:</strong> ${escapeHtml(macPath)}</li>
                    <li>Open <code>plugins.txt</code></li>
                    <li>Copy the whole file and paste into SkyModderAI</li>
                </ol>
                <p class="hint"><code>*</code> = enabled, no <code>*</code> = disabled. SkyModderAI understands both.</p>
            </div>`;

        toolsEl.innerHTML = Object.values(tools).map(t => 
            `<li>${quickLink(t.url || '#', t.name || '')} — ${escapeHtml(t.desc || '')}</li>`
        ).join('');

        learningEl.innerHTML = (Array.isArray(learning) ? learning : []).map(r =>
            `<li>${quickLink(r.url || '#', r.name || '')} — ${escapeHtml(r.desc || '')}</li>`
        ).join('');

        const internalHostEl = document.getElementById('quickstart-live-desc');
        if (internalHostEl && internalLinks.length > 0) {
            internalHostEl.innerHTML = `Internal links: ${internalLinks.map((lnk) => quickLink(lnk.url, lnk.name)).join(' · ')}`;
        }
    } catch (e) {
        firstStepsEl.innerHTML = '<p class="hint">Could not load quick start. Try again.</p>';
    }
}

function initQuickstartLivePreview() {
    const panel = document.getElementById('panel-quickstart');
    const titleEl = document.getElementById('quickstart-live-title');
    const descEl = document.getElementById('quickstart-live-desc');
    const contentEl = document.getElementById('quickstart-live-content');
    const frameWrapEl = document.getElementById('quickstart-live-frame-wrap');
    const frameEl = document.getElementById('quickstart-live-frame');
    const openEl = document.getElementById('quickstart-live-open');
    if (!panel || !titleEl || !descEl || !contentEl || !frameWrapEl || !frameEl || !openEl) return;

    let lastUrl = '';
    let pendingTimer = null;

    function normalizeUrl(anchor) {
        const href = anchor.getAttribute('href') || '';
        if (!href || href.startsWith('#') || href.startsWith('mailto:') || href.startsWith('tel:')) return '';
        if (href.startsWith('http://') || href.startsWith('https://')) return href;
        if (href.startsWith('/')) return href;
        return '';
    }

    function isInternalUrl(url) {
        if (!url) return false;
        if (url.startsWith('/')) return true;
        try {
            const parsed = new URL(url, window.location.origin);
            return parsed.origin === window.location.origin;
        } catch (_) {
            return false;
        }
    }

    function showTextPreview() {
        frameWrapEl.classList.add('hidden');
        contentEl.classList.remove('hidden');
    }

    function showFramePreview(url) {
        contentEl.classList.add('hidden');
        frameWrapEl.classList.remove('hidden');
        if (frameEl.getAttribute('src') !== url) {
            frameEl.setAttribute('src', url);
        }
    }

    function load(url) {
        if (!url || url === lastUrl) return;
        lastUrl = url;
        titleEl.textContent = 'Loading preview…';
        openEl.href = url;
        if (isInternalUrl(url)) {
            descEl.textContent = 'Internal page preview (live and scrollable).';
            titleEl.textContent = 'Live internal preview';
            showFramePreview(url);
            return;
        }
        showTextPreview();
        contentEl.textContent = 'Fetching page content...';
        fetch(`/api/link-reader?url=${encodeURIComponent(url)}`)
            .then((r) => r.ok ? r.json() : null)
            .then((data) => {
                if (!data || url !== lastUrl) return;
                titleEl.textContent = data.title || 'Untitled';
                if (data.description) descEl.textContent = data.description;
                contentEl.textContent = data.content || 'No readable content found.';
                openEl.href = data.url || url;
            })
            .catch(() => {
                if (url !== lastUrl) return;
                titleEl.textContent = 'Preview unavailable';
                contentEl.textContent = 'Could not load this page preview.';
            });
    }

    panel.addEventListener('mouseover', (e) => {
        const link = e.target.closest('a[href]');
        if (!link) return;
        const url = normalizeUrl(link);
        if (!url) return;
        if (pendingTimer) clearTimeout(pendingTimer);
        pendingTimer = setTimeout(() => load(url), 180);
    });
    panel.addEventListener('focusin', (e) => {
        const link = e.target.closest('a[href]');
        if (!link) return;
        const url = normalizeUrl(link);
        if (url) load(url);
    });
    panel.addEventListener('click', (e) => {
        const link = e.target.closest('a[href]');
        if (!link) return;
        const url = normalizeUrl(link);
        if (!url) return;
        if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button === 1) {
            return;
        }
        // Obsidian-like behavior: click previews in place; open explicitly via "Open link".
        e.preventDefault();
        load(url);
    });
}

function initQuickstartGameSelect() {
    const gameSelect = document.getElementById('quickstart-game');
    const analyzeGameSelect = document.getElementById('game-select');
    if (gameSelect && analyzeGameSelect) {
        gameSelect.value = analyzeGameSelect.value || 'skyrimse';
        gameSelect.addEventListener('change', () => { loadQuickstartContent(); });
        analyzeGameSelect.addEventListener('change', () => { gameSelect.value = analyzeGameSelect.value; });
    }
}

// -------------------------------------------------------------------
// Build a List — preference-based mod list generation
// -------------------------------------------------------------------
let buildListOptionsLoaded = false;
let lastBuiltListMods = [];

function initBuildListIfNeeded() {
    if (buildListOptionsLoaded) return;
    buildListOptionsLoaded = true;
    const gameSelect = document.getElementById('build-list-game');
    loadBuildListOptions(gameSelect?.value || 'skyrimse');
    const btn = document.getElementById('build-list-btn');
    if (btn) btn.addEventListener('click', runBuildList);
    const copyBtn = document.getElementById('build-list-copy-btn');
    if (copyBtn) copyBtn.addEventListener('click', copyBuildListAsPluginsTxt);
    const toAnalyzeBtn = document.getElementById('build-list-to-analyze-btn');
    if (toAnalyzeBtn) {
        toAnalyzeBtn.addEventListener('click', () => sendBuildListToAnalyze({ autoAnalyze: true, focusAnalyze: true }));
    }
    const proCheck = document.getElementById('build-list-pro-setups');
    const proWrap = document.getElementById('build-list-pro-check-wrap');
    if (proWrap && !hasPaidAccess(currentUserTier)) {
        proWrap.style.opacity = '0.6';
        if (proCheck) proCheck.disabled = true;
    }
    if (gameSelect) {
        gameSelect.addEventListener('change', () => {
            loadBuildListOptions(gameSelect.value || 'skyrimse');
        });
    }
}

async function loadBuildListOptions(gameId = 'skyrimse') {
    const container = document.getElementById('build-list-preferences');
    if (!container) return;
    try {
        const res = await fetch(`/api/list-preferences/options?game=${encodeURIComponent(gameId)}`);
        const data = await res.json().catch(() => ({ options: [] }));
        const options = data.options || [];
        container.innerHTML = options.map(opt => `
            <div class="build-list-pref-row">
                <label for="build-pref-${escapeHtml(opt.key)}">${escapeHtml(opt.label)}:</label>
                <select id="build-pref-${escapeHtml(opt.key)}" data-pref="${escapeHtml(opt.key)}">
                    ${(opt.choices || []).map(c => `<option value="${escapeHtml(c.value)}">${escapeHtml(c.label)}</option>`).join('')}
                </select>
            </div>
        `).join('');
    } catch (e) {
        container.innerHTML = '<p class="hint">Could not load options.</p>';
    }
}

async function runBuildList() {
    const btn = document.getElementById('build-list-btn');
    const resultsEl = document.getElementById('build-list-results');
    const modsEl = document.getElementById('build-list-mods');
    const setupsEl = document.getElementById('build-list-setups');
    if (!btn || !resultsEl || !modsEl) return;
    btn.disabled = true;
    btn.textContent = 'Generating…';
    resultsEl.classList.add('hidden');
    const gameSelect = document.getElementById('build-list-game');
    const game = (gameSelect && gameSelect.value) ? gameSelect.value : 'skyrimse';
    const preferences = {};
    document.querySelectorAll('[data-pref]').forEach(el => {
        const key = el.dataset.pref;
        if (key && el.value) preferences[key] = el.value;
    });
    const proSetups = document.getElementById('build-list-pro-setups')?.checked && hasPaidAccess(currentUserTier);
    try {
        const specs = getCurrentSpecs();
        const body = { game, preferences, pro_setups: proSetups, limit: 50 };
        if (Object.keys(specs).length > 0) body.specs = specs;
        const res = await fetch('/api/build-list', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            alert(data.error || 'Failed to build list.');
            return;
        }
        const mods = data.mods || [];
        lastBuiltListMods = mods;
        if (Array.isArray(data.ignored_preferences) && data.ignored_preferences.length > 0) {
            showActionFeedback(`Adjusted ${data.ignored_preferences.length} invalid preference value(s) for ${game}.`);
        }
        modsEl.innerHTML = mods.map(m => `
            <div class="build-list-mod-item">
                <a href="${escapeHtml(m.nexus_url || '#')}" target="_blank" rel="noopener noreferrer" class="build-list-mod-link">${escapeHtml(m.name)}</a>
                <span class="build-list-mod-reason">${escapeHtml(m.reason || '')}</span>
            </div>
        `).join('');
        const setups = data.setups || [];
        if (setups.length > 0 && setupsEl) {
            setupsEl.classList.remove('hidden');
            setupsEl.innerHTML = '<h4>Pro: AI setups</h4>' + setups.map(s => `
                <div class="build-list-setup">
                    <h5>${escapeHtml(s.name || 'Setup')}</h5>
                    <p class="build-list-setup-rationale">${escapeHtml(s.rationale || '')}</p>
                    <ul class="build-list-setup-mods">${(s.mods || []).map(m => `
                        <li><a href="${escapeHtml(m.nexus_url || '#')}" target="_blank" rel="noopener noreferrer">${escapeHtml(m.name || m)}</a></li>
                    `).join('')}</ul>
                </div>
            `).join('');
        } else if (setupsEl) {
            setupsEl.classList.add('hidden');
        }
        resultsEl.classList.remove('hidden');
        showActionFeedback('List generated. Sending to Analyze automatically…');
        sendBuildListToAnalyze({ autoAnalyze: true, focusAnalyze: true });
    } catch (e) {
        alert('Network error. Try again.');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Generate List';
    }
}

function copyBuildListAsPluginsTxt() {
    const lines = lastBuiltListMods.map(m => '*' + (m.name || '').replace(/^[\*\+\-]?\s*/, ''));
    const text = lines.join('\n');
    if (!text) { alert('No list to copy.'); return; }
    navigator.clipboard.writeText(text).then(() => alert('Copied to clipboard.')).catch(() => alert('Could not copy.'));
}

function sendBuildListToAnalyze(options = {}) {
    const autoAnalyze = !!options.autoAnalyze;
    const focusAnalyze = options.focusAnalyze !== false;
    const lines = lastBuiltListMods.map(m => '*' + (m.name || '').replace(/^[\*\+\-]?\s*/, ''));
    const text = lines.join('\n');
    if (!text) { alert('No list to send.'); return; }
    if (elements.modListInput) {
        elements.modListInput.value = text;
        updateModCounter();
    }
    const buildGame = document.getElementById('build-list-game');
    if (buildGame && elements.gameSelect && buildGame.value) {
        elements.gameSelect.value = buildGame.value;
    }
    if (focusAnalyze) {
        document.querySelector('.main-tab[data-tab="analyze"]')?.click();
    }
    if (autoAnalyze) {
        setTimeout(() => {
            analyzeModList();
        }, 120);
    }
}

// -------------------------------------------------------------------
// Community feed — robust with tags, replies, votes, Pro badges
// -------------------------------------------------------------------
let communityFilterTag = '';
let communitySearchQuery = '';
let communitySort = 'new';

async function loadCommunityFeed() {
    const feed = document.getElementById('community-feed');
    if (!feed) return;
    feed.innerHTML = '<p class="hint community-loading">Loading...</p>';
    try {
        const params = new URLSearchParams({ limit: 50, sort: communitySort });
        if (communityFilterTag) params.set('tag', communityFilterTag);
        if (communitySearchQuery) params.set('q', communitySearchQuery);
        const res = await fetch(`/api/community/posts?${params}`);
        const data = await res.json().catch(() => ({ posts: [] }));
        const posts = data.posts || [];
        loadCommunityHealth();
        if (posts.length === 0) {
            feed.innerHTML = '<p class="hint">No posts yet. Be the first to share a tip or say hi!</p>';
            return;
        }
        feed.innerHTML = posts.map(p => renderCommunityPost(p)).join('');
        bindCommunityPostHandlers();
    } catch (e) {
        feed.innerHTML = '<p class="hint">Could not load posts. Try again later.</p>';
        loadCommunityHealth();
    }
}

async function loadCommunityHealth() {
    const el = document.getElementById('community-health-text');
    if (!el) return;
    try {
        const res = await fetch('/api/community/health');
        const data = await res.json().catch(() => ({}));
        if (!res.ok || !data.success) {
            el.textContent = 'Community health metrics unavailable right now.';
            return;
        }
        const avg = (data.avg_helpfulness_30d == null) ? 'n/a' : `${data.avg_helpfulness_30d}/5`;
        el.textContent = `Last 7 days: ${data.posts_7d} posts, ${data.replies_7d} replies, ${data.active_users_7d} active users, ${data.complaints_7d} complaints. Helpfulness avg (30d): ${avg}. Open reports: ${data.open_reports}.`;
    } catch (e) {
        el.textContent = 'Could not load community pulse right now.';
    }
}

function renderCommunityPost(p) {
    const proBadge = (p.is_pro ? '<span class="community-pro-badge">Pro</span>' : '');
    const repliesHtml = (p.replies || []).map(r => `
        <div class="community-reply">
            <span class="community-reply-meta">${escapeHtml(r.user)}${r.is_pro ? ' <span class="community-pro-badge community-pro-badge-sm">Pro</span>' : ''} · ${formatDate(r.created_at)}</span>
            <div class="community-reply-content">${escapeHtml(r.content)}</div>
            <button type="button" class="community-report-btn" data-reply="${r.id}">Report</button>
        </div>
    `).join('');
    const voteUp = p.my_vote === 1 ? ' community-vote-active' : '';
    const voteDn = p.my_vote === -1 ? ' community-vote-active' : '';
    return `
        <article class="community-post-item" data-post-id="${p.id}">
            <div class="community-post-header">
                <span class="community-post-tag community-post-tag-${escapeHtml(p.tag || 'general')}">${escapeHtml((p.tag || 'general').charAt(0).toUpperCase() + (p.tag || 'general').slice(1))}</span>
                <div class="community-post-meta">${escapeHtml(p.user)}${proBadge} · ${formatDate(p.created_at)}</div>
            </div>
            <div class="community-post-content">${escapeHtml(p.content)}</div>
            <div class="community-post-actions-row">
                <div class="community-votes">
                    <button type="button" class="community-vote-btn community-vote-up${voteUp}" data-post="${p.id}" aria-label="Helpful">▲</button>
                    <span class="community-vote-count">${p.votes || 0}</span>
                    <button type="button" class="community-vote-btn community-vote-down${voteDn}" data-post="${p.id}" aria-label="Not helpful">▼</button>
                </div>
                <button type="button" class="community-reply-btn secondary-button" data-post="${p.id}">Reply</button>
                <button type="button" class="community-report-btn secondary-button" data-post="${p.id}">Report</button>
            </div>
            <div class="community-replies" id="replies-${p.id}">${repliesHtml}</div>
            <div class="community-reply-form hidden" id="reply-form-${p.id}">
                <textarea class="community-reply-input" placeholder="Write a reply..." rows="2" maxlength="2000"></textarea>
                <button type="button" class="community-reply-submit primary-button" data-post="${p.id}">Post reply</button>
            </div>
        </article>
    `;
}

function bindCommunityPostHandlers() {
    document.querySelectorAll('.community-vote-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const postId = parseInt(btn.dataset.post, 10);
            const isUp = btn.classList.contains('community-vote-up');
            const current = btn.classList.contains('community-vote-active');
            let vote = isUp ? 1 : -1;
            if (current) vote = 0;
            try {
                const res = await fetch(`/api/community/posts/${postId}/vote`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ vote })
                });
                const data = await res.json().catch(() => ({}));
                if (res.ok && data.success) {
                    trackClientActivity('community_vote', { post_id: postId, vote });
                    loadCommunityFeed();
                }
            } catch (_) {}
        });
    });
    document.querySelectorAll('.community-reply-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const postId = btn.dataset.post;
            const form = document.getElementById(`reply-form-${postId}`);
            if (form) form.classList.toggle('hidden');
        });
    });
    document.querySelectorAll('.community-reply-submit').forEach(btn => {
        btn.addEventListener('click', async () => {
            const postId = parseInt(btn.dataset.post, 10);
            const form = document.getElementById(`reply-form-${postId}`);
            const textarea = form?.querySelector('.community-reply-input');
            const content = textarea?.value?.trim() || '';
            if (content.length < 3) { alert('Reply must be at least 3 characters.'); return; }
            btn.disabled = true;
            try {
                const res = await fetch(`/api/community/posts/${postId}/replies`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content })
                });
                const data = await res.json().catch(() => ({}));
                if (res.ok && data.success) {
                    textarea.value = '';
                    form.classList.add('hidden');
                    trackClientActivity('community_reply', { post_id: postId });
                    loadCommunityFeed();
                } else alert(data.error || 'Failed to reply');
            } catch (e) { alert('Network error'); }
            btn.disabled = false;
        });
    });
    document.querySelectorAll('.community-report-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const postId = btn.dataset.post ? parseInt(btn.dataset.post, 10) : null;
            const replyId = btn.dataset.reply ? parseInt(btn.dataset.reply, 10) : null;
            const reason = prompt('Reason for report (spam, abuse, off_topic, illegal, other):', 'other');
            if (!reason) return;
            const details = prompt('Optional details (short):', '') || '';
            btn.disabled = true;
            try {
                const res = await fetch('/api/community/reports', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ post_id: postId, reply_id: replyId, reason: reason.trim().toLowerCase(), details })
                });
                const data = await res.json().catch(() => ({}));
                if (res.ok && data.success) showActionFeedback('Report submitted. Thanks for helping keep this space useful.');
                else alert(data.error || 'Failed to submit report');
            } catch (e) {
                alert('Network error');
            }
            btn.disabled = false;
        });
    });
}

function escapeHtml(s) {
    if (!s) return '';
    const div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
}

function formatDate(iso) {
    if (!iso) return '';
    const d = new Date(iso);
    const now = new Date();
    const diff = (now - d) / 1000;
    if (diff < 60) return 'just now';
    if (diff < 3600) return Math.floor(diff / 60) + 'm ago';
    if (diff < 86400) return Math.floor(diff / 3600) + 'h ago';
    if (diff < 604800) return Math.floor(diff / 86400) + 'd ago';
    return d.toLocaleDateString();
}

function initCommunityPost() {
    const input = document.getElementById('community-post-input');
    const btn = document.getElementById('community-post-btn');
    const countEl = document.getElementById('community-char-count');
    const tagSelect = document.getElementById('community-post-tag');
    if (!input || !btn) return;
    input.addEventListener('input', () => {
        if (countEl) countEl.textContent = input.value.length + ' / 2000';
    });
    btn.addEventListener('click', async () => {
        const content = input.value.trim();
        if (content.length < 3) {
            alert('Post must be at least 3 characters.');
            return;
        }
        btn.disabled = true;
        try {
            const body = { content, tag: (tagSelect && tagSelect.value) || 'general' };
            const res = await fetch('/api/community/posts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            const data = await res.json().catch(() => ({}));
            if (!res.ok) {
                alert(data.error || 'Failed to post');
                return;
            }
            input.value = '';
            if (countEl) countEl.textContent = '0 / 2000';
            trackClientActivity('community_post', { tag: (tagSelect && tagSelect.value) || 'general' });
            loadCommunityFeed();
        } catch (e) {
            alert('Network error. Try again.');
        } finally {
            btn.disabled = false;
        }
    });
    document.querySelectorAll('.community-tag-btn').forEach(b => {
        b.addEventListener('click', () => {
            document.querySelectorAll('.community-tag-btn').forEach(x => x.classList.remove('active'));
            b.classList.add('active');
            communityFilterTag = b.dataset.tag || '';
            loadCommunityFeed();
        });
    });
    document.querySelectorAll('.community-sort-btn').forEach(b => {
        b.addEventListener('click', () => {
            document.querySelectorAll('.community-sort-btn').forEach(x => x.classList.remove('active'));
            b.classList.add('active');
            communitySort = b.dataset.sort || 'new';
            loadCommunityFeed();
        });
    });
    const searchInput = document.getElementById('community-search');
    if (searchInput) {
        let searchT = null;
        searchInput.addEventListener('input', () => {
            clearTimeout(searchT);
            searchT = setTimeout(() => {
                communitySearchQuery = searchInput.value.trim();
                loadCommunityFeed();
            }, 300);
        });
    }
}

// -------------------------------------------------------------------
// Command palette (Cmd+K / Ctrl+K) — Vercel/Linear style
// -------------------------------------------------------------------
const COMMAND_ACTIONS = [
    { id: 'analyze', label: 'Analyze mod list', shortcut: 'Ctrl+Enter', fn: () => analyzeModList() },
    { id: 'focus-mod-list', label: 'Focus mod list', fn: () => elements.modListInput?.focus() },
    { id: 'focus-mod-search', label: 'Search mods', fn: () => document.getElementById('mod-search-input')?.focus() },
    { id: 'tab-analyze', label: 'Go to Analyze', fn: () => document.querySelector('.main-tab[data-tab="analyze"]')?.click() },
    { id: 'tab-quickstart', label: 'Go to Quick Start', fn: () => document.querySelector('.main-tab[data-tab="quickstart"]')?.click() },
    { id: 'tab-build-list', label: 'Go to Build a List', fn: () => document.querySelector('.main-tab[data-tab="build-list"]')?.click() },
    { id: 'tab-dev', label: 'Go to Dev Tools', fn: () => document.querySelector('.main-tab[data-tab="dev"]')?.click() },
    { id: 'dev-analyze', label: 'Analyze dev project', shortcut: 'Ctrl+Enter', fn: () => { document.querySelector('.main-tab[data-tab="dev"]')?.click(); setTimeout(() => runDevAnalyze(), 100); } },
    { id: 'tab-community', label: 'Go to Community', fn: () => document.querySelector('.main-tab[data-tab="community"]')?.click() },
    { id: 'copy-report', label: 'Copy report', fn: () => copyReport() },
    { id: 'share-link', label: 'Copy share link', fn: () => copyShareLink() },
    { id: 'clear', label: 'Clear mod list', fn: () => elements.clearBtn?.click() },
    { id: 'sample', label: 'Load sample list', fn: () => loadSampleList() },
    { id: 'profile', label: 'Open profile', fn: () => window.location.href = '/profile' },
    { id: 'signup', label: 'Open signup', fn: () => window.location.href = '/signup-pro' },
    { id: 'pricing', label: 'Go to pricing section', fn: () => { window.location.hash = 'pricing'; } },
];

function openCommandPalette() {
    const palette = document.getElementById('command-palette');
    const input = document.getElementById('command-palette-input');
    if (!palette || !input) return;
    palette.classList.remove('hidden');
    palette.setAttribute('aria-hidden', 'false');
    input.value = '';
    input.focus();
    runCommandPaletteSearch('');
}

function closeCommandPalette() {
    const palette = document.getElementById('command-palette');
    if (palette) {
        palette.classList.add('hidden');
        palette.setAttribute('aria-hidden', 'true');
    }
}

function runCommandPaletteSearch(q) {
    const resultsEl = document.getElementById('command-palette-results');
    if (!resultsEl) return;
    const ql = (q || '').toLowerCase().trim();
    const filtered = ql
        ? COMMAND_ACTIONS.filter(a => a.label.toLowerCase().includes(ql))
        : COMMAND_ACTIONS;
    resultsEl.innerHTML = filtered.slice(0, 8).map((a, i) => `
        <button type="button" class="command-palette-item${i === 0 ? ' highlighted' : ''}" data-index="${i}" data-action="${escapeHtml(a.id)}">
            <span class="command-palette-item-label">${escapeHtml(a.label)}</span>
            ${a.shortcut ? `<span class="command-palette-shortcut">${escapeHtml(a.shortcut)}</span>` : ''}
        </button>
    `).join('');
    resultsEl.querySelectorAll('.command-palette-item').forEach((btn, i) => {
        btn.addEventListener('click', () => {
            const a = COMMAND_ACTIONS.find(x => x.id === btn.dataset.action);
            if (a && a.fn) { closeCommandPalette(); a.fn(); }
        });
    });
}

// -------------------------------------------------------------------
// Link preview — Obsidian-style hover popover for links
// -------------------------------------------------------------------
function initLinkPreviews() {
    const popover = document.getElementById('link-preview-popover');
    const imgEl = document.getElementById('link-preview-image');
    const titleEl = document.getElementById('link-preview-title');
    const descEl = document.getElementById('link-preview-desc');
    const openEl = document.getElementById('link-preview-open');
    if (!popover || !openEl) return;

    const SHOW_DELAY = 400;
    const HIDE_DELAY = 200;
    let showTimer = null;
    let hideTimer = null;
    let currentLink = null;
    let lastFetchUrl = null;

    function normalizePreviewUrl(link) {
        const href = link?.getAttribute('href') || '';
        if (!href || href.startsWith('#') || href.startsWith('mailto:') || href.startsWith('tel:')) return '';
        if (href.startsWith('http://') || href.startsWith('https://') || href.startsWith('/')) return href;
        return '';
    }

    function clearTimers() {
        if (showTimer) { clearTimeout(showTimer); showTimer = null; }
        if (hideTimer) { clearTimeout(hideTimer); hideTimer = null; }
    }

    function hidePreview() {
        clearTimers();
        popover.classList.remove('link-preview-visible');
        popover.setAttribute('aria-hidden', 'true');
        currentLink = null;
    }

    function positionPopover(link) {
        const rect = link.getBoundingClientRect();
        const popRect = popover.getBoundingClientRect();
        const gap = 8;
        let left = rect.left;
        let top = rect.bottom + gap;
        const viewW = window.innerWidth;
        const viewH = window.innerHeight;
        if (left + popRect.width > viewW - 16) left = viewW - popRect.width - 16;
        if (left < 16) left = 16;
        if (top + popRect.height > viewH - 16) top = rect.top - popRect.height - gap;
        if (top < 16) top = 16;
        popover.style.left = `${left}px`;
        popover.style.top = `${top}px`;
    }

    function showPreview(link, url) {
        currentLink = link;
        openEl.href = url;
        positionPopover(link);
        popover.classList.add('link-preview-visible');
        popover.setAttribute('aria-hidden', 'false');
        if (url !== lastFetchUrl) {
            titleEl.textContent = 'Loading…';
            descEl.textContent = '';
            imgEl.style.backgroundImage = '';
            imgEl.classList.add('empty');
            lastFetchUrl = url;
            fetch(`/api/link-preview?url=${encodeURIComponent(url)}`)
                .then(r => r.ok ? r.json() : null)
                .then(data => {
                    if (!data || url !== lastFetchUrl) return;
                    titleEl.textContent = data.title || 'Untitled';
                    descEl.textContent = data.description || '';
                    if (data.image) {
                        imgEl.style.backgroundImage = `url(${data.image})`;
                        imgEl.classList.remove('empty');
                    } else {
                        imgEl.classList.add('empty');
                    }
                })
                .catch(() => {
                    if (url === lastFetchUrl) titleEl.textContent = 'Preview unavailable';
                });
        }
    }

    document.addEventListener('mouseover', (e) => {
        const link = e.target.closest('a[href]');
        if (!link || link.closest('#link-preview-popover')) return;
        const normalized = normalizePreviewUrl(link);
        if (!normalized) return;
        if (link === currentLink) return;
        clearTimers();
        hideTimer = null;
        showTimer = setTimeout(() => {
            showTimer = null;
            showPreview(link, normalized);
        }, SHOW_DELAY);
    });

    document.addEventListener('mouseout', (e) => {
        const link = e.target.closest('a[href]');
        const toPopover = e.relatedTarget?.closest('#link-preview-popover');
        const toOtherLink = e.relatedTarget?.closest('a[href]');
        if (link && !toPopover) {
            if (showTimer) { clearTimeout(showTimer); showTimer = null; }
            if (toOtherLink && !toOtherLink.closest('#link-preview-popover')) {
                const nextUrl = normalizePreviewUrl(toOtherLink);
                if (!nextUrl) return;
                currentLink = null;
                showTimer = setTimeout(() => showPreview(toOtherLink, nextUrl), SHOW_DELAY);
            } else {
                hideTimer = setTimeout(hidePreview, HIDE_DELAY);
            }
        }
    });

    popover.addEventListener('mouseenter', () => {
        if (hideTimer) { clearTimeout(hideTimer); hideTimer = null; }
    });

    popover.addEventListener('mouseleave', (e) => {
        const toLink = e.relatedTarget?.closest('a[href]');
        if (!toLink) hideTimer = setTimeout(hidePreview, HIDE_DELAY);
    });
}

function initCommandPalette() {
    const trigger = document.getElementById('command-palette-trigger');
    const palette = document.getElementById('command-palette');
    const input = document.getElementById('command-palette-input');
    const backdrop = palette?.querySelector('.command-palette-backdrop');
    if (trigger) trigger.addEventListener('click', openCommandPalette);
    if (backdrop) backdrop.addEventListener('click', closeCommandPalette);
    if (input) {
        input.addEventListener('input', () => runCommandPaletteSearch(input.value));
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') { closeCommandPalette(); return; }
            const items = palette?.querySelectorAll('.command-palette-item') ?? [];
            const current = palette?.querySelector('.command-palette-item.highlighted');
            let idx = current ? parseInt(current.dataset.index, 10) : 0;
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                idx = Math.min(idx + 1, items.length - 1);
                items.forEach((el, i) => el.classList.toggle('highlighted', i === idx));
                if (items[idx]) items[idx].scrollIntoView({ block: 'nearest' });
                return;
            }
            if (e.key === 'ArrowUp') {
                e.preventDefault();
                idx = idx <= 0 ? items.length - 1 : idx - 1;
                items.forEach((el, i) => el.classList.toggle('highlighted', i === idx));
                if (items[idx]) items[idx].scrollIntoView({ block: 'nearest' });
                return;
            }
            if (e.key === 'Enter') {
                const target = idx >= 0 && items[idx] ? items[idx] : items[0];
                if (target) { target.click(); e.preventDefault(); }
            }
        });
    }
    document.addEventListener('keydown', (e) => {
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
            e.preventDefault();
            if (palette?.classList.contains('hidden')) openCommandPalette();
            else closeCommandPalette();
        }
    });
}

// -------------------------------------------------------------------
// Share link — create shareable read-only analysis URL
// -------------------------------------------------------------------
function copyShareLink() {
    if (!lastAnalysisSummary || !elements.modListInput?.value?.trim()) {
        showActionFeedback('Run an analysis first, then share.');
        return;
    }
    const modList = elements.modListInput.value.trim();
    const game = elements.gameSelect?.value || 'skyrimse';
    const payload = btoa(JSON.stringify({ m: modList.slice(0, 5000), g: game }));
    const url = `${window.location.origin}/?share=${encodeURIComponent(payload)}`;
    navigator.clipboard.writeText(url).then(() => {
        showActionFeedback('Share link copied. Anyone with the link can load your mod list and run analysis.');
    }).catch(() => showActionFeedback('Could not copy share link.'));
}

function loadShareFromUrl() {
    const params = new URLSearchParams(window.location.search);
    const share = params.get('share');
    if (!share) return;
    try {
        const payload = JSON.parse(atob(decodeURIComponent(share)));
        if (payload.m && elements.modListInput) {
            elements.modListInput.value = payload.m;
            if (payload.g && elements.gameSelect) elements.gameSelect.value = payload.g;
            updateModCounter();
            document.querySelector('.main-tab[data-tab="analyze"]')?.click();
        }
    } catch (_) {}
}

function initPageActionBindings() {
    const dismissErrorBtn = document.getElementById('index-error-dismiss');
    if (dismissErrorBtn) {
        dismissErrorBtn.addEventListener('click', () => {
            const banner = dismissErrorBtn.closest('.index-error-banner');
            if (banner) banner.remove();
            if (window.history.replaceState) {
                window.history.replaceState({}, '', window.location.pathname);
            }
        });
    }

    const modalCloseTargets = [
        document.getElementById('checkout-modal-backdrop'),
        document.getElementById('checkout-modal-close'),
        document.getElementById('checkout-modal-cancel'),
    ].filter(Boolean);
    modalCloseTargets.forEach((el) => {
        el.addEventListener('click', closeCheckoutModal);
    });
}

// -------------------------------------------------------------------
// Initialization
// -------------------------------------------------------------------
initCommandPalette();
initLinkPreviews();
loadShareFromUrl();
initPageActionBindings();
initFeedbackModal();
initAnalysisFeedbackPanel();
initMainTabs();
initCommunityPost();
initQuickstartGameSelect();
initQuickstartLivePreview();
loadGames();
checkUserTier();
initGameFolderScan();
initDevTools();
updateModCounter();

const masterlistVersionSelect = document.getElementById('masterlist-version');
const gameVersionSelect = document.getElementById('game-version');
if (elements.gameSelect) {
    elements.gameSelect.addEventListener('change', () => {
        const gameId = elements.gameSelect.value;
        if (masterlistVersionSelect) loadMasterlistVersions(gameId).then(versions => populateMasterlistVersionSelect(masterlistVersionSelect, versions));
        if (gameVersionSelect) loadGameVersions(gameId).then(data => populateGameVersionSelect(gameVersionSelect, data));
        // Mod list is intentionally preserved — accidental game switch shouldn't wipe work.
        // User can Clear or paste over if switching games intentionally.
        fetchAndShowRecommendations();
        refreshInputMatchPreview({ silent: true });
    });
}
if (gameVersionSelect) {
    gameVersionSelect.addEventListener('change', updateGameVersionInfo);
}

// Expose for inline handlers
window.upgradeToPro = upgradeToPro;
window.closeCheckoutModal = closeCheckoutModal;
window.submitCheckout = submitCheckout;
