"""
Context Threading — Intentional information flow with bookmarking.

# CONTEXT: Philosophy
  Information should flow through the system with intention preserved.
  When AI explores tangents, it leaves "breadcrumbs" — lightweight markers
  that track:
    - WHY we diverged (the intention)
    - WHAT we're exploring (the branch)
    - WHEN to return (the return condition)
    - WHAT to keep (compression metadata)

  This is not a separate bookmarking system. It's an optimization of the
  existing information pipeline that adds minimal overhead while maximizing
  context continuity.

# ARCHITECTURE:
  Input → [Intention Extraction] → [Compression] → [Branch Tracking] → AI
                                                      ↓
  Output ← [Learning] ← [Merge Check] ← [Return Condition] ← AI Response

  Each stage preserves what matters for the goal, discards what doesn't.

# USAGE:
  from context_threading import ContextThread, InformationPipeline

  # Start a thread
  thread = ContextThread(goal="Fix CTD on startup")

  # Branch off for exploration
  branch = thread.branch("Check SKSE version", return_when="version_found")

  # Compress with intention
  compressed = pipeline.compress(context, intention=thread.intention)

  # Auto-merge when return condition met
  if thread.should_merge(branch):
      merged = thread.merge(branch)
"""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class BranchStatus(Enum):
    """Status of a context branch."""

    ACTIVE = "active"
    MERGED = "merged"
    ABANDONED = "abandoned"
    RETURN_TRIGGERED = "return_triggered"


class CompressionLevel(Enum):
    """How aggressively to compress information."""

    NONE = "none"  # Keep everything
    LIGHT = "light"  # Remove redundancy only
    MODERATE = "moderate"  # Remove tangential info
    AGGRESSIVE = "aggressive"  # Keep only goal-relevant info


@dataclass
class Bookmark:
    """
    A lightweight bookmark marking a point in the information flow.

    Not a separate system — integrates with existing context management.
    """

    id: str
    thread_id: str
    branch_id: Optional[str]
    timestamp: float
    intention: str  # WHY we're here
    context_summary: str  # WHAT we're working with
    return_condition: Optional[str]  # WHEN to return
    compression_level: CompressionLevel
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "thread_id": self.thread_id,
            "branch_id": self.branch_id,
            "timestamp": self.timestamp,
            "intention": self.intention,
            "context_summary": self.context_summary[:200],  # Truncate for storage
            "return_condition": self.return_condition,
            "compression_level": self.compression_level.value,
            "metadata": self.metadata,
        }


