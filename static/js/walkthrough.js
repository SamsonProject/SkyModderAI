/**
 * GameplayUI — The Gameplay Companion Engine
 * Connects users to existing high-quality wikis and scans local mod context.
 * Acts as a search aggregator for UESP/Fandom and checks your load order for relevance.
 */

const GameplayUI = {
    elements: {
        container: null,
        input: null,
        results: null
    },

    // Wiki Base URLs
    wikis: {
        skyrimse: 'https://en.uesp.net/wiki/Skyrim:',
        skyrim: 'https://en.uesp.net/wiki/Skyrim:',
        skyrimvr: 'https://en.uesp.net/wiki/Skyrim:',
        oblivion: 'https://en.uesp.net/wiki/Oblivion:',
        fallout3: 'https://fallout.fandom.com/wiki/',
        falloutnv: 'https://fallout.fandom.com/wiki/',
        fallout4: 'https://fallout.fandom.com/wiki/',
        starfield: 'https://starfield.fandom.com/wiki/'
    },

    init(containerId) {
        this.elements.container = document.getElementById(containerId);
        if (!this.elements.container) return;

        const game = (window.userContext && window.userContext.selectedGame) || 'skyrimse';
        // Only render if game changed or container is empty
        if (this.elements.container.dataset.loadedGame === game && this.elements.container.innerHTML.trim() !== '') {
            return;
        }
        this.elements.container.dataset.loadedGame = game;

        this.renderLayout();

        // Bind events
        this.elements.input = document.getElementById('gp-search-input');
        this.elements.results = document.getElementById('gp-results');
        this.elements.suggestions = document.getElementById('gp-search-suggestions');

        const btn = document.getElementById('gp-search-btn');
        if (btn) btn.addEventListener('click', () => this.runSearch());

        if (this.elements.input) {
            this.elements.input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    this.runSearch();
                    if (this.elements.suggestions) this.elements.suggestions.classList.add('hidden');
                }
            });
            this.elements.input.addEventListener('input', (e) => {
                this.showSuggestions(e.target.value);
            });
            // Auto-search if empty to show categories
            this.elements.input.addEventListener('focus', () => {
                if (this.elements.input.value.trim()) {
                    this.showSuggestions(this.elements.input.value);
                } else {
                    this.renderCategories();
                }
            });
            this.elements.input.addEventListener('blur', () => {
                setTimeout(() => {
                    if (this.elements.suggestions) this.elements.suggestions.classList.add('hidden');
                }, 200);
            });
        }
    },

    showSuggestions(query) {
        if (!query || query.length < 2) {
            if (this.elements.suggestions) this.elements.suggestions.classList.add('hidden');
            return;
        }
        const q = query.toLowerCase();
        const game = (window.userContext && window.userContext.selectedGame) || 'skyrimse';

        const cats = this.getCategoriesForGame(game).filter(c => c.name.toLowerCase().includes(q));
        const pops = this.getPopularLinks(game).filter(l => l.toLowerCase().includes(q));
        const mods = (window.userContext && window.userContext.currentModListParsed || [])
            .filter(m => m.toLowerCase().includes(q))
            .slice(0, 3);

        if (cats.length === 0 && pops.length === 0 && mods.length === 0) {
            this.elements.suggestions.classList.add('hidden');
            return;
        }

        let html = '';
        cats.forEach(c => {
            html += `<div class="gp-suggestion-item" onclick="window.GameplayUI.runSearch('${this.escapeHtml(c.query)}')"><span>${c.icon} ${this.escapeHtml(c.name)}</span><span class="gp-suggestion-type">Category</span></div>`;
        });
        pops.forEach(l => {
            html += `<div class="gp-suggestion-item" onclick="window.GameplayUI.runSearch('${this.escapeHtml(l)}')"><span>${this.escapeHtml(l)}</span><span class="gp-suggestion-type">Popular</span></div>`;
        });
        mods.forEach(m => {
            html += `<div class="gp-suggestion-item" onclick="window.GameplayUI.runSearch('${this.escapeHtml(m)}')"><span>⚡ ${this.escapeHtml(m)}</span><span class="gp-suggestion-type">Your Mod</span></div>`;
        });

        this.elements.suggestions.innerHTML = html;
        this.elements.suggestions.classList.remove('hidden');
    },

    renderLayout() {
        this.elements.container.innerHTML = `
            <div class="gp-layout">
                <div class="gp-header">
                    <h2>Gameplay Companion</h2>
                    <p class="gp-subtitle">Intelligent walkthroughs linked to your load order. Search a quest, location, or NPC.</p>
                </div>

                <div class="gp-search-box">
                    <input type="text" id="gp-search-input" placeholder="e.g. Bleak Falls Barrow, Nick Valentine, The Golden Claw..." autocomplete="off">
                    <button id="gp-search-btn" class="primary-button">Search</button>
                    <div id="gp-search-suggestions" class="gp-suggestions hidden"></div>
                </div>

                <div id="gp-categories" class="gp-categories">
                    <!-- Dynamic Categories -->
                </div>

                <div id="gp-results" class="gp-results hidden">
                    <!-- Dynamic Content -->
                </div>
            </div>
        `;
        this.renderCategories();
    },

    renderCategories() {
        const container = this.elements.container.querySelector('#gp-categories');
        if (!container) return;
        const game = (window.userContext && window.userContext.selectedGame) || 'skyrimse';
        const cats = this.getCategoriesForGame(game);

        container.innerHTML = `
            <div class="gp-cat-grid">
                ${cats.map(c => `
                    <button class="gp-cat-card" onclick="window.GameplayUI.runSearch('${c.query}')">
                        <span class="gp-cat-icon">${c.icon}</span>
                        <span class="gp-cat-name">${c.name}</span>
                    </button>
                `).join('')}
            </div>
            <div class="gp-popular-links">
                <span class="hint">Most used:</span>
                ${this.getPopularLinks(game).map(l => `<a href="#" onclick="window.GameplayUI.runSearch('${l}'); return false;">${l}</a>`).join(' · ')}
            </div>
        `;
        container.classList.remove('hidden');
    },

    getCategoriesForGame(game) {
        const defaults = [
            { name: 'Main Quest', query: 'Main Quest', icon: '👑' },
            { name: 'Factions', query: 'Factions', icon: '⚔️' },
            { name: 'Followers', query: 'Followers', icon: '🤝' },
            { name: 'Locations', query: 'Locations', icon: '🗺️' },
            { name: 'Unique Items', query: 'Unique Items', icon: '💎' },
            { name: 'Builds', query: 'Character Builds', icon: '🧙‍♂️' }
        ];
        if (game.includes('fallout')) {
            return [
                { name: 'Main Story', query: 'Main Quest', icon: '☢️' },
                { name: 'Companions', query: 'Companions', icon: '🐕' },
                { name: 'Weapons', query: 'Unique Weapons', icon: '🔫' },
                { name: 'Settlements', query: 'Settlements', icon: '🏠' },
                { name: 'Perks', query: 'Perks', icon: '⭐' },
                { name: 'DLC', query: 'DLC', icon: '💿' }
            ];
        }
        return defaults;
    },

    runSearch(presetQuery) {
        const query = presetQuery || this.elements.input.value.trim();
        if (!query) return;
        if (presetQuery) this.elements.input.value = presetQuery;

        const game = (window.userContext && window.userContext.selectedGame) || 'skyrimse';
        const wikiBase = this.wikis[game] || this.wikis.skyrimse;
        const wikiUrl = `${wikiBase}${encodeURIComponent(query)}`;

        // 1. External Resources (The "Book" that already exists)
        let html = `
            <div class="gp-section">
                <h3>External Guides</h3>
                <div class="gp-actions">
                    <a href="${wikiUrl}" target="_blank" rel="noopener" class="gp-card-link">
                        <span class="gp-icon">📖</span>
                        <div>
                            <strong>Open Wiki Guide</strong>
                            <span class="hint">${new URL(wikiBase).hostname}</span>
                        </div>
                    </a>
                    <a href="https://www.google.com/search?q=${encodeURIComponent(query + ' walkthrough ' + game)}" target="_blank" rel="noopener" class="gp-card-link">
                        <span class="gp-icon">🔍</span>
                        <div>
                            <strong>Google Walkthroughs</strong>
                            <span class="hint">Videos & Articles</span>
                        </div>
                    </a>
                    <a href="https://www.google.com/search?q=${encodeURIComponent(query + ' bug fix ' + game + ' site:reddit.com')}" target="_blank" rel="noopener" class="gp-card-link">
                        <span class="gp-icon">🐛</span>
                        <div>
                            <strong>Search Known Bugs</strong>
                            <span class="hint">Reddit & Forums</span>
                        </div>
                    </a>
                    <a href="https://www.google.com/search?q=${encodeURIComponent(game + ' console commands cheats')}" target="_blank" rel="noopener" class="gp-card-link">
                        <span class="gp-icon">💻</span>
                        <div>
                            <strong>Cheats & Console</strong>
                            <span class="hint">God mode, items, etc.</span>
                        </div>
                    </a>
                </div>
            </div>
        `;

        // 2. Mod Context Engine (The "Engine" part)
        // Hide categories when showing results
        const catContainer = this.elements.container.querySelector('#gp-categories');
        if (catContainer) catContainer.classList.add('hidden');

        const relevantMods = this.findRelevantMods(query);
        if (relevantMods.length > 0) {
            html += `
                <div class="gp-section gp-context-section">
                    <h3>⚡ Mod Context</h3>
                    <p class="hint">You have ${relevantMods.length} mod(s) active that might alter "${this.escapeHtml(query)}". If you're stuck, check these first.</p>
                    <div class="gp-mod-list">
                        ${relevantMods.map(m => `
                            <div class="gp-mod-item">
                                <span class="gp-mod-name">${this.escapeHtml(m)}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        this.elements.results.innerHTML = html;
        this.elements.results.classList.remove('hidden');
    },

    getPopularLinks(game) {
        if (game.includes('skyrim')) return ['Bleak Falls Barrow', 'Diplomatic Immunity', 'Stones of Barenziah', 'Dark Brotherhood', 'Thieves Guild'];
        if (game.includes('fallout4')) return ['The Molecular Level', 'Best Weapons', 'Bobbleheads', 'Magazines', 'Settlement Building'];
        if (game.includes('newvegas')) return ['Come Fly With Me', 'Snow Globes', 'Unique Weapons', 'Endings'];
        if (game.includes('starfield')) return ['Main Quest', 'Ship Building', 'Outposts', 'Companions'];
        return ['Main Quest', 'Walkthrough', 'Tips'];
    },

    findRelevantMods(query) {
        if (!window.userContext || !window.userContext.currentModListParsed) return [];
        const terms = query.toLowerCase().split(/\s+/).filter(t => t.length > 3);
        if (terms.length === 0) return [];

        return window.userContext.currentModListParsed.filter(mod => {
            const name = mod.toLowerCase();
            // Simple heuristic: if mod name contains significant part of query
            return terms.some(t => name.includes(t));
        });
    },

    escapeHtml(str) {
        if (!str) return '';
        return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
    }
};

// Expose to global scope
window.GameplayUI = GameplayUI;
