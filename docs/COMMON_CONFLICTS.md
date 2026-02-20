# ⚠️ Common Mod Conflicts

**Known incompatibilities and how to fix them. Updated regularly by the community.**

---

## 🏆 Popular Mods with Known Conflicts

### SkyUI
**What it does:** PC-friendly inventory interface

**Conflicts with:**
- **Chesko's Wearable Lanterns** → Install "Wearable Lanterns - SkyUI Patch"
- **iNeed** → Install "iNeed - SkyUI Patch"
- **Frostfall** → Usually compatible, but load SkyUI FIRST

**Load order tip:** SkyUI should load EARLY (after patches, before gameplay mods)

**Nexus ID:** [3863](https://www.nexusmods.com/skyrimspecialedition/mods/3863)

---

### Ordinator - Perks of Skyrim
**What it does:** Complete perk tree overhaul

**Conflicts with:**
- **Apocalypse - Magic Overhaul** → Install "Ordinator - Apocalypse Patch"
- **Adamant** → INCOMPATIBLE (choose one perk overhaul)
- **Vanilla perk mods** → Most are incompatible; use Ordinator add-ons instead

**Safe with:**
- ✅ SkyUI
- ✅ USSEP
- ✅ Combat mods (most)
- ✅ Visual mods

**Load order tip:** Ordinator loads AFTER most mods, BEFORE patches

**Nexus ID:** [1137](https://www.nexusmods.com/skyrimspecialedition/mods/1137)

---

### Immersive Armors
**What it does:** Adds 600+ new armors to leveled lists

**Conflicts with:**
- **Immersive Weapons** → Usually compatible, but install "IA + IW Patch"
- **Bijin Armor** → May need patch for specific armor conflicts
- **Vanilla armor replacers** → Visual conflicts only (choose preferred textures)

**Load order tip:** Load AFTER armor replacers, BEFORE patches

**Nexus ID:** [2970](https://www.nexusmods.com/skyrimspecialedition/mods/2970)

---

### Relationship Dialogue Overhaul (RDO)
**What it does:** Expands NPC dialogue and interactions

**Conflicts with:**
- **Inigo** → Install "RDO - Inigo Patch"
- **Immersive Citizens** → INCOMPATIBLE (choose one)
- **AI Overhaul mods** → Usually incompatible

**Load order tip:** RDO loads LATE (after NPC mods, before patches)

**Nexus ID:** [1187](https://www.nexusmods.com/skyrimspecialedition/mods/1187)

---

### Frostfall
**What it does:** Hypothermia and survival mechanics

**Conflicts with:**
- **iNeed** → Install "Frostfall + iNeed Patch" (both by Chesko)
- **SunHelm** → INCOMPATIBLE (choose one survival system)
- **Campfire** → Compatible (designed to work together)

**Load order tip:** Frostfall loads AFTER environment mods

**Nexus ID:** [2160](https://www.nexusmods.com/skyrimspecialedition/mods/2160)

---

### Apachii SkyHair
**What it does:** Adds anime-style hairstyles

**Conflicts with:**
- **KS Hairdos** → Visual conflict (choose one hair pack)
- **Race mods (Bijin, etc.)** → May need compatibility patch

**Load order tip:** Hair mods load EARLY (after race mods)

**Nexus ID:** [10169](https://www.nexusmods.com/skyrimspecialedition/mods/10169)

---

## 🔥 Major Overhaul Conflicts

### Perk Overhauls (Choose ONE)
- ❌ Ordinator + Adamant
- ❌ Ordinator + Vokrii
- ❌ Adamant + Vokrii

**Solution:** Pick one. Each has its own ecosystem of patches.

---

### Combat Overhauls (Choose ONE)
- ❌ Wildcat + Valhalla Combat
- ❌ Ultimate Combat + Combat Overhaul SE
- ❌ True Directional Movement + VioLens (may conflict)

**Solution:** Read mod descriptions carefully. Some are designed to work together.

---

### Survival Mods (Choose ONE)
- ❌ Frostfall + SunHelm
- ❌ iNeed + SunHelm (partial compatibility with patches)
- ❌ Multiple needs mods (hunger, thirst, sleep)

**Solution:** One survival system is enough. Stack patches on top.

---

### Weather/ENB (Choose ONE of each)
- ❌ Obsidian Weathers + Cathedral Weathers (INCOMPATIBLE)
- ❌ True Storms + Obsidian Weathers (use "Obsidian + True Storms Patch")
- ❌ Multiple ENB presets (will cause visual glitches)

**Solution:** Pick one weather mod, one ENB. Install patches if combining weather + ENB.

---

## 🎯 Conflict Patterns

### Pattern 1: "Same Record Edit"
**Symptoms:** Two mods change the same NPC, weapon, or location.

**Example:** Mod A changes Iron Sword damage to 10. Mod B changes it to 15.

**Detection:** SkyModderAI will flag "Both mods edit record: IronSword"

**Solution:**
1. Check which mod should win (read descriptions)
2. Install a patch if available
3. Manually resolve in xEdit (advanced)

---

### Pattern 2: "Script Bloat"
**Symptoms:** Game slows down, saves grow large, scripts stack.

**Causes:**
- Too many script-heavy mods
- Poorly optimized scripts
- Scripts that never terminate

**Common culprits:**
- Quest mods with complex scripts
- Mods that add many NPCs
- Automation mods (crafting, harvesting)

**Solution:**
1. Use SkyModderAI to identify script-heavy mods
2. Remove or replace problematic mods
3. Install script optimization mods (e.g., "SSE Engine Fixes")

---

### Pattern 3: "Mesh/Texture Override"
**Symptoms:** Visual glitches, missing textures, wrong models.

**Example:** Character faces look broken after installing multiple NPC mods.

**Detection:** Visual only — game works but looks wrong.

**Solution:**
1. Check load order (later mods override earlier)
2. Use consistency patches
3. Choose one comprehensive overhaul

---

## 🛠️ Game-Specific Conflicts

### Skyrim SE/AE

#### Common Issues:
- **Anniversary Edition breaking mods** → Some SKSE mods broke after AE update
- **Downgrade enabler conflicts** → Using AE downgrade + AE mods = crash

**Solutions:**
- Check mod pages for AE compatibility
- Use "Skyrim Downgrader" carefully
- Follow r/skyrimmods "Mega Modding Thread" for current AE status

---

### Fallout 4

#### Common Issues:
- **Script extender (F4SE) version mismatches**
- **DLC requirements** → Some mods need all DLCs
- **Creation Club conflicts** → CC content can conflict with mods

**Solutions:**
- Always update F4SE after game updates
- Check mod requirements carefully
- Disable CC content if causing issues

---

### Oblivion

#### Common Issues:
- **4GB patch required** → Oblivion needs memory patch
- **LOOT less effective** → Smaller community, fewer rules
- **Old mods** → Many mods are 10+ years old

**Solutions:**
- Install OBSE + 4GB patch first
- Use Wrye Bash instead of/with MO2
- Check mod dates (prefer updated versions)

---

## 📊 Conflict Severity Levels

SkyModderAI uses these labels:

### 🔴 Critical
**Will crash your game or corrupt saves.**

**Action required:** Remove one of the conflicting mods immediately.

**Examples:**
- Two overhauls of the same system
- Mods that delete the same records
- Incompatible script extenders

---

### 🟠 High
**Major functionality broken, but game runs.**

**Action required:** Install patch or accept limited functionality.

**Examples:**
- Perk conflicts that break quest rewards
- Armor conflicts that cause missing items
- Script conflicts that prevent quests from starting

---

### 🟡 Medium
**Minor issues, mostly cosmetic.**

**Action required:** Optional fix for perfectionists.

**Examples:**
- Texture conflicts
- Minor stat differences
- Dialogue ordering issues

---

### 🟢 Low
**Theoretical conflict, unlikely to notice.**

**Action required:** None, but good to know.

**Examples:**
- Both mods edit same unused cell
- Conflicting changes to removed content
- Load order differences with no practical impact

---

## 🔍 How to Debug Conflicts

### Step 1: Identify the Problem
```
1. When does it crash? (startup, specific location, specific action)
2. What mods were recently added?
3. Does SkyModderAI flag any conflicts?
```

### Step 2: Binary Search
```
1. Disable half your mods
2. Test if problem persists
3. If fixed → problem is in disabled half
4. If not fixed → problem is in enabled half
5. Repeat until you find the culprit
```

### Step 3: Check for Patches
```
1. Search Nexus for "[Mod A] + [Mod B] patch"
2. Check mod descriptions for compatibility notes
3. Ask on mod pages or r/skyrimmods
```

### Step 4: Manual Resolution (Advanced)
```
1. Open xEdit
2. Load both conflicting mods
3. Compare conflicting records
4. Create patch that combines both (or chooses winner)
```

---

## 📚 Resources

- **[SkyModderAI Conflict Database](../data/)** — Our curated conflict rules
- **[LOOT Masterlist](https://github.com/loot/skyrim)** — Load order rules
- **[xEdit Discord](https://discord.gg/EdhRDbN)** — Patch creation help
- **[r/skyrimmods Conflict Help](https://www.reddit.com/r/skyrimmods/search/?q=conflict)** — Community support

---

## 🤝 Report a Conflict

Found a conflict we don't list? [Submit it here](https://github.com/SamsonProject/SkyModderAI/issues/new?template=conflict_report.md)

Include:
- Mod names and Nexus IDs
- Game version
- Description of the issue
- Suggested solution (if known)

---

**Remember:** When in doubt, ask the community. We've all been there! 🛡️

---

*Last updated: February 20, 2026 | Maintained by the SkyModderAI community*
