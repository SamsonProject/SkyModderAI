"""
SkyModderAI - Search Service

Handles mod search and query operations.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from exceptions import InvalidGameIDError, ValidationError
from search_engine import get_search_engine
from security_utils import validate_game_id

logger = logging.getLogger(__name__)


class SearchService:
    """Service for search operations."""

    def __init__(self, game: str = "skyrimse") -> None:
        """
        Initialize search service.

        Args:
            game: Game ID to search in
        """
        try:
            self.game = validate_game_id(game)
        except ValueError as e:
            raise InvalidGameIDError(str(e))

    def search(
        self,
        query: str,
        limit: int = 10,
        for_ai: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Search for mods.

        Args:
            query: Search query
            limit: Max results (default: 10, max: 50)
            for_ai: Include AI context

        Returns:
            List of search results

        Raises:
            ValidationError: If query invalid
        """
        if not query or not query.strip():
            raise ValidationError("Search query is required")

        query = query.strip()
        if len(query) < 2:
            raise ValidationError("Search query too short (min 2 characters)")

        # Sanitize limit
        limit = max(1, min(limit, 50))

        # Perform search
        se = get_search_engine(self.game)
        results = se.search(query, limit=limit, for_ai=for_ai)

        logger.info(f"Search: '{query}' -> {len(results)} results")

        return results

    def search_requirements(
        self,
        mod_name: str,
        include_patches: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Search for mod requirements.

        Args:
            mod_name: Mod name
            include_patches: Include patches

        Returns:
            List of required mods
        """
        se = get_search_engine(self.game)
        mod_info = se.get_mod_info(mod_name)

        if not mod_info:
            return []

        requirements = mod_info.get("requirements", [])
        if include_patches:
            requirements.extend(mod_info.get("compatible_patches", []))

        return requirements

    def search_incompatibilities(self, mod_name: str) -> List[Dict[str, Any]]:
        """
        Search for mod incompatibilities.

        Args:
            mod_name: Mod name

        Returns:
            List of incompatible mods
        """
        se = get_search_engine(self.game)
        mod_info = se.get_mod_info(mod_name)

        if not mod_info:
            return []

        return mod_info.get("incompatibilities", [])

    def fuzzy_search(
        self,
        query: str,
        threshold: float = 0.6,
    ) -> List[Dict[str, Any]]:
        """
        Fuzzy search for mods.

        Args:
            query: Search query
            threshold: Match threshold (0-1)

        Returns:
            List of fuzzy matches
        """
        se = get_search_engine(self.game)
        return se.fuzzy_search(query, threshold=threshold)

    def get_mod_suggestions(self, prefix: str, limit: int = 5) -> List[str]:
        """
        Get mod name suggestions for autocomplete.

        Args:
            prefix: Name prefix
            limit: Max suggestions

        Returns:
            List of mod names
        """
        se = get_search_engine(self.game)
        return se.get_suggestions(prefix, limit=limit)
