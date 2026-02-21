# SkyModderAI — What We Are (And What We're Not)

**Date**: February 17, 2026
**Architecture Decision**: Focused specialization over comprehensive database

---

## ✅ What SkyModderAI IS

### 1. **Mod Compatibility Engine**
**Core competency:** Detecting conflicts, missing requirements, load order issues

**Data we store:**
- Mod metadata (name, version, requirements, incompatibilities)
- LOOT masterlist data (rules, load order, patches)
- User conflict reports (anonymized, hashed mod names)
- Compatibility scores (learned from user sessions)

**Data we DON'T store:**
- Quest walkthroughs
- Item databases
- NPC information
- Game mechanics guides

**Why:** LOOT already has mod rules. We enhance with AI + community learning.

---

### 2. **Link Aggregator**
**Core competency:** Connecting users to existing high-quality resources

**We link to:**
- **Nexus Mods** — Mod downloads, descriptions, requirements
- **UESP** — Game mechanics, quests, items, NPCs
- **LOOT** — Load order rules, cleaning guides
- **xEdit docs** — Mod cleaning, conflict resolution
- **Community wikis** — Game-specific knowledge
- **YouTube** — Video guides, tutorials

**We DON'T duplicate:**
- Walkthroughs (UESP has better)
- Item databases (wikis have better)
- Mod descriptions (Nexus has better)
- Video tutorials (YouTube has better)

**Why:** Linking is free, always up-to-date, and respects existing creators.

---

### 3. **Specialized Data Center**
**Core competency:** Mod interaction data that doesn't exist elsewhere

**Data we store:**
- Mod pair compatibility (learned from user sessions)
- Conflict patterns (which mods conflict together)
- Performance correlations (mod count → FPS/stability)
- Load order effectiveness (what order works best)

**Data we DON'T store:**
- Quest data
- Item stats
- Character builds
- Screenshot galleries

**Why:** This data is UNIQUE to what we do. Nobody else collects mod interaction telemetry.

---

### 4. **AI Training Platform (OpenCLAW)**
**Core competency:** Learning from anonymized user sessions to improve recommendations

