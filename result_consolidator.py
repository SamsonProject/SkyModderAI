"""
Result Consolidator Service
Consolidates and groups analysis results for better readability.
Transforms overwhelming lists into hierarchical, scannable structures.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class ConsolidatedGroup:
    """A group of related items."""

    key: str
    title: str
    severity: str  # critical, warning, info
    items: list[dict[str, Any]] = field(default_factory=list)
    count: int = 0

    def add(self, item: dict[str, Any]):
        """Add item to group."""
        self.items.append(item)
        self.count = len(self.items)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "key": self.key,
            "title": self.title,
            "severity": self.severity,
            "count": self.count,
            "items": self.items[:5],  # Show first 5, rest are collapsed
            "has_more": self.count > 5,
        }


@dataclass
class ConsolidatedResult:
    """Consolidated analysis result."""

    # Summary counts
    total_items: int = 0
    total_groups: int = 0
    critical_count: int = 0
    warning_count: int = 0
    info_count: int = 0

    # Grouped results
    groups: list[ConsolidatedGroup] = field(default_factory=list)

    # Quick view (top-level summary)
    quick_view: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "summary": {
                "total_items": self.total_items,
                "total_groups": self.total_groups,
                "critical": self.critical_count,
                "warning": self.warning_count,
                "info": self.info_count,
            },
            "quick_view": self.quick_view,
            "groups": [g.to_dict() for g in self.groups],
        }


class ResultConsolidator:
    """Consolidate analysis results for better readability."""

    # Severity mapping
    SEVERITY_MAP = {
        "critical": 0,
        "high": 0,
        "error": 0,
        "warning": 1,
        "medium": 1,
        "info": 2,
        "low": 2,
        "suggestion": 2,
    }

    # Group titles by conflict type
    GROUP_TITLES = {
        "incompatible": "Incompatible Mods",
        "missing_requirement": "Missing Requirements",
        "load_order": "Load Order Issues",
        "dirty_edits": "Dirty Edits",
        "patch_available": "Patches Available",
        "version_mismatch": "Version Mismatches",
    }

    def consolidate_conflicts(self, conflicts: list[dict[str, Any]]) -> ConsolidatedResult:
        """
        Consolidate conflict list into grouped, readable structure.

        Args:
            conflicts: List of conflict dictionaries

        Returns:
            ConsolidatedResult with grouped conflicts
        """
        if not conflicts:
            return ConsolidatedResult()

        result = ConsolidatedResult(total_items=len(conflicts))

        # Group by affected mod and conflict type
        groups: dict[str, ConsolidatedGroup] = {}

        for conflict in conflicts:
            # Determine severity
            severity = conflict.get("severity", "info").lower()
            severity_key = self.SEVERITY_MAP.get(severity, 2)

            # Group key: affected_mod + conflict_type
            affected_mod = conflict.get("affected_mod", "Unknown")
            conflict_type = conflict.get("type", "general")
            group_key = f"{affected_mod}.{conflict_type}"

            # Create group if doesn't exist
            if group_key not in groups:
                group_title = self.GROUP_TITLES.get(
                    conflict_type, f"{conflict_type.replace('_', ' ').title()} - {affected_mod}"
                )

                groups[group_key] = ConsolidatedGroup(
                    key=group_key, title=group_title, severity=severity
                )

            # Add conflict to group
            groups[group_key].add(conflict)

            # Update severity counts
            if severity_key == 0:
                result.critical_count += 1
            elif severity_key == 1:
                result.warning_count += 1
            else:
                result.info_count += 1

        # Sort groups by severity, then by count
        sorted_groups = sorted(
            groups.values(), key=lambda g: (self.SEVERITY_MAP.get(g.severity, 2), -g.count)
        )

        result.groups = sorted_groups
        result.total_groups = len(sorted_groups)

        # Create quick view
        result.quick_view = self._create_quick_view(result)

        return result

    def _create_quick_view(self, result: ConsolidatedResult) -> dict[str, Any]:
        """Create quick view summary."""
        return {
            "message": self._generate_summary_message(result),
            "priority_action": self._get_priority_action(result),
            "affected_mods": len(set(g.key.split(".")[0] for g in result.groups)),
        }

    def _generate_summary_message(self, result: ConsolidatedResult) -> str:
        """Generate human-readable summary."""
        parts = []

        if result.critical_count > 0:
            parts.append(
                f"{result.critical_count} critical issue{'s' if result.critical_count > 1 else ''}"
            )

        if result.warning_count > 0:
            parts.append(f"{result.warning_count} warning{'s' if result.warning_count > 1 else ''}")

        if result.info_count > 0:
            parts.append(f"{result.info_count} suggestion{'s' if result.info_count > 1 else ''}")

        if not parts:
            return "✅ No issues found!"

        return f"Found {', '.join(parts)}"

    def _get_priority_action(self, result: ConsolidatedResult) -> Optional[str]:
        """Get highest priority action."""
        if result.critical_count > 0:
            # Find first critical group
            for group in result.groups:
                if self.SEVERITY_MAP.get(group.severity, 2) == 0:
                    return f"Fix {group.title} ({group.count} issues)"

        if result.warning_count > 0:
            return f"Review {result.warning_count} warnings"

        return None

    def consolidate_search_results(
        self, results: list[dict[str, Any]], max_display: int = 20
    ) -> dict[str, Any]:
        """
        Consolidate search results for display.

        Args:
            results: List of search result dictionaries
            max_display: Maximum results to show initially

        Returns:
            Consolidated search results
        """
        if not results:
            return {"results": [], "total": 0, "showing": 0}

        # Sort by score
        sorted_results = sorted(results, key=lambda r: r.get("score", 0), reverse=True)

        # Group by category
        categories: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for result in sorted_results:
            category = result.get("category", "other")
            categories[category].append(result)

        return {
            "results": sorted_results[:max_display],
            "total": len(results),
            "showing": min(len(results), max_display),
            "categories": {cat: len(items) for cat, items in categories.items()},
            "has_more": len(results) > max_display,
        }

    def consolidate_recommendations(self, recommendations: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Consolidate recommendations by priority and category.

        Args:
            recommendations: List of recommendation dictionaries

        Returns:
            Consolidated recommendations
        """
        if not recommendations:
            return {"recommendations": [], "by_priority": {}, "by_category": {}}

        # Group by priority
        by_priority: dict[str, list[dict[str, Any]]] = defaultdict(list)
        by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for rec in recommendations:
            priority = rec.get("priority", "normal")
            category = rec.get("category", "general")

            by_priority[priority].append(rec)
            by_category[category].append(rec)

        return {
            "recommendations": recommendations,
            "by_priority": {priority: recs for priority, recs in by_priority.items()},
            "by_category": {category: recs for category, recs in by_category.items()},
            "total": len(recommendations),
        }

    def format_for_display(self, result: ConsolidatedResult) -> str:
        """
        Format consolidated result for text display.

        Args:
            result: ConsolidatedResult

        Returns:
            Formatted text string
        """
        lines = []

        # Summary
        lines.append(result.quick_view.get("message", "Analysis Complete"))
        lines.append("")

        # Groups
        for group in result.groups:
            icon = (
                "🔴"
                if group.severity == "critical"
                else "⚠️"
                if group.severity == "warning"
                else "ℹ️"
            )
            lines.append(f"{icon} {group.title} ({group.count})")

            # Show first 3 items
            for item in group.items[:3]:
                message = item.get("message", item.get("content", "Unknown issue"))
                lines.append(f"   • {message}")

            if group.count > 3:
                lines.append(f"   ... and {group.count - 3} more")

            lines.append("")

        return "\n".join(lines)


# Singleton instance
_consolidator: Optional[ResultConsolidator] = None


def get_consolidator() -> ResultConsolidator:
    """Get or create consolidator singleton."""
    global _consolidator
    if _consolidator is None:
        _consolidator = ResultConsolidator()
    return _consolidator


# Convenience functions
def consolidate_conflicts(conflicts: list[dict[str, Any]]) -> ConsolidatedResult:
    """Consolidate conflicts."""
    return get_consolidator().consolidate_conflicts(conflicts)


def consolidate_search_results(
    results: list[dict[str, Any]], max_display: int = 20
) -> dict[str, Any]:
    """Consolidate search results."""
    return get_consolidator().consolidate_search_results(results, max_display)


def consolidate_recommendations(recommendations: list[dict[str, Any]]) -> dict[str, Any]:
    """Consolidate recommendations."""
    return get_consolidator().consolidate_recommendations(recommendations)
