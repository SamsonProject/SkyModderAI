# Research Ingest

**Purpose:** Future home for data collection hooks. All ingestion must be:

- **Async or batched** — Never block user requests
- **Privacy-safe** — No PII; structural aggregates only
- **Lightweight** — Minimal overhead (e.g., append to a queue file, or fire-and-forget HTTP to internal endpoint)

## Planned Hooks

| Hook | Trigger | Data |
|------|---------|------|
| `post_analyze` | After `/api/analyze` | Conflict type counts, game, mod count bucket |
| `post_search` | After search endpoints | Query hash, result count, zero-result flag |
| `post_ai_context` | After AI context build | Conflict types in context |

## Implementation

When ready: add optional `research.ingest.enqueue(...)` calls from `app.py`, guarded by `RESEARCH_INGEST_ENABLED` env var. Default: disabled.
