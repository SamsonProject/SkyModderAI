// SkyModderAI - Frontend JavaScript
// Handles mod list analysis, UI updates, and Stripe checkout

const PLUGIN_LIMIT_WARN = 253;
let currentUserTier = (typeof window.__USER_TIER__ !== 'undefined' ? window.__USER_TIER__ : 'free');
let currentUserEmail = null;
let aiChatEnabled = false;
let platformCapabilities = {};
let currentReport = '';
let currentSuggestedOrder = [];
let currentAnalysisData = null;
let lastAnalysisSummary = null;
let autoAnalyzeTimeout = null;

// Priority 1: Extensive Linking & Keywords
const SMART_LINKS = {
    'loot': 'https://loot.github.io/',
    'nexus': 'https://www.nexusmods.com/',
    'nexus mods': 'https://www.nexusmods.com/',
    'mo2': 'https://www.modorganizer.org/',
    'mod organizer 2': 'https://www.modorganizer.org/',
    'vortex': 'https://www.nexusmods.com/site/mods/1',
    'xedit': 'https://tes5edit.github.io/',
    'sseedit': 'https://tes5edit.github.io/',
    'skse': 'https://skse.silverlock.org/',
    'wabbajack': 'https://www.wabbajack.org/',
    'google': 'https://www.google.com/',
    'amazon': 'https://www.amazon.com/',
    'youtube': 'https://www.youtube.com/'
};

// Pre-compile regexes for performance (Senior Engineer Optimization)
const SMART_LINK_MATCHERS = Object.keys(SMART_LINKS)
    .sort((a, b) => b.length - a.length)
    .map(key => ({
        regex: new RegExp(`\\b(${key})\\b(?![^<]*>|[^<>]*<\\/a>)`, 'gi'),
        url: SMART_LINKS[key]
    }));

// -------------------------------------------------------------------
// Unified User Context - Single Source of Truth
// -------------------------------------------------------------------
const userContext = {
    // Game context
    selectedGame: 'skyrimse',
    gameVersion: '',
    masterlistBranch: '',

    // Current work
    currentModList: '',
    currentModListParsed: [],
    lastAnalysisResult: null,

    // Saved lists metadata
    savedLists: [],
    currentSavedList: null,

    // Search context
    searchQuery: '',
    searchResults: [],
    recentSearches: [],

    // UI state
    activeTab: 'analyze',
    filterState: {
        errors: true,
        warnings: true,
        info: true
    },

    // Timestamps for tracking
    lastAnalysisTime: null,
    lastSaveTime: null,

    // Initialize from localStorage
    init() {
        try {
            const stored = localStorage.getItem('skymodder_userContext');
            if (stored) {
                const data = JSON.parse(stored);
                // Only restore safe fields, avoid overwriting fresh state
                Object.assign(this, {
                    selectedGame: data.selectedGame || 'skyrimse',
                    gameVersion: data.gameVersion || '',
                    masterlistBranch: data.masterlistBranch || '',
                    currentModList: data.currentModList || '',
                    savedLists: data.savedLists || [],
                    recentSearches: data.recentSearches || [],
                    filterState: data.filterState || { errors: true, warnings: true, info: true }
                });
            }
        } catch (e) {
            console.warn('Failed to restore userContext:', e);
        }

        // Listen for cross-tab changes
        window.addEventListener('storage', (e) => {
            if (e.key === 'skymodder_userContext' && e.newValue) {
                try {
                    const data = JSON.parse(e.newValue);
                    this.mergeChanges(data);
                } catch (e) {
                    console.warn('Failed to merge cross-tab context:', e);
                }
            }
        });
    },

    // Save to localStorage
    save() {
        try {
            const toSave = {
                selectedGame: this.selectedGame,
                gameVersion: this.gameVersion,
                masterlistBranch: this.masterlistBranch,
                currentModList: this.currentModList,
                savedLists: this.savedLists,
                recentSearches: this.recentSearches,
                filterState: this.filterState,
                lastAnalysisTime: this.lastAnalysisTime,
                lastSaveTime: this.lastSaveTime
            };
            localStorage.setItem('skymodder_userContext', JSON.stringify(toSave));
        } catch (e) {
            console.warn('Failed to save userContext:', e);
        }
    },

    // Merge changes from other tabs
    mergeChanges(data) {
        // Only update if the other tab is newer
        if (data.lastAnalysisTime && data.lastAnalysisTime > this.lastAnalysisTime) {
            this.lastAnalysisResult = data.lastAnalysisResult;
            this.lastAnalysisTime = data.lastAnalysisTime;
        }
        if (data.lastSaveTime && data.lastSaveTime > this.lastSaveTime) {
            this.savedLists = data.savedLists;
            this.lastSaveTime = data.lastSaveTime;
        }
        // Always sync game context
        this.selectedGame = data.selectedGame || this.selectedGame;
        this.gameVersion = data.gameVersion || this.gameVersion;
        this.masterlistBranch = data.masterlistBranch || this.masterlistBranch;
        this.currentModList = data.currentModList || this.currentModList;
        this.recentSearches = data.recentSearches || this.recentSearches;

        // Trigger UI updates if needed
        this.notifyChange();
    },

    // Notify components of context changes
    notifyChange() {
        window.dispatchEvent(new CustomEvent('userContextChange', { detail: this }));
    },

    // Update game context
    setGame(game, version = '', branch = '') {
        this.selectedGame = game;
        this.gameVersion = version;
        this.masterlistBranch = branch;
        this.save();
        this.notifyChange();
    },

    // Update current mod list
    setModList(listText) {
        this.currentModList = listText;
        // Parse into array for easier processing
        this.currentModListParsed = listText.split('\n')
            .map(line => line.trim())
            .filter(line => line && !line.startsWith('#'));
        this.save();
        this.notifyChange();
    },

    // Update analysis result
    setAnalysisResult(result) {
        this.lastAnalysisResult = result;
        this.lastAnalysisTime = Date.now();
        this.save();
        this.notifyChange();
    },

    // Add search to recent searches
    addRecentSearch(query) {
        if (!query || !query.trim()) return;
        query = query.trim();
        this.recentSearches = this.recentSearches.filter(s => s !== query);
        this.recentSearches.unshift(query);
        this.recentSearches = this.recentSearches.slice(0, 10); // Keep last 10
        this.save();
    },

    // Get context summary for display
    getSummary() {
        const analysis = this.lastAnalysisResult;
        const errorCount = analysis?.errors?.length || 0;
        const warningCount = analysis?.warnings?.length || 0;
        const modCount = this.currentModListParsed.length;

        return {
            game: this.selectedGame,
            gameVersion: this.gameVersion,
            masterlistBranch: this.masterlistBranch,
            modCount,
            errorCount,
            warningCount,
            hasAnalysis: !!analysis,
            currentSavedList: this.currentSavedList
        };
    }
};

// Initialize userContext immediately
userContext.init();
window.userContext = userContext;

// -------------------------------------------------------------------
// Context Trail - Shows current user context path
// -------------------------------------------------------------------
function updateContextTrail() {
    if (!elements.contextTrailContent) return;

    const summary = userContext.getSummary();
    const items = [];

    // Hide trail if no mods and no analysis (reduces clutter)
    if (summary.modCount === 0 && !summary.hasAnalysis) {
        if (elements.contextTrail) elements.contextTrail.classList.add('hidden');
        return;
    }
    if (elements.contextTrail) elements.contextTrail.classList.remove('hidden');

    // Game selector (always shown)
    const gameName = getGameDisplayName(summary.game);
    items.push(`<span class="context-trail-item clickable context-trail-game" onclick="showGameSelector()">${gameName}</span>`);

    // Game version if available
    if (summary.gameVersion) {
        items.push(`<span class="context-trail-separator">|</span>`);
        items.push(`<span class="context-trail-item clickable" onclick="showGameVersionSelector()">v${summary.gameVersion}</span>`);
    }

    // Masterlist branch if available
    if (summary.masterlistBranch) {
        items.push(`<span class="context-trail-separator">|</span>`);
        items.push(`<span class="context-trail-item clickable" onclick="showMasterlistSelector()">${summary.masterlistBranch}</span>`);
    }

    // Mod count
    if (summary.modCount > 0) {
        items.push(`<span class="context-trail-separator">|</span>`);
        items.push(`<span class="context-trail-item clickable" onclick="focusModList()">${summary.modCount} mods</span>`);
    }

    // Analysis results
    if (summary.hasAnalysis) {
        items.push(`<span class="context-trail-separator">|</span>`);
        const errorClass = summary.errorCount > 0 ? 'context-trail-errors' : '';
        const warningClass = summary.warningCount > 0 ? 'context-trail-warnings' : '';

        if (summary.errorCount > 0) {
            items.push(`<span class="context-trail-item clickable ${errorClass}" onclick="scrollToErrors()">${summary.errorCount} errors</span>`);
        }
        if (summary.warningCount > 0) {
            items.push(`<span class="context-trail-item clickable ${warningClass}" onclick="scrollToWarnings()">${summary.warningCount} warnings</span>`);
        }
        if (summary.errorCount === 0 && summary.warningCount === 0) {
            items.push(`<span class="context-trail-item clickable" onclick="scrollToResults()">✓ Clean</span>`);
        }
    }

    // Current saved list
    if (summary.currentSavedList) {
        items.push(`<span class="context-trail-separator">|</span>`);
        items.push(`<span class="context-trail-item clickable context-trail-saved-list" onclick="openLibraryList()">${summary.currentSavedList}</span>`);
    }

    // Show empty state if no content
    if (items.length === 1) {
        items.push('<span class="context-trail-empty">No mods loaded</span>');
    }

    elements.contextTrailContent.innerHTML = items.join('');
}

// Context trail action handlers
function showGameSelector() {
    if (elements.gameSelect) {
        elements.gameSelect.focus();
        elements.gameSelect.click();
    }
}

function showGameVersionSelector() {
    const versionSelect = document.getElementById('game-version');
    if (versionSelect) {
        versionSelect.focus();
        versionSelect.click();
    }
}

function showMasterlistSelector() {
    const masterlistSelect = document.getElementById('masterlist-version');
    if (masterlistSelect) {
        masterlistSelect.focus();
        masterlistSelect.click();
    }
}

function focusModList() {
    if (elements.modListInput) {
        elements.modListInput.focus();
        // Switch to Analyze tab if not already there
        const analyzeTab = document.querySelector('[data-tab="analyze"]');
        if (analyzeTab && !analyzeTab.classList.contains('active')) {
            analyzeTab.click();
        }
    }
}

