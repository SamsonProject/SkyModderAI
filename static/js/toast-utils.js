/**
 * Toast Notification System
 * Replaces alert() with non-blocking, user-friendly notifications
 */

(function() {
    'use strict';

    // Toast container
    let toastContainer = null;

    // Get or create toast container
    function getContainer() {
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 99999;
                display: flex;
                flex-direction: column;
                gap: 0.75rem;
                pointer-events: none;
            `;
            document.body.appendChild(toastContainer);
        }
        return toastContainer;
    }

    // Create toast element
    function createToast(message, type = 'info', duration = 5000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ'
        };

        const colors = {
            success: 'linear-gradient(135deg, #10b981, #059669)',
            error: 'linear-gradient(135deg, #ef4444, #dc2626)',
            warning: 'linear-gradient(135deg, #f59e0b, #d97706)',
            info: 'linear-gradient(135deg, #3b82f6, #2563eb)'
        };

        toast.style.cssText = `
            background: ${colors[type]};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
            display: flex;
            align-items: center;
            gap: 0.75rem;
            min-width: 300px;
            max-width: 500px;
            pointer-events: auto;
            animation: slideIn 0.3s ease;
            cursor: pointer;
        `;

        toast.innerHTML = `
            <span style="font-size: 1.25rem; font-weight: 700;">${icons[type]}</span>
            <span style="flex: 1; font-size: 0.9375rem; line-height: 1.5;">${message}</span>
            <button onclick="this.closest('.toast').remove()" style="background: transparent; border: none; color: white; font-size: 1.25rem; cursor: pointer; padding: 0; line-height: 1; opacity: 0.7;">&times;</button>
        `;

        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => {
                toast.style.opacity = '0';
                toast.style.transition = 'opacity 0.3s ease';
                setTimeout(() => toast.remove(), 300);
            }, duration);
        }

        // Click to dismiss
        toast.addEventListener('click', (e) => {
            if (e.target.tagName !== 'BUTTON') {
                toast.remove();
            }
        });

        return toast;
    }

    // Show toast
    function showToast(message, type = 'info', duration = 5000) {
        const container = getContainer();
        const toast = createToast(message, type, duration);
        container.appendChild(toast);

        // Limit to 5 toasts max
        while (container.children.length > 5) {
            container.removeChild(container.firstChild);
        }
    }

    // Convenience methods
    window.showToast = showToast;
    window.showSuccess = (msg, duration) => showToast(msg, 'success', duration);
    window.showError = (msg, duration) => showToast(msg, 'error', duration);
    window.showWarning = (msg, duration) => showToast(msg, 'warning', duration);
    window.showInfo = (msg, duration) => showToast(msg, 'info', duration);

    // Add CSS animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
    `;
    document.head.appendChild(style);

})();
