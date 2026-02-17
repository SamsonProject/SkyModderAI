"""
SkyModderAI Search Engine — Ferrari-grade ranking for Bethesda modding.

Implements:
- BM25 ranking (Okapi BM25, industry standard for relevance)
- Multi-signal scoring (relevance + authority + specificity)
- Query expansion (abbreviations, synonyms, common typos)
- Inverted index for sub-50ms lookups
- Structured output for AI assistant navigation

No external search libs—pure Python, zero API keys.
"""

import logging
import math
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# Query expansion: Bethesda modding slang, abbreviations, synonyms
# -------------------------------------------------------------------
_QUERY_EXPANSIONS = {
    # Abbreviations → full terms (for matching)
    "ussep": ["unofficial skyrim special edition patch", "ussep"],
    "usleep": ["unofficial skyrim legendary edition patch", "usleep"],
    "uskp": ["unofficial skyrim patch", "uskp"],
    "skse": ["skse", "skyrim script extender"],
    "fnis": ["fnis", "fores new idles"],
    "nemesis": ["nemesis", "nemesis engine"],
    "dar": ["dynamic animation replacer", "dar"],
    "oar": ["open animation replacer", "oar"],
    "sse": ["skyrim special edition", "sse"],
    "le": ["legendary edition", "skyrim le"],
    "vr": ["skyrim vr", "vr"],
    "enb": ["enb", "enbseries"],
    "smp": ["smp", "hdt smp", "physics"],
    "cbbe": ["cbbe", "caliente"],
    "unp": ["unp", "unpb"],
    "smim": ["smim", "static mesh improvement"],
    "dyndolod": ["dyndolod", "dynamic lod"],
    "xedit": ["xedit", "sseedit", "tes5edit", "fo4edit"],
    "loot": ["loot", "load order"],
    "mo2": ["mod organizer", "mo2"],
    "vortex": ["vortex", "nexus mod manager"],
    "ctd": ["crash", "ctd", "crash to desktop"],
    "ils": ["infinite loading", "ils", "loading screen"],
    "papyrus": ["papyrus", "script", "scripts"],
    "skeleton": ["skeleton", "xp32", "xpmse"],
    "bodyslide": ["bodyslide", "body slide"],
    "wabbajack": ["wabbajack", "wabbajack list"],
    "requiem": ["requiem", "requiem the roleplaying overhaul"],
    "ordinator": ["ordinator", "ordinator perks"],
    "immersive": ["immersive", "immersive citizens"],
    "legacy": ["legacy", "legacy of the dragonborn", "lotd"],
    "bruma": ["bruma", "beyond skyrim", "bs bruma"],
    "parallax": ["parallax", "parallax textures"],
    "grass": ["grass", "grass mod", "landscape"],
    "weather": ["weather", "obsidian", "cathedral", "rustic"],
}