function scrollToErrors() {
    const errorSection = document.getElementById('errors-section') || document.querySelector('.conflicts-section.error');
    if (errorSection) {
        errorSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

function scrollToWarnings() {
    const warningSection = document.getElementById('warnings-section') || document.querySelector('.conflicts-section.warning');
    if (warningSection) {
        warningSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

function scrollToResults() {
    const resultsPanel = document.getElementById('results-panel');
    if (resultsPanel) {
        resultsPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

function openLibraryList() {
    const libraryTab = document.querySelector('[data-tab="library"]');
    if (libraryTab) {
        libraryTab.click();
    }
}

function linkify(text) {
    if (!text) return '';
    let linked = text;
    SMART_LINK_MATCHERS.forEach(({ regex, url }) => {
        linked = linked.replace(regex, `<a href="${url}" class="smart-link" data-portal="true">$1</a>`);
    });
    return linked;
}

// Listen for userContext changes and update trail
window.addEventListener('userContextChange', () => {
    updateContextTrail();
});

// DOM Elements
const elements = {};

function initDomElements() {
    Object.assign(elements, {
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
        contextTrailContent: document.getElementById('context-trail-content'),
        chatInput: document.getElementById('chat-input'),
        chatSendBtn: document.getElementById('chat-send-btn'),
        chatUpgradeCta: document.getElementById('chat-upgrade-cta'),
        fixGuideSection: document.getElementById('fix-guide-section'),
        fixGuideContent: document.getElementById('fix-guide-content'),
        // Library elements
        librarySearch: document.getElementById('library-search'),
        librarySearchClear: document.getElementById('library-search-clear'),
        libraryFilterGame: document.getElementById('library-filter-game'),
        libraryFilterVersion: document.getElementById('library-filter-version'),
        libraryFilterMasterlist: document.getElementById('library-filter-masterlist'),
        libraryRefreshBtn: document.getElementById('library-refresh-btn'),
        libraryStatus: document.getElementById('library-status'),
        libraryGrid: document.getElementById('library-grid'),
        // Context trail elements
        contextTrail: document.getElementById('context-trail')
    });
}

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
    // Marketing revamp: Everything is free.
    return true;
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
        matches.forEach((mod) => {
            const row = document.createElement('div');
            row.className = 'mod-search-item mod-search-row';
            const modName = mod.mod_name || mod; // Support both object and string for backward compatibility
            row.dataset.index = String(rowIndex++);
            row.dataset.modName = modName;

            // Mod image if available
            if (mod.picture_url) {
                const imgContainer = document.createElement('div');
                imgContainer.style.position = 'relative';
                imgContainer.style.width = '100%';
                imgContainer.style.height = '160px';
                imgContainer.style.marginBottom = '12px';
                imgContainer.style.borderRadius = '8px 8px 0 0';
                imgContainer.style.overflow = 'hidden';

                const img = document.createElement('img');
                img.src = mod.picture_url;
                img.alt = modName;
                img.className = 'mod-preview-img';
                img.style.width = '100%';
                img.style.height = '100%';
                img.style.objectFit = 'cover';
                img.onerror = function () {
                    this.style.display = 'none';
                };

                // Make the image clickable to the Nexus Mods page if ID is available
                if (mod.nexus_mod_id) {
                    const link = document.createElement('a');
                    link.href = `https://www.nexusmods.com/${nexusSlug}/mods/${mod.nexus_mod_id}`;
                    link.target = '_blank';
                    link.rel = 'noopener noreferrer';
                    link.appendChild(img);
                    imgContainer.appendChild(link);
                } else {
                    imgContainer.appendChild(img);
                }

                row.appendChild(imgContainer);
            }

            // Mod name label (make it a link if Nexus Mod ID is available)
            const label = document.createElement(mod.nexus_mod_id ? 'a' : 'span');
            label.className = 'mod-search-name';
            label.textContent = modName;

            if (mod.nexus_mod_id) {
                label.href = `https://www.nexusmods.com/${nexusSlug}/mods/${mod.nexus_mod_id}`;
                label.target = '_blank';
                label.rel = 'noopener noreferrer';
                label.style.textDecoration = 'none';
                label.style.color = 'var(--text-primary)';
                label.addEventListener('mouseover', () => {
                    label.style.textDecoration = 'underline';
                    label.style.color = 'var(--accent-primary)';
                });
                label.addEventListener('mouseout', () => {
                    label.style.textDecoration = 'none';
                    label.style.color = 'var(--text-primary)';
                });
            }

            // Quick Add button
            const addBtn = document.createElement('button');
            addBtn.className = 'mod-search-quick-add primary-button small';
            addBtn.textContent = 'Add';
            addBtn.title = `Add ${modName} to current list`;

            // Analyze button
            const analyzeBtn = document.createElement('button');
            analyzeBtn.className = 'mod-search-analyze secondary-button small';
            analyzeBtn.textContent = 'Analyze';
            analyzeBtn.title = `Analyze ${modName} for conflicts`;

            function addModToList() {
                const listInput = document.getElementById('mod-list-input');
                if (listInput) {
                    const prefix = listInput.value.trim() ? '\n' : '';
                    listInput.value += prefix + '*' + modName;
                    updateModCounter();
                    // Add to recent searches
                    userContext.addRecentSearch(q);
                }
                resultsEl.classList.add('hidden');
                inputEl.value = '';
                if (clearBtn) clearBtn.classList.add('hidden');
            }

            function analyzeMod() {
                // Create a temporary list with just this mod
                const tempModList = `*${modName}`;
                const gameSelect = document.getElementById('game-select');
                const versionSelect = document.getElementById('game-version');
                const masterlistSelect = document.getElementById('masterlist-version');

                // Set the mod list and switch to analyze tab
                const listInput = document.getElementById('mod-list-input');
                if (listInput) {
                    listInput.value = tempModList;
                    updateModCounter();
                }

                // Update game/version if provided
                if (gameSelect && gameSelect.value) {
                    userContext.setGame(gameSelect.value, versionSelect?.value || '', masterlistSelect?.value || '');
                }

                // Switch to analyze tab and run analysis
                const analyzeTab = document.querySelector('[data-tab="analyze"]');
                if (analyzeTab && !analyzeTab.classList.contains('active')) {
                    analyzeTab.click();
                }

                // Add to recent searches
                userContext.addRecentSearch(q);

                // Auto-run analysis after a short delay
                setTimeout(() => {
                    const analyzeBtn = document.getElementById('analyze-btn');
                    if (analyzeBtn) analyzeBtn.click();
                }, 100);

                resultsEl.classList.add('hidden');
                inputEl.value = '';
                if (clearBtn) clearBtn.classList.add('hidden');
            }

            addBtn.addEventListener('click', (e) => { e.stopPropagation(); addModToList(); });
            analyzeBtn.addEventListener('click', (e) => { e.stopPropagation(); analyzeMod(); });
            label.addEventListener('mousedown', (e) => { e.preventDefault(); addModToList(); });

            row.addEventListener('click', (e) => {
                if (!e.target.closest('.mod-search-nexus') && !e.target.closest('button')) {
                    e.preventDefault();
                    addModToList();
                }
            });

            row.appendChild(label);

            // Action buttons container
            const actions = document.createElement('div');
            actions.className = 'mod-search-actions';
            actions.appendChild(addBtn);
            actions.appendChild(analyzeBtn);
            row.appendChild(actions);

            // Nexus link
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

                // Mod name label
                const label = document.createElement('span');
                label.className = 'mod-search-name';
                label.textContent = item.name || '';

                // Quick Add button
                const addBtn = document.createElement('button');
                addBtn.className = 'mod-search-quick-add primary-button small';
                addBtn.textContent = 'Add';
                addBtn.title = `Add ${item.name} to current list`;

                // Analyze button
                const analyzeBtn = document.createElement('button');
                analyzeBtn.className = 'mod-search-analyze secondary-button small';
                analyzeBtn.textContent = 'Analyze';
                analyzeBtn.title = `Analyze ${item.name} for conflicts`;

                function addModToList() {
                    const listInput = document.getElementById('mod-list-input');
                    if (listInput && item.name) {
                        const prefix = listInput.value.trim() ? '\n' : '';
                        listInput.value += prefix + '*' + item.name;
                        updateModCounter();
                        // Add to recent searches
                        userContext.addRecentSearch(q);
                    }
                    resultsEl.classList.add('hidden');
                    inputEl.value = '';
                    if (clearBtn) clearBtn.classList.add('hidden');
                }

                function analyzeMod() {
                    if (!item.name) return;
                    // Create a temporary list with just this mod
                    const tempModList = `*${item.name}`;
                    const gameSelect = document.getElementById('game-select');
                    const versionSelect = document.getElementById('game-version');
                    const masterlistSelect = document.getElementById('masterlist-version');

                    // Set the mod list and switch to analyze tab
                    const listInput = document.getElementById('mod-list-input');
                    if (listInput) {
                        listInput.value = tempModList;
                        updateModCounter();
                    }

                    // Update game/version if provided
                    if (gameSelect && gameSelect.value) {
                        userContext.setGame(gameSelect.value, versionSelect?.value || '', masterlistSelect?.value || '');
                    }

                    // Switch to analyze tab and run analysis
                    const analyzeTab = document.querySelector('[data-tab="analyze"]');
                    if (analyzeTab && !analyzeTab.classList.contains('active')) {
                        analyzeTab.click();
                    }

                    // Add to recent searches
                    userContext.addRecentSearch(q);

                    // Auto-run analysis after a short delay
                    setTimeout(() => {
                        const analyzeBtn = document.getElementById('analyze-btn');
                        if (analyzeBtn) analyzeBtn.click();
                    }, 100);

                    resultsEl.classList.add('hidden');
                    inputEl.value = '';
                    if (clearBtn) clearBtn.classList.add('hidden');
                }

                addBtn.addEventListener('click', (e) => { e.stopPropagation(); addModToList(); });
                analyzeBtn.addEventListener('click', (e) => { e.stopPropagation(); analyzeMod(); });
                label.addEventListener('mousedown', (e) => { e.preventDefault(); addModToList(); });
                row.addEventListener('click', (e) => {
                    if (!e.target.closest('a') && !e.target.closest('button')) {
                        e.preventDefault();
                        addModToList();
                    }
                });

                row.appendChild(label);

                // Action buttons container
                const actions = document.createElement('div');
                actions.className = 'mod-search-actions';
                actions.appendChild(addBtn);
                actions.appendChild(analyzeBtn);
                row.appendChild(actions);

                // External link
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
 * Unified Game State Sync
 * Links all game selectors and updates dependent data (versions, quickstart, build list).
 */
const GAME_SELECTORS = ['game-select', 'quickstart-game', 'build-list-game', 'dev-game-select'];

function initGlobalGameSync() {
    GAME_SELECTORS.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('change', (e) => {
                updateGlobalGame(e.target.value, id);
            });
        }
    });
}

async function updateGlobalGame(gameId, sourceId = null) {
    if (!gameId) return;

    // 1. Sync other selectors
    GAME_SELECTORS.forEach(id => {
        if (id === sourceId) return;
        const el = document.getElementById(id);
        if (el) el.value = gameId;
    });

    // 2. Update User Context
    userContext.setGame(gameId);

    // 3. Update Versions (Analyze tab) - High value tool: Version Adaptation
    const masterlistSelect = document.getElementById('masterlist-version');
    const gameVersionSelect = document.getElementById('game-version');

    const p1 = loadMasterlistVersions(gameId).then(v => {
        if (masterlistSelect) populateMasterlistVersionSelect(masterlistSelect, v);
    });
    const p2 = loadGameVersions(gameId).then(v => {
        if (gameVersionSelect) populateGameVersionSelect(gameVersionSelect, v);
    });

    // 4. Update Tab Content & Previews
    loadQuickstartContent();
    loadBuildListOptions(gameId);
    fetchAndShowRecommendations();
    refreshInputMatchPreview({ silent: true });

    // Refresh gameplay tab if active
    if (document.querySelector('.main-tab[data-tab="gameplay"].active')) {
        if (window.GameplayUI) window.GameplayUI.init('gameplay-container');
        else if (window.WalkthroughUI) window.WalkthroughUI.init('gameplay-container');
    }

    await Promise.all([p1, p2]);
}

async function loadGames() {
    try {
        const response = await fetch('/api/games');
        if (!response.ok) return;
        const data = await response.json();
        if (!data.games) return;
        supportedGames = data.games;

        const storedGame = userContext.selectedGame || localStorage.getItem('skymodder_selected_game');
        const defaultGame = data.default || 'skyrimse';
        const gameToSelect = data.games.some(g => g.id === storedGame) ? storedGame : defaultGame;

        // Populate ALL game selectors
        GAME_SELECTORS.forEach(id => {
            const el = document.getElementById(id);
            if (!el) return;
            el.innerHTML = '';
            data.games.forEach(g => {
                const opt = document.createElement('option');
                opt.value = g.id;
                opt.textContent = g.name;
                if (g.id === gameToSelect) opt.selected = true;
                el.appendChild(opt);
            });
        });

        // Initial sync
        updateGlobalGame(gameToSelect);
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
        currentUserEmail = data.email || null;
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
            return showToast(data.error || 'Could not parse mod list.', 'error');
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
        if (!silent) showToast('Could not fetch live matches. Try again.', 'error');
    } finally {
        if (actionBtn && applyFormatted) actionBtn.disabled = false;
    }
}

/**
 * Fetch and display LOOT-based suggestions (missing requirements and companion mods).
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

        renderNextActions(data.next_actions || []);
        // Render LOOT-based suggestions - no categories, just name and reason
        cards.innerHTML = recs.map(r => `
            <div class="mod-preview-card" data-mod-name="${escapeHtml(r.name)}">
                <a href="${escapeHtml(r.nexus_url || '#')}" target="_blank" rel="noopener noreferrer" title="${escapeHtml(r.name)}">
                    <img src="${escapeHtml(r.image_url || '/static/icons/mod-placeholder.svg')}" alt="" loading="lazy">
                    <span class="mod-preview-name">${escapeHtml(r.name)}</span>
                    <span class="mod-preview-reason">${escapeHtml(r.reason || '')}</span>
                </a>
                <button type="button" class="mod-preview-add" title="Add to list" aria-label="Add ${escapeHtml(r.name)} to list">+</button>
            </div>
        `).join('');
    } catch (e) {
        strip.classList.add('hidden');
    }
}

/**
 * Update the mod counter and show/hide free tier / plugin limit warnings.
 */
function updateModCounter(options = {}) {
    if (!elements.modListInput || !elements.modCount) return;

    const text = elements.modListInput.value;

    // Update userContext with current mod list
    userContext.setModList(text);

    const lines = userContext.currentModListParsed.length;

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

    // Priority 3: Automation - Auto-analyze
    if (!options.skipAutoAnalyze) {
        clearTimeout(autoAnalyzeTimeout);
        autoAnalyzeTimeout = setTimeout(() => {
            const content = elements.modListInput.value.trim();
            if (content && content.length > 5) analyzeModList();
        }, 1500);
    }
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

    if (btn) btn.disabled = true;
    if (statusEl) statusEl.textContent = 'Scanning…';

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

    // GPU Fallback: WebGL (More compatible)
    if (!detected.gpu) {
        try {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            if (gl) {
                const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                if (debugInfo) {
                    const renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
                    if (renderer) {
                        detected.gpu = renderer;
                        parts.push(`GPU (WebGL): ${renderer}`);
                    }
                }
            }
        } catch (e) {
            console.warn('WebGL scan failed:', e);
        }
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
        if (statusEl) statusEl.textContent = `Detected ${count} value(s). Add VRAM manually if needed.`;
        currentSpecs = { ...currentSpecs, ...Object.fromEntries(Object.entries(detected).filter(([, v]) => v)) };
        showToast(`System scanned: ${detected.cpu || ''} ${detected.gpu || ''}`, 'success');
        saveSpecs(); // Auto-save detected specs
    } else {
        if (statusEl) statusEl.textContent = 'Could not detect specs in this browser. Try Steam System Info paste.';
        showToast('Could not detect system specs. Browser may be restricted.', 'warning');
    }

    if (btn) btn.disabled = false;
}
window.scanSystem = scanSystem;

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
                // Try new key first, then fall back to old key for backward compatibility
                const stored = localStorage.getItem('skymodderai_specs') || localStorage.getItem('modcheck_specs');
                if (stored) specs = JSON.parse(stored);
            } catch (_) { }
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
    } catch (_) { }
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
            try { localStorage.setItem('skymodderai_specs', JSON.stringify(currentSpecs)); } catch (_) { }
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

    // Live PDF-style rendering
    let html = `
        <div class="live-doc-container">
            <div class="live-doc-header">
                <div class="live-doc-title">Strategic Fix Plan: ${escapeHtml(fixGuideMeta.gameName)}</div>
                <div class="live-doc-meta">Generated ${fixGuideMeta.date} • SkyModderAI Agent</div>
            </div>
            <div class="live-doc-body">
    `;

    let stepNum = 0;
    fixGuideSteps.forEach((s) => {
        const parseMd = (window.marked && typeof marked.parse === 'function') ? (s) => marked.parse(s) : (s) => escapeHtml(s);

        if (s.type === 'intro') {
            html += `<div class="live-doc-intro">${escapeHtml(s.content)}</div>`;
        } else if (s.type === 'step' || s.type === 'fix') {
            stepNum++;
            const severityClass = s.severity ? ` severity-${s.severity}` : '';
            let content = '';

            if (s.type === 'fix') {
                content = `<strong>${escapeHtml(s.mod || '')}</strong>: ${linkify(escapeHtml(s.message || ''))}`;
                if (s.action) content += `<br><em style="color:var(--accent)">Action:</em> ${linkify(escapeHtml(s.action))}`;
            } else {
                content = linkify(escapeHtml(s.content));
            }

            html += `
                <div class="live-doc-step${severityClass}" ${s.id ? `data-fix-id="${escapeHtml(s.id)}"` : ''}>
                    <span class="live-doc-num">${stepNum}.</span>
                    <div class="live-doc-content">${content}</div>
                    ${s.type === 'fix' ? `<label class="fix-guide-check"><input type="checkbox" class="fix-guide-resolved"> Mark as Resolved</label>` : ''}
                </div>`;
        } else if (s.type === 'ai') {
            // AI updates inserted as dynamic blocks
            const body = linkify(parseMd(s.content));
            html += `
                <div class="live-doc-ai-update">
                    <span class="live-doc-ai-badge">Agent Update</span>
                    ${s.question ? `<p style="font-size:0.85em;color:var(--text-muted);margin-bottom:8px;">Re: ${escapeHtml(s.question)}</p>` : ''}
                    <div class="live-doc-content">${body}</div>
                </div>`;
        }
    });

    html += `</div></div>`; // Close body and container
    elements.fixGuideContent.innerHTML = html;
    elements.fixGuideContent.querySelectorAll('.fix-guide-resolved').forEach(cb => {
        cb.addEventListener('change', () => renderFixGuide());
    });

    const composeBtn = document.getElementById('compose-fix-guide-btn');
    if (composeBtn) composeBtn.addEventListener('click', composeFixGuide);

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

async function composeFixGuide() {
    const btn = document.getElementById('compose-fix-guide-btn');
    if (btn) {
        btn.disabled = true;
        btn.textContent = 'Composing...';
    }

    try {
        const res = await fetch('/api/compose-guide', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                steps: fixGuideSteps,
                game: fixGuideMeta.gameName
            })
        });
        const data = await res.json();
        if (data.document) {
            const parseMd = (window.marked && typeof marked.parse === 'function') ? (s) => marked.parse(s) : (s) => escapeHtml(s);
            const htmlContent = `
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <title>SkyModderAI Strategic Plan - ${escapeHtml(fixGuideMeta.gameName)}</title>
                    <style>
                        body { font-family: 'Segoe UI', system-ui, sans-serif; line-height: 1.6; padding: 40px; max-width: 800px; margin: 0 auto; color: #111; }
                        h1, h2, h3 { color: #005f73; margin-top: 1.5em; }
                        code { background: #f4f4f4; padding: 2px 5px; border-radius: 3px; font-family: monospace; }
                        pre { background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }
                        blockquote { border-left: 4px solid #00d4e8; margin: 1em 0; padding-left: 15px; color: #555; }
                        hr { border: 0; border-top: 1px solid #eee; margin: 2em 0; }
                    </style>
                </head>
                <body>
                    ${parseMd(data.document)}
                </body>
                </html>
            `;
            const win = window.open('', '_blank');
            win.document.write(htmlContent);
            win.document.close();
            setTimeout(() => win.print(), 500);
        }
    } catch (e) {
        showToast('Failed to compose guide.', 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = 'Compose PDF Guide';
        }
    }
}

function downloadFixGuideHTML() {
    const html = buildFixGuideHTMLForDownload();
    const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `skymodderai-fix-guide-${(fixGuideMeta.date || '').replace(/\s/g, '-') || 'report'}.html`;
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
            const reply = parseMd ? (() => { try { return parseMd(s.content); } catch (_) { return escapeHtml(s.content); } })() : escapeHtml(s.content);
            body += `<div class="fg-ai"><span class="fg-num">${n}</span>${s.question ? `<p class="fg-q">You asked: ${escapeHtml(s.question)}</p>` : ''}<div class="fg-reply">${reply}</div></div>`;
        }
    });
    return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Action Plan: ${escapeHtml(fixGuideMeta.gameName)}</title>
