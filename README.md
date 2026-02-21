# SkyModderAI

**AI-powered mod compatibility checker for Bethesda games.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/SamsonProject/SkyModderAI.git
cd SkyModderAI

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

Then open **http://localhost:5000**

---

## ✨ Features

### **Core Features**

| Feature | Description | Why It Matters |
|---------|-------------|----------------|
| **Conflict Detection** | Finds incompatible mods, missing requirements, load order issues | Prevents CTDs and broken saves |
| **Load Order Validator** | Suggests correct load order based on LOOT rules + community data | Based on LOOT rules + community data |
| **Requirements Checker** | Validates mod dependencies | Catches missing masters before release |
| **Compatibility Database** | Crowdsourced mod compatibility from real users | Real-world data from actual users |
| **LOOT Metadata Generator** | Generates YAML for masterlist | Saves mod authors hours of work |

### **Advanced Features**

| Feature | Description | Status |
|---------|-------------|--------|
| **🐾 OpenCLAW** | Automated modding assistant — learns from sessions, proposes improvements | ✅ Browser-based |
| **List Builder** | Build mod lists from preferences (performance, stability, visuals) | ✅ Complete |
| **Community Builds** | Share and discover community load orders | ✅ Complete |
| **Shared Load Orders** | Save and share your mod lists with the community | ✅ Complete |
| **Feedback System** | Rate conflicts, submit bugs, suggest improvements | ✅ Complete |
| **API** | RESTful API for developers | ✅ `/api/v1/` |

### **Coming Soon**

- **Mod Manager Integration** — MO2, Vortex, Wabbajack plugins
- **Real-time Collaboration** — Work on mod lists with friends
- **Advanced Analytics** — Track mod performance over time
- **Mobile App** — Check your mod list on the go

---

## 🎮 Supported Games

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

## 🐾 OpenCLAW — Automated Modding Assistant

**OpenCLAW is your browser-based automated modding assistant.** It learns from your modding sessions, proposes improvements, and guides implementation — all safely sandboxed.

### **What OpenCLAW Does**

1. **Analyzes** your current mod conflicts and performance
2. **Researches** solutions from Nexus, Reddit, GitHub
3. **Proposes** a 5-phase improvement plan
4. **Executes** changes in a sandbox (with your permission)
5. **Learns** from your feedback to improve future suggestions

### **Access OpenCLAW**

1. Navigate to the site
2. Click **"OpenCLAW"** in the main navigation
3. Grant permissions (8 granular scopes available)
4. Propose a plan (select goal, playstyle, game)
5. Execute and enjoy!

**URL:** `/api/v1/openclaw/`

### **OpenCLAW Safety**

