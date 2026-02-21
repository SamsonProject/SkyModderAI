# Services Layer

**Business logic and domain services for SkyModderAI.**

---

## 📁 Service Structure

**Core Services (in `services/` directory):**
```
services/
├── __init__.py
├── analysis_service.py       # Mod analysis and conflict detection
├── auth_service.py           # Authentication and authorization
├── community_service.py      # Community features and builds
└── search_service.py         # Search functionality
```

**Additional Services (root level):**
```
Root Level Services:
├── ad_builder_service.py     # Ad Builder (templates, designs, brand kits)
├── business_service.py       # Business directory and trust scores
├── cache_service.py          # Redis caching layer
├── compatibility_service.py  # Compatibility database
├── curation_service.py       # Session curation
├── feedback_service.py       # Feedback and bug reports
├── presentation_service.py   # PDF/export functionality
├── shopping_service.py       # Shopping/ads (legacy, being replaced)
├── sponsor_service.py        # Sponsor management (legacy)
├── transparency_service.py   # Transparency reports
├── samson_telemetry.py       # SAMSON telemetry collection
└── walkthrough_manager.py    # Walkthrough management
```

**Note:** Services are distributed between `services/` directory and root level. New services should be placed in `services/` for organization.

---

## 🔧 Service Descriptions

### **analysis_service.py**

**Purpose:** Mod analysis, conflict detection, and recommendations.

**Key Functions:**
- `analyze_mod_list()` — Analyze mod list for conflicts
- `detect_conflicts()` — Find incompatible mods
- `suggest_fixes()` — Recommend patches and alternatives
- `calculate_compatibility()` — Compute mod compatibility scores

**Dependencies:**
- `conflict_detector.py` — Core conflict detection logic
- `loot_parser.py` — LOOT masterlist parsing
- `knowledge_index.py` — Community knowledge base

**Example Usage:**
```python
from services.analysis_service import analyze_mod_list

result = analyze_mod_list(
    mod_list=["USSEP.esp", "SkyUI.esp"],
    game="skyrimse"
)
print(result.conflicts)  # List of detected conflicts
```

---

### **auth_service.py**

**Purpose:** User authentication, authorization, and session management.

**Key Functions:**
- `authenticate_user()` — Validate user credentials
- `create_session()` — Create user session
- `validate_session()` — Check session validity
- `grant_permission()` — Grant OpenCLAW permissions
- `revoke_permission()` — Revoke OpenCLAW permissions

**Dependencies:**
- `models.py` — User and session models
- `security_utils.py` — Password hashing, token generation

**Example Usage:**
```python
from services.auth_service import authenticate_user

user = authenticate_user(email="user@example.com", password="secret")
if user:
    session = create_session(user.email)
```

---

### **community_service.py**

**Purpose:** Community features, builds, and collaboration.

**Key Functions:**
- `get_community_builds()` — Fetch community load orders
- `submit_build()` — Share user's mod list
- `vote_build()` — Upvote/downvote community builds
- `get_build_comments()` — Fetch build discussion

**Dependencies:**
- `community_builds.py` — Community builds module
- `models.py` — Community post and reply models

**Example Usage:**
```python
from services.community_service import get_community_builds

builds = get_community_builds(game="skyrimse", limit=10)
for build in builds:
    print(f"{build.title} by {build.author}")
```

---

### **search_service.py**

**Purpose:** Search functionality for mods, conflicts, and knowledge.

**Key Functions:**
- `search_mods()` — Search mod database
- `search_conflicts()` — Search conflict database
- `search_knowledge()` — Search knowledge index
- `autocomplete()` — Search autocomplete suggestions

**Dependencies:**
- `search_engine.py` — Core search engine
- `knowledge_index.py` — Knowledge base

**Example Usage:**
```python
from services.search_service import search_mods

results = search_mods(query="skyui", game="skyrimse")
for result in results:
    print(f"{result.name} - {result.description}")
```

---

## 🎯 Service Design Principles

### **1. Single Responsibility**

Each service handles one domain:
- `analysis_service` → Mod analysis only
- `auth_service` → Authentication only
- `community_service` → Community features only

### **2. Stateless Design**

Services are stateless — no instance variables that persist between calls.

```python
# ✅ Good: Stateless
def analyze_mod_list(mod_list, game):
    return ConflictDetector().detect(mod_list)

# ❌ Bad: Stateful
class AnalysisService:
    def __init__(self):
        self.cache = {}  # Don't do this
```

### **3. Dependency Injection**

Pass dependencies as parameters, don't import globally.

```python
# ✅ Good: Dependency injection
def analyze_mod_list(mod_list, detector=None):
    detector = detector or ConflictDetector()
    return detector.detect(mod_list)

# ❌ Bad: Hard-coded dependency
def analyze_mod_list(mod_list):
    detector = ConflictDetector()  # Hard to test
```

