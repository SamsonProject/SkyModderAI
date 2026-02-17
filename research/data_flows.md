# Data Flows — What Comes In, Goes Out, Gets Collected

**Purpose:** Catalog all data flowing through SkyModderAI for research ingestion. Research collects **structural aggregates only**—no PII, no user mod lists (unless opt-in anonymized).

---

## 1. Data Coming In (User → Site)

| Source | Data | PII? | Research Use |
|--------|------|------|--------------|
| **Analyze** | Mod list text, game, masterlist version, game version | No (if not logged with user) | Conflict type distribution, load-order patterns |
| **Build List** | Preferences, game, optional Nexus slug | No | Preference × conflict correlation |
| **Quick Start** | Game, preferences | No | Popular setups |
| **Mod Search** | Query, game, limit | No | Query patterns, zero-result queries |
| **AI Chat** | User message, context (conflicts, mod list, specs) | No (if stripped) | Common questions, resolution success |
| **Community** | Post content, tag, votes | No (or anonymized) | Topic distribution, engagement |
| **Recommendations** | Mod list, game, specs | No | Mod co-occurrence, spec × recommendations |
| **Web Search (Pro)** | Query | No | Solution-finding patterns |
| **Refresh Masterlist** | Game | No | Update frequency |
| **Auth** | Email, password, OAuth | Yes | Never collected for research |

---

## 2. Data Going Out (Site → User)

| Endpoint | Data | Research Use |
|----------|------|--------------|
| **Analyze** | Conflicts, suggested order, stats, resolution links | Which resolutions get clicked? (future) |
| **Recommendations** | Mod list, warnings | Recommendation quality |
| **AI Chat** | Assistant response | Response length, resolution rate |
| **Search** | Results, scores | Relevance feedback (future) |
| **Quick Start** | Preset configs | Preset popularity |
| **Build List** | Generated list | List structure, mod count distribution |

---

## 3. External Data (Site ↔ External)

| Source | Data | Direction |
|--------|------|-----------|
| **LOOT masterlist** | Mod database, requirements, incompatibilities, patches | In (download) |
| **Nexus** | Mod metadata, links | In (API/preview) |
| **OpenAI** | Chat completions | Out (prompts), In (responses) |
| **Web search** | Reddit, Nexus, etc. | Out (query), In (results) |
| **Stripe** | Payments | Out (create checkout), In (webhooks) |

---

## 4. What Research Collects (Structural Only)

From [docs/fuel_spec.md](../docs/fuel_spec.md) and extension:

| Data | Source | Schema |
|------|--------|--------|
| **Fuel** | LOOT parser (masterlist) | `data/fuel/{game}_{timestamp}.json` |
| **Conflict type frequencies** | Per-analysis aggregate | Counts by type, game |
| **Error/warning/info ratios** | Per-analysis aggregate | Severity distribution |
| **Top incompatible pairs** | LOOT | From fuel |
| **Cooperation ratio** | Patches / incompatibilities | From fuel |
| **Query patterns** | Search logs (anonymized) | Query → result count, zero-result rate |
| **Resolution lookups** | `/api/resolve` | Type × game (no user) |

### What We Never Collect

- User mod lists (unless explicit opt-in, anonymized buckets only)
- Email, IP, session tokens
- Chat content with identifying context
- Payment details

---

## 5. Ingestion Points (Future)

| Point | Trigger | Action |
|-------|---------|--------|
| **Post-analyze** | After `/api/analyze` returns | Async enqueue: conflict type counts, game, mod count bucket |
| **Post-fuel** | When `samson_fuel.write_fuel()` runs | Fuel already in `data/fuel/` |
| **Search** | After `/api/mod-search` or `/api/search` | Enqueue: query hash, result count, game |
| **AI context** | After `/api/ai-context` | Enqueue: query type, conflict types in context |
| **Cron** | Scheduled | Aggregate enqueued items; run pipeline |

**Implementation:** Use a queue (Redis, SQS, or file-based) that research pipeline consumes. Fire-and-forget from request path.

---

## 6. Retention

- **Fuel:** Keep last N exports per game (e.g., 30). Older = archive or delete.
- **Aggregates:** Rolling window (e.g., 90 days). No raw request logs.
- **Outputs:** Analysis results kept for improvement tracking. Prune old outputs periodically.
