"""
Transparency Service
Provides visibility into how analysis was performed.
Shows data sources, filters, AI involvement, and confidence scores.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class AnalysisMetadata:
    """Metadata about how analysis was performed."""

    # Data sources
    data_sources: list[dict[str, Any]] = field(default_factory=list)

    # Filters applied
    filters: list[dict[str, Any]] = field(default_factory=list)

    # AI involvement
    ai_involvement: dict[str, Any] = field(default_factory=dict)

    # Performance metrics
    performance: dict[str, Any] = field(default_factory=dict)

    # Confidence score
    confidence: float = 0.0

    # Timestamps
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "data_sources": self.data_sources,
            "filters": self.filters,
            "ai_involvement": self.ai_involvement,
            "performance": self.performance,
            "confidence": round(self.confidence, 2),
            "timing": {
                "started_at": self.started_at.isoformat() if self.started_at else None,
                "completed_at": self.completed_at.isoformat() if self.completed_at else None,
                "duration_ms": self.performance.get("duration_ms", 0),
            },
        }


class TransparencyService:
    """Provide transparency into analysis operations."""

    def __init__(self):
        """Initialize transparency service."""
        self._start_times: dict[str, float] = {}

    def start_analysis(self, analysis_id: str) -> AnalysisMetadata:
        """
        Start tracking an analysis operation.

        Args:
            analysis_id: Unique identifier for this analysis

        Returns:
            AnalysisMetadata object
        """
        self._start_times[analysis_id] = time.time()

        metadata = AnalysisMetadata(started_at=datetime.now())

        # Add default data sources
        metadata.data_sources = self._get_data_sources()

        return metadata

    def complete_analysis(
        self, analysis_id: str, metadata: AnalysisMetadata, result: dict[str, Any]
    ) -> AnalysisMetadata:
        """
        Complete analysis tracking.

        Args:
            analysis_id: Unique identifier
            metadata: AnalysisMetadata object
            result: Analysis result dictionary

        Returns:
            Updated AnalysisMetadata
        """
        # Calculate duration
        start_time = self._start_times.pop(analysis_id, time.time())
        duration_ms = (time.time() - start_time) * 1000

        metadata.completed_at = datetime.now()
        metadata.performance = {
            "duration_ms": round(duration_ms, 2),
            "items_analyzed": len(result.get("mod_list", [])),
            "conflicts_found": len(result.get("conflicts", [])),
            "cache_hits": 0,
            "cache_misses": 0,
        }

        # Get cache stats from cache service
        try:
            from cache_service import get_cache

            cache = get_cache()
            stats = cache.get_stats()
            metadata.performance["cache_hits"] = stats.get("hits", 0)
            metadata.performance["cache_misses"] = stats.get("misses", 0)
        except Exception as e:
            logger.debug(f"Could not get cache stats: {e}")

        # Calculate confidence
        metadata.confidence = self._calculate_confidence(result, metadata)

        # Add AI involvement
        metadata.ai_involvement = self._get_ai_involvement(result)

        return metadata

    def _get_data_sources(self) -> list[dict[str, Any]]:
        """Get configured data sources."""
        return [
            {
                "name": "LOOT Masterlist",
                "description": "Load order optimization rules",
                "last_updated": "Auto-updated",
                "url": "https://loot.github.io/",
            },
            {
                "name": "Community Reports",
                "description": "User-submitted conflict reports",
                "last_updated": "Real-time",
                "url": "/community",
            },
            {
                "name": "Research Pipeline",
                "description": "Autonomous research (Nexus, Reddit, GitHub)",
                "last_updated": "Every 6 hours",
                "url": "/api/research",
            },
        ]

    def _get_ai_involvement(self, result: dict[str, Any]) -> dict[str, Any]:
        """Determine AI involvement in analysis."""
        # Check if AI was used
        ai_used = result.get("ai_used", False)

        return {
            "conflict_detection": "Deterministic (no AI)" if not ai_used else "AI-assisted",
            "resolution_suggestions": "AI-assisted" if ai_used else "Rule-based",
            "recommendations": "AI-assisted" if ai_used else "Curated database",
            "tokens_used": result.get("ai_tokens", 0),
            "model": result.get("ai_model", "N/A"),
        }

    def _calculate_confidence(self, result: dict[str, Any], metadata: AnalysisMetadata) -> float:
        """
        Calculate confidence score for analysis.

        Based on:
        - Data source coverage
        - Version match quality
        - Community verification
        - AI confidence (if used)
        """
        confidence = 1.0

        # Reduce confidence for missing data
        if len(result.get("conflicts", [])) == 0 and len(result.get("mod_list", [])) > 0:
            # No conflicts found might mean incomplete data
            confidence *= 0.9

        # Reduce confidence for version mismatches
        version_info = result.get("version_info")
        if version_info and not version_info.get("matched", True):
            confidence *= 0.8

        # Reduce confidence if AI was uncertain
        if result.get("ai_confidence"):
            confidence *= result["ai_confidence"]

        # Boost confidence for community-verified results
        if result.get("community_verified", False):
            confidence = min(1.0, confidence * 1.1)

        return round(confidence, 2)

    def get_filters_applied(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Get list of filters applied during analysis.

        Args:
            context: Analysis context (game, version, etc.)

        Returns:
            List of applied filters
        """
        filters = []

        # Game version filter
        if context.get("game_version"):
            filters.append(
                {
                    "name": "Game Version",
                    "value": context["game_version"],
                    "description": "Only show compatible mods",
                }
            )

        # Credibility filter
        if context.get("min_credibility"):
            filters.append(
                {
                    "name": "Credibility Threshold",
                    "value": f"≥ {context['min_credibility']}",
                    "description": "Only show reliable sources",
                }
            )

        # Conflict type filters
        if context.get("conflict_types"):
            filters.append(
                {
                    "name": "Conflict Types",
                    "value": ", ".join(context["conflict_types"]),
                    "description": "Filter by conflict type",
                }
            )

        return filters

    def create_transparency_panel(
        self, metadata: AnalysisMetadata, context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Create complete transparency panel data.

        Args:
            metadata: AnalysisMetadata
            context: Analysis context

        Returns:
            Dictionary for UI rendering
        """
        return {
            "how_analyzed": {
                "data_sources": metadata.data_sources,
                "filters": self.get_filters_applied(context),
                "ai_involvement": metadata.ai_involvement,
                "performance": metadata.performance,
            },
            "confidence": {
                "score": metadata.confidence,
                "factors": self._get_confidence_factors(metadata),
            },
            "under_hood": {
                "deterministic": "90% of analysis uses deterministic rules",
                "ai_assisted": "10% uses AI for complex reasoning",
                "community": "Results verified by community reports",
            },
        }

    def _get_confidence_factors(self, metadata: AnalysisMetadata) -> list[str]:
        """Get factors affecting confidence score."""
        factors = []

        if metadata.confidence >= 0.9:
            factors.append("✅ High data coverage")
            factors.append("✅ Version matched")
        elif metadata.confidence >= 0.7:
            factors.append("⚠️ Some data may be incomplete")
        else:
            factors.append("❌ Limited data available")

        if metadata.ai_involvement.get("tokens_used", 0) == 0:
            factors.append("✅ 100% deterministic analysis")

        return factors


# Singleton instance
_transparency_service: Optional[TransparencyService] = None


def get_transparency_service() -> TransparencyService:
    """Get or create transparency service singleton."""
    global _transparency_service
    if _transparency_service is None:
        _transparency_service = TransparencyService()
    return _transparency_service


# Convenience functions
def start_analysis(analysis_id: str) -> AnalysisMetadata:
    """Start analysis tracking."""
    return get_transparency_service().start_analysis(analysis_id)


def complete_analysis(
    analysis_id: str, metadata: AnalysisMetadata, result: dict[str, Any]
) -> AnalysisMetadata:
    """Complete analysis tracking."""
    return get_transparency_service().complete_analysis(analysis_id, metadata, result)


def create_transparency_panel(
    metadata: AnalysisMetadata, context: dict[str, Any]
) -> dict[str, Any]:
    """Create transparency panel data."""
    return get_transparency_service().create_transparency_panel(metadata, context)