### **4. Error Handling**

Raise specific exceptions, catch broad ones.

```python
# ✅ Good: Specific exceptions
def authenticate_user(email, password):
    if not email:
        raise ValidationError("Email is required")
    if not user_exists(email):
        raise AuthenticationError("User not found")

# ❌ Bad: Catch-all
def authenticate_user(email, password):
    try:
        # ... everything ...
    except Exception:
        return None
```

---

## 🧪 Testing Services

### **Unit Tests**

```python
# tests/unit/test_analysis_service.py
import pytest
from services.analysis_service import analyze_mod_list
from conflict_detector import ConflictDetector


class TestAnalysisService:
    def test_analyze_mod_list(self):
        mod_list = ["USSEP.esp", "SkyUI.esp"]
        result = analyze_mod_list(mod_list, game="skyrimse")
        assert result is not None
    
    def test_analyze_with_mock_detector(self, mocker):
        mock_detector = mocker.Mock()
        mock_detector.detect.return_value = []
        
        result = analyze_mod_list(
            ["USSEP.esp"],
            game="skyrimse",
            detector=mock_detector
        )
        
        mock_detector.detect.assert_called_once()
```

### **Integration Tests**

```python
# tests/integration/test_service_integration.py
def test_full_analysis_flow(client):
    response = client.post('/api/v1/analyze', json={
        'mod_list': ['USSEP.esp', 'SkyUI.esp'],
        'game': 'skyrimse'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'conflicts' in data
```

---

## 📊 Service Dependencies

```
┌─────────────────────────────────────────────────────────┐
│                     Blueprints (API)                     │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                   Services Layer                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐│
│  │ Analysis │  │   Auth   │  │Community │  │  Search  ││
│  │ Service  │  │ Service  │  │ Service  │  │ Service  ││
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘│
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                  Repositories Layer                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │   User   │  │ Community│  │   Mod    │              │
│  │Repository│  │Repository│  │Repository│              │
│  └──────────┘  └──────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    Database (SQLAlchemy)                 │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Future Services

### **Planned Additions**

| Service | Purpose | Status |
|---------|---------|--------|
| `notification_service.py` | Email, push notifications | 📋 Planned |
| `ml_service.py` | Machine learning predictions | 📋 Planned |
| `analytics_service.py` | Ad analytics (Pro feature) | 📋 Planned (Ad Builder) |
| `video_export_service.py` | Video rendering for ads | 📋 Planned (Ad Builder) |

### **Existing Services (Not in `services/`)**

| Service | Location | Notes |
|---------|----------|-------|
| `telemetry_service.py` | `samson_telemetry.py` (root) | ✅ Complete |
| `export_service.py` | `presentation_service.py` (root) | ✅ Complete |
| `cache_service.py` | `cache_service.py` (root) | ✅ Complete |
| `ad_builder_service.py` | `ad_builder_service.py` (root) | ✅ Phase 1 Complete |

### **Service Extraction**

**Candidates for extraction from `app.py`:**

```python
# Future: services/list_builder_service.py
# Currently in: list_builder.py (root level)

# Future: services/mod_recommendation_service.py
# Currently in: mod_recommendations.py (root level)

# Future: services/system_impact_service.py
# Currently in: system_impact.py (root level)
```

---

## 🔐 Security Considerations

### **Input Validation**

Always validate service inputs:

```python
from security_utils import validate_mod_list

def analyze_mod_list(mod_list, game):
    mod_list = validate_mod_list(mod_list)  # Validate
    game = validate_game_id(game)  # Validate
    return ConflictDetector().detect(mod_list)
```

### **Rate Limiting**

Apply rate limiting at service level:

```python
from security_utils import rate_limit

@rate_limit(limit=30, window=60)
def analyze_mod_list(mod_list, game):
    # ...
```

### **Logging**

Log service operations (without PII):

```python
import logging
from logging_utils import redact_email

logger = logging.getLogger(__name__)

def authenticate_user(email, password):
    logger.info(f"Auth attempt for {redact_email(email)}")
    # ...
```

---

## 📈 Performance

### **Caching**

Use cache for expensive operations:

```python
from cache_service import cache

def analyze_mod_list(mod_list, game):
    cache_key = f"analysis:{game}:{hash(mod_list)}"
    
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    result = ConflictDetector().detect(mod_list)
    cache.set(cache_key, result, ttl=3600)
    return result
```

### **Batch Operations**

Batch database operations:

```python
# ✅ Good: Batch insert
def save_multiple_conflicts(conflicts):
    session.bulk_insert_mappings(Conflict, conflicts)
    session.commit()

# ❌ Bad: One-by-one
def save_multiple_conflicts(conflicts):
    for conflict in conflicts:
        session.add(Conflict(**conflict))  # Slow
    session.commit()
```

---

**Last Updated:** February 20, 2026
