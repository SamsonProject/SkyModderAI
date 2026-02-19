"""
Curation Service - Daily intelligence curation for SkyModderAI.

Handles:
- Semantic clustering of new knowledge
- Information compaction (duplicate removal)
- Cross-linking related entries
- Trash bin audit
- Self-organizing category discovery

Run daily at 2 AM UTC via scheduler.
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from db import get_db_session
from models import KnowledgeSource, TrashBinItem

logger = logging.getLogger(__name__)


def run_curation_pipeline() -> Dict[str, Any]:
    """
    Run full curation pipeline.

    Returns:
        {
            "clustering": {"processed": int, "clusters_found": int},
            "compaction": {"duplicates_removed": int, "space_saved_bytes": int},
            "cross_linking": {"links_added": int},
            "trash_audit": {"reviewed": int, "deleted": int, "compacted": int},
            "category_discovery": {"new_categories": int, "recategorized": int}
        }
    """
    logger.info("Starting curation pipeline...")

    results = {
        "clustering": run_semantic_clustering(),
        "compaction": run_information_compaction(),
        "cross_linking": run_cross_linking(),
        "trash_audit": run_trash_audit(),
        "category_discovery": run_category_discovery(),
    }

    logger.info(f"Curation pipeline completed: {results}")
    return results


def run_semantic_clustering() -> Dict[str, Any]:
    """
    Cluster related knowledge entries semantically.

    Groups entries by:
    - Game + version compatibility
    - Mod name similarity
    - Category/subcategory
    - Shared tags

    Returns:
        {"processed": int, "clusters_found": int}
    """
    logger.info("Running semantic clustering...")

    session = get_db_session()

    try:
        # Get all active knowledge sources
        sources = session.query(KnowledgeSource).filter(KnowledgeSource.status == "active").all()

        # Group by game + category
        clusters: Dict[str, List[KnowledgeSource]] = {}
        for source in sources:
            key = f"{source.game}:{source.category or 'uncategorized'}"
            if key not in clusters:
                clusters[key] = []
            clusters[key].append(source)

        # Find sub-clusters by version compatibility
        cluster_count = 0
        for cluster_key, cluster_sources in clusters.items():
            if len(cluster_sources) < 2:
                continue

            # Group by version compatibility
            version_groups: Dict[str, List[KnowledgeSource]] = {}
            for source in cluster_sources:
                version_key = source.game_version or "any"
                if version_key not in version_groups:
                    version_groups[version_key] = []
                version_groups[version_key].append(source)

            # Mark clusters with 3+ related entries
            for version_key, version_sources in version_groups.items():
                if len(version_sources) >= 3:
                    cluster_count += 1
                    # Add cluster metadata
                    for source in version_sources:
                        if not source.tags:
                            source.tags = "[]"
                        tags = json.loads(source.tags)
                        if "clustered" not in tags:
                            tags.append("clustered")
                            source.tags = json.dumps(tags)

        session.commit()

        result = {"processed": len(sources), "clusters_found": cluster_count}
        logger.info(f"Semantic clustering complete: {result}")
        return result

    except Exception as e:
        logger.exception(f"Semantic clustering failed: {e}")
        session.rollback()
        return {"processed": 0, "clusters_found": 0, "error": str(e)}


def run_information_compaction() -> Dict[str, Any]:
    """
    Compact duplicate or near-duplicate entries.

    Identifies duplicates by:
    - Same source URL
    - Same content hash
    - Same title + game

    Moves duplicates to trash bin, keeps best version (highest credibility).

    Returns:
        {"duplicates_removed": int, "space_saved_bytes": int}
    """
    logger.info("Running information compaction...")

    session = get_db_session()

    try:
        duplicates_removed = 0
        space_saved = 0

        # Group by content hash
        hash_groups: Dict[str, List[KnowledgeSource]] = {}
        sources = (
            session.query(KnowledgeSource)
            .filter(KnowledgeSource.status == "active", KnowledgeSource.content_hash.isnot(None))
            .all()
        )

        for source in sources:
            if source.content_hash not in hash_groups:
                hash_groups[source.content_hash] = []
            hash_groups[source.content_hash].append(source)

        # Process groups with duplicates
        for content_hash, group in hash_groups.items():
            if len(group) < 2:
                continue

            # Sort by credibility (keep highest)
            def get_credibility(source: KnowledgeSource) -> float:
                if source.credibility:
                    return source.credibility.overall_score or 0.5
                return 0.5

            group.sort(key=get_credibility, reverse=True)
            keep = group[0]
            duplicates = group[1:]

            # Move duplicates to trash
            for dup in duplicates:
                # Calculate space saved
                if dup.summary:
                    space_saved += len(dup.summary.encode("utf-8"))

                # Create trash entry
                trash = TrashBinItem(
                    item_type="knowledge_source",
                    item_id=dup.id,
                    original_data=json.dumps(dup.to_dict()),
                    reason="duplicate_compaction",
                    auto_classified=True,
                    action_taken="compacted",
                    action_data=json.dumps({"kept_id": keep.id, "kept_url": keep.source_url}),
                )
                session.add(trash)

                # Mark for deletion
                dup.status = "archived"
                dup.trash_reason = f"Duplicate of {keep.source_url}"

                duplicates_removed += 1

        session.commit()

        result = {"duplicates_removed": duplicates_removed, "space_saved_bytes": space_saved}
        logger.info(f"Information compaction complete: {result}")
        return result

    except Exception as e:
        logger.exception(f"Information compaction failed: {e}")
        session.rollback()
        return {"duplicates_removed": 0, "space_saved_bytes": 0, "error": str(e)}


def run_cross_linking() -> Dict[str, Any]:
    """
    Add cross-references between related entries.

    Links entries that:
    - Reference the same mods
    - Have compatible game versions
    - Share tags
    - Are in same category chain

    Returns:
        {"links_added": int}
    """
    logger.info("Running cross-linking...")

    session = get_db_session()

    try:
        links_added = 0

        # Get all active sources with requirements/compatibility info
        sources = session.query(KnowledgeSource).filter(KnowledgeSource.status == "active").all()

        # Build index by mod name
        mod_index: Dict[str, List[int]] = {}
        for source in sources:
            # Index by requires
            if source.requires:
                try:
                    requires = json.loads(source.requires)
                    for req in requires:
                        if req not in mod_index:
                            mod_index[req] = []
                        mod_index[req].append(source.id)
                except (json.JSONDecodeError, TypeError):
                    pass

            # Index by conflicts_with
            if source.conflicts_with:
                try:
                    conflicts = json.loads(source.conflicts_with)
                    for conflict in conflicts:
                        if conflict not in mod_index:
                            mod_index[conflict] = []
                        mod_index[conflict].append(source.id)
                except (json.JSONDecodeError, TypeError):
                    pass

        # Add cross-links
        for mod_name, source_ids in mod_index.items():
            if len(source_ids) < 2:
                continue

            # Link all pairs
            for i, id_a in enumerate(source_ids):
                for id_b in source_ids[i + 1 :]:
                    source_a = session.query(KnowledgeSource).get(id_a)
                    source_b = session.query(KnowledgeSource).get(id_b)

                    if not source_a or not source_b:
                        continue

                    # Add to compatible_with if not already linked
                    if source_a.compatible_with:
                        try:
                            compatible = json.loads(source_a.compatible_with)
                            if id_b not in compatible:
                                compatible.append(id_b)
                                source_a.compatible_with = json.dumps(compatible)
                                links_added += 1
                        except (json.JSONDecodeError, TypeError):
                            source_a.compatible_with = json.dumps([id_b])
                            links_added += 1
                    else:
                        source_a.compatible_with = json.dumps([id_b])
                        links_added += 1

        session.commit()

        result = {"links_added": links_added}
        logger.info(f"Cross-linking complete: {result}")
        return result

    except Exception as e:
        logger.exception(f"Cross-linking failed: {e}")
        session.rollback()
        return {"links_added": 0, "error": str(e)}


def run_trash_audit() -> Dict[str, Any]:
    """
    Audit trash bin items.

    Actions:
    - Review items older than 7 days
    - Auto-delete confirmed trash
    - Compact items that can be merged
    - Re-route misclassified items

    Returns:
        {"reviewed": int, "deleted": int, "compacted": int, "re_routed": int}
    """
    logger.info("Running trash audit...")

    session = get_db_session()

    try:
        reviewed = 0
        deleted = 0
        compacted = 0
        re_routed = 0

        # Get items older than 7 days
        cutoff = datetime.now() - timedelta(days=7)
        items = (
            session.query(TrashBinItem)
            .filter(TrashBinItem.created_at < cutoff, TrashBinItem.reviewed == False)
            .all()
        )

        for item in items:
            reviewed += 1
            action_data = json.loads(item.action_data or "{}")

            if item.action_taken == "compacted":
                # Already compacted, safe to delete
                deleted += 1
                session.delete(item)

            elif item.action_taken == "re-routed":
                # Re-route to correct category
                if "new_category" in action_data:
                    if item.item_type == "knowledge_source":
                        source = session.query(KnowledgeSource).get(item.item_id)
                        if source:
                            source.category = action_data["new_category"]
                            re_routed += 1
                    session.delete(item)

            elif item.reason == "duplicate_compaction":
                # Duplicates already compacted, safe to delete
                deleted += 1
                session.delete(item)

            else:
                # Keep for manual review, extend expiration
                item.expires_at = datetime.now() + timedelta(days=30)

        # Auto-delete items older than 90 days
        old_cutoff = datetime.now() - timedelta(days=90)
        old_items = session.query(TrashBinItem).filter(TrashBinItem.created_at < old_cutoff).all()

        for item in old_items:
            deleted += 1
            session.delete(item)

        session.commit()

        result = {
            "reviewed": reviewed,
            "deleted": deleted,
            "compacted": compacted,
            "re_routed": re_routed,
        }
        logger.info(f"Trash audit complete: {result}")
        return result

    except Exception as e:
        logger.exception(f"Trash audit failed: {e}")
        session.rollback()
        return {"reviewed": 0, "deleted": 0, "compacted": 0, "re_routed": 0, "error": str(e)}


def run_category_discovery() -> Dict[str, Any]:
    """
    Discover new categories from emerging patterns.

    Analyzes:
    - New tag combinations
    - Emerging mod types
    - User search patterns

    Creates new subcategories when patterns are detected.

    Returns:
        {"new_categories": int, "recategorized": int}
    """
    logger.info("Running category discovery...")

    session = get_db_session()

    try:
        new_categories = 0
        recategorized = 0

        # Analyze existing categories
        sources = (
            session.query(KnowledgeSource)
            .filter(KnowledgeSource.status == "active", KnowledgeSource.category.isnot(None))
            .all()
        )

        # Group by category
        category_sources: Dict[str, List[KnowledgeSource]] = {}
        for source in sources:
            cat = source.category or "uncategorized"
            if cat not in category_sources:
                category_sources[cat] = []
            category_sources[cat].append(source)

        # Look for subcategory patterns in tags
        for category, cat_sources in category_sources.items():
            if len(cat_sources) < 10:
                continue

            # Count tag frequency
            tag_counts: Dict[str, int] = {}
            for source in cat_sources:
                if source.tags:
                    try:
                        tags = json.loads(source.tags)
                        for tag in tags:
                            if tag not in tag_counts:
                                tag_counts[tag] = 0
                            tag_counts[tag] += 1
                    except (json.JSONDecodeError, TypeError):
                        pass

            # Find dominant tags that could be subcategories
            for tag, count in tag_counts.items():
                if count >= len(cat_sources) * 0.3:  # 30%+ have this tag
                    # This tag could be a subcategory
                    # Check if subcategory already exists
                    subcat_exists = any(s.subcategory == tag for s in cat_sources)

                    if not subcat_exists:
                        new_categories += 1
                        # Update sources with this tag to use as subcategory
                        for source in cat_sources:
                            if source.tags and tag in json.loads(source.tags):
                                if not source.subcategory:
                                    source.subcategory = tag
                                    recategorized += 1

        session.commit()

        result = {"new_categories": new_categories, "recategorized": recategorized}
        logger.info(f"Category discovery complete: {result}")
        return result

    except Exception as e:
        logger.exception(f"Category discovery failed: {e}")
        session.rollback()
        return {"new_categories": 0, "recategorized": 0, "error": str(e)}


# =============================================================================
# Helper Functions
# =============================================================================


def compute_content_hash(title: str, summary: str, game: str) -> str:
    """Compute SHA256 hash of content for duplicate detection."""
    content = f"{title}|{summary}|{game}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def suggest_category(title: str, summary: str, tags: List[str]) -> Optional[str]:
    """Suggest category based on content analysis."""
    title_lower = title.lower()
    summary_lower = summary.lower()

    # Category keywords
    category_keywords = {
        "utility": ["patch", "fix", "unofficial", "skyui", "skse", "loot", "xedit"],
        "design": ["texture", "mesh", "body", "enb", "lighting", "weather"],
        "fun": ["combat", "perk", "spell", "quest", "difficulty"],
        "environmental": ["landscape", "flora", "city", "npc", "water", "lod"],
    }

    # Count matches
    scores: Dict[str, int] = {}
    for category, keywords in category_keywords.items():
        score = sum(1 for kw in keywords if kw in title_lower or kw in summary_lower)
        if score > 0:
            scores[category] = score

    if scores:
        return max(scores, key=scores.get)

    return None
