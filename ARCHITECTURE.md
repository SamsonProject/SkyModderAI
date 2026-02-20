# SkyModderAI - System Architecture

**Date:** February 20, 2026
**Philosophy:** Local-first, smart linking, tool integration over reinvention

---

## 🎯 Core Philosophy

**What We Are:**
> A smart orchestration layer between existing tools (LOOT, AI APIs) and modders who need fast, accurate conflict detection.

**What We're Not:**
> A mod hosting platform, game database, or replacement for existing tools. We link, we don't hoard.

---

## 🏛️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Browser                          │
├─────────────────────────────────────────────────────────────┤
│  localStorage                    Session Data                │
│  ├── current_mod_list           (ephemeral, auto-save)       │
│  ├── recent_searches                                        │
│  ├── ui_preferences                                           │
│  └── saved_lists (optional)     (user choice: local/cloud)   │
└─────────────────────────────────────────────────────────────┘
                            ↕ HTTP/HTTPS
┌─────────────────────────────────────────────────────────────┐
│                    SkyModderAI Server                        │
├─────────────────────────────────────────────────────────────┤
│  Flask Application Layer                                     │
│  ├── blueprints/              (modular routes)               │
│  ├── services/                (business logic)               │
│  └── templates/               (extends base.html)            │
├─────────────────────────────────────────────────────────────┤
│  Tool Integration Layer                                      │
│  ├── LOOT Parser              (load order rules)             │
│  ├── Conflict Detector        (mod conflicts)                │
│  ├── Search Engine            (BM25 mod search)              │
│  ├── AI Integration           (summaries, when needed)       │
│  └── Knowledge Index          (curated links, not content)   │
├─────────────────────────────────────────────────────────────┤
│  Data Storage Layer                                          │
│  ├── SQLite (instance/app.db) (user accounts, shared data)  │
│  ├── JSON files (data/)       (mod databases, versioned)     │
│  └── Cache (Redis/memory)     (performance optimization)     │
└─────────────────────────────────────────────────────────────┘
                            ↕ API Calls
┌─────────────────────────────────────────────────────────────┐
│                    External Services                         │
├─────────────────────────────────────────────────────────────┤
│  LOOT GitHub              (load order masterlist)            │
│  Nexus Mods API           (mod metadata)                     │
│  AI APIs (OpenAI/etc)     (summaries, optional)              │
│  UESP                     (game information - linked)        │
│  YouTube                  (tutorials - linked)               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Flow

### **Mod Analysis Flow**
```
User Input (mod list)
    ↓
Browser localStorage (auto-save current list)
    ↓
Server receives list
    ↓
LOOT Parser (parse ESP/ESM names)
    ↓
Conflict Detector (check against rules)
    ↓
Search Engine (find missing mods)
    ↓
AI Integration (optional: generate summary)
    ↓
Results → Browser (display + localStorage backup)
    ↓
User saves (optional: server storage for cloud sync)
```

### **Data Storage Decision Tree**
```
Is this user-specific?
├── Yes → Browser localStorage (default)
│   └── Optional: Server sync (user choice, requires account)
└── No → Is this shared/community?
    ├── Yes → Server SQLite (community posts, businesses)
    └── No → Is this reference data?
        ├── Yes → JSON files (mod databases, LOOT rules)
        └── No → Don't store it (link to external source)
```

---

## 🗄️ Data Storage Strategy

### **Local-First (Browser localStorage)**

**What:**
- Current mod list (auto-save)
- Recent searches
- UI preferences (theme, collapsed sections)
- Session data (unsaved work)

**Why:**
- Fast (no server round-trip)
- Works offline
- User controls their data
- Reduces server load

**How:**
```javascript
// Auto-save current mod list
localStorage.setItem('current_mod_list', modListJSON);

// Auto-save every 30 seconds
setInterval(() => {
  localStorage.setItem('current_mod_list', modListJSON);
}, 30000);

// Load on page load
const saved = localStorage.getItem('current_mod_list');
```

**Compression:**
```javascript
// Gzip before storage (pako.js library)
const compressed = pako.gzip(JSON.stringify(data));
localStorage.setItem('data', compressed);

// Decompress on load
const compressed = localStorage.getItem('data');
const data = JSON.parse(pako.ungzip(compressed));
```

---

### **Server Storage (SQLite)**

**What:**
- User accounts (email, auth, tier)
- User sessions (device management)
- Saved lists (if user opts for cloud sync)
- Community posts (shared content)
- Business directory (shared content)
- Advertising data (shared content)

