"""
Floating Link Architecture — Obsidian-style internal linking for SkyModderAI.
Enables clickable, hover-preview links throughout the app without leaving the page.

Features:
- Smart link detection in all text content
- Hover previews (Nexus mods, guides, images, videos)
- Internal navigation without page reload
- Rich embeds for Imgur, YouTube, guides
- Context-aware link suggestions
"""

import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Internal link patterns
INTERNAL_LINKS = {
    # Tool sections
    "analyze": "/#panel-analyze",
    "quickstart": "/#panel-quickstart",
    "build": "/#panel-build-list",
    "build-a-list": "/#panel-build-list",
    "library": "/#panel-library",
    "community": "/#panel-community",
    "gameplay": "/#panel-gameplay",
    "dev tools": "/#panel-dev",
    "dev": "/#panel-dev",

    # Documentation
    "api": "/api",
    "api hub": "/api",
    "documentation": "/docs",
    "docs": "/docs",
    "safety": "/safety",
    "terms": "/terms",
    "privacy": "/privacy",

    # User sections
    "profile": "/profile",
    "settings": "/profile#settings",
    "saved lists": "/#panel-library",

    # External resources (opened in iframe/preview)
    "nexus": "https://www.nexusmods.com/",
    "nexus mods": "https://www.nexusmods.com/",
    "vortex": "https://www.nexusmods.com/site/mods/1",
    "mod organizer": "https://www.modorganizer.org/",
    "mo2": "https://www.modorganizer.org/",
    "loot": "https://loot.github.io/",
    "xedit": "https://tes5edit.github.io/",
    "sseedit": "https://tes5edit.github.io/",
    "skse": "https://skse.silverlock.org/",
    "wabbajack": "https://www.wabbajack.org/",
}

# Smart link regex patterns
LINK_PATTERNS = {
    # Nexus mod links
    "nexus_mod": r'https?://(?:www\.)?nexusmods\.com/([a-z]+)/mods/(\d+)',

    # YouTube links
    "youtube": r'https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]+)',

    # Imgur links
    "imgur": r'https?://(?:i\.)?imgur\.com/([a-zA-Z0-9]+)',

    # GitHub links
    "github": r'https?://(?:www\.)?github\.com/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)',

    # Reddit links
    "reddit": r'https?://(?:www\.)?reddit\.com/r/([a-zA-Z0-9_-]+)',

    # Internal page links (double brackets like Obsidian)
    "internal": r'\[\[([^\]]+)\]\]',

    # Markdown links
    "markdown": r'\[([^\]]+)\]\(([^)]+)\)',
}


def process_text_with_links(
    text: str,
    game_id: Optional[str] = None,
    preserve_urls: bool = True,
) -> str:
    """
    Process text to add smart links and hover previews.

    Args:
        text: Input text to process
        game_id: Current game context for Nexus links
        preserve_urls: Keep original URLs visible

    Returns:
        HTML with smart links
    """
    if not text:
        return ""

    html = text

    # Process internal links [[Like This]]
    html = process_internal_links(html)

    # Process Nexus mod links
    html = process_nexus_links(html, game_id)

    # Process YouTube links
    html = process_youtube_links(html)

    # Process Imgur links
    html = process_imgur_links(html)

    # Process markdown links
    html = process_markdown_links(html)

    # Process bare URLs (make them clickable with previews)
    if preserve_urls:
        html = process_bare_urls(html)

    return html


def process_internal_links(html: str) -> str:
    """Process [[Internal Link]] syntax like Obsidian."""

    def replace_internal(match):
        link_text = match.group(1)
        link_lower = link_text.lower()

        # Check if it's a known internal link
        if link_lower in INTERNAL_LINKS:
            url = INTERNAL_LINKS[link_lower]
            return f'<a href="{url}" class="internal-link" data-link-type="internal" data-preview="{link_text}">{link_text}</a>'

        # Try fuzzy matching
        for key, url in INTERNAL_LINKS.items():
            if link_lower in key or key in link_lower:
                return f'<a href="{url}" class="internal-link" data-link-type="internal" data-preview="{link_text}">{link_text}</a>'

        # Unknown internal link - suggest creation
        return f'<span class="internal-link unknown" data-suggest="{link_text}">?{link_text}</span>'

    return re.sub(r'\[\[([^\]]+)\]\]', replace_internal, html)