# Common typos / variants (query → corrections to try)
_TYPO_MAP = {
    "ordinator": ["ordinator", "ordinatior", "ordnator", "ordintor"],
    "immersive": ["immersive", "imersive", "immerssive", "immersiev", "imerssive"],
    "unofficial": ["unofficial", "unoffical", "unofficail", "unoficial"],
    "alternate": ["alternate", "alternative", "alternet", "altarnate"],
    "relationship": ["relationship", "relation", "relationship dialogue", "relatinship"],
    "cutting": ["cutting", "cutting room floor", "crf", "cuttting", "cuting"],
    "falskaar": ["falskaar", "falskar", "falskar", "falskaarr"],
    "dragonborn": ["dragonborn", "dragon born", "dragonborne", "dragonbourn"],
    "dawnguard": ["dawnguard", "dawn guard", "dawn gaurd", "dawnquard"],
    "hearthfire": ["hearthfire", "hearth fire", "hearthfires", "hearthfyre"],
    "skyui": ["skyui", "sky ui", "sky ui se", "skyuise", "skyu i"],
    "sseedit": ["sseedit", "xedit", "tes5edit", "sse edit", "sse edt"],
    "dyndolod": ["dyndolod", "dyndolad", "dynolod", "dyndoload", "dynadolod"],
    "requiem": ["requiem", "requeim", "requim", "requeam"],
    "enbseries": ["enbseries", "enb series", "enbs", "enb"],
    "caliente": ["caliente", "caliente body", "cbbe", "cbbec"],
    "bodyslide": ["bodyslide", "body slide", "bodyslyde", "bodyslid"],
    "nemesis": ["nemesis", "nemisis", "nemesys", "nemesys engine"],
    "skse": ["skse", "skyrim script extender", "skskyrim", "skscriptextender"],
    "smim": ["smim", "static mesh improvement", "staticmeshimprovement", "smimse"],
    "ussep": ["ussep", "unofficial patch", "unofficial sse patch"],
    "wabbajack": ["wabbajack", "wabajack", "wabbajak", "wabajak"],
    "parallax": ["parallax", "paralax", "parallux", "paralax"],
    "enbhelper": ["enbhelper", "enb helper", "enbhelpers", "enbhelpeer"],
    "skeleton": ["skeleton", "xp32", "xpmse", "skeletal"],
    "animation": ["animation", "animations", "anims", "animmations"],
    "texture": ["texture", "textures", "texure", "textur"],
    "modlist": ["modlist", "mod list", "loadorder", "load order"],
    "modorganizer": ["modorganizer", "mod organizer", "mo2", "modorg"],
    "nexusmods": ["nexusmods", "nexus mods", "nexus", "nexusmod"],
    "scriptextender": ["scriptextender", "script extender", "skse", "f4se", "fose"],
    "unofficialskyrimspecialeditionpatch": [
        "unofficialskyrimspecialeditionpatch",
        "ussep",
        "unofficial sse patch",
        "unofficial skyrim patch",
    ],
    "skyrimscriptextender": ["skyrimscriptextender", "skse", "skyrim se script extender", "skse64"],
}


def _tokenize(text: str) -> List[str]:
    """Tokenize: lowercase, split on non-alphanumeric, filter short tokens."""
    if not text:
        return []
    text = text.lower().strip()
    tokens = re.findall(r"[a-z0-9]+", text)
    return [t for t in tokens if len(t) >= 2]


def _expand_query(tokens: List[str]) -> List[str]:
    """Expand query tokens with abbreviations and synonyms. Returns expanded token set."""
    expanded = set(tokens)
    for t in tokens:
        if t in _QUERY_EXPANSIONS:
            expanded.update(_QUERY_EXPANSIONS[t])
        if t in _TYPO_MAP:
            expanded.update(_TYPO_MAP[t])
    return list(expanded)


@dataclass
class SearchResult:
    """A single search result with score breakdown for transparency."""

    mod_name: str
    clean_name: str
    score: float
    score_breakdown: Dict[str, float] = field(default_factory=dict)
    matched_fields: List[str] = field(default_factory=list)
    snippet: Optional[str] = None
    mod_info: Optional[Dict] = None  # requirements, tags, etc. for AI context
    nexus_mod_id: Optional[int] = None  # Nexus Mods ID for direct linking
    picture_url: Optional[str] = None  # URL to mod's primary image