@dataclass
class ContextThread:
    """
    Main thread of execution with branching support.

    Tracks the main goal and all branches that diverge from it.
    """

    id: str
    goal: str  # Primary intention
    created_at: float = field(default_factory=lambda: time.time())
    branches: dict[str, ContextBranch] = field(default_factory=dict)
    current_branch: Optional[str] = None
    bookmarks: list[Bookmark] = field(default_factory=list)
    compression_history: list[dict] = field(default_factory=list)

    def branch(self, intention: str, return_when: Optional[str] = None) -> ContextBranch:
        """Create a new branch for exploration."""
        branch_id = f"branch_{len(self.branches) + 1}_{int(time.time())}"
        branch = ContextBranch(
            id=branch_id,
            thread_id=self.id,
            intention=intention,
            parent_goal=self.goal,
            return_condition=return_when,
        )
        self.branches[branch_id] = branch
        self.current_branch = branch_id

        # Leave a bookmark
        self.add_bookmark(
            intention=intention,
            branch_id=branch_id,
            return_condition=return_when,
        )

        logger.info(f"Thread {self.id}: branched to {branch_id} — {intention}")
        return branch

    def add_bookmark(
        self,
        intention: str,
        branch_id: Optional[str] = None,
        return_condition: Optional[str] = None,
        compression_level: CompressionLevel = CompressionLevel.MODERATE,
        **metadata,
    ) -> Bookmark:
        """Add a bookmark at the current point."""
        bookmark = Bookmark(
            id=f"bm_{len(self.bookmarks) + 1}_{int(time.time())}",
            thread_id=self.id,
            branch_id=branch_id,
            timestamp=time.time(),
            intention=intention,
            context_summary=f"Branch: {branch_id}" if branch_id else "Main thread",
            return_condition=return_condition,
            compression_level=compression_level,
            metadata=metadata,
        )
        self.bookmarks.append(bookmark)
        return bookmark

    def should_merge(self, branch_id: str, current_context: str) -> bool:
        """Check if a branch should merge back to main thread."""
        branch = self.branches.get(branch_id)
        if not branch:
            return True

        # Check return condition
        if branch.return_condition:
            if branch.return_condition.lower() in current_context.lower():
                branch.status = BranchStatus.RETURN_TRIGGERED
                logger.info(f"Branch {branch_id}: return condition met")
                return True

        # Check if branch has been active too long (prevent infinite loops)
        if branch.status == BranchStatus.ACTIVE:
            age = time.time() - branch.created_at
            if age > 300:  # 5 minutes max
                logger.warning(f"Branch {branch_id}: auto-merging after timeout")
                return True

        return False

    def merge(self, branch_id: str) -> dict[str, Any]:
        """Merge a branch back into main thread."""
        branch = self.branches.get(branch_id)
        if not branch:
            return {"error": "Branch not found"}

        branch.status = BranchStatus.MERGED
        branch.merged_at = time.time()
        self.current_branch = None

        # Add merge bookmark
        self.add_bookmark(
            intention=f"Merged branch {branch_id}",
            metadata={
                "branch_intention": branch.intention,
                "branch_duration": branch.merged_at - branch.created_at,
            },
        )

        logger.info(f"Thread {self.id}: merged branch {branch_id}")
        return {
            "thread_id": self.id,
            "branch_id": branch_id,
            "merged": True,
            "duration": branch.merged_at - branch.created_at,
        }

    def get_compression_config(self) -> dict:
        """Get current compression configuration based on thread state."""
        if self.current_branch:
            # In a branch — compress more aggressively
            return {
                "level": CompressionLevel.AGGRESSIVE,
                "preserve": [self.branches[self.current_branch].intention],
                "max_context_chars": 8000,
            }
        else:
            # Main thread — moderate compression
            return {
                "level": CompressionLevel.MODERATE,
                "preserve": [self.goal],
                "max_context_chars": 12000,
            }

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "goal": self.goal,
            "created_at": self.created_at,
            "current_branch": self.current_branch,
            "branch_count": len(self.branches),
            "bookmarks": [b.to_dict() for b in self.bookmarks[-10:]],  # Last 10
            "compression_history": self.compression_history[-5:],  # Last 5
        }


@dataclass
class ContextBranch:
    """
    A branch diverging from the main thread.

    Tracks its own intention and when to return to main thread.
    """

    id: str
    thread_id: str
    intention: str
    parent_goal: str
    created_at: float = field(default_factory=lambda: time.time())
    merged_at: Optional[float] = None
    return_condition: Optional[str] = None
    status: BranchStatus = BranchStatus.ACTIVE
    compression_applied: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "thread_id": self.thread_id,
            "intention": self.intention,
            "parent_goal": self.parent_goal,
            "return_condition": self.return_condition,
            "status": self.status.value,
            "duration": (self.merged_at or time.time()) - self.created_at,
        }


