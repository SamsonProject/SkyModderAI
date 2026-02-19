/**
 * Feedback UI - User feedback collection for SkyModderAI
 * 
 * Provides:
 * - Rating widgets (1-5 stars)
 * - Feedback forms (bug reports, suggestions)
 * - Session tracking
 * - Post-session curation trigger
 */

// Session tracker
class SessionTracker {
    constructor(userEmail = null) {
        this.userEmail = userEmail;
        this.sessionId = this.generateSessionId();
        this.startTime = new Date();
        this.events = [];
        this.queries = [];
        this.resolutions = [];
        
        // Store session ID for later use
        sessionStorage.setItem('skymodder_session_id', this.sessionId);
    }
    
    generateSessionId() {
        return 'sess_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    }
    
    trackQuery(type, data) {
        this.queries.push({
            type: type,
            data: data,
            timestamp: new Date().toISOString()
        });
        
        this.events.push({
            event: 'query',
            type: type,
            timestamp: new Date().toISOString()
        });
    }
    
    trackResolution(type, data, helpful = true) {
        this.resolutions.push({
            type: type,
            data: data,
            helpful: helpful,
            timestamp: new Date().toISOString()
        });
    }
    
    trackAction(action, details = null) {
        this.events.push({
            event: 'action',
            action: action,
            details: details,
            timestamp: new Date().toISOString()
        });
    }
    
    getSessionSummary() {
        const duration = (new Date() - this.startTime) / 1000;
        
        return {
            session_id: this.sessionId,
            user_email: this.userEmail,
            start_time: this.startTime.toISOString(),
            end_time: new Date().toISOString(),
            duration_seconds: duration,
            query_count: this.queries.length,
            resolution_count: this.resolutions.length,
            event_count: this.events.length,
            queries: this.queries,
            resolutions: this.resolutions,
            events: this.events
        };
    }
    
    async saveSession() {
        try {
            const summary = this.getSessionSummary();
            
            // Send to backend (async, doesn't block)
            await fetch('/api/feedback/session', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(summary)
            });
            
            console.log('Session saved:', this.sessionId);
        } catch (error) {
            console.error('Failed to save session:', error);
        }
    }
}

// Feedback collector
class FeedbackCollector {
    constructor() {
        this.currentRating = null;
        this.currentFeedback = null;
    }
    
    /**
     * Create a rating widget
     * @param {string} containerId - ID of container element
     * @param {function} onRate - Callback when rated
     * @param {object} context - Context about what's being rated
     */
    createRatingWidget(containerId, onRate, context = {}) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        container.innerHTML = `
            <div class="feedback-rating-widget">
                <p class="feedback-prompt">Was this helpful?</p>
                <div class="star-rating">
                    ${[1, 2, 3, 4, 5].map(i => `
                        <button class="star-btn" data-rating="${i}" aria-label="Rate ${i} stars">
                            <span class="star">☆</span>
                        </button>
                    `).join('')}
                </div>
                <div class="feedback-status"></div>
            </div>
        `;
        
        const stars = container.querySelectorAll('.star-btn');
        const status = container.querySelector('.feedback-status');
        
        stars.forEach(star => {
            star.addEventListener('click', async (e) => {
                const rating = parseInt(e.currentTarget.dataset.rating);
                this.currentRating = rating;
                
                // Update visual
                stars.forEach((s, i) => {
                    const starSpan = s.querySelector('.star');
                    if (i < rating) {
                        starSpan.textContent = '★';
                        starSpan.classList.add('filled');
                    } else {
                        starSpan.textContent = '☆';
                        starSpan.classList.remove('filled');
                    }
                });
                
                // Submit rating
                status.textContent = 'Submitting...';
                try {
                    await this.submitRating(rating, context);
                    status.textContent = 'Thanks for your feedback!';
                    status.classList.add('success');
                    
                    if (onRate) onRate(rating);
                } catch (error) {
                    status.textContent = 'Failed to submit. Please try again.';
                    status.classList.add('error');
                }
            });
            
            star.addEventListener('mouseenter', () => {
                const rating = parseInt(star.dataset.rating);
                stars.forEach((s, i) => {
                    const starSpan = s.querySelector('.star');
                    if (i < rating) {
                        starSpan.textContent = '★';
                    } else {
                        starSpan.textContent = '☆';
                    }
                });
            });
        });
        