<style>
    @page { margin: 2cm; }
    body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; line-height: 1.5; color: #111; max-width: 800px; margin: 0 auto; padding: 40px; background: #fff; }
    h1 { font-size: 24px; border-bottom: 2px solid #000; padding-bottom: 12px; margin-bottom: 24px; }
    .meta { color: #666; font-size: 14px; margin-bottom: 32px; font-style: italic; }
    .fg-intro { background: #f8f9fa; padding: 16px; border-left: 4px solid #333; margin-bottom: 24px; }

    .fg-step, .fg-fix, .fg-ai { margin-bottom: 16px; padding: 12px; border: 1px solid #e5e7eb; border-radius: 4px; page-break-inside: avoid; }
    .fg-fix.fg-error { border-left: 4px solid #dc2626; background: #fef2f2; }
    .fg-fix.fg-warning { border-left: 4px solid #d97706; background: #fffbeb; }
    .fg-fix.fg-done { text-decoration: line-through; opacity: 0.6; }

    .fg-num { font-weight: bold; display: inline-block; width: 24px; color: #555; }
    .fg-action { margin-top: 8px; font-weight: 600; color: #0284c7; display: block; }
    .fg-action::before { content: "→ "; }

    .checkbox-print { display: inline-block; width: 14px; height: 14px; border: 1px solid #333; margin-right: 8px; vertical-align: middle; position: relative; top: -1px; }
    .checkbox-print.checked::after { content: "✓"; position: absolute; top: -4px; left: 1px; font-size: 16px; font-weight: bold; }

    .fg-ai { background: #f0f9ff; border: 1px dashed #0ea5e9; }
    .fg-q { font-size: 0.85em; color: #64748b; margin-bottom: 4px; }

    @media print {
        body { padding: 0; max-width: 100%; }
        .fg-fix.fg-error { border-left-color: #000 !important; border-left-width: 4px !important; }
        a { text-decoration: none; color: #000; }
    }
</style>
</head>
<body>
<h1>SkyModderAI Action Plan</h1>
<div class="meta">Generated for ${escapeHtml(fixGuideMeta.gameName)} on ${escapeHtml(fixGuideMeta.date)}</div>
${body}
</body>
</html>`;
}

function printFixGuide() {
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

// NEW: Populate transparency panel from metadata
function populateTransparencyPanel(metadata) {
    const panel = document.getElementById('transparency-panel');
    if (!panel || !metadata) return;

    const sources = metadata.data_sources || [];
    const filters = metadata.filters || [];
    const ai = metadata.ai_involvement || {};
    const perf = metadata.performance || {};

    panel.innerHTML = `
        <div class="transparency-section">
            <h4>📊 Data Sources</h4>
            <ul class="transparency-list">
                ${sources.map(s => `
                    <li>
                        <strong>${escapeHtml(s.name)}</strong>
                        <span class="hint">${escapeHtml(s.description || '')}</span>
                        ${s.url ? `<a href="${escapeHtml(s.url)}" target="_blank" rel="noopener">Learn more ↗</a>` : ''}
                    </li>
                `).join('')}
            </ul>
        </div>
        <div class="transparency-section">
            <h4>⚙️ Filters Applied</h4>
            <ul class="transparency-list">
                ${filters.map(f => `
                    <li>
                        <strong>${escapeHtml(f.name)}</strong>: ${escapeHtml(f.value || 'None')}
                        <span class="hint">${escapeHtml(f.description || '')}</span>
                    </li>
                `).join('')}
            </ul>
        </div>
        <div class="transparency-section">
            <h4>🤖 AI Involvement</h4>
            <ul class="transparency-list">
                <li><strong>Conflict Detection:</strong> ${escapeHtml(ai.conflict_detection || 'Deterministic')}</li>
                <li><strong>Resolution Suggestions:</strong> ${escapeHtml(ai.resolution_suggestions || 'Rule-based')}</li>
                <li><strong>Tokens Used:</strong> ${ai.tokens_used || 0}</li>
            </ul>
        </div>
        <div class="transparency-section">
            <h4>⏱️ Performance</h4>
            <ul class="transparency-list">
                <li><strong>Duration:</strong> ${(perf.duration_ms || 0).toFixed(2)}ms</li>
                <li><strong>Items Analyzed:</strong> ${perf.items_analyzed || 0}</li>
                <li><strong>Conflicts Found:</strong> ${perf.conflicts_found || 0}</li>
            </ul>
        </div>
    `;
}

// NEW: Display consolidated conflicts (hierarchical)
function displayConsolidatedConflicts(consolidated) {
    const container = document.getElementById('conflicts-container');
    if (!container || !consolidated || !consolidated.groups) return;

    container.innerHTML = '';

    // Display groups hierarchically
    consolidated.groups.forEach(group => {
        const groupEl = document.createElement('div');
        groupEl.className = `conflict-group ${group.severity}`;
        groupEl.innerHTML = `
            <div class="conflict-group-header" onclick="toggleConflictGroup('${group.key}')">
                <span class="conflict-group-icon">${group.severity === 'critical' ? '🔴' : group.severity === 'warning' ? '⚠️' : 'ℹ️'}</span>
                <span class="conflict-group-title">${escapeHtml(group.title)}</span>
                <span class="conflict-group-count">(${group.count} issue${group.count > 1 ? 's' : ''})</span>
                <span class="conflict-group-toggle">${group.has_more ? '▼' : '▶'}</span>
            </div>
            <div class="conflict-group-content" id="group-content-${group.key}" style="display: ${group.has_more ? 'none' : 'block'};">
                ${group.items.map(item => `
                    <div class="conflict-item ${group.severity}">
                        <div class="conflict-message">${escapeHtml(item.message || '')}</div>
                        ${item.suggested_action ? `<div class="conflict-action"><strong>Fix:</strong> ${escapeHtml(item.suggested_action)}</div>` : ''}
                    </div>
                `).join('')}
                ${group.has_more ? `<div class="conflict-more-hint hint">+ ${group.count - 5} more issues (expand to see all)</div>` : ''}
            </div>
        `;
        container.appendChild(groupEl);
    });
}

// NEW: Toggle conflict group expand/collapse
window.toggleConflictGroup = function(groupKey) {
    const content = document.getElementById(`group-content-${groupKey}`);
    if (content) {
        content.style.display = content.style.display === 'none' ? 'block' : 'none';
    }
};

// NEW: Toggle transparency panel
window.toggleTransparencyPanel = function() {
    const panel = document.getElementById('transparency-panel');
    if (panel) {
        panel.classList.toggle('hidden');
    }
};

// Fallback to flat display (existing behavior)
function displayFlatConflicts(data) {
    const container = document.getElementById('conflicts-container');
    if (!container) return;

    container.innerHTML = '';
    const errors = data.conflicts?.errors ?? [];
    const warnings = data.conflicts?.warnings ?? [];
    const info = data.conflicts?.info ?? [];
    const nexusSlug = data.nexus_game_slug || 'skyrimspecialedition';

    if (errors.length) {
        container.appendChild(createConflictsSection('Errors', 'error', errors, nexusSlug));
    }
    if (warnings.length) {
        container.appendChild(createConflictsSection('Warnings', 'warning', warnings, nexusSlug));
    }
    if (info.length) {
        container.appendChild(createConflictsSection('Info', 'info', info, nexusSlug));
    }
}

function createConflictsSection(title, type, conflicts, nexusGameSlug) {
    const section = document.createElement('div');
    section.className = `conflicts-section ${type}`;
    section.dataset.severity = type;

    const header = document.createElement('h4');
    header.textContent = title;
    section.appendChild(header);

    // Grouping Logic: Combine identical solutions into single "Smart Cards"
    const groups = {};
    const singles = [];

    conflicts.forEach(conflict => {
        const action = conflict.suggested_action;
        // Group errors/warnings if they share a specific solution string
        if (action && (type === 'error' || type === 'warning')) {
            if (!groups[action]) {
                groups[action] = [];
            }
            groups[action].push(conflict);
        } else {
            singles.push(conflict);
        }
    });

    // Process groups: if a group has only 1 item, treat it as a single
    Object.keys(groups).forEach(key => {
        if (groups[key].length === 1) {
            singles.push(groups[key][0]);
            delete groups[key];
        }
    });

    // Render Groups (Smart Cards)
    Object.keys(groups).forEach(actionKey => {
        const groupItems = groups[actionKey];
        const first = groupItems[0];

        const item = document.createElement('div');
        item.className = `conflict-item ${type} conflict-group-item`;

        // Badges
        const badgeWrap = document.createElement('div');
        badgeWrap.className = 'conflict-badges';
        const badge = document.createElement('span');
        badge.className = 'conflict-type-badge';
        badge.textContent = 'Shared Solution';
        badgeWrap.appendChild(badge);

        // Check if all have same type
        const allSameType = groupItems.every(c => c.type === first.type);
        if (allSameType && first.type) {
            const typeLabel = CONFLICT_TYPE_LABELS[first.type] || first.type;
            const typeBadge = document.createElement('span');
            typeBadge.className = 'conflict-type-badge';
            typeBadge.style.marginLeft = '4px';
            typeBadge.textContent = typeLabel;
            badgeWrap.appendChild(typeBadge);
        }
        item.appendChild(badgeWrap);

        // Action (The Solution) - Prominent
        const actionDiv = document.createElement('div');
        actionDiv.className = 'conflict-action-group';

        const parseMd = (window.marked && typeof marked.parse === 'function') ? (s) => marked.parse(s) : (window.marked && typeof marked === 'function') ? (s) => marked(s) : null;
        let actionHtml = actionKey;
        if (parseMd) {
            try { actionHtml = linkify(parseMd(actionKey)); } catch (_) { actionHtml = linkify(actionKey); }
        } else {
            actionHtml = linkify(actionKey);
        }
        // Remove wrapping <p> from marked if present
        actionHtml = actionHtml.replace(/^<p>|<\/p>$/g, '');

        actionDiv.innerHTML = `<span style="color:var(--accent-primary)">Solution:</span> ${actionHtml}`;
        item.appendChild(actionDiv);

        // Affected Mods List
        const modList = document.createElement('div');
        modList.className = 'conflict-group-mods';

        const modNames = groupItems.map(c => c.affected_mod).filter(Boolean);
        const uniqueMods = [...new Set(modNames)];

        modList.innerHTML = `<strong>Applies to ${uniqueMods.length} mods:</strong><br>${uniqueMods.join(', ')}`;
        item.appendChild(modList);

        // Resolved Checkbox (Group level)
        const checkWrap = document.createElement('label');
        checkWrap.className = 'conflict-resolved-check';
        checkWrap.innerHTML = '<input type="checkbox" class="conflict-resolved-cb"> Mark all resolved';
        item.appendChild(checkWrap);

        section.appendChild(item);
    });

    // Render Singles (Standard Cards)
    singles.forEach(conflict => {
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
        if (conflict.occurrence_count && conflict.occurrence_count > 1) {
            const freq = document.createElement('span');
            freq.className = 'conflict-frequency-badge';
            freq.textContent = `Seen ${conflict.occurrence_count} times`;
            freq.title = 'Community reported frequency';
            badgeWrap.appendChild(freq);
        }
        if (badgeWrap.children.length) item.appendChild(badgeWrap);

        const message = document.createElement('p');
        message.className = 'conflict-message';
        const parseMd = (window.marked && typeof marked.parse === 'function') ? (s) => marked.parse(s) : (window.marked && typeof marked === 'function') ? (s) => marked(s) : null;
        if (parseMd) {
            try {
                message.innerHTML = linkify(parseMd(conflict.message || ''));
            } catch (_) {
                message.innerHTML = linkify(escapeHtml(conflict.message || ''));
            }
        } else {
            message.innerHTML = linkify(escapeHtml(conflict.message || ''));
        }
        item.appendChild(message);

        if (conflict.suggested_action) {
            const action = document.createElement('div');
            action.className = 'conflict-action';
            if (parseMd) {
                try {
                    action.innerHTML = linkify(parseMd(conflict.suggested_action));
                } catch (_) {
                    action.innerHTML = linkify(escapeHtml(conflict.suggested_action));
                }
            } else {
                action.innerHTML = linkify(escapeHtml(conflict.suggested_action));
            }
            item.appendChild(action);
        }

        const modName = conflict.affected_mod;
        if (modName) item.dataset.affectedMod = modName;
        if (conflict.related_mod) item.dataset.relatedMod = conflict.related_mod;

        const checkWrap = document.createElement('label');
        checkWrap.className = 'conflict-resolved-check';
        checkWrap.innerHTML = '<input type="checkbox" class="conflict-resolved-cb"> Resolved';
        item.appendChild(checkWrap);

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

function renderNextActions(nextActions) {
    const section = document.getElementById('next-actions-section');
    const content = document.getElementById('next-actions-content');
    if (!section || !content) return;
    const items = Array.isArray(nextActions) ? nextActions : [];
    if (items.length === 0) {
        section.classList.add('hidden');
        content.innerHTML = '';
        return;
    }
    section.classList.remove('hidden');
    content.innerHTML = items.map(a => {
        const actions = Array.isArray(a.actions) ? a.actions : [];
        const buttons = actions.map(btn => {
            const label = escapeHtml(btn.label || 'Do');
            const payload = escapeHtml(JSON.stringify(btn));
            return `<button type="button" class="secondary-button next-action-btn" data-next-action="${payload}" style="margin-right:8px;margin-top:6px;">${label}</button>`;
        }).join('');
        return `
            <div class="mod-warning mod-warning-${escapeHtml(a.kind || 'info')}" style="margin-top:10px;">
                <div style="font-weight:600;">${escapeHtml(a.title || '')}</div>
                <div class="hint" style="margin-top:4px;">${escapeHtml(a.summary || '')}</div>
                <div style="margin-top:8px;">${buttons}</div>
            </div>
        `;
    }).join('');

    content.querySelectorAll('.next-action-btn').forEach(el => {
        el.addEventListener('click', async () => {
            let cfg = null;
            try { cfg = JSON.parse(el.getAttribute('data-next-action') || 'null'); } catch (_) { }
            if (!cfg || !cfg.type) return;
            if (cfg.type === 'link' && cfg.url) {
                window.open(cfg.url, '_blank', 'noopener');
                return;
            }
            if (cfg.type === 'tab' && cfg.target) {
                document.querySelector(`.main-tab[data-tab="${cfg.target}"]`)?.click();
                return;
            }
            if (cfg.type === 'scroll' && cfg.target) {
                document.getElementById(cfg.target)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                return;
            }
            if (cfg.type === 'filter' && cfg.value) {
                const v = cfg.value;
                const fe = document.getElementById('filter-errors');
                const fw = document.getElementById('filter-warnings');
                const fi = document.getElementById('filter-info');
                if (v === 'errors') { if (fe) fe.checked = true; if (fw) fw.checked = false; if (fi) fi.checked = false; }
                if (v === 'warnings') { if (fe) fe.checked = false; if (fw) fw.checked = true; if (fi) fi.checked = false; }
                applyConflictFilters();
                return;
            }
            if (cfg.type === 'client' && cfg.value) {
                if (cfg.value === 'focus_mod_search') {
                    document.getElementById('mod-search-input')?.focus();
                    return;
                }
                if (cfg.value === 'share_link') {
                    copyShareLink();
                    return;
                }
                if (cfg.value === 'set_masterlist_latest') {
                    const el = document.getElementById('masterlist-version');
                    if (el) el.value = '';
                    return;
                }
                if (cfg.value === 'refresh_masterlist') {
                    document.getElementById('refresh-masterlist-btn')?.click();
                    return;
                }
            }
            if (cfg.type === 'suggest' && cfg.value) {
                // Minimal wiring: prompt user toward existing tools.
                if (cfg.value === 'search_solutions') {
                    const q = document.getElementById('results-search-input')?.value?.trim();
                    if (elements.chatInput && hasPaidAccess(currentUserTier)) {
                        elements.chatInput.value = q ? `Search solutions for: ${q}` : 'Search solutions for the most severe issue above.';
                        elements.chatInput.focus();
                    } else {
                        document.querySelector('.main-tab[data-tab="community"]')?.click();
                    }
                    return;
                }
            }
        });
    });
}

let isAnalyzing = false;

/**
 * Send mod list to server for analysis and display results.
 */
async function analyzeModList() {
    if (isAnalyzing) return;
    if (!elements.modListInput) {
        console.error('SkyModderAI: mod list textarea not found');
        return;
    }

    const modList = elements.modListInput.value.trim();
    // No minimum mod count: 1 or 2 mods (or any number) is fine.
    if (!modList) {
        showToast('Please enter at least one mod.', 'warning');
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
            showToast(error.error || 'Analysis failed', 'error');
            hideLoading();
            isAnalyzing = false;
            return;
        }
        {
            const data = await response.json();
            if (!elements.conflictsContainer) return;

            elements.resultsPanel?.classList.remove('limit-reached');

            // NEW: Populate confidence badge from metadata
            if (data.metadata && data.metadata.confidence) {
                const confidenceValue = Math.round(data.metadata.confidence * 100);
                const confidenceEl = document.getElementById('confidence-value');
                if (confidenceEl) {
                    confidenceEl.textContent = confidenceValue;
                }
                // Update badge color based on confidence
                const badgeEl = document.getElementById('confidence-badge');
                if (badgeEl) {
                    badgeEl.className = 'confidence-badge confidence-' +
                        (confidenceValue >= 80 ? 'high' : confidenceValue >= 60 ? 'medium' : 'low');
                }
            }

            // NEW: Populate transparency panel
            if (data.metadata) {
                populateTransparencyPanel(data.metadata);
            }

            // NEW: Use consolidated conflicts if available
            const consolidated = data.consolidated;
            if (consolidated && consolidated.groups) {
                // Use consolidated hierarchical display
                displayConsolidatedConflicts(consolidated);
            } else {
                // Fallback to flat display
                displayFlatConflicts(data);
            }

            // Check for empty conflicts (for success state)
            const errors = data.conflicts?.errors || [];
            const warnings = data.conflicts?.warnings || [];
            const info = data.conflicts?.info || [];
            
            if (errors.length === 0 && warnings.length === 0 && info.length === 0) {
                elements.conflictsContainer.innerHTML = `
                    <div class="success-state">
                        <div class="success-icon">✓</div>
                        <h3>All Clear</h3>
                        <p>No known conflicts found in your load order.</p>
                        <p class="hint" style="margin-top:0.5rem">Samson is watching. You are good to go.</p>
                    </div>
                `;
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

            // Store analysis result in userContext
            userContext.setAnalysisResult(data);

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
            updateModCounter({ skipAutoAnalyze: true });

            // Trigger AI Strategic Summary if enabled
            if (hasPaidAccess(currentUserTier) && aiChatEnabled) {
                generateAiSummary(data.ai_context || data.report, data.game);
            }

            const canChat = hasPaidAccess(currentUserTier) && aiChatEnabled;
            if (elements.chatSection) elements.chatSection.classList.toggle('hidden', !canChat);
            if (canChat && elements.chatMessages) {
                elements.chatMessages.innerHTML = '';
                appendChatMessage('assistant', "Hi! I'm here to help with your load order. Ask me about any conflict above, how to fix it, or what to do next. I have your full analysis—just ask.");
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
                // Auto-scroll to results after analysis (Priority 3B)
                autoScrollToResults();
            }

            // Apply Priority 3C & 3D enhancements to results
            setTimeout(() => {
                colorCodeConflictItems();
                addQuickFixChips();
            }, 200); // Small delay to ensure DOM is ready
        }
    } catch (error) {
        console.error('Analysis error:', error);
        showToast('Analysis failed. Please check your connection and try again.', 'error');
    } finally {
        isAnalyzing = false;
        hideLoading();
    }
}

async function generateAiSummary(context, game) {
    const container = document.getElementById('ai-summary-section');
    if (!container) return;

    container.classList.remove('hidden');
    container.innerHTML = '<div class="ai-summary-loading"><span class="spinner-small"></span> Generating Strategic Plan...</div>';

    try {
        const res = await fetch('/api/analyze/summary', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ context, game })
        });
        const data = await res.json();
        if (data.summary) {
            const parseMd = (window.marked && typeof marked.parse === 'function') ? (s) => marked.parse(s) : (s) => escapeHtml(s);
            container.innerHTML = `<div class="ai-summary-content">${parseMd(data.summary)}</div>`;
        } else {
            container.classList.add('hidden');
        }
    } catch (e) {
        console.error("AI Summary failed", e);
        container.classList.add('hidden');
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
    p.innerHTML = role === 'assistant' ? linkify(parseMd(String(text || ''))) : escapeHtml(String(text || ''));
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
    const agentInput = document.getElementById('agent-input'); // Support agent window input
    const msg = input?.value?.trim();
    if (!msg || !elements.chatMessages) return;
    input.value = '';
    appendChatMessage('user', msg);
    if (btn) btn.disabled = true;
    try {
        const gameSelect = document.getElementById('game-select');
        const game = (gameSelect && gameSelect.value) ? gameSelect.value : 'skyrimse';
        const modList = parseModListFromTextarea();
        const pageContext = capturePageContext();
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: msg,
                context: currentReport || '',
                page_context: pageContext,
                game,
                mod_list: modList
            })
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
        const emailInput = document.getElementById('checkout-email');
        if (emailInput && currentUserEmail) {
            emailInput.value = currentUserEmail;
        }
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
    showToast(message, 'success');
}

function initToastSystem() {
    const style = document.createElement('style');
    style.textContent = `
        .toast-container {
            position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
            display: flex; flex-direction: column; gap: 8px; z-index: 10002;
            pointer-events: none;
        }
        .toast {
            background: var(--card-bg); color: var(--text-primary);
            border: 1px solid var(--border-color); border-radius: 8px;
            padding: 12px 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            font-size: 0.95rem; opacity: 0; transform: translateY(10px);
            transition: opacity 0.3s, transform 0.3s;
            pointer-events: auto; display: flex; align-items: center; gap: 12px;
        }
        .toast.visible { opacity: 1; transform: translateY(0); }
        .toast-success { border-left: 4px solid var(--accent-primary); }
        .toast-error { border-left: 4px solid #ef4444; }
        .toast-warning { border-left: 4px solid #f59e0b; }
    `;
    document.head.appendChild(style);
    const container = document.createElement('div');
    container.className = 'toast-container';
    container.id = 'toast-container';
    document.body.appendChild(container);
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return; // Should be initialized
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    // Trigger reflow
    void toast.offsetWidth;
    toast.classList.add('visible');
    setTimeout(() => {
        toast.classList.remove('visible');
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}
window.showToast = showToast;

function trackClientActivity(eventType, eventData = {}) {
    fetch('/api/activity/track', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_type: eventType, event_data: eventData })
    }).catch(() => { });
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
        showToast('Please enter a valid email.', 'warning');
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
        showToast(err.message || 'Checkout failed. Please try again.', 'error');
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
        showToast('No suggested load order available. Run analysis first.', 'warning');
        return;
    }
    const text = currentSuggestedOrder.map(name => '*' + name).join('\n');
    navigator.clipboard.writeText(text).then(() => {
        if (elements.copyLoadOrderBtn) {
            const orig = elements.copyLoadOrderBtn.textContent;
            elements.copyLoadOrderBtn.textContent = 'Copied!';
            setTimeout(() => { elements.copyLoadOrderBtn.textContent = orig; }, 2000);
        }
    }).catch(() => showToast('Failed to copy.', 'error'));
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
        showToast('No report to download. Run analysis first.', 'warning');
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
    a.download = `skymodderai-report-${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    URL.revokeObjectURL(a.href);
}

/**
 * Download analysis payload as JSON for tooling/history pipelines.
 */
function downloadReportJson() {
    if (!currentAnalysisData) {
        showToast('No report JSON available. Run analysis first.', 'warning');
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
    a.download = `skymodderai-report-${new Date().toISOString().slice(0, 10)}.json`;
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
        showToast('Could not read clipboard. Paste with Ctrl+V.', 'error');
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
            showToast(data.error || `Could not load sample (${res.status}).`, 'error');
            return;
        }
        const modList = (data.mod_list != null) ? String(data.mod_list) : '';
        modListInput.value = modList;
        updateModCounter();
        if (modList.length === 0) {
            showToast(`No sample list for "${game}".`, 'info');
        }
    } catch (e) {
        console.error('Failed to load sample:', e);
        showToast('Could not load sample list.', 'error');
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
        showToast('No report to copy.', 'warning');
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
            showToast('Failed to copy to clipboard.', 'error');
        });
}

// -------------------------------------------------------------------
// Event Listeners
// -------------------------------------------------------------------
function initGlobalEventListeners() {
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
                userContext.setAnalysisResult(null); // Clear analysis to hide context trail
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

    if (elements.pasteBtn) {
        elements.pasteBtn.addEventListener('click', pasteFromClipboard);
    }
    const shareLinkBtn = document.getElementById('share-link-btn');
    if (shareLinkBtn) shareLinkBtn.addEventListener('click', copyShareLink);

    if (elements.sampleBtn) {
        elements.sampleBtn.addEventListener('click', loadSampleList);
    }

    if (saveListBtn) saveListBtn.addEventListener('click', saveListToStorage);
    if (loadSavedSelect) {
        loadSavedSelect.addEventListener('change', loadSavedList);
        (async () => {
            await refreshSavedListsSource();
            populateLoadSavedSelect();
        })();
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
                showToast('Could not read file. Try a .txt file.', 'error');
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
}

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
            } catch (_) { }
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
    const statusEl = document.getElementById('game-folder-scan-status');
    if (!dropZone || !fileInput) return;

    function updateTierUi() {
    }

    const handleFiles = async (fileList) => {
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
                    } catch (_) { }
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
                        if (statusEl) showToast('Your browser selected files, not a folder tree. Choose the top-level folder.', 'warning');
                    }
                    await runGameFolderScan(withPath);
                } else {
                    showToast('Drop a folder (not individual files).', 'warning');
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
const SAVED_LISTS_KEY = 'skymodderai_saved_lists';
let cloudSavedLists = null;
let cloudSavedItems = null;

async function fetchCloudSavedLists() {
    try {
        const res = await fetch('/api/list-preferences', { method: 'GET' });
        if (!res.ok) return null;
        const data = await res.json().catch(() => null);
        if (data && data.success) {
            cloudSavedItems = Array.isArray(data.items) ? data.items : null;
            if (data.lists && typeof data.lists === 'object') {
                return data.lists;
            }
        }
        return null;
    } catch (_) {
        return null;
    }
}

async function upsertCloudSavedList(name, list, game) {
    try {
        const gameVersion = document.getElementById('game-version')?.value || '';
        const masterlistVersion = document.getElementById('masterlist-version')?.value || '';

        // Include analysis snapshot if available
        const analysisSnapshot = userContext.lastAnalysisResult ? {
            summary: {
                errors: userContext.lastAnalysisResult.conflicts?.errors?.length || 0,
                warnings: userContext.lastAnalysisResult.conflicts?.warnings?.length || 0,
                info: userContext.lastAnalysisResult.conflicts?.info?.length || 0,
                total: (userContext.lastAnalysisResult.conflicts?.errors?.length || 0) +
                    (userContext.lastAnalysisResult.conflicts?.warnings?.length || 0) +
                    (userContext.lastAnalysisResult.conflicts?.info?.length || 0)
            },
            plugin_limit_warning: userContext.lastAnalysisResult.plugin_limit_warning,
            suggested_load_order: userContext.lastAnalysisResult.suggested_load_order,
            system_impact: userContext.lastAnalysisResult.system_impact,
            mod_warnings: userContext.lastAnalysisResult.mod_warnings,
            saved_at: new Date().toISOString()
        } : null;

        const res = await fetch('/api/list-preferences', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name,
                list,
                game,
                game_version: gameVersion || undefined,
                masterlist_version: masterlistVersion || undefined,
                source: 'analyze',
                analysis_snapshot: analysisSnapshot,
            })
        });
        if (!res.ok) return false;
        const data = await res.json().catch(() => null);
        return !!(data && data.success);
    } catch (_) {
        return false;
    }
}

function getSavedListsUnified() {
    if (cloudSavedLists && typeof cloudSavedLists === 'object') return cloudSavedLists;
    return getSavedLists();
}

async function refreshSavedListsSource() {
    cloudSavedLists = await fetchCloudSavedLists();
}

function getSavedLists() {
    try {
        // Try new key first, then fall back to old key for backward compatibility
        const raw = localStorage.getItem(SAVED_LISTS_KEY) || localStorage.getItem('modcheck_saved_lists');
        return raw ? JSON.parse(raw) : {};
    } catch (_) { return {}; }
}
function saveListToStorage() {
    const list = elements.modListInput?.value?.trim();
    if (!list) { showToast('No mod list to save.', 'warning'); return; }
    const name = prompt('Name this list (e.g. "Skyrim 2024 build"):');
    if (!name || !name.trim()) return;
    const game = elements.gameSelect?.value || 'skyrimse';
    (async () => {
        const okCloud = await upsertCloudSavedList(name.trim(), list, game);
        if (okCloud) {
            await refreshSavedListsSource();
            populateLoadSavedSelect();
            showToast('List saved.', 'success');
            return;
        }
        const saved = getSavedLists();
        saved[name.trim()] = { list, game, savedAt: new Date().toISOString() };
        try {
            localStorage.setItem(SAVED_LISTS_KEY, JSON.stringify(saved));
            populateLoadSavedSelect();
            showToast('List saved locally.', 'success');
        } catch (e) { showToast('Could not save list.', 'error'); }
    })();
}
function populateLoadSavedSelect() {
    if (!loadSavedSelect) return;
    const saved = getSavedListsUnified();
    const keys = Object.keys(saved).sort();
    loadSavedSelect.innerHTML = '<option value="">Load saved…</option>';

    // Prefer structured cloud items for grouping, but always fall back to legacy dict.
    const items = Array.isArray(cloudSavedItems) ? cloudSavedItems : null;
    if (items && items.length > 0) {
        const byGroup = {};
        items.forEach(it => {
            const g = it.game || 'unknown';
            const gv = it.game_version || '';
            const mv = it.masterlist_version || '';
            const label = `${g}${gv ? ` • ${gv}` : ''}${mv ? ` • LOOT ${mv}` : ''}`;
            if (!byGroup[label]) byGroup[label] = [];
            byGroup[label].push(it);
        });
        Object.keys(byGroup).sort().forEach(groupLabel => {
            const og = document.createElement('optgroup');
            og.label = groupLabel;
            byGroup[groupLabel]
                .sort((a, b) => String(a.name || '').localeCompare(String(b.name || '')))
                .forEach(it => {
                    const opt = document.createElement('option');
                    opt.value = it.name;
                    opt.textContent = it.name;
                    og.appendChild(opt);
                });
            loadSavedSelect.appendChild(og);
        });
        return;
    }

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
    const saved = getSavedListsUnified();
    const item = saved[key];
    if (!item || !item.list) { showToast('List not found.', 'error'); return; }
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
    (async () => {
        await refreshSavedListsSource();
        populateLoadSavedSelect();
    })();
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
            showToast('Could not read file. Try a .txt file.', 'error');
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
    function updateForTab(target) {
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
            if (target === 'openclaw') {
                // OpenCLAW panel - redirect to dashboard or show info
                console.log('OpenCLAW tab selected');
            }
            if (target === 'gameplay') {
                if (window.GameplayUI) window.GameplayUI.init('gameplay-container');
                else if (window.WalkthroughUI) window.WalkthroughUI.init('gameplay-container');
            }
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

    if (analyzeBtn) analyzeBtn.addEventListener('click', runDevAnalyze);
    if (sampleBtn) sampleBtn.addEventListener('click', showDevSampleReport);
    if (copyBtn) copyBtn.addEventListener('click', copyDevReport);
    if (downloadBtn) downloadBtn.addEventListener('click', downloadDevReport);

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

function showDevSampleReport() {
    const resultsEl = document.getElementById('dev-results');
    const reportEl = document.getElementById('dev-report-content');
    if (!resultsEl || !reportEl) return;
    reportEl.innerHTML = (typeof marked !== 'undefined' ? marked.parse(DEV_SAMPLE_REPORT) : escapeHtml(DEV_SAMPLE_REPORT).replace(/\n/g, '<br>'));
    resultsEl.classList.remove('hidden');
}

function copyDevReport() {
    const reportEl = document.getElementById('dev-report-content');
    if (!reportEl?.textContent) return;
    navigator.clipboard.writeText(reportEl.textContent).then(() => {
        const btn = document.getElementById('dev-copy-report-btn');
        if (btn) { btn.textContent = 'Copied!'; setTimeout(() => { btn.textContent = 'Copy'; }, 1500); showToast('Report copied.', 'success'); }
    }).catch(() => showToast('Could not copy.', 'error'));
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
    const textExt = ['.psc', '.ini', '.json', '.txt', '.md', '.toml', '.yaml', '.yml'];
    const binExt = ['.esp', '.esm', '.esl'];
    const added = [];
    for (let i = 0; i < Math.min(fileList.length, 25); i++) {
        const f = fileList[i];
        const name = (f.name || '').toLowerCase();
        const isText = textExt.some(e => name.endsWith(e)) || name.includes('readme') || name.includes('license');
        const isBin = binExt.some(e => name.endsWith(e));

        if (!isText && !isBin) continue;

        try {
            let content = '';
            if (isBin) {
                content = `(Binary plugin file: ${f.name})`;
            } else {
                const text = await f.text();
                content = text.slice(0, 15000);
            }
            added.push({ path: f.webkitRelativePath || f.name, content: content });
        } catch (_) { }
    }
    devUploadedFiles = [...devUploadedFiles, ...added].slice(0, 25);
    renderDevFileList();
}

async function runDevAnalyze() {

    const repoInput = document.getElementById('dev-repo-url');
    const pasteInput = document.getElementById('dev-paste-input');
    const activeTab = document.querySelector('.dev-input-tab.active');
    const mode = activeTab?.dataset.mode || 'repo';

    const game = (document.getElementById('dev-game-select')?.value || 'skyrimse');
    const statusEl = document.getElementById('dev-status');
    const resultsEl = document.getElementById('dev-results');
    const reportEl = document.getElementById('dev-report-content');
    const analyzeBtn = document.getElementById('dev-analyze-btn');
    if (!statusEl || !resultsEl || !reportEl) return;

    let payload = { game };
    let isValid = false;

    if (mode === 'repo') {
        const repoUrl = (repoInput?.value || '').trim();
        if (repoUrl && repoUrl.includes('github.com')) {
            payload.repo_url = repoUrl;
            isValid = true;
            statusEl.textContent = 'Fetching repo…';
        } else {
            statusEl.textContent = 'Please enter a valid GitHub URL.';
        }
    } else if (mode === 'upload') {
        if (devUploadedFiles.length > 0) {
            payload.files = devUploadedFiles;
            isValid = true;
            statusEl.textContent = 'Analyzing uploaded files…';
        } else {
            statusEl.textContent = 'Please upload at least one file.';
        }
    } else if (mode === 'paste') {
        const pasteContent = (pasteInput?.value || '').trim();
        if (pasteContent.length > 20) {
            payload.files = [{ path: 'pasted.txt', content: pasteContent }];
            isValid = true;
            statusEl.textContent = 'Analyzing pasted code…';
        } else {
            statusEl.textContent = 'Please paste code (at least 20 chars).';
        }
    }

    if (!isValid) {
        statusEl.classList.remove('hidden');
        return;
    }

    statusEl.classList.remove('hidden');
    resultsEl.classList.add('hidden');
    if (analyzeBtn) analyzeBtn.disabled = true;

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
    } finally {
        if (analyzeBtn) analyzeBtn.disabled = false;
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

        // Automation: Auto-build when preferences change
        container.querySelectorAll('select').forEach(s => {
            s.addEventListener('change', () => runBuildList());
        });
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
    const proSetups = document.getElementById('build-list-pro-setups')?.checked;
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
            showToast(data.error || 'Failed to build list.', 'error');
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
            setupsEl.innerHTML = '<h4>AI setups</h4>' + setups.map(s => `
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
        showToast('Network error. Try again.', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Generate List';
    }
}

function copyBuildListAsPluginsTxt() {
    const lines = lastBuiltListMods.map(m => '*' + (m.name || '').replace(/^[\*\+\-]?\s*/, ''));
    const text = lines.join('\n');
    if (!text) { showToast('No list to copy.', 'warning'); return; }
    navigator.clipboard.writeText(text).then(() => showToast('Copied to clipboard.', 'success')).catch(() => showToast('Could not copy.', 'error'));
}

function sendBuildListToAnalyze(options = {}) {
    const autoAnalyze = !!options.autoAnalyze;
    const focusAnalyze = options.focusAnalyze !== false;
    const lines = lastBuiltListMods.map(m => '*' + (m.name || '').replace(/^[\*\+\-]?\s*/, ''));
    const text = lines.join('\n');
    if (!text) { showToast('No list to send.', 'warning'); return; }
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
        if (data.tags && !window.communityTagsLoaded) {
            updateCommunityTagsUI(data.tags);
            window.communityTagsLoaded = true;
        }
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

function updateCommunityTagsUI(tags) {
    // Update post creation dropdown
    const tagSelect = document.getElementById('community-post-tag');
    if (tagSelect) {
        const currentVal = tagSelect.value;
        tagSelect.innerHTML = tags.map(t =>
            `<option value="${escapeHtml(t)}">${escapeHtml(t.charAt(0).toUpperCase() + t.slice(1))}</option>`
        ).join('');
        if (tags.includes(currentVal)) tagSelect.value = currentVal;
    }

    // Update filter buttons
    const filterContainer = document.querySelector('.community-filter-tags');
    if (filterContainer) {
        const currentTag = communityFilterTag;
        let html = `<button type="button" class="community-tag-btn${currentTag === '' ? ' active' : ''}" data-tag="">All</button>`;
        html += tags.map(t => {
            const activeClass = t === currentTag ? ' active' : '';
            return `<button type="button" class="community-tag-btn${activeClass}" data-tag="${escapeHtml(t)}">
                ${escapeHtml(t.charAt(0).toUpperCase() + t.slice(1))}
            </button>`;
        }).join('');
        filterContainer.innerHTML = html;
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
                <div class="community-reply-content">${linkify(escapeHtml(r.content))}</div>
            <button type="button" class="community-report-btn" data-reply="${r.id}">Report</button>
        </div>
    `).join('');
    const voteUp = p.my_vote === 1 ? ' community-vote-active' : '';
    return `
        <article class="community-post-item" data-post-id="${p.id}">
            <div class="community-post-header">
                <span class="community-post-tag community-post-tag-${escapeHtml(p.tag || 'general')}">${escapeHtml((p.tag || 'general').charAt(0).toUpperCase() + (p.tag || 'general').slice(1))}</span>
                <div class="community-post-meta">${escapeHtml(p.user)}${proBadge} · ${formatDate(p.created_at)}</div>
            </div>
            <div class="community-post-content">${linkify(escapeHtml(p.content))}</div>
            <div class="community-post-actions-row">
                <div class="community-votes">
                    <button type="button" class="community-vote-btn community-vote-up${voteUp}" data-post="${p.id}" aria-label="Helpful">▲</button>
                    <span class="community-vote-count" style="margin-left:4px;">${p.votes || 0}</span>
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
            const current = btn.classList.contains('community-vote-active');
            const vote = current ? 0 : 1; // Toggle: if active (1), send 0. If inactive, send 1.
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
            } catch (_) { }
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
            if (content.length < 3) { showToast('Reply must be at least 3 characters.', 'warning'); return; }
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
                } else showToast(data.error || 'Failed to reply', 'error');
            } catch (e) { showToast('Network error', 'error'); }
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
                else showToast(data.error || 'Failed to submit report', 'error');
            } catch (e) {
                showToast('Network error', 'error');
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
            showToast('Post must be at least 3 characters.', 'warning');
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
                showToast(data.error || 'Failed to post', 'error');
                return;
            }
            input.value = '';
            if (countEl) countEl.textContent = '0 / 2000';
            trackClientActivity('community_post', { tag: (tagSelect && tagSelect.value) || 'general' });
            loadCommunityFeed();
        } catch (e) {
            showToast('Network error. Try again.', 'error');
        } finally {
            btn.disabled = false;
        }
    });
    // Use delegation for dynamic tags
    const filterContainer = document.querySelector('.community-filter-tags');
    if (filterContainer) {
        filterContainer.addEventListener('click', (e) => {
            const b = e.target.closest('.community-tag-btn');
            if (!b) return;
            document.querySelectorAll('.community-tag-btn').forEach(x => x.classList.remove('active'));
            b.classList.add('active');
            communityFilterTag = b.dataset.tag || '';
            loadCommunityFeed();
        });
    }
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
    { id: 'scan-hardware', label: 'Scan hardware specs', fn: () => scanSystem() },
    {
        id: 'scan-folder',
        label: 'Scan game folder',
        fn: () => {
            const btn = document.getElementById('game-folder-browse-btn');
            if (btn) btn.click();
            else {
                document.querySelector('.main-tab[data-tab="analyze"]')?.click();
                setTimeout(() => document.getElementById('game-folder-browse-btn')?.click(), 200);
            }
        }
    },
    { id: 'focus-mod-search', label: 'Search mods', fn: () => document.getElementById('mod-search-input')?.focus() },
    { id: 'tab-analyze', label: 'Go to Analyze', fn: () => document.querySelector('.main-tab[data-tab="analyze"]')?.click() },
    { id: 'tab-openclaw', label: 'Go to OpenCLAW', fn: () => document.querySelector('.main-tab[data-tab="openclaw"]')?.click() },
    { id: 'tab-quickstart', label: 'Go to Quick Start', fn: () => document.querySelector('.main-tab[data-tab="quickstart"]')?.click() },
    { id: 'tab-build-list', label: 'Go to Build a List', fn: () => document.querySelector('.main-tab[data-tab="build-list"]')?.click() },
    { id: 'tab-library', label: 'Go to Library', fn: () => document.querySelector('.main-tab[data-tab="library"]')?.click() },
    { id: 'tab-gameplay', label: 'Go to Gameplay', fn: () => document.querySelector('.main-tab[data-tab="gameplay"]')?.click() },
    { id: 'tab-dev', label: 'Go to Dev Tools', fn: () => document.querySelector('.main-tab[data-tab="dev"]')?.click() },
    { id: 'dev-analyze', label: 'Analyze dev project', shortcut: 'Ctrl+Enter', fn: () => { document.querySelector('.main-tab[data-tab="dev"]')?.click(); setTimeout(() => runDevAnalyze(), 100); } },
    { id: 'tab-community', label: 'Go to Community', fn: () => document.querySelector('.main-tab[data-tab="community"]')?.click() },
    { id: 'copy-report', label: 'Copy report', fn: () => copyReport() },
    { id: 'share-link', label: 'Copy share link', fn: () => copyShareLink() },
    { id: 'clear', label: 'Clear mod list', fn: () => elements.clearBtn?.click() },
    { id: 'sample', label: 'Load sample list', fn: () => loadSampleList() },
    { id: 'profile', label: 'Open profile', fn: () => window.location.href = '/profile' },
    { id: 'signup', label: 'Open signup', fn: () => window.location.href = '/signup-pro' },
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
// Theme System
// -------------------------------------------------------------------
const THEMES = {
    'slate': {
        name: 'Slate (Default)',
        colors: {
            '--bg-app': '#0f172a', '--bg-panel': '#1e293b', '--bg-input': '#020617',
            '--text-main': '#f8fafc', '--text-muted': '#94a3b8', '--border': '#334155',
            '--accent': '#38bdf8', '--accent-hover': '#0ea5e9', '--accent-text': '#0f172a',
            '--accent-rgb': '56, 189, 248',
            '--danger': '#ef4444', '--success': '#22c55e', '--warning': '#f59e0b',
            '--shadow-sm': '0 1px 2px 0 rgb(0 0 0 / 0.05)',
            '--shadow-md': '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -1px rgb(0 0 0 / 0.06)'
        }
    },
    'obsidian': {
        name: 'Obsidian',
        colors: {
            '--bg-app': '#111111', '--bg-panel': '#1e1e1e', '--bg-input': '#252525',
            '--text-main': '#e0e0e0', '--text-muted': '#888888', '--border': '#333333',
            '--accent': '#a855f7', '--accent-hover': '#9333ea', '--accent-text': '#ffffff',
            '--accent-rgb': '168, 85, 247',
            '--danger': '#ff5555', '--success': '#4caf50', '--warning': '#ff9800',
            '--shadow-sm': 'none', '--shadow-md': '0 4px 12px rgba(0,0,0,0.5)'
        }
    },
    'nexus': {
        name: 'Nexus',
        colors: {
            '--bg-app': '#222222', '--bg-panel': '#2b2b2b', '--bg-input': '#1a1a1a',
            '--text-main': '#ffffff', '--text-muted': '#9b9b9b', '--border': '#404040',
            '--accent': '#da8e35', '--accent-hover': '#e69d45', '--accent-text': '#000000',
            '--accent-rgb': '218, 142, 53',
            '--danger': '#d32f2f', '--success': '#388e3c', '--warning': '#fbc02d',
            '--shadow-sm': '0 1px 3px rgba(0,0,0,0.3)', '--shadow-md': '0 4px 6px rgba(0,0,0,0.4)'
        }
    },
    'dawn': {
        name: 'Dawn',
        colors: {
            '--bg-app': '#f8fafc', '--bg-panel': '#ffffff', '--bg-input': '#f1f5f9',
            '--text-main': '#0f172a', '--text-muted': '#64748b', '--border': '#e2e8f0',
            '--accent': '#0ea5e9', '--accent-hover': '#0284c7', '--accent-text': '#ffffff',
            '--accent-rgb': '14, 165, 233',
            '--danger': '#ef4444', '--success': '#22c55e', '--warning': '#f59e0b',
            '--shadow-sm': '0 1px 2px 0 rgb(0 0 0 / 0.05)',
            '--shadow-md': '0 4px 6px -1px rgb(0 0 0 / 0.1)'
        }
    }
};

function applyTheme(key) {
    const t = THEMES[key] || THEMES['slate'];
    const root = document.documentElement;

    // Set data-theme attribute for CSS hooks
    root.setAttribute('data-theme', key);

    // Apply CSS variables from theme
    for (const [k, v] of Object.entries(t.colors)) {
        root.style.setProperty(k, v);
    }
    localStorage.setItem('skymodder_theme', key);
    const sel = document.getElementById('theme-select');
    if (sel) sel.value = key;
}

function initModernTheme() {
    // Inject a cohesive, modern color scheme and UI reset
    const style = document.createElement('style');
    style.textContent = `
        :root {
            /* Spacing & Radius (Shared) */
            --radius-sm: 6px;
            --radius-md: 8px;
            --radius-lg: 12px;

            /* Layout Lane */
            --content-width: 1200px;
        }

        /* Layout Stability & Reset */
        html {
            scrollbar-gutter: stable;
            overflow-x: hidden;
        }
        *, *::before, *::after {
            box-sizing: border-box;
        }

        body {
            background-color: var(--bg-app);
            color: var(--text-main);
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            -webkit-font-smoothing: antialiased;
            transition: background-color 0.3s, color 0.3s;
            display: flex;
            flex-direction: column;
            min-height: 100vh;
            width: 100%;
            margin: 0;
        }

        /* Universal Layout Lane */
        main {
            flex: 1;
            width: 100%;
            max-width: var(--content-width);
            margin: 0 auto;
            padding: 2rem 1.5rem;
        }

        /* Map existing variables to new scheme if they exist */
        :root {
            --card-bg: var(--bg-panel);
            --text-primary: var(--text-main);
            --text-secondary: var(--text-muted);
            --border-color: var(--border);
            --accent-primary: var(--accent);
        }

        /* Unified Component Styling */
        .card, .tab-panel, .modal-content, .library-card, .gp-layout {
            background-color: var(--bg-panel);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-sm);
            padding: 2.5rem;
            margin-bottom: 2rem;
            animation: fadeIn 0.3s ease-out;
        }

        @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }

        /* Typography Standardization */
        h1, h2, h3, h4, h5, h6 { color: var(--text-main); margin-top: 0; line-height: 1.3; }
        h2 { font-size: 1.75rem; font-weight: 700; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border); }
        h3 { font-size: 1.25rem; font-weight: 600; margin: 2rem 0 1rem 0; }
        p { margin-bottom: 1rem; line-height: 1.6; color: var(--text-muted); max-width: 75ch; }
        ul, ol { margin-bottom: 1.5rem; padding-left: 1.5rem; color: var(--text-muted); }
        li { margin-bottom: 0.5rem; line-height: 1.6; }
        a { color: var(--accent); text-decoration: none; transition: color 0.2s; }
        a:hover { color: var(--accent-hover); text-decoration: underline; }

        /* Input Standardization */
        input[type="text"], input[type="email"], input[type="password"], input[type="search"], textarea, select {
            width: 100%;
            padding: 0.75rem 1rem;
            background: var(--bg-input);
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            color: var(--text-main);
            font-family: inherit;
            font-size: 0.95rem;
            transition: all 0.2s;
            box-sizing: border-box;
        }
        input:focus, textarea:focus, select:focus {
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.15);
            outline: none;
        }
        label { display: block; margin-bottom: 0.5rem; font-weight: 500; color: var(--text-main); font-size: 0.9rem; }

        /* Button Standardization */
        button, .primary-button, .secondary-button, .danger-button {
            height: 40px;
            padding: 0 1.25rem;
            border-radius: var(--radius-md);
            font-weight: 600;
            font-size: 0.9rem;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
            cursor: pointer;
            border: 1px solid transparent;
        }

        .primary-button {
            background-color: var(--accent);
            color: var(--accent-text);
        }
        .primary-button:hover {
            background-color: var(--accent-hover);
            transform: translateY(-1px);
        }

        .secondary-button {
            background-color: transparent;
            border-color: var(--border);
            color: var(--text-main);
        }
        .secondary-button:hover {
            background-color: rgba(255,255,255,0.05);
            border-color: var(--text-muted);
        }

        .danger-button { background: rgba(239, 68, 68, 0.1); color: var(--danger); border-color: transparent; }
        .danger-button:hover { background: rgba(239, 68, 68, 0.2); }

        /* Result Badges & States */
        .conflict-type-badge {
            background: var(--bg-input); border: 1px solid var(--border);
            color: var(--text-muted); padding: 2px 8px; border-radius: 12px;
            font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;
        }
        .conflict-related-badge {
            background: rgba(56, 189, 248, 0.1); color: var(--accent);
            padding: 2px 8px; border-radius: 12px; font-size: 0.75rem;
        }
        .conflict-frequency-badge {
            background: rgba(139, 92, 246, 0.15); color: var(--accent);
            padding: 2px 8px; border-radius: 12px; font-size: 0.75rem;
            border: 1px solid rgba(139, 92, 246, 0.3); font-weight: 600;
        }
        .success-state {
            text-align: center; padding: 3rem 2rem; background: var(--bg-panel);
            border: 1px solid var(--border); border-radius: var(--radius-lg); margin-bottom: 2rem;
        }
        .success-icon { width: 48px; height: 48px; background: rgba(34, 197, 94, 0.1); color: var(--success); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; margin: 0 auto 1rem auto; }
        .success-state h3 { font-size: 1.25rem; margin-bottom: 0.5rem; color: var(--text-main); }

        /* Dev Tools Polish */
        #dev-drop-zone {
            border: 2px dashed var(--border);
            border-radius: var(--radius-lg);
            padding: 3rem 2rem;
            text-align: center;
            background: var(--bg-input);
            transition: all 0.2s ease;
            cursor: pointer;
            position: relative;
            overflow: hidden;
            margin-bottom: 1.5rem;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 200px;
        }
        #dev-drop-zone:hover, #dev-drop-zone.dev-drop-active {
            border-color: var(--accent);
            background: rgba(56, 189, 248, 0.03);
            transform: scale(1.005);
        }

        /* Gameplay Search Suggestions */
        .gp-search-box { position: relative; }
        .gp-suggestions {
            position: absolute; top: 100%; left: 0; right: 0;
            background: var(--bg-panel); border: 1px solid var(--border);
            border-radius: 0 0 var(--radius-md) var(--radius-md);
            z-index: 100; max-height: 300px; overflow-y: auto;
            box-shadow: var(--shadow-md);
        }
        .gp-suggestion-item {
            padding: 10px 16px; cursor: pointer; border-bottom: 1px solid var(--border);
            display: flex; justify-content: space-between; align-items: center;
            transition: background 0.15s;
        }
        .gp-suggestion-item:last-child { border-bottom: none; }
        .gp-suggestion-item:hover { background: var(--bg-input); }
        .gp-suggestion-type { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }

        .dev-file-chip {
            display: inline-flex;
            align-items: center;
            background: var(--bg-panel);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 6px 12px;
            font-size: 0.9rem;
            margin: 4px;
            box-shadow: var(--shadow-sm);
        }
        .dev-file-remove {
            margin-left: 8px;
            color: var(--text-muted);
            cursor: pointer;
            border: none;
            background: transparent;
            font-size: 1.1rem;
            line-height: 1;
            padding: 0;
            display: flex;
            align-items: center;
        }
        .dev-file-remove:hover { color: var(--danger); }
        #dev-report-content {
            font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
            font-size: 0.95rem;
            line-height: 1.6;
            color: var(--text-main);
            background: var(--bg-input);
            padding: 2rem;
            border-radius: var(--radius-md);
            border: 1px solid var(--border);
            margin-top: 1rem;
            max-width: 900px;
        }
        #dev-report-content h2, #dev-report-content h3 {
            margin-top: 1.5em;
            margin-bottom: 0.75em;
            color: var(--accent);
        }
        #dev-report-content ul {
            padding-left: 1.5em;
            margin-bottom: 1em;
        }
        #dev-report-content li {
            margin-bottom: 0.5em;
        }
        .dev-tabs {
            display: flex;
            gap: 1rem;
            border-bottom: 1px solid var(--border);
            margin-bottom: 1.5rem;
        }
        .dev-input-tab {
            padding: 0.75rem 1rem;
            color: var(--text-muted);
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.2s;
            font-weight: 500;
            background: none;
            border-top: none;
            border-left: none;
            border-right: none;
        }
        .dev-input-tab:hover { color: var(--text-main); }
        .dev-input-tab.active {
            color: var(--accent);
            border-bottom-color: var(--accent);
        }

        /* Responsive / Mobile Polish */
        @media (max-width: 768px) {
            main { padding: 1rem; }
            .card, .tab-panel, .modal-content, .library-card, .gp-layout {
                padding: 1.25rem;
                border-radius: var(--radius-md);
                margin-bottom: 1.5rem;
            }
            h1 { font-size: 1.75rem; }
            h2 { font-size: 1.4rem; }
            h3 { font-size: 1.2rem; }

            .dev-tabs {
                overflow-x: auto;
                white-space: nowrap;
                padding-bottom: 4px;
                margin-bottom: 1rem;
                -webkit-overflow-scrolling: touch;
                scrollbar-width: none;
            }
            .dev-tabs::-webkit-scrollbar { display: none; }

            /* Better touch targets & input sizing */
            button, .primary-button, .secondary-button, .danger-button { min-height: 44px; }
            input, select, textarea { font-size: 16px !important; } /* Prevent iOS zoom */
            .dev-results-header { flex-direction: column; align-items: flex-start; gap: 1rem; }
        }
    `;
    document.head.appendChild(style);

    const saved = localStorage.getItem('skymodder_theme') || 'slate';
    applyTheme(saved);

    // Live Document (PDF-like) Styles
    const docStyle = document.createElement('style');
    docStyle.textContent = `
        .live-doc-container {
            background: #ffffff;
            color: #1e293b;
            padding: 48px;
            border-radius: 2px;
            box-shadow: 0 10px 30px -10px rgba(0,0,0,0.15);
            font-family: 'Georgia', 'Times New Roman', serif;
            line-height: 1.6;
            margin: 0 auto;
            max-width: 850px;
            position: relative;
        }
        body:not(.light-mode) .live-doc-container {
            background: #1e293b; color: #e2e8f0; border: 1px solid #334155;
        }
        .live-doc-header {
            border-bottom: 2px solid var(--accent); margin-bottom: 32px; padding-bottom: 16px;
            display: flex; justify-content: space-between; align-items: flex-end;
        }
        .live-doc-title {
            font-size: 24px; font-weight: 700; color: var(--text-main);
            font-family: 'Inter', sans-serif; letter-spacing: -0.02em;
        }
        .live-doc-meta {
            font-size: 13px; color: var(--text-muted); font-family: 'Inter', sans-serif;
            text-transform: uppercase; letter-spacing: 0.05em;
        }
        .live-doc-intro {
            font-style: italic; color: var(--text-muted); margin-bottom: 32px;
            padding-bottom: 24px; border-bottom: 1px solid var(--border);
        }
        .live-doc-step {
            margin-bottom: 20px; padding: 4px 0 4px 16px; border-left: 3px solid var(--border);
            transition: all 0.3s ease;
        }
        .live-doc-step:hover { border-left-color: var(--accent); background: rgba(255,255,255,0.02); }
        .live-doc-step.severity-error { border-left-color: var(--danger); }
        .live-doc-step.severity-warning { border-left-color: var(--warning); }
        .live-doc-num {
            font-family: 'Inter', sans-serif; font-weight: 700; color: var(--accent);
            margin-right: 8px; font-size: 0.9em;
        }
        .live-doc-content { display: inline; }
        .live-doc-content strong { font-weight: 600; color: var(--text-main); }
        .live-doc-content a { color: var(--accent); text-decoration: underline; text-underline-offset: 3px; }
        .live-doc-ai-update {
            margin: 32px 0; padding: 24px; background: rgba(56, 189, 248, 0.05);
            border: 1px dashed var(--accent); border-radius: 8px; position: relative;
            animation: doc-fade-in 0.5s ease-out;
        }
        @keyframes doc-fade-in { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .live-doc-ai-badge {
            position: absolute; top: -10px; left: 20px; background: var(--bg-panel); color: var(--accent);
            padding: 0 8px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;
            border: 1px solid var(--accent); border-radius: 4px;
        }
    `;
    document.head.appendChild(docStyle);
}

// -------------------------------------------------------------------
// Marketing Revamp: Donation Header & Footer
// -------------------------------------------------------------------
function initDonationUI() {
    // Inject styles for donation UI
    const style = document.createElement('style');
    style.textContent = `
        .donation-header {
            background: linear-gradient(90deg, var(--bg-panel) 0%, var(--bg-app) 100%);
            border-bottom: 1px solid var(--border);
            padding: 8px 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.9rem;
            color: var(--text-secondary);
        }
        .donation-link {
            color: var(--accent-primary);
            text-decoration: none;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: opacity 0.2s;
        }
        .donation-link:hover { opacity: 0.8; }
        .app-footer {
            text-align: center;
            padding: 2rem;
            color: var(--text-secondary);
            font-size: 0.9rem;
            border-top: 1px solid var(--border-color);
            margin-top: 4rem;
        }
    `;
    document.head.appendChild(style);

    // Inject Header
    const header = document.createElement('div');
    header.className = 'donation-header';
    header.innerHTML = `
        <span>SkyModderAI is free & open source.</span>
        <a href="#" onclick="upgradeToPro(); return false;" class="donation-link">
            <span>🍯</span> Buy me a mead
        </a>
    `;
    document.body.insertBefore(header, document.body.firstChild);

    // Inject Footer
    const footer = document.createElement('footer');
    footer.className = 'app-footer';
    footer.innerHTML = `
        <div style="display:flex;justify-content:center;align-items:center;gap:1.5rem;flex-wrap:wrap;">
            <p style="margin:0">Built for the community. <a href="https://www.buymeacoffee.com/skymodder" target="_blank" style="color:var(--text-main)">Support development</a></p>
            <div style="display:flex;align-items:center;gap:0.5rem;">
                <label for="theme-select" style="font-size:0.85rem;color:var(--text-muted)">Theme:</label>
                <select id="theme-select" style="padding:4px 8px;font-size:0.85rem;background:var(--bg-input);color:var(--text-main);border:1px solid var(--border);border-radius:4px;">
                    ${Object.entries(THEMES).map(([k, v]) => `<option value="${k}">${v.name}</option>`).join('')}
                </select>
            </div>
        </div>
    `;
    document.body.appendChild(footer);

    document.getElementById('theme-select').addEventListener('change', (e) => {
        applyTheme(e.target.value);
    });
}

// -------------------------------------------------------------------
// Agent Window - Floating AI Companion
// -------------------------------------------------------------------
function initAgentWindow() {
    const style = document.createElement('style');
    style.textContent = `
        #agent-toggle { position: fixed; bottom: 24px; left: 24px; width: 56px; height: 56px; border-radius: 50%; background: var(--accent); color: var(--accent-text); border: none; cursor: pointer; box-shadow: var(--shadow-md); z-index: 10001; display: flex; align-items: center; justify-content: center; transition: transform 0.2s; padding: 8px; overflow: hidden; }
        #agent-toggle:hover { transform: scale(1.05); }
        #agent-toggle img { width: 100%; height: 100%; object-fit: contain; pointer-events: none; }
        #agent-window { position: fixed; bottom: 96px; left: 24px; width: 380px; height: 600px; max-height: 80vh; background: var(--bg-panel); border: 1px solid var(--border); border-radius: var(--radius-lg); box-shadow: var(--shadow-md); z-index: 10000; display: flex; flex-direction: column; transform: translateY(20px); opacity: 0; pointer-events: none; transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1); overflow: hidden; }
        #agent-window.active { transform: translateY(0); opacity: 1; pointer-events: all; }
        .agent-header { padding: 16px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; background: var(--bg-panel); }
        .agent-title { font-weight: 600; font-size: 1rem; color: var(--text-main); }
        .agent-body { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 16px; background: var(--bg-app); }
        .agent-input-area { padding: 16px; border-top: 1px solid var(--border); display: flex; gap: 10px; background: var(--bg-panel); }
        .agent-input { flex: 1; background: var(--bg-input); border: 1px solid var(--border); color: var(--text-main); padding: 10px 14px; border-radius: 20px; resize: none; height: 44px; font-family: inherit; line-height: 1.4; }
        .agent-input:focus { outline: 2px solid var(--accent); border-color: transparent; }
        .agent-send { background: var(--accent); color: var(--accent-text); border: none; border-radius: 50%; width: 44px; height: 44px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: background 0.2s; font-weight: bold; font-size: 1.2rem; padding-bottom: 2px; }
        .agent-send:hover { background: var(--accent-hover); }
        .chat-msg { max-width: 85%; padding: 10px 14px; border-radius: 12px; font-size: 0.95rem; line-height: 1.5; }
        .chat-msg-user { align-self: flex-end; background: var(--accent); color: var(--accent-text); border-bottom-right-radius: 2px; }
        .chat-msg-assistant { align-self: flex-start; background: var(--bg-panel); border: 1px solid var(--border); color: var(--text-main); border-bottom-left-radius: 2px; }
        @media (max-width: 768px) {
            #agent-toggle { bottom: 90px; }
            #agent-window { bottom: 156px; }
        }
        @media (max-width: 480px) { #agent-window { width: 92%; left: 4%; right: 4%; bottom: 156px; height: 60vh; } }
    `;
    document.head.appendChild(style);

    const toggle = document.createElement('button');
    toggle.id = 'agent-toggle';
    toggle.innerHTML = '<img src="/static/icons/samson_dog.svg" alt="Samson">';
    toggle.title = 'Open Agent';
    document.body.appendChild(toggle);

    const win = document.createElement('div');
    win.id = 'agent-window';
    win.innerHTML = `
        <div class="agent-header">
            <span class="agent-title">Samson</span>
            <button id="agent-close" style="background:none;border:none;color:var(--text-muted);cursor:pointer;font-size:1.5rem;line-height:1;">×</button>
        </div>
        <div class="agent-body" id="agent-messages">
            <div class="chat-msg chat-msg-assistant"><div class="chat-msg-body">Hi! I'm Samson. I can see your load order. How can I help?</div></div>
        </div>
        <form class="agent-input-area" id="agent-form">
            <textarea class="agent-input" id="agent-input" placeholder="Ask anything..."></textarea>
            <button type="submit" class="agent-send">➤</button>
        </form>
    `;
    document.body.appendChild(win);

    const msgs = document.getElementById('agent-messages');
    const input = document.getElementById('agent-input');
    const form = document.getElementById('agent-form');

    toggle.addEventListener('click', () => {
        win.classList.toggle('active');
        if (win.classList.contains('active')) input.focus();
    });

    document.getElementById('agent-close').addEventListener('click', () => win.classList.remove('active'));

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const text = input.value.trim();
        if (!text) return;

        // UI Update
        const userDiv = document.createElement('div');
        userDiv.className = 'chat-msg chat-msg-user';
        userDiv.innerHTML = `<div class="chat-msg-body">${escapeHtml(text)}</div>`;
        msgs.appendChild(userDiv);
        input.value = '';
        msgs.scrollTop = msgs.scrollHeight;

        // Prepare context
        const pageContext = capturePageContext();
        const modList = parseModListFromTextarea();
        const game = elements.gameSelect?.value || 'skyrimse';

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: text,
                    context: currentReport || '',
                    page_context: pageContext,
                    game,
                    mod_list: modList
                })
            });
            const data = await res.json().catch(() => ({}));

            const botDiv = document.createElement('div');
            botDiv.className = 'chat-msg chat-msg-assistant';
            const parseMd = (window.marked && typeof marked.parse === 'function') ? (s) => marked.parse(s) : (s) => escapeHtml(s);
            botDiv.innerHTML = `<div class="chat-msg-body">${linkify(parseMd(data.reply || data.error || 'Error.'))}</div>`;
            msgs.appendChild(botDiv);
            msgs.scrollTop = msgs.scrollHeight;
        } catch (e) {
            const errDiv = document.createElement('div');
            errDiv.className = 'chat-msg chat-msg-assistant';
            errDiv.innerHTML = `<div class="chat-msg-body">Network error.</div>`;
            msgs.appendChild(errDiv);
        }
    });

    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            form.dispatchEvent(new Event('submit'));
        }
    });
}

function capturePageContext() {
    const activeTab = document.querySelector('.main-tab.active');
    const tabName = activeTab ? activeTab.dataset.tab : 'unknown';
    let content = `Current Tab: ${tabName}\n`;

    if (tabName === 'analyze') {
        const report = document.getElementById('conflicts-container')?.innerText;
        if (report) content += `Analysis Report (visible text):\n${report.slice(0, 3000)}\n`;
    } else if (tabName === 'quickstart') {
        content += "User is looking at Quick Start guide.\n";
    } else if (tabName === 'community') {
        const feed = document.getElementById('community-feed')?.innerText;
        if (feed) content += `Community Feed (visible):\n${feed.slice(0, 2000)}\n`;
    } else if (tabName === 'dev') {
        const devReport = document.getElementById('dev-report-content')?.innerText;
        if (devReport) content += `Dev Report:\n${devReport.slice(0, 2000)}\n`;
    }
    return content;
}

// -------------------------------------------------------------------
// Priority 4: Dynamic Floating Links & Portal System
// -------------------------------------------------------------------
function initFloatingPortal() {
    // Inject CSS for portal and smart links
    const style = document.createElement('style');
    style.textContent = `
        .smart-link { color: var(--accent-primary); text-decoration: none; border-bottom: 1px dashed var(--accent-primary); transition: all 0.2s; }
        .smart-link:hover { background: rgba(0, 212, 232, 0.1); border-bottom-style: solid; cursor: alias; }
        #floating-portal {
            position: fixed; bottom: 20px; right: 20px; width: 400px; height: 500px;
            background: var(--card-bg); border: 1px solid var(--border-color);
            border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            z-index: 9999; display: flex; flex-direction: column;
            transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.3s;
            transform: translateY(20px); opacity: 0; pointer-events: none;
        }
        #floating-portal.active { transform: translateY(0); opacity: 1; pointer-events: all; }
        .portal-header {
            padding: 12px 16px; background: rgba(0,0,0,0.2); border-bottom: 1px solid var(--border-color);
            display: flex; justify-content: space-between; align-items: center; cursor: move;
        }
        .portal-title { font-weight: 600; font-size: 0.9rem; color: var(--text-primary); display: flex; align-items: center; gap: 8px; }
        .portal-controls button { background: none; border: none; color: var(--text-secondary); cursor: pointer; font-size: 1.2rem; padding: 0 4px; }
        .portal-controls button:hover { color: var(--text-primary); }
        .portal-body { flex: 1; position: relative; background: var(--card-bg); color: var(--text-primary); }
        .portal-body iframe { width: 100%; height: 100%; border: none; }
        .portal-fallback {
            position: absolute; top: 0; left: 0; right: 0; bottom: 0;
            background: var(--card-bg); color: var(--text-primary);
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            padding: 20px; text-align: center;
        }
        #link-preview-image { height: 180px; background-size: cover; background-position: center; border-radius: 6px 6px 0 0; margin: -12px -12px 12px -12px; }
        #link-preview-image.empty { display: none; }
    `;
    document.head.appendChild(style);

    // Create Portal DOM
    const portal = document.createElement('div');
    portal.id = 'floating-portal';
    portal.innerHTML = `
        <div class="portal-header" id="portal-drag-handle">
            <span class="portal-title">🌐 Browsing</span>
            <div class="portal-controls">
                <button id="portal-close">×</button>
            </div>
        </div>
        <div class="portal-body">
            <iframe id="portal-frame" name="portal-frame"></iframe>
            <div id="portal-fallback" class="portal-fallback hidden">
                <p style="margin-bottom:1rem">This site cannot be embedded directly.</p>
                <a id="portal-ext-link" href="#" target="_blank" class="primary-button">Open in New Tab</a>
            </div>
        </div>
    `;
    document.body.appendChild(portal);

    // Event Listeners
    document.body.addEventListener('click', (e) => {
        if (e.target.classList.contains('smart-link')) {
            e.preventDefault();
            openPortal(e.target.href);
        }
    });

    document.getElementById('portal-close').addEventListener('click', () => {
        portal.classList.remove('active');
        document.getElementById('portal-frame').src = 'about:blank';
    });

    // Draggable logic
    const handle = document.getElementById('portal-drag-handle');
    let isDragging = false, startX, startY, initLeft, initTop;

    handle.addEventListener('mousedown', (e) => {
        isDragging = true;
        startX = e.clientX;
        startY = e.clientY;
        const rect = portal.getBoundingClientRect();
        initLeft = rect.left;
        initTop = rect.top;
        portal.style.right = 'auto';
        portal.style.bottom = 'auto';
        portal.style.left = initLeft + 'px';
        portal.style.top = initTop + 'px';
    });

    window.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        const dx = e.clientX - startX;
        const dy = e.clientY - startY;
        portal.style.left = (initLeft + dx) + 'px';
        portal.style.top = (initTop + dy) + 'px';
    });

    window.addEventListener('mouseup', () => isDragging = false);
}

function openPortal(url) {
    const portal = document.getElementById('floating-portal');
    const frame = document.getElementById('portal-frame');
    const fallback = document.getElementById('portal-fallback');
    const extLink = document.getElementById('portal-ext-link');
    const title = portal.querySelector('.portal-title');

    portal.classList.add('active');
    title.textContent = `🌐 ${new URL(url).hostname}`;

    // Check for known blockers
    const blockers = ['google.com', 'amazon.com', 'github.com', 'nexusmods.com'];
    const isBlocked = blockers.some(b => url.includes(b));

    if (isBlocked) {
        frame.classList.add('hidden');
        fallback.classList.remove('hidden');
        extLink.href = url;
    } else {
        fallback.classList.add('hidden');
        frame.classList.remove('hidden');
        frame.src = url;
    }
}

// -------------------------------------------------------------------
// Link preview — Obsidian-style hover popover for links
// -------------------------------------------------------------------
function initLinkPreviews() {
    let popover = document.getElementById('link-preview-popover');
    if (!popover) {
        popover = document.createElement('div');
        popover.id = 'link-preview-popover';
        popover.className = 'link-preview-popover';
        popover.setAttribute('aria-hidden', 'true');
        popover.innerHTML = `
            <div class="link-preview-content">
                <div id="link-preview-image" class="link-preview-image empty"></div>
                <div class="link-preview-body">
                    <div id="link-preview-title" class="link-preview-title">Loading...</div>
                    <div id="link-preview-desc" class="link-preview-desc"></div>
                    <a id="link-preview-open" href="#" target="_blank" rel="noopener noreferrer" class="link-preview-open">Open Link</a>
                </div>
            </div>`;
        document.body.appendChild(popover);
    }
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
            // Reset state
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
                        // Dynamic live preview picture
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
    // Inject Styles for Vercel/Linear-like Command Palette
    const style = document.createElement('style');
    style.textContent = `
        #command-palette {
            position: fixed; inset: 0; z-index: 10000;
            display: flex; align-items: flex-start; justify-content: center;
            padding-top: 14vh;
            backdrop-filter: blur(4px);
            background-color: rgba(15, 23, 42, 0.6);
            opacity: 0; pointer-events: none; transition: opacity 0.15s ease-out;
        }
        #command-palette:not(.hidden) { opacity: 1; pointer-events: auto; }
        #command-palette.hidden { display: none; }

        .command-palette-modal {
            width: 100%; max-width: 600px;
            background: var(--bg-panel);
            border: 1px solid var(--border);
            border-radius: 12px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            overflow: hidden;
            display: flex; flex-direction: column;
            animation: cp-slide-in 0.2s ease-out;
        }
        @keyframes cp-slide-in {
            from { transform: translateY(-10px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        .command-palette-header {
            padding: 16px; border-bottom: 1px solid var(--border);
            display: flex; align-items: center; gap: 12px;
        }
        #command-palette-input {
            width: 100%; background: transparent; border: none;
            font-size: 1.1rem; color: var(--text-main); padding: 0; outline: none;
        }
        #command-palette-input::placeholder { color: var(--text-muted); }
        #command-palette-results { max-height: 320px; overflow-y: auto; padding: 8px; }
        .command-palette-item {
            width: 100%; display: flex; align-items: center; justify-content: space-between;
            padding: 10px 12px; background: transparent; border: none;
            color: var(--text-muted); border-radius: 6px; cursor: pointer;
            text-align: left; font-size: 0.95rem; transition: all 0.1s;
        }
        .command-palette-item:hover, .command-palette-item.highlighted {
            background: var(--accent); color: var(--accent-text);
        }
        .command-palette-item.highlighted .command-palette-shortcut {
            color: rgba(0,0,0,0.6); background: rgba(0,0,0,0.1);
        }
        .command-palette-shortcut {
            font-size: 0.75rem; background: rgba(255,255,255,0.1);
            padding: 2px 6px; border-radius: 4px; font-family: monospace;
        }
        .command-palette-footer {
            padding: 8px 16px; background: rgba(0,0,0,0.2);
            border-top: 1px solid var(--border); font-size: 0.75rem;
            color: var(--text-muted); display: flex; justify-content: flex-end; gap: 12px;
        }
    `;
    document.head.appendChild(style);

    // Ensure DOM structure exists
    let palette = document.getElementById('command-palette');
    if (!palette) {
        palette = document.createElement('div');
        palette.id = 'command-palette';
        palette.className = 'hidden';
        palette.innerHTML = `
            <div class="command-palette-backdrop" style="position:absolute;inset:0;"></div>
            <div class="command-palette-modal">
                <div class="command-palette-header">
                    <span style="color:var(--text-muted)">🔍</span>
                    <input type="text" id="command-palette-input" placeholder="Type a command..." autocomplete="off">
                </div>
                <div id="command-palette-results"></div>
                <div class="command-palette-footer">
                    <span>Use <strong>↑↓</strong> to navigate</span>
                    <span><strong>Enter</strong> to select</span>
                    <span><strong>Esc</strong> to close</span>
                </div>
            </div>
        `;
        document.body.appendChild(palette);
    }

    const trigger = document.getElementById('command-palette-trigger');
    const input = document.getElementById('command-palette-input');
    const backdrop = palette.querySelector('.command-palette-backdrop');

    if (trigger) trigger.addEventListener('click', openCommandPalette);
    if (backdrop) backdrop.addEventListener('click', closeCommandPalette);

    if (input) {
        input.addEventListener('input', () => runCommandPaletteSearch(input.value));
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') { closeCommandPalette(); return; }
            const items = palette.querySelectorAll('.command-palette-item');
            const current = palette.querySelector('.command-palette-item.highlighted');
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
                e.preventDefault();
                const target = (idx >= 0 && items[idx]) ? items[idx] : items[0];
                if (target) target.click();
            }
        });
    }

    document.addEventListener('keydown', (e) => {
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
            e.preventDefault();
            if (palette.classList.contains('hidden')) openCommandPalette();
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
    } catch (_) { }
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
    const checkoutForm = document.getElementById('checkout-form');
    if (checkoutForm) checkoutForm.addEventListener('submit', submitCheckout);
}

// -------------------------------------------------------------------
// Priority 3 Features Implementation
// -------------------------------------------------------------------

// Game state management for sync across tabs (Priority 3G)
const gameState = {
    get game() {
        return localStorage.getItem('skymodder_selected_game') || 'skyrimse';
    },
    set game(val) {
        localStorage.setItem('skymodder_selected_game', val);
        document.querySelectorAll('.game-selector').forEach(el => el.value = val);
    }
};

// localStorage session persistence (Priority 3F)
function initLocalStoragePersistence() {
    if (!elements.modListInput) return;

    // Save on every change
    elements.modListInput.addEventListener('input', () => {
        localStorage.setItem('skymodder_modlist', elements.modListInput.value);
        localStorage.setItem('skymodder_game', elements.gameSelect?.value || 'skyrimse');
        localStorage.setItem('skymodder_saved_at', Date.now());
        updateModCounter();
    });

    // Check for saved session on page load
    const saved = localStorage.getItem('skymodder_modlist');
    const savedAt = localStorage.getItem('skymodder_saved_at');
    const ageMinutes = savedAt ? (Date.now() - savedAt) / 60000 : 999;

    if (saved && saved.trim().length > 0 && ageMinutes < 480) { // 8 hours
        showRestoreBanner(saved, ageMinutes);
    }
}

// Show restore banner for saved session
function showRestoreBanner(savedList, ageMinutes) {
    const banner = document.createElement('div');
    banner.className = 'index-info-banner';
    banner.innerHTML = `
        <span>📋 You have a mod list from ${Math.round(ageMinutes)} minutes ago.
        <button type="button" class="link-button" onclick="restoreSavedSession()">Restore it</button> or
        <button type="button" class="link-button" onclick="dismissRestoreBanner()">dismiss</button></span>
    `;

    const mainContent = document.querySelector('main');
    if (mainContent) {
        mainContent.insertBefore(banner, mainContent.firstChild);
    }

    // Store saved list globally for restoration
    window._savedModList = savedList;
}

// Restore saved session
function restoreSavedSession() {
    if (window._savedModList && elements.modListInput) {
        elements.modListInput.value = window._savedModList;
        updateModCounter();
        refreshInputMatchPreview({ silent: true });

        // Restore game selection
        const savedGame = localStorage.getItem('skymodder_game');
        if (savedGame) {
            gameState.game = savedGame;
        }
    }
    dismissRestoreBanner();
}

// Dismiss restore banner
function dismissRestoreBanner() {
    const banner = document.querySelector('.index-info-banner');
    if (banner) banner.remove();
    delete window._savedModList;
}

/**
 * Parse mod list text into array of mod names.
 * Handles plugins.txt format (* prefix = enabled), MO2 format (+/- prefix), and plain lists.
 */
function parseModList(text) {
    if (!text) return [];
    const lines = text.split('\n');
    const mods = [];
    for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith('#')) continue;
        let modName = trimmed;
        if (modName.startsWith('*') || modName.startsWith('+') || modName.startsWith('-')) {
            modName = modName.slice(1);
        }
        if (modName.includes('/') || modName.includes('\\')) {
            modName = modName.split('/').pop().split('\\').pop();
        }
        if (modName && (modName.endsWith('.esp') || modName.endsWith('.esm') || modName.endsWith('.esl'))) {
            mods.push(modName);
        }
    }
    return mods;
}

/**
 * Get display name for a game ID.
 */
function getGameDisplayName(gameId) {
    const gameNames = {
        skyrim: 'Skyrim LE',
        skyrimse: 'Skyrim SE',
        skyrimvr: 'Skyrim VR',
        oblivion: 'Oblivion',
        fallout3: 'Fallout 3',
        falloutnv: 'Fallout New Vegas',
        fallout4: 'Fallout 4',
        starfield: 'Starfield'
    };
    return gameNames[gameId] || gameId || 'Skyrim SE';
}

// Auto-scroll to results after analysis (Priority 3B)
function autoScrollToResults() {
    setTimeout(() => {
        const resultsSection = document.getElementById('results-section');
        if (resultsSection) {
            resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }, 100); // 100ms delay ensures DOM is painted
}

// Color-code conflict items (Priority 3C)
function colorCodeConflictItems() {
    const conflictItems = document.querySelectorAll('.conflict-item');
    conflictItems.forEach(item => {
        // Remove existing color classes
        item.classList.remove('error', 'warning', 'info');

        // Add appropriate class based on content
        const text = item.textContent.toLowerCase();
        if (text.includes('error') || text.includes('critical') || text.includes('failed')) {
            item.classList.add('error');
        } else if (text.includes('warning') || text.includes('caution') || text.includes('deprecated')) {
            item.classList.add('warning');
        } else {
            item.classList.add('info');
        }
    });
}

// Add Quick Fix chips to conflict items (Priority 3D)
function addQuickFixChips() {
    const conflictItems = document.querySelectorAll('.conflict-item');
    conflictItems.forEach((item, index) => {
        // Skip if already has a quick fix chip
        if (item.querySelector('.quick-fix-chip')) return;

        const chip = document.createElement('button');
        chip.className = 'quick-fix-chip';
        chip.textContent = '⚡ Quick Fix';
        chip.onclick = () => openQuickFix(item.textContent, index);

        // Append to the end of the conflict item
        item.appendChild(chip);
    });
}

// Open Quick Fix functionality
function openQuickFix(conflictText, index) {
    // Try to get resolution from API first
    fetch(`/api/resolve?type=conflict&game=${gameState.game}`)
        .then(response => response.json())
        .then(data => {
            if (data.resolution) {
                showInlineResolution(item, data.resolution);
            } else {
                // Fallback: pre-fill AI chat if Pro, or search if not
                if (currentUserTier === 'pro') {
                    if (elements.chatInput) {
                        elements.chatInput.value = `How do I fix: ${conflictText.trim()}`;
                        elements.chatInput.focus();
                    }
                } else {
                    // Open DuckDuckGo search
                    const modName = extractModName(conflictText);
                    window.open(`https://duckduckgo.com/?q=${encodeURIComponent(modName + ' skyrim conflict fix')}`, '_blank');
                }
            }
        })
        .catch(error => {
            console.error('Error fetching resolution:', error);
            // Fallback to search
            const modName = extractModName(conflictText);
            window.open(`https://duckduckgo.com/?q=${encodeURIComponent(modName + ' skyrim conflict fix')}`, '_blank');
        });
}

