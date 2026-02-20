# SkyModderAI - Bespoke & Dynamic Architecture Audit

**Date:** February 18, 2026
**Goal:** Hardcode less, configure more. Simple like iPhone, transparent like a watch.

---

## Executive Summary

**Current State:** SkyModderAI has excellent architecture but contains hardcoded values, fixed URLs, and configuration that should be dynamic.

**Vision:** Make every aspect configurable while maintaining simplicity. Users should see a clean interface (iPhone) but be able to look under the hood (transparent gears).

**Key Principles:**
1. **Configuration over Code** - If it might change, it belongs in config
2. **Sensible Defaults** - Work out of the box, customize when needed
3. **Transparent Operation** - Show users what's happening and why
4. **Progressive Disclosure** - Simple by default, powerful when needed

---

## 🔴 Critical: Hardcoded Values to Externalize

### 1. **URLs & External Links** ❌

**Current:** Hardcoded in `quickstart_config.py`, `mod_warnings.py`, `knowledge_index.py`

```python
# Current (hardcoded)
"url": "https://www.nexusmods.com/"
"url": "https://loot.github.io/"
"url": "https://skse.silverlock.org/"
```

**Problem:** Links break, alternatives emerge, community preferences change.

**Solution:** External links configuration file

```yaml
# config/external_links.yaml
tools:
  nexus:
    url: https://www.nexusmods.com/
    label: "Nexus Mods"
    description: "Primary mod repository"
    alternatives:
      - url: https://bethesda.net/
        label: "Bethesda.net"

loot:
  url: https://loot.github.io/
  label: "LOOT"
  description: "Load order optimization tool"

skse:
  url: https://skse.silverlock.org/
  label: "SKSE"
  description: "Script extender"
```

**Implementation:**
```python
# config_loader.py
class ExternalLinks:
    def __init__(self, config_path: str = "config/external_links.yaml"):
        self.links = self._load_config(config_path)

    def get_link(self, key: str, fallback: str = None) -> dict:
        """Get link by key, with fallback"""
        return self.links.get(key, {"url": fallback, "label": key})

    def get_all_links(self, category: str = None) -> list:
        """Get all links, optionally filtered by category"""
        if category:
            return self.links.get(category, [])
        return self.links
```

**Priority:** 🔴 High
**Effort:** 2 hours
**Impact:** Links can be updated without code changes

---

### 2. **Game-Specific Configuration** ❌

**Current:** Hardcoded in `quickstart_config.py`

```python
# Current (hardcoded per game)
"skyrimse": {
    "unofficial_patch": {"name": "USSEP", "url": "https://..."},
    "mod_manager": {"name": "MO2", "url": "https://..."},
}
```

**Problem:** Adding new games requires code changes. Community may prefer different tools.

**Solution:** Game configuration files

```yaml
# config/games/skyrimse.yaml
game:
  id: skyrimse
  name: "Skyrim Special Edition"
  versions:
    - "1.6.1170"
    - "1.6.640"
    - "1.5.97"
  default_version: "1.6.1170"

tools:
  mod_manager:
    - name: "Mod Organizer 2"
      url: "https://nexusmods.com/skyrimspecialedition/mods/6194"
      recommended: true
    - name: "Vortex"
      url: "https://nexusmods.com/site/mods/1"
      recommended: false

essentials:
  - name: "SKSE64"
    url: "https://skse.silverlock.org/"
    required: true
  - name: "USSEP"
    url: "https://nexusmods.com/skyrimspecialedition/mods/266"
    required: true

paths:
  appdata: "%LOCALAPPDATA%/Skyrim Special Edition"
  ini: "SkyrimPrefs.ini"
```

**Implementation:**
```python
# game_config.py
class GameConfig:
    def __init__(self, config_dir: str = "config/games"):
        self.config_dir = Path(config_dir)
        self._cache = {}

    def get_game(self, game_id: str) -> dict:
        """Load game configuration"""
        if game_id not in self._cache:
            config_path = self.config_dir / f"{game_id}.yaml"
            self._cache[game_id] = self._load_yaml(config_path)
        return self._cache[game_id]

    def get_essential_mods(self, game_id: str) -> list:
        """Get essential mods for game"""
        config = self.get_game(game_id)
        return config.get("essentials", [])
```

**Priority:** 🔴 High
**Effort:** 4 hours
**Impact:** Add new games without code changes

---

### 3. **Rate Limits & Thresholds** ⚠️

**Current:** In `constants.py` (better than inline, still requires redeploy)