        container.addEventListener('mouseleave', () => {
            if (this.currentRating) {
                stars.forEach((s, i) => {
                    const starSpan = s.querySelector('.star');
                    if (i < this.currentRating) {
                        starSpan.textContent = '★';
                        starSpan.classList.add('filled');
                    } else {
                        starSpan.textContent = '☆';
                        starSpan.classList.remove('filled');
                    }
                });
            }
        });
    }
    
    /**
     * Submit a rating
     * @param {number} rating - 1-5 rating
     * @param {object} context - Context about what's being rated
     */
    async submitRating(rating, context = {}) {
        const response = await fetch('/api/feedback/rating', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                rating: rating,
                context: context,
                session_id: sessionStorage.getItem('skymodder_session_id')
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to submit rating');
        }
        
        return await response.json();
    }
    
    /**
     * Show feedback form modal
     * @param {string} type - "bug", "suggestion", "other"
     * @param {object} context - Context about the feedback
     */
    showFeedbackForm(type = 'other', context = {}) {
        const modal = document.createElement('div');
        modal.className = 'feedback-modal';
        modal.innerHTML = `
            <div class="feedback-modal-content">
                <div class="feedback-modal-header">
                    <h3>${this.getFeedbackTitle(type)}</h3>
                    <button class="feedback-close">&times;</button>
                </div>
                <div class="feedback-modal-body">
                    <form id="feedback-form">
                        <div class="form-group">
                            <label for="feedback-category">Category</label>
                            <select id="feedback-category" name="category" required>
                                ${this.getCategoryOptions(type)}
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="feedback-content">
                                ${this.getFeedbackLabel(type)}
                            </label>
                            <textarea 
                                id="feedback-content" 
                                name="content" 
                                rows="5" 
                                required
                                placeholder="${this.getFeedbackPlaceholder(type)}"
                            ></textarea>
                        </div>
                        <div class="form-group">
                            <label>
                                <input type="checkbox" name="anonymous" />
                                Submit anonymously
                            </label>
                        </div>
                        <div class="feedback-modal-footer">
                            <button type="button" class="feedback-cancel">Cancel</button>
                            <button type="submit" class="feedback-submit">Submit</button>
                        </div>
                    </form>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Event handlers
        const closeBtn = modal.querySelector('.feedback-close');
        const cancelBtn = modal.querySelector('.feedback-cancel');
        const form = modal.querySelector('#feedback-form');
        
        closeBtn.addEventListener('click', () => this.closeFeedbackForm(modal));
        cancelBtn.addEventListener('click', () => this.closeFeedbackForm(modal));
        modal.addEventListener('click', (e) => {
            if (e.target === modal) this.closeFeedbackForm(modal);
        });
        
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(form);
            
            const data = {
                type: type,
                category: formData.get('category'),
                content: formData.get('content'),
                anonymous: formData.get('anonymous') === 'on',
                context: context,
                session_id: sessionStorage.getItem('skymodder_session_id')
            };
            
            const submitBtn = modal.querySelector('.feedback-submit');
            submitBtn.textContent = 'Submitting...';
            submitBtn.disabled = true;
            
            try {
                await this.submitFeedback(data);
                this.closeFeedbackForm(modal);
                this.showFeedbackThanks();
            } catch (error) {
                submitBtn.textContent = 'Submit';
                submitBtn.disabled = false;
                alert('Failed to submit feedback. Please try again.');
            }
        });
        
        modal.classList.add('show');
    }
    
    getFeedbackTitle(type) {
        const titles = {
            'bug': 'Report a Bug',
            'suggestion': 'Suggest a Feature',
            'confusion': 'Report Confusion',
            'praise': 'Send Praise',
            'other': 'Send Feedback'
        };
        return titles[type] || 'Send Feedback';
    }
    
    getFeedbackLabel(type) {
        const labels = {
            'bug': 'Describe the bug you encountered',
            'suggestion': 'Describe your feature idea',
            'confusion': 'What was confusing?',
            'praise': 'What did you like?',
            'other': 'Your feedback'
        };
        return labels[type] || 'Your feedback';
    }
    
    getFeedbackPlaceholder(type) {
        const placeholders = {
            'bug': 'I was trying to... and instead...',
            'suggestion': 'It would be great if...',
            'confusion': 'I didn\'t understand...',
            'praise': 'I loved...',
            'other': 'Share your thoughts...'
        };
        return placeholders[type] || 'Share your thoughts...';
    }
    
    getCategoryOptions(type) {
        const categories = {
            'bug': [
                { value: 'crash', label: 'Crash' },
                { value: 'incorrect_result', label: 'Incorrect Result' },
                { value: 'ui_issue', label: 'UI Issue' },
                { value: 'performance', label: 'Performance' },
                { value: 'other', label: 'Other' }
            ],
            'suggestion': [
                { value: 'feature', label: 'New Feature' },
                { value: 'improvement', label: 'Improvement' },
                { value: 'ui_ux', label: 'UI/UX' },
                { value: 'content', label: 'Content' },
                { value: 'other', label: 'Other' }
            ],
            'confusion': [
                { value: 'ui', label: 'UI Confusion' },
                { value: 'instructions', label: 'Unclear Instructions' },
                { value: 'terminology', label: 'Confusing Terminology' },
                { value: 'other', label: 'Other' }
            ],
            'praise': [
                { value: 'accuracy', label: 'Accuracy' },
                { value: 'speed', label: 'Speed' },
                { value: 'ui', label: 'User Interface' },
                { value: 'helpfulness', label: 'Helpfulness' },
                { value: 'other', label: 'Other' }
            ],
            'other': [
                { value: 'general', label: 'General' },
                { value: 'support', label: 'Support' },
                { value: 'business', label: 'Business' },
                { value: 'other', label: 'Other' }
            ]
        };
        
        const opts = categories[type] || categories['other'];
        return opts.map(o => `<option value="${o.value}">${o.label}</option>`).join('');
    }
    
    closeFeedbackForm(modal) {
        modal.classList.remove('show');
        setTimeout(() => modal.remove(), 300);
    }
    
    showFeedbackThanks() {
        const toast = document.createElement('div');
        toast.className = 'feedback-toast';
        toast.textContent = 'Thanks for your feedback!';
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);
        
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
    
    /**
     * Submit feedback
     * @param {object} data - Feedback data
     */
    async submitFeedback(data) {
        const response = await fetch('/api/feedback/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error('Failed to submit feedback');
        }
        
        return await response.json();
    }
}

// Initialize feedback system
let sessionTracker = null;
let feedbackCollector = null;

function initFeedbackSystem(userEmail = null) {
    sessionTracker = new SessionTracker(userEmail);
    feedbackCollector = new FeedbackCollector();
    
    // Track page view
    sessionTracker.trackAction('page_view', {
        path: window.location.pathname
    });
    
    // Save session on page unload (async, doesn't block)
    window.addEventListener('beforeunload', () => {
        if (sessionTracker) {
            // Use sendBeacon for reliable delivery
            const summary = sessionTracker.getSessionSummary();
            const blob = new Blob([JSON.stringify(summary)], { type: 'application/json' });
            navigator.sendBeacon('/api/feedback/session', blob);
        }
    });
    
    return { sessionTracker, feedbackCollector };
}

// Export for use in other scripts
window.SkyModderFeedback = {
    init: initFeedbackSystem,
    getSessionTracker: () => sessionTracker,
    getFeedbackCollector: () => feedbackCollector
};

// Auto-init if DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        initFeedbackSystem(window.userEmail || null);
    });
} else {
    initFeedbackSystem(window.userEmail || null);
}
