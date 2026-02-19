"""
Reliability Weighting Service
Multi-dimensional source evaluation for scraped/researched information.

Dimensions:
1. Source Credibility - Who published this?
2. Content Freshness - When was this published/updated?
3. Community Validation - How has the community received this?
4. Technical Accuracy - Does this match known patterns?
5. Author Reputation - What's the author's track record?

Each dimension scores 0.0-1.0, combined into weighted reliability score.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ReliabilityScore:
    """Multi-dimensional reliability score for a source."""

    # Dimension scores (0.0-1.0)
    source_credibility: float = 0.5
    content_freshness: float = 0.5
    community_validation: float = 0.5
    technical_accuracy: float = 0.5
    author_reputation: float = 0.5

    # Metadata
    source_url: str = ""
    source_type: str = "unknown"  # nexus, reddit, forum, github, youtube
    game_version: str = ""
    last_updated: Optional[datetime] = None

    # Computed
    overall_score: float = field(default=0.0, init=False)
    confidence: float = field(default=0.0, init=False)
    flags: List[str] = field(default_factory=list)

    def compute(self) -> "ReliabilityScore":
        """Compute overall score and confidence."""
        # Weighted average (credibility + accuracy weighted higher)
        weights = {
            "source_credibility": 0.25,
            "content_freshness": 0.15,
            "community_validation": 0.20,
            "technical_accuracy": 0.25,
            "author_reputation": 0.15,
        }

        self.overall_score = (
            self.source_credibility * weights["source_credibility"]
            + self.content_freshness * weights["content_freshness"]
            + self.community_validation * weights["community_validation"]
            + self.technical_accuracy * weights["technical_accuracy"]
            + self.author_reputation * weights["author_reputation"]
        )

        # Confidence based on data availability
        data_points = sum(
            [
                1 if self.source_credibility != 0.5 else 0,
                1 if self.content_freshness != 0.5 else 0,
                1 if self.community_validation != 0.5 else 0,
                1 if self.technical_accuracy != 0.5 else 0,
                1 if self.author_reputation != 0.5 else 0,
            ]
        )
        self.confidence = min(1.0, data_points / 5.0)

        # Add flags for edge cases
        if self.content_freshness < 0.3:
            self.flags.append("outdated")
        if self.community_validation < 0.3:
            self.flags.append("unverified")
        if self.source_credibility < 0.3:
            self.flags.append("low_credibility")
        if self.overall_score >= 0.8:
            self.flags.append("highly_reliable")

        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/display."""
        return {
            "overall_score": round(self.overall_score, 3),
            "confidence": round(self.confidence, 3),
            "dimensions": {
                "source_credibility": round(self.source_credibility, 3),
                "content_freshness": round(self.content_freshness, 3),
                "community_validation": round(self.community_validation, 3),
                "technical_accuracy": round(self.technical_accuracy, 3),
                "author_reputation": round(self.author_reputation, 3),
            },
            "flags": self.flags,
            "source_url": self.source_url,
            "source_type": self.source_type,
            "game_version": self.game_version,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }


