"""
OpenClaw workflow engine.

Design goals:
- Keep capabilities ambitious but constrained.
- Force explicit permission scopes for higher-risk workflows.
- Produce explainable, guard-checkable plans before any execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

# =============================================================================
# Permission Scopes
# =============================================================================


class PermissionScope(str, Enum):
    """OpenClaw permission scopes."""

    LAUNCH_GAME = "launch_game"
    READ_GAME_LOGS = "read_game_logs"
    READ_PERFORMANCE_METRICS = "read_performance_metrics"
    CONTROLLER_SIGNAL = "controller_signal"
    INPUT_SIGNAL_AGGREGATE = "input_signal_aggregate"
    INTERNET_RESEARCH = "internet_research"
    WRITE_SANDBOX_FILES = "write_sandbox_files"
    SUGGEST_MOD_TWEAKS = "suggest_mod_tweaks"


OPENCLAW_PERMISSION_SCOPES = [scope.value for scope in PermissionScope]

# Denied operations (hard-coded safety)
OPENCLAW_DENIED_OPERATIONS: frozenset = frozenset(
    {
        "modify_system_files",
        "modify_registry",
        "modify_bios",
        "modify_bootloader",
        "modify_kernel",
        "modify_drivers",
        "network_exfiltration",
        "execute_arbitrary_code",
    }
)

# Allowed file extensions for sandbox operations
OPENCLAW_ALLOWED_EXTENSIONS: frozenset = frozenset(
    {
        ".txt",
        ".md",
        ".json",
        ".yaml",
        ".yml",
        ".ini",
        ".esp",
        ".esm",
        ".esl",
        ".psc",
        ".log",
    }
)


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class FileAction:
    """Represents a file operation in the sandbox."""

    operation: str  # read, write, delete, move, copy
    rel_path: str
    bytes_requested: int = 0
    content_hash: Optional[str] = None


@dataclass
class PlanAction:
    """Represents a single action in an OpenClaw plan."""

    phase: str
    kind: str
    description: str
    requires_permissions: List[str] = field(default_factory=list)
    file_action: Optional[FileAction] = None
    launch: Optional[Dict[str, str]] = None


@dataclass
class SafetyContract:
    """Safety constraints for plan execution."""

    requires_manual_confirmation: bool = True
    no_system_level_operations: bool = True
    sandbox_first: bool = True
    rollback_before_apply: bool = True


@dataclass
class OpenClawPlan:
    """Complete OpenClaw execution plan."""

    game: str
    objective: str
    playstyle: str
    actions: List[PlanAction] = field(default_factory=list)
    safety_contract: SafetyContract = field(default_factory=SafetyContract)
    telemetry: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert plan to dictionary for JSON serialization."""
        return {
            "game": self.game,
            "objective": self.objective,
            "playstyle": self.playstyle,
            "actions": [
                {
                    "phase": action.phase,
                    "kind": action.kind,
                    "description": action.description,
                    "requires_permissions": action.requires_permissions,
                    "file_action": (
                        {
                            "operation": action.file_action.operation,
                            "rel_path": action.file_action.rel_path,
                            "bytes_requested": action.file_action.bytes_requested,
                        }
                        if action.file_action
                        else None
                    ),
                    "launch": action.launch,
                }
                for action in self.actions
            ],
            "safety_contract": {
                "requires_manual_confirmation": self.safety_contract.requires_manual_confirmation,
                "no_system_level_operations": self.safety_contract.no_system_level_operations,
                "sandbox_first": self.safety_contract.sandbox_first,
                "rollback_before_apply": self.safety_contract.rollback_before_apply,
            },
            "telemetry": self.telemetry,
        }


# =============================================================================
# Plan Building
# =============================================================================