// Extract mod name from conflict text
function extractModName(conflictText) {
    const match = conflictText.match(/^([A-Za-z0-9_\-\s]+)/);
    return match ? match[1].trim() : 'mod conflict';
}

// Show inline resolution panel
function showInlineResolution(item, resolution) {
    const panel = document.createElement('div');
    panel.className = 'quick-fix-panel';
    panel.innerHTML = `
        <div class="quick-fix-content">
            <h4>Suggested Fix</h4>
            <p>${resolution}</p>
            <button type="button" class="secondary-button" onclick="this.closest('.quick-fix-panel').remove()">Close</button>
        </div>
    `;

    item.parentNode.insertBefore(panel, item.nextSibling);
}

// Expose new functions globally
window.restoreSavedSession = restoreSavedSession;
window.dismissRestoreBanner = dismissRestoreBanner;

// -------------------------------------------------------------------
// Initialization
// -------------------------------------------------------------------
loadShareFromUrl();
initPageActionBindings();
initToastSystem();
initCommunityPost();
initQuickstartGameSelect();
initQuickstartLivePreview();
loadGames();
checkUserTier();
initGameFolderScan();
initDevTools();
// Initialize Priority 3 features
updateModCounter();

const gameVersionSelect = document.getElementById('game-version');
if (gameVersionSelect) {
    gameVersionSelect.addEventListener('change', updateGameVersionInfo);
}