```python
RATE_LIMIT_ANALYZE = 30  # Max analyze requests per window
PLUGIN_LIMIT = 255
PLUGIN_LIMIT_WARN_THRESHOLD = 253
```

**Problem:** Can't adjust based on server load, user tier, or special events.

**Solution:** Database-backed configuration with admin UI

```sql
-- config table
CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    type TEXT DEFAULT 'string',  -- string, int, float, bool, json
    category TEXT,               -- rate_limits, thresholds, features
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by TEXT              -- admin who changed it
);

-- Example values
INSERT INTO config VALUES
    ('rate_limit.analyze', '30', 'int', 'rate_limits', 'Max analyze requests per minute', 'admin'),
    ('plugin.limit', '255', 'int', 'thresholds', 'Bethesda engine plugin limit', 'system'),
    ('plugin.warn_threshold', '253', 'int', 'thresholds', 'Warn user before this limit', 'system');
```

**Implementation:**
```python
# config_service.py
class ConfigService:
    def __init__(self):
        self._cache = {}
        self._load_config()

    def get(self, key: str, default: any = None) -> any:
        """Get config value with type conversion"""
        value = self._cache.get(key, {}).get("value", default)
        type_ = self._cache.get(key, {}).get("type", "string")
        return self._convert(value, type_)

    def set(self, key: str, value: any, updated_by: str = "system"):
        """Update config value"""
        # Validate, save to DB, update cache, log change
        self._audit_change(key, value, updated_by)
```

**Admin UI:**
```
/admin/config
├─ Rate Limits
│  ├─ Analyze: [30] requests/minute [Save]
│  ├─ Search: [60] requests/minute [Save]
│  └─ API: [100] requests/minute [Save]
├─ Thresholds
│  ├─ Plugin Limit: [255] [Save]
│  └─ Warn Threshold: [253] [Save]
└─ Feature Flags
   ├─ OpenCLAW: [ ] Enabled [Save]
   └─ Sponsors: [x] Enabled [Save]
```

**Priority:** 🟡 Medium
**Effort:** 1 day
**Impact:** Adjust limits without redeploying

---

### 4. **AI Prompts & Templates** ❌

**Current:** Hardcoded in `app.py`, `weekly_report.py`

```python
# Current (hardcoded in code)
system = (
    "You are the SkyModderAI assistant. Your task: help the user fix their load order..."
)
```

**Problem:** Can't improve prompts without code changes. No A/B testing.

**Solution:** Prompt templates in database

```sql
CREATE TABLE prompt_templates (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    template TEXT NOT NULL,
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    metadata JSON  -- A/B test group, performance metrics
);

INSERT INTO prompt_templates VALUES
    (1, 'chat.system', 'You are the SkyModderAI assistant...', 1, true, '{"ab_group": "A"}'),
    (2, 'chat.system', 'You are an expert modding engineer...', 2, true, '{"ab_group": "B"}');
```

**Implementation:**
```python
# prompt_service.py
class PromptService:
    def get_template(self, name: str, context: dict = None) -> str:
        """Get active template, render with context"""
        template = self._db.get_active_template(name)
        return self._render(template, context)

    def ab_test(self, template_name: str, user_id: str) -> str:
        """Return template variant based on A/B test"""
        variant = self._get_user_variant(user_id)
        return self._db.get_template(template_name, variant)
```

**Priority:** 🟡 Medium
**Effort:** 4 hours
**Impact:** Improve AI responses without redeploying

---

### 5. **Email Templates** ⚠️

**Current:** Partially templated in `weekly_report.py`

```python
html = f"""
<html>
<body>
    <h1>SkyModderAI Weekly Report</h1>
    ...
</body>
</html>
"""
```

**Problem:** Can't customize branding, add analytics, or translate.

**Solution:** Email template files with variables

```html
<!-- templates/emails/weekly_report.html -->
<!DOCTYPE html>
<html>
<head>
    <style>{{ css_styles }}</style>
</head>
<body>
    <header>
        <img src="{{ logo_url }}" alt="SkyModderAI">
    </header>

    <h1>Weekly Report - {{ period }}</h1>

    <section class="metrics">
        <h2>What Worked Well</h2>
        <ul>
            {% for item in worked_well %}
            <li>{{ item }}</li>
            {% endfor %}
        </ul>
    </section>

    <footer>
        <p>{{ footer_text }}</p>
        <a href="{{ unsubscribe_url }}">Unsubscribe</a>
    </footer>
</body>
</html>
```

**Implementation:**
```python
# email_service.py
class EmailService:
    def send_weekly_report(self, recipient: str, data: dict):
        template = self._load_template("weekly_report.html")
        html = self._render(template, data)
        self._send(recipient, "Weekly Report", html)
```

