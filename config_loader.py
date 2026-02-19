"""
Configuration Loader Service
Loads and caches configuration from YAML files.
Provides centralized access to all configuration settings.
"""

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Load and cache configuration from YAML files."""
    
    def __init__(self, config_dir: str = None):
        """
        Initialize configuration loader.
        
        Args:
            config_dir: Path to configuration directory
        """
        if config_dir is None:
            config_dir = Path(__file__).parent / "config"
        
        self.config_dir = Path(config_dir)
        self._cache: Dict[str, Any] = {}
        
        logger.info(f"Configuration loader initialized: {self.config_dir}")
    
    def _load_yaml(self, file_path: Path) -> Dict[str, Any]:
        """
        Load YAML file.
        
        Args:
            file_path: Path to YAML file
            
        Returns:
            Parsed YAML content as dictionary
        """
        if not file_path.exists():
            logger.warning(f"Configuration file not found: {file_path}")
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
                logger.debug(f"Loaded configuration: {file_path}")
                return content or {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML {file_path}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return {}
    
    def _get_config_path(self, name: str) -> Path:
        """Get path to configuration file."""
        return self.config_dir / name
    
    def get_external_links(self) -> Dict[str, Any]:
        """
        Get all external links configuration.
        
        Returns:
            Dictionary of external links by category
        """
        if "external_links" not in self._cache:
            self._cache["external_links"] = self._load_yaml(
                self._get_config_path("external_links.yaml")
            )
        return self._cache["external_links"]
    
    def get_link(self, category: str, key: str, fallback: str = None) -> Optional[Dict[str, Any]]:
        """
        Get a specific link by category and key.
        
        Args:
            category: Link category (e.g., "tools", "repositories")
            key: Link key (e.g., "loot", "nexus_mods")
            fallback: Fallback URL if link not found
            
        Returns:
            Link dictionary with url, label, description, or None
        """
        links = self.get_external_links()
        
        # Navigate to category
        if category not in links:
            logger.warning(f"Link category not found: {category}")
            return {"url": fallback, "label": key} if fallback else None
        
        category_links = links[category]
        
        # Navigate to key (supports nested keys like "unofficial_patches.skyrimse")
        keys = key.split(".")
        value = category_links
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                logger.warning(f"Link key not found: {key}")
                return {"url": fallback, "label": key} if fallback else None
        
        # If value is a dict with url, return it
        if isinstance(value, dict) and "url" in value:
            return value
        
        # If value is just a URL string, wrap it
        if isinstance(value, str):
            return {"url": value, "label": key}
        
        return {"url": fallback, "label": key} if fallback else None
    
    def get_game_config(self, game_id: str) -> Dict[str, Any]:
        """
        Get game-specific configuration.
        
        Args:
            game_id: Game identifier (e.g., "skyrimse", "fallout4")
            
        Returns:
            Game configuration dictionary
        """
        cache_key = f"game.{game_id}"
        
        if cache_key not in self._cache:
            game_config_path = self.config_dir / "games" / f"{game_id}.yaml"
            self._cache[cache_key] = self._load_yaml(game_config_path)
        
        return self._cache[cache_key]
    
    def get_all_games(self) -> List[str]:
        """
        Get list of all configured games.
        
        Returns:
            List of game IDs
        """
        games_dir = self.config_dir / "games"
        if not games_dir.exists():
            return []
        
        return [
            f.stem for f in games_dir.glob("*.yaml")
        ]
    
    def get_email_template(self, template_name: str) -> str:
        """
        Get email template content.
        
        Args:
            template_name: Template name (without .html extension)
            
        Returns:
            Template content as string
        """
        cache_key = f"email.{template_name}"
        
        if cache_key not in self._cache:
            template_path = self.config_dir / "email_templates" / f"{template_name}.html"
            self._cache[cache_key] = template_path.read_text(encoding='utf-8') if template_path.exists() else ""
        
        return self._cache[cache_key]
    
    def get_prompt_template(self, template_name: str) -> str:
        """
        Get AI prompt template.
        
        Args:
            template_name: Template name (without .txt extension)
            
        Returns:
            Prompt template content
        """
        cache_key = f"prompt.{template_name}"
        
        if cache_key not in self._cache:
            template_path = self.config_dir / "prompts" / f"{template_name}.txt"
            self._cache[cache_key] = template_path.read_text(encoding='utf-8') if template_path.exists() else ""
        
        return self._cache[cache_key]
    
    def reload(self, config_name: str = None):
        """
        Reload configuration from disk.
        
        Args:
            config_name: Specific config to reload, or None for all
        """
        if config_name:
            if config_name in self._cache:
                del self._cache[config_name]
                logger.info(f"Reloaded configuration: {config_name}")
        else:
            self._cache.clear()
            logger.info("Reloaded all configurations")
    
    def clear_cache(self):
        """Clear all cached configuration."""
        self._cache.clear()
        logger.info("Configuration cache cleared")


# Global configuration loader instance
_config_loader: Optional[ConfigLoader] = None


def get_config_loader() -> ConfigLoader:
    """
    Get or create global configuration loader.
    
    Returns:
        ConfigLoader instance
    """
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader


# Convenience functions for direct import
def get_link(category: str, key: str, fallback: str = None) -> Optional[Dict[str, Any]]:
    """Get a link by category and key."""
    return get_config_loader().get_link(category, key, fallback)


def get_game_config(game_id: str) -> Dict[str, Any]:
    """Get game configuration."""
    return get_config_loader().get_game_config(game_id)


def get_all_games() -> List[str]:
    """Get all configured games."""
    return get_config_loader().get_all_games()


def get_email_template(template_name: str) -> str:
    """Get email template."""
    return get_config_loader().get_email_template(template_name)


def get_prompt_template(template_name: str) -> str:
    """Get AI prompt template."""
    return get_config_loader().get_prompt_template(template_name)
