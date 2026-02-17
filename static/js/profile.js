(function () {
    function showMessage(message, type) {
        type = type || 'info';
        if (window.showToast) {
            window.showToast(message, type);
            return;
        }
        // Fallback toast if app.js isn't loaded
        var toast = document.createElement('div');
        toast.className = 'toast toast-' + type;
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(function () { toast.classList.add('visible'); }, 10);
        setTimeout(function () { toast.classList.remove('visible'); }, 4000);
        setTimeout(function () { toast.remove(); }, 4300);
    }

    async function revokeSession(btn) {
        var li = btn.closest('.profile-session-item');
        var displayId = li && li.getAttribute('data-display-id');
        if (!displayId) return;
        btn.disabled = true;
        try {
            var res = await fetch('/api/sessions/revoke', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ display_id: displayId })
            });
            var data = await res.json().catch(function () { return {}; });
            if (res.ok && data.success) {
                li.remove();
            } else {
                showMessage(data.error || 'Failed to revoke session.', 'error');
                btn.disabled = false;
            }
        } catch (err) {
            showMessage('Network error.', 'error');
            btn.disabled = false;
        }
    }

    async function revokeOtherSessions(btn) {
        if (!confirm("Sign out on all other devices? You'll stay signed in here.")) return;
        btn.disabled = true;
        try {
            var res = await fetch('/api/sessions/revoke-others', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            var data = await res.json().catch(function () { return {}; });
            if (res.ok && data.success) {
                document.querySelectorAll('.profile-sessions-list .profile-session-item').forEach(function (li) {
                    if (li.getAttribute('data-current') !== 'true') li.remove();
                });
                btn.remove();
            } else {
                showMessage(data.error || 'Failed to revoke other sessions.', 'error');
                btn.disabled = false;
            }
        } catch (err) {
            showMessage('Network error.', 'error');
            btn.disabled = false;
        }
    }

    async function revokeApiKey(btn, keyId) {
        if (!confirm('Revoke this API key? Any tools using it will stop working.')) return;
        btn.disabled = true;
        try {
            var res = await fetch('/api/developer/keys/' + keyId, { method: 'DELETE' });
            var data = await res.json().catch(function () { return {}; });
            if (res.ok && data.success) {
                var li = btn.closest('.profile-api-item');
                if (li) li.remove();
            } else {
                showMessage(data.error || 'Failed to revoke key.', 'error');
                btn.disabled = false;
            }
        } catch (err) {
            showMessage('Network error.', 'error');
            btn.disabled = false;
        }
    }

    function attachRevokeButtons(scope) {
        scope.querySelectorAll('.api-key-revoke').forEach(function (btn) {
            if (btn.dataset.bound === '1') return;
            btn.dataset.bound = '1';
            btn.addEventListener('click', function () {
                var li = btn.closest('.profile-api-item');
                var keyId = li && li.getAttribute('data-key-id');
                if (!keyId) return;
                revokeApiKey(btn, keyId);
            });
        });
    }

    async function createApiKey(btn, labelInput, newKeyBox, newKeyValue) {
        var label = labelInput ? labelInput.value.trim() : '';
        btn.disabled = true;
        try {
            var res = await fetch('/api/developer/keys', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ label: label })
            });
            var data = await res.json().catch(function () { return {}; });
            if (!res.ok || !data.key) {
                showMessage(data.error || 'Failed to create API key.', 'error');
                return;
            }

            if (newKeyValue && newKeyBox) {
                newKeyValue.textContent = data.key;
                newKeyBox.classList.remove('hidden');
            }
            if (labelInput) labelInput.value = '';

            var list = document.querySelector('.profile-api-list');
            if (list) {
                var li = document.createElement('li');
                li.className = 'profile-api-item';
                li.setAttribute('data-key-id', data.key_id);
                li.innerHTML =
                    '<div><code>' + (data.key_prefix || '') + '</code>' +
                    (data.label ? ' <span class="api-key-label">— ' + data.label + '</span>' : '') +
                    ' <span class="api-key-meta">Created just now</span></div>' +
                    '<button type="button" class="api-key-revoke secondary-button">Revoke</button>';
                list.appendChild(li);
                attachRevokeButtons(li);
            }
        } catch (err) {
            showMessage('Network error.', 'error');
        } finally {
            btn.disabled = false;
        }
    }

    document.querySelectorAll('.session-revoke').forEach(function (btn) {
        btn.addEventListener('click', function () {
            revokeSession(btn);
        });
    });

    var revokeOthersBtn = document.getElementById('revoke-others-btn');
    if (revokeOthersBtn) {
        revokeOthersBtn.addEventListener('click', function () {
            revokeOtherSessions(revokeOthersBtn);
        });
    }

    attachRevokeButtons(document);

    var createKeyBtn = document.getElementById('create-api-key-btn');
    var keyLabelInput = document.getElementById('api-key-label');
    var newKeyBox = document.getElementById('api-key-new-box');
    var newKeyValue = document.getElementById('api-key-new-value');
    if (createKeyBtn) {
        createKeyBtn.addEventListener('click', function () {
            createApiKey(createKeyBtn, keyLabelInput, newKeyBox, newKeyValue);
        });
    }

    var copyKeyBtn = document.getElementById('api-key-copy-btn');
    if (copyKeyBtn && newKeyValue) {
        copyKeyBtn.addEventListener('click', function () {
            navigator.clipboard.writeText(newKeyValue.textContent).then(function () {
                copyKeyBtn.textContent = 'Copied!';
                setTimeout(function () {
                    copyKeyBtn.textContent = 'Copy';
                }, 2000);
            });
        });
    }

    var saveLinksBtn = document.getElementById('save-links-btn');
    var saveLinksStatus = document.getElementById('save-links-status');
    if (saveLinksBtn) {
        saveLinksBtn.addEventListener('click', async function () {
            var nexus = document.getElementById('links-nexus-url')?.value?.trim() || '';
            var github = document.getElementById('links-github-username')?.value?.trim() || '';
            var discord = document.getElementById('links-discord-handle')?.value?.trim() || '';
            saveLinksBtn.disabled = true;
            if (saveLinksStatus) saveLinksStatus.textContent = 'Saving…';
            try {
                var res = await fetch('/api/profile/links', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        nexus_profile_url: nexus,
                        github_username: github,
                        discord_handle: discord
                    })
                });
                var data = await res.json().catch(function () { return {}; });
                if (!res.ok) {
                    showMessage(data.error || 'Failed to save linked accounts.', 'error');
                    if (saveLinksStatus) saveLinksStatus.textContent = '';
                    return;
                }
                if (saveLinksStatus) saveLinksStatus.textContent = 'Saved.';
            } catch (err) {
                showMessage('Network error.', 'error');
                if (saveLinksStatus) saveLinksStatus.textContent = '';
            } finally {
                saveLinksBtn.disabled = false;
            }
        });
    }

    function formatRelativeDate(value) {
        if (!value) return '';
        var d = new Date(value.indexOf('T') === -1 ? value.replace(' ', 'T') + 'Z' : value);
        if (Number.isNaN(d.getTime())) return value;
        var diffSec = Math.max(1, Math.floor((Date.now() - d.getTime()) / 1000));
        if (diffSec < 60) return diffSec + 's ago';
        var diffMin = Math.floor(diffSec / 60);
        if (diffMin < 60) return diffMin + 'm ago';
        var diffHr = Math.floor(diffMin / 60);
        if (diffHr < 24) return diffHr + 'h ago';
        var diffDay = Math.floor(diffHr / 24);
        return diffDay + 'd ago';
    }

    function humanizeEventType(eventType) {
        var map = {
            analyze: 'Ran Analyze',
            build_list: 'Built a list',
            build_list_generate: 'Generated build list',
            dev_analyze: 'Ran Dev Analyze',
            dev_loop_suggest: 'Used Samson Loop',
            community_post_create: 'Created community post',
            community_reply_create: 'Replied in community',
            community_vote: 'Voted in community',
            feedback_submit: 'Sent feedback',
            satisfaction_submit: 'Rated analysis helpfulness'
        };
        return map[eventType] || (eventType || 'Activity').replace(/_/g, ' ');
    }

    async function loadProfileDashboard() {
        var postsEl = document.getElementById('profile-kpi-posts');
        var repliesEl = document.getElementById('profile-kpi-replies');
        var votesEl = document.getElementById('profile-kpi-votes');
        var helpfulnessEl = document.getElementById('profile-kpi-helpfulness');
        var tagsEl = document.getElementById('profile-top-tags');
        var suggestionsEl = document.getElementById('profile-suggestions');
        var activityEl = document.getElementById('profile-recent-activity');
        if (!postsEl || !repliesEl || !votesEl || !helpfulnessEl || !tagsEl || !suggestionsEl || !activityEl) return;

        try {
            var res = await fetch('/api/profile/dashboard');
            var data = await res.json().catch(function () { return {}; });
            if (!res.ok || !data.success) throw new Error(data.error || 'Could not load profile dashboard.');
            var stats = data.stats || {};
            postsEl.textContent = String(stats.posts_count || 0);
            repliesEl.textContent = String(stats.replies_count || 0);
            votesEl.textContent = String(stats.votes_cast || 0);
            helpfulnessEl.textContent = stats.avg_helpfulness != null ? String(stats.avg_helpfulness) : '—';

            var tags = data.top_tags || [];
            if (tags.length === 0) {
                tagsEl.innerHTML = '<span class="hint">No tags yet — your next post can start one.</span>';
            } else {
                tagsEl.innerHTML = tags.map(function (t) {
                    return '<span class="profile-tag-chip">' + t.tag + ' · ' + t.count + '</span>';
                }).join('');
            }

            var suggestions = data.suggestions || [];
            suggestionsEl.innerHTML = suggestions.length
                ? suggestions.map(function (s) { return '<li>' + s + '</li>'; }).join('')
                : '<li class="hint">You are fully dialed in. Keep helping others and sharing wins.</li>';

            var activity = data.recent_activity || [];
            activityEl.innerHTML = activity.length
                ? activity.slice(0, 8).map(function (a) {
                    var label = humanizeEventType(a.event_type);
                    return '<li><strong>' + label + '</strong> <span class="hint">· ' + formatRelativeDate(a.created_at) + '</span></li>';
                }).join('')
                : '<li class="hint">No recent activity yet. Run analysis or join community to get started.</li>';
        } catch (err) {
            tagsEl.innerHTML = '<span class="hint">Dashboard unavailable right now.</span>';
            suggestionsEl.innerHTML = '<li class="hint">Could not load suggestions right now.</li>';
            activityEl.innerHTML = '<li class="hint">Could not load activity right now.</li>';
        }
    }

    loadProfileDashboard();
})();
