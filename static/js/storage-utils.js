/**
 * SkyModderAI - Local-First Storage Utilities
 *
 * Philosophy:
 * - Store user data in browser localStorage by default
 * - Compress data before storage (pako gzip)
 * - Optional cloud sync (user choice, requires account)
 * - Auto-save session data (every 30 seconds)
 * - Export/import functionality (user owns their data)
 */

// Simple logging utility (replaces console.log in production)
const Logger = window.Logger || (window.Logger = {
    debug: (...args) => { if (window.location.hostname === 'localhost') window.Logger.debug(...args); },
    info: (...args) => { if (window.location.hostname === 'localhost') window.Logger.info(...args); },
    warn: (...args) => { if (window.location.hostname === 'localhost') window.Logger.warn(...args); },
    error: (...args) => { window.Logger.error(...args); }
});

// Compression utilities (using pako.js for gzip)
const StorageUtils = {
    /**
     * Compress data before storage
     * @param {Object} data - JavaScript object to compress
     * @returns {string} Base64-encoded compressed data
     */
    compress(data) {
        try {
            const json = JSON.stringify(data);
            const compressed = pako.gzip(json, { level: 9 });
            // Convert Uint8Array to base64 for localStorage
            return btoa(String.fromCharCode(...compressed));
        } catch (e) {
            Logger.warn('Compression failed, storing uncompressed:', e);
            return JSON.stringify(data);
        }
    },

    /**
     * Decompress data after retrieval
     * @param {string} compressed - Base64-encoded compressed data
     * @returns {Object} Decompressed JavaScript object
     */
    decompress(compressed) {
        try {
            // Convert base64 to Uint8Array
            const binary = atob(compressed);
            const bytes = new Uint8Array(binary.length);
            for (let i = 0; i < binary.length; i++) {
                bytes[i] = binary.charCodeAt(i);
            }
            // Decompress
            const json = pako.ungzip(bytes, { to: 'string' });
            return JSON.parse(json);
        } catch (e) {
            Logger.warn('Decompression failed, trying uncompressed:', e);
            // Fallback: try parsing as uncompressed JSON
            try {
                return JSON.parse(compressed);
            } catch (e2) {
                Logger.error('Failed to parse data:', e2);
                return null;
            }
        }
    },

    /**
     * Smart setItem - compresses if data is large enough to warrant it
     * @param {string} key - Storage key
     * @param {any} value - Value to store
     * @param {boolean} forceCompress - Always compress (default: auto-detect)
     */
    setItem(key, value, forceCompress = false) {
        try {
            const json = JSON.stringify(value);
            const shouldCompress = forceCompress || json.length > 1024; // Compress if >1KB

            if (shouldCompress) {
                const compressed = this.compress(value);
                localStorage.setItem(key + '_compressed', '1');
                localStorage.setItem(key, compressed);
                
            } else {
                localStorage.setItem(key + '_compressed', '0');
                localStorage.setItem(key, json);
                
            }
        } catch (e) {
            Logger.error('[Storage] Failed to store:', e);
            // Handle quota exceeded
            if (e.name === 'QuotaExceededError') {
                this.handleQuotaExceeded();
            }
        }
    },

    /**
     * Smart getItem - auto-detects compression
     * @param {string} key - Storage key
     * @param {any} defaultValue - Default value if not found
     * @returns {any} Stored value or default
     */
    getItem(key, defaultValue = null) {
        try {
            const compressed = localStorage.getItem(key + '_compressed') === '1';
            const value = localStorage.getItem(key);

            if (!value) return defaultValue;

            return compressed ? this.decompress(value) : JSON.parse(value);
        } catch (e) {
            Logger.warn('[Storage] Failed to retrieve:', e);
            return defaultValue;
        }
    },

    /**
     * Remove item and its compression flag
     * @param {string} key - Storage key
     */
    removeItem(key) {
        localStorage.removeItem(key + '_compressed');
        localStorage.removeItem(key);
    },

    /**
     * Handle localStorage quota exceeded
     * Strategy: Clear old session data, keep user saves
     */
    handleQuotaExceeded() {
        Logger.warn('[Storage] Quota exceeded, clearing old session data...');
        
        // Clear session data (keep saved lists)
        const sessionKeys = [
            'current_mod_list',
            'recent_searches',
            'session_data',
            'ui_preferences'
        ];
        
        sessionKeys.forEach(key => {
            this.removeItem(key);
            
        });
        
        alert('Storage quota exceeded. Old session data has been cleared. Your saved lists are preserved.');
    },

    /**
     * Export all user data to downloadable JSON
     */
    exportData() {
        const exportData = {
            version: '1.0',
            exported_at: new Date().toISOString(),
            user_context: this.getItem('skymodder_userContext'),
            saved_lists: this.getItem('skymodder_saved_lists'),
            preferences: this.getItem('skymodder_preferences'),
            recent_searches: this.getItem('skymodder_recent_searches')
        };

        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `skymodderai-export-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
        
    },

    /**
     * Import user data from JSON file
     * @param {File} file - JSON file to import
     */
    importData(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    const data = JSON.parse(e.target.result);
                    
                    // Import each section
                    if (data.user_context) this.setItem('skymodder_userContext', data.user_context);
                    if (data.saved_lists) this.setItem('skymodder_saved_lists', data.saved_lists);
                    if (data.preferences) this.setItem('skymodder_preferences', data.preferences);
                    if (data.recent_searches) this.setItem('skymodder_recent_searches', data.recent_searches);
                    
                    resolve(data);
                } catch (err) {
                    Logger.error('[Storage] Import failed:', err);
                    reject(err);
                }
            };
            reader.onerror = reject;
            reader.readAsText(file);
        });
    },

    /**
     * Get storage usage statistics
     */
    getUsage() {
        let total = 0;
        let keys = [];
        
        for (let key in localStorage) {
            if (localStorage.hasOwnProperty(key)) {
                const value = localStorage.getItem(key);
                total += value.length;
                keys.push({ key, size: value.length });
            }
        }
        
        // Sort by size
        keys.sort((a, b) => b.size - a.size);
        
        return {
            total_bytes: total,
            total_kb: (total / 1024).toFixed(2),
            total_mb: (total / 1024 / 1024).toFixed(2),
            keys_count: Object.keys(localStorage).length,
            top_keys: keys.slice(0, 10) // Top 10 largest keys
        };
    },

    /**
     * Clear all SkyModderAI data (with confirmation)
     */
    clearAll() {
        if (!confirm('Are you sure you want to clear ALL local data? This cannot be undone.')) {
            return false;
        }
        
        const keys = Object.keys(localStorage);
        const skymodderKeys = keys.filter(k => k.startsWith('skymodder_') || k.startsWith('user_'));
        
        skymodderKeys.forEach(key => {
            localStorage.removeItem(key);
        });
        
        alert(`Cleared ${skymodderKeys.length} local storage items. Page will reload.`);
        location.reload();
        
        return true;
    }
};

// Auto-save manager
const AutoSaveManager = {
    interval: null,
    dirty: false,

    /**
     * Start auto-save loop
     * @param {number} intervalMs - Save interval in milliseconds (default: 30000 = 30s)
     */
    start(intervalMs = 30000) {
        
        this.interval = setInterval(() => {
            if (this.dirty) {
                this.save();
                this.dirty = false;
            }
        }, intervalMs);

        // Save before page unload
        window.addEventListener('beforeunload', () => {
            if (this.dirty) {
                this.save();
            }
        });
    },

    /**
     * Mark data as dirty (needs saving)
     */
    markDirty() {
        this.dirty = true;
    },

    /**
     * Save current session data
     */
    save() {
        // Save current mod list
        if (typeof userContext !== 'undefined') {
            StorageUtils.setItem('skymodder_current_mod_list', {
                list: userContext.currentModList,
                game: userContext.selectedGame,
                timestamp: Date.now()
            });
        }
        
    },

    /**
     * Stop auto-save loop
     */
    stop() {
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    
    // Start auto-save
    AutoSaveManager.start(30000); // 30 seconds
    
    // Log storage usage on load
    const usage = StorageUtils.getUsage();
    
    
    // Add storage management to dev tools (if available)
    if (typeof window.__DEV_TOOLS__ !== 'undefined') {
        window.__DEV_TOOLS__.storage = {
            utils: StorageUtils,
            autoSave: AutoSaveManager,
            usage: StorageUtils.getUsage()
        };
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { StorageUtils, AutoSaveManager };
}
