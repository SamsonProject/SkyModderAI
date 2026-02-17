# List Builder Feature — Roadmap

SkyModderAI's list builder lets users define preferences and get AI-generated mod lists, with deep Nexus/MO2/Vortex integration.

---

## Phase 1: Foundation (Current)

### Standard preferences (all users)
- **Environment**: Dark fantasy, vanilla+, high fantasy, survival, horror, sci-fi
- **Hair/character**: KS Hairdos, Apachii, vanilla only, HDT-SMP, etc.
- **Body**: CBBE, UNP, vanilla
- **Combat**: Vanilla, Souls-like, action, immersive
- **Graphics**: Performance, balanced, ultra, ENB preference
- **Content**: Quest-heavy, new lands, vanilla+, minimal
- **Stability**: Maximum stability, experimental OK

### UI
- New "Build a List" tab
- Preference toggles/selects
- Generate button → standard list (LOOT-based recommendations)

### Backend
- `list_preferences` schema
- `GET/POST /api/list-preferences` — save/load (Pro: cloud, Free: localStorage)
- `POST /api/build-list` — generate list from preferences + game

---

## Phase 2: AI List Builder (Pro)

### Chat composition
- Chat with AI: "I want dark fantasy, KS Hairdos, CBBE, performance focus"
- AI composes list iteratively
- Pretty report: HTML/PDF with mod cards, screenshots, install order

### Pro: Multiple setups
- AI generates N combinations (e.g. 3–5) based on preferences
- "Setup A: Dark fantasy + performance" vs "Setup B: Dark fantasy + ultra"
- Each setup = full mod list with rationale

### Cost controls
- Per-user AI token budget (e.g. 50k tokens/month Pro)
- List generation capped (e.g. max 5 setups per request)
- User approval required for expensive operations (e.g. image generation)

---

## Phase 3: Screenshots & Nexus Integration

### Nexus API
- GraphQL/REST: mod metadata, images, endorsements
- Mod cards show real screenshots from Nexus
- Fallback: mod-placeholder.svg when no image

### One-click install
- **Vortex**: `nxm://` or `vortex://` links — opens Vortex, starts download
- **MO2**: NXM links work if MO2 is default handler
- **Nexus**: Direct "Download with manager" links (requires Nexus login)

### Wabbajack-style
- Export list as `.txt` (plugins.txt format) — user imports to MO2/Vortex
- Future: Generate Wabbajack-compatible manifest (complex — requires mod hashes, file IDs)

---

## Phase 4: Future / Experimental

### Rendered projections
- **Idea**: AI generates text description → image model renders "what your game could look like"
- **Cost**: High (DALL-E, Midjourney API, etc.)
- **Controls**: Pro-only, opt-in, strict cap (e.g. 3 images/month), user confirms before each

### Intimate mod manager linking
- Detect MO2/Vortex install (browser can't; would need desktop companion)
- Alternative: Browser extension that talks to local MO2/Vortex
- Or: Export list → user pastes/imports manually (current approach)

---

## Data Model

### List preferences (stored per user or localStorage)
```json
{
  "game": "skyrimse",
  "environment": "dark_fantasy",
  "hair": "ks_hairdos",
  "body": "cbbe",
  "combat": "souls_like",
  "graphics": "balanced",
  "content": "quest_heavy",
  "stability": "max"
}
```

### Generated list response
```json
{
  "mods": [{"name": "...", "reason": "...", "nexus_url": "...", "image_url": "..."}],
  "setups": [  // Pro only
    {"name": "Dark fantasy performance", "mods": [...], "rationale": "..."},
    {"name": "Dark fantasy ultra", "mods": [...], "rationale": "..."}
  ]
}
```

---

## Implementation Order

1. ✅ **list_builder.py** — preferences schema, list generation from LOOT + mod_recommendations
2. ✅ **UI** — Build a List tab, preference form
3. ✅ **API** — /api/list-preferences/options, /api/build-list
4. ✅ **Pro** — AI multiple setups (pro_setups: true in request)
5. **Nexus** — API integration for images (when key available)
6. **Links** — Vortex/MO2 NXM links (research exact format)
7. **Screenshots** — Fetch from Nexus mod pages or API
8. **Rendered projections** — Opt-in, cost-capped, user approval
