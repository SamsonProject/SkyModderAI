# Community Builds Implementation

**Date:** February 19, 2026
**Status:** ✅ Complete - Ready for Testing

---

## Overview

Replaced all hardcoded mod recommendations with a **community-driven build system**. This aligns SkyModderAI with its core philosophy: "Community-Driven Development" and "Freedom to Create."

---

## What Changed

### ❌ Removed (Hardcoded Curation)

| File | What Was Removed | Why |
|------|-----------------|-----|
| `mod_recommendations.py` | `_CURATED_TOP_PICKS` dictionary (USSEP, SkyUI, Ordinator, etc.) | Developer-curated mods ≠ community-driven |
| `list_builder.py` | Import of `_CURATED_TOP_PICKS`, fallback to curated lists | Same reason |
| `quickstart_config.py` | `script_ext`, `unofficial_patch` hardcoded links (SKSE, USSEP, etc.) | Should be discovered via community builds, not prescribed |
| `dev_panel.html` | "Popular Mods" tab with pre-checked USSEP, SkyUI, etc. | Implies developer endorsement |

### ✅ Added (Community-Driven)

| File | What Was Added | Purpose |
|------|---------------|---------|
| `migrations/add_community_builds.py` | Database schema + 20 seeded builds | Foundation for community submissions |
| `community_builds.py` | Service layer (get, submit, vote, delete) | Backend logic |
| `app.py` | API endpoints (`/api/community-builds/*`) | RESTful API |
| `dev_panel.html` | "Community Builds" tab | UI for browsing builds |
| All files | Transparency labels on seeded builds | Honest about origins |

---

## Seeded Builds (20 Total)

All seeded builds are from **popular, free, community-created modlists** (Wabbajack, Nexus Collections). None are for sale.

### Skyrim SE (11 builds)
- **Vanilla+**: Gate to Sovngarde, The Phoenix Flavour, Nordic Souls, Living Skyrim, True North
- **Hardcore**: Wildlander, Do Not Go Gentle, Legends of the Frost
- **Power Fantasy**: Lost Legacy, Apostasy, Path of the Dovahkiin

### Fallout 4 (4 builds)
- Magnum Opus, FUSION, Wasteland Reborn, Life in the Ruins

### Fallout New Vegas (2 builds)
- Viva New Vegas, Uranium Fever

### Other (3 builds)
- Oblivion Enhanced, Starfield Melius, Skyrim VR FUS

### Transparency
All seeded builds have:
- `is_seed = 1` flag
- `seed_note`: "Seeded from popular Wabbajack modlist - will be replaced by community submissions"

---

## API Endpoints

### GET `/api/community-builds`
Get builds with filters.

**Query Params:**
- `game`: skyrimse, fallout4, etc.
- `playstyle`: vanilla_plus, hardcore, etc.
- `performance_tier`: low, mid, high
- `limit`: 1-100 (default 50)
- `include_seed`: true/false (default true)

**Response:**
```json
{
  "success": true,
  "builds": [...],
  "count": 20
}
```

### GET `/api/community-builds/:id`
Get a specific build.

### POST `/api/community-builds`
Submit a new build (requires auth).

**Body:**
```json
{
  "game": "skyrimse",
  "name": "My Vanilla+ Build",
  "description": "Description here",
  "mod_list": "USSEP.esp\nSkyUI.esp\n...",
  "author": "Optional",
  "playstyle_tags": ["vanilla_plus", "stable"],
  "performance_tier": "mid"
}
```

### POST `/api/community-builds/:id/vote`
Vote on a build (requires auth).

**Body:**
```json
{ "vote": 1 }  // 1 = upvote, -1 = downvote
```

### DELETE `/api/community-builds/:id`
Delete a build (author or admin only).

### GET `/api/community-builds/stats`
Get statistics.

---

## Database Schema

```sql
CREATE TABLE community_builds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    author TEXT DEFAULT 'Community',
    source TEXT DEFAULT 'Community',
    source_url TEXT,
    wiki_url TEXT,
    mod_count INTEGER,
    playstyle_tags TEXT,  -- JSON array
    performance_tier TEXT DEFAULT 'mid',
    upvotes INTEGER DEFAULT 0,
    downvotes INTEGER DEFAULT 0,
    is_seed INTEGER DEFAULT 0,
    seed_note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_community_builds_game ON community_builds(game);
CREATE INDEX idx_community_builds_tags ON community_builds(playstyle_tags);

CREATE TABLE community_build_votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    build_id INTEGER NOT NULL,
    user_email TEXT NOT NULL,
    vote INTEGER NOT NULL,  -- 1 or -1
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (build_id) REFERENCES community_builds(id),
    UNIQUE (build_id, user_email)
);
```

