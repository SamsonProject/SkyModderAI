# 🚀 Quick Start Guides

**Get SkyModderAI working with your mod manager in 5 minutes.**

---

## 📋 Table of Contents

- [Mod Organizer 2](#mod-organizer-2)
- [Vortex](#vortex)
- [Wabbajack](#wabbajack)
- [Manual Modding](#manual-modding)

---

## 🛠️ Mod Organizer 2

### Step 1: Install SkyModderAI

```bash
# Clone the repository
git clone https://github.com/SamsonProject/SkyModderAI.git
cd SkyModderAI

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

Open your browser to **http://localhost:5000**

---

### Step 2: Export Your Mod List from MO2

**Method A: Copy to Clipboard (Recommended)**

1. In Mod Organizer 2, go to **Tools** → **Copy to clipboard**
2. Select **Active mods**
3. Your mod list is now copied!

**Method B: Export to File**

1. In Mod Organizer 2, go to **Tools** → **Export mod list**
2. Save as `my_mods.txt`
3. Open the file and copy the contents

---

### Step 3: Analyze in SkyModderAI

1. Go to **http://localhost:5000**
2. Select your game (Skyrim SE, Fallout 4, etc.)
3. Paste your mod list into the text box
4. Click **Analyze**

---

### Step 4: Review Results

SkyModderAI will show:

- ✅ **Compatible mods** (no action needed)
- ⚠️ **Conflicts** (need patches or load order changes)
- ❌ **Incompatible mods** (can't use together)
- 💡 **Recommendations** (patches and compatibility mods)

---

### Step 5: Apply Fixes

**For each conflict:**

1. Click on the conflict to see details
2. Follow the recommended solution:
   - Download suggested patches from Nexus
   - Adjust load order as recommended
   - Remove incompatible mods if necessary
3. Return to MO2 and apply changes
4. Re-analyze to confirm fixes

---

### Pro Tips for MO2 Users

**Create Profiles for Testing:**
```
1. Click the Profiles button (📋)
2. Create "Testing - Before SkyModderAI"
3. Make your changes
4. Create "Testing - After Fixes"
5. Compare stability
```

**Use MO2's Conflict Filter:**
```
1. Right-click on a mod
2. Select "Information"
3. Go to "Conflicts" tab
4. Cross-reference with SkyModderAI results
```

**Export Load Order:**
```
1. Tools → Copy to clipboard → Load order
2. Paste into SkyModderAI for load order analysis
```

---

## 🌀 Vortex

### Step 1: Install SkyModderAI

Same as MO2 (see above).

---

### Step 2: Export Your Mod List from Vortex

**Method A: Copy as Text**

1. In Vortex, go to **Mods** → **Plugins**
2. Click the **⋮** (three dots) menu
3. Select **Export** → **Copy as text**
4. Your mod list is copied!

**Method B: Export to File**

1. In Vortex, go to **Mods** → **Plugins**
2. Click the **⋮** menu
3. Select **Export** → **Export to file**
4. Save and open the file

---

### Step 3: Analyze in SkyModderAI

Same as MO2 (see above).

---

### Step 4: Apply Fixes in Vortex

**Adjust Load Order:**
```
1. Go to Plugins tab
2. Drag mods to reorder
3. Use SkyModderAI's recommended order
4. Vortex will show deployment changes
```

**Install Patches:**
```
1. Download patches from Nexus (via Vortex)
2. Vortex will auto-detect and install
3. Enable patches in Plugins tab
4. Re-analyze to confirm
```

**Resolve Conflicts:**
```
1. Vortex shows conflicts in the Mods tab
2. Click on a conflict to see details
3. Choose which mod wins (or use patches)
4. Cross-reference with SkyModderAI
```

---

### Pro Tips for Vortex Users

**Use Collections:**
```
1. Create a collection for your stable build
2. Export collection before making changes
3. Test SkyModderAI recommendations
4. Revert if needed
```

**Enable Auto-Sort:**
```
1. Settings → Load Order Sorting
2. Enable "Auto-sort load order"
3. Vortex will use LOOT rules
4. SkyModderAI adds extra conflict detection
```

**Deployment Check:**
```
1. After changes, click "Deploy Mods"
2. Vortex will show file conflicts
3. Resolve in favor of SkyModderAI recommendations
```

---

## 📦 Wabbajack

### Step 1: Analyze Before Building

**Import Wabbajack List:**

1. Go to **http://localhost:5000**
2. Select **Import** → **Wabbajack (.wabbajack)**
3. Upload your `.wabbajack` file
4. SkyModderAI will analyze the entire list

---

### Step 2: Review Pre-Build Analysis

SkyModderAI will show:

- ✅ **List is stable** (proceed with build)
- ⚠️ **Known conflicts** (may need manual patches)
- ❌ **Critical issues** (consider different list)

---

### Step 3: Customize (Optional)

**Remove Problematic Mods:**
```
1. In Wabbajack, click "Manual Installation"
2. Uncheck mods flagged by SkyModderAI
3. Add replacement mods if needed
4. Proceed with build
```

**Add Extra Mods:**
```
1. Build your Wabbajack list first
2. Export final mod list
3. Analyze in SkyModderAI with additions
4. Install recommended patches
```

---

### Pro Tips for Wabbajack Users

**Test Before Long Build:**
```
1. Export mod list from similar Wabbajack build
2. Analyze in SkyModderAI
3. Identify potential issues before 2-hour build
```

**Post-Build Check:**
```
1. After Wabbajack completes, export mod list
2. Run through SkyModderAI
3. Install any missing patches
4. Enjoy stable game!
```

**Custom Lists:**
```
1. Build your custom list
2. Export mod list from Wabbajack
3. Submit to SkyModderAI community database
4. Help other modders!
```

---

## 📝 Manual Modding

### Step 1: Gather Your Mod List

**From Game Folder:**
```
1. Go to your game's Data folder
2. List all .esp, .esm, .esl files
3. Copy the filenames
```

**From Mod Manager:**
```
1. Whatever manager you use, export enabled mods
2. Most have "Export" or "Copy to clipboard" options
3. If not, manually list them
```

---

### Step 2: Format for SkyModderAI

**Accepted Formats:**

```
# Simple list (one mod per line)
USSEP.esp
SkyUI.esp
Immersive Armors.esp

# With load order (numbered)
1. USSEP.esp
2. SkyUI.esp
3. Immersive Armors.esp

# From LOOT (paste directly)
[2024-01-15 12:00:00] LOOT v0.18.0
- USSEP.esp
- SkyUI.esp
```

---

### Step 3: Analyze and Apply

Same as other managers (see above).

---

## 🎯 Game-Specific Guides

### Skyrim Special Edition

**Recommended Analysis Settings:**
```
- Game: Skyrim SE
- Version: Your actual version (check in game)
- Include ESL: Yes
- Check for patches: Yes
```

**Common Skyrim SE Issues:**
- AE update broke some mods (check compatibility)
- Script extender (SKSE) must match game version
- Some mods need Anniversary Edition content

---

### Fallout 4

**Recommended Analysis Settings:**
```
- Game: Fallout 4
- Version: Next-Gen or Classic (choose correctly)
- Include Creation Club: If you have CC content
```

**Common Fallout 4 Issues:**
- Next-Gen update (2024) broke some mods
- F4SE must match game version
- DLC requirements vary by mod

---

### Oblivion

**Recommended Analysis Settings:**
```
- Game: Oblivion
- Version: GOTY Edition (recommended)
- Include unofficial patches: Yes
```

**Common Oblivion Issues:**
- 4GB patch required for heavy modding
- LOOT rules less comprehensive (older game)
- Many mods are 10+ years old (check compatibility)

---

## ❓ Troubleshooting

### "Mod list won't paste"
**Solution:** Make sure you're copying the full list. Some managers have character limits in their export.

### "Results don't match my game"
**Solution:** Check that you selected the correct game and version. Skyrim SE ≠ Skyrim AE ≠ Skyrim VR.

### "I don't understand the conflicts"
**Solution:** Click on each conflict for details. Still confused? Ask on our Discord or r/skyrimmods.

### "Fixes didn't work"
**Solution:** Some conflicts require manual patching (xEdit). We flag them, but can't auto-fix everything.

---

## 📚 Next Steps

After analyzing your mods:

1. ✅ **Apply all critical fixes**
2. ⚠️ **Consider high-priority recommendations**
3. 💡 **Browse optional patches for perfection**
4. 🎮 **Test your game!**
5. 🔄 **Re-analyze after adding new mods**

---

## 🤝 Need Help?

- **Discord:** [Join our server](https://discord.gg/YOUR_INVITE)
- **Reddit:** r/skyrimmods, r/falloutmods
- **GitHub:** [Open an issue](https://github.com/SamsonProject/SkyModderAI/issues)

---

**Happy modding!** 🛡️

*Last updated: February 20, 2026*