**Priority:** 🟢 Low
**Effort:** 2 hours
**Impact:** Better branding, easier translations

---

## 🟡 Important: Result Consolidation & Readability

### 6. **Conflict Display** ⚠️

**Current:** Shows all conflicts individually (can be overwhelming)

**Problem:** Users see 50+ individual conflicts, hard to see patterns.

**Solution:** Hierarchical display with smart grouping

```
Current (overwhelming):
├─ Mod A conflicts with Mod B
├─ Mod A conflicts with Mod C
├─ Mod A conflicts with Mod D
├─ Mod E conflicts with Mod F
├─ Mod E conflicts with Mod G
... (45 more)

Improved (grouped):
├─ 🔴 Critical Issues (3)
│  ├─ Mod A has 3 compatibility issues [Expand]
│  └─ Mod E has 2 compatibility issues [Expand]
├─ ⚠️ Load Order (5)
│  └─ 5 mods need reordering [Expand]
└─ ℹ️ Suggestions (12)
   └─ 12 optional improvements [Expand]
```

**Implementation:**
```python
# result_consolidator.py
class ResultConsolidator:
    def consolidate_conflicts(self, conflicts: list) -> dict:
        """Group conflicts by affected mod and severity"""
        grouped = defaultdict(list)

        for conflict in conflicts:
            key = self._get_group_key(conflict)
            grouped[key].append(conflict)

        return {
            "critical": [g for g in grouped if g.severity == "critical"],
            "warnings": [g for g in grouped if g.severity == "warning"],
            "suggestions": [g for g in grouped if g.severity == "info"],
            "total_groups": len(grouped),
            "total_conflicts": sum(len(g) for g in grouped.values())
        }

    def _get_group_key(self, conflict: dict) -> str:
        """Group by primary affected mod"""
        return conflict["affected_mod"]
```

**Priority:** 🟡 High
**Effort:** 4 hours
**Impact:** Much more readable results

---

### 7. **Transparency Panel** ❌

**Current:** Users see results but not _why_ or _how_.

**Problem:** Black box feeling. Users don't trust what they can't understand.

**Solution:** "Show Your Work" panel (collapsible)

```
┌─────────────────────────────────────────────────────────┐
│  Analysis Results                                       │
├─────────────────────────────────────────────────────────┤
│  ✅ 3 Critical Issues Found                             │
│  ⚠️ 5 Warnings                                          │
│  ℹ️ 12 Suggestions                                       │
│                                                         │
│  [🔍 Show Analysis Details ▼]                          │
└─────────────────────────────────────────────────────────┘

[Expanded]
┌─────────────────────────────────────────────────────────┐
│  How This Was Analyzed                                  │
├─────────────────────────────────────────────────────────┤
│  📊 Data Sources:                                       │
│  ├─ LOOT Masterlist (3514 mods)                         │
│  ├─ Community Reports (127 verified conflicts)          │
│  └─ Research Pipeline (updated 2 hours ago)             │
│                                                         │
│  ⚙️ Filters Applied:                                    │
│  ├─ Game Version: Skyrim AE 1.6.1170                    │
│  ├─ Credibility Threshold: ≥0.75                        │
│  └─ Excluded: 3 low-credibility sources                 │
│                                                         │
│  🤖 AI Involvement:                                     │
│  ├─ Conflict Detection: Deterministic (no AI)           │
│  ├─ Resolution Suggestions: AI-assisted                 │
│  └─ Confidence: 94%                                     │
│                                                         │
│  ⏱️ Performance:                                        │
│  ├─ Analysis Time: 87ms                                 │
│  ├─ Cache Hits: 12/15 mods                              │
│  └─ AI Tokens Used: 0 (deterministic)                   │
└─────────────────────────────────────────────────────────┘
```

**Implementation:**
```python
# transparency_service.py
class TransparencyService:
    def get_analysis_metadata(self, analysis_result: dict) -> dict:
        """Return metadata about how analysis was performed"""
        return {
            "data_sources": self._get_data_sources(),
            "filters_applied": self._get_filters(),
            "ai_involvement": self._get_ai_usage(),
            "performance": self._get_performance_metrics(),
            "confidence": self._calculate_confidence(analysis_result)
        }
```

**Priority:** 🟡 High
**Effort:** 1 day
**Impact:** Builds trust, educates users

---

### 8. **Unified Result Format** ❌

**Current:** Different endpoints return different formats.

**Problem:** Inconsistent UX, hard to build unified UI components.

**Solution:** Standardized result envelope

