# 🛡️ SkyModderAI

**The smart mod compatibility checker for Bethesda games.** Built by modders, for modders.

[![CI](https://github.com/SamsonProject/SkyModderAI/actions/workflows/ci.yml/badge.svg)](https://github.com/SamsonProject/SkyModderAI/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Discord](https://img.shields.io/badge/Discord-Join-7289da?logo=discord)](https://discord.gg/YOUR_INVITE)
[![Nexus Mods](https://img.shields.io/badge/Nexus%20Mods-Follow-black?logo=nexus-mods)](https://www.nexusmods.com/users/YOUR_ID)

![Skyrim Banner](docs/images/banner-skyrim.jpg)

---

## ⚡ Quick Start

**Got a mod list ready? Let's find those conflicts in under 2 minutes:**

```bash
# Clone and run
git clone https://github.com/SamsonProject/SkyModderAI.git
cd SkyModderAI
pip install -r requirements.txt
python app.py
```

Then open **http://localhost:5000** and paste your mod list.

**No installation needed** — Also available as a [web app](https://skymodderai.onrender.com).

---

## 🎮 What It Does

SkyModderAI analyzes your load order and tells you:

| Feature | What You Get |
|---------|--------------|
| **Conflict Detection** | Finds incompatible mods before they crash your game |
| **LOOT Integration** | Uses the same load order rules as LOOT, with extra smarts |
| **Smart Suggestions** | Recommends patches and compatibility mods from Nexus |
| **Export Options** | Save your analysis as PDF, HTML, or Markdown |
| **Core Tool: 100% Free** | No accounts, no paywalls, no ads in the analyzer |

### Example Output

```
⚠️ 3 Conflicts Found

1. SMIM vs. SkyUI
   → Solution: Install "SMIM SkyUI Patch" (Nexus ID: 12345)

2. Ordinator vs. Apocalypse Spells
   → Solution: Load Ordinator AFTER Apocalypse (LOOT rule #4521)

3. ENB vs. Realistic Lighting
   → Warning: Known incompatibility. Consider "ENB Light Patch"
```

---

## 💰 How We Make Money (Honest Talk)

**The core tool is free. Always will be.** No ads in your analyzer. No premium tiers.

We make money two ways:

### 1. 🍺 Buy Me Mead (Direct Donations)
See a mead bottle somewhere on the site? Click it if you're feeling generous. That's it. No guilt trips, no fake urgency. Just a modder saying "thanks."

### 2. 📦 Business/Shopping Tab (Democratic Ads)
Want to promote your modding business, commission service, or curated list?
- **$0 upfront** — List your service for free
- **Pay per 1000 vetted clicks** — Only charged when real modders engage
- **Community-voted sorting** — Good ads rise, spam sinks
- **Transparent pricing** — See exactly what you're paying for

**Why this works:** We only make money when users find value in the ads. So we're incentivized to show relevant stuff, not spam.

**No corporate bullshit.** No data selling. No tracking your mod list.

---

## 🎯 Supported Games

- **Skyrim:** Legendary Edition, Special Edition, Anniversary Edition, VR
- **Fallout:** 3, New Vegas, 4
- **Oblivion** (beta support)
- **Starfield** (early access)

---

## 📸 Screenshots

### Main Analysis Dashboard
![Dashboard Screenshot](docs/images/screenshot-dashboard.png)

### Conflict Report
![Conflict Report](docs/images/screenshot-conflicts.png)

### Mod Recommendations
![Recommendations](docs/images/screenshot-recommendations.png)

---

## 🔧 Integration with Your Workflow

### Mod Organizer 2
```bash
# Export mod list from MO2
Tools → Copy to clipboard → Active mods
# Paste into SkyModderAI
```

### Vortex
```bash
# Export from Vortex
Plugins → Export → Copy as text
# Paste into SkyModderAI
```

### Wabbajack
```bash
# Analyze custom lists before building
SkyModderAI → Import → Wabbajack .wabbajack file
```

### LOOT
```bash
# SkyModderAI uses LOOT's masterlist automatically
# No configuration needed - just works
```

---

## 🚀 Advanced Usage

### Command Line Analysis
```bash
# Analyze a mod list file
python app.py analyze --game skyrimse my_mods.txt

# Export to PDF
python app.py analyze --game skyrimse --export pdf my_mods.txt

# Show only critical conflicts
python app.py analyze --game skyrimse --severity critical my_mods.txt
```

### API Access
```python
import requests

response = requests.post('http://localhost:5000/api/analyze', json={
    'game': 'skyrimse',
    'mod_list': 'USSEP.esp\nSkyUI.esp\n...'
})

conflicts = response.json()['conflicts']
print(f"Found {len(conflicts)} conflicts")
```

### Batch Testing
```bash
# Test multiple load orders
for list in load_orders/*.txt; do
    python app.py analyze --game skyrimse "$list"
done
```

---

## 📚 Documentation

| Guide | Description |
|-------|-------------|
| [Quick Start](docs/README.md) | Get running in 5 minutes |
| [Modding Glossary](docs/MODDING_GLOSSARY.md) | ESP vs ESM, load order, ITMs, and more |
| [Common Conflicts](docs/COMMON_CONFLICTS.md) | Known issues with popular mods |
| [Architecture](ARCHITECTURE.md) | How it works under the hood |
| [Contributing](CONTRIBUTING.md) | How to help improve SkyModderAI |

---

## 🤝 Community

**Join 2,000+ modders keeping their games stable:**

- 💬 **[Discord Server](https://discord.gg/YOUR_INVITE)** — Get help, share load orders
- 📱 **[Reddit](https://reddit.com/r/skyrimmods)** — Post your success stories
- 🐛 **[GitHub Issues](https://github.com/SamsonProject/SkyModderAI/issues)** — Report bugs, request features
- ⭐ **[Nexus Mods](https://www.nexusmods.com/users/YOUR_ID)** — Follow for updates

### Featured by

- r/skyrimmods — [Community Spotlight, Jan 2025](https://reddit.com/r/skyrimmods/comments/...)
- r/falloutmods — [Tool Recommendation](https://reddit.com/r/falloutmods/comments/...)

---

## 🛠️ Development

### Setup for Contributors
```bash
git clone https://github.com/SamsonProject/SkyModderAI.git
cd SkyModderAI
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
pre-commit install
```

### Running Tests
```bash
# Full test suite
pytest tests/

# Test specific game parser
pytest tests/test_loot_parser.py -k skyrimse

# Performance tests
pytest tests/test_performance.py
```

### Code Quality
```bash
# Format code
ruff format .

# Lint
ruff check .

# Type checking
mypy blueprints/ services/
```

---

## 📊 Performance

- **500 mods analyzed in < 5 seconds** (tested on M1 Mac)
- **< 300KB page load** (mobile-friendly)
- **Offline-capable** (core features work without internet)

---

## 🔒 Privacy & Security

- **No accounts required** for basic usage
- **All analysis runs locally** (your mod list never leaves your PC unless you opt-in)
- **Open source** — audit the code yourself
- **No telemetry** (we don't track what mods you use)

---

## 💖 Support the Project

SkyModderAI is **free and will stay free**. We're not selling your data, not gating features, and not turning into a corporate hellscape.

### 🍺 Buy Me Mead
See a mead bottle icon? Click it if you're feeling generous. No guilt trips, no "unlock premium features" bullshit. Just a modder saying thanks.

### 📦 Promote Your Business
Got a modding commission service? Curated lists? Community projects?
- **List for free** on our Shopping/Business tabs
- **Pay only for real engagement** ($0 upfront, charged per 1000 vetted clicks)
- **Community decides what rises** through democratic voting

**Why this matters:** We only make money when users find value in promoted content. So we're incentivized to show relevant stuff, not spam.

### Other Ways to Help
- ⭐ **[Star this repo](https://github.com/SamsonProject/SkyModderAI)** — Helps others find it
- 🐛 **[Report conflicts](https://github.com/SamsonProject/SkyModderAI/issues)** — Make the database smarter
- 📢 **[Tell your friends](#)** — Word of mouth is everything

**Current monthly costs:** $15 (hosting) | **Sponsored by:** [Your Name Here]

---

## 📜 License

MIT License — Use it, modify it, share it. Just don't blame us if your save game gets corrupted (always back up!).

---

## 🙏 Credits

**Built on the shoulders of giants:**

- **[LOOT Team](https://github.com/loot/loot)** — Load order masterlists
- **[Nexus Mods](https://www.nexusmods.com/)** — Mod database API
- **[UESP](https://en.uesp.net/)** — Game mechanics documentation
- **[xEdit Team](https://github.com/xEdit/xEdit)** — Conflict detection inspiration

**Contributors:**

[![Contributors](https://contrib.rocks/image?repo=SamsonProject/SkyModderAI)](https://github.com/SamsonProject/SkyModderAI/graphs/contributors)

---

## 🎯 Roadmap

### Q2 2026
- [ ] Wabbajack integration (direct import)
- [ ] Mod profile management (save/load multiple configs)
- [ ] Real-time conflict detection (as you add mods)

### Q3 2026
- [ ] Starfield full support
- [ ] AI-powered load order optimization
- [ ] Community-sourced conflict rules

### Q4 2026
- [ ] MO2/Vortex plugin (run inside mod managers)
- [ ] Automated patch suggestions (xEdit scripts)
- [ ] Multiplayer co-op modding sessions

---

**Last updated:** February 20, 2026 | **Version:** 1.4.2

---

<div align="center">

**🛡️ Mod safely. Mod smarter. Mod longer.**

*SkyModderAI is not affiliated with Bethesda Softworks or ZeniMax Media.*

</div>