class InformationPipeline:
    """
    Optimized information flow with intentional compression.

    Stages:
    1. Input → Extract intention
    2. Compress → Remove non-essential info
    3. Track → Add branch/bookmark metadata
    4. AI Processing
    5. Output → Learn from compression decisions
    """

    def __init__(self, thread: Optional[ContextThread] = None):
        self.thread = thread or ContextThread(id="default", goal="General assistance")
        self.compression_stats = {
            "total_processed": 0,
            "total_saved_chars": 0,
            "branches_created": 0,
            "merges_completed": 0,
        }

    def compress(
        self,
        context: str,
        intention: Optional[str] = None,
        level: Optional[CompressionLevel] = None,
    ) -> tuple[str, dict]:
        """
        Compress context with intention.

        Args:
            context: Raw context to compress
            intention: What we're trying to achieve (preserves goal-relevant info)
            level: Compression aggressiveness

        Returns:
            (compressed_context, stats)
        """
        if not context:
            return ("", {"original": 0, "compressed": 0, "saved": 0})

        intention = intention or self.thread.goal
        level = level or self.thread.get_compression_config()["level"]

        original_len = len(context)

        # Stage 1: Remove redundancy
        compressed = self._remove_redundancy(context)

        # Stage 2: Remove tangential info (based on intention)
        if level in (CompressionLevel.MODERATE, CompressionLevel.AGGRESSIVE):
            compressed = self._remove_tangential(compressed, intention)

        # Stage 3: Aggressive compression if requested
        if level == CompressionLevel.AGGRESSIVE:
            compressed = self._aggressive_compress(compressed, intention)

        compressed_len = len(compressed)
        saved = original_len - compressed_len

        # Track compression
        self.thread.compression_history.append(
            {
                "timestamp": time.time(),
                "original": original_len,
                "compressed": compressed_len,
                "saved": saved,
                "level": level.value,
                "intention": intention[:100],
            }
        )

        self.compression_stats["total_processed"] += 1
        self.compression_stats["total_saved_chars"] += saved

        stats = {
            "original": original_len,
            "compressed": compressed_len,
            "saved": saved,
            "ratio": f"{(compressed_len / original_len * 100):.1f}%" if original_len > 0 else "0%",
            "level": level.value,
        }

        logger.debug(f"Compressed: {original_len} → {compressed_len} ({stats['ratio']})")
        return (compressed, stats)

    def _remove_redundancy(self, context: str) -> str:
        """Remove duplicate lines and redundant information."""
        lines = context.splitlines()
        seen = set()
        unique_lines = []

        for line in lines:
            line_hash = hashlib.md5(line.strip().encode()).hexdigest()
            if line_hash not in seen:
                seen.add(line_hash)
                unique_lines.append(line)

        return "\n".join(unique_lines)

    def _remove_tangential(self, context: str, intention: str) -> str:
        """Remove information not relevant to the intention."""
        # Keep lines that mention intention keywords
        intention_keywords = set(intention.lower().split())

        lines = context.splitlines()
        relevant_lines = []

        for line in lines:
            line_lower = line.lower()
            # Keep if it mentions intention keywords
            if any(kw in line_lower for kw in intention_keywords if len(kw) > 3):
                relevant_lines.append(line)
            # Always keep errors, warnings, actions
            elif any(marker in line.lower() for marker in ["[error]", "[warning]", "→ action"]):
                relevant_lines.append(line)
            # Keep short lines (likely headers/structure)
            elif len(line) < 50:
                relevant_lines.append(line)

        return "\n".join(relevant_lines)

    def _aggressive_compress(self, context: str, intention: str) -> str:
        """Aggressive compression — keep only goal-critical info."""
        # Extract just the structure: conflicts and actions
        lines = context.splitlines()
        critical_lines = []

        for line in lines:
            # Keep conflict markers
            if any(marker in line for marker in ["[error]", "[warning]", "[info]"]):
                critical_lines.append(line)
            # Keep action items
            elif line.strip().startswith("→"):
                critical_lines.append(line)
            # Keep section headers
            elif line.startswith("#") or line.startswith("=" * 10):
                critical_lines.append(line)

        # Add intention reminder at top
        header = f"# Goal: {intention}\n# Compressed for focus\n\n"
        return header + "\n".join(critical_lines)

    def create_branch(self, intention: str, return_when: Optional[str] = None) -> ContextBranch:
        """Create a new branch in the current thread."""
        branch = self.thread.branch(intention, return_when)
        self.compression_stats["branches_created"] += 1
        return branch

    def check_merge(self, current_context: str) -> Optional[dict]:
        """Check if current branch should merge."""
        if not self.thread.current_branch:
            return None

        if self.thread.should_merge(self.thread.current_branch, current_context):
            result = self.thread.merge(self.thread.current_branch)
            self.compression_stats["merges_completed"] += 1
            return result

        return None

    def get_thread_summary(self) -> dict:
        """Get summary of current thread state."""
        return {
            "thread": self.thread.to_dict(),
            "stats": self.compression_stats,
            "active_branch": self.thread.current_branch,
        }


# Global pipeline instance (can be overridden per-request)
_global_pipeline: Optional[InformationPipeline] = None


def get_pipeline() -> InformationPipeline:
    """Get or create global pipeline instance."""
    global _global_pipeline
    if _global_pipeline is None:
        _global_pipeline = InformationPipeline()
    return _global_pipeline


def start_thread(goal: str) -> ContextThread:
    """Start a new context thread."""
    pipeline = get_pipeline()
    pipeline.thread = ContextThread(id=f"thread_{int(time.time())}", goal=goal)
    return pipeline.thread


def compress_context(
    context: str,
    intention: Optional[str] = None,
    level: str = "moderate",
) -> tuple[str, dict]:
    """Convenience function for compressing context."""
    pipeline = get_pipeline()
    compression_level = CompressionLevel[level.upper()]
    return pipeline.compress(context, intention, compression_level)


def branch_context(intention: str, return_when: Optional[str] = None) -> ContextBranch:
    """Convenience function for creating a branch."""
    pipeline = get_pipeline()
    return pipeline.create_branch(intention, return_when)
