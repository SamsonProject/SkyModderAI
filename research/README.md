# Research — Self-Improving Skyrim Modding System

**Purpose:** Collect, analyze, and learn from all data flowing through ModCheck—without charging users, slowing requests, or compromising privacy. Use existing corporate infrastructure (free tiers, research grants, partnerships) to run periodic analysis that improves the site, debugging, mod efficiency, and eventually pushes toward live modded Skyrim.

---

## Vision

1. **Data collection** — All structural data in and out: load orders, conflict patterns, search queries, AI chat context, community posts, error rates, resolution success.
2. **Corporate power structure** — Leverage cloud free tiers, academic/research credits, and partnerships instead of charging users or adding latency.
3. **Routine analysis** — At a scheduled time (e.g., nightly/weekly), batch jobs analyze collected data to:
   - Improve the site (UX, performance, error handling)
   - Debug recurring failure modes
   - Suggest mod rewrites for efficiency
   - Discover novel ways to push Skyrim to the extremes
4. **Long-term goal: OpenClaw** — Live modded Skyrim: play, talk to an agent, change everything in real time (within legal bounds). Self-improving system that turns modders into devs as they play. See [openclaw.md](openclaw.md) for vision, caution, and pay-tier design.

---

## Folder Structure

```
research/
├── README.md           # This file
├── corporate_power.md  # How we leverage free tiers, grants, partnerships
├── openclaw.md         # Live modded Skyrim vision (caution, pay tier)
├── data_flows.md       # What data comes in, goes out, gets collected
├── pipeline.md         # Routine analysis pipeline (schedule, scope, outputs)
└── ingest/             # Future: data collection hooks (async, non-blocking)
```

---

## Principles

- **Never slow users** — Collection is fire-and-forget or batched. No synchronous writes to research storage during requests.
- **Never charge for research** — Analysis runs on free/credits infrastructure. Users don't pay for the research pipeline.
- **Privacy first** — No PII in research data. Structural aggregates only. See [data_flows.md](data_flows.md).
- **Corporate power over custom** — Prefer AWS/GCP/Azure free tiers, GitHub Actions, Render cron, academic credits over building and paying for custom infra.

---

## Links

- [docs/fuel_spec.md](../docs/fuel_spec.md) — Structural fuel schema (LOOT graph, conflict types)
- [docs/architecture.md](../docs/architecture.md) — Thermodynamic/information-theoretic framing
- [samson_fuel.py](../samson_fuel.py) — Fuel extraction from LOOT (no user data)
