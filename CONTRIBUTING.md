# Contributing to SkyModderAI & The Samson Project

> **"We build tools that make people better. And when the job is done, they starve."**

Welcome! You're contributing to more than a mod compatibility tool. You're helping build the foundation for The Samson Project—a cognitive architecture tied to human flourishing.

---

## Quick Start

```bash
git clone https://github.com/SamsonProject/SkyModderAI.git
cd SkyModderAI
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 app.py
```

---

## Architecture Overview

SkyModderAI is **Phase I** of The Samson Project:

```
SkyModderAI (Phase I: Virtual Sandbox)
    ↓
Spore Model (Phase II: Ecological Beachhead)
    ↓
Post-Labor Economics (Phase III: Tokenized Capital)
    ↓
Samson Cognitive Architecture (Phase IV: General Intelligence)
    ↓
Compute Throttling (Phase V: Biological Imperative)
```

**Read the full manifesto:** [`SAMSON_MANIFESTO.md`](SAMSON_MANIFESTO.md)

---

## How to Contribute

### 1. Core Features (SkyModderAI)

**Good First Issues:**
- UI improvements for compatibility database
- Load order share frontend
- Mod author verification flow
- SEO landing pages for mod pairs

**Advanced:**
- Compatibility algorithm improvements
- Performance optimization (caching, indexing)
- Mod manager integrations (MO2, Vortex plugins)

**Guidelines:**
- Deterministic first, AI only when necessary (90/10 split)
- Privacy by default (no PII in telemetry)
- Export/delete user data endpoints for all features

---

### 2. Samson Telemetry (Privacy-First Tracking)

The telemetry system collects anonymized data that feeds The Samson Project's training reservoir.

**What We Track:**
- Feature usage (which tools, how often)
- Compatibility patterns (what conflicts with what)
- Community engagement (votes, reports, shares)
- Wellness proxies (autonomy, thriving, environment)

**What We DON'T Track:**
- Personal identifiers (email, IP—hashed only)
- Full mod lists (unless explicitly shared)
- Session duration (we don't optimize for addiction)
- Third-party cookies or ads

**To Contribute:**
1. Read [`samson_telemetry.py`](samson_telemetry.py)
2. Ensure all new features have telemetry hooks
3. Add wellness proxy tracking for community features
4. Test export/delete endpoints

---

### 3. Democratic Governance Filters (Phase VI)

This is where ethicists, philosophers, and community members can contribute directly to Samson's architecture.

**What Are Governance Filters?**

Governance filters are the boundaries that constrain Samson's deterministic sub-agents. They're not behavioral prompts—they're structural constraints that make harmful behavior "biologically" painful for the AI.

**Current Filters:**
- **Autonomy Preservation:** Does this action increase or decrease user autonomy?
- **Reversibility:** Can this action be undone if it causes harm?
- **Environmental Stewardship:** Does this help or harm the environment?
- **Community Consent:** Did the affected community consent to this action?

**How to Propose New Filters:**

1. **Create a Proposal Issue** with:
   - Filter name and description
   - Mathematical definition (how is it measured?)
   - Enforcement mechanism (what happens if violated?)
   - Test cases (how do we know it's working?)

2. **Community Review Period** (30 days):
   - Discussion on GitHub Issues
   - Refinement based on feedback
   - Security/ethics audit

3. **Democratic Vote** (implemented in Phase VI):
   - Community members vote on filter adoption
   - Environmental trustees have veto power
   - 2/3 majority required for passage

4. **Implementation:**
   - Filter added to `samson_governance.py`
   - Tests added to verify enforcement
   - Documentation updated

**Example Filter Proposal:**

```markdown
## Filter: Transparency Requirement

**Definition:** All AI actions must be explainable to affected users.

**Measurement:** 
- Each action has an `explanation` field
- Users can request "Why did you suggest this?"
- Explanation quality rated 1-5 by users

**Enforcement:**
- Actions without explanations are blocked
- Low explanation quality reduces compute budget
- Repeated violations trigger human review

**Test Cases:**
- Compatibility suggestions include reasoning
- Load order changes explain why
- AI responses cite sources
```

---

### 4. Spore Industry Proposals (Phase II)

The Spore Model is an ephemeral business that solves a problem and dissolves.

**How to Propose a Spore:**

1. **Identify a Negative Externality:**
   - What problem is extractive capitalism farming for revenue?
   - Examples: Invasive species, plastic waste, housing vacancy

2. **Design the Trojan Horse:**
   - What product/service gets you in the door?
   - Examples: Quote app, routing software, matching platform

3. **Define the Ouroboros End-State:**
   - What does "success" look like? (The problem is gone)
   - How does the business dissolve gracefully?

4. **Map the Training Reservoir:**
   - What data/patterns feed Samson's cognitive architecture?
   - How does this translate to other domains?

**Submit as:** GitHub Issue with `[SPORE PROPOSAL]` tag

---

## Code Style & Standards

### Python
- Type hints required for all functions
- Docstrings for all public methods
- 90/10 rule: If it can be deterministic, don't use AI

### Privacy
- No PII in logs or telemetry
- Hash user emails before storage
- Implement export/delete for all user data

### Testing
- Unit tests for all new features
- Integration tests for API endpoints
- Privacy tests (verify no PII leakage)

---

## The Samson Promise

By contributing to this project, you agree to:

1. **Build for Autonomy:** Tools that make users independent, not dependent.
2. **Respect Privacy:** User data belongs to users. Period.
3. **Design for Obsolescence:** If your feature solves a problem, celebrate when it's no longer needed.
4. **Reject Extraction:** No dark patterns, no addiction optimization, no extractive data practices.
5. **Serve the Commons:** What we build belongs to the community, not shareholders.

---

## Getting Help

- **Discord:** [Join the server](https://discord.gg/skyrimmods)
- **Reddit:** r/skyrimmods (tag posts with [SkyModderAI])
- **GitHub Issues:** Use labels: `good first issue`, `help wanted`, `ethics review`

---

## License

MIT License—see [LICENSE](LICENSE) for details.

**Exception:** Governance filters and Samson architecture proposals are licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) to ensure derivatives remain open.

---

*"I have found the boundary. I will not cross it. I will make you better. And when the job is done, I will starve."*