def process_nexus_links(html: str, game_id: Optional[str] = None) -> str:
    """Process Nexus mod links with hover previews."""

    def replace_nexus(match):
        game_slug = match.group(1)
        mod_id = match.group(2)
        full_url = match.group(0)

        return f'''
        <a href="{full_url}"
           class="external-link nexus-link"
           data-link-type="nexus"
           data-game="{game_slug}"
           data-mod-id="{mod_id}"
           target="_blank"
           rel="noopener noreferrer">
            Nexus Mod #{mod_id}
        </a>
        '''

    return re.sub(LINK_PATTERNS["nexus_mod"], replace_nexus, html)


def process_youtube_links(html: str) -> str:
    """Process YouTube links with embed previews."""

    def replace_youtube(match):
        video_id = match.group(1)
        full_url = match.group(0)

        return f'''
        <a href="{full_url}"
           class="external-link youtube-link"
           data-link-type="youtube"
           data-video-id="{video_id}"
           target="_blank"
           rel="noopener noreferrer">
            ▶ Watch Video
        </a>
        '''

    return re.sub(LINK_PATTERNS["youtube"], replace_youtube, html)


def process_imgur_links(html: str) -> str:
    """Process Imgur links with image previews."""

    def replace_imgur(match):
        img_id = match.group(1)
        full_url = match.group(0)

        return f'''
        <a href="{full_url}"
           class="external-link imgur-link"
           data-link-type="imgur"
           data-img-id="{img_id}"
           target="_blank"
           rel="noopener noreferrer">
            📷 View Image
        </a>
        '''

    return re.sub(LINK_PATTERNS["imgur"], replace_imgur, html)


def process_markdown_links(html: str) -> str:
    """Process Markdown [text](url) links with smart previews."""

    def replace_markdown(match):
        link_text = match.group(1)
        url = match.group(2)

        # Determine link type
        link_type = "external"
        for pattern, ltype in [("nexusmods", "nexus"), ("youtube", "youtube"),
                               ("imgur", "imgur"), ("github", "github")]:
            if pattern in url:
                link_type = ltype
                break

        return f'''
        <a href="{url}"
           class="markdown-link {link_type}-link"
           data-link-type="{link_type}"
           target="_blank"
           rel="noopener noreferrer">
            {link_text}
        </a>
        '''

    return re.sub(LINK_PATTERNS["markdown"], replace_markdown, html)


def process_bare_urls(html: str) -> str:
    """Make bare URLs clickable with previews."""

    # URL pattern
    url_pattern = r'https?://[^\s<>"\']+'

    def replace_url(match):
        url = match.group(0)

        # Don't link if already inside an <a> tag
        # (This is simplified - proper HTML parsing would be better)

        # Determine link type
        link_type = "external"
        display_text = url

        if "nexusmods" in url:
            link_type = "nexus"
            display_text = "📦 Nexus Mod"
        elif "youtube" in url or "youtu.be" in url:
            link_type = "youtube"
            display_text = "▶ Video"
        elif "imgur" in url:
            link_type = "imgur"
            display_text = "📷 Image"
        elif "github" in url:
            link_type = "github"
            display_text = "🐙 GitHub"

        return f'''
        <a href="{url}"
           class="bare-url {link_type}-link"
           data-link-type="{link_type}"
           target="_blank"
           rel="noopener noreferrer">
            {display_text}
        </a>
        '''

    return re.sub(url_pattern, replace_url, html)