**Why:**
- Cross-device sync (when user chooses)
- Shared content (community, businesses)
- Authentication (can't be local-only)
- Revenue features (ads, donations)

**Schema:**
```sql
-- User accounts (authentication)
users (
    email TEXT PRIMARY KEY,
    tier TEXT DEFAULT 'free',
    email_verified INTEGER DEFAULT 0,
    password_hash TEXT,
    created_at TIMESTAMP
)

-- User sessions (device management)
user_sessions (
    token TEXT PRIMARY KEY,
    user_email TEXT,
    user_agent TEXT,
    created_at TIMESTAMP,
    expires_at INTEGER
)

-- Saved lists (optional cloud sync)
user_saved_lists (
    id INTEGER PRIMARY KEY,
    user_email TEXT,
    name TEXT,
    list_text TEXT,
    analysis_snapshot TEXT,
    saved_at TIMESTAMP,
    UNIQUE(user_email, name)
)

-- Community content (shared)
community_posts (
    id INTEGER PRIMARY KEY,
    user_email TEXT,
    content TEXT,
    created_at TIMESTAMP
)

-- Business directory (shared)
businesses (
    id TEXT PRIMARY KEY,
    name TEXT,
    slug TEXT UNIQUE,
    status TEXT DEFAULT 'pending'
)

-- Advertising (shared)
ad_campaigns (
    id INTEGER PRIMARY KEY,
    business_id TEXT,
    name TEXT,
    status TEXT DEFAULT 'draft'
)
```

---

### **Reference Data (JSON Files)**

**What:**
- Mod databases (skyrimse_mod_database.json)
- Game versions (game_versions.json)
- LOOT rules (loot/skyrimse/, loot/fallout4/)

**Why:**
- Static reference data (doesn't change often)
- Fast lookup (file system vs. database)
- Version control (git tracking)
- Easy updates (pull from LOOT, Nexus)

**Structure:**
```
data/
├── skyrimse_mod_database.json
├── fallout4_mod_database.json
├── game_versions.json
└── loot/
    ├── skyrimse/
    │   └── masterlist.json
    └── fallout4/
        └── masterlist.json
```

**Update Strategy:**
```bash
# Weekly cron job
python3 scripts/update_loot_data.py
python3 scripts/update_nexus_metadata.py

# Auto-update on startup (if data is old)
@app.before_request
def check_data_freshness():
    if data_is_stale():
        trigger_background_update()
```

---

## 🔧 Tool Integration

### **LOOT Parser** (Core)
**What:** Parses LOOT masterlist for load order rules
**File:** `loot_parser.py`
**Usage:**
```python
from loot_parser import LOOTParser
parser = LOOTParser('skyrimse')
rules = parser.get_rules()
```

### **Conflict Detector** (Core)
**What:** Detects mod conflicts using LOOT rules
**File:** `conflict_detector.py`
**Usage:**
```python
from conflict_detector import ConflictDetector
detector = ConflictDetector('skyrimse')
conflicts = detector.detect_conflicts(mod_list)
```

### **Search Engine** (Core)
**What:** BM25 search for mod database
**File:** `search_engine.py`
**Usage:**
```python
from search_engine import get_search_engine
results = search_engine.search('skyrimse', 'USSEP')
```

### **AI Integration** (Optional)
**What:** Generates summaries when needed
**File:** `app.py` (AI summary endpoint)
**Usage:**
```python
# Only when user requests summary
if user_requests_summary:
    summary = generate_ai_summary(context)
```

### **Knowledge Index** (Linking)
**What:** Curated links to external resources
**File:** `knowledge_index.py`
**Philosophy:** Link, don't store
**Usage:**
```python
from knowledge_index import get_resolution_for_conflict
link = get_resolution_for_conflict('USSEP conflict')
# Returns: UESP link, not full article
```

---

## 🔗 Linking Strategy

### **External Links (Reference)**

**Nexus Mods:**
- Mod downloads
- Mod descriptions
- Requirements
- **Why:** They host the files, we link

**UESP:**
- Game mechanics
- Quest information
- Item databases
- **Why:** They maintain it better, we link

**LOOT:**
- Load order rules
- Cleaning guides
- **Why:** Official source, we sync data

**GitHub:**
- Tool sources (xEdit, MO2, Wabbajack)
- Mod sources (open source mods)
- **Why:** Open source, version control

**YouTube:**
- Tutorials
- Video guides
- **Why:** Video format, they host it

### **Link Health**

**Weekly Check:**
```python
# scripts/check_link_health.py
for link in link_database:
    status = check_link(link.url)
    if status != 200:
        flag_for_review(link)
        notify_maintainer(link)
```

**Link Database:**
```sql
external_links (
    id INTEGER PRIMARY KEY,
    url TEXT UNIQUE,
    type TEXT,  -- nexus, uesp, github, youtube
    category TEXT,  -- mod, guide, tool
    last_checked TIMESTAMP,
    status INTEGER,  -- 200, 404, 500
    maintainer_email TEXT
)
```

---

## ⚡ Performance Strategy

### **Compression**

**CSS/JS:**
```bash
# Build step (Makefile)
minify:
    cssmin static/css/*.css > static/css/style.min.css
    jsmin static/js/*.js > static/js/app.min.js
    gzip -k static/css/style.min.css
    gzip -k static/js/app.min.js
```

**JSON Data:**
```python
# Before storage
import gzip
import json

compressed = gzip.compress(json.dumps(data).encode())
# Store compressed

# After retrieval
decompressed = json.loads(gzip.decompress(compressed).decode())
```

**Images:**
```bash
# Convert to WebP
convert image.png -quality 85 image.webp

# Resize for thumbnails
convert image.png -resize 300x300 image_thumb.webp
```

### **Caching**

**Redis (if available):**
```python
from cache_service import get_cache

cache = get_cache()

# Cache analysis results (5 minutes)
@cache.cached(timeout=300, key_prefix='analysis')
def analyze_mod_list(game, mod_list):
    return detector.detect_conflicts(mod_list)
```

**Memory (fallback):**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def analyze_mod_list(game, mod_list_hash):
    return detector.detect_conflicts(mod_list)
```

### **Database Indexes**

```sql
-- User queries (by email)
CREATE INDEX idx_users_email ON users(email);

-- Saved lists (by user, name)
CREATE INDEX idx_saved_lists_user ON user_saved_lists(user_email, name);

-- Community posts (by created_at)
CREATE INDEX idx_posts_created ON community_posts(created_at DESC);

-- Business directory (by status, category)
CREATE INDEX idx_business_status ON businesses(status, primary_category);

-- Ad campaigns (by business, status)
CREATE INDEX idx_campaigns_business ON ad_campaigns(business_id, status);
```

---

## 📱 Mobile Optimization

### **Data Budget**
- **Target:** <300KB per page load
- **Core tool:** <200KB (priority)
- **Business pages:** <300KB
- **Shopping pages:** <400KB (ads are heavy)

### **Lazy Loading**
```html
<!-- Images -->
<img src="placeholder.webp" data-src="actual-image.webp" loading="lazy">

<!-- Below-fold content -->
<div data-defer-load="/api/content">
  <div class="skeleton-loader"></div>
</div>
```

### **Responsive Design**
```css
/* Mobile-first */
.container {
  padding: 1rem;
}

/* Tablet+ */
@media (min-width: 768px) {
  .container {
    padding: 2rem;
  }
}

/* Desktop+ */
@media (min-width: 1024px) {
  .container {
    max-width: 1200px;
    margin: 0 auto;
  }
}
```

---

## 🔒 Security

### **Data Protection**
- User passwords: bcrypt hashing
- Sessions: secure cookies, HTTP-only
- API keys: hashed before storage
- PII: redacted from logs

### **Rate Limiting**
```python
# Per-endpoint limits
RATE_LIMIT_ANALYZE = 10 per minute
RATE_LIMIT_SEARCH = 30 per minute
RATE_LIMIT_API = 100 per minute
RATE_LIMIT_AUTH = 5 per minute
```

### **Input Validation**
```python
# All user input validated
def validate_mod_list(mod_list):
    if len(mod_list) > MAX_MOD_LIST_SIZE:
        raise ValidationError("Mod list too large")
    if not is_valid_mod_format(mod_list):
        raise ValidationError("Invalid mod list format")
```

---

## 📈 Monitoring

### **Performance Metrics**
```python
# Log slow queries
if query_time > 100ms:
    logger.warning(f"Slow query: {query_time}ms - {query}")

# Log page load times
@app.after_request
def log_load_time(response):
    load_time = get_load_time()
    logger.info(f"Page load: {load_time}ms - {request.path}")
```

### **Error Tracking**
```python
# Log all errors
@app.errorhandler(Exception)
def handle_error(error):
    logger.error(f"Error: {error} - {request.path}", exc_info=True)
    return render_template('error.html', error=str(error)), 500
```

### **User Analytics** (Anonymized)
```python
# Track feature usage (no PII)
def track_event(event_type, properties=None):
    event = {
        'type': event_type,
        'properties': properties,
        'timestamp': datetime.now().isoformat(),
        # NO user_email, NO IP address
    }
    analytics.append(event)
```

---

## 🎯 Summary

**Architecture Principles:**
1. **Local-first:** Browser storage for user session data
2. **Smart linking:** Reference external sources, don't hoard
3. **Tool integration:** Use LOOT, AI APIs, don't reinvent
4. **Compression:** Gzip JSON, minify CSS/JS, WebP images
5. **Performance:** <100ms core tool, <300KB mobile data
6. **Security:** Validate input, rate limit, hash sensitive data
7. **Monitoring:** Log slow queries, errors, anonymized analytics

**What Makes This Work:**
- Clear separation: local vs. server vs. reference data
- Smart use of existing tools (LOOT, AI APIs)
- Linking strategy (reference, don't duplicate)
- Performance budget (strict limits)
- Security first (validation, rate limiting)

**Status:** DOCUMENTED ✅
