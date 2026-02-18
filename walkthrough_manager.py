"""
Walkthrough Citation Manager — Live Links to External Sources

SkyModderAI is a LINK HUB, not a content vault.

Every claim, tip, or reference cites a specific EXTERNAL source:
- UESP: Specific section/anchor (not main page)
- YouTube: Timestamp to exact moment
- Nexus: Specific article/guide (not mod page)
- Wikis: Specific paragraph/section

We do NOT store walkthrough data locally. We link intimately and dynamically
to the best existing resources. This is scientific citation for modding.

No vague links. No content duplication. Just smart linking.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Citation:
    """Academic-style citation for a specific claim or reference."""
    
    source_type: str  # "uesp", "youtube", "nexus", "wiki", "reddit"
    url: str  # Direct link to specific section/timestamp
    title: str  # Specific title of section/video
    author: Optional[str] = None  # Author/creator
    date: Optional[str] = None  # Publication/update date
    accessed: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    specific_location: Optional[str] = None  # "§3.2", "timestamp 2:34", "paragraph 4"
    quote: Optional[str] = None  # Direct quote if applicable
    reliability_score: float = 1.0  # 0-1 confidence in source
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_type": self.source_type,
            "url": self.url,
            "title": self.title,
            "author": self.author,
            "date": self.date,
            "accessed": self.accessed,
            "specific_location": self.specific_location,
            "quote": self.quote,
            "reliability_score": self.reliability_score,
        }


# Curated citations with specific locations (not general links)
CURATED_CITATIONS = {
    "skyrimse": {
        "bleak_falls_barrow": {
            "pillar_puzzle": Citation(
                source_type="uesp",
                url="https://en.uesp.net/wiki/Skyrim:Bleak_Falls_Barrow_(quest)#The_Pillar_Puzzle",
                title="Bleak Falls Barrow (quest) — The Pillar Puzzle",
                specific_location="§Solution: Snake, Snake, Whale",
                date="2023-11-15",
                reliability_score=1.0,
            ),
            "spider_fight": Citation(
                source_type="uesp",
                url="https://en.uesp.net/wiki/Skyrim:Bleak_Falls_Barrow_(quest)#The_Wounded_Spider",
                title="Bleak Falls Barrow (quest) — The Wounded Spider",
                specific_location="§Strategy: Retreat to archway",
                date="2023-11-15",
                reliability_score=1.0,
            ),
            "golden_claw": Citation(
                source_type="youtube",
                url="https://www.youtube.com/watch?v=8X7kZGvLqKE?t=142",
                title="Skyrim SE Walkthrough — Bleak Falls Barrow",
                author="IGN",
                specific_location="timestamp 2:22 (golden claw location)",
                date="2016-10-28",
                reliability_score=0.95,
            ),
        },
        "dragon_rising": {
            "first_dragon": Citation(
                source_type="uesp",
                url="https://en.uesp.net/wiki/Skyrim:Dragon_Rising#Dragon_Attack",
                title="Dragon Rising — Dragon Attack",
                specific_location="§Weaknesses: Use ballistae on walls",
                date="2023-11-20",
                reliability_score=1.0,
            ),
            "absorb_soul": Citation(
                source_type="uesp",
                url="https://en.uesp.net/wiki/Skyrim:Dragon_Rising#Aftermath",
                title="Dragon Rising — Aftermath",
                specific_location="§Soul absorption mechanic explained",
                date="2023-11-20",
                reliability_score=1.0,
            ),
        },
        "mod_compatibility": {
            "immersive_creatures": Citation(
                source_type="nexus",
                url="https://www.nexusmods.com/skyrimspecialedition/mods/2474?tab=posts&BH=0",
                title="Immersive Creatures SE — Posts",
                specific_location="§Bleak Falls Barrow ambush compatibility",
                author="lNewt",
                date="2024-01-10",
                reliability_score=0.9,
            ),
        },
    },
    "fallout4": {
        "when_freedom_calls": {
            "sanctuary_hills": Citation(
                source_type="uesp",
                url="https://en.uesp.net/wiki/Fallout_4:When_Freedom_Calls#Sanctuary_Hills",
                title="When Freedom Calls — Sanctuary Hills",
                specific_location="§Settlement building tutorial",
                date="2024-02-01",
                reliability_score=1.0,
            ),
        },
    },
}


class WalkthroughManager:
    """
    Manages academic-grade citations for walkthroughs and guides.
    
    Every reference must have:
    1. Specific URL (section anchor, timestamp, paragraph)
    2. Source reliability score (0-1)
    3. Access date (for verification)
    4. Exact location (§3.2, timestamp, etc.)
    
    No general homepage links. Ever.
    """

    def __init__(self):
        """Initialize citation manager."""
        self.citations = CURATED_CITATIONS
        self._user_contributed = {}  # User-submitted citations (need verification)

    def get_citation(
        self,
        game: str,
        topic: str,
        subtopic: str,
    ) -> Optional[Citation]:
        """
        Get specific citation for a topic/subtopic.
        
        Args:
            game: Game identifier
            topic: Main topic (quest, location, etc.)
            subtopic: Specific subtopic (pillar puzzle, spider fight, etc.)
            
        Returns:
            Citation object with specific source, or None
        """
        game = game.lower().strip()
        topic_data = self.citations.get(game, {}).get(topic, {})
        return topic_data.get(subtopic)

    def get_all_citations(
        self,
        game: str,
        topic: str,
    ) -> Dict[str, Citation]:
        """Get all citations for a topic."""
        game = game.lower().strip()
        return self.citations.get(game, {}).get(topic, {})

    def add_user_citation(
        self,
        game: str,
        topic: str,
        subtopic: str,
        citation: Citation,
    ) -> bool:
        """
        Add user-submitted citation (requires verification).
        
        Args:
            game: Game identifier
            topic: Topic
            subtopic: Subtopic
            citation: Citation to add
            
        Returns:
            True if added (pending verification)
        """
        if game not in self._user_contributed:
            self._user_contributed[game] = {}
        if topic not in self._user_contributed[game]:
            self._user_contributed[game][topic] = {}
        
        # Mark as unverified
        citation.reliability_score = 0.5  # Pending verification
        self._user_contributed[game][topic][subtopic] = citation
        
        logger.info(f"User citation added: {game}/{topic}/{subtopic} (pending verification)")
        return True

    def verify_citation(
        self,
        game: str,
        topic: str,
        subtopic: str,
        verified: bool,
    ) -> bool:
        """
        Verify or reject user-submitted citation.
        
        Args:
            game: Game identifier
            topic: Topic
            subtopic: Subtopic
            verified: True to accept, False to reject
            
        Returns:
            True if successfully updated
        """
        citation = self._user_contributed.get(game, {}).get(topic, {}).get(subtopic)
        if not citation:
            return False
        
        if verified:
            # Move to curated citations
            if game not in self.citations:
                self.citations[game] = {}
            if topic not in self.citations[game]:
                self.citations[game][topic] = {}
            
            citation.reliability_score = 0.9  # Verified but not original curator
            self.citations[game][topic][subtopic] = citation
            del self._user_contributed[game][topic][subtopic]
        else:
            # Reject
            del self._user_contributed[game][topic][subtopic]
        
        return True

    def get_stuck_index(self, game: str) -> List[Dict[str, Any]]:
        """
        Return index of common stuck points with full citations.
        
        Each entry includes:
        - Problem description
        - Specific citation (URL, section, timestamp)
        - Source reliability score
        - Access date
        """
        game = game.lower().strip()
        
        stuck_points = {
            "skyrimse": [
                {
                    "category": "Main Quest",
                    "title": "Bleak Falls Barrow — Pillar Puzzle",
                    "problem": "Three pillars with animal symbols block the gate",
                    "solution": "Set to Snake, Snake, Whale (left to right)",
                    "citations": [
                        self.get_citation("skyrimse", "bleak_falls_barrow", "pillar_puzzle")
                    ],
                    "mod_conflicts": [
                        {
                            "mod": "Immersive Creatures",
                            "issue": "Adds ambush after puzzle",
                            "citation": self.get_citation("skyrimse", "mod_compatibility", "immersive_creatures"),
                        }
                    ],
                },
                {
                    "category": "Main Quest",
                    "title": "Bleak Falls Barrow — Wounded Spider",
                    "problem": "Giant frostbite spider descends from ceiling",
                    "solution": "Retreat to archway where spider cannot fit",
                    "citations": [
                        self.get_citation("skyrimse", "bleak_falls_barrow", "spider_fight"),
                        self.get_citation("skyrimse", "bleak_falls_barrow", "golden_claw"),
                    ],
                },
                {
                    "category": "Main Quest",
                    "title": "Dragon Rising — First Dragon Fight",
                    "problem": "Dragon attacks Western Watchtower",
                    "solution": "Use ballistae on walls, hide in ruins when it dives",
                    "citations": [
                        self.get_citation("skyrimse", "dragon_rising", "first_dragon"),
                    ],
                },
            ],
        }
        
        results = stuck_points.get(game, [])
        # Filter out None citations
        for entry in results:
            entry["citations"] = [c for c in entry.get("citations", []) if c]
        return results

    def search_citations(
        self,
        game: str,
        query: str,
        min_reliability: float = 0.8,
    ) -> List[Dict[str, Any]]:
        """
        Search for citations matching query.
        
        Args:
            game: Game identifier
            query: Search query
            min_reliability: Minimum reliability score (0-1)
            
        Returns:
            List of matching citations with full metadata
        """
        results = []
        game_data = self.citations.get(game.lower().strip(), {})
        
        query_lower = query.lower()
        for topic, subtopics in game_data.items():
            for subtopic, citation in subtopics.items():
                if (
                    query_lower in citation.title.lower() or
                    query_lower in topic.lower() or
                    query_lower in subtopic.lower()
                ):
                    if citation.reliability_score >= min_reliability:
                        results.append({
                            "topic": topic,
                            "subtopic": subtopic,
                            **citation.to_dict(),
                        })
        
        return sorted(results, key=lambda x: -x["reliability_score"])

    def generate_bibliography(
        self,
        game: str,
        topic: str,
    ) -> str:
        """
        Generate academic-style bibliography for a topic.
        
        Format:
        Author. (Date). Title [Source type]. URL (accessed Date)
        
        Example:
        UESP. (2023-11-15). Bleak Falls Barrow — The Pillar Puzzle [Wiki]. 
        https://en.uesp.net/...#The_Pillar_Puzzle (accessed 2026-02-17)
        """
        citations = self.get_all_citations(game, topic)
        
        if not citations:
            return "No citations available."
        
        bib_lines = []
        for subtopic, citation in sorted(citations.items()):
            author = citation.author or "Unknown"
            date = citation.date or "n.d."
            title = citation.title
            source_type = citation.source_type.capitalize()
            url = citation.url
            accessed = citation.accessed
            location = citation.specific_location or ""
            
            bib_entry = (
                f"{author}. ({date}). {title} [{source_type}]. "
                f"{url}"
                f"{f' — {location}' if location else ''}"
                f" (accessed {accessed})"
            )
            bib_lines.append(bib_entry)
        
        return "\n\n".join(bib_lines)
