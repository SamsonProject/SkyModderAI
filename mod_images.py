"""
Mod Images & Media — Smart image previews for mods.
Fetches mod images from Nexus API, caches them, and provides fallbacks.
Also handles inline embedding for Imgur, videos, and guides.
"""

import logging
import os
import re
import time
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Nexus API configuration
NEXUS_API_KEY = os.environ.get("NEXUS_API_KEY")
NEXUS_API_BASE = "https://api.nexusmods.com/v1"
NEXUS_AVAILABLE = bool(NEXUS_API_KEY)

# Image cache directory
IMAGE_CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "mod_images")
os.makedirs(IMAGE_CACHE_DIR, exist_ok=True)

# Cache expiry (24 hours)
CACHE_EXPIRY = 24 * 60 * 60

# Placeholder images
MOD_PLACEHOLDER = "/static/icons/mod-placeholder.svg"
IMGUR_PLACEHOLDER = "/static/icons/image-placeholder.svg"
VIDEO_PLACEHOLDER = "/static/icons/video-placeholder.svg"

# Supported embed domains
EMBED_DOMAINS = {
    "imgur.com": "imgur",
    "i.imgur.com": "imgur",
    "youtube.com": "youtube",
    "youtu.be": "youtube",
    "vimeo.com": "vimeo",
    "twitch.tv": "twitch",
    "nexusmods.com": "nexus",
    "github.com": "github",
    "reddit.com": "reddit",
}


def get_mod_image(
    game_id: str,
    mod_id: str,
    mod_name: str,
    use_cache: bool = True,
) -> str:
    """
    Get mod image URL from Nexus API or cache.
    
    Args:
        game_id: Game identifier (skyrimse, fallout4, etc.)
        mod_id: Nexus mod ID
        mod_name: Mod name for fallback search
        use_cache: Whether to use cached image
    
    Returns:
        Image URL (Nexus, cached, or placeholder)
    """
    if not NEXUS_AVAILABLE:
        return MOD_PLACEHOLDER
    
    # Check cache first
    cache_key = f"{game_id}_{mod_id}"
    cache_file = os.path.join(IMAGE_CACHE_DIR, f"{cache_key}.json")
    
    if use_cache and os.path.exists(cache_file):
        try:
            import json
            with open(cache_file, "r") as f:
                data = json.load(f)
            
            # Check if cache is still valid
            if time.time() - data.get("timestamp", 0) < CACHE_EXPIRY:
                return data.get("image_url", MOD_PLACEHOLDER)
        except Exception as e:
            logger.warning(f"Cache read failed for {cache_key}: {e}")
    
    # Fetch from Nexus API
    try:
        import requests
        
        # Map game_id to Nexus game_id
        nexus_game_ids = {
            "skyrimse": "skyrimspecialedition",
            "skyrim": "skyrim",
            "skyrimvr": "skyrimspecialedition",
            "oblivion": "oblivion",
            "fallout3": "fallout3",
            "falloutnv": "newvegas",
            "fallout4": "fallout4",
            "starfield": "starfield",
        }
        
        nexus_game = nexus_game_ids.get(game_id, game_id)
        
        headers = {
            "apikey": NEXUS_API_KEY,
            "Accept": "application/json",
        }
        
        url = f"{NEXUS_API_BASE}/games/{nexus_game}/mods/{mod_id}.json"
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            image_url = data.get("picture_url") or data.get("image_url")
            
            if image_url:
                # Cache the result
                cache_result(cache_key, image_url)
                return image_url
        
        # Try searching by name as fallback
        return search_mod_image_by_name(game_id, mod_name)
        
    except Exception as e:
        logger.warning(f"Nexus API fetch failed for mod {mod_id}: {e}")
        return search_mod_image_by_name(game_id, mod_name)


def search_mod_image_by_name(game_id: str, mod_name: str) -> str:
    """Search Nexus API by mod name to find image."""
    if not NEXUS_AVAILABLE:
        return MOD_PLACEHOLDER
    
    try:
        import requests
        from urllib.parse import quote
        
        nexus_game_ids = {
            "skyrimse": "skyrimspecialedition",
            "skyrim": "skyrim",
            "skyrimvr": "skyrimspecialedition",
            "oblivion": "oblivion",
            "fallout3": "fallout3",
            "falloutnv": "newvegas",
            "fallout4": "fallout4",
            "starfield": "starfield",
        }
        
        nexus_game = nexus_game_ids.get(game_id, game_id)
        
        headers = {
            "apikey": NEXUS_API_KEY,
            "Accept": "application/json",
        }
        
        # Search for mod by name
        url = f"{NEXUS_API_BASE}/games/{nexus_game}/mods/search.json?name={quote(mod_name)}"
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            mods = response.json().get("mods", [])
            if mods:
                # Get first match
                image_url = mods[0].get("picture_url") or mods[0].get("image_url")
                if image_url:
                    mod_id = mods[0].get("id", "unknown")
                    cache_key = f"{game_id}_{mod_id}"
                    cache_result(cache_key, image_url)
                    return image_url
        
        return MOD_PLACEHOLDER
        
    except Exception as e:
        logger.warning(f"Nexus API search failed for '{mod_name}': {e}")
        return MOD_PLACEHOLDER