// Expose for inline handlers
window.upgradeToPro = upgradeToPro;
window.closeCheckoutModal = closeCheckoutModal;
window.submitCheckout = submitCheckout;

// -------------------------------------------------------------------
// Library functionality (Pro feature)
// -------------------------------------------------------------------
let libraryItems = [];
let libraryFilters = {
    search: '',
    game: '',
    game_version: '',
    masterlist_version: ''
};

function initLibrary() {
    if (!elements.libraryGrid) return;

    // Search functionality
    if (elements.librarySearch) {
        elements.librarySearch.addEventListener('input', (e) => {
            libraryFilters.search = e.target.value.toLowerCase();
            if (elements.librarySearchClear) {
                elements.librarySearchClear.classList.toggle('hidden', !libraryFilters.search);
            }
            renderLibrary();
        });
    }

    if (elements.librarySearchClear) {
        elements.librarySearchClear.addEventListener('click', () => {
            elements.librarySearch.value = '';
            libraryFilters.search = '';
            elements.librarySearchClear.classList.add('hidden');
            renderLibrary();
        });
    }

    // Filter functionality
    ['libraryFilterGame', 'libraryFilterVersion', 'libraryFilterMasterlist'].forEach(id => {
        const el = elements[id];
        if (el) {
            el.addEventListener('change', (e) => {
                const key = id.replace('libraryFilter', '').toLowerCase();
                libraryFilters[key] = e.target.value;
                renderLibrary();
            });
        }
    });

    // Refresh button
    if (elements.libraryRefreshBtn) {
        elements.libraryRefreshBtn.addEventListener('click', loadLibrary);
    }

    // Load library on first show
    const libraryTab = document.querySelector('[data-tab="library"]');
    if (libraryTab) {
        libraryTab.addEventListener('click', () => {
            if (libraryItems.length === 0) {
                loadLibrary();
            }
        });
    }
}

