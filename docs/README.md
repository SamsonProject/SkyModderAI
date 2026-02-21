# SkyModderAI Documentation

**Your complete reference for SkyModderAI — AI-powered mod compatibility checker for Bethesda games.**

---

## 📖 Getting Started

### **New Users**
- [Quickstart Guides](QUICKSTART_GUIDES.md) — MO2, Vortex, Wabbajack integration
- [Modding Glossary](MODDING_GLOSSARY.md) — ESP vs ESM, load order, conflicts explained
- [Common Conflicts](COMMON_CONFLICTS.md) — Known issues with popular mods

### **Developers**
- [Build Instructions](build.md) — Setup, installation, running locally
- [Architecture Overview](architecture.md) — System design and data flow
- [Data Models](models.md) — Database schema and ORM models
- [Security Guide](SECURITY.md) — Security policies and best practices

---

## 🏗️ Architecture & Design

### **Core Architecture**
- [ARCHITECTURE.md](../ARCHITECTURE.md) — Main system architecture (root level)
- [architecture.md](architecture.md) — Thermodynamic and information-theoretic formulation
- [models.md](models.md) — Formal equations and data models
- [build.md](build.md) — Implementation path and build process

### **Design Decisions**
- [architecture_decision.md](architecture_decision.md) — Focused specialization over comprehensive database
- [PHILOSOPHY.md](../PHILOSOPHY.md) — Core principles and philosophy
- [samson_manifesto.md](samson_manifesto.md) — Long-term vision

---

## 🐾 OpenCLAW (Automated Modding Assistant)

**OpenCLAW is your browser-based automated modding assistant — it learns from sessions, proposes improvements, and guides implementation.**

### **User Guides**
- [OpenCLAW Browser Implementation](openclaw_browser_implementation.md) — How to use OpenCLAW
- [OpenCLAW Browser Plan](openclaw_browser_plan.md) — Future enhancement roadmap

### **Technical Documentation**
- [OpenCLAW Engine](../openclaw_engine.py) — Core engine (source code)
- [OpenCLAW Blueprint](../blueprints/openclaw.py) — API endpoints (source code)
- [OpenCLAW Dev Directory](../dev/) — Sandbox, guard, automator, learner (git-ignored)

### **OpenCLAW Features**
- ✅ Permission-based access (8 granular scopes)
- ✅ 5-phase improvement plans
- ✅ Safety validation (hard-coded constraints)
- ✅ Sandbox file operations
- ✅ Post-session feedback loop
- ✅ Privacy-first telemetry

---

## 🔬 Research & Data

### **Research Integration**
- [RESEARCH_SUMMARY.md](RESEARCH_SUMMARY.md) — Comprehensive research integration summary
- Bethesda game knowledge (10 games documented)
- Hardware recommendations (4 tiers)
- Compatibility patterns
- Community resources

### **Data Specifications**
- Structural export specification (archived - see RESEARCH_SUMMARY.md)
- Privacy-respecting data collection
- Community-driven knowledge base

---

## 🛡️ Security & Privacy

### **Security Documentation**
- [SECURITY.md](SECURITY.md) — Technical security details
- [../SECURITY.md](../SECURITY.md) — Security policy (root level)
- [../CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md) — Community standards

### **Privacy Features**
- ✅ No PII collected (email hashed only)
- ✅ Local-first architecture (mod lists in browser localStorage)
- ✅ Opt-in cloud sync
- ✅ Export/delete user data endpoints
- ✅ Privacy-first telemetry (SAMSON_TELEMETRY)

---

## 📚 Feature Documentation

### **Core Features**
1. **Conflict Detection**
   - Finds incompatible mods
   - Missing requirements
   - Load order issues

2. **Load Order Optimization**
   - LOOT rules integration
   - Community-driven suggestions
   - Deterministic-first approach

3. **Compatibility Database**
   - Crowdsourced mod compatibility
   - Real-world user data
   - Privacy-respecting collection

4. **OpenCLAW Automation**
   - Automated improvement plans
   - Sandbox execution
   - Feedback-driven learning

