from __future__ import annotations

# Web search fallback for mod discovery.
# Uses DuckDuckGo via duckduckgo-search (no API key required).
# Filters out sponsored/commercial results before AI sees them.
# Graceful degradation: retries once on failure, returns partial results.
import logging
import re
import time
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

WEB_SEARCH_RETRY_DELAY = 1.5  # seconds between retries

# Allowed domains for search results — only trusted modding sources
ALLOWED_DOMAINS = [
    "nexusmods.com",
    "reddit.com",
    "github.com",
    "loot.github.io",
    "skse.silverlock.org",
    "f4se.silverlock.org",
    "tes5edit.github.io",
    "bethesda.net",
    "creationkit.com",
    "stepmodifications.org",
    "wiki.nexusmods.com",
    "afkmods.com",
    "loverslab.com",
    "moddb.com",
    "tesseractmodding.wordpress.com",
]

# Blocked phrases that indicate sponsored/commercial content
BLOCKED_PHRASES = [
    "buy now",
    "on sale",
    "discount",
    "best price",
    "deal",
    "promo",
    "coupon",
    "sponsored",
    "advertisement",
    "shop now",
    "limited time",
    "special offer",
]


def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except Exception as e:
        logger.debug(f"Failed to parse URL domain: {e}")
        return ""


def filter_search_results(results: list[dict]) -> list[dict]:
    """
    Filter search results to remove sponsored/commercial content.
    Only allows results from trusted modding domains.
    Blocks results with commercial phrases in snippets.
    """
    clean = []
    for r in results:
        url = r.get("url", "") or r.get("href", "")
        domain = extract_domain(url)
        snippet = (r.get("snippet", "") or r.get("body", "") or "").lower()
        title = (r.get("title", "") or "").lower()

        # Check if domain is allowed
        if not any(domain.endswith(d) for d in ALLOWED_DOMAINS):
            continue

        # Check for blocked phrases in snippet or title
        combined_text = snippet + " " + title
        if any(phrase in combined_text for phrase in BLOCKED_PHRASES):
            continue

        clean.append(r)

    return clean


# Plugin extensions we care about (.esm, .esp, .esl)
PLUGIN_EXT = re.compile(r"\.(esm|esp|esl)\b", re.I)


def _extract_plugin_names_from_text(text: str) -> list[str]:
    """Extract plugin-like names (Something.esp) from text."""
    if not text:
        return []
    # Match "Name.esp", "Name.esm", etc.
    found = set()
    for m in PLUGIN_EXT.finditer(text):
        start = m.start()
        # Walk back to find start of name (alphanumeric, spaces, underscores, hyphens)
        i = start - 1
        while i >= 0 and (text[i].isalnum() or text[i] in " _-"):
            i -= 1
        name = text[i + 1 : m.end()].strip()
        if len(name) > 3 and name not in ("", "esp", "esm", "esl", "esl"):
            found.add(name)
    return list(found)


def _extract_from_result(result: dict) -> list[str]:
    """Extract plugin names from a DDG result (title, href, body)."""
    names = []
    for key in ("title", "href", "body"):
        val = result.get(key) or ""
        names.extend(_extract_plugin_names_from_text(val))
    return names