async function loadLibrary() {
    if (!elements.libraryGrid) return;

    if (elements.libraryStatus) {
        elements.libraryStatus.textContent = 'Loading your library...';
    }

    try {
        const params = new URLSearchParams();
        if (libraryFilters.game) params.append('game', libraryFilters.game);
        if (libraryFilters.game_version) params.append('game_version', libraryFilters.game_version);
        if (libraryFilters.masterlist_version) params.append('masterlist_version', libraryFilters.masterlist_version);

        const response = await fetch(`/api/list-preferences?${params.toString()}`);
        if (!response.ok) {
            throw new Error('Failed to load library');
        }

        const data = await response.json();
        libraryItems = data.items || [];

        // Populate filter dropdowns with available options
        populateLibraryFilters();

        renderLibrary();

        if (elements.libraryStatus) {
            elements.libraryStatus.textContent = `${libraryItems.length} item${libraryItems.length !== 1 ? 's' : ''}`;
        }
    } catch (error) {
        console.error('Library load error:', error);
        if (elements.libraryGrid) {
            elements.libraryGrid.innerHTML = '<p class="hint">Failed to load library. Try refreshing.</p>';
        }
        if (elements.libraryStatus) {
            elements.libraryStatus.textContent = 'Error loading library';
        }
    }
}

