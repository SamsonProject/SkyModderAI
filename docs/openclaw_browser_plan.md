# OpenCLAW Browser Integration Plan

**Date:** February 20, 2026  
**Status:** 🚀 **READY TO IMPLEMENT**

---

## 🎯 Vision

> **"Run OpenCLAW entirely through the browser — no desktop app needed. Users grant permissions, OpenCLAW analyzes their mod list, proposes fixes, and guides them through implementation — all safely sandboxed."**

---

## 🏗️ Current State

### ✅ What's Already Built

**Backend (`/dev/openclaw/`):**
- `sandbox.py` — Secure file operations (20KB)
- `guard.py` — Safety validation (14KB)
- `automator.py` — Plan execution engine (11KB)
- `learner.py` — ML learning from sessions (21KB)
- `telemetry.py` — Privacy-first telemetry (15KB)
- `train_models.py` — Model training pipeline (17KB)

**API (`blueprints/openclaw.py`):**
- `/api/v1/openclaw/` — Dashboard
- `/api/v1/openclaw/plan/propose` — Propose improvement plan
- `/api/v1/openclaw/plan/execute` — Execute approved plan
- `/api/v1/openclaw/permissions` — Manage permissions
- `/api/v1/openclaw/sandbox/info` — Sandbox usage info
- `/api/v1/openclaw/loop/feedback` — Submit post-run feedback
- `/api/v1/openclaw/safety-status` — Safety hardening score

**Engine (`openclaw_engine.py`):**
- Permission scopes (8 types)
- Plan building (5-phase workflow)
- Safety validation
- Feedback loop suggestions

**Database (`models.py`):**
- `openclaw_grants` — User workspace grants
- `openclaw_permissions` — User-granted scopes
- `openclaw_plan_runs` — Execution history
- `openclaw_feedback` — Post-run feedback
- `openclaw_events` — Audit log

### ❌ What's Missing

1. **Frontend UI** — `templates/openclaw.html` doesn't exist
2. **File Upload** — Users can't upload mod lists/logs yet
3. **Real-time Progress** — No WebSocket for live execution updates
4. **Sandbox Visualization** — Can't see what OpenCLAW is doing
5. **One-Click Apply** — Manual steps to apply changes in mod manager

---

## 📋 Implementation Plan

### **Phase 1: Frontend UI (1-2 days)** ⭐ **START HERE**

Create `templates/openclaw.html` — the main dashboard.

**Features:**
- Permission grant interface (checkboxes for each scope)
- Plan proposal form (objective, playstyle selection)
- Plan visualization (show what will change)
- Execution progress bar
- Feedback submission form (FPS, crashes, enjoyment)
- Sandbox file viewer (see what OpenCLAW created)

**File:** `templates/openclaw.html`

