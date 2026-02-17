# Corporate Power Structure — Free Tiers, Credits, Partnerships

**Goal:** Run research analysis without charging users or slowing the site. Use existing corporate/commercial infrastructure that offers free tiers, credits, or research programs.

---

## 1. Cloud Free Tiers

| Provider | Free Tier | Use Case |
|----------|-----------|----------|
| **AWS** | 12 months free (EC2, S3, Lambda) | Batch jobs, storage for fuel/aggregates |
| **GCP** | $300 credits / 90 days; Always-free (Cloud Functions, Firestore) | Scheduled analysis, lightweight DB |
| **Azure** | $200 credits / 30 days; Always-free (Functions, Cosmos DB) | Same as above |
| **Render** | Free tier for web; Cron jobs on paid plans | Already used for app; add cron for research |
| **Vercel** | Serverless functions, cron | Edge jobs if we migrate |
| **Railway** | Free tier | Alternative to Render |

**Strategy:** Start with Render cron (if available) or GitHub Actions scheduled workflows. Move to AWS/GCP when volume justifies.

---

## 2. GitHub Actions (Zero Cost for Public Repos)

- **Scheduled workflows** — `schedule: cron('0 4 * * *')` = 4 AM UTC daily
- **Free for public repos** — 2000 min/month
- **Use:** Run `research/pipeline/run.py` (or similar) that:
  - Pulls fuel from `data/fuel/` (or S3 if we add it)
  - Runs analysis scripts
  - Writes outputs to `research/outputs/` or a branch
  - Opens PRs with improvement suggestions (optional)

**No user charge. No latency. Runs on GitHub's infra.**

---

## 3. Academic / Research Credits

| Program | Who | What |
|---------|-----|------|
| **Google Cloud for Startups** | Early-stage startups | Credits |
| **AWS Activate** | Startups | Credits |
| **Azure for Startups** | Startups | Credits |
| **GitHub Education** | Students, teachers | Pro features, credits |
| **Oracle Cloud Free Tier** | Anyone | Always-free VMs, storage |

**Strategy:** If SkyModderAI qualifies as a research/education project, apply. Use credits for heavier analysis (e.g., ML on conflict patterns).

---

## 4. Partnerships

- **Nexus Mods** — Already integrated. Potential: anonymized mod popularity × conflict rates for research (with permission).
- **LOOT** — Open source. We consume masterlist. No formal partnership needed; we could contribute back improvements.
- **Bethesda** — Modding is officially supported. No direct partnership; stay within ToS.

**Strategy:** Don't depend on partnerships for core research. Use them to enrich data if offered.

---

## 5. What We Don't Do

- **Charge users for research** — Never. Research is a backend process.
- **Sell data** — Never. No PII. Structural aggregates only.
- **Block requests on research writes** — Collection is async or batched. User requests return immediately.

---

## 6. Implementation Order

1. **Now:** Document data flows, pipeline design. No infra yet.
2. **Phase 1:** GitHub Actions cron → run fuel extraction + simple analysis (e.g., conflict type distribution). Output to `research/outputs/`.
3. **Phase 2:** Add Render cron (or similar) if we need more than 2000 min/month or persistent storage.
4. **Phase 3:** Apply for cloud credits if we need ML/heavy compute.
5. **Phase 4:** OpenClaw-related infra (separate pay tier; see [openclaw.md](openclaw.md)).
