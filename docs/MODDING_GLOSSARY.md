# 📖 Modding Glossary

**New to modding? Confused by ESP vs ESM? This guide explains the terms you'll see in SkyModderAI.**

---

## 📦 File Types

### ESP (Elder Scrolls Plugin)
**What it is:** A mod file that changes the game world.

**What you need to know:**
- Most mods are ESPs
- Can be loaded or unloaded freely
- Limited to 254 ESPs in your load order (the "plugin limit")

**Example:** `SkyUI.esp`, `USSEP.esp`

---

### ESM (Elder Scrolls Master)
**What it is:** A master file that other mods can depend on.

**What you need to know:**
- Loads BEFORE regular ESPs
- Usually official DLC or large framework mods
- Doesn't count toward the 254 plugin limit

**Example:** `Update.esm`, `Dawnguard.esm`, `Falskaar.esm`

---

### ESL (Elder Scrolls Light)
**What it is:** A "light" plugin that doesn't count toward the limit.

**What you need to know:**
- Perfect for small mods
- Up to 4096 ESL-flagged mods can be active
- Great for avoiding the plugin cap

**Example:** `Unofficial Skyrim Special Edition Patch.esp` (ESL-flagged)

---

### ESPFE (ESP Flagged as ESL)
**What it is:** An ESP file with the ESL flag set.

**What you need to know:**
- Acts like an ESL (doesn't count toward limit)
- Shows as `.esp` in your mod manager
- Created in xEdit by checking "ESL Flagged"

---

## 🎯 Load Order Concepts

### Load Order
**What it is:** The sequence in which mods load.

**Why it matters:** Later mods override earlier mods. If two mods change the same thing, the one that loads **last** wins.

**Example:**
```
1. Unofficial Skyrim Patch.esp    ← Loads first
2. Immersive Armors.esp          ← Overrides patch
3. Armor Patch.esp               ← Overrides both (final say)
```

---

### Master File
**What it is:** A file that other mods require to work.

**How to spot it:** In your mod manager, masters are listed under "Requirements" or shown with a special icon.

**Rule:** Masters must load BEFORE the mods that depend on them.

---

### Dirty Edit
**What it is:** Unintended changes in a mod (usually accidental).

**Common types:**
- **ITM (Identical To Master):** Record that's the same as vanilla — useless, can cause issues
- **UDR (Undeleted Reference):** Deleted object that still exists — can crash your game
- **Deleted NavMesh:** Navigation data that wasn't properly removed

**Fix:** Use xEdit to clean dirty mods (or download "Cleaned" versions from Nexus).

---

### Conflict Types

#### 1. **Override Conflict** (Most Common)
**What:** Two mods change the same thing (e.g., same NPC, same weapon).

**Solution:** Use a patch mod, or manually decide which mod should win with your mod manager.

**Example:** Mod A makes swords do 10 damage. Mod B makes them do 20 damage. If Mod B loads last, swords do 20 damage.

---

#### 2. **Compatibility Conflict** (Dangerous)
**What:** Two mods are fundamentally incompatible and will crash or break your game.

**Solution:** Don't use both mods together, or install a compatibility patch.

**Example:** Two overhauls that both completely rewrite the perk system (Ordinator + Apocalypse Overhaul).

---

#### 3. **Visual Conflict** (Cosmetic)
**What:** Two mods change the same visual element (e.g., texture, mesh).

**Solution:** Choose which one you prefer, or find a merged texture pack.

**Example:** Two different ENB presets, or two weather mods.

---

## 🔧 Mod Manager Terms

### MO2 (Mod Organizer 2)
**What it is:** A mod manager that uses a virtual file system.

**Pros:**
- Doesn't modify your game folder
- Easy to create profiles (different mod setups)
- Best for advanced modders

**SkyModderAI Integration:** Export mod list via Tools → Copy to clipboard → Active mods

---

### Vortex
**What it is:** Nexus Mods' official mod manager.

**Pros:**
- User-friendly interface
- Built-in Nexus integration
- Good for beginners

**SkyModderAI Integration:** Plugins → Export → Copy as text

---

### Wabbajack
**What it is:** Automated modlist installer.

**What it does:** Downloads and configures hundreds of mods automatically based on curated lists.

**SkyModderAI Integration:** Import `.wabbajack` files to analyze before building

---

### LOOT (Load Order Optimization Tool)
**What it is:** Automatically sorts your load order.

**What it does:** Uses community-maintained rules to put mods in the optimal order.

**SkyModderAI uses LOOT's data** — so you get the same smart sorting, plus extra conflict detection.

---

## 🛠️ Tools You'll Encounter

### xEdit (SSEEdit, FO4Edit, etc.)
**What it is:** Advanced mod editing and conflict detection tool.

**Use it for:**
- Cleaning dirty mods
- Creating patches
- Seeing exactly what mods change

**SkyModderAI connection:** Our conflict detection is inspired by xEdit's approach.

---

### FNIS / Nemesis
**What it is:** Animation behavior generator.

**When you need it:** When using animation mods (new combat moves, emotes, etc.).

**Warning:** Must run FNIS/Nemesis AFTER installing animation mods, or your game will crash.

---

### SKSE (Skyrim Script Extender)
**What it is:** Extends Skyrim's scripting capabilities.

**Required by:** Many advanced mods (SkyUI, Ordinator, etc.).

**Note:** Must install SKSE **before** mods that require it.

---

## 📊 Numbers That Matter

| Number | What It Means |
|--------|---------------|
| **254** | Maximum ESP/ESM plugins (plugin limit) |
| **4096** | Maximum ESL + ESPFE plugins |
| **~300** | Recommended practical limit for stability |
| **5** | Seconds SkyModderAI takes to analyze 500 mods |

---

## 🎓 Common Beginner Mistakes

### ❌ "More mods = better game"
**Reality:** 200 well-chosen mods beat 500 random ones. Quality > quantity.

### ❌ "I don't need patches"
**Reality:** Patches make mods work together. Always check for compatibility patches.

### ❌ "LOOT sorted it, so it's perfect"
**Reality:** LOOT sorts load order, but doesn't fix incompatibilities. Use SkyModderAI for that.

### ❌ "I'll just install and play"
**Reality:** Test after every 10-20 mods. Catching bugs early saves hours.

---

## 🆘 When Things Go Wrong

### Game won't start
1. Disable half your mods
2. If it works, the problem is in the disabled half
3. Repeat until you find the culprit

### Crashes at specific location
1. It's probably a script or cell edit conflict
2. Use SkyModderAI to find mods that edit that area
3. Check for patches

### Saves are corrupted
1. **Always back up saves** before adding/removing mods
2. Mid-playthrough mod changes can break saves
3. Some mods are "safe to remove" — check mod descriptions

---

## 📚 Learn More

- **[UESP Modding Guide](https://en.uesp.net/wiki/Modding)** — Technical reference
- **[Nexus Mods Learning Center](https://wiki.nexusmods.com/)** — Beginner tutorials
- **[r/skyrimmods Wiki](https://www.reddit.com/r/skyrimmods/wiki/index)** — Community knowledge
- **[Modding Wiki](https://modding.wiki/)** — Comprehensive guides

---

**Still confused?** Ask on our [Discord](https://discord.gg/YOUR_INVITE) or r/skyrimmods. No question is too basic!

---

*Last updated: February 20, 2026*