```html
{% extends "base.html" %}

{% block title %}OpenCLAW — Automated Modding Assistant{% endblock %}

{% block content %}
<div class="openclaw-dashboard">
    <!-- Permission Grant Section -->
    <section class="permissions">
        <h2>Grant OpenCLAW Permissions</h2>
        <p class="hint">OpenCLAW needs your permission to help. Each scope is granular and revocable.</p>
        
        <div class="permission-grid">
            {% for scope in permissions %}
            <label class="permission-card {{ 'granted' if scope.granted else '' }}">
                <input type="checkbox" 
                       name="permissions" 
                       value="{{ scope.scope }}"
                       {{ 'checked' if scope.granted else '' }}
                       data-scope="{{ scope.scope }}">
                <div class="permission-icon">
                    {% if scope.scope == 'read_game_logs' %}📋
                    {% elif scope.scope == 'write_sandbox_files' %}📝
                    {% elif scope.scope == 'launch_game' %}🎮
                    {% endif %}
                </div>
                <div class="permission-name">{{ scope.scope | replace('_', ' ') | title }}</div>
                <div class="permission-desc">{{ permission_descriptions[scope.scope] }}</div>
            </label>
            {% endfor %}
        </div>
    </section>

    <!-- Plan Proposal Section -->
    <section class="plan-proposal">
        <h2>What Should OpenCLAW Help With?</h2>
        
        <form id="openclaw-plan-form">
            <div class="form-group">
                <label for="objective">Your Goal</label>
                <select id="objective" name="objective" required>
                    <option value="improve_stability">Fix crashes and stutters</option>
                    <option value="improve_performance">Better FPS</option>
                    <option value="resolve_conflicts">Resolve mod conflicts</option>
                    <option value="optimize_load_order">Optimize load order</option>
                    <option value="suggest_mods">Suggest compatible mods</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="playstyle">Playstyle</label>
                <select id="playstyle" name="playstyle">
                    <option value="balanced">Balanced (visuals + performance)</option>
                    <option value="performance">Performance-focused</option>
                    <option value="visuals">Visual quality-focused</option>
                    <option value="stability">Maximum stability</option>
                </select>
            </div>
            
            <button type="submit" class="btn btn-primary">
                🐾 Propose Plan
            </button>
        </form>
    </section>

    <!-- Plan Visualization -->
    <section class="plan-view" style="display: none;">
        <h2>Proposed Plan</h2>
        <div id="plan-actions"></div>
        <div class="plan-actions">
            <button class="btn btn-success" onclick="executePlan()">
                ✓ Execute Plan
            </button>
            <button class="btn btn-secondary" onclick="revisePlan()">
                ✎ Revise
            </button>
        </div>
    </section>

    <!-- Execution Progress -->
    <section class="execution-progress" style="display: none;">
        <h2>OpenCLAW at Work</h2>
        <div class="progress-bar">
            <div class="progress-fill" style="width: 0%"></div>
        </div>
        <div id="execution-log"></div>
    </section>

    <!-- Feedback Form -->
    <section class="feedback-form" style="display: none;">
        <h2>How Did It Go?</h2>
        <form id="openclaw-feedback-form">
            <div class="form-row">
                <div class="form-group">
                    <label for="fps_avg">Average FPS</label>
                    <input type="number" id="fps_avg" name="fps_avg" placeholder="e.g., 45">
                </div>
                <div class="form-group">
                    <label for="crashes">Crashes</label>
                    <input type="number" id="crashes" name="crashes" value="0">
                </div>
                <div class="form-group">
                    <label for="stutter_events">Stutter Events</label>
                    <input type="number" id="stutter_events" name="stutter_events" value="0">
                </div>
            </div>
            
            <div class="form-group">
                <label for="enjoyment_score">Enjoyment (1-10)</label>
                <input type="range" id="enjoyment_score" name="enjoyment_score" 
                       min="1" max="10" value="5">
                <div class="range-labels">
                    <span>😞</span>
                    <span>😐</span>
                    <span>😄</span>
                </div>
            </div>
            
            <button type="submit" class="btn btn-primary">
                Submit Feedback
            </button>
        </form>
    </section>
</div>

<script src="/static/js/openclaw.js"></script>
{% endblock %}
```

---

### **Phase 2: JavaScript Client (1 day)**

Create `static/js/openclaw.js` — handles API calls and UI updates.

**Features:**
- Permission management (grant/revoke)
- Plan proposal/execution
- Real-time progress updates
- Feedback submission
- Error handling

**File:** `static/js/openclaw.js`