class ReliabilityWeighter:
    """Computes reliability scores for information sources."""

    # Source type base credibility scores
    SOURCE_BASE_SCORES = {
        "nexus_mods": 0.9,  # Official mod hosting
        "github": 0.8,  # Code repository
        "reddit_official": 0.75,  # r/skyrimmods, r/fo4mods
        "bethesda_forums": 0.7,  # Official forums
        "reddit_general": 0.5,  # General Reddit
        "youtube_verified": 0.7,  # Verified modding channels
        "youtube_general": 0.4,  # Random YouTube
        "forum_general": 0.4,  # General forums
        "unknown": 0.3,  # Unknown sources
    }

    # Author reputation thresholds
    AUTHOR_REPUTATION_THRESHOLDS = {
        "nexus_endorsements_high": 1000,  # 1000+ endorsements
        "nexus_endorsements_med": 100,  # 100+ endorsements
        "reddit_karma_high": 10000,  # 10k+ karma
        "reddit_karma_med": 1000,  # 1k+ karma
        "github_contributions_high": 50,  # 50+ contributions
        "github_contributions_med": 10,  # 10+ contributions
    }

    # Freshness decay (days)
    FRESHNESS_HALF_LIFE = {
        "mod_release": 180,  # 6 months
        "guide_tutorial": 365,  # 1 year
        "technical_fix": 90,  # 3 months
        "news_announcement": 30,  # 1 month
    }

    def score_source(self, source_data: Dict[str, Any]) -> ReliabilityScore:
        """
        Compute reliability score for a source.

        Args:
            source_data: Dictionary with source metadata:
                - url: Source URL
                - type: Source type (nexus, reddit, etc.)
                - published_date: When published
                - updated_date: When last updated
                - author: Author name/ID
                - endorsements: Number of endorsements/upvotes
                - views: View count
                - comments: Comment count
                - game_version: Game version this applies to
                - content_type: Type of content (mod, guide, fix, etc.)

        Returns:
            ReliabilityScore object
        """
        score = ReliabilityScore(
            source_url=source_data.get("url", ""),
            source_type=source_data.get("type", "unknown"),
            game_version=source_data.get("game_version", ""),
        )

        # 1. Source Credibility
        score.source_credibility = self._score_source_credibility(source_data)

        # 2. Content Freshness
        score.content_freshness = self._score_freshness(source_data)

        # 3. Community Validation
        score.community_validation = self._score_community_validation(source_data)

        # 4. Technical Accuracy (requires content analysis)
        score.technical_accuracy = self._score_technical_accuracy(source_data)

        # 5. Author Reputation
        score.author_reputation = self._score_author_reputation(source_data)

        # Set last updated
        updated = source_data.get("updated_date") or source_data.get("published_date")
        if updated:
            if isinstance(updated, str):
                try:
                    score.last_updated = datetime.fromisoformat(updated)
                except ValueError:
                    pass
            elif isinstance(updated, datetime):
                score.last_updated = updated

        return score.compute()

    def _score_source_credibility(self, data: Dict[str, Any]) -> float:
        """Score based on source type and domain."""
        source_type = data.get("type", "unknown").lower()

        # Base score from lookup table
        base_score = self.SOURCE_BASE_SCORES.get(source_type, 0.3)

        # Adjust for specific domains
        url = data.get("url", "").lower()
        if "nexusmods.com" in url:
            base_score = max(base_score, 0.85)
        elif "reddit.com/r/skyrimmods" in url or "reddit.com/r/fo4mods" in url:
            base_score = max(base_score, 0.75)
        elif "bethesda.net" in url:
            base_score = max(base_score, 0.7)

        # Adjust for HTTPS, custom domain penalties
        if not url.startswith("https://"):
            base_score *= 0.9

        return min(1.0, base_score)

    def _score_freshness(self, data: Dict[str, Any]) -> float:
        """Score based on content age and update frequency."""
        published = data.get("published_date")
        updated = data.get("updated_date")
        content_type = data.get("content_type", "mod_release")

        # Use updated date if available, else published
        reference_date = updated or published
        if not reference_date:
            return 0.5  # Unknown age

        if isinstance(reference_date, str):
            try:
                reference_date = datetime.fromisoformat(reference_date)
            except ValueError:
                return 0.5
        elif not isinstance(reference_date, datetime):
            return 0.5

        # Calculate age in days
        age_days = (datetime.now() - reference_date).days

        # Get half-life for content type
        half_life = self.FRESHNESS_HALF_LIFE.get(content_type, 180)

        # Exponential decay: score = 2^(-age/half_life)
        freshness = 2 ** (-age_days / half_life)

        return min(1.0, max(0.0, freshness))

    def _score_community_validation(self, data: Dict[str, Any]) -> float:
        """Score based on community engagement and reception."""
        endorsements = data.get("endorsements", 0)
        upvotes = data.get("upvotes", 0)
        likes = data.get("likes", 0)
        views = data.get("views", 0)
        comments = data.get("comments", 0)
        rating = data.get("rating", 0)  # 0-5 scale

        # Normalize endorsements (log scale)
        import math

        endorsement_score = min(1.0, math.log10(max(1, endorsements)) / 4)  # 10k = 1.0

        # Upvote/like ratio (if available)
        total_engagement = upvotes + likes
        engagement_score = min(1.0, math.log10(max(1, total_engagement)) / 4)

        # Rating score (5-star scale)
        rating_score = rating / 5.0 if rating else 0.5

        # Comment engagement (indicates discussion)
        comment_score = min(1.0, math.log10(max(1, comments)) / 3)  # 1k = 1.0

        # Weighted combination
        score = (
            endorsement_score * 0.4
            + engagement_score * 0.2
            + rating_score * 0.3
            + comment_score * 0.1
        )

        return min(1.0, max(0.0, score))

    def _score_technical_accuracy(self, data: Dict[str, Any]) -> float:
        """
        Score based on technical accuracy indicators.
        This requires content analysis - for now, use heuristics.
        """
        content = data.get("content", "")
        title = data.get("title", "")
        tags = data.get("tags", [])

        # Positive indicators
        positive_signals = 0
        negative_signals = 0

        # Has code blocks or technical details
        if "```" in content or "code" in tags:
            positive_signals += 1

        # Has version numbers
        import re

        if re.search(r"\d+\.\d+\.\d+", content):
            positive_signals += 1

        # Has links to official sources
        if "nexusmods.com" in content or "github.com" in content:
            positive_signals += 1

        # Has screenshots/evidence
        if data.get("has_screenshots") or data.get("has_images"):
            positive_signals += 1

        # Marked as verified/solution
        if data.get("is_solution") or data.get("verified"):
            positive_signals += 2

        # Negative: clickbait title
        if any(word in title.lower() for word in ["amazing", "incredible", "must have"]):
            negative_signals += 1

        # Negative: outdated game version mentioned
        if data.get("game_version"):
            if any(old in data["game_version"] for old in ["1.5.", "1.4."]):
                negative_signals += 1

        # Calculate score
        total_signals = positive_signals + negative_signals + 1  # +1 to avoid division by zero
        score = (positive_signals + 0.5) / (total_signals + 1)

        return min(1.0, max(0.0, score))

    def _score_author_reputation(self, data: Dict[str, Any]) -> float:
        """Score based on author's track record."""
        author = data.get("author", "")
        author_endorsements = data.get("author_endorsements", 0)
        author_posts = data.get("author_posts", 0)
        author_karma = data.get("author_karma", 0)

        import math

        # Author endorsement score
        endorsement_score = min(1.0, math.log10(max(1, author_endorsements)) / 4)

        # Post count score (experience)
        post_score = min(1.0, math.log10(max(1, author_posts)) / 3)

        # Karma score
        karma_score = min(1.0, math.log10(max(1, author_karma)) / 5)

        # Known author bonus
        known_authors = ["arthmoor", "enai siaion", "meh321", "doubleyou", "ruvyn"]
        known_bonus = 0.2 if any(known in author.lower() for known in known_authors) else 0

        score = endorsement_score * 0.4 + post_score * 0.3 + karma_score * 0.1 + known_bonus

        return min(1.0, max(0.0, score))

    def filter_by_reliability(
        self, sources: List[Dict[str, Any]], min_score: float = 0.5, min_confidence: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Filter sources by reliability score.

        Args:
            sources: List of source data dictionaries
            min_score: Minimum overall score (0.0-1.0)
            min_confidence: Minimum confidence (0.0-1.0)

        Returns:
            Filtered list of sources with reliability scores added
        """
        filtered = []
        for source in sources:
            score = self.score_source(source)
            if score.overall_score >= min_score and score.confidence >= min_confidence:
                source["reliability_score"] = score.to_dict()
                filtered.append(source)
        return filtered


# Singleton instance
_reliability_weighter = None


def get_reliability_weighter() -> ReliabilityWeighter:
    """Get or create reliability weighter singleton."""
    global _reliability_weighter
    if _reliability_weighter is None:
        _reliability_weighter = ReliabilityWeighter()
    return _reliability_weighter
