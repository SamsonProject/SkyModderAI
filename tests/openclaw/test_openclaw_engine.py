"""
Tests for OpenClaw plan and loop suggestion engine.
"""

from openclaw_engine import build_openclaw_plan, suggest_loop_adjustments


def test_plan_includes_launch_when_permission_granted():
    plan = build_openclaw_plan(
        game="skyrimse",
        objective="improve fps",
        playstyle="action",
        permissions={
            "launch_game": True,
            "write_sandbox_files": True,
            "read_game_logs": True,
            "read_performance_metrics": True,
        },
        telemetry={},
    )
    kinds = [a.get("kind") for a in plan.get("actions", [])]
    assert "launch_intent" in kinds
    assert "sandbox_write" in kinds


def test_plan_omits_launch_without_permission():
    plan = build_openclaw_plan(
        game="skyrimse",
        objective="improve stability",
        playstyle="balanced",
        permissions={},
        telemetry={},
    )
    kinds = [a.get("kind") for a in plan.get("actions", [])]
    assert "launch_intent" not in kinds


def test_feedback_suggestions_for_low_fps_and_crashes():
    tips = suggest_loop_adjustments(
        {
            "fps_avg": 42,
            "crashes": 2,
            "stutter_events": 15,
            "enjoyment_score": 4,
        }
    )
    joined = " ".join(tips).lower()
    assert "stability" in joined
    assert "performance" in joined or "fps" in joined