def cache_result(cache_key: str, image_url: str):
    """Cache image URL to disk."""
    try:
        import json
        
        cache_file = os.path.join(IMAGE_CACHE_DIR, f"{cache_key}.json")
        data = {
            "image_url": image_url,
            "timestamp": time.time(),
        }
        
        with open(cache_file, "w") as f:
            json.dump(data, f)
            
    except Exception as e:
        logger.warning(f"Cache write failed for {cache_key}: {e}")


def extract_embed_info(text: str) -> List[Dict]:
    """
    Extract embeddable content from text (Imgur, YouTube, etc.).
    
    Returns list of {type, url, embed_url, thumbnail}.
    """
    embeds = []
    
    # Imgur images/albums
    imgur_pattern = r'https?://(?:i\.)?imgur\.com/([a-zA-Z0-9]+)(?:\.[a-zA-Z]+)?'
    for match in re.finditer(imgur_pattern, text):
        img_id = match.group(1)
        embeds.append({
            "type": "imgur",
            "url": match.group(0),
            "embed_url": f"https://i.imgur.com/{img_id}.jpg",
            "thumbnail": f"https://i.imgur.com/{img_id}s.jpg",
        })
    
    # YouTube videos
    youtube_patterns = [
        r'https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
        r'https?://youtu\.be/([a-zA-Z0-9_-]+)',
    ]
    for pattern in youtube_patterns:
        for match in re.finditer(pattern, text):
            video_id = match.group(1)
            embeds.append({
                "type": "youtube",
                "url": match.group(0),
                "embed_url": f"https://www.youtube.com/embed/{video_id}",
                "thumbnail": f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg",
            })
    
    # Vimeo videos
    vimeo_pattern = r'https?://(?:www\.)?vimeo\.com/([0-9]+)'
    for match in re.finditer(vimeo_pattern, text):
        video_id = match.group(1)
        embeds.append({
            "type": "vimeo",
            "url": match.group(0),
            "embed_url": f"https://player.vimeo.com/video/{video_id}",
            "thumbnail": None,  # Would need API call
        })
    
    # Twitch clips/streams
    twitch_pattern = r'https?://(?:www\.)?twitch\.tv/([a-zA-Z0-9_]+)'
    for match in re.finditer(twitch_pattern, text):
        channel = match.group(1)
        embeds.append({
            "type": "twitch",
            "url": match.group(0),
            "embed_url": f"https://player.twitch.tv/?channel={channel}&parent={get_current_domain()}",
            "thumbnail": None,
        })
    
    return embeds


def get_current_domain() -> str:
    """Get current domain for embed parent restrictions."""
    # This would be set from request context in Flask
    return os.environ.get("BASE_URL", "localhost").replace("https://", "").replace("http://", "")


def generate_embed_html(embed_type: str, embed_url: str, thumbnail: Optional[str] = None) -> str:
    """Generate HTML for embedded content."""
    if embed_type == "imgur":
        return f'<img src="{embed_url}" alt="Imgur image" class="embed-image" loading="lazy">'
    
    elif embed_type == "youtube":
        return f'''
        <div class="embed-video embed-youtube">
            <iframe src="{embed_url}" frameborder="0" allowfullscreen loading="lazy"></iframe>
        </div>
        '''
    
    elif embed_type == "vimeo":
        return f'''
        <div class="embed-video embed-vimeo">
            <iframe src="{embed_url}" frameborder="0" allowfullscreen loading="lazy"></iframe>
        </div>
        '''
    
    elif embed_type == "twitch":
        return f'''
        <div class="embed-video embed-twitch">
            <iframe src="{embed_url}" frameborder="0" allowfullscreen loading="lazy"></iframe>
        </div>
        '''
    
    return ""


def enrich_mod_with_image(parser, mod_entry: dict, game_id: str) -> dict:
    """
    Enrich a mod entry with image URL.
    Tries multiple sources: LOOT data, Nexus API, search.
    """
    mod_name = mod_entry.get("name", "")
    
    # Check if already has image
    if mod_entry.get("image_url") and mod_entry["image_url"] != MOD_PLACEHOLDER:
        return mod_entry
    
    # Try to get from LOOT database
    mod_info = parser.mod_database.get(mod_name.lower().strip())
    if mod_info and hasattr(mod_info, "picture_url") and mod_info.picture_url:
        mod_entry["image_url"] = mod_info.picture_url
        return mod_entry
    
    # Try Nexus API if we have mod ID
    nexus_url = mod_entry.get("nexus_url", "")
    if nexus_url:
        # Extract mod ID from Nexus URL
        match = re.search(r'/mods/(\d+)', nexus_url)
        if match:
            mod_id = match.group(1)
            mod_entry["image_url"] = get_mod_image(game_id, mod_id, mod_name)
            return mod_entry
    
    # Fallback to placeholder
    mod_entry["image_url"] = MOD_PLACEHOLDER
    return mod_entry


# Batch image fetching for recommendations
def enrich_recommendations_with_images(
    parser,
    recommendations: List[dict],
    game_id: str,
) -> List[dict]:
    """
    Enrich multiple mod recommendations with images.
    Uses batching and caching for efficiency.
    """
    enriched = []
    
    for rec in recommendations:
        enriched_rec = enrich_mod_with_image(parser, rec, game_id)
        enriched.append(enriched_rec)
    
    return enriched
