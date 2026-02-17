# Structural Fuel — Export Specification

**Purpose:** Data and structural substrate for constrained-system research. ModCheck provides:
1. Privacy-respecting feedback — errors, conflict patterns, structural data (no PII)
2. Physically-grounded structure — mod ecosystem as a model of constrained systems
3. Schema for drive mappings — mod-world to Heart/Intellect/Referee

---

## 1. Privacy-Respecting Data Collection

### What We Collect (Structural Only)

| Data | Source | PII? | Use |
|------|--------|-----|-----|
| Conflict type frequencies | LOOT masterlist + analysis | No | Failure mode distribution |
| Dependency graph structure | LOOT (requirements, load_after) | No | Graph topology |
| Incompatibility pairs | LOOT | No | Mutual-loss patterns |
| Patch availability | LOOT | No | Cooperation patterns |
| Error/warning/info ratios | Per-analysis aggregate | No | Severity distribution |
| Game + masterlist version | Analysis | No | Context |

### What We Never Collect

- User mod lists
- User identity, email, session data for fuel
- IP addresses, device info
- Any re-identifying data

### Opt-In (Future)

Explicit consent only: anonymized conflict type × game × mod-count buckets. No user lists.

---

## 2. Physical Structure

Mod ecosystem as constrained system:

- **Entities:** Mods. Identity, requirements, incompatibilities.
- **Relations:** Requirements (A→B), incompatibilities (A↔B), patches (A+B→C).
- **Ordering:** Load order = topological sort. Violations = stress.
- **Failure modes:** CTD, ILS = physical collapse when constraints violated.

### Graph

```
Nodes: mods (LOOT masterlist — public)
Edges: requirement, incompatible, patch, load_after
Stable: valid topology, no active incompatibilities
Unstable: cycle, missing req, unresolved conflict → crash
```

---

## 3. Drive Mappings

| Drive | ModCheck Analog |
|-------|-----------------|
| Wonder-seeking | Complexity gradient: mod count, patch count, depth |
| Relational depth | Community, engagement over time |
| Compression | Pruning: reduce context, preserve structure |
| Game-theoretic | Conflict = defection; patch = cooperation |
| Information preservation | Never discard graph structure |
| Meta-reasoning | Post-analysis: "What could we have understood better?" |

---

## 4. Schema

```json
{
  "source": "modcheck",
  "timestamp": "ISO8601",
  "game": "skyrimse",
  "structure": {
    "node_count": 1500,
    "edge_types": {"requirement": N, "incompatible": N, "patch": N, "load_after": N},
    "failure_modes": ["missing_requirement", "incompatible", "load_order_violation", "dirty_edits"],
    "cooperation_ratio": 0.35,
    "avg_dependency_depth": 2.1
  },
  "aggregate": {
    "top_incompatible_pairs": [["A", "B"], ...]
  }
}
```

No user data. All from LOOT (public).

---

## 5. Files

- `samson_fuel.py` — Extraction module
- `data/fuel/` — Local export (gitignored)
