# SkyModderAI Mod Organizer 2 Extension

**Version:** 1.0.0  
**Compatibility:** Mod Organizer 2.4.0+  
**Game Support:** Skyrim SE, Skyrim VR, Fallout 4, Oblivion

---

## 📦 Installation

### Option 1: Install via MO2 Extension Manager

1. Open Mod Organizer 2
2. Tools → Extension Manager
3. Search for "SkyModderAI"
4. Click Install

### Option 2: Manual Installation

1. Download this extension
2. Extract to: `<MO2 Folder>/plugins/skyrimse/skymodderai/`
3. Restart MO2
4. Enable in Tools → Extensions

---

## 🚀 Features

### One-Click Analysis

- Analyze your current mod list without leaving MO2
- Get instant conflict detection
- View compatibility scores

### Export to SkyModderAI

- Export mod list with one click
- Automatically includes load order
- Supports all MO2 profiles

### Import Fixes

- Import recommended load order
- Auto-resolve conflicts
- Apply patches from Nexus

### Real-time Monitoring

- Monitor for new compatibility reports
- Get notified of conflicts
- Track mod updates

---

## 📖 Usage Guide

### Analyze Your Mod List

1. Click the **SkyModderAI** icon in toolbar (or Tools → SkyModderAI)
2. Click **"Analyze Current Load Order"**
3. Wait for analysis to complete
4. Review conflicts and recommendations

### Export Mod List

1. Tools → SkyModderAI → Export Mod List
2. Choose export format:
   - Simple list (mod names only)
   - Full export (with load order, metadata)
   - JSON (for API use)
3. Click Export
4. File saved to: `<MO2 Folder>/exports/skymodderai_YYYYMMDD.txt`

### Import Recommendations

1. After analysis, click **"Import Recommended Load Order"**
2. MO2 will prompt to reorder mods
3. Confirm to apply changes
4. Load order updated!

---

## 🔧 Configuration

### Settings

Open: Tools → Extensions → SkyModderAI

**General:**
- [ ] Enable auto-analysis on profile change
- [ ] Show notification badge on conflicts
- [ ] Auto-export on mod install

**API:**
- Server URL: `https://skymodderai.com`
- API Key: (optional, for premium features)

**Notifications:**
- [ ] Show toast on new conflicts
- [ ] Email notifications
- [ ] Discord webhook

---

## 🎨 Toolbar Integration

The extension adds a toolbar icon:

```
[💾] [📦] [⚙️] [🔍 SkyModderAI] [📊]
```

Click to open the SkyModderAI panel.

---

## 📊 SkyModderAI Panel

### Tabs

1. **Analysis** - Current conflict report
2. **Compatibility** - Search compatibility database
3. **Exports** - Manage exported mod lists
4. **Settings** - Extension configuration

### Analysis Tab

Shows:
- Total mods
- Conflicts detected
- Compatibility score
- Recommended fixes

Click on a conflict to:
- View details
- Download patch
- Adjust load order

---

## 🔌 API Integration

### Export Format

**Simple List:**
```
USSEP.esp
SkyUI.esp
Immersive Armors.esp
```

**Full Export:**
```json
{
  "game": "skyrimse",
  "profile": "Default",
  "mod_count": 250,
  "mods": [
    {
      "name": "USSEP.esp",
      "enabled": true,
      "priority": 1,
      "load_order": 0
    }
  ]
}
```

---

## 🐛 Troubleshooting

### Extension Not Loading

1. Check MO2 version (2.4.0+ required)
2. Verify extension folder structure
3. Check MO2 log: `<MO2 Folder>/logs/mo_interface.log`

### Analysis Fails

1. Check internet connection
2. Verify server URL in settings
3. Try manual export/import

### Conflicts Not Showing

1. Click "Refresh Analysis"
2. Check if mod list changed
3. Clear cache: Settings → Clear Cache

---

## 📝 Development

### Build from Source

```bash
# Clone repository
git clone https://github.com/SamsonProject/SkyModderAI.git
cd SkyModderAI/extensions/mo2

# Install dependencies
pip install -r requirements.txt

# Build
python build.py

# Output: skymodderai_mo2.zip
```

### Project Structure

```
mo2-extension/
├── __init__.py          # Extension entry point
├── main_window.py       # Main UI window
├── analysis_panel.py    # Analysis tab
├── export_handler.py    # Export functionality
├── api_client.py        # SkyModderAI API client
├── config.py            # Configuration
└── resources/
    ├── icons/           # Toolbar icons
    └── styles/          # CSS styles
```

### API Client

```python
from api_client import SkyModderAIClient

client = SkyModderAIClient(api_key="your_key")

# Analyze mod list
result = client.analyze(mod_list=["USSEP.esp", "SkyUI.esp"])

# Get compatibility
compat = client.get_compatibility("USSEP", "SkyUI")

# Submit report
client.submit_report(
    mod_a="ModA.esp",
    mod_b="ModB.esp",
    status="incompatible",
    description="CTD on startup"
)
```

---

## 📄 License

MIT License - Same as SkyModderAI

---

## 🤝 Contributing

Contributions welcome! See main SkyModderAI CONTRIBUTING.md

---

## 📞 Support

- **Discord:** https://discord.gg/skyrimmods
- **GitHub:** https://github.com/SamsonProject/SkyModderAI/issues
- **Nexus:** https://nexusmods.com/skyrimspecialedition/mods/SKYMODDERAI

---

## 📈 Changelog

### 1.0.0 (2026-02-21)
- Initial release
- One-click analysis
- Export/import functionality
- Real-time monitoring

### 1.0.1 (TBD)
- Bug fixes
- Performance improvements
- Additional game support

---

**Happy Modding!** 🛡️
