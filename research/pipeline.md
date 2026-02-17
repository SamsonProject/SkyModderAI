# Routine Analysis Pipeline

**Purpose:** At a scheduled time, analyze collected research data to produce improvements across the site, debugging, mod efficiency, and novel Skyrim pushes.

---

## 1. Schedule

| Cadence | Scope | Infra |
|---------|-------|-------|
| **Daily** | Fuel aggregation, conflict type distribution, error rate | GitHub Actions cron |
| **Weekly** | Deeper analysis, mod efficiency suggestions, knowledge index gaps | Same or Render cron |
| **Monthly** | Trend reports, OpenClaw readiness check (when relevant) | Manual or scheduled |

**Default:** 4 AM UTC daily (low traffic).

---

## 2. Pipeline Steps

### Step 1: Ingest

- Read fuel files from `data/fuel/` (or S3 if migrated)
- Read enqueued aggregates from queue (if implemented)
- Merge with previous run's state (rolling window)

### Step 2: Aggregate

- Conflict type × game × mod-count-bucket distribution
- Top incompatible pairs over time
- Cooperation ratio trend
- Zero-result search queries (candidates for knowledge index)
- Resolution lookup frequency (which types need better docs)

### Step 3: Analyze

| Analysis | Output | Use |
|----------|--------|-----|
| **Conflict hotspots** | Mod pairs with highest conflict rate | Prioritize resolution docs, patches |
| **Recurring errors** | Error types that spike | Debug, add to knowledge index |
| **Query gaps** | Queries with no good results | Improve search, add mods to index |
| **Load-order patterns** | Common violations | Suggest LOOT rules, docs |
| **Mod efficiency** | Heavy mods with many patches | Suggest merge/simplify (for mod authors) |
| **Novel pushes** | Underused mod combos, stable large lists | Blog, recommendations |

### Step 4: Produce Outputs

- `research/outputs/daily/{date}.json` — Raw aggregates
- `research/outputs/suggestions/{date}.md` — Human-readable improvement suggestions
- Optional: PR with knowledge_index updates, new resolution entries

### Step 5: Act (Manual or Automated)

- **Manual:** Review suggestions, update docs, add resolutions
- **Semi-auto:** Script to add high-priority resolutions to knowledge_index
- **Full auto (future):** Agent suggests mod rewrites; human approves

---

## 3. Improvement Targets

| Target | Metric | Action |
|--------|--------|--------|
| **Site** | Error rate, latency, zero-result rate | Fix bugs, optimize queries, expand index |
| **Debugging** | Recurring conflict types | Add resolutions, esoteric solutions |
| **Mod efficiency** | Patch count, dependency depth | Suggest merges, lighter alternatives |
| **Novel Skyrim** | Stable 500+ plugin lists, underused combos | Document, recommend |
| **OpenClaw** | User progression (modder → dev) | Improve agent prompts, add capabilities |

---

## 4. Script Layout (Future)

```
research/
├── pipeline/
│   ├── run.py        # Entry: ingest → aggregate → analyze → output
│   ├── ingest.py     # Read fuel, queue
│   ├── aggregate.py  # Roll up counts, distributions
│   ├── analyze.py    # Conflict hotspots, gaps, efficiency
│   └── output.py     # Write JSON, Markdown
└── outputs/          # Gitignored
    ├── daily/
    └── suggestions/
```

---

## 5. Dependencies

- Python 3.x
- Access to `data/fuel/` (local or mounted)
- Optional: Redis/SQS for queue; S3 for fuel archive
- No user-facing deps; pipeline runs in isolation
