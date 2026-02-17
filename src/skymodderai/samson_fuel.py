"""
Structural fuel extraction from LOOT data.

Privacy: No PII, no user mod lists. Only public LOOT masterlist structure.
Extracts graph structure (dependencies, conflicts, patches) for research.
See docs/fuel_spec.md.

Usage:
  from samson_fuel import extract_fuel, write_fuel
  fuel = extract_fuel(parser)
  write_fuel(fuel)  # writes to data/fuel/
"""

import json
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Export dir (gitignored). Generic name.
FUEL_DIR = Path(__file__).parent / "data" / "fuel"


def _norm(s: str) -> str:
    """Normalize mod name for lookup (matches LOOT parser)."""
    if not s:
        return ""
    return s.lower().replace(".esp", "").replace(".esm", "").replace(".esl", "").strip()


def _compute_dependency_depth(mod_database: Dict[str, Any], max_depth: int = 10) -> float:
    """
    Average depth of requirement chain. A requires B requires C → depth 2 for A.
    BFS from each mod with requirements. Returns mean depth.
    """
    depths = []
    db_by_norm = {_norm(k): k for k in mod_database.keys()}

    for clean_name, info in mod_database.items():
        reqs = getattr(info, "requirements", None) or []
        if not reqs:
            continue
        depth = 0
        frontier = {_norm(r) for r in reqs if _norm(r) in db_by_norm}
        seen = {clean_name} | frontier
        while frontier and depth < max_depth:
            next_frontier = set()
            for n in frontier:
                key = db_by_norm.get(n)
                if not key:
                    continue
                child_info = mod_database.get(key)
                if not child_info:
                    continue
                child_reqs = getattr(child_info, "requirements", None) or []
                for r in child_reqs:
                    rn = _norm(r)
                    if rn in db_by_norm and rn not in seen:
                        seen.add(rn)
                        next_frontier.add(rn)
            frontier = next_frontier
            if frontier:
                depth += 1
        depths.append(depth)
    return sum(depths) / len(depths) if depths else 0.0


def extract_fuel(
    parser: Any,
    game: Optional[str] = None,
    include_top_pairs: int = 20,
) -> Dict[str, Any]:
    """
    Extract structural fuel from a LOOTParser. No user data.

    Args:
        parser: LOOTParser instance with mod_database populated
        game: Game id (default: parser.game)
        include_top_pairs: Max incompatible pairs to include (for schema size)

    Returns:
        Fuel dict in Samson schema. No PII.
    """
    db = getattr(parser, "mod_database", {})
    game_id = game or getattr(parser, "game", "skyrimse")

    # Edge counts
    req_count = 0
    incomp_count = 0
    patch_count = 0
    load_after_count = 0
    load_before_count = 0
    incompatible_pairs: List[tuple] = []

    for name, info in db.items():
        reqs = getattr(info, "requirements", None) or []
        incomps = getattr(info, "incompatibilities", None) or []
        load_after = getattr(info, "load_after", None) or []
        load_before = getattr(info, "load_before", None) or []
        patches = getattr(info, "patches", None) or []

        req_count += len(reqs)
        incomp_count += len(incomps)
        load_after_count += len(load_after)
        load_before_count += len(load_before)
        patch_count += len(patches)

        for inc in incomps:
            inc_name = inc if isinstance(inc, str) else getattr(inc, "name", str(inc))
            if name and inc_name:
                pair = tuple(sorted([name, inc_name]))
                incompatible_pairs.append(pair)

    # Dedupe pairs (A-B and B-A)
    pair_counts = defaultdict(int)
    for p in incompatible_pairs:
        pair_counts[p] += 1
    top_pairs = sorted(pair_counts.items(), key=lambda x: -x[1])[:include_top_pairs]
    top_pair_names = [[a, b] for (a, b), _ in top_pairs]

    # Cooperation ratio: patches / (incompatibilities + 1) to avoid div by zero
    cooperation_ratio = patch_count / (incomp_count + 1) if incomp_count >= 0 else 0.0

    # Dependency depth
    try:
        avg_depth = _compute_dependency_depth(db)
    except Exception as e:
        logger.debug(f"Dependency depth computation failed: {e}")
        avg_depth = 0.0

    fuel = {
        "source": "modcheck",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "game": game_id,
        "structure": {
            "node_count": len(db),
            "edge_types": {
                "requirement": req_count,
                "incompatible": incomp_count,
                "patch": patch_count,
                "load_after": load_after_count,
                "load_before": load_before_count,
            },
            "failure_modes": [
                "missing_requirement",
                "incompatible",
                "load_order_violation",
                "dirty_edits",
                "patch_available",
                "unknown_mod",
            ],
            "cooperation_ratio": round(cooperation_ratio, 4),
            "avg_dependency_depth": round(avg_depth, 2),
        },
        "aggregate": {
            "top_incompatible_pairs": top_pair_names,
        },
    }
    return fuel


def write_fuel(fuel: Dict[str, Any], subdir: Optional[str] = None) -> Path:
    """
    Write fuel to data/fuel/. Creates dir if needed.
    Returns path written. Caller responsible for not committing PII.
    """
    FUEL_DIR.mkdir(parents=True, exist_ok=True)
    if subdir:
        (FUEL_DIR / subdir).mkdir(parents=True, exist_ok=True)
    out_dir = FUEL_DIR / subdir if subdir else FUEL_DIR
    game = fuel.get("game", "unknown")
    ts = fuel.get("timestamp", "").replace(":", "-").replace(".", "-")[:19]
    fname = f"{game}_{ts}.json"
    path = out_dir / fname
    with open(path, "w", encoding="utf-8") as f:
        json.dump(fuel, f, indent=2)
    logger.info(f"Fuel written: {path}")
    return path