class ModSearchEngine:
    """
    BM25 + multi-signal search engine for mod discovery.
    Indexes mod name, requirements, incompatibilities, load_after, tags, messages.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Args:
            k1: BM25 term frequency saturation (1.2–2.0 typical)
            b: BM25 length normalization (0.75 typical)
        """
        self.k1 = k1
        self.b = b
        self._documents: List[Dict] = []
        self._doc_id_to_mod: Dict[int, str] = {}
        self._inverted_index: Dict[str, List[Tuple[int, int]]] = defaultdict(
            list
        )  # term -> [(doc_id, tf)]
        self._doc_lengths: List[int] = []
        self._avg_doc_length: float = 0.0
        self._n_docs: int = 0
        self._df: Dict[str, int] = {}  # document frequency per term
        self._authority: Dict[
            str, int
        ] = {}  # mod -> how many other mods reference it (load_after, req, etc.)

    def index_parser(self, parser) -> None:
        """
        Build index from LOOTParser.mod_database.
        Each mod becomes a document with fields: name, requirements, incompatibilities, load_after, tags, messages.
        """
        self._documents = []
        self._doc_id_to_mod = {}
        self._inverted_index = defaultdict(list)
        self._doc_lengths = []
        self._authority = defaultdict(int)

        for clean_name, info in parser.mod_database.items():
            # Build document text from all searchable fields
            parts = [
                info.name,
                " ".join(info.requirements or []),
                " ".join(info.incompatibilities or []),
                " ".join(info.load_after or []),
                " ".join(info.load_before or []),
                " ".join(info.tags or []),
                " ".join(info.messages or []),
            ]
            for p in info.patches or []:
                if isinstance(p, dict):
                    parts.append(" ".join(str(v) for v in p.values()))
                else:
                    parts.append(str(p))

            doc_text = " ".join(p for p in parts if p)
            tokens = _tokenize(doc_text)
            if not tokens:
                continue

            doc_id = len(self._documents)
            self._documents.append(
                {
                    "mod_name": info.name,
                    "clean_name": clean_name,
                    "tokens": tokens,
                    "info": info,
                }
            )
            self._doc_id_to_mod[doc_id] = info.name

            # TF per term in this doc
            tf_local = defaultdict(int)
            for t in tokens:
                tf_local[t] += 1
            for term, tf in tf_local.items():
                self._inverted_index[term].append((doc_id, tf))

            self._doc_lengths.append(len(tokens))

            # Authority: mods that are required/load_after'd by others get boosted
            for _ in info.requirements or []:
                self._authority[clean_name] += 1
            for _ in info.load_after or []:
                self._authority[clean_name] += 1

        self._n_docs = len(self._documents)
        self._avg_doc_length = sum(self._doc_lengths) / self._n_docs if self._n_docs else 0

        # Document frequency
        self._df = {}
        for term, postings in self._inverted_index.items():
            self._df[term] = len(postings)

        logger.info(
            f"Search engine indexed {self._n_docs} mods, {len(self._inverted_index)} unique terms"
        )

    def _idf(self, term: str) -> float:
        """BM25 IDF component."""
        n = self._df.get(term, 0)
        if n == 0:
            return 0.0
        return math.log((self._n_docs - n + 0.5) / (n + 0.5) + 1.0)

    def _bm25_score(
        self, doc_id: int, query_tokens: List[str]
    ) -> Tuple[float, Dict[str, float], List[str]]:
        """
        Compute BM25 score for doc_id given query tokens.
        Returns (total_score, breakdown, matched_fields).
        """
        doc_tokens = self._documents[doc_id]["tokens"]
        doc_len = len(doc_tokens)
        doc_tf = defaultdict(int)
        for t in doc_tokens:
            doc_tf[t] += 1

        score = 0.0
        breakdown = {}
        matched = []

        for term in query_tokens:
            if term not in doc_tf:
                continue
            tf = doc_tf[term]
            idf = self._idf(term)
            # BM25 formula
            norm = (
                1 - self.b + self.b * (doc_len / self._avg_doc_length)
                if self._avg_doc_length
                else 1
            )
            term_score = idf * (tf * (self.k1 + 1)) / (tf + self.k1 * norm)
            score += term_score
            breakdown[term] = round(term_score, 4)
            matched.append(term)

        return score, breakdown, matched

    def search(
        self,
        query: str,
        limit: int = 25,
        game: Optional[str] = None,
        expand_query: bool = True,
        min_score: float = 0.01,
        include_breakdown: bool = False,
    ) -> List[SearchResult]:
        """
        Search mods with BM25 + authority boost.
        Returns sorted SearchResult list.
        """
        if not self._documents:
            return []

        q = query.strip()
        if not q:
            return []

        tokens = _tokenize(q)
        if expand_query:
            tokens = _expand_query(tokens)
        if not tokens:
            tokens = _tokenize(q)  # fallback to raw

        # Only score docs that have at least one query term
        candidates = set()
        for term in tokens:
            for doc_id, _ in self._inverted_index.get(term, []):
                candidates.add(doc_id)

        if not candidates:
            return []

        results = []
        for doc_id in candidates:
            bm25, breakdown, matched = self._bm25_score(doc_id, tokens)
            if bm25 < min_score:
                continue

            doc = self._documents[doc_id]
            clean_name = doc["clean_name"]

            # Authority boost: mods referenced by many others rank higher (like PageRank-lite)
            auth = self._authority.get(clean_name, 0)
            auth_boost = 1.0 + 0.15 * min(auth, 10)  # cap at ~2.5x

            # Name match boost: exact/prefix match in mod name is strongest signal
            name_lower = doc["mod_name"].lower()
            name_boost = 1.0
            if tokens:
                first_token = tokens[0]
                if name_lower.startswith(first_token) or first_token in name_lower:
                    name_boost = 1.5

            final_score = bm25 * auth_boost * name_boost

            # Snippet: first message or requirement that matches
            snippet = None
            info = doc.get("info")
            if info and matched:
                for msg in (info.messages or [])[:1]:
                    if any(m in msg.lower() for m in matched):
                        snippet = msg[:120] + ("..." if len(msg) > 120 else "")
                        break
                if not snippet and info.requirements:
                    snippet = f"Requires: {', '.join(info.requirements[:3])}"

            mod_info_dict = None
            if info:
                mod_info_dict = {
                    "requirements": info.requirements,
                    "incompatibilities": info.incompatibilities,
                    "load_after": info.load_after[:5] if info.load_after else [],
                    "tags": info.tags[:5] if info.tags else [],
                    "dirty_edits": info.dirty_edits,
                }

            score_breakdown = {"bm25": round(bm25, 4), "authority_boost": round(auth_boost, 2)}
            if include_breakdown and breakdown:
                score_breakdown["terms"] = breakdown

            # Get Nexus Mods ID and picture URL if available
            nexus_mod_id = None
            picture_url = None
            if info and hasattr(info, "nexus_mod_id") and info.nexus_mod_id:
                nexus_mod_id = info.nexus_mod_id
                picture_url = getattr(info, "picture_url", None)

            results.append(
                SearchResult(
                    mod_name=doc["mod_name"],
                    clean_name=clean_name,
                    score=round(final_score, 4),
                    score_breakdown=score_breakdown,
                    matched_fields=matched,
                    snippet=snippet,
                    mod_info=mod_info_dict,
                    nexus_mod_id=nexus_mod_id,
                    picture_url=picture_url,
                )
            )

        results.sort(key=lambda r: (-r.score, r.mod_name.lower()))
        return results[:limit]

    def search_for_ai(
        self,
        query: str,
        limit: int = 15,
        include_mod_info: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Search results formatted for AI assistant consumption.
        Returns list of dicts with mod_name, score, snippet, mod_info (requirements, etc.).
        """
        raw = self.search(query, limit=limit, include_breakdown=False)
        out = []
        for r in raw:
            entry = {
                "mod_name": r.mod_name,
                "score": r.score,
                "snippet": r.snippet,
                "nexus_mod_id": r.nexus_mod_id,
                "picture_url": r.picture_url,
            }
            if include_mod_info and r.mod_info:
                entry["mod_info"] = r.mod_info
            out.append(entry)
        return out


# -------------------------------------------------------------------
# Global engine instance (lazy-built from parser)
# -------------------------------------------------------------------
_engines: Dict[str, ModSearchEngine] = {}


def get_search_engine(parser) -> ModSearchEngine:
    """Get or create search engine for a parser. Cached per (game, version)."""
    key = f"{getattr(parser, 'game', 'skyrimse')}_{getattr(parser, 'version', 'latest')}"
    if key not in _engines:
        eng = ModSearchEngine()
        eng.index_parser(parser)
        _engines[key] = eng
    return _engines[key]