def search_mods_web(
    query: str,
    game_display_name: str,
    nexus_slug: str,
    max_results: int = 15,
) -> list[dict]:
    """
    Search the web for mod/plugin names when DB has few matches.
    Returns list of {name, url, source} for display.

    No API key needed: uses duckduckgo-search (scrapes DDG).
    """
    if not query or len(query) < 2:
        return []

    try:
        from duckduckgo_search import DDGS
    except ImportError:
        logger.warning("duckduckgo-search not installed. Web search disabled.")
        return []

    seen = set()
    out: list[dict] = []

    # 1) Nexus-specific: site:nexusmods.com {game} {query}
    nexus_query = f"site:nexusmods.com {game_display_name} {query}"
    for attempt in range(2):  # Retry once on failure
        try:
            with DDGS() as ddgs:
                for r in ddgs.text(nexus_query, max_results=max_results):
                    for name in _extract_from_result(r):
                        name_norm = name.lower()
                        if name_norm not in seen:
                            seen.add(name_norm)
                            out.append(
                                {
                                    "name": name,
                                    "url": r.get("href", ""),
                                    "source": "nexus",
                                }
                            )
                            if len(out) >= max_results:
                                return out[:max_results]
            break
        except Exception as e:
            logger.warning("Web search (Nexus) attempt %d failed: %s", attempt + 1, e)
            if attempt == 0:
                time.sleep(WEB_SEARCH_RETRY_DELAY)

    # 2) Broader: "{game} mod {query}" for more slots
    if len(out) < max_results:
        broad_query = f'"{game_display_name}" mod {query} .esp OR .esm'
        for attempt in range(2):
            try:
                with DDGS() as ddgs:
                    for r in ddgs.text(broad_query, max_results=max_results):
                        for name in _extract_from_result(r):
                            name_norm = name.lower()
                            if name_norm not in seen:
                                seen.add(name_norm)
                                out.append(
                                    {
                                        "name": name,
                                        "url": r.get("href", ""),
                                        "source": "web",
                                    }
                                )
                                if len(out) >= max_results:
                                    return out[:max_results]
                break
            except Exception as e:
                logger.warning("Web search (broad) attempt %d failed: %s", attempt + 1, e)
                if attempt == 0:
                    time.sleep(WEB_SEARCH_RETRY_DELAY)

    # Filter results to remove sponsored/commercial content before AI sees them
    return filter_search_results(out)[:max_results]


def search_solutions_web(
    query: str,
    game_display_name: str,
    max_results: int = 10,
) -> list[dict]:
    """
    Search for scattered solutions (Reddit, forums, Nexus posts).
    Use for: "ctd skyrim", "infinite loading fix", "purple textures".
    Returns list of {title, url, snippet, source}.
    Results are filtered to remove sponsored/commercial content.
    """
    if not query or len(query.strip()) < 2:
        return []

    try:
        from duckduckgo_search import DDGS
    except ImportError:
        logger.warning("duckduckgo-search not installed. Solution search disabled.")
        return []

    out: list[dict] = []
    seen_urls = set()

    # 1) Reddit: r/skyrimmods, r/fo4, etc.
    reddit_query = f"site:reddit.com {game_display_name} mod {query}"
    for attempt in range(2):
        try:
            with DDGS() as ddgs:
                for r in ddgs.text(reddit_query, max_results=max_results):
                    url = r.get("href", "")
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)
                    out.append(
                        {
                            "title": r.get("title", ""),
                            "url": url,
                            "snippet": (r.get("body") or "")[:200],
                            "source": "reddit",
                        }
                    )
                    if len(out) >= max_results:
                        return out[:max_results]
            break
        except Exception as e:
            logger.warning("Solution search (Reddit) attempt %d failed: %s", attempt + 1, e)
            if attempt == 0:
                time.sleep(WEB_SEARCH_RETRY_DELAY)

    # 2) Broader: Nexus forums, general modding
    broad_query = f"{game_display_name} mod {query} fix solution"
    for attempt in range(2):
        try:
            with DDGS() as ddgs:
                for r in ddgs.text(broad_query, max_results=max_results):
                    url = r.get("href", "")
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)
                    source = "nexus" if "nexusmods" in url else "web"
                    out.append(
                        {
                            "title": r.get("title", ""),
                            "url": url,
                            "snippet": (r.get("body") or "")[:200],
                            "source": source,
                        }
                    )
                    if len(out) >= max_results:
                        return out[:max_results]
            break
        except Exception as e:
            logger.warning("Solution search (broad) attempt %d failed: %s", attempt + 1, e)
            if attempt == 0:
                time.sleep(WEB_SEARCH_RETRY_DELAY)

    # Filter results to remove sponsored/commercial content before AI sees them
    return filter_search_results(out)[:max_results]