def build_openclaw_plan(
    *,
    game: str,
    objective: str,
    playstyle: str,
    permissions: Dict[str, bool],
    telemetry: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build a constrained, explainable plan for OpenClaw.
    The plan is intentionally sandbox-first and can be preflight-validated.

    Args:
        game: Game identifier (e.g., 'skyrimse')
        objective: User's objective (e.g., 'improve stability')
        playstyle: User's playstyle (e.g., 'balanced', 'performance', 'visuals')
        permissions: Dictionary of permission scope -> granted status
        telemetry: Optional telemetry data

    Returns:
        Plan dictionary ready for JSON serialization
    """
    plan = OpenClawPlan(
        game=(game or "skyrimse").lower(),
        objective=(objective or "improve stability and visual quality").strip(),
        playstyle=(playstyle or "balanced").strip(),
        telemetry=telemetry or {},
    )

    # Check permissions
    can_launch = bool(permissions.get(PermissionScope.LAUNCH_GAME))
    can_logs = bool(permissions.get(PermissionScope.READ_GAME_LOGS))
    can_perf = bool(permissions.get(PermissionScope.READ_PERFORMANCE_METRICS))
    can_web = bool(permissions.get(PermissionScope.INTERNET_RESEARCH))
    can_write_sandbox = bool(permissions.get(PermissionScope.WRITE_SANDBOX_FILES))
    can_input = bool(permissions.get(PermissionScope.INPUT_SIGNAL_AGGREGATE))
    can_controller = bool(permissions.get(PermissionScope.CONTROLLER_SIGNAL))

    # Phase 1: Baseline analysis (always included)
    plan.actions.append(
        PlanAction(
            phase="baseline",
            kind="analyze_current_state",
            description="Analyze LOOT conflicts, plugin pressure, and system impact as baseline.",
            requires_permissions=[],
        )
    )

    # Phase 2: Observation (permission-gated)
    if can_logs:
        plan.actions.append(
            PlanAction(
                phase="observe",
                kind="read_runtime_logs",
                description="Read game/runtime logs to classify crash and stutter signatures.",
                requires_permissions=[PermissionScope.READ_GAME_LOGS],
            )
        )

    if can_perf:
        plan.actions.append(
            PlanAction(
                phase="observe",
                kind="read_performance_metrics",
                description="Capture FPS frametime + plugin count correlation snapshot.",
                requires_permissions=[PermissionScope.READ_PERFORMANCE_METRICS],
            )
        )

    if can_input or can_controller:
        signals = []
        if can_input:
            signals.append(PermissionScope.INPUT_SIGNAL_AGGREGATE)
        if can_controller:
            signals.append(PermissionScope.CONTROLLER_SIGNAL)
        plan.actions.append(
            PlanAction(
                phase="observe",
                kind="read_playstyle_signals",
                description="Use aggregated input/controller signals to tune recommendations by playstyle.",
                requires_permissions=signals,
            )
        )

    if can_web:
        plan.actions.append(
            PlanAction(
                phase="research",
                kind="internet_research",
                description="Fetch known fixes and compatibility notes from trusted modding sources.",
                requires_permissions=[PermissionScope.INTERNET_RESEARCH],
            )
        )

    # Phase 3: Sandbox writes (permission-gated)
    if can_write_sandbox:
        plan.actions.extend(
            [
                PlanAction(
                    phase="plan",
                    kind="sandbox_write",
                    description="Write candidate preset profile in OpenClaw workspace.",
                    requires_permissions=[PermissionScope.WRITE_SANDBOX_FILES],
                    file_action=FileAction(
                        operation="write",
                        rel_path=".openclaw/profiles/candidate_profile.json",
                        bytes_requested=16384,
                    ),
                ),
                PlanAction(
                    phase="plan",
                    kind="sandbox_write",
                    description="Write rollback notes and manual reversion checklist.",
                    requires_permissions=[PermissionScope.WRITE_SANDBOX_FILES],
                    file_action=FileAction(
                        operation="write",
                        rel_path=".openclaw/checkpoints/rollback_notes.md",
                        bytes_requested=8192,
                    ),
                ),
            ]
        )

    # Phase 4: Execution (permission-gated)
    if can_launch:
        plan.actions.append(
            PlanAction(
                phase="execute",
                kind="launch_intent",
                description="Offer launch intent through OpenClaw wrapper (user-confirmed).",
                requires_permissions=[PermissionScope.LAUNCH_GAME],
                launch={"game": plan.game, "mode": "wrapper_intent_only"},
            )
        )

    # Phase 5: Verification (always included)
    plan.actions.append(
        PlanAction(
            phase="verify",
            kind="post_run_review",
            description="Compare new run against baseline; keep only net-positive changes.",
            requires_permissions=[],
        )
    )

    return plan.to_dict()


# =============================================================================
# Feedback Processing
# =============================================================================


def suggest_loop_adjustments(feedback: Dict[str, Any]) -> List[str]:
    """
    Turn post-run feedback into next-step suggestions.

    Args:
        feedback: Dictionary containing feedback data:
            - fps_avg: Average FPS
            - crashes: Number of crashes
            - stutter_events: Number of stutter events
            - enjoyment_score: User enjoyment rating (1-10)

    Returns:
        List of suggestion strings (max 5)
    """
    tips: List[str] = []
    fps_avg = _to_float(feedback.get("fps_avg"))
    crashes = _to_int(feedback.get("crashes"))
    stutter = _to_int(feedback.get("stutter_events"))
    enjoyment = _to_int(feedback.get("enjoyment_score"))

    if crashes > 0:
        tips.append(
            "Prioritize stability profile: trim script-heavy mods and resolve high-severity conflicts first."
        )

    if fps_avg is not None and fps_avg < 50:
        tips.append(
            "Shift graphics profile toward balanced/performance and reduce VRAM-heavy texture packs."
        )

    if stutter > 8:
        tips.append("Enable frametime-focused profile and review script latency hotspots.")

    if enjoyment >= 8 and crashes == 0:
        tips.append(
            "Current profile is healthy; iterate visuals incrementally with one change per run."
        )

    if not tips:
        tips.append(
            "Collect another run with FPS + crash notes to improve confidence in next recommendations."
        )

    return tips[:5]


# =============================================================================
# Safety Validation
# =============================================================================


def validate_plan_safety(plan: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate a plan against safety constraints.

    Args:
        plan: Plan dictionary from build_openclaw_plan

    Returns:
        Tuple of (is_safe, list_of_violations)
    """
    violations: List[str] = []

    # Check safety contract
    safety = plan.get("safety_contract", {})
    if not safety.get("requires_manual_confirmation"):
        violations.append("Plan must require manual confirmation")
    if not safety.get("no_system_level_operations"):
        violations.append("Plan must not allow system-level operations")
    if not safety.get("sandbox_first"):
        violations.append("Plan must use sandbox-first approach")

    # Check actions for denied operations
    for action in plan.get("actions", []):
        kind = action.get("kind", "")
        if kind in OPENCLAW_DENIED_OPERATIONS:
            violations.append(f"Action '{kind}' is not allowed")

        # Validate file actions
        file_action = action.get("file_action")
        if file_action:
            rel_path = file_action.get("rel_path", "")
            operation = file_action.get("operation", "")

            # Check path traversal attempts
            if ".." in rel_path or rel_path.startswith("/"):
                violations.append(f"Invalid file path: {rel_path}")

            # Check file extension
            ext = "." + rel_path.rsplit(".", 1)[-1] if "." in rel_path else ""
            if ext and ext not in OPENCLAW_ALLOWED_EXTENSIONS:
                violations.append(f"Disallowed file extension: {ext}")

            # Check bytes requested
            bytes_req = file_action.get("bytes_requested", 0)
            if bytes_req > 50 * 1024 * 1024:  # 50MB
                violations.append(f"File operation too large: {bytes_req} bytes")

    return len(violations) == 0, violations


def validate_permissions(permissions: Dict[str, bool]) -> tuple[bool, List[str]]:
    """
    Validate permission grants.

    Args:
        permissions: Dictionary of permission scope -> granted status

    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues: List[str] = []

    for scope in permissions:
        if scope not in OPENCLAW_PERMISSION_SCOPES:
            issues.append(f"Unknown permission scope: {scope}")

    # Warn about dangerous combinations
    if permissions.get(PermissionScope.LAUNCH_GAME) and permissions.get(
        PermissionScope.WRITE_SANDBOX_FILES
    ):
        issues.append(
            "Warning: Launch + Write permissions allow automated changes. Ensure user consent."
        )

    return len(issues) == 0, issues


# =============================================================================
# Helpers
# =============================================================================


def _to_int(v: Any) -> int:
    """Safely convert value to int."""
    try:
        return int(v or 0)
    except (TypeError, ValueError):
        return 0


def _to_float(v: Any) -> Optional[float]:
    """Safely convert value to float."""
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def get_permission_descriptions() -> Dict[str, str]:
    """Get human-readable descriptions for each permission scope."""
    return {
        PermissionScope.LAUNCH_GAME: "Launch the game through OpenClaw wrapper",
        PermissionScope.READ_GAME_LOGS: "Read game crash and performance logs",
        PermissionScope.READ_PERFORMANCE_METRICS: "Monitor FPS and performance metrics",
        PermissionScope.CONTROLLER_SIGNAL: "Read controller input patterns",
        PermissionScope.INPUT_SIGNAL_AGGREGATE: "Analyze aggregated input/playstyle data",
        PermissionScope.INTERNET_RESEARCH: "Research mod solutions online",
        PermissionScope.WRITE_SANDBOX_FILES: "Write files to OpenClaw sandbox workspace",
        PermissionScope.SUGGEST_MOD_TWEAKS: "Suggest mod configuration changes",
    }