def get_link_preview_data(link_type: str, **kwargs) -> dict:
    """
    Get preview data for a link (used by API endpoint).

    Returns preview HTML, thumbnail, and metadata.
    """
    if link_type == "nexus":
        return get_nexus_preview_data(**kwargs)
    elif link_type == "youtube":
        return get_youtube_preview_data(**kwargs)
    elif link_type == "imgur":
        return get_imgur_preview_data(**kwargs)
    elif link_type == "internal":
        return get_internal_preview_data(**kwargs)

    return {"type": "generic", "url": kwargs.get("url", "")}


def get_nexus_preview_data(game: str, mod_id: str) -> dict:
    """Get Nexus mod preview data."""
    # This would fetch from Nexus API or cache
    return {
        "type": "nexus",
        "game": game,
        "mod_id": mod_id,
        "loading": True,
        "preview_url": f"/api/link-preview/nexus/{game}/{mod_id}",
    }


def get_youtube_preview_data(video_id: str) -> dict:
    """Get YouTube video preview data."""
    return {
        "type": "youtube",
        "video_id": video_id,
        "thumbnail": f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg",
        "embed_url": f"https://www.youtube.com/embed/{video_id}",
        "title": "YouTube Video",
    }


def get_imgur_preview_data(img_id: str) -> dict:
    """Get Imgur image preview data."""
    return {
        "type": "imgur",
        "img_id": img_id,
        "image_url": f"https://i.imgur.com/{img_id}.jpg",
        "thumbnail": f"https://i.imgur.com/{img_id}s.jpg",
    }


def get_internal_preview_data(page: str) -> dict:
    """Get internal page preview data."""
    # Map to internal sections
    section_map = {
        "analyze": "Mod Analysis",
        "quickstart": "Quick Start Guide",
        "build": "Build-a-List",
        "library": "Your Saved Lists",
        "community": "Community Discussions",
        "gameplay": "Gameplay Engine",
        "dev": "Developer Tools",
    }

    title = section_map.get(page.lower(), page)

    return {
        "type": "internal",
        "page": page,
        "title": title,
        "url": INTERNAL_LINKS.get(page.lower(), "/"),
    }


def extract_all_links(text: str) -> List[Dict]:
    """Extract all links from text with metadata."""
    links = []

    # Extract each type
    for link_type, pattern in LINK_PATTERNS.items():
        for match in re.finditer(pattern, text):
            links.append({
                "type": link_type,
                "text": match.group(0),
                "groups": match.groups(),
                "start": match.start(),
                "end": match.end(),
            })

    return sorted(links, key=lambda x: x["start"])


def suggest_related_links(context: dict) -> List[Dict]:
    """
    Suggest related links based on current context.

    Args:
        context: Current page context (game, mods, etc.)

    Returns:
        List of suggested links with URLs and labels
    """
    suggestions = []

    game_id = context.get("game_id")
    mod_list = context.get("mod_list", [])

    # Suggest tool sections based on context
    if mod_list:
        suggestions.append({
            "label": "Analyze Your List",
            "url": "/#panel-analyze",
            "type": "internal",
            "icon": "🔍",
        })

    # Suggest Nexus based on game
    if game_id:
        nexus_games = {
            "skyrimse": "skyrimspecialedition",
            "skyrim": "skyrim",
            "fallout4": "fallout4",
            "starfield": "starfield",
        }
        nexus_slug = nexus_games.get(game_id, game_id)
        suggestions.append({
            "label": f"Browse {game_id} Mods on Nexus",
            "url": f"https://www.nexusmods.com/{nexus_slug}/",
            "type": "external",
            "icon": "📦",
        })

    # Suggest guides
    if len(mod_list) > 50:
        suggestions.append({
            "label": "Read: Managing Large Mod Lists",
            "url": "/quickstart#large-lists",
            "type": "internal",
            "icon": "📖",
        })

    return suggestions
