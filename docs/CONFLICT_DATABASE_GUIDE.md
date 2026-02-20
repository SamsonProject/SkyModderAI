# 📝 Contributing to the Conflict Database

**Help make SkyModderAI smarter! Add conflict reports, patches, and load order rules.**

---

## 🎯 What We Need

### High Priority Conflicts

We're especially looking for reports on:

- **Popular mods** (10k+ downloads on Nexus)
- **Recent mods** (released/updated in last 6 months)
- **Overhaul mods** (perk trees, combat, weather, survival)
- **Mods without patches** that should have them

### Example High-Value Reports

```
✅ "Ordinator 9.30 + Vokrii 2.5 crash on startup"
✅ "SunHelm 3.0 + iNeed 1.30 food mechanics conflict"
✅ "New weather mod X + True Storms incompatibility"

❌ "Obscure mod A + obscure mod B" (low impact)
❌ "Mod from 2015, no longer used" (outdated)
```

---

## 📋 How to Report a Conflict

### Step 1: Verify the Conflict

Before reporting:

1. **Test both mods individually** - Confirm each works alone
2. **Test together** - Confirm the conflict occurs
3. **Document what happens**:
   - Crash to desktop (CTD)?
   - Broken functionality?
   - Visual glitches?
   - Script errors?

### Step 2: Gather Information

Collect:

- **Mod names** (exact names from Nexus)
- **Nexus IDs** (from mod page URLs)
- **Mod versions** (check mod pages or mod manager)
- **Game version** (Skyrim SE 1.6.640, etc.)
- **Load order** (export from your mod manager)
- **Error messages** (screenshots, logs)

### Step 3: Check Existing Reports

Search before submitting:

- [GitHub Issues](https://github.com/SamsonProject/SkyModderAI/issues) - Search for mod names
- [data/example_conflict_database.json](data/example_conflict_database.json) - Check existing entries
- Mod pages - Authors often list incompatibilities

### Step 4: Submit Your Report

**Option A: GitHub Issue (Recommended)**

1. Go to [New Issue](https://github.com/SamsonProject/SkyModderAI/issues/new)
2. Select "Conflict Report" template
3. Fill in all fields
4. Submit!

**Option B: Direct PR (Advanced)**

1. Fork the repository
2. Edit `data/example_conflict_database.json`
3. Add your conflict entry (see format below)
4. Submit PR

---

## 📝 Conflict Entry Format

### JSON Structure

```json
{
  "id": "SKYRIM_XXX",
  "mod_a": {
    "name": "Exact Mod Name",
    "nexus_id": 12345,
    "versions_affected": ["1.0.0", "1.1.0", "all"]
  },
  "mod_b": {
    "name": "Exact Mod Name",
    "nexus_id": 67890,
    "versions_affected": ["all"]
  },
  "severity": "critical|high|medium|low|info",
  "type": "incompatible|compatibility|override|load_order",
  "description": "Clear description of what goes wrong",
  "solution": {
    "type": "patch|choose_one|load_order|workaround",
    "patch_name": "Name of Patch Mod",
    "patch_nexus_id": 11111,
    "load_order": "Load order instructions",
    "recommendation": "Which mod to choose or workaround",
    "note": "Additional context"
  },
  "sources": [
    "https://link-to-evidence-1",
    "Community report #1234",
    "Mod author statement"
  ]
}
```

### Severity Levels

| Level | Meaning | Example |
|-------|---------|---------|
| **critical** | Game-breaking, crashes, save corruption | Two perk overhauls |
| **high** | Major functionality broken | Quests won't start |
| **medium** | Minor issues, workarounds exist | Visual glitches |
| **low** | Cosmetic, barely noticeable | Wrong icon |
| **info** | Good to know, no action needed | Load order tip |

### Conflict Types

| Type | Meaning |
|------|---------|
| **incompatible** | Cannot use together at all |
| **compatibility** | Can use together with patch |
| **override** | Both edit same record, choose winner |
| **load_order** | Order matters for functionality |

---

## 🛠️ Example Entries

### Example 1: Incompatible Mods

```json
{
  "id": "SKYRIM_100",
  "mod_a": {
    "name": "Vokrii - Minimalistic Perk Overhaul",
    "nexus_id": 26176,
    "versions_affected": ["all"]
  },
  "mod_b": {
    "name": "Adamant - A Perk Overhaul",
    "nexus_id": 30191,
    "versions_affected": ["all"]
  },
  "severity": "critical",
  "type": "incompatible",
  "description": "Both mods completely replace the perk system. Using both will cause crashes and broken perks.",
  "solution": {
    "type": "choose_one",
    "recommendation": "Choose ONE perk overhaul. They cannot be used together.",
    "alternatives": [
      "Vokrii for streamlined, vanilla-friendly experience",
      "Adamant for more complex, RPG-focused gameplay"
    ]
  },
  "sources": [
    "Mod author statements on both mod pages",
    "Community consensus"
  ]
}
```

### Example 2: Patch Available

```json
{
  "id": "SKYRIM_101",
  "mod_a": {
    "name": "Immersive Armors",
    "nexus_id": 2970,
    "versions_affected": ["all"]
  },
  "mod_b": {
    "name": "Immersive Weapons",
    "nexus_id": 2764,
    "versions_affected": ["all"]
  },
  "severity": "low",
  "type": "compatibility",
  "description": "Both mods add items to leveled lists. Generally compatible but may cause minor distribution issues.",
  "solution": {
    "type": "patch",
    "patch_name": "Immersive Armors and Weapons Compatibility Patch",
    "patch_nexus_id": 33894,
    "load_order": "Load patch AFTER both mods"
  },
  "sources": [
    "https://www.nexusmods.com/skyrimspecialedition/mods/33894"
  ]
}
```

### Example 3: Load Order Rule

```json
{
  "id": "LO_050",
  "mod": "Unofficial Skyrim Special Edition Patch",
  "nexus_id": 266,
  "rule": "load_early",
  "position": "after_official_dlc",
  "reason": "USSEP is a base patch that should be overridden by other mods",
  "sources": [
    "LOOT masterlist",
    "USSEP mod page"
  ]
}
```

---

## 🔍 Research Tips

### Finding Conflicts

1. **Read mod descriptions** - Authors often list incompatibilities
2. **Check mod posts** - Look for "Issues" or "Known Bugs" sections
3. **Search Reddit** - r/skyrimmods search for mod names + "conflict"
4. **Check Nexus comments** - Users report issues there
5. **Test yourself** - Install both mods, see what breaks

### Verifying Solutions

1. **Official patches** - Check mod author's files tab
2. **Community patches** - Search Nexus for "[Mod A] + [Mod B] patch"
3. **Load order tests** - Try different orders, see what works
4. **Ask authors** - Many mod authors are active on Discord/Nexus

### Good Sources

- **Mod pages** - Official incompatibility lists
- **LOOT masterlist** - Load order rules
- **xEdit conflict reports** - Technical conflict data
- **Community Discord servers** - Real-time help
- **Reddit megathreads** - r/skyrimmods monthly conflict threads

---

## 📊 Quality Guidelines

### What Makes a Good Report

✅ **Specific**: "Mod A v1.2 + Mod B v2.0 crash on cell load"
✅ **Verifiable**: Links to mod pages, screenshots of errors
✅ **Actionable**: Includes solution or workaround
✅ **Complete**: All fields filled, sources cited

### What to Avoid

❌ **Vague**: "These mods don't work"
❌ **Unverified**: "I heard these conflict"
❌ **No solution**: Reports problem without fix
❌ **Incomplete**: Missing mod versions, Nexus IDs

---

## 🎯 Priority Areas

### Skyrim SE/AE

**High Priority:**
- Anniversary Edition compatibility
- Next-gen update conflicts
- Popular mods (10k+ downloads)
- Recent releases (last 6 months)

**Specific Needs:**
- Creation Club conflict reports
- AE downgrade enabler issues
- Script extender (SKSE) mod compatibility

### Fallout 4

**High Priority:**
- Next-Gen update (2024) conflicts
- Creation Club compatibility
- F4SE mod issues

### Oblivion

**High Priority:**
- 4GB patch compatibility
- OBSE mod conflicts
- Old mod compatibility with modern tools

---

## 🏆 Recognition

Contributors are credited in:

- **README.md** - Top contributors section
- **CHANGELOG** - When conflict database is updated
- **Discord** - Contributor role for active helpers

**Example:**
```markdown
### Conflict Database Contributors
- @Modder123 - 50+ conflict reports
- @SkyrimVet - Ordinator compatibility research
- @FalloutFan - Fallout 4 Next-Gen testing
```

---

## ❓ FAQ

**Q: Do I need to be a technical expert?**

A: No! If you can describe what broke and which mods were involved, that's valuable data.

**Q: What if I don't know the solution?**

A: Report anyway! We can research solutions later. Knowing there's a problem is half the battle.

**Q: Can I report conflicts for mods I don't use?**

A: Yes! If you're helping test or research, all reports are welcome.

**Q: How long until my report is added?**

A: Usually within a week. Complex conflicts may take longer to verify.

**Q: What if my report is wrong?**

A: No worries! We'll discuss in the issue and update if needed. Good faith efforts are always appreciated.

---

## 🤝 Get Help

**Stuck?** Ask for help:

- **Discord:** [Join our server](https://discord.gg/YOUR_INVITE)
- **GitHub:** Comment on existing issues
- **Reddit:** r/skyrimmods, r/falloutmods

**Questions about specific conflicts?** Tag maintainers:

- `@skymodderai-team` - General questions
- `@conflict-researchers` - Research help
- `@database-maintainers` - Format questions

---

**Thank you for helping make SkyModderAI better for everyone!** 🛡️

Every conflict report saves another modder from a broken save game.

*Last updated: February 20, 2026*
