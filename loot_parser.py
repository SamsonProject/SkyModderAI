"""
LOOT Masterlist Parser
Downloads and parses LOOT masterlist data for mod conflict detection.
Supports multiple games with caching (cache filenames are version-agnostic).
"""

import difflib
import json
import logging
import os
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests
import yaml
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# -------------------------------------------------------------------
# Logging
# -------------------------------------------------------------------
logger = logging.getLogger(__name__)


@dataclass
class ModConflict:
    """Represents a conflict between mods."""
    type: str  # 'overwrite', 'requirement', 'incompatible', 'patch_available', etc.
    severity: str  # 'error', 'warning', 'info'
    message: str
    affected_mod: Optional[str] = None
    suggested_action: Optional[str] = None
    related_mod: Optional[str] = None  # Other mod involved (requirement, incompatible, load order)


@dataclass
class ModInfo:
    """Information about a mod from LOOT masterlist."""
    name: str
    clean_name: str  # normalized for matching
    requirements: List[str]
    incompatibilities: List[str]
    load_after: List[str]
    load_before: List[str]
    patches: List[Dict[str, str]]  # {mod: patch_name}
    dirty_edits: bool
    messages: List[str]
    tags: List[str]
    nexus_mod_id: Optional[int] = None  # Nexus Mods ID for direct linking
    picture_url: Optional[str] = None   # URL to mod's primary image


