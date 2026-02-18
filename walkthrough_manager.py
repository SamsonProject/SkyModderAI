import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class WalkthroughManager:
    """
    Manages loading and searching of gameplay walkthroughs.
    Serves the 'Stuck Selector' and provides context-aware guide data.
    """

    def __init__(self, data_dir: str = "data/walkthroughs"):
        # Resolves relative to the application root if not absolute
        if not os.path.isabs(data_dir):
            base_path = os.path.dirname(os.path.abspath(__file__))
            self.data_dir = os.path.join(base_path, data_dir)
        else:
            self.data_dir = data_dir

        self._cache: Dict[str, Dict[str, Any]] = {}

    def get_walkthrough(self, game: str, walkthrough_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a specific walkthrough by ID for a given game.
        """
        cache_key = f"{game}:{walkthrough_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        file_path = os.path.join(self.data_dir, game, f"{walkthrough_id}.json")

        if not os.path.exists(file_path):
            logger.warning(f"Walkthrough not found: {file_path}")
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._cache[cache_key] = data
                return data
        except Exception as e:
            logger.error(f"Error loading walkthrough {file_path}: {e}")
            return None

    def get_stuck_index(self, game: str) -> List[Dict[str, Any]]:
        """
        Returns the index for the 'Stuck Selector' (Categories -> Quests).
        Scans the game directory for valid JSON guide files.
        """
        game_dir = os.path.join(self.data_dir, game)
        if not os.path.exists(game_dir):
            return []

        index = []
        try:
            for filename in os.listdir(game_dir):
                if not filename.endswith(".json"):
                    continue

                # In a high-scale env, we'd use a manifest file.
                # For local/embedded, scanning is fast enough and less prone to sync errors.
                try:
                    with open(os.path.join(game_dir, filename), "r", encoding="utf-8") as f:
                        data = json.load(f)
                        index.append({
                            "id": data.get("id", filename.replace(".json", "")),
                            "title": data.get("title", "Unknown Guide"),
                            "category": data.get("category", "Uncategorized"),
                            "tags": data.get("tags", []),
                        })
                except Exception:
                    continue
        except Exception as e:
            logger.error(f"Error scanning walkthroughs for {game}: {e}")
            return []

        return sorted(index, key=lambda x: (x["category"], x["title"]))
