"""
SkyModderAI - Analysis Service

Handles mod list analysis, conflict detection, and recommendations.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List

from conflict_detector import ConflictDetector, parse_mod_list_text
from exceptions import (
    ConflictDetectionError,
    InvalidGameIDError,
    InvalidModListError,
)
from mod_recommendations import get_loot_based_suggestions
from security_utils import validate_game_id, validate_mod_list
from system_impact import get_system_impact

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Result of mod list analysis."""

    game: str
    mod_count: int
    enabled_count: int
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    system_impact: Dict[str, Any] = field(default_factory=dict)
    summary: Dict[str, Any] = field(default_factory=dict)
    warnings: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "game": self.game,
            "mod_count": self.mod_count,
            "enabled_count": self.enabled_count,
            "conflicts": self.conflicts,
            "recommendations": self.recommendations,
            "system_impact": self.system_impact,
            "summary": self.summary,
            "warnings": self.warnings,
        }


class AnalysisService:
    """Service for mod analysis operations."""

    def __init__(self, game: str = "skyrimse") -> None:
        """
        Initialize analysis service.

        Args:
            game: Game ID to analyze for
        """
        try:
            self.game = validate_game_id(game)
        except ValueError as e:
            raise InvalidGameIDError(str(e))

    def analyze(self, mod_list: str) -> AnalysisResult:
        """
        Analyze a mod list for conflicts and issues.

        Args:
            mod_list: Newline-separated mod list

        Returns:
            AnalysisResult with conflicts, recommendations, and impact

        Raises:
            InvalidModListError: If mod list invalid
            ConflictDetectionError: If analysis fails
        """
        try:
            # Validate mod list
            mod_list = validate_mod_list(mod_list)

            # Parse mods
            mods = parse_mod_list_text(mod_list)

            # Detect conflicts
            detector = ConflictDetector(self.game)
            analysis = detector.analyze(mods)

            # Get LOOT-based recommendations (missing requirements and companion mods)
            mod_names = [m.get("name", "") for m in mods]
            recommendations = get_loot_based_suggestions(detector.parser, mod_names)

            # Get system impact
            impact = get_system_impact(mods, self.game)

            # Get mod warnings
            from mod_warnings import get_mod_warnings

            warnings = get_mod_warnings(mods, self.game)

            logger.info(
                f"Analysis completed: {len(mods)} mods, "
                f"{len(analysis.get('conflicts', []))} conflicts"
            )

            return AnalysisResult(
                game=self.game,
                mod_count=len(mods),
                enabled_count=sum(1 for m in mods if m.get("enabled", True)),
                conflicts=analysis.get("conflicts", []),
                recommendations=recommendations,
                system_impact=impact,
                summary=analysis.get("summary", {}),
                warnings=warnings,
            )

        except (InvalidModListError, InvalidGameIDError):
            raise
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise ConflictDetectionError(str(e))

    def analyze_mod(self, mod_name: str) -> Dict[str, Any]:
        """
        Analyze a single mod.

        Args:
            mod_name: Mod name to analyze

        Returns:
            Mod analysis data
        """
        from search_engine import get_search_engine

        se = get_search_engine(self.game)
        results = se.search(mod_name, limit=1)

        if not results:
            return {"name": mod_name, "found": False}

        mod_data = results[0]
        return {
            "name": mod_data.get("name", mod_name),
            "found": True,
            "compatibility_score": mod_data.get("score", 0),
            "requirements": mod_data.get("requirements", []),
            "incompatibilities": mod_data.get("incompatibilities", []),
        }

    def get_load_order(self, mod_list: str) -> List[str]:
        """
        Get optimized load order for mod list.

        Args:
            mod_list: Newline-separated mod list

        Returns:
            List of mod names in optimal order
        """
        mods = parse_mod_list_text(mod_list)
        detector = ConflictDetector(self.game)
        return detector.optimize_load_order(mods)

    def compare_load_orders(
        self,
        mod_list_a: str,
        mod_list_b: str,
    ) -> Dict[str, Any]:
        """
        Compare two load orders.

        Args:
            mod_list_a: First mod list
            mod_list_b: Second mod list

        Returns:
            Comparison data
        """
        mods_a = parse_mod_list_text(mod_list_a)
        mods_b = parse_mod_list_text(mod_list_b)

        names_a = {m["name"] for m in mods_a if m.get("enabled", True)}
        names_b = {m["name"] for m in mods_b if m.get("enabled", True)}

        return {
            "only_in_a": list(names_a - names_b),
            "only_in_b": list(names_b - names_a),
            "in_both": list(names_a & names_b),
            "count_a": len(names_a),
            "count_b": len(names_b),
        }

    def get_analysis_summary(self, mod_list: str) -> Dict[str, Any]:
        """
        Get quick analysis summary without full details.

        Args:
            mod_list: Newline-separated mod list

        Returns:
            Summary statistics
        """
        mods = parse_mod_list_text(mod_list)
        detector = ConflictDetector(self.game)
        analysis = detector.analyze(mods)

        return {
            "mod_count": len(mods),
            "enabled_count": sum(1 for m in mods if m.get("enabled", True)),
            "conflict_count": len(analysis.get("conflicts", [])),
            "warning_count": len(analysis.get("warnings", [])),
            "game": self.game,
        }
