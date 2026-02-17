"""
OpenClaw workflow engine.

Design goals:
- Keep capabilities ambitious but constrained.
- Force explicit permission scopes for higher-risk workflows.
- Produce explainable, guard-checkable plans before any execution.
"""

from __future__ import annotations

from typing import Any, Dict, List

OPENCLAW_PERMISSION_SCOPES = [
    "launch_game",
    "read_game_logs",
    "read_performance_metrics",
    "controller_signal",
    "input_signal_aggregate",
    "internet_research",
    "write_sandbox_files",
    "suggest_mod_tweaks",
]


def build_openclaw_plan(
    *,
    game: str,
    objective: str,
    playstyle: str,
    permissions: Dict[str, bool],
    telemetry: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build a constrained, explainable plan for OpenClaw.
    The plan is intentionally sandbox-first and can be preflight-validated.
    """
    game_id = (game or "skyrimse").lower()
    objective_text = (objective or "improve stability and visual quality").strip()
    playstyle_text = (playstyle or "balanced").strip()

    can_launch = bool(permissions.get("launch_game"))
    can_logs = bool(permissions.get("read_game_logs"))
    can_perf = bool(permissions.get("read_performance_metrics"))
    can_web = bool(permissions.get("internet_research"))
    can_write_sandbox = bool(permissions.get("write_sandbox_files"))
    can_input = bool(permissions.get("input_signal_aggregate"))
    can_controller = bool(permissions.get("controller_signal"))

    actions: List[Dict[str, Any]] = []
    actions.append(
        {
            "phase": "baseline",
            "kind": "analyze_current_state",
            "description": "Analyze LOOT conflicts, plugin pressure, and system impact as baseline.",
            "requires_permissions": [],
        }
    )
    if can_logs:
        actions.append(
            {
                "phase": "observe",
                "kind": "read_runtime_logs",
                "description": "Read game/runtime logs to classify crash and stutter signatures.",
                "requires_permissions": ["read_game_logs"],
            }
        )
    if can_perf:
        actions.append(
            {
                "phase": "observe",
                "kind": "read_performance_metrics",
                "description": "Capture FPS frametime + plugin count correlation snapshot.",
                "requires_permissions": ["read_performance_metrics"],
            }
        )
    if can_input or can_controller:
        signals = []
        if can_input:
            signals.append("input_signal_aggregate")
        if can_controller:
            signals.append("controller_signal")
        actions.append(
            {
                "phase": "observe",
                "kind": "read_playstyle_signals",
                "description": "Use aggregated input/controller signals to tune recommendations by playstyle.",
                "requires_permissions": signals,
            }
        )
    if can_web:
        actions.append(
            {
                "phase": "research",
                "kind": "internet_research",
                "description": "Fetch known fixes and compatibility notes from trusted modding sources.",
                "requires_permissions": ["internet_research"],
            }
        )

    # Sandbox write actions (always guard-checkable)
    if can_write_sandbox:
        actions.extend(
            [
                {
                    "phase": "plan",
                    "kind": "sandbox_write",
                    "description": "Write candidate preset profile in OpenClaw workspace.",
                    "requires_permissions": ["write_sandbox_files"],
                    "file_action": {
                        "operation": "write",
                        "rel_path": ".openclaw/profiles/candidate_profile.json",
                        "bytes_requested": 16384,
                    },
                },
                {
                    "phase": "plan",
                    "kind": "sandbox_write",
                    "description": "Write rollback notes and manual reversion checklist.",
                    "requires_permissions": ["write_sandbox_files"],
                    "file_action": {
                        "operation": "write",
                        "rel_path": ".openclaw/checkpoints/rollback_notes.md",
                        "bytes_requested": 8192,
                    },
                },
            ]
        )

    if can_launch:
        actions.append(
            {
                "phase": "execute",
                "kind": "launch_intent",
                "description": "Offer launch intent through OpenClaw wrapper (user-confirmed).",
                "requires_permissions": ["launch_game"],
                "launch": {"game": game_id, "mode": "wrapper_intent_only"},
            }
        )

    actions.append(
        {
            "phase": "verify",
            "kind": "post_run_review",
            "description": "Compare new run against baseline; keep only net-positive changes.",
            "requires_permissions": [],
        }
    )

    return {
        "game": game_id,
        "objective": objective_text,
        "playstyle": playstyle_text,
        "telemetry": telemetry or {},
        "actions": actions,
        "safety_contract": {
            "requires_manual_confirmation": True,
            "no_system_level_operations": True,
            "sandbox_first": True,
            "rollback_before_apply": True,
        },
    }


def suggest_loop_adjustments(feedback: Dict[str, Any]) -> List[str]:
    """
    Turn post-run feedback into next-step suggestions.
    """
    tips: List[str] = []
    fps_avg = _to_float(feedback.get("fps_avg"))
    crashes = _to_int(feedback.get("crashes"))
    stutter = _to_int(feedback.get("stutter_events"))
    enjoyment = _to_int(feedback.get("enjoyment_score"))

    if crashes > 0:
        tips.append("Prioritize stability profile: trim script-heavy mods and resolve high-severity conflicts first.")
    if fps_avg is not None and fps_avg < 50:
        tips.append("Shift graphics profile toward balanced/performance and reduce VRAM-heavy texture packs.")
    if stutter > 8:
        tips.append("Enable frametime-focused profile and review script latency hotspots.")
    if enjoyment >= 8 and crashes == 0:
        tips.append("Current profile is healthy; iterate visuals incrementally with one change per run.")
    if not tips:
        tips.append("Collect another run with FPS + crash notes to improve confidence in next recommendations.")
    return tips[:5]


def _to_int(v: Any) -> int:
    try:
        return int(v or 0)
    except Exception:
        return 0


def _to_float(v: Any):
    try:
        return float(v)
    except Exception:
        return None

