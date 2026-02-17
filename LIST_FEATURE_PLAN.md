# Bespoke List Builder Architecture

SkyModderAI's list builder is not a random generator. It is a bespoke architect for your game. By combining user preferences with our intimate database of compatibility, we generate stable, tailored foundations for any playthrough.

---

## Core Philosophy

1.  **Bespoke Generation**: Every list is unique to the user's specs and stylistic desires.
2.  **Stability First**: We don't just pick popular mods; we pick mods that work *together*.
3.  **Seamless Handoff**: The list isn't just text; it's a launchpad into the Analysis and Floating Portal workflows.

## The Engine

### 1. Preference Matrix
We categorize mods not just by type, but by "vibe" and "weight":
- **Environment**: Dark Fantasy, High Fantasy, Vanilla+, Horror.
- **Gameplay**: Souls-like, SimonRim, EnaiRim, Requiem-based.
- **Visuals**: Performance (low VRAM), Balanced, Screenarchery (4090+).

### 2. AI Architect
The AI doesn't just list mods; it composes a *setup*.
- **Base Layer**: Essential fixes and tools (SKSE, Address Library, USSEP).
- **Core Layer**: The big overhauls defined by the user's gameplay choice.
- **Visual Layer**: Textures and lighting that match the user's VRAM constraints.
- **Conflict Resolution**: The builder pre-emptively avoids known incompatible pairs from the `conflict_stats` bin.

### 3. Integration
- **Auto-Analyze**: Generated lists are immediately fed into the Analyzer to verify integrity.
- **Smart Linking**: Every mod in the generated list is hyperlinked to our Floating Portal system for instant Nexus browsing.

## Data Model

### User Preferences
```json
{
  "game": "skyrimse",
  "style": "dark_fantasy",
  "combat": "modern_action",
  "specs": {
    "gpu": "RTX 3080",
    "vram": "10GB"
  }
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