---

## UI Changes

### Before (Dev Panel)
```
🔍 Search | 📋 Paste | 📁 Import | ⭐ Popular Mods
                                                      ↓
                                        [ ] USSEP.esp (checked)
                                        [ ] SkyUI.esp
                                        [ ] Ordinator.esp
                                        ...
```

### After (Dev Panel)
```
🔍 Search | 📋 Paste | 📁 Import | 🔥 Community Builds
                                                      ↓
                                        [Select Game: Skyrim SE ▼]

                                        Gate to Sovngarde
                                        1700+ mods • vanilla_plus • mid
                                        👍 0  👎 0  🌱 Seed
                                        [📄 Source] [📖 Wiki] [➕ Load Build]
```

---

## Philosophy Alignment

| Principle | Before | After |
|-----------|--------|-------|
| **Community-Driven** | ❌ Dev-curated mods | ✅ User-submitted builds |
| **Link Aggregator** | ⚠️ Some hardcoded | ✅ All links dynamic |
| **Freedom to Create** | ❌ Preset lists | ✅ Community builds |
| **Transparency** | ⚠️ Hidden curation | ✅ Labeled seeds |
| **Self-Improving** | ❌ Static | ✅ Vote-based evolution |

---

## Migration Instructions

1. **Run the migration:**
   ```bash
   cd /media/chris/Samsung-T7/SkyModderAI/SkyModderAI
   python3 migrations/add_community_builds.py
   ```

2. **Expected output:**
   ```
   ✓ Created community_builds table with 20 seed builds
     Note: All seed builds are marked with is_seed=1 and will be replaced
     as community members submit their own builds.
   ```

3. **Test the API:**
   ```bash
   # Get all builds
   curl http://localhost:5000/api/community-builds

   # Get Skyrim SE builds
   curl http://localhost:5000/api/community-builds?game=skyrimse

   # Get stats
   curl http://localhost:5000/api/community-builds/stats
   ```

4. **Test the UI:**
   - Open http://localhost:5000
   - Go to "Mod Authors" tab (🛠️)
   - Click "Community Builds" tab
   - Select "Skyrim SE" from dropdown
   - See seeded builds

---

## Next Steps

### Immediate (This Week)
- [ ] Run migration
- [ ] Test API endpoints
- [ ] Test UI in dev panel
- [ ] Fix any bugs

### Short-Term (Week 2-3)
- [ ] Add "Submit Build" form UI
- [ ] Add vote buttons (👍/👎) in UI
- [ ] Update "Sample" button on main page to load community builds
- [ ] Add community builds page (`/community-builds`)

### Medium-Term (Month 1-2)
- [ ] Implement telemetry collection (opt-in)
- [ ] Add build cloning (users can fork builds)
- [ ] Add build comments/discussion
- [ ] Add author profiles

### Long-Term (Month 3-6)
- [ ] Phase out seeded builds as community submissions grow
- [ ] Add build verification (users confirm builds work)
- [ ] Add build updates (authors can update builds)
- [ ] Add build analytics (most popular, trending)

---

## Red Team Analysis (Self-Critique)

### What Could Go Wrong

1. **Empty Room Problem**: No community submissions → users see only seeds → feels static
   - **Mitigation**: Transparent labels, active outreach for submissions

2. **Vote Manipulation**: Alt accounts upvote own builds
   - **Mitigation**: Email verification, session age limits, pattern detection

3. **Low Quality Builds**: Spam, broken lists, outdated mods
   - **Mitigation**: Community flagging, downvotes, moderation tools

4. **Legal Issues**: Mod authors object to inclusion
   - **Mitigation**: Link-only (no redistribution), DMCA process, opt-out

5. **Philosophy Hypocrisy**: Seeds are still top-down curation
   - **Mitigation**: Transparent labels, sunset clause, active replacement

---

## Success Metrics

| Metric | Target (Month 1) | Target (Month 3) |
|--------|-----------------|------------------|
| Community builds submitted | 20+ | 100+ |
| Builds with 10+ votes | 5+ | 30+ |
| Seed builds replaced | 0% | 50% |
| User submissions (non-seed) | 5+ | 50+ |

---

## Files Changed

```
migrations/add_community_builds.py    (NEW - 400 lines)
community_builds.py                   (NEW - 420 lines)
app.py                                (MODIFIED - +230 lines)
mod_recommendations.py                (MODIFIED - removed _CURATED_TOP_PICKS)
list_builder.py                       (MODIFIED - removed hardcoded lists)
quickstart_config.py                  (MODIFIED - removed mod links)
templates/includes/dev_panel.html     (MODIFIED - replaced Popular Mods tab)
```

---

**Built by modders, for modders.**
**Community-driven, not developer-curated.**
