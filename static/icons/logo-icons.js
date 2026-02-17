/**
 * Rotating SkyModderAI logos for header/branding.
 * Uses Imgur-hosted logos; picks one at random on each page load.
 * Offline fallback: local SVG when Imgur fails (no internet).
 */
(function () {
    const LOGO_URLS = [
        'https://i.imgur.com/Bva2jjl.png',
        'https://i.imgur.com/A2zyIzA.png',
        'https://i.imgur.com/i5ps4Rl.png',
        'https://i.imgur.com/Qvaglbg.png',
        'https://i.imgur.com/wRMm4CC.png',
        'https://i.imgur.com/LK8k1ck.png',
        'https://i.imgur.com/SmYtlCE.png'
    ];

    const FALLBACK_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32"><defs><linearGradient id="lg" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" style="stop-color:#00d9ff"/><stop offset="100%" style="stop-color:#7c3aed"/></linearGradient></defs><rect width="32" height="32" rx="8" fill="transparent"/><text x="16" y="22" font-family="system-ui,sans-serif" font-size="18" font-weight="bold" fill="url(#lg)" text-anchor="middle">S</text></svg>';

    function pickRandomLogo() {
        return LOGO_URLS[Math.floor(Math.random() * LOGO_URLS.length)];
    }

    function showFallback(el) {
        el.innerHTML = FALLBACK_SVG;
        el.classList.add('logo-fallback');
    }

    function initLogoIcons() {
        document.querySelectorAll('.logo-icon-rotate').forEach(function (el) {
            var img = document.createElement('img');
            img.src = pickRandomLogo();
            img.alt = 'SkyModderAI';
            img.onerror = function () {
                el.innerHTML = '';
                showFallback(el);
            };
            el.innerHTML = '';
            el.appendChild(img);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initLogoIcons);
    } else {
        initLogoIcons();
    }
})();