```python
# result_types.py
@dataclass
class AnalysisResult:
    """Standard result envelope for all analyses"""

    # Metadata
    id: str
    type: str  # "conflict_analysis", "load_order", "recommendations"
    game: str
    version: str
    created_at: datetime

    # Results
    summary: dict  # High-level counts
    details: list  # Detailed findings
    consolidated: dict  # Grouped for readability

    # Transparency
    metadata: dict  # How it was analyzed
    confidence: float  # 0.0-1.0

    # Actions
    actions: list  # Suggested next steps
    export_formats: list  # Available export formats

    def to_dict(self) -> dict:
        """Convert to API response"""
        return {
            "id": self.id,
            "type": self.type,
            "summary": self.summary,
            "details": self.details,
            "consolidated": self.consolidated,
            "metadata": self.metadata,
            "confidence": self.confidence,
            "actions": self.actions,
            "export_formats": self.export_formats
        }
```

**Priority:** 🟡 Medium
**Effort:** 1 day
**Impact:** Consistent UX, easier to maintain

---

## 🟢 Nice to Have: Progressive Disclosure

### 9. **User Preference Profiles** ❌

**Current:** One-size-fits-all results.

**Solution:** User can set preference level

```
Settings → Analysis Detail Level
├─ 🟢 Simple (Beginner)
│  └─ Show only critical issues, plain language
├─ 🟡 Standard (Most Users)
│  └─ Show all issues, technical terms explained
└─ 🔵 Advanced (Power Users)
   └─ Show everything, raw data available
```

**Implementation:**
```python
# user_preferences.py
class UserPreferences:
    def get_analysis_detail_level(self, user_id: str) -> str:
        """Get user's preferred detail level"""
        return self._db.get_preference(user_id, "detail_level", "standard")

    def filter_results(self, results: list, level: str) -> list:
        """Filter results based on detail level"""
        if level == "simple":
            return [r for r in results if r.severity == "critical"]
        elif level == "standard":
            return [r for r in results if r.severity != "debug"]
        return results  # advanced: show everything
```

**Priority:** 🟢 Low
**Effort:** 4 hours
**Impact:** Better UX for different user types

---

### 10. **Customizable Dashboards** ❌

**Current:** Fixed layout.

**Solution:** Drag-and-drop dashboard widgets

```
[Dashboard Settings ⚙️]

[Drag widgets to customize your view]
┌─────────────┬─────────────┐
│ Recent      │ Quick Stats │
│ Analyses    │             │
├─────────────┴─────────────┤
│ Conflict Overview         │
├───────────────────────────┤
│ Community Builds          │
└───────────────────────────┘

[Save Layout] [Reset to Default]
```

**Priority:** 🟢 Low
**Effort:** 2 days
**Impact:** Power users love customization

---

## Implementation Priority

### **Phase 1: Critical (Week 1)**
1. ✅ External links configuration
2. ✅ Game configuration files
3. ✅ Result consolidation (hierarchical display)
4. ✅ Transparency panel

### **Phase 2: Important (Week 2-3)**
5. ✅ Database-backed config with admin UI
6. ✅ Prompt templates in database
7. ✅ Unified result format
8. ✅ Email templates

### **Phase 3: Nice to Have (Month 2)**
9. User preference profiles
10. Customizable dashboards
11. A/B testing framework
12. Translation system

---

## Configuration File Structure

```
config/
├── external_links.yaml      # All external URLs
├── games/
│   ├── skyrimse.yaml
│   ├── skyrim.yaml
│   ├── fallout4.yaml
│   └── ...
├── email_templates/
│   ├── weekly_report.html
│   ├── verification.html
│   └── ...
└── prompts/
    ├── chat_system.txt
    ├── analysis_summary.txt
    └── ...
```

---

## Benefits

### **For Users:**
- ✅ More readable, consolidated results
- ✅ Transparency into how analysis works
- ✅ Customizable detail level
- ✅ Trust through visibility

### **For Developers:**
- ✅ Add games without code changes
- ✅ Update links without redeploying
- ✅ A/B test prompts
- ✅ Adjust limits dynamically

### **For Business:**
- ✅ Faster iteration
- ✅ Lower deployment risk
- ✅ Better user trust
- ✅ Easier localization

---

## Next Steps

1. **Create config directory structure**
2. **Migrate hardcoded URLs to `external_links.yaml`**
3. **Create game configuration files**
4. **Implement result consolidator**
5. **Build transparency panel UI**
6. **Add database config table + admin UI**

**Total Effort:** ~1 week for Phase 1
**Impact:** Massive improvement in flexibility and UX

---

**Questions? Want me to start implementing Phase 1?**