```javascript
/**
 * OpenCLAW Browser Client
 */

class OpenClawClient {
    constructor() {
        this.baseUrl = '/api/v1/openclaw';
        this.currentPlan = null;
    }

    // Permission Management
    async grantPermission(scope, granted) {
        const res = await fetch(`${this.baseUrl}/permissions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ scope, granted })
        });
        
        if (!res.ok) throw new Error('Permission update failed');
        return await res.json();
    }

    async getPermissions() {
        const res = await fetch(`${this.baseUrl}/permissions`);
        if (!res.ok) throw new Error('Failed to get permissions');
        return await res.json();
    }

    // Plan Management
    async proposePlan(objective, playstyle, game = 'skyrimse') {
        const res = await fetch(`${this.baseUrl}/plan/propose`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ game, objective, playstyle })
        });
        
        if (!res.ok) {
            const error = await res.json();
            throw new Error(error.message || 'Plan proposal failed');
        }
        
        const data = await res.json();
        this.currentPlan = data.plan;
        return data;
    }

    async executePlan(planId) {
        const res = await fetch(`${this.baseUrl}/plan/execute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ plan_id: planId })
        });
        
        if (!res.ok) {
            const error = await res.json();
            throw new Error(error.message || 'Plan execution failed');
        }
        
        return await res.json();
    }

    // Feedback
    async submitFeedback(feedback) {
        const res = await fetch(`${this.baseUrl}/loop/feedback`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(feedback)
        });
        
        if (!res.ok) throw new Error('Feedback submission failed');
        return await res.json();
    }

    // Sandbox Info
    async getSandboxInfo() {
        const res = await fetch(`${this.baseUrl}/sandbox/info`);
        if (!res.ok) throw new Error('Failed to get sandbox info');
        return await res.json();
    }
}

// UI Event Handlers
const client = new OpenClawClient();

// Permission toggles
document.querySelectorAll('input[name="permissions"]').forEach(checkbox => {
    checkbox.addEventListener('change', async (e) => {
        const scope = e.target.dataset.scope;
        const granted = e.target.checked;
        
        try {
            await client.grantPermission(scope, granted);
            e.target.closest('.permission-card').classList.toggle('granted', granted);
        } catch (error) {
            alert(`Failed to update permission: ${error.message}`);
            e.target.checked = !granted; // Revert
        }
    });
});

// Plan proposal form
document.getElementById('openclaw-plan-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const objective = document.getElementById('objective').value;
    const playstyle = document.getElementById('playstyle').value;
    
    try {
        const result = await client.proposePlan(objective, playstyle);
        displayPlan(result.plan);
    } catch (error) {
        alert(`Plan proposal failed: ${error.message}`);
    }
});

function displayPlan(plan) {
    const planView = document.querySelector('.plan-view');
    const planActions = document.getElementById('plan-actions');
    
    planActions.innerHTML = plan.actions.map(action => `
        <div class="plan-action">
            <div class="action-phase">${action.phase}</div>
            <div class="action-kind">${action.kind}</div>
            <div class="action-desc">${action.description}</div>
            ${action.requires_permissions.length ? `
                <div class="action-permissions">
                    Requires: ${action.requires_permissions.join(', ')}
                </div>
            ` : ''}
        </div>
    `).join('');
    
    planView.style.display = 'block';
}

async function executePlan() {
    if (!client.currentPlan) return;
    
    const progressSection = document.querySelector('.execution-progress');
    const progressBar = document.querySelector('.progress-fill');
    const logDiv = document.getElementById('execution-log');
    
    progressSection.style.display = 'block';
    
    try {
        // Execute plan (this would be WebSocket in production for real-time updates)
        const result = await client.executePlan(client.currentPlan.plan_id);
        
        // Update progress
        progressBar.style.width = '100%';
        logDiv.innerHTML = `
            <div class="log-entry success">
                ✓ Plan executed successfully
            </div>
            <div class="log-entry">
                Files created: ${result.result.files_created || 0}
            </div>
        `;
        
        // Show feedback form
        document.querySelector('.feedback-form').style.display = 'block';
        
    } catch (error) {
        progressBar.style.width = '0%';
        logDiv.innerHTML = `
            <div class="log-entry error">
                ✗ Execution failed: ${error.message}
            </div>
        `;
    }
}

// Feedback form
document.getElementById('openclaw-feedback-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const feedback = {
        fps_avg: document.getElementById('fps_avg').value,
        crashes: document.getElementById('crashes').value,
        stutter_events: document.getElementById('stutter_events').value,
        enjoyment_score: document.getElementById('enjoyment_score').value
    };
    
    try {
        const result = await client.submitFeedback(feedback);
        alert('Feedback submitted! OpenCLAW will learn from this session.');
        
        // Show suggestions
        if (result.suggestions) {
            displaySuggestions(result.suggestions);
        }
    } catch (error) {
        alert(`Feedback failed: ${error.message}`);
    }
});

function displaySuggestions(suggestions) {
    const suggestionsHtml = suggestions.map(s => `
        <div class="suggestion-card">💡 ${s}</div>
    `).join('');
    
    alert('OpenCLAW Suggestions:\n\n' + suggestions.join('\n'));
}
```

---

### **Phase 3: File Upload Support (1 day)**

Add endpoint for users to upload mod lists, logs, configs.

**Backend:** Add to `blueprints/openclaw.py`

```python
@openclaw_bp.route("/upload", methods=["POST"])
def upload_files() -> Any:
    """
    Upload mod list, logs, or configs for analysis.
    
    Supports:
    - modlist.txt (text format)
    - plugins.txt (MO2/Vortex format)
    - SKSE logs
    - ENB logs
    """
    if "user_email" not in session:
        raise AuthenticationError()
    
    if "file" not in request.files:
        raise ValidationError("No file uploaded")
    
    file = request.files["file"]
    if file.filename == "":
        raise ValidationError("No file selected")
    
    # Validate file type
    allowed_extensions = {".txt", ".log", ".json", ".ini"}
    ext = "." + file.filename.rsplit(".", 1)[-1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(f"File type {ext} not allowed")
    
    # Save to user's sandbox
    from dev.openclaw.sandbox import OpenClawSandbox
    
    sandbox = OpenClawSandbox(
        workspace_root="./openclaw_workspace",
        user_email=session["user_email"]
    )
    
    # Save file
    rel_path = f"uploads/{file.filename}"
    sandbox.write_file(rel_path, file.read())
    
    logger.info(f"File uploaded: {file.filename} by {session['user_email']}")
    
    return jsonify({
        "success": True,
        "file_path": rel_path,
        "message": "File uploaded successfully"
    })
```

**Frontend:** Add upload zone to `openclaw.html`

```html
<div class="file-upload-zone" id="upload-zone">
    <p>📁 Drop your mod list here, or click to browse</p>
    <p class="hint">Supports: modlist.txt, plugins.txt, SKSE logs</p>
    <input type="file" id="file-input" accept=".txt,.log,.json,.ini" multiple>
</div>

<script>
const uploadZone = document.getElementById('upload-zone');
const fileInput = document.getElementById('file-input');

uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('dragover');
});

uploadZone.addEventListener('dragleave', () => {
    uploadZone.classList.remove('dragover');
});

uploadZone.addEventListener('drop', async (e) => {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    for (const file of files) {
        await uploadFile(file);
    }
});

uploadZone.addEventListener('click', () => {
    fileInput.click();
});

fileInput.addEventListener('change', async (e) => {
    for (const file of e.target.files) {
        await uploadFile(file);
    }
});

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const res = await fetch('/api/v1/openclaw/upload', {
        method: 'POST',
        body: formData
    });
    
    if (!res.ok) throw new Error('Upload failed');
    
    const result = await res.json();
    console.log('Uploaded:', result.file_path);
}
</script>
```

---

### **Phase 4: WebSocket for Real-Time Progress (2 days)**

Add WebSocket support for live execution updates.

**Backend:** Add to `app.py`

```python
from flask_socketio import SocketIO, emit

socketio = SocketIO(app, cors_allowed_origins=[BASE_URL])

@socketio.on('connect')
def handle_connect():
    if 'user_email' not in session:
        return False
    logger.info(f"WebSocket connected: {session['user_email']}")

@socketio.on('execute_plan')
def handle_execute_plan(data):
    plan_id = data.get('plan_id')
    
    # Execute plan in background thread
    from dev.openclaw.automator import OpenClawAutomator
    
    automator = OpenClawAutomator(
        db=get_db(),
        workspace_root="./openclaw_workspace",
        user_email=session['user_email']
    )
    
    def progress_callback(phase, action, message):
        emit('progress', {
            'phase': phase,
            'action': action,
            'message': message,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    
    result = automator.execute_plan(
        plan_id=plan_id,
        progress_callback=progress_callback
    )
    
    emit('complete', {
        'success': True,
        'result': result.to_dict()
    })
```

**Frontend:** Update `openclaw.js`

```javascript
import { io } from 'https://cdn.socket.io/4.5.4/socket.io.min.js';

const socket = io();

socket.on('connect', () => {
    console.log('WebSocket connected');
});

socket.on('progress', (data) => {
    const logDiv = document.getElementById('execution-log');
    logDiv.innerHTML += `
        <div class="log-entry">
            [${data.phase}] ${data.message}
        </div>
    `;
    logDiv.scrollTop = logDiv.scrollHeight;
});

socket.on('complete', (data) => {
    console.log('Execution complete:', data);
});

async function executePlan() {
    socket.emit('execute_plan', { plan_id: client.currentPlan.plan_id });
}
```

---

### **Phase 5: One-Click Apply Guide (1 day)**

Create step-by-step guide for applying changes in mod manager.

**File:** `templates/includes/openclaw_guide.html`

```html
<div class="openclaw-guide">
    <h3>📋 Apply These Changes</h3>
    
    <div class="guide-step">
        <div class="step-number">1</div>
        <div class="step-content">
            <h4>Download Recommended Mods</h4>
            <ul>
                {% for mod in plan.recommended_mods %}
                <li>
                    <a href="{{ mod.nexus_url }}" target="_blank">{{ mod.name }}</a>
                    {% if mod.is_patch %}
                        <span class="badge">Patch</span>
                    {% endif %}
                </li>
                {% endfor %}
            </ul>
        </div>
    </div>
    
    <div class="guide-step">
        <div class="step-number">2</div>
        <div class="step-content">
            <h4>Adjust Load Order</h4>
            <p>Move these mods in your mod manager:</p>
            <ol class="load-order-list">
                {% for mod in plan.load_order_changes %}
                <li>
                    <span class="mod-name">{{ mod.name }}</span>
                    <span class="mod-position">Position: {{ mod.position }}</span>
                </li>
                {% endfor %}
            </ol>
        </div>
    </div>
    
    <div class="guide-step">
        <div class="step-number">3</div>
        <div class="step-content">
            <h4>Apply Configuration Changes</h4>
            <p>Download and apply these config files:</p>
            <div class="config-files">
                {% for config in plan.config_files %}
                <a href="/api/v1/openclaw/download/{{ config.path }}" 
                   class="config-download" download>
                    📥 {{ config.name }}
                </a>
                {% endfor %}
            </div>
        </div>
    </div>
</div>
```

---

## 🚀 Deployment Checklist

- [ ] Create `templates/openclaw.html`
- [ ] Create `static/js/openclaw.js`
- [ ] Add file upload endpoint
- [ ] Add WebSocket support (optional, for real-time)
- [ ] Add navigation link to OpenCLAW dashboard
- [ ] Test with real mod lists
- [ ] Add rate limiting to upload endpoint
- [ ] Add error boundaries in frontend
- [ ] Test on mobile
- [ ] Add loading states
- [ ] Add success/error toasts

---

## 🎨 UI/UX Notes

**Design Principles:**
- **Transparency:** Show exactly what OpenCLAW is doing
- **Control:** User confirms every change
- **Safety:** Clear visual indicators of what's safe/dangerous
- **Progress:** Real-time feedback on execution

**Color Scheme:**
- Primary: `#3b82f6` (blue) — OpenCLAW branding
- Success: `#22c55e` (green) — Safe operations
- Warning: `#f59e0b` (amber) — Requires confirmation
- Error: `#ef4444` (red) — Blocked/dangerous

---

## 📊 Success Metrics

- **Activation:** % of users who grant at least 1 permission
- **Engagement:** % who propose and execute a plan
- **Retention:** % who submit feedback after execution
- **Safety:** 0 security incidents, 0 data leaks

---

## 🔐 Security Notes

1. **Sandbox Isolation:** Each user gets isolated workspace
2. **Path Validation:** No traversal outside sandbox
3. **File Size Limits:** Max 50MB per file
4. **Extension Whitelist:** Only safe file types
5. **Rate Limiting:** 5 plans/minute, 3 executions/5 minutes
6. **Audit Logging:** All operations logged to `openclaw_events`

---

**Ready to implement?** Start with Phase 1 (frontend UI) — it's the quickest win and makes OpenCLAW visible to users!