- ✅ Permission-based access (you control what it can do)
- ✅ Sandbox isolation (can't modify system files)
- ✅ Hard-coded denied operations (BIOS, kernel, drivers blocked)
- ✅ File extension whitelist (only safe types allowed)
- ✅ Path traversal protection (no escapes from sandbox)
- ✅ Audit logging (all operations tracked)

---

## 🏗️ Architecture

### **Design Principles**

1. **Deterministic First, AI Second** — Rules don't hallucinate (90/10 split)
2. **Privacy by Default** — No PII in telemetry, local-first storage
3. **Community-Driven** — Crowdsourced compatibility data
4. **Transparent** — Show exactly why conflicts are flagged
5. **Self-Limiting** — Success means the problem is solved

### **Tech Stack**

- **Backend:** Python 3.9+, Flask
- **Database:** PostgreSQL (production), SQLite (development)
- **Cache:** Redis (production), in-memory (development)
- **Frontend:** Vanilla JS, no framework
- **Testing:** pytest, hypothesis, locust

### **Repository Structure**

```
SkyModderAI/
├── blueprints/          # Flask route blueprints
│   ├── api.py           # REST API
│   ├── analysis.py      # Analysis routes
│   ├── auth.py          # Authentication
│   ├── community.py     # Community features
│   ├── openclaw.py      # OpenCLAW automation
│   └── ...
├── services/            # Business logic
├── repositories/        # Data access layer
├── templates/           # HTML templates
├── static/              # Frontend assets
├── tests/               # Test suite
└── docs/                # Documentation
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for full system design.

---

## 📚 Documentation

### **Getting Started**
- [Quickstart Guides](docs/QUICKSTART_GUIDES.md) — MO2, Vortex, Wabbajack integration
- [Modding Glossary](docs/MODDING_GLOSSARY.md) — ESP vs ESM, load order, conflicts
- [Common Conflicts](docs/COMMON_CONFLICTS.md) — Known issues with popular mods

### **Technical Documentation**
- [Architecture](ARCHITECTURE.md) — System design, data flow, storage strategy
- [Build Guide](docs/build.md) — Setup, installation, deployment
- [Data Models](docs/models.md) — Database schema and ORM
- [Security](docs/SECURITY.md) — Security policies and best practices

### **OpenCLAW Documentation**
- [User Guide](docs/openclaw_browser_implementation.md) — How to use OpenCLAW
- [Technical Plan](docs/openclaw_browser_plan.md) — Enhancement roadmap

### **Research & Philosophy**
- [Research Summary](docs/RESEARCH_SUMMARY.md) — Comprehensive research integration
- [Philosophy](PHILOSOPHY.md) — Core principles
- [Samson Manifesto](docs/samson_manifesto.md) — Long-term vision

**Full documentation index:** [docs/README.md](docs/README.md)

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test suite
pytest tests/test_conflict_detector.py -v

# Run OpenCLAW tests
pytest tests/test_openclaw.py -v
```

**Test Coverage:** 80%+ required (enforced in CI)

---

## 🤝 Contributing

### **Ways to Contribute**

1. **Code** — New features, bug fixes, performance improvements
2. **Documentation** — Guides, tutorials, translations
3. **Testing** — Bug reports, compatibility data
4. **Community** — Help others, share builds, vote on features

### **Quick Start**

```bash
git clone https://github.com/SamsonProject/SkyModderAI.git
cd SkyModderAI
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
pre-commit install
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

### **Good First Issues**

- UI improvements for compatibility database
- Load order share frontend
- Mod author verification flow
- SEO landing pages for mod pairs
- Test coverage improvements

---

## 🔒 Security & Privacy

### **What We Track**
- Feature usage (anonymized)
- Compatibility patterns (aggregated)
- Session continuity (local UUID)

### **What We DON'T Track**
- Personal identifiers (email, IP — hashed only)
- Full mod lists (unless explicitly shared)
- Session duration (we don't optimize for addiction)

### **Your Rights**
- **Export your data:** `GET /api/samson/telemetry/export`
- **Delete your data:** `POST /api/samson/telemetry/delete`
- **Opt-out:** Set `SAMSON_TELEMETRY_ENABLED=false`

See [SECURITY.md](SECURITY.md) for full security policy.

---

## 📊 Performance & Scaling

### **Current Capacity**

| Users | PostgreSQL Pool | Max Overflow | Cache |
|-------|----------------|--------------|-------|
| **10K** | 10 | 20 | Redis |
| **100K** | 20 | 40 | Redis |
| **1M** | 50 | 100 | Redis Cluster |

### **Optimizations**

- Redis caching (production)
- LOOT data cached for 7 days
- In-memory fallback (development)
- Rate limiting (default: 100/minute)
- Connection pooling

See [docs/scaling_guide.md](docs/scaling_guide.md) for detailed scaling strategies.

---

## 🎯 Roadmap

### **Q1 2026** (Current)
- [x] OpenCLAW browser integration
- [x] Codebase cleanup & consistency fixes
- [ ] Compatibility database UI
- [ ] Mod author verification program

### **Q2 2026**
- [ ] 10K active users
- [ ] Mod manager plugins (MO2, Vortex)
- [ ] Real-time collaboration
- [ ] Mobile-responsive UI

### **2027+**
- [ ] Phase II deployment (ecological beachhead)
- [ ] Worker ownership pilot (first robot equity)
- [ ] Ethical AGI research (cognitive architecture)

---

## 📞 Support & Community

### **Get Help**
- **Email:** support@skymodderai.com
- **GitHub:** [Issues](https://github.com/SamsonProject/SkyModderAI/issues)
- **Reddit:** r/skyrimmods (tag: [SkyModderAI])

### **Community Resources**
- **Nexus Mods:** [Mod compatibility data](https://www.nexusmods.com/)
- **LOOT:** [Load Order Optimization Tool](https://loot.github.io/)
- **UESP:** [Unofficial Elder Scrolls Pages](https://en.uesp.net/)

---

## 📜 License

**MIT License** — Free to use, modify, and distribute.

```
Copyright (c) 2026 SkyModderAI

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

See [LICENSE](LICENSE) for full terms.

---

## 🙏 Acknowledgments

- **LOOT Team** — Load order rules and masterlist data
- **Nexus Mods** — Mod hosting and API
- **UESP** — Game mechanics documentation
- **xEdit Team** — Mod cleaning tools
- **Modding Community** — Compatibility reports and feedback

---

## 🎮 Built by Modders, for Modders

**SkyModderAI** is 100% free + donations. No paywalls, no premium tiers, no bullshit.

If it saved your load order, consider buying us a mead. If not, no hard feelings — use it, leave it, come back when you need it.

**Free forever. Open source. Privacy-first.**

---

**Last Updated:** February 20, 2026  
**Version:** 1.0.0 (Beta)

[![Built with Python](https://img.shields.io/badge/Built%20with-Python-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Powered by Flask](https://img.shields.io/badge/Powered%20by-Flask-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Hosted on Render](https://img.shields.io/badge/Hosted%20on-Render-46E3B7?logo=render&logoColor=white)](https://render.com/)