### **Advanced Features**
- **List Builder** — Build mod lists from preferences
- **Community Builds** — Share and discover community load orders
- **Shopping** — Ethical sponsor system (community-curated)
- **Business Directory** — Modding services marketplace
- **API** — RESTful API for developers

---

## 🧪 Testing

### **Test Structure**
```
tests/
├── unit/                    # Unit tests
│   ├── test_conflict_detector.py
│   ├── test_openclaw_engine.py
│   └── test_search_engine.py
├── integration/             # Integration tests
│   ├── test_integration.py
│   └── test_integration_e2e.py
├── openclaw/               # OpenCLAW tests
│   ├── test_openclaw.py
│   ├── test_openclaw_safety.py
│   └── test_openclaw_engine.py
└── conftest.py             # Shared test configuration
```

### **Running Tests**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_conflict_detector.py -v

# Run OpenCLAW tests
pytest tests/openclaw/ -v
```

---

## 📦 Project Structure

```
SkyModderAI/
├── 📄 README.md                    # Project overview
├── 📄 PHILOSOPHY.md                # Core principles
├── 📄 ARCHITECTURE.md              # System architecture
├── 📄 CONTRIBUTING.md              # Contribution guide
├── 📄 SECURITY.md                  # Security policy
├── 📄 CODE_OF_CONDUCT.md           # Community standards
│
├── 🐍 app.py                       # Main Flask application
├── 🐍 config.py                    # Configuration management
├── 🐍 models.py                    # SQLAlchemy ORM models
├── 🐍 constants.py                 # Shared constants
│
├── 📁 blueprints/                  # Flask route blueprints
│   ├── api.py                      # REST API endpoints
│   ├── analysis.py                 # Analysis routes
│   ├── auth.py                     # Authentication routes
│   ├── community.py                # Community features
│   ├── openclaw.py                 # OpenCLAW automation
│   ├── shopping.py                 # Shopping/sponsors
│   └── business.py                 # Business directory
│
├── 📁 services/                    # Business logic layer
│   ├── analysis_service.py
│   ├── community_service.py
│   ├── search_service.py
│   └── ...
│
├── 📁 repositories/                # Data access layer
│   ├── user_repository.py
│   ├── community_repository.py
│   └── mod_repository.py
│
├── 📁 templates/                   # HTML templates
│   ├── index.html                  # Main landing page
│   ├── openclaw.html               # OpenCLAW dashboard
│   ├── analysis.html               # Analysis interface
│   └── ...
│
├── 📁 static/                      # Frontend assets
│   ├── css/
│   ├── js/
│   └── images/
│
├── 📁 tests/                       # Test suite
│   ├── unit/
│   ├── integration/
│   └── openclaw/
│
├── 📁 docs/                        # Documentation (you are here)
│   ├── README.md                   # Documentation index
│   ├── QUICKSTART_GUIDES.md
│   ├── MODDING_GLOSSARY.md
│   ├── COMMON_CONFLICTS.md
│   └── ...
│
├── 📁 dev/                         # OpenCLAW development (git-ignored)
│   ├── sandbox.py
│   ├── guard.py
│   ├── automator.py
│   └── learner.py
│
└── 📁 migrations/                  # Database migrations
    ├── versions/
    └── ...
```

---

## 🚀 Development Workflow

### **1. Setup**
```bash
git clone https://github.com/SamsonProject/SkyModderAI.git
cd SkyModderAI
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
pre-commit install
```

### **2. Run Locally**
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env

# Run the application
python3 app.py
# Visit: http://localhost:5000
```

### **3. Enable OpenCLAW (Optional)**
```bash
export SKYMODDERAI_OPENCLAW_ENABLED=1
python3 app.py
# Visit: http://localhost:5000/api/v1/openclaw/
```

### **4. Run Tests**
```bash
# All tests
pytest

# With coverage
pytest --cov=. --cov-report=html

# Specific test suite
pytest tests/openclaw/ -v
```

