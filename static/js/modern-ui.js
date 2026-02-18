/**
 * SkyModderAI - Modern UI Enhancements
 * Smooth animations, micro-interactions, and visual polish
 */

(function() {
    'use strict';

    // -----------------------------------------------------------------------
    // Utility Functions
    // -----------------------------------------------------------------------
    
    function $(selector) {
        return document.querySelector(selector);
    }
    
    function $$(selector) {
        return document.querySelectorAll(selector);
    }
    
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    function throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    // -----------------------------------------------------------------------
    // Smooth Scroll Animations
    // -----------------------------------------------------------------------
    
    function initScrollAnimations() {
        const observerOptions = {
            root: null,
            rootMargin: '0px',
            threshold: 0.1
        };
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);
        
        // Observe sections
        $$('.tool-section, .hero, .input-panel, .results-panel').forEach(el => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(20px)';
            el.style.transition = 'opacity 0.6s cubic-bezier(0.4, 0, 0.2, 1), transform 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
            observer.observe(el);
        });
    }

    // -----------------------------------------------------------------------
    // Button Ripple Effect
    // -----------------------------------------------------------------------
    
    function initRippleEffect() {
        $$('.primary-button, .secondary-button, .cta-button').forEach(button => {
            button.addEventListener('click', function(e) {
                const rect = button.getBoundingClientRect();
                const ripple = document.createElement('span');
                const size = Math.max(rect.width, rect.height);
                const x = e.clientX - rect.left - size / 2;
                const y = e.clientY - rect.top - size / 2;
                
                ripple.style.cssText = `
                    position: absolute;
                    width: ${size}px;
                    height: ${size}px;
                    left: ${x}px;
                    top: ${y}px;
                    background: rgba(255, 255, 255, 0.3);
                    border-radius: 50%;
                    transform: scale(0);
                    animation: ripple 0.6s ease-out;
                    pointer-events: none;
                `;
                
                button.style.position = 'relative';
                button.style.overflow = 'hidden';
                button.appendChild(ripple);
                
                setTimeout(() => ripple.remove(), 600);
            });
        });
        
        // Add ripple keyframes
        if (!$('#ripple-styles')) {
            const style = document.createElement('style');
            style.id = 'ripple-styles';
            style.textContent = `
                @keyframes ripple {
                    to {
                        transform: scale(4);
                        opacity: 0;
                    }
                }
            `;
            document.head.appendChild(style);
        }
    }

    // -----------------------------------------------------------------------
    // Input Panel Enhancements
    // -----------------------------------------------------------------------
    
    function initInputEnhancements() {
        const textarea = $('#mod-list-input');
        if (!textarea) return;
        
        // Auto-resize textarea
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 400) + 'px';
        });
        
        // Glow effect on focus
        textarea.addEventListener('focus', function() {
            this.parentElement.classList.add('input-focused');
        });
        
        textarea.addEventListener('blur', function() {
            this.parentElement.classList.remove('input-focused');
        });
        
        // Character count animation
        const modCount = $('#mod-count');
        if (modCount) {
            const observer = new MutationObserver(mutations => {
                mutations.forEach(mutation => {
                    if (mutation.type === 'characterData' || mutation.type === 'childList') {
                        modCount.style.transform = 'scale(1.1)';
                        modCount.style.transition = 'transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1)';
                        setTimeout(() => {
                            modCount.style.transform = 'scale(1)';
                        }, 200);
                    }
                });
            });
            
            observer.observe(modCount, { 
                characterData: true, 
                childList: true,
                subtree: true 
            });
        }
    }

    // -----------------------------------------------------------------------
    // Tab Transitions
    // -----------------------------------------------------------------------
    
    function initTabTransitions() {
        $$('.main-tab').forEach(tab => {
            tab.addEventListener('click', function() {
                const tabPanel = $(`#panel-${this.dataset.tab}`);
                if (tabPanel) {
                    tabPanel.style.animation = 'none';
                    tabPanel.offsetHeight; // Trigger reflow
                    tabPanel.style.animation = 'slideUp 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
                }
            });
        });
    }

    // -----------------------------------------------------------------------
    // Conflict Item Animations
    // -----------------------------------------------------------------------
    
    function initConflictAnimations() {
        const container = $('#conflicts-container');
        if (!container) return;
        
        const observer = new MutationObserver(mutations => {
            mutations.forEach(mutation => {
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach(node => {
                        if (node.nodeType === 1 && node.classList.contains('conflict-item')) {
                            node.style.opacity = '0';
                            node.style.transform = 'translateX(-20px)';
                            setTimeout(() => {
                                node.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                                node.style.opacity = '1';
                                node.style.transform = 'translateX(0)';
                            }, 50);
                        }
                    });
                }
            });
        });
        
        observer.observe(container, { childList: true });
    }

    // -----------------------------------------------------------------------
    // Loading Overlay Enhancement
    // -----------------------------------------------------------------------
    
    function initLoadingOverlay() {
        const overlay = $('#loading-overlay');
        if (!overlay) return;
        
        // Add pulse animation to loading text
        const loadingText = overlay.querySelector('p');
        if (loadingText) {
            loadingText.style.animation = 'pulse 2s ease-in-out infinite';
        }
        
        // Enhanced spinner with trail
        const spinner = overlay.querySelector('.spinner');
        if (spinner && !spinner.classList.contains('spinner-enhanced')) {
            spinner.classList.add('spinner-enhanced');
            spinner.style.background = 'conic-gradient(from 0deg, transparent 0deg, rgba(6, 182, 212, 0.3) 360deg)';
        }
    }

    // -----------------------------------------------------------------------
    // Search Input Enhancement
    // -----------------------------------------------------------------------
    
    function initSearchEnhancements() {
        const searchInput = $('#mod-search-input');
        if (!searchInput) return;
        
        // Floating label effect
        searchInput.addEventListener('focus', function() {
            this.parentElement.classList.add('search-focused');
        });
        
        searchInput.addEventListener('blur', function() {
            if (!this.value) {
                this.parentElement.classList.remove('search-focused');
            }
        });
    }

    // -----------------------------------------------------------------------
    // Stats Counter Animation
    // -----------------------------------------------------------------------
    
    function animateCounter(element, target, duration = 1000) {
        const start = 0;
        const increment = target / (duration / 16);
        let current = start;
        
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                current = target;
                clearInterval(timer);
            }
            element.textContent = Math.floor(current);
        }, 16);
    }
    
    function initStatsAnimation() {
        const stats = $$('.stat .count');
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const target = parseInt(entry.target.textContent) || 0;
                    if (target > 0) {
                        entry.target.textContent = '0';
                        animateCounter(entry.target, target, 800);
                    }
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });
        
        stats.forEach(stat => observer.observe(stat));
    }

    // -----------------------------------------------------------------------
    // Card Hover Effects
    // -----------------------------------------------------------------------
    
    function initCardEffects() {
        $$('.mod-preview-card, .library-card, .conflict-item').forEach(card => {
            card.addEventListener('mousemove', function(e) {
                const rect = card.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                card.style.setProperty('--mouse-x', `${x}px`);
                card.style.setProperty('--mouse-y', `${y}px`);
            });
        });
    }

    // -----------------------------------------------------------------------
    // Keyboard Shortcuts Visual Feedback
    // -----------------------------------------------------------------------
    
    function initKeyboardFeedback() {
        document.addEventListener('keydown', (e) => {
            // Visual feedback for Ctrl+Enter
            if (e.ctrlKey && e.key === 'Enter') {
                const analyzeBtn = $('#analyze-btn');
                if (analyzeBtn) {
                    analyzeBtn.style.transform = 'scale(0.95)';
                    setTimeout(() => {
                        analyzeBtn.style.transform = 'scale(1)';
                    }, 150);
                }
            }
            
            // Command palette trigger
            if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                e.preventDefault();
                const palette = $('#command-palette-trigger');
                if (palette) {
                    palette.click();
                }
            }
        });
    }

    // -----------------------------------------------------------------------
    // Toast Notifications (Modern)
    // -----------------------------------------------------------------------
    
    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        toast.style.cssText = `
            position: fixed;
            bottom: 24px;
            right: 24px;
            padding: 16px 24px;
            background: var(--bg-card, #0f172a);
            backdrop-filter: blur(10px);
            border: 1px solid var(--border, rgba(51, 65, 85, 0.5));
            border-left: 4px solid ${type === 'success' ? 'var(--success, #10b981)' : type === 'error' ? 'var(--error, #ef4444)' : 'var(--info, #3b82f6)'};
            border-radius: 10px;
            color: var(--text-primary, #f8fafc);
            font-weight: 500;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
            z-index: 10000;
            animation: slideInRight 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideOutRight 0.3s ease forwards';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
    
    // Add toast animations
    if (!$('#toast-styles')) {
        const style = document.createElement('style');
        style.id = 'toast-styles';
        style.textContent = `
            @keyframes slideInRight {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            @keyframes slideOutRight {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(100%);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    // Expose to global scope
    window.showToast = showToast;

    // -----------------------------------------------------------------------
    // Particle Background Effect (Optional Enhancement)
    // -----------------------------------------------------------------------
    
    function initParticles() {
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            return; // Respect user preferences
        }
        
        const hero = $('.hero');
        if (!hero) return;
        
        const particleCount = 20;
        
        for (let i = 0; i < particleCount; i++) {
            const particle = document.createElement('div');
            particle.className = 'hero-particle';
            
            const size = Math.random() * 4 + 2;
            const x = Math.random() * 100;
            const y = Math.random() * 100;
            const duration = Math.random() * 20 + 10;
            const delay = Math.random() * 5;
            
            particle.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                background: radial-gradient(circle, rgba(6, 182, 212, 0.6), transparent);
                border-radius: 50%;
                left: ${x}%;
                top: ${y}%;
                animation: particleFloat ${duration}s ease-in-out infinite;
                animation-delay: ${delay}s;
                opacity: ${Math.random() * 0.5 + 0.2};
                pointer-events: none;
            `;
            
            hero.appendChild(particle);
        }
        
        // Add particle animation
        if (!$('#particle-styles')) {
            const style = document.createElement('style');
            style.id = 'particle-styles';
            style.textContent = `
                @keyframes particleFloat {
                    0%, 100% {
                        transform: translate(0, 0) scale(1);
                        opacity: 0.3;
                    }
                    25% {
                        transform: translate(10%, 10%) scale(1.2);
                        opacity: 0.5;
                    }
                    50% {
                        transform: translate(-5%, 15%) scale(0.8);
                        opacity: 0.4;
                    }
                    75% {
                        transform: translate(15%, -10%) scale(1.1);
                        opacity: 0.6;
                    }
                }
            `;
            document.head.appendChild(style);
        }
    }

    // -----------------------------------------------------------------------
    // Recommendation Cards Animation
    // -----------------------------------------------------------------------
    
    function initRecommendationsAnimation() {
        const strip = $('#recommendations-strip');
        if (!strip) return;
        
        const observer = new MutationObserver(mutations => {
            mutations.forEach(mutation => {
                if (mutation.type === 'attributes' && 
                    mutation.attributeName === 'class' && 
                    !strip.classList.contains('hidden')) {
                    
                    const cards = $$('.mod-preview-card', strip);
                    cards.forEach((card, index) => {
                        card.style.opacity = '0';
                        card.style.transform = 'translateY(20px)';
                        setTimeout(() => {
                            card.style.transition = `opacity 0.4s ease ${index * 0.1}s, transform 0.4s ease ${index * 0.1}s`;
                            card.style.opacity = '1';
                            card.style.transform = 'translateY(0)';
                        }, 100);
                    });
                }
            });
        });
        
        observer.observe(strip, { attributes: true });
    }

    // -----------------------------------------------------------------------
    // Initialize All Enhancements
    // -----------------------------------------------------------------------
    
    function init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
            return;
        }
        
        // Initialize all enhancements
        initScrollAnimations();
        initRippleEffect();
        initInputEnhancements();
        initTabTransitions();
        initConflictAnimations();
        initLoadingOverlay();
        initSearchEnhancements();
        initStatsAnimation();
        initCardEffects();
        initKeyboardFeedback();
        initParticles();
        initRecommendationsAnimation();
        
        // Log initialization
        console.log('✨ SkyModderAI Modern UI initialized');
    }
    
    // Start initialization
    init();
    
})();
