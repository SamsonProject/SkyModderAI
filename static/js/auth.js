(function () {
    let emailCache = new Set();
    
    function showMessage(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 5000);
    }
    
    function detectExistingAccount(email) {
        return emailCache.has(email) || 
               (localStorage.getItem('knownEmails') || '').split(',').includes(email);
    }
    
    function trackKnownEmail(email) {
        if (!email || !email.includes('@')) return;
        emailCache.add(email);
        const knownEmails = new Set((localStorage.getItem('knownEmails') || '').split(',').filter(Boolean));
        knownEmails.add(email);
        localStorage.setItem('knownEmails', Array.from(knownEmails).join(','));
    }

    function handleUrlErrors() {
        var params = new URLSearchParams(window.location.search);
        var error = params.get('error');
        var plan = (params.get('plan') || '').toLowerCase();
        if (plan === 'openclaw' || plan === 'claw') {
            showMessage('OpenClaw Lab is experimental and high risk. Please review the GitHub implementation and make backups before purchasing.');
        }
        if (error === 'invalid_or_expired') {
            showMessage('That verification link is invalid or expired. Enter your email again for a new link.');
        } else if (error === 'missing_token') {
            showMessage('Missing verification link. Enter your email for a new one.');
        }
        if (error && window.history.replaceState) {
            window.history.replaceState({}, '', window.location.pathname);
        }
    }

    function switchToLogin(email = '') {
        document.getElementById('login-email').value = email;
        document.getElementById('login-tab').click();
        if (email) {
            document.getElementById('login-password').focus();
        }
    }
    
    function switchToSignup(email = '') {
        document.getElementById('signup-email').value = email;
        document.getElementById('signup-tab').click();
        if (email) {
            document.getElementById('signup-password').focus();
        }
    }
    
    async function onLoginSubmit(e) {
        e.preventDefault();
        const emailInput = document.getElementById('login-email');
        const passwordInput = document.getElementById('login-password');
        const rememberInput = document.getElementById('login-remember');
        const btn = document.getElementById('login-submit-btn');
        if (!emailInput || !passwordInput || !btn) return;
        
        const email = emailInput.value.trim().toLowerCase();
        if (!email || !email.includes('@')) {
            showMessage('Please enter a valid email address', 'error');
            return;
        }

        const password = passwordInput.value;
        if (!password) {
            showMessage('Please enter your password', 'error');
            return;
        }

        btn.disabled = true;
        btn.textContent = 'Logging in…';
        try {
            var next = new URLSearchParams(window.location.search).get('next') || '';
            var endpoint = '/api/login' + (next ? '?next=' + encodeURIComponent(next) : '');
            var res = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: email,
                    password: password,
                    remember_me: !!(rememberInput && rememberInput.checked)
                })
            });
            var data = await res.json().catch(function () { return {}; });
            if (!res.ok) {
                showMessage(data.error || 'Login failed.');
                return;
            }
            window.location.href = data.redirect || '/';
        } catch (err) {
            showMessage('Network error. Try again.');
        } finally {
            btn.disabled = false;
            btn.textContent = 'Log in';
        }
    }

    async function onSignupSubmit(e) {
        e.preventDefault();
        var emailInput = document.getElementById('signup-email');
        var passwordInput = document.getElementById('signup-password');
        var confirmInput = document.getElementById('signup-confirm');
        var btn = document.getElementById('signup-submit-btn');
        var successDiv = document.getElementById('signup-success');
        if (!emailInput || !passwordInput || !confirmInput || !btn || !successDiv) return;

        var email = emailInput.value.trim();
        var password = passwordInput.value;
        var confirm = confirmInput.value;
        if (!email || email.indexOf('@') === -1) return;
        if (password.length < 8) {
            showMessage('Password must be at least 8 characters.');
            return;
        }
        if (password !== confirm) {
            showMessage('Passwords do not match.');
            return;
        }

        btn.disabled = true;
        btn.textContent = 'Sending…';
        successDiv.classList.add('hidden');
        try {
            var res = await fetch('/api/signup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: email,
                    password: password || undefined,
                    confirm: confirm || undefined
                })
            });
            var data = await res.json().catch(function () { return {}; });
            if (!res.ok) {
                showMessage(data.error || 'Something went wrong.');
                return;
            }
            successDiv.classList.remove('hidden');
        } catch (err) {
            showMessage('Network error. Try again.');
        } finally {
            btn.disabled = false;
            btn.textContent = 'Send verification email';
        }
    }

    // Initialize email autofill and detection
    function initEmailAutofill() {
        const emailInputs = document.querySelectorAll('input[type="email"]');
        emailInputs.forEach(input => {
            // Auto-focus first email field
            if (document.activeElement.tagName !== 'INPUT') {
                input.focus();
            }
            
            // Check for existing account on blur
            input.addEventListener('blur', (e) => {
                const email = e.target.value.trim().toLowerCase();
                if (!email || !email.includes('@')) return;
                
                if (e.target.id === 'signup-email' && detectExistingAccount(email)) {
                    showMessage('You already have an account. Switching to login...', 'info');
                    setTimeout(() => switchToLogin(email), 800);
                }
            });
            
            // Auto-detect email provider
            input.addEventListener('input', (e) => {
                const email = e.target.value.toLowerCase();
                if (email.includes('@')) {
                    const domain = email.split('@')[1];
                    if (['gmail.com', 'outlook.com', 'yahoo.com', 'proton.me'].some(d => domain.includes(d))) {
                        trackKnownEmail(email);
                    }
                }
            });
        });
        
        // Tab switching
        const tabs = document.querySelectorAll('[role="tab"]');
        tabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                const target = e.target.getAttribute('aria-controls');
                document.querySelectorAll('[role="tabpanel"]').forEach(panel => {
                    panel.classList.toggle('active', panel.id === target);
                });
                tabs.forEach(t => t.classList.toggle('active', t === e.target));
            });
        });
    }
    
    // Initialize everything
    document.addEventListener('DOMContentLoaded', () => {
        handleUrlErrors();
        
        const loginForm = document.getElementById('login-form');
        if (loginForm) loginForm.addEventListener('submit', onLoginSubmit);
        
        const signupForm = document.getElementById('signup-pro-form');
        if (signupForm) signupForm.addEventListener('submit', onSignupSubmit);
        
        initEmailAutofill();
        
        // Check URL for email parameter
        const urlParams = new URLSearchParams(window.location.search);
        const email = urlParams.get('email');
        if (email) {
            if (urlParams.get('action') === 'signup') {
                switchToSignup(email);
            } else {
                switchToLogin(email);
            }
        }
    });
})();