function populateLibraryFilters() {
    // Populate game versions
    if (elements.libraryFilterVersion) {
        const versions = [...new Set(libraryItems.map(item => item.game_version).filter(Boolean))];
        const currentValue = elements.libraryFilterVersion.value;
        elements.libraryFilterVersion.innerHTML = '<option value="">All versions</option>';
        versions.sort().forEach(version => {
            const option = document.createElement('option');
            option.value = version;
            option.textContent = version;
            elements.libraryFilterVersion.appendChild(option);
        });
        elements.libraryFilterVersion.value = currentValue;
    }

    // Populate masterlist versions
    if (elements.libraryFilterMasterlist) {
        const versions = [...new Set(libraryItems.map(item => item.masterlist_version).filter(Boolean))];
        const currentValue = elements.libraryFilterMasterlist.value;
        elements.libraryFilterMasterlist.innerHTML = '<option value="">All LOOT versions</option>';
        versions.sort().forEach(version => {
            const option = document.createElement('option');
            option.value = version;
            option.textContent = version;
            elements.libraryFilterMasterlist.appendChild(option);
        });
        elements.libraryFilterMasterlist.value = currentValue;
    }
}

function renderLibrary() {
    if (!elements.libraryGrid) return;

    let filtered = libraryItems.filter(item => {
        if (libraryFilters.search) {
            const searchStr = libraryFilters.search;
            const matchesName = item.name.toLowerCase().includes(searchStr);
            const matchesTags = item.tags && item.tags.toLowerCase().includes(searchStr);
            const matchesNotes = item.notes && item.notes.toLowerCase().includes(searchStr);
            if (!matchesName && !matchesTags && !matchesNotes) return false;
        }
        if (libraryFilters.game && item.game !== libraryFilters.game) return false;
        if (libraryFilters.game_version && item.game_version !== libraryFilters.game_version) return false;
        if (libraryFilters.masterlist_version && item.masterlist_version !== libraryFilters.masterlist_version) return false;
        return true;
    });

    if (filtered.length === 0) {
        elements.libraryGrid.innerHTML = '<p class="hint">No saved lists found matching your filters.</p>';
        return;
    }

    elements.libraryGrid.innerHTML = filtered.map(item => createLibraryCard(item)).join('');

    // Add event listeners to cards
    elements.libraryGrid.querySelectorAll('.library-card').forEach(card => {
        const itemId = parseInt(card.dataset.id);
        const item = libraryItems.find(i => i.id === itemId);
        if (!item) return;

        // Load button
        const loadBtn = card.querySelector('.library-load-btn');
        if (loadBtn) {
            loadBtn.addEventListener('click', () => loadLibraryItem(item));
        }

        // Analyze button
        const analyzeBtn = card.querySelector('.library-analyze-btn');
        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', () => analyzeLibraryItem(item));
        }

        // Duplicate button
        const dupBtn = card.querySelector('.library-duplicate-btn');
        if (dupBtn) dupBtn.addEventListener('click', () => duplicateLibraryItem(item));

        // Rename button
        const renameBtn = card.querySelector('.library-rename-btn');
        if (renameBtn) {
            renameBtn.addEventListener('click', () => renameLibraryItem(item));
        }

        // Edit tags/notes button
        const editBtn = card.querySelector('.library-edit-btn');
        if (editBtn) {
            editBtn.addEventListener('click', () => editLibraryItem(item));
        }

        // Delete button
        const deleteBtn = card.querySelector('.library-delete-btn');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => deleteLibraryItem(item));
        }
    });
}

