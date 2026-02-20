"""
Deviation Labeling Service - Identifies non-standard modding approaches.

Analyzes knowledge sources and flags approaches that:
- Deviate from community consensus
- Use experimental techniques
- Conflict with established best practices
- Are novel but unverified

This helps users understand risk levels and make informed decisions.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

from db import get_db_session
from models import KnowledgeSource

logger = logging.getLogger(__name__)


def analyze_deviations() -> dict[str, Any]:
    """
    Analyze all knowledge sources for deviation flags.

    Returns:
        {
            "analyzed": int,
            "deviations_found": int,
            "high_risk": int,
            "medium_risk": int,
            "low_risk": int
        }
    """
    logger.info("Starting deviation analysis...")

    session = get_db_session()

    try:
        # Get all active knowledge sources
        sources = session.query(KnowledgeSource).filter(KnowledgeSource.status == "active").all()

        analyzed = 0
        deviations_found = 0
        high_risk = 0
        medium_risk = 0
        low_risk = 0

        for source in sources:
            analyzed += 1

            # Analyze for deviations
            deviation_flags, risk_level = analyze_source_deviations(source)

            if deviation_flags:
                deviations_found += 1
                source.deviation_flags = json.dumps(deviation_flags)

                if risk_level == "high":
                    high_risk += 1
                    source.is_standard_approach = False
                elif risk_level == "medium":
                    medium_risk += 1
                else:
                    low_risk += 1

        session.commit()

        result = {
            "analyzed": analyzed,
            "deviations_found": deviations_found,
            "high_risk": high_risk,
            "medium_risk": medium_risk,
            "low_risk": low_risk,
        }

        logger.info(f"Deviation analysis complete: {result}")
        return result

    except Exception as e:
        logger.exception(f"Deviation analysis failed: {e}")
        session.rollback()
        return {
            "analyzed": 0,
            "deviations_found": 0,
            "high_risk": 0,
            "medium_risk": 0,
            "low_risk": 0,
            "error": str(e),
        }


def analyze_source_deviations(source: KnowledgeSource) -> tuple[list[str], str]:
    """
    Analyze a single knowledge source for deviations.

    Args:
        source: KnowledgeSource to analyze

    Returns:
        (deviation_flags, risk_level)
        - deviation_flags: List of flags like ["experimental", "conflicts_consensus"]
        - risk_level: "high", "medium", "low", or None
    """
    flags = []
    risk_score = 0

    # Get credibility score for context
    credibility = source.credibility
    cred_score = credibility.overall_score if credibility else 0.5

    # 1. Check for experimental keywords
    experimental_keywords = [
        "experimental",
        "beta",
        "wip",
        "work in progress",
        "unstable",
        "use at own risk",
        "not recommended",
        "prototype",
        "alpha",
        "testing",
    ]

    text = f"{source.title} {source.summary}".lower()
    for keyword in experimental_keywords:
        if keyword in text:
            flags.append("experimental")
            risk_score += 2
            break

    # 2. Check for non-standard techniques
    nonstandard_patterns = [
        (r"script\s*extender\s+hook", "skse_hook"),
        (r"memory\s+patch", "memory_patch"),
        (r"dll\s+injection", "dll_injection"),
        (r"engine\s+override", "engine_override"),
        (r"unofficial\s+fix", "unofficial_fix"),
        (r"hack", "code_hack"),
        (r"workaround", "workaround"),
    ]

    for pattern, flag_name in nonstandard_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            flags.append(f"non_standard_{flag_name}")
            risk_score += 1

    # 3. Check for conflicts with consensus
    # If multiple sources exist for same topic with different approaches
    conflicting_approaches = check_conflicting_approaches(source)
    if conflicting_approaches:
        flags.append("conflicts_consensus")
        risk_score += 2

    # 4. Check for novel techniques (new, unverified)
    if is_novel_technique(source):
        flags.append("novel_technique")
        risk_score += 1

    # 5. Check for version-specific issues
    if has_version_issues(source):
        flags.append("version_sensitive")
        risk_score += 1

    # 6. Low credibility penalty
    if cred_score < 0.4:
        flags.append("low_credibility")
        risk_score += 2
    elif cred_score < 0.6:
        flags.append("moderate_credibility")
        risk_score += 1

    # 7. Check for missing verification
    if not source.credibility or not source.credibility.last_verified:
        flags.append("unverified")
        risk_score += 1

    # Determine risk level
    if risk_score >= 5:
        risk_level = "high"
    elif risk_score >= 3:
        risk_level = "medium"
    elif risk_score >= 1:
        risk_level = "low"
    else:
        risk_level = None

    # Remove duplicates
    flags = list(set(flags))

    return flags, risk_level


def check_conflicting_approaches(source: KnowledgeSource) -> bool:
    """
    Check if this source conflicts with established consensus.

    Looks for other sources on same topic with different approaches.
    """
    session = get_db_session()

    try:
        # Find similar sources in same category
        similar = (
            session.query(KnowledgeSource)
            .filter(
                KnowledgeSource.game == source.game,
                KnowledgeSource.category == source.category,
                KnowledgeSource.id != source.id,
                KnowledgeSource.status == "active",
            )
            .all()
        )

        if not similar:
            return False

        # Check for conflicting recommendations
        source_methods = extract_methods(source.summary)

        conflicts = 0
        for other in similar:
            other_methods = extract_methods(other.summary)

            # If methods are different, count as conflict
            if source_methods and other_methods:
                if not source_methods.intersection(other_methods):
                    conflicts += 1

        # Conflict if >50% of similar sources use different methods
        return conflicts > len(similar) * 0.5

    except Exception as e:
        logger.debug(f"Error checking conflicting approaches: {e}")
        return False


def extract_methods(text: str) -> set:
    """Extract method keywords from text."""
    methods = set()

    method_keywords = [
        "install",
        "download",
        "enable",
        "disable",
        "patch",
        "merge",
        "load order",
        "skse",
        "enb",
        "replacer",
        "modular",
        "manual",
        "automatic",
        "mo2",
        "vortex",
    ]

    text_lower = text.lower()
    for keyword in method_keywords:
        if keyword in text_lower:
            methods.add(keyword)

    return methods


def is_novel_technique(source: KnowledgeSource) -> bool:
    """
    Check if this describes a novel (new) technique.

    Novel techniques are:
    - Recently created (<30 days)
    - Low community validation
    - Unique approach
    """
    if not source.created_at:
        return False

    from datetime import datetime, timedelta

    # Check age
    age = datetime.now() - source.created_at
    if age > timedelta(days=30):
        return False

    # Check community validation
    credibility = source.credibility
    if not credibility:
        return True

    if credibility.community_validation < 0.3:
        return True

    return False


def has_version_issues(source: KnowledgeSource) -> bool:
    """
    Check if this has version-specific compatibility issues.

    Version issues include:
    - Only works with specific game version
    - Known to break with certain versions
    - Requires version-specific patches
    """
    if not source.game_version:
        return False

    version_keywords = [
        "only works with",
        "requires version",
        "broken in",
        "compatible with",
        "version specific",
        "ae only",
        "se only",
        "1.6.1170",
        "1.5.97",
        "next-gen",
    ]

    text = f"{source.title} {source.summary}".lower()
    for keyword in version_keywords:
        if keyword in text:
            return True

    return False


def get_deviation_warning(deviation_flags: list[str]) -> Optional[dict[str, Any]]:
    """
    Generate user-facing warning for deviation flags.

    Returns:
        {
            "level": "high"|"medium"|"low",
            "message": str,
            "details": [...]
        }
    """
    if not deviation_flags:
        return None

    # Determine overall risk level
    high_risk_flags = {"experimental", "conflicts_consensus", "low_credibility"}
    medium_risk_flags = {"novel_technique", "version_sensitive", "unverified"}

    flags_set = set(deviation_flags)

    if flags_set.intersection(high_risk_flags):
        level = "high"
    elif flags_set.intersection(medium_risk_flags):
        level = "medium"
    else:
        level = "low"

    # Generate message
    messages = {
        "experimental": "This mod uses experimental features that may be unstable.",
        "non_standard_skse_hook": "Uses non-standard SKSE hooking technique.",
        "non_standard_memory_patch": "Patches game memory - may cause crashes.",
        "non_standard_dll_injection": "Injects DLL files - use with caution.",
        "non_standard_engine_override": "Overrides engine behavior - may conflict with other mods.",
        "non_standard_unofficial_fix": "Unofficial fix - not author-approved.",
        "non_standard_code_hack": "Uses code hacks - potential stability issues.",
        "non_standard_workaround": "Workaround solution - not a proper fix.",
        "conflicts_consensus": "Conflicts with community-recommended approaches.",
        "novel_technique": "New technique - limited community verification.",
        "version_sensitive": "Version-specific - may not work with your game version.",
        "low_credibility": "Low credibility source - verify before using.",
        "moderate_credibility": "Moderately verified - proceed with caution.",
        "unverified": "Not yet verified by community.",
    }

    details = []
    for flag in deviation_flags:
        if flag in messages:
            details.append({"flag": flag, "message": messages[flag]})

    # Overall message
    level_messages = {
        "high": "⚠️ HIGH RISK: This solution uses non-standard or experimental approaches.",
        "medium": "⚠️ MEDIUM RISK: This solution has some unverified elements.",
        "low": "ℹ️ LOW RISK: Minor concerns - generally safe but review details.",
    }

    return {
        "level": level,
        "message": level_messages.get(level, "ℹ️ Review recommended."),
        "details": details,
    }


def format_deviation_for_ui(deviation_flags: list[str]) -> Optional[str]:
    """
    Format deviation flags for UI display.

    Returns HTML/Markdown snippet for display.
    """
    if not deviation_flags:
        return None

    warning = get_deviation_warning(deviation_flags)
    if not warning:
        return None

    # Format as markdown
    md = f"\n\n> **{warning['message']}**\n\n"

    if warning["details"]:
        md += "**Details:**\n"
        for detail in warning["details"]:
            md += f"- {detail['message']}\n"

    md += "\n"
    return md


def batch_label_deviations(source_ids: list[int]) -> dict[str, Any]:
    """
    Batch label multiple sources for deviations.

    Args:
        source_ids: List of KnowledgeSource IDs to label

    Returns:
        {
            "processed": int,
            "labeled": int,
            "errors": int
        }
    """
    session = get_db_session()

    try:
        processed = 0
        labeled = 0
        errors = 0

        for source_id in source_ids:
            try:
                source = session.query(KnowledgeSource).get(source_id)
                if not source:
                    errors += 1
                    continue

                flags, _ = analyze_source_deviations(source)
                if flags:
                    source.deviation_flags = json.dumps(flags)
                    labeled += 1

                processed += 1

            except Exception as e:
                logger.debug(f"Error labeling source {source_id}: {e}")
                errors += 1

        session.commit()

        return {"processed": processed, "labeled": labeled, "errors": errors}

    except Exception as e:
        logger.exception(f"Batch labeling failed: {e}")
        session.rollback()
        return {"processed": 0, "labeled": 0, "errors": 1, "error": str(e)}
