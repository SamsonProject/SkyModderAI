# OpenClaw Integration Plan (Safety-First, High-Capability)

This is the practical roadmap for making OpenClaw worth a premium tier while preserving strict safety constraints.

## Product Direction

- Treat OpenClaw like a **mod-like local companion**: it runs with the game launch flow, stores state locally, asks scoped permissions, and continuously improves recommendations.
- Keep the web app as **planner/control plane** and the local helper as **executor/data plane**.

## Safety Contract (Non-Negotiable)

- No BIOS/UEFI, bootloader, registry hive, kernel/driver, or privileged system changes.
- No writes outside dedicated sandbox workspace.
- No execution without explicit user confirmation for each plan.
- Every write is guard-checked against immutable policy constraints.
- Rollback/checkpoint artifacts must be generated before applying any profile changes.

## Architecture

### 1) Control Plane (already integrated)

- Tier gate + grant token.
- Scope permissions API.
- Plan propose API.
- Guard-check API.
- Execute plan API (sandbox-constrained).
- Feedback loop API for iterative refinement.
- Safety posture endpoints and capability map.

### 2) Local Companion (next build step)

- Installed binary/script that:
  - launches game through wrapper intent,
  - reads logs/perf counters (permission-scoped),
  - writes only to sandbox workspace,
  - posts telemetry back to OpenClaw loop endpoints.
- Includes transparent permission prompt UI and revocation controls.

## Improvement Loop

1. Baseline analysis (LOOT conflicts, plugin pressure, system impact).
2. Runtime observation (logs/FPS/input/controller signals).
3. Plan proposal (guard-checked sandbox actions).
4. User approval.
5. Execution in sandbox + launch intent.
6. Post-run feedback capture (FPS/crashes/stutter/enjoyment).
7. Next-cycle recommendations tuned by evidence.

## $15 Tier Value Anchor

- Stronger than static LOOT checks:
  - evidence-driven tuning over repeated runs,
  - playstyle-aware recommendations,
  - safety-verifiable action plans and rollback notes.
- "Power without bricking risk" is the core promise.