function createLibraryCard(item) {
    const gameName = getGameDisplayName(item.game);
    const versionInfo = [item.game_version, item.masterlist_version].filter(Boolean).join(' | ');
    const tagsDisplay = item.tags ? item.tags.split(',').map(tag => `<span class="library-tag">${tag.trim()}</span>`).join('') : '';
    const notesDisplay = item.notes ? `<p class="library-notes">${item.notes}</p>` : '';
    const updatedDate = new Date(item.updated_at || item.saved_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    const modCount = item.list_text.split('\n').filter(line => line.trim() && !line.trim().startsWith('#')).length;

    // Analysis health indicator
    let healthDisplay = '';
    if (item.analysis_snapshot) {
        const analysis = item.analysis_snapshot;
        const errorCount = analysis.summary?.errors || 0;
        const warningCount = analysis.summary?.warnings || 0;
        const infoCount = analysis.summary?.info || 0;
        const total = analysis.summary?.total || 0;

        let healthClass = 'health-clean';
        let healthText = 'Clean';
        if (errorCount > 0) {
            healthClass = 'health-errors';
            healthText = `${errorCount} error${errorCount !== 1 ? 's' : ''}`;
        } else if (warningCount > 0) {
            healthClass = 'health-warnings';
            healthText = `${warningCount} warning${warningCount !== 1 ? 's' : ''}`;
        } else if (infoCount > 0) {
            healthClass = 'health-info';
            healthText = `${infoCount} note${infoCount !== 1 ? 's' : ''}`;
        }

        healthDisplay = `<div class="library-health ${healthClass}" title="Analysis health: ${total} total issues">${healthText}</div>`;
    } else {
        healthDisplay = '<div class="library-health health-unknown" title="No analysis data">Not analyzed</div>';
    }

    return `
        <div class="library-card" data-id="${item.id}">
            <div class="library-card-header">
                <div class="library-card-top">
                    <h3 class="library-card-title">${escapeHtml(item.name)}</h3>
                    ${healthDisplay}
                </div>
                <div class="library-card-meta">
                    <span class="library-game-badge">${gameName}</span>
                    <span class="library-date">Updated ${updatedDate}</span>
                </div>
            </div>
            <div class="library-card-body">
                ${tagsDisplay ? `<div class="library-tags">${tagsDisplay}</div>` : ''}
                ${notesDisplay}
                <div class="library-stats-badges" style="display:flex;gap:8px;margin-top:12px;flex-wrap:wrap;">
                    <span class="conflict-type-badge" style="background:var(--bg-input)">📦 ${modCount} Mods</span>
                    ${versionInfo ? `<span class="conflict-type-badge" style="background:var(--bg-input)">v${versionInfo}</span>` : ''}
                    ${item.analysis_snapshot ? `<span class="conflict-type-badge" style="color:var(--success);border-color:var(--success)">Analyzed</span>` : ''}
                </div>
            </div>
            <div class="library-card-actions">
                <button type="button" class="library-load-btn secondary-button small">Load</button>
                <button type="button" class="library-analyze-btn primary-button small">Analyze</button>
                <button type="button" class="library-duplicate-btn secondary-button small">Duplicate</button>
                <button type="button" class="library-rename-btn secondary-button small">Rename</button>
                <button type="button" class="library-edit-btn secondary-button small">Edit</button>
                <button type="button" class="library-delete-btn danger-button small">Delete</button>
            </div>
        </div>
    `;
}

function loadLibraryItem(item) {
    // Switch to Analyze tab and load the list
    const analyzeTab = document.querySelector('[data-tab="analyze"]');
    if (analyzeTab) {
        analyzeTab.click();
    }

    if (elements.modListInput) {
        elements.modListInput.value = item.list_text;
        updateModCounter();
    }

    if (elements.gameSelect) {
        elements.gameSelect.value = item.game;
        // Trigger change to update versions
        elements.gameSelect.dispatchEvent(new Event('change'));
    }

    // Show success message
    showToast(`Loaded "${item.name}" into analyzer`, 'success');
}

function analyzeLibraryItem(item) {
    // Load the item and run analysis
    loadLibraryItem(item);
    setTimeout(() => {
        if (elements.analyzeBtn) {
            elements.analyzeBtn.click();
        }
    }, 100);
}

async function duplicateLibraryItem(item) {
    const newName = `${item.name} (Copy)`;
    try {
        const res = await fetch('/api/list-preferences', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: newName,
                list: item.list_text,
                game: item.game,
                game_version: item.game_version,
                masterlist_version: item.masterlist_version,
                source: 'duplicate',
                analysis_snapshot: item.analysis_snapshot
            })
        });
        if (res.ok) {
            showToast('List duplicated.', 'success');
            loadLibrary();
        } else {
            showToast('Failed to duplicate.', 'error');
        }
    } catch (e) {
        showToast('Network error.', 'error');
    }
}

async function renameLibraryItem(item) {
    const res = await openVaultModal('Rename Vault Item', [{ id: 'name', label: 'Name', value: item.name }]);
    if (!res || !res.name || res.name === item.name) return;

    try {
        const response = await fetch('/api/list-preferences', {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: item.id, new_name: res.name })
        });

        if (!response.ok) throw new Error('Failed to rename');

        // Update local data
        const idx = libraryItems.findIndex(i => i.id === item.id);
        if (idx !== -1) {
            libraryItems[idx].name = res.name;
        }

        renderLibrary();
        showToast('Renamed successfully', 'success');
    } catch (error) {
        console.error('Rename error:', error);
        showToast('Failed to rename', 'error');
    }
}

async function editLibraryItem(item) {
    const res = await openVaultModal('Edit Metadata', [
        { id: 'tags', label: 'Tags (comma-separated)', value: item.tags || '' },
        { id: 'notes', label: 'Notes', type: 'textarea', value: item.notes || '' }
    ]);
    if (!res) return;

    try {
        const updateData = { id: item.id };
        if (res.tags !== item.tags) updateData.tags = res.tags;
        if (res.notes !== item.notes) updateData.notes = res.notes;

        if (Object.keys(updateData).length === 1) return; // No changes

        const response = await fetch('/api/list-preferences', {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updateData)
        });

        if (!response.ok) throw new Error('Failed to update');

        // Update local data
        const idx = libraryItems.findIndex(i => i.id === item.id);
        if (idx !== -1) {
            Object.assign(libraryItems[idx], updateData);
        }

        renderLibrary();
        showToast('Updated successfully', 'success');
    } catch (error) {
        console.error('Edit error:', error);
        showToast('Failed to update', 'error');
    }
}

async function deleteLibraryItem(item) {
    const res = await openVaultModal(`Delete "${item.name}"?`, [], 'Delete');
    if (res === null) return; // Cancelled (openVaultModal returns null on cancel)

    try {
        const response = await fetch('/api/list-preferences', {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: item.id })
        });

        if (!response.ok) throw new Error('Failed to delete');

        // Update local data
        libraryItems = libraryItems.filter(i => i.id !== item.id);

        renderLibrary();
        showToast('Deleted successfully', 'success');
    } catch (error) {
        console.error('Delete error:', error);
        showToast('Failed to delete', 'error');
    }
}

function initVaultUI() {
    // Inject Vault Modal CSS & HTML
    const style = document.createElement('style');
    style.textContent = `
        #vault-modal { position: fixed; inset: 0; z-index: 10050; display: flex; align-items: center; justify-content: center; opacity: 0; pointer-events: none; transition: opacity 0.2s; }
        #vault-modal.active { opacity: 1; pointer-events: auto; }
        .vault-backdrop { position: absolute; inset: 0; background: rgba(0,0,0,0.6); backdrop-filter: blur(2px); }
        .vault-dialog { position: relative; width: 100%; max-width: 420px; background: var(--bg-panel); border: 1px solid var(--border); border-radius: 12px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1), 0 8px 10px -6px rgba(0,0,0,0.1); padding: 24px; transform: scale(0.95); transition: transform 0.2s; }
        #vault-modal.active .vault-dialog { transform: scale(1); }
        .vault-title { font-size: 1.25rem; font-weight: 600; color: var(--text-main); margin-bottom: 16px; }
        .vault-field { margin-bottom: 16px; }
        .vault-field label { display: block; font-size: 0.85rem; color: var(--text-muted); margin-bottom: 6px; }
        .vault-field input, .vault-field textarea { width: 100%; background: var(--bg-input); border: 1px solid var(--border); color: var(--text-main); padding: 8px 12px; border-radius: 6px; font-family: inherit; }
        .vault-field input:focus, .vault-field textarea:focus { outline: 2px solid var(--accent); border-color: transparent; }
        .vault-actions { display: flex; justify-content: flex-end; gap: 12px; margin-top: 24px; }
    `;
    document.head.appendChild(style);

    const modal = document.createElement('div');
    modal.id = 'vault-modal';
    modal.innerHTML = `
        <div class="vault-backdrop"></div>
        <div class="vault-dialog">
            <h3 class="vault-title" id="vault-title"></h3>
            <div id="vault-body"></div>
            <div class="vault-actions">
                <button class="secondary-button" id="vault-cancel">Cancel</button>
                <button class="primary-button" id="vault-confirm">Save</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);

    modal.querySelector('.vault-backdrop').addEventListener('click', closeVaultModal);
    document.getElementById('vault-cancel').addEventListener('click', closeVaultModal);
}

let vaultResolve = null;

function openVaultModal(title, fields, confirmLabel = 'Save') {
    return new Promise((resolve) => {
        vaultResolve = resolve;
        document.getElementById('vault-title').textContent = title;
        const body = document.getElementById('vault-body');
        body.innerHTML = fields.map(f => `
            <div class="vault-field">
                ${f.label ? `<label>${f.label}</label>` : ''}
                ${f.type === 'textarea'
                ? `<textarea id="${f.id}" rows="${f.rows || 3}">${escapeHtml(f.value || '')}</textarea>`
                : `<input type="${f.type || 'text'}" id="${f.id}" value="${escapeHtml(f.value || '')}" ${f.placeholder ? `placeholder="${f.placeholder}"` : ''}>`
            }
            </div>
        `).join('');

        const confirmBtn = document.getElementById('vault-confirm');
        confirmBtn.textContent = confirmLabel;
        confirmBtn.className = confirmLabel === 'Delete' ? 'danger-button' : 'primary-button';

        const newBtn = confirmBtn.cloneNode(true);
        confirmBtn.parentNode.replaceChild(newBtn, confirmBtn);

        newBtn.addEventListener('click', () => {
            const result = {};
            fields.forEach(f => {
                const el = document.getElementById(f.id);
                if (el) result[f.id] = el.value;
            });
            closeVaultModal();
            resolve(result); // Resolve with object (or empty object for delete)
        });

        const modal = document.getElementById('vault-modal');
        modal.classList.add('active');
        setTimeout(() => {
            const first = body.querySelector('input, textarea');
            if (first) first.focus();
        }, 50);
    });
}

function closeVaultModal() {
    document.getElementById('vault-modal').classList.remove('active');
    if (vaultResolve) { vaultResolve(null); vaultResolve = null; }
}

// -------------------------------------------------------------------
// Gameplay Engine UI (Walkthroughs)
// -------------------------------------------------------------------
const WalkthroughUI = {
    container: null,
    currentGame: '',

    init(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;

        const gameSelect = document.getElementById('game-select');
        this.currentGame = gameSelect ? gameSelect.value : 'skyrimse';

        // Re-load if game changed
        if (this.container.dataset.loadedGame !== this.currentGame) {
            this.loadIndex();
        }
    },

    async loadIndex() {
        this.container.innerHTML = '<p class="hint">Loading guides...</p>';
        try {
            const res = await fetch(`/api/walkthroughs?game=${encodeURIComponent(this.currentGame)}`);
            const data = await res.json();
            this.container.dataset.loadedGame = this.currentGame;
            this.renderIndex(data.guides || []);
        } catch (e) {
            this.container.innerHTML = '<p class="hint">Could not load guides. Try again later.</p>';
        }
    },

    renderIndex(guides) {
        if (guides.length === 0) {
            this.container.innerHTML = '<p class="hint">No guides available for this game yet.</p>';
            return;
        }

        let html = '<div class="walkthrough-layout"><div class="walkthrough-sidebar">';

        // Group by category
        const categories = {};
        guides.forEach(g => {
            const cat = g.category || 'General';
            if (!categories[cat]) categories[cat] = [];
            categories[cat].push(g);
        });

        for (const [cat, items] of Object.entries(categories)) {
            html += `<div class="wt-category"><div class="wt-category-title">${escapeHtml(cat)}</div>`;
            items.forEach(g => {
                html += `<div class="wt-item" data-id="${escapeHtml(g.id)}">${escapeHtml(g.title)}</div>`;
            });
            html += '</div>';
        }

        html += '</div><div class="walkthrough-content" id="wt-content"><div class="wt-placeholder">Select a guide to view details.</div></div></div>';

        this.container.innerHTML = html;

        this.container.querySelectorAll('.wt-item').forEach(item => {
            item.addEventListener('click', () => {
                this.container.querySelectorAll('.wt-item').forEach(i => i.classList.remove('active'));
                item.classList.add('active');
                this.loadGuide(item.dataset.id);
            });
        });
    },

    async loadGuide(id) {
        const contentEl = document.getElementById('wt-content');
        if (!contentEl) return;
        contentEl.innerHTML = '<p class="hint">Loading guide...</p>';

        try {
            const res = await fetch(`/api/walkthroughs/${encodeURIComponent(id)}?game=${encodeURIComponent(this.currentGame)}`);
            const data = await res.json();
            this.renderGuide(data, contentEl);
        } catch (e) {
            contentEl.innerHTML = '<p class="hint">Failed to load guide.</p>';
        }
    },

    renderGuide(data, container) {
        let html = `<div class="wt-header"><h2>${escapeHtml(data.title)}</h2></div>`;

        if (data.steps && data.steps.length > 0) {
            data.steps.forEach((step, idx) => {
                html += `
                    <div class="wt-step">
                        <div class="wt-step-header"><h3>${idx + 1}. ${escapeHtml(step.title)}</h3></div>
                        <div class="wt-step-body">
                            <p>${escapeHtml(step.description || '')}</p>
                            ${step.vanilla_solution ? `
                                <div class="wt-spoiler closed">
                                    <div class="wt-spoiler-btn">Show Solution</div>
                                    <div class="wt-spoiler-content">${escapeHtml(step.vanilla_solution)}</div>
                                </div>
                            ` : ''}
                            ${step.mod_notes ? step.mod_notes.map(n => `
                                <div class="wt-mod-context">
                                    <div class="wt-mod-header">Mod: ${escapeHtml(n.mod_id)}</div>
                                    <div>${escapeHtml(n.note)}</div>
                                </div>
                            `).join('') : ''}
                            ${step.bugs ? `
                                <div class="wt-bugs" style="margin-top:1rem;font-size:0.9rem;color:var(--warning)">
                                    <strong>Known Bugs:</strong>
                                    <ul style="margin-top:0.5rem;padding-left:1.5rem">
                                        ${step.bugs.map(b => `<li>${escapeHtml(b.symptom)}: ${escapeHtml(b.fix)}</li>`).join('')}
                                    </ul>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                `;
            });
        }

        container.innerHTML = html;

        container.querySelectorAll('.wt-spoiler').forEach(el => {
            el.addEventListener('click', () => el.classList.toggle('closed'));
        });
    }
};
window.WalkthroughUI = WalkthroughUI;

// Wait for the DOM to be fully loaded before initializing
document.addEventListener('DOMContentLoaded', function () {
    initDomElements();
    initGlobalEventListeners();

    // Initialize all components
    initModernTheme();
    initVaultUI();
    initLibrary();
    initGlobalGameSync();
    initMainTabs();
    initCommandPalette();
    initLinkPreviews();
    initLocalStoragePersistence();
    initFloatingPortal();
    initDonationUI();
    initAgentWindow();

    // Hotfix: Remove "(plain language)" text if present in static HTML
    // (User feedback: "It's right at the front of the webpage")
    (function cleanUpSafetyText() {
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
        let node;
        while (node = walker.nextNode()) {
            if (node.nodeValue && node.nodeValue.includes('(plain language)')) {
                node.nodeValue = node.nodeValue.replace(/\s*\(plain language\)/g, '');
            }
        }
    })();

    // Load any shared list from URL if present
    loadShareFromUrl();
    loadSpecs();
    initPageActionBindings();
    initToastSystem();
    initCommunityPost();
    initQuickstartGameSelect();
    initQuickstartLivePreview();

    // Initialize game folder scan if on the analyze page
    if (document.querySelector('.tab-panel#panel-analyze')) {
        initGameFolderScan();
    }

    // Initialize quickstart if on the quickstart page
    if (document.querySelector('.tab-panel#panel-quickstart')) {
        loadQuickstartContent();
        initQuickstartLivePreview();
    }

    // Initialize dev tools if on the dev page
    if (document.querySelector('.tab-panel#panel-dev')) {
        initDevTools();
    }

    // Initialize build list if on the build list page
    if (document.querySelector('.tab-panel#panel-build-list')) {
        initBuildListIfNeeded();
    }

    // Initialize community if on the community page
    if (document.querySelector('.tab-panel#panel-community')) {
        loadCommunityFeed();
        loadCommunityHealth();
        bindCommunityPostHandlers();
    }

    // Initialize analysis feedback panel
    initAnalysisFeedbackPanel();
    initFeedbackModal();

    // Expose Library functions globally
    window.loadLibrary = loadLibrary;
});
