"""
Research Pipeline - Autonomous internet research for SkyModderAI.

Sources:
- Nexus Mods API (new/updated mods)
- Reddit (r/skyrimmods, r/fo4mods, r/modding)
- Bethesda.net forums
- GitHub (modding tools)

All sources are scored for reliability and added to knowledge base.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from db import get_db_session
from models import KnowledgeSource, SourceCredibility, UserActivity

logger = logging.getLogger(__name__)


def run_research_cycle() -> Dict[str, Any]:
    """
    Run full research cycle.
    
    Returns:
        {
            "nexus": {"mods_found": int, "added": int},
            "reddit": {"posts_found": int, "added": int},
            "forums": {"threads_found": int, "added": int},
            "github": {"repos_found": int, "added": int},
            "total_added": int
        }
    """
    logger.info("Starting research cycle...")
    start_time = datetime.now()
    
    results = {
        "nexus": scrape_nexus_mods(),
        "reddit": scrape_reddit(),
        "forums": scrape_forums(),
        "github": scrape_github()
    }
    
    results["total_added"] = sum(r.get("added", 0) for r in results.values())
    
    duration = (datetime.now() - start_time).total_seconds()
    logger.info(f"Research cycle completed in {duration:.2f}s: {results['total_added']} items added")
    
    # Track activity
    track_research_run(results)
    
    return results


def scrape_nexus_mods() -> Dict[str, Any]:
    """
    Scrape Nexus Mods API for new and updated mods.
    
    Requires Nexus API key from environment:
    export NEXUS_API_KEY=your_key_here
    
    Returns:
        {"mods_found": int, "added": int, "errors": int}
    """
    logger.info("Scraping Nexus Mods...")
    
    import os
    api_key = os.getenv('NEXUS_API_KEY')
    
    if not api_key:
        logger.warning("NEXUS_API_KEY not set. Skipping Nexus scrape.")
        return {"mods_found": 0, "added": 0, "errors": 0, "skipped": True}
    
    try:
        import requests
        from reliability_weighter import get_reliability_weighter
        
        session = get_db_session()
        weighter = get_reliability_weighter()
        
        # Nexus API endpoints
        base_url = "https://api.nexusmods.com/v1"
        headers = {
            "apikey": api_key,
            "User-Agent": "SkyModderAI/1.0 (Research Pipeline)"
        }
        
        # Games to scrape
        games = {
            "skyrimse": "skyrimspecialedition",
            "skyrim": "skyrim",
            "skyrimvr": "skyrimspecialedition",  # Same as SE
            "fallout4": "fallout4",
            "falloutnv": "newvegas",
            "oblivion": "oblivion"
        }
        
        mods_found = 0
        added = 0
        errors = 0
        
        for game_id, nexus_game in games.items():
            try:
                # Get recently updated mods
                url = f"{base_url}/games/{nexus_game}/mods/updated.json"
                params = {"period": "1w"}  # Last week
                
                response = requests.get(url, headers=headers, params=params, timeout=30)
                if response.status_code != 200:
                    logger.warning(f"Nexus API returned {response.status_code} for {nexus_game}")
                    errors += 1
                    continue
                
                mods = response.json().get("mods", [])
                mods_found += len(mods)
                
                # Process each mod
                for mod in mods[:50]:  # Limit to top 50 per game
                    try:
                        mod_info = process_nexus_mod(mod, game_id, nexus_game, headers, base_url)
                        if mod_info:
                            # Score reliability
                            score = weighter.score_source({
                                "url": mod_info["source_url"],
                                "type": "nexus_mods",
                                "endorsements": mod_info.get("endorsements", 0),
                                "published_date": mod_info.get("created_at"),
                                "updated_date": mod_info.get("updated_at"),
                                "author": mod_info.get("author"),
                                "content": mod_info.get("summary", ""),
                                "game_version": game_id
                            })
                            
                            # Add to knowledge base
                            add_knowledge_source(session, mod_info, score)
                            added += 1
                            
                    except Exception as e:
                        logger.debug(f"Error processing Nexus mod: {e}")
                        errors += 1
                
            except Exception as e:
                logger.warning(f"Error scraping {nexus_game}: {e}")
                errors += 1
        
        session.commit()
        
        result = {"mods_found": mods_found, "added": added, "errors": errors}
        logger.info(f"Nexus scrape complete: {result}")
        return result
        
    except Exception as e:
        logger.exception(f"Nexus scrape failed: {e}")
        return {"mods_found": 0, "added": 0, "errors": 1, "error": str(e)}


def process_nexus_mod(mod: Dict[str, Any], game_id: str, nexus_game: str, 
                      headers: Dict[str, str], base_url: str) -> Optional[Dict[str, Any]]:
    """Process a single Nexus mod into knowledge source format."""
    try:
        mod_id = mod.get("id")
        if not mod_id:
            return None
        
        # Get full mod details
        detail_url = f"{base_url}/games/{nexus_game}/mods/{mod_id}.json"
        response = requests.get(detail_url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
        
        details = response.json()
        
        # Extract relevant info
        return {
            "source_url": f"https://www.nexusmods.com/{nexus_game}/mods/{mod_id}",
            "title": details.get("name", "Unknown Mod"),
            "summary": (details.get("summary", "") or "")[:500],
            "game": game_id,
            "game_version": None,  # Nexus doesn't provide this consistently
            "mod_version": details.get("version", ""),
            "category": categorize_nexus_mod(details),
            "subcategory": None,
            "tags": extract_nexus_tags(details),
            "author": details.get("author", ""),
            "endorsements": details.get("endorsement_count", 0),
            "created_at": datetime.fromtimestamp(details.get("created_time", 0)).isoformat() if details.get("created_time") else None,
            "updated_at": datetime.fromtimestamp(details.get("updated_time", 0)).isoformat() if details.get("updated_time") else None,
            "content_hash": None,  # Will be computed
            "requires": extract_requirements(details),
            "conflicts_with": None,
            "compatible_with": None,
            "deviation_flags": None,
            "is_standard_approach": True,
            "status": "active"
        }
        
    except Exception as e:
        logger.debug(f"Error processing Nexus mod details: {e}")
        return None


def categorize_nexus_mod(details: Dict[str, Any]) -> str:
    """Categorize Nexus mod based on its properties."""
    categories = details.get("categories", [])
    category_ids = [c.get("category_id") for c in categories] if categories else []
    
    # Category mapping from Nexus IDs
    if 1 in category_ids:  # Armour
        return "design"
    elif 2 in category_ids:  # Art
        return "design"
    elif 3 in category_ids:  # Audio
        return "design"
    elif 6 in category_ids:  # Gameplay
        return "fun"
    elif 7 in category_ids:  # Items
        return "fun"
    elif 8 in category_ids:  # Landscapes
        return "environmental"
    elif 9 in category_ids:  # Models and Textures
        return "design"
    elif 10 in category_ids:  # Overhauls
        return "fun"
    elif 11 in category_ids:  # Patches
        return "utility"
    elif 12 in category_ids:  # Player Homes
        return "environmental"
    elif 13 in category_ids:  # Quests
        return "fun"
    elif 14 in category_ids:  # Utilities
        return "utility"
    elif 15 in category_ids:  # Visuals and Graphics
        return "design"
    
    return "uncategorized"


def extract_nexus_tags(details: Dict[str, Any]) -> List[str]:
    """Extract tags from Nexus mod."""
    tags = []
    
    # Add category tags
    categories = details.get("categories", [])
    for cat in categories:
        if cat.get("name"):
            tags.append(cat["name"].lower().replace(" ", "_"))
    
    # Add version tags
    game_versions = details.get("game_versions", [])
    for version in game_versions:
        tags.append(f"version_{version}")
    
    # Add mod type tags
    if details.get("contains_bsa"):
        tags.append("has_bsa")
    if details.get("is_featured"):
        tags.append("featured")
    
    return tags[:20]  # Limit tags


def extract_requirements(details: Dict[str, Any]) -> List[str]:
    """Extract mod requirements from Nexus data."""
    requirements = []
    
    # Nexus doesn't provide structured requirements, so we extract from description
    description = details.get("description", "") or ""
    
    # Look for common requirement patterns
    import re
    
    # SKSE
    if re.search(r'SKSE|Script Extender', description, re.IGNORECASE):
        requirements.append("SKSE")
    
    # Address Library
    if re.search(r'Address Library|All in one', description, re.IGNORECASE):
        requirements.append("Address Library for SKSE")
    
    # Engine Fixes
    if re.search(r'Engine Fixes', description, re.IGNORECASE):
        requirements.append("Engine Fixes")
    
    # Other mods mentioned
    mod_mentions = re.findall(r'\[([^\]]+)\]\(https://www\.nexusmods\.com/[^\)]+/mods/(\d+)\)', description)
    for mod_name, mod_id in mod_mentions[:5]:  # Limit to 5
        requirements.append(mod_name)
    
    return requirements


def scrape_reddit() -> Dict[str, Any]:
    """
    Scrape Reddit for modding discussions.
    
    Subreddits:
    - r/skyrimmods
    - r/fo4mods
    - r/modding
    
    Returns:
        {"posts_found": int, "added": int, "errors": int}
    """
    logger.info("Scraping Reddit...")
    
    try:
        import requests
        from reliability_weighter import get_reliability_weighter
        
        session = get_db_session()
        weighter = get_reliability_weighter()
        
        subreddits = [
            ("skyrimmods", "skyrimse"),
            ("fo4mods", "fallout4"),
            ("modding", "general")
        ]
        
        posts_found = 0
        added = 0
        errors = 0
        
        for subreddit, game_id in subreddits:
            try:
                # Reddit JSON endpoint (no auth required for public subs)
                url = f"https://www.reddit.com/r/{subreddit}/hot.json"
                headers = {"User-Agent": "SkyModderAI/1.0 (Research Pipeline)"}
                
                response = requests.get(url, headers=headers, timeout=30)
                if response.status_code != 200:
                    logger.warning(f"Reddit returned {response.status_code} for r/{subreddit}")
                    errors += 1
                    continue
                
                data = response.json()
                posts = data.get("data", {}).get("children", [])
                posts_found += len(posts)
                
                # Process each post
                for post in posts[:30]:  # Limit to top 30 per subreddit
                    try:
                        post_data = post.get("data", {})
                        
                        # Skip if no selftext (link posts only)
                        if not post_data.get("selftext"):
                            continue
                        
                        # Score reliability
                        score = weighter.score_source({
                            "url": f"https://www.reddit.com/r/{subreddit}/comments/{post_data.get('id')}",
                            "type": "reddit_general",
                            "upvotes": post_data.get("ups", 0),
                            "comments": post_data.get("num_comments", 0),
                            "published_date": datetime.fromtimestamp(post_data.get("created_utc", 0)).isoformat() if post_data.get("created_utc") else None,
                            "author": post_data.get("author", ""),
                            "content": post_data.get("selftext", "")[:2000],
                            "game_version": game_id
                        })
                        
                        # Add to knowledge base if score is good
                        if score.overall_score >= 0.5:
                            knowledge = {
                                "source_url": f"https://www.reddit.com/r/{subreddit}/comments/{post_data.get('id')}",
                                "title": post_data.get("title", "")[:500],
                                "summary": (post_data.get("selftext", "") or "")[:1000],
                                "game": game_id,
                                "category": "community_discussion",
                                "tags": ["reddit", subreddit],
                                "author": post_data.get("author", ""),
                                "upvotes": post_data.get("ups", 0),
                                "comments": post_data.get("num_comments", 0),
                                "created_at": datetime.fromtimestamp(post_data.get("created_utc", 0)).isoformat() if post_data.get("created_utc") else None,
                                "status": "active"
                            }
                            
                            add_knowledge_source(session, knowledge, score)
                            added += 1
                            
                    except Exception as e:
                        logger.debug(f"Error processing Reddit post: {e}")
                        errors += 1
                
            except Exception as e:
                logger.warning(f"Error scraping r/{subreddit}: {e}")
                errors += 1
        
        session.commit()
        
        result = {"posts_found": posts_found, "added": added, "errors": errors}
        logger.info(f"Reddit scrape complete: {result}")
        return result
        
    except Exception as e:
        logger.exception(f"Reddit scrape failed: {e}")
        return {"posts_found": 0, "added": 0, "errors": 1, "error": str(e)}


def scrape_forums() -> Dict[str, Any]:
    """
    Scrape forums for modding discussions.
    
    Forums:
    - Bethesda.net
    - Nexus Forums
    
    Returns:
        {"threads_found": int, "added": int, "errors": int}
    """
    logger.info("Scraping forums...")
    
    # Forum scraping is complex and often requires authentication
    # For now, we'll skip and log that it needs implementation
    
    logger.info("Forum scraping requires authentication. Skipping for now.")
    return {"threads_found": 0, "added": 0, "errors": 0, "skipped": True, "note": "Requires forum API access"}


def scrape_github() -> Dict[str, Any]:
    """
    Scrape GitHub for modding tools and resources.
    
    Returns:
        {"repos_found": int, "added": int, "errors": int}
    """
    logger.info("Scraping GitHub...")
    
    try:
        import requests
        import os
        from reliability_weighter import get_reliability_weighter
        
        session = get_db_session()
        weighter = get_reliability_weighter()
        
        # GitHub API (optional token for higher rate limits)
        token = os.getenv('GITHUB_TOKEN')
        headers = {"User-Agent": "SkyModderAI/1.0 (Research Pipeline)"}
        if token:
            headers["Authorization"] = f"token {token}"
        
        # Search for modding tools
        search_queries = [
            "skyrim modding tools",
            "fallout modding",
            "bethesda modding",
            "skse plugin",
            "xedit script"
        ]
        
        repos_found = 0
        added = 0
        errors = 0
        
        for query in search_queries:
            try:
                url = "https://api.github.com/search/repositories"
                params = {
                    "q": query,
                    "sort": "stars",
                    "order": "desc",
                    "per_page": 10
                }
                
                response = requests.get(url, headers=headers, params=params, timeout=30)
                if response.status_code != 200:
                    logger.warning(f"GitHub API returned {response.status_code}")
                    errors += 1
                    continue
                
                data = response.json()
                repos = data.get("items", [])
                repos_found += len(repos)
                
                # Process each repo
                for repo in repos:
                    try:
                        # Score reliability
                        score = weighter.score_source({
                            "url": repo.get("html_url"),
                            "type": "github",
                            "author_contributions": repo.get("stargazers_count", 0),
                            "published_date": repo.get("created_at"),
                            "updated_date": repo.get("updated_at"),
                            "content": repo.get("description", ""),
                            "game_version": "general"
                        })
                        
                        # Add to knowledge base if score is good
                        if score.overall_score >= 0.6:
                            knowledge = {
                                "source_url": repo.get("html_url"),
                                "title": repo.get("name", "")[:500],
                                "summary": (repo.get("description", "") or "")[:1000],
                                "game": "general",
                                "category": "tool",
                                "subcategory": "modding_tool",
                                "tags": ["github", "tool", "open_source"],
                                "author": repo.get("owner", {}).get("login", ""),
                                "stars": repo.get("stargazers_count", 0),
                                "forks": repo.get("forks_count", 0),
                                "created_at": repo.get("created_at"),
                                "updated_at": repo.get("updated_at"),
                                "status": "active"
                            }
                            
                            add_knowledge_source(session, knowledge, score)
                            added += 1
                            
                    except Exception as e:
                        logger.debug(f"Error processing GitHub repo: {e}")
                        errors += 1
                
            except Exception as e:
                logger.warning(f"Error scraping GitHub for '{query}': {e}")
                errors += 1
        
        session.commit()
        
        result = {"repos_found": repos_found, "added": added, "errors": errors}
        logger.info(f"GitHub scrape complete: {result}")
        return result
        
    except Exception as e:
        logger.exception(f"GitHub scrape failed: {e}")
        return {"repos_found": 0, "added": 0, "errors": 1, "error": str(e)}


def add_knowledge_source(session, knowledge: Dict[str, Any], score) -> bool:
    """Add knowledge source to database with credibility score."""
    try:
        # Check if already exists
        existing = session.query(KnowledgeSource).filter(
            KnowledgeSource.source_url == knowledge["source_url"]
        ).first()
        
        if existing:
            logger.debug(f"Knowledge source already exists: {knowledge['source_url']}")
            return False
        
        # Create credibility record
        credibility = SourceCredibility(
            source_url=knowledge["source_url"],
            source_type="nexus_mods" if "nexusmods" in knowledge["source_url"] else 
                       "reddit" if "reddit" in knowledge["source_url"] else
                       "github" if "github" in knowledge["source_url"] else "unknown",
            overall_score=score.overall_score,
            source_credibility=score.source_credibility,
            content_freshness=score.content_freshness,
            community_validation=score.community_validation,
            technical_accuracy=score.technical_accuracy,
            author_reputation=score.author_reputation,
            confidence=score.confidence,
            flags=json.dumps(score.flags) if score.flags else None
        )
        session.add(credibility)
        session.flush()  # Get ID
        
        # Create knowledge source
        import hashlib
        content_for_hash = f"{knowledge.get('title', '')}|{knowledge.get('summary', '')}|{knowledge.get('game', '')}"
        content_hash = hashlib.sha256(content_for_hash.encode()).hexdigest()
        
        source = KnowledgeSource(
            source_url=knowledge["source_url"],
            title=knowledge["title"],
            content_hash=content_hash,
            game=knowledge.get("game", "unknown"),
            game_version=knowledge.get("game_version"),
            mod_version=knowledge.get("mod_version"),
            category=knowledge.get("category", "uncategorized"),
            subcategory=knowledge.get("subcategory"),
            tags=json.dumps(knowledge.get("tags", [])) if knowledge.get("tags") else None,
            credibility_id=credibility.id,
            summary=knowledge.get("summary"),
            key_points=None,
            conflicts_with=None,
            requires=json.dumps(knowledge.get("requires", [])) if knowledge.get("requires") else None,
            compatible_with=None,
            deviation_flags=None,
            is_standard_approach=knowledge.get("is_standard_approach", True),
            status=knowledge.get("status", "active")
        )
        session.add(source)
        
        logger.debug(f"Added knowledge source: {knowledge['source_url']}")
        return True
        
    except Exception as e:
        logger.debug(f"Error adding knowledge source: {e}")
        session.rollback()
        return False


def track_research_run(results: Dict[str, Any]):
    """Track research run in database."""
    try:
        activity = UserActivity(
            event_type="research_run",
            event_data=json.dumps(results),
            session_id="system"
        )
        session = get_db_session()
        session.add(activity)
        session.commit()
    except Exception as e:
        logger.debug(f"Failed to track research run: {e}")


# Import json for the module
import json
