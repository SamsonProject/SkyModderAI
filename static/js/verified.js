(function () {
    var checkoutBtn = document.getElementById('go-to-checkout-btn');
    if (!checkoutBtn) return;

    function showMessage(message, type) {
        type = type || 'info';
        if (window.showToast) {
            window.showToast(message, type);
            return;
        }
        // Fallback toast
        var toast = document.createElement('div');
        toast.className = 'toast toast-' + type;
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(function () { toast.classList.add('visible'); }, 10);
        setTimeout(function () { toast.classList.remove('visible'); }, 4000);
        setTimeout(function () { toast.remove(); }, 4300);
    }

    async function beginCheckout(plan) {
        var body = { plan: plan || 'pro' };
        var res = await fetch('/api/create-checkout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        var data = await res.json().catch(function () { return {}; });
        if (res.ok && data.checkout_url) {
            window.location.href = data.checkout_url;
            return true;
        }
        showMessage(data.error || 'Something went wrong.', 'error');
        return false;
    }

    checkoutBtn.addEventListener('click', async function () {
        checkoutBtn.disabled = true;
        checkoutBtn.textContent = 'Redirecting…';
        try {
            await beginCheckout('pro');
        } catch (err) {
            showMessage('Network error. Try again.', 'error');
        } finally {
            checkoutBtn.disabled = false;
            checkoutBtn.textContent = 'Go to Pro checkout — $5/month';
        }
    });

    var openclawBtn = document.getElementById('go-to-openclaw-checkout-btn');
    if (!openclawBtn) return;
    var openclawEnabled = openclawBtn.dataset.openclawEnabled === '1';
    var ackRepo = document.getElementById('openclaw-ack-repo');
    var ackBackup = document.getElementById('openclaw-ack-backup');
    var ackRisk = document.getElementById('openclaw-ack-risk');

    function updateOpenclawButtonState() {
        if (!openclawBtn || !ackRepo || !ackBackup || !ackRisk) return;
        openclawBtn.disabled = !openclawEnabled || !(ackRepo.checked && ackBackup.checked && ackRisk.checked);
    }
    [ackRepo, ackBackup, ackRisk].forEach(function (el) {
        if (el) el.addEventListener('change', updateOpenclawButtonState);
    });
    updateOpenclawButtonState();

    openclawBtn.addEventListener('click', async function () {
        if (!ackRepo?.checked || !ackBackup?.checked || !ackRisk?.checked) {
            showMessage('You must confirm all OpenClaw safety acknowledgements first.', 'warning');
            return;
        }
        openclawBtn.disabled = true;
        openclawBtn.textContent = 'Redirecting…';
        try {
            var ackRes = await fetch('/api/openclaw/request-access', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    acknowledgements: {
                        read_repo_code: true,
                        confirmed_backups: true,
                        accepts_experimental_risk: true
                    }
                })
            });
            var ackData = await ackRes.json().catch(function () { return {}; });
            if (!ackRes.ok) {
                showMessage(ackData.error || 'OpenClaw acknowledgements were not accepted.', 'error');
                return;
            }
            if (ackData.grant_token) {
                try { localStorage.setItem('openclaw_grant_token', ackData.grant_token); } catch (_) { }
            }
            await beginCheckout('openclaw');
        } catch (err) {
            showMessage('Network error. Try again.', 'error');
        } finally {
            openclawBtn.textContent = 'Go to OpenClaw Lab checkout';
            updateOpenclawButtonState();
        }
    });
})();
