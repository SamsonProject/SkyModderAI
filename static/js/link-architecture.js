/**
 * SkyModderAI — Floating Link Architecture & Smart Previews
 * Obsidian-style internal linking with hover previews
 */

// Simple logging utility (replaces console.log in production)
const Logger = window.Logger || (window.Logger = {
    debug: (...args) => { if (window.location.hostname === 'localhost') window.Logger.debug(...args); },
    info: (...args) => { if (window.location.hostname === 'localhost') window.Logger.info(...args); },
    warn: (...args) => { if (window.location.hostname === 'localhost') window.Logger.warn(...args); },
    error: (...args) => { window.Logger.error(...args); }
});

(function() {
    'use strict';

    // -----------------------------------------------------------------------
    // Configuration
    // -----------------------------------------------------------------------
    const LINK_PREVIEW_CONFIG = {
        delay: 300, // ms before showing preview
        hideDelay: 200, // ms before hiding preview
        maxWidth: 400,
        maxHeight: 300,
        offset: 10, // px from link
    };

    let previewTimeout = null;
    let hideTimeout = null;
    let currentPreview = null;

    // -----------------------------------------------------------------------
    // Link Preview Popover
    // -----------------------------------------------------------------------

    function initLinkPreviews() {
        // Create preview popover element
        const popover = document.createElement('div');
        popover.id = 'link-preview-popover';
        popover.className = 'link-preview-popover hidden';
        popover.setAttribute('role', 'tooltip');
        popover.setAttribute('aria-hidden', 'true');
        document.body.appendChild(popover);

        // Add event delegation for all links
        document.addEventListener('mouseover', handleLinkHover);
        document.addEventListener('mouseout', handleLinkLeave);
        document.addEventListener('click', handleLinkClick);
    }

    function handleLinkHover(e) {
        const link = e.target.closest('a[data-link-type]');
        if (!link) return;

        // Clear any pending hide
        if (hideTimeout) {
            clearTimeout(hideTimeout);
            hideTimeout = null;
        }

        // Show preview after delay
        previewTimeout = setTimeout(() => {
            showLinkPreview(link);
        }, LINK_PREVIEW_CONFIG.delay);
    }

    function handleLinkLeave(e) {
        const link = e.target.closest('a[data-link-type]');
        if (!link) return;

        // Clear pending show
        if (previewTimeout) {
            clearTimeout(previewTimeout);
            previewTimeout = null;
        }

        // Hide after delay
        hideTimeout = setTimeout(() => {
            hideLinkPreview();
        }, LINK_PREVIEW_CONFIG.hideDelay);
    }

    function handleLinkClick(e) {
        const link = e.target.closest('a[data-link-type]');
        if (!link) return;

        // Handle internal links specially
        if (link.dataset.linkType === 'internal') {
            e.preventDefault();
            navigateInternal(link.href);
            hideLinkPreview();
        }

        // Handle embedded content
        if (['youtube', 'imgur', 'vimeo'].includes(link.dataset.linkType)) {
            e.preventDefault();
            showEmbeddedContent(link);
        }
    }

    async function showLinkPreview(link) {
        const popover = document.getElementById('link-preview-popover');
        if (!popover) return;

        const linkType = link.dataset.linkType;
        let previewData = {};

        // Fetch preview data based on type
        try {
            if (linkType === 'nexus') {
                previewData = await fetchNexusPreview(
                    link.dataset.game,
                    link.dataset.modId
                );
            } else if (linkType === 'youtube') {
                previewData = getYouTubePreview(link.dataset.videoId);
            } else if (linkType === 'imgur') {
                previewData = getImgurPreview(link.dataset.imgId);
            } else if (linkType === 'internal') {
                previewData = getInternalPreview(link.dataset.preview);
            } else {
                previewData = { type: 'generic', url: link.href };
            }

            // Render preview
            renderPreview(popover, previewData, link);

            // Position and show
            positionPopover(popover, link);
            popover.classList.remove('hidden');
            popover.setAttribute('aria-hidden', 'false');

            currentPreview = popover;
        } catch (error) {
            Logger.warn('Link preview failed:', error);
        }
    }

    function hideLinkPreview() {
        const popover = document.getElementById('link-preview-popover');
        if (!popover) return;

        popover.classList.add('hidden');
        popover.setAttribute('aria-hidden', 'true');
        popover.innerHTML = '';
        currentPreview = null;
    }

    function positionPopover(popover, link) {
        const rect = link.getBoundingClientRect();
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;

        // Default: show below and to the right
        let top = rect.bottom + scrollTop + LINK_PREVIEW_CONFIG.offset;
        let left = rect.left + scrollLeft;

        // Check if we need to adjust position
        if (left + LINK_PREVIEW_CONFIG.maxWidth > window.innerWidth + scrollLeft) {
            left = window.innerWidth + scrollLeft - LINK_PREVIEW_CONFIG.maxWidth - 20;
        }

        if (top + LINK_PREVIEW_CONFIG.maxHeight > window.innerHeight + scrollTop) {
            // Show above instead
            top = rect.top + scrollTop - LINK_PREVIEW_CONFIG.maxHeight - LINK_PREVIEW_CONFIG.offset;
        }

        popover.style.top = `${top}px`;
        popover.style.left = `${left}px`;
        popover.style.maxWidth = `${LINK_PREVIEW_CONFIG.maxWidth}px`;
    }

    // -----------------------------------------------------------------------
    // Preview Data Fetchers
    // -----------------------------------------------------------------------

    async function fetchNexusPreview(game, modId) {
        try {
            const response = await fetch(`/api/link-preview/nexus/${game}/${modId}`);
            if (!response.ok) throw new Error('Failed to fetch');
            return await response.json();
        } catch (error) {
            Logger.warn('Nexus preview fetch failed:', error);
            return {
                type: 'nexus',
                loading: false,
                error: 'Could not load preview',
                fallback: `https://www.nexusmods.com/${game}/mods/${modId}`
            };
        }
    }

    function getYouTubePreview(videoId) {
        return {
            type: 'youtube',
            videoId: videoId,
            thumbnail: `https://img.youtube.com/vi/${videoId}/mqdefault.jpg`,
            embedUrl: `https://www.youtube.com/embed/${videoId}`,
            title: 'YouTube Video',
            canEmbed: true
        };
    }

    function getImgurPreview(imgId) {
        return {
            type: 'imgur',
            imgId: imgId,
            imageUrl: `https://i.imgur.com/${imgId}.jpg`,
            thumbnail: `https://i.imgur.com/${imgId}s.jpg`,
            canEmbed: true
        };
    }

    function getInternalPreview(page) {
        const sectionMap = {
            'analyze': { title: 'Mod Analysis', description: 'Analyze your mod list for conflicts' },
            'quickstart': { title: 'Quick Start', description: 'Get started with modding' },
            'build': { title: 'Build-a-List', description: 'Generate a mod list from preferences' },
            'library': { title: 'Library', description: 'Your saved mod lists' },
            'community': { title: 'Community', description: 'Community discussions and help' },
            'gameplay': { title: 'Gameplay', description: 'Gameplay engine and walkthroughs' },
            'dev': { title: 'Dev Tools', description: 'Developer tools and API' }
        };

        const section = sectionMap[page.toLowerCase()] || { title: page, description: '' };

        return {
            type: 'internal',
            page: page,
            title: section.title,
            description: section.description,
            url: `/#panel-${page.toLowerCase()}`
        };
    }

    // -----------------------------------------------------------------------
    // Preview Rendering
    // -----------------------------------------------------------------------

    function renderPreview(popover, data, link) {
        let html = '';

        if (data.type === 'nexus') {
            html = renderNexusPreview(data);
        } else if (data.type === 'youtube') {
            html = renderYouTubePreview(data);
        } else if (data.type === 'imgur') {
            html = renderImgurPreview(data);
        } else if (data.type === 'internal') {
            html = renderInternalPreview(data);
        } else {
            html = renderGenericPreview(data);
        }

        popover.innerHTML = html;
    }

    function renderNexusPreview(data) {
        if (data.loading) {
            return `
                <div class="preview-loading">
                    <div class="preview-spinner"></div>
                    <p>Loading mod info...</p>
                </div>
            `;
        }

        if (data.error) {
            return `
                <div class="preview-error">
                    <p>${data.error}</p>
                    <a href="${data.fallback}" target="_blank" rel="noopener">Open on Nexus →</a>
                </div>
            `;
        }

        return `
            <div class="preview-nexus">
                ${data.image ? `<img src="${data.image}" alt="${data.name}" class="preview-image">` : ''}
                <div class="preview-content">
                    <h4 class="preview-title">${data.name || 'Nexus Mod'}</h4>
                    ${data.author ? `<p class="preview-author">by ${data.author}</p>` : ''}
                    ${data.description ? `<p class="preview-description">${truncate(data.description, 150)}</p>` : ''}
                    <div class="preview-meta">
                        ${data.downloads ? `<span>⬇ ${formatNumber(data.downloads)}</span>` : ''}
                        ${data.endorsements ? `<span>👍 ${formatNumber(data.endorsements)}</span>` : ''}
                    </div>
                    <a href="${data.url}" target="_blank" rel="noopener" class="preview-link">View on Nexus →</a>
                </div>
            </div>
        `;
    }

    function renderYouTubePreview(data) {
        return `
            <div class="preview-youtube">
                <img src="${data.thumbnail}" alt="Video thumbnail" class="preview-thumbnail">
                <div class="preview-overlay">
                    <span class="play-button">▶</span>
                </div>
                <p class="preview-title">${data.title || 'YouTube Video'}</p>
            </div>
        `;
    }

    function renderImgurPreview(data) {
        return `
            <div class="preview-imgur">
                <img src="${data.imageUrl}" alt="Image preview" class="preview-image" loading="lazy">
            </div>
        `;
    }

    function renderInternalPreview(data) {
        return `
            <div class="preview-internal">
                <h4 class="preview-title">${data.title}</h4>
                ${data.description ? `<p class="preview-description">${data.description}</p>` : ''}
                <div class="preview-hint">Click to navigate</div>
            </div>
        `;
    }

    function renderGenericPreview(data) {
        return `
            <div class="preview-generic">
                <a href="${data.url}" target="_blank" rel="noopener">${data.url}</a>
            </div>
        `;
    }

    // -----------------------------------------------------------------------
    // Embedded Content
    // -----------------------------------------------------------------------

    function showEmbeddedContent(link) {
        const linkType = link.dataset.linkType;
        let embedHtml = '';

        if (linkType === 'youtube') {
            const videoId = link.dataset.videoId;
            embedHtml = `
                <div class="embedded-content embedded-youtube">
                    <iframe src="https://www.youtube.com/embed/${videoId}"
                            frameborder="0"
                            allowfullscreen
                            loading="lazy">
                    </iframe>
                </div>
            `;
        } else if (linkType === 'imgur') {
            const imgId = link.dataset.imgId;
            embedHtml = `
                <div class="embedded-content embedded-imgur">
                    <img src="https://i.imgur.com/${imgId}.jpg" alt="Imgur image" loading="lazy">
                </div>
            `;
        }

        // Insert after the link
        if (embedHtml) {
            const wrapper = document.createElement('div');
            wrapper.innerHTML = embedHtml;
            link.parentNode.insertBefore(wrapper, link.nextSibling);
        }
    }

    // -----------------------------------------------------------------------
    // Internal Navigation
    // -----------------------------------------------------------------------

    function navigateInternal(url) {
        // Smooth scroll to section
        if (url.startsWith('/#')) {
            const sectionId = url.substring(2);
            const section = document.getElementById(sectionId);
            if (section) {
                section.scrollIntoView({ behavior: 'smooth', block: 'start' });

                // Update URL without page jump
                history.pushState(null, '', url);

                // Trigger tab switch if needed
                const tabPanel = url.replace('/#panel-', '');
                const tab = document.querySelector(`.main-tab[data-tab="${tabPanel}"]`);
                if (tab) {
                    tab.click();
                }
            }
        } else {
            // Regular navigation
            window.location.href = url;
        }
    }

    // -----------------------------------------------------------------------
    // Utility Functions
    // -----------------------------------------------------------------------

    function truncate(text, maxLength) {
        if (!text) return '';
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    function formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }

    // -----------------------------------------------------------------------
    // Smart Link Detection in Text
    // -----------------------------------------------------------------------

    function processTextWithLinks(container) {
        if (!container) return;

        // Find all text nodes
        const textNodes = [];
        const walker = document.createTreeWalker(
            container,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );

        let node;
        while (node = walker.nextNode()) {
            if (node.textContent.trim() && node.parentNode.tagName !== 'SCRIPT') {
                textNodes.push(node);
            }
        }

        // Process each text node
        textNodes.forEach(textNode => {
            const html = processTextLinks(textNode.textContent);
            if (html !== textNode.textContent) {
                const wrapper = document.createElement('span');
                wrapper.innerHTML = html;
                textNode.parentNode.replaceChild(wrapper, textNode);
            }
        });
    }

    function processTextLinks(text) {
        let html = text;

        // Process [[Internal Links]]
        html = html.replace(/\[\[([^\]]+)\]\]/g, (match, p1) => {
            const page = p1.toLowerCase();
            return `<a href="/#panel-${page}" data-link-type="internal" data-preview="${p1}" class="internal-link">${p1}</a>`;
        });

        // Process Nexus URLs
        html = html.replace(
            /https?:\/\/(?:www\.)?nexusmods\.com\/([a-z]+)\/mods\/(\d+)/g,
            '<a href="$&" data-link-type="nexus" data-game="$1" data-mod-id="$2" class="external-link nexus-link" target="_blank" rel="noopener">Nexus Mod #$2</a>'
        );

        // Process YouTube URLs
        html = html.replace(
            /https?:\/\/(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]+)/g,
            '<a href="$&" data-link-type="youtube" data-video-id="$1" class="external-link youtube-link" target="_blank" rel="noopener">▶ Video</a>'
        );

        // Process Imgur URLs
        html = html.replace(
            /https?:\/\/(?:i\.)?imgur\.com\/([a-zA-Z0-9]+)/g,
            '<a href="$&" data-link-type="imgur" data-img-id="$1" class="external-link imgur-link" target="_blank" rel="noopener">📷 Image</a>'
        );

        return html;
    }

    // -----------------------------------------------------------------------
    // Initialize
    // -----------------------------------------------------------------------

    function init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
            return;
        }

        initLinkPreviews();

        // Process existing content
        document.querySelectorAll('.chat-messages, .community-content, .fix-guide-content').forEach(container => {
            processTextWithLinks(container);
        });

    }

    // Expose to global scope
    window.SkyLinkArchitecture = {
        processTextWithLinks,
        processTextLinks,
        showLinkPreview,
        hideLinkPreview,
        navigateInternal
    };

    init();

})();