**Data we collect (opt-in, anonymized):**
- Mod lists (hashed names)
- Conflict reports
- Performance metrics (FPS, crashes, stutter)
- User feedback (what worked, what didn't)

**Data we DON'T collect:**
- Save games
- Personal information
- System specs (only buckets: "8GB RAM", "RTX 3060")
- Raw input data

**Why:** This is our competitive advantage. Community-owned AI trained by modders.

---

## ❌ What SkyModderAI IS NOT

### NOT a Bethesda Game Database

**Don't store:**
- Quest walkthroughs (`bleak_falls_barrow.json` type data)
- Item databases (weapons, armor, potions)
- NPC information (locations, schedules, quests)
- Location guides (dungeons, cities, points of interest)
- Game mechanics tutorials (crafting, combat, magic)

**Why:**
- UESP does this better (https://en.uesp.net/wiki/Skyrim:Skyrim)
- Fandom wikis do this better (https://elderscrolls.fandom.com)
- This data is static, doesn't need our AI
- Maintenance burden (game updates break this)
- Legal gray area (Bethesda IP)

**What to do instead:**
- Link to UESP for quest info
- Link to wikis for item databases
- Link to YouTube for tutorials

---

### NOT a Content Repository

**Don't store:**
- Modding tutorials (how to install mods)
- Build guides (character builds, playstyles)
- Screenshot galleries
- Lore discussions
- Mod reviews (long-form)

**Why:**
- Nexus has mod descriptions
- Reddit has discussions (r/skyrimmods)
- YouTube has tutorials
- Blogs have build guides

**What to do instead:**
- Link to Nexus mod pages
- Link to Reddit threads
- Link to YouTube videos
- Let community post links in comments

---

### NOT a Search Engine Replacement

**Don't build:**
- General web search (Google does this)
- Mod search beyond our database (Nexus search does this)
- Academic search (we're not a library)

**Why:**
- Google indexes everything
- Nexus has mod search
- We're specialized, not general

**What to do instead:**
- Search OUR data (mod conflicts, compatibility)
- Link to Google/Nexus for broader searches
- Focus on what we're good at

---

## 📊 Data Architecture: Keep vs. Link

### KEEP (Store in our database)

| Data Type | Why | Example |
|-----------|-----|---------|
| Mod metadata | Core to conflict detection | `USSEP.esp`, version, requirements |
| LOOT rules | Load order optimization | "SkyUI must load after USSEP" |
| User conflicts | Learning data | "Mod A + Mod B = crash" (hashed) |
| Performance data | AI training | "150 mods = 45 FPS avg" (anonymized) |
| Compatibility scores | Unique value | "USSEP + Ordinator: 0.95 compatible" |
| Patch availability | Practical utility | "Use Ordinator + Alternate Start patch" |

### LINK (Reference external sources)

| Data Type | Link To | Why |
|-----------|---------|-----|
| Quest walkthroughs | UESP | They maintain it better |
| Item databases | Wikis | More comprehensive |
| Mod descriptions | Nexus | Official source |
| Video tutorials | YouTube | Better format |
| Mod reviews | Nexus/Reddit | Community-driven |
| Build guides | Reddit/Blogs | More creative freedom |
| Lore discussions | Wikis/Reddit | Richer context |

---

## 🗑️ Files to Remove/Convert

### Remove (Not our focus)

- `bleak_falls_barrow.json` — Quest walkthrough data
- Any `*_walkthrough.json` files
- Any `quests/` directory
- Any `items/` directory
- Any `npcs/` directory
- Any `locations/` directory

### Keep (Core functionality)

- `*_mod_database.json` — Mod metadata
- `game_versions.json` — Game version info
- `loot/` — LOOT masterlist data
- `samson_fuel/` — Dependency graph data
- `openclaw_learning/` — AI training data (future)

---

## 🔗 Link Architecture

Instead of storing data, we LINK to it:

```javascript
// ❌ Bad: Storing walkthrough data
{
  "quest": "bleak_falls_barrow",
  "steps": [...]
}

// ✅ Good: Linking to UESP
{
  "quest": "bleak_falls_barrow",
  "uesp_link": "https://en.uesp.net/wiki/Skyrim:Bleak_Falls_Barrow_(quest)",
  "mod_conflicts": [...]  // This IS our data
}
```

---

## 🎯 Competitive Advantage

**What makes us unique:**

1. **LOOT + AI** — Automated conflict detection + learned patterns
2. **Community telemetry** — Real-world mod interaction data
3. **Specialized focus** — Mod compatibility, not general game info
4. **Link aggregation** — Best resources, properly organized
5. **OpenCLAW** — Self-improving AI trained by community

**What makes us generic (avoid):**

1. ❌ Quest databases (UESP does this)
2. ❌ Item wikis (Fandom does this)
3. ❌ Mod hosting (Nexus does this)
4. ❌ Video tutorials (YouTube does this)
5. ❌ General search (Google does this)

---

## 📝 Action Items

### Immediate
- [ ] Remove `bleak_falls_barrow.json`
- [ ] Remove any other walkthrough/quest data
- [ ] Document what data types we actually store
- [ ] Update database schema comments

### Short-term
- [ ] Add UESP links to quest references
- [ ] Add Nexus links to mod references
- [ ] Build "resource linker" (auto-link to best external source)
- [ ] Create "link database" (curated list of best external resources)

### Long-term
- [ ] Build OpenCLAW learning pipeline
- [ ] Collect anonymized mod interaction data
- [ ] Train compatibility models
- [ ] Become THE source for mod compatibility data

---

## 💡 Philosophy

> **"We don't store what others already maintain better.**
> **We specialize in what ONLY we can do."**

**What only we can do:**
- Collect mod interaction telemetry
- Train AI on real-world conflicts
- Predict compatibility before installation
- Optimize load orders with ML

**What others do better:**
- Quest walkthroughs → UESP
- Item databases → Wikis
- Mod hosting → Nexus
- Video guides → YouTube

**Our job:** Link to the best, specialize in the rest.

---

**Built by modders, for modders.**
**Focused, not comprehensive.**
**Specialized, not generic.**