class LOOTParser:
    """Parser for LOOT masterlist data with caching and fuzzy matching. Supports all Bethesda games with LOOT masterlists."""

    # GitHub repo name = game id for LOOT (loot/skyrimse, loot/oblivion, etc.)
    LATEST_VERSIONS = {
        'skyrim': '0.26',
        'skyrimse': '0.26',
        'skyrimvr': '0.21',
        'oblivion': '0.26',
        'fallout3': '0.26',
        'falloutnv': '0.26',
        'fallout4': '0.26',
        'starfield': '0.26',
    }
    
    # Nexus Mods API settings
    NEXUS_API_BASE = 'https://api.nexusmods.com/v1'
    NEXUS_API_TIMEOUT = 5  # seconds
    NEXUS_RATE_LIMIT = 1.0  # seconds between requests
    
    # Game ID to Nexus Mods domain mapping
    NEXUS_GAME_DOMAINS = {
        'skyrimse': 'skyrimspecialedition',
        'skyrimle': 'skyrim',
        'skyrimvr': 'skyrimvr',
        'oblivion': 'oblivion',
        'fallout3': 'fallout3',
        'falloutnv': 'newvegas',
        'fallout4': 'fallout4',
        'starfield': 'starfield',
    }
    
    # Default to Skyrim SE if game not found
    DEFAULT_NEXUS_DOMAIN = 'skyrimspecialedition'

    # Common file extensions to strip
    EXTENSIONS = ('.esp', '.esm', '.esl')

    def __init__(self, game: str = 'skyrimse', version: str = 'latest', cache_dir: str = './data'):
        """
        Initialize parser for a specific game and masterlist.

        Args:
            game: Game identifier (skyrimse, fallout4, etc.)
            version: 'latest' or explicit version string (used only for download URL)
            cache_dir: Directory to store cached YAML and JSON files
        """
        self.game = game.lower()
        if version == 'latest':
            self.version = self.LATEST_VERSIONS.get(self.game, '0.26')
        else:
            self.version = version

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.masterlist_data: Dict[str, Any] = {}
        self.mod_database: Dict[str, ModInfo] = {}

        # Cache for normalized names
        self._normalize_cache: Dict[str, str] = {}

        # Setup requests session with retries
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def _to_str(self, val: Any) -> str:
        """Extract a string from LOOT structures (handles nested dicts, YAML refs). Ensures set() never receives unhashable types."""
        if val is None:
            return ''
        if isinstance(val, str):
            return val
        if isinstance(val, dict):
            return self._to_str(val.get('name', val.get('content', val.get('display', ''))))
        return str(val) if val else ''

    def _normalize_name(self, name: str) -> str:
        """
        Normalize mod name for matching (lowercase, remove extensions).

        Uses an internal cache to avoid repeated processing.
        """
        if name in self._normalize_cache:
            return self._normalize_cache[name]

        # Convert to lowercase and strip
        clean = name.lower().strip()

        # Remove common file extensions
        for ext in self.EXTENSIONS:
            if clean.endswith(ext):
                clean = clean[:-len(ext)]
                break

        self._normalize_cache[name] = clean
        return clean

    def _render_content(self, content: Any) -> str:
        """
        Render a LOOT content object (string, dict, or list) to Markdown string.
        """
        if isinstance(content, str):
            return content
        if isinstance(content, dict):
            # Handle link type
            if content.get('type') == 'link':
                link = content.get('link', '')
                text = content.get('content', '')
                return f'[{text}]({link})'
            # Default: just return content string
            return content.get('content', str(content))
        if isinstance(content, list):
            # Join list elements with spaces
            return ' '.join(self._render_content(item) for item in content)
        return str(content)

    def download_masterlist(self, force_refresh: bool = False) -> bool:
        """
        Download the masterlist YAML from GitHub, or load from cache.

        Args:
            force_refresh: If True, ignore cached file and download fresh.

        Returns:
            True if masterlist data is available (either from cache or download).
        """
        is_latest = self.version == self.LATEST_VERSIONS.get(self.game, '0.26')
        cache_file = self.cache_dir / (f'{self.game}_masterlist.yaml' if is_latest else f'{self.game}_v{self.version}_masterlist.yaml')
        legacy_cache = self.cache_dir / f'{self.game}_v{self.version}_masterlist.yaml' if is_latest else None

        # Try loading from cache (versionless for latest; versioned for pinned)
        if not force_refresh:
            for path in (cache_file, legacy_cache) if legacy_cache else (cache_file,):
                if path is None or not path.exists():
                    continue
                logger.info(f"Loading cached masterlist for {self.game}" + (f" (v{self.version})" if not is_latest else ""))
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        self.masterlist_data = yaml.safe_load(f)
                    if legacy_cache and path == legacy_cache:
                        with open(cache_file, 'w', encoding='utf-8') as f:
                            yaml.dump(self.masterlist_data, f, allow_unicode=True)
                    return True
                except Exception as e:
                    logger.warning(f"Failed to load cached masterlist: {e}")
                    break

        # Download fresh (version = GitHub tag, e.g. v0.26)
        url = f'https://raw.githubusercontent.com/loot/{self.game}/v{self.version}/masterlist.yaml'
        logger.info(f"Downloading masterlist for {self.game}" + (f" v{self.version}" if not is_latest else "") + "...")
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            self.masterlist_data = yaml.safe_load(response.text)

            # Cache the raw YAML
            with open(cache_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.masterlist_data, f, allow_unicode=True)

            plugin_count = len(self.masterlist_data.get('plugins', []))
            logger.info(f"Downloaded masterlist ({plugin_count} mods)")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error downloading masterlist: {e}")
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error downloading masterlist: {e}")

        return False

    def parse_masterlist(self) -> None:
        """Parse the loaded masterlist into a structured mod database."""
        if not self.masterlist_data:
            logger.error("No masterlist data loaded. Call download_masterlist() first.")
            return

        plugins = self.masterlist_data.get('plugins', [])
        total = len(plugins)
        logger.info(f"Parsing {total} mods from masterlist...")

        for i, plugin in enumerate(plugins):
            if (i + 1) % 500 == 0:
                logger.info(f"Parse progress: {i + 1}/{total} mods")
            name = plugin.get('name', '')
            if not name:
                continue

            # Initialize collections for this plugin
            requirements = []
            incompatibilities = []
            load_after = []
            load_before = []
            patches = []
            messages = []
            raw_tags = plugin.get('tag', []) or []
            tags = [self._to_str(t) for t in raw_tags if self._to_str(t)]

            # Parse requirements (req)
            for req in plugin.get('req', []):
                s = self._to_str(req)
                if s:
                    requirements.append(s)

            # Parse incompatibilities (inc)
            for inc in plugin.get('inc', []):
                s = self._to_str(inc)
                if s:
                    incompatibilities.append(s)

            # Parse load after rules
            for after in plugin.get('after', []):
                s = self._to_str(after)
                if s:
                    load_after.append(s)

            # Parse load before rules (if present)
            for before in plugin.get('before', []):
                s = self._to_str(before)
                if s:
                    load_before.append(s)

            # Parse messages (msg) with substitutions
            for msg in plugin.get('msg', []):
                if not isinstance(msg, dict):
                    continue

                # Handle LOOT merge convention '<<'
                if '<<' in msg:
                    base = msg['<<']
                    if isinstance(base, dict):
                        # Merge base into msg, excluding the '<<' key
                        msg = {**base, **{k: v for k, v in msg.items() if k != '<<'}}

                content = msg.get('content', '')
                subs = msg.get('subs', [])

                # Render substitutions first
                rendered_subs = [self._render_content(s) for s in subs]

                # Render content with substitutions
                if isinstance(content, str):
                    if rendered_subs:
                        try:
                            message_text = content.format(*rendered_subs)
                        except (IndexError, ValueError, KeyError):
                            message_text = content  # fallback
                    else:
                        message_text = content
                elif isinstance(content, list):
                    parts = []
                    for item in content:
                        item_text = self._render_content(item)
                        if rendered_subs:
                            try:
                                item_text = item_text.format(*rendered_subs)
                            except (IndexError, ValueError, KeyError):
                                pass
                        parts.append(item_text)
                    message_text = '\n'.join(parts)
                else:
                    message_text = self._render_content(content)

                if message_text:
                    messages.append(message_text)

            # Determine if mod has dirty edits (based on tags or messages)
            dirty_edits = ('Delev' in tags or 'Relev' in tags or
                           any('dirty' in msg.lower() for msg in messages))

            clean_name = self._normalize_name(name)

            # Ensure messages are strings (set() requires hashable)
            messages = [m if isinstance(m, str) else str(m) for m in messages]

            # Ensure all list items are strings (set() requires hashable)
            def _strs(lst):
                return [self._to_str(x) for x in lst if self._to_str(x)]

            requirements = _strs(requirements)
            incompatibilities = _strs(incompatibilities)
            load_after = _strs(load_after)
            load_before = _strs(load_before)
            tags = _strs(tags)

            # Check if we already have an entry (should not happen, but safe)
            if clean_name in self.mod_database:
                existing = self.mod_database[clean_name]
                # Merge lists with deduplication (only hashable/strings for set())
                existing.requirements = list(set(_strs(existing.requirements) + requirements))
                existing.incompatibilities = list(set(_strs(existing.incompatibilities) + incompatibilities))
                existing.load_after = list(set(_strs(existing.load_after) + load_after))
                existing.load_before = list(set(_strs(existing.load_before) + load_before))
                existing.patches.extend(patches)  # patches are dicts, not easily deduped
                existing.messages = list(set(_strs(existing.messages) + messages))
                existing.tags = list(set(_strs(existing.tags) + tags))
                # Update dirty_edits with the new value if it's True
                existing.dirty_edits = existing.dirty_edits or dirty_edits
            else:
                mod_info = ModInfo(
                    name=name,
                    clean_name=clean_name,
                    requirements=requirements,
                    incompatibilities=incompatibilities,
                    load_after=load_after,
                    load_before=load_before,
                    patches=patches,
                    dirty_edits=dirty_edits,
                    messages=messages,
                    tags=tags
                )
                self.mod_database[clean_name] = mod_info

            # Register base alias for regex plugin names (e.g. "Mod\.es[mp]" -> also "mod")
            # so user input "Mod.esp" matches
            if '\\' in name or ('[' in name and ']' in name):
                base = re.sub(r'\\..*$', '', name).strip()
                if base:
                    base_clean = self._normalize_name(base)
                    if base_clean and base_clean not in self.mod_database:
                        self.mod_database[base_clean] = self.mod_database[clean_name]

        logger.info(f"Parsed {len(self.mod_database)} unique mods into database")

    def _compact_for_match(self, s: str) -> str:
        """Collapse spaces, dashes, underscores for flexible matching (e.g. 'Shattered Space' -> 'shatteredspace')."""
        return ''.join(c for c in s.lower() if c.isalnum())

    def get_mod_info(self, mod_name: str) -> Optional[ModInfo]:
        """
        Retrieve mod info by name, with flexible matching: exact, compact (spaces/dashes removed), then fuzzy.

        Args:
            mod_name: The mod name as it appears in user's list.

        Returns:
            ModInfo object or None if not found.
        """
        clean_name = self._normalize_name(mod_name)
        if clean_name in self.mod_database:
            return self.mod_database[clean_name]

        # Compact match: "Shattered Space" -> "shatteredspace" matches DB key "shatteredspace"
        compact = self._compact_for_match(clean_name)
        if compact:
            for db_key, info in self.mod_database.items():
                if self._compact_for_match(db_key) == compact:
                    return info

        # Fuzzy match if exact and compact fail
        all_names = list(self.mod_database.keys())
        matches = difflib.get_close_matches(clean_name, all_names, n=1, cutoff=0.7)
        if matches:
            logger.debug(f"Fuzzy matched '{mod_name}' to '{matches[0]}'")
            return self.mod_database[matches[0]]

        return None

    def get_fuzzy_suggestion(self, mod_name: str, cutoff: float = 0.65) -> Optional[str]:
        """
        Return a suggested mod name from the database (e.g. for typos).
        Uses stricter cutoff (0.65) so we don't suggest unrelated mods like
        "OblivionDeadLands" for "Oblivion Reloaded".
        """
        clean_name = self._normalize_name(mod_name)
        if clean_name in self.mod_database:
            return None
        all_names = list(self.mod_database.keys())
        matches = difflib.get_close_matches(clean_name, all_names, n=1, cutoff=cutoff)
        if matches:
            return self.mod_database[matches[0]].name
        return None

    def search_mod_names(self, query: str, limit: int = 25) -> List[str]:
        """Return mod display names: prefix matches first, then contains, then fuzzy for typos."""
        q = query.lower().strip()
        if not q:
            return []
        starts, contains = [], []
        for info in self.mod_database.values():
            name_lower = info.name.lower()
            if info.clean_name.startswith(q) or name_lower.startswith(q):
                starts.append(info.name)
            elif q in (info.clean_name or '') or q in name_lower:
                contains.append(info.name)
        result = list(dict.fromkeys(starts + contains))
        if len(result) < limit:
            all_names = [info.name for info in self.mod_database.values()]
            fuzzy = difflib.get_close_matches(q, all_names, n=limit, cutoff=0.45)
            for n in fuzzy:
                if n not in result:
                    result.append(n)
                    if len(result) >= limit:
                        break
        return result[:limit]

    def _database_path(self) -> Path:
        """Per-game (and per-version when pinned) JSON path so games don't overwrite each other."""
        is_latest = self.version == self.LATEST_VERSIONS.get(self.game, '0.26')
        name = f'{self.game}_mod_database.json' if is_latest else f'{self.game}_v{self.version}_mod_database.json'
        return self.cache_dir / name

    def save_database(self, filepath: Optional[Union[str, Path]] = None) -> None:
        """
        Save the parsed mod database to JSON (per-game, per-version when pinned).
        """
        if filepath is None:
            filepath = self._database_path()
        filepath = Path(filepath)

        data = {clean_name: asdict(info) for clean_name, info in self.mod_database.items()}
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved mod database to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save database: {e}")

    def load_database(self, filepath: Optional[Union[str, Path]] = None) -> bool:
        """
        Load a previously saved JSON database (per-game). Tries versioned path then versionless.
        Returns True if loaded successfully.
        """
        if filepath is not None:
            paths_to_try = [Path(filepath)]
        else:
            default_path = self._database_path()
            paths_to_try = [default_path]
            if default_path.name != f'{self.game}_mod_database.json':
                paths_to_try.append(self.cache_dir / f'{self.game}_mod_database.json')
            if self.game == 'skyrimse':
                paths_to_try.append(self.cache_dir / 'mod_database.json')

        for path in paths_to_try:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                self.mod_database = {}
                for clean_name, info_dict in data.items():
                    self.mod_database[clean_name] = ModInfo(**info_dict)

                logger.info(f"Loaded {len(self.mod_database)} mods from database")
                return True
            except FileNotFoundError:
                continue
            except Exception as e:
                logger.error(f"Error loading database: {e}")
                return False

        logger.warning(f"Database file not found for {self.game}")
        return False

    @classmethod
    def _version_sort_key(cls, ver: str) -> tuple:
        """Convert version string to sortable tuple (newest first). e.g. '0.26' -> (0, 26)."""
        try:
            parts = [int(x) for x in ver.split('.') if x.isdigit()]
            return tuple(parts) if parts else (0,)
        except (ValueError, AttributeError):
            return (0,)

    @classmethod
    def fetch_masterlist_versions(cls, game: str, timeout: int = 10) -> List[str]:
        """
        Fetch available masterlist versions (GitHub branches like v0.26) for a game.
        Returns version strings sorted newest first (e.g. ['0.26', '0.21', '0.20', ...]).
        Each game has its own LOOT repo; older versions support fewer mods.
        """
        game = game.lower()
        if game not in cls.LATEST_VERSIONS:
            return []
        try:
            r = requests.get(
                f'https://api.github.com/repos/loot/{game}/branches',
                params={'per_page': 100},
                timeout=timeout,
                headers={'Accept': 'application/vnd.github.v3+json'},
            )
            r.raise_for_status()
            data = r.json()
            versions = []
            for b in data:
                name = (b.get('name') or '').strip()
                ver = name[1:] if name.startswith('v') else name
                if ver and all(p.isdigit() for p in ver.split('.') if p):
                    versions.append(ver)
            seen = set()
            unique = []
            for v in versions:
                if v and v not in seen:
                    seen.add(v)
                    unique.append(v)
            # Sort newest first (0.26 before 0.21)
            unique.sort(key=cls._version_sort_key, reverse=True)
            return unique
        except Exception as e:
            logger.warning(f"Could not fetch masterlist versions for {game}: {e}")
            return []


# -------------------------------------------------------------------
# CLI: Pre-download LOOT data for build/deploy (avoids cold-start delay)
# -------------------------------------------------------------------
if __name__ == '__main__':
    import sys
    args = sys.argv[1:]
    export_fuel = '--export-samson-fuel' in args
    games = [a for a in args if a != '--export-samson-fuel'] or ['skyrimse']
    failed = []
    for game in games:
        g = game.lower()
        if g not in LOOTParser.LATEST_VERSIONS:
            print(f"Unknown game: {g}")
            failed.append(g)
            continue
        p = LOOTParser(g)
        if p.download_masterlist(force_refresh=False):
            p.parse_masterlist()
            p.save_database()
            print(f"OK: {g} ({len(p.mod_database)} mods)")
            if export_fuel:
                try:
                    from samson_fuel import extract_fuel, write_fuel
                    fuel = extract_fuel(p)
                    path = write_fuel(fuel)
                    print(f"  Fuel: {path}")
                except Exception as e:
                    print(f"  Samson fuel export failed: {e}")
        else:
            print(f"FAIL: {g}")
            failed.append(g)
    sys.exit(1 if failed else 0)