### **5. Deploy**
```bash
# Production deployment (Render, Docker, etc.)
# See build.md for detailed deployment guide
```

---

## 📊 Supported Games

| Game | Status | Notes |
|------|--------|-------|
| **Skyrim SE/AE** | ✅ Production | Full support |
| **Skyrim Legendary** | ✅ Production | Full support |
| **Skyrim VR** | ✅ Production | Full support |
| **Fallout 4** | ✅ Production | Full support |
| **Oblivion** | 🧪 Beta | Community testing |
| **Fallout 3** | 📋 Planned | Future release |
| **Fallout: NV** | 📋 Planned | Future release |
| **Starfield** | 📋 Planned | Future release |

---

## 🔧 Configuration

### **Environment Variables**
See [`.env.example`](../.env.example) for all available options.

**Required:**
- `SECRET_KEY` — Session encryption
- `DATABASE_URL` — PostgreSQL connection string
- `BASE_URL` — Application base URL

**Optional:**
- `SKYMODDERAI_OPENCLAW_ENABLED` — Enable OpenCLAW (default: 0)
- `REDIS_URL` — Redis cache (production)
- `OPENAI_API_KEY` — AI chat features
- `STRIPE_SECRET_KEY` — Payment processing

---

## 🤝 Contributing

### **Ways to Contribute**
1. **Code** — New features, bug fixes, performance improvements
2. **Documentation** — Guides, tutorials, translations
3. **Testing** — Bug reports, compatibility data
4. **Community** — Help others, share builds, vote on features

### **Contribution Process**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit with clear messages
6. Open a Pull Request

See [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed guidelines.

---

## 📈 Scaling & Performance

### **Current Capacity**
- **100K users** — PostgreSQL pool: 20, max_overflow: 40
- **1M users** — PostgreSQL pool: 50, max_overflow: 100 (planned)

### **Performance Optimizations**
- Redis caching (production)
- LOOT data cached for 7 days
- In-memory fallback for development
- Rate limiting (default: 100/minute)

See [scaling_guide.md](scaling_guide.md) for detailed scaling strategies.

---

## 📞 Support & Community

### **Get Help**
- **Email:** support@skymodderai.com
- **GitHub:** [Issues](https://github.com/SamsonProject/SkyModderAI/issues)
- **Reddit:** r/skyrimmods (tag: [SkyModderAI])

### **Community Resources**
- **Nexus Mods:** [SkyModderAI](https://www.nexusmods.com/users/myaccount?tab=api+access)
- **LOOT:** [Load Order Optimization Tool](https://loot.github.io/)
- **UESP:** [Unofficial Elder Scrolls Pages](https://en.uesp.net/)

---

## 📜 License

**MIT License** — Free to use, modify, and distribute.

See [LICENSE](../LICENSE) for full terms.

---

## 🎯 Quick Links

| Category | Links |
|----------|-------|
| **Getting Started** | [Quickstart](QUICKSTART_GUIDES.md) · [Glossary](MODDING_GLOSSARY.md) · [Common Conflicts](COMMON_CONFLICTS.md) |
| **Architecture** | [Main Architecture](../ARCHITECTURE.md) · [Design Decisions](architecture_decision.md) · [Models](models.md) |
| **OpenCLAW** | [User Guide](openclaw_browser_implementation.md) · [Plan](openclaw_browser_plan.md) · [Engine](../openclaw_engine.py) |
| **Development** | [Build Guide](build.md) · [Security](SECURITY.md) · [Contributing](../CONTRIBUTING.md) |
| **Research** | [Research Summary](RESEARCH_SUMMARY.md) · [Philosophy](../PHILOSOPHY.md) |
| **Ad Builder** | [Design](AD_BUILDER_DESIGN.md) · [Progress](AD_BUILDER_PROGRESS.md) · [README](AD_BUILDER_README.md) |
| **Archive** | [Historical Docs](archive/README.md) |

---

**Last Updated:** February 21, 2026  
**Version:** 1.0.0 (Beta)

**Built by modders, for modders.** 🎮
