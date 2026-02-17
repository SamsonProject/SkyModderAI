"""
List Builder — Preference-based mod list generation.
Standard options for all users; Pro: AI-generated multiple setups.
"""

import logging
from typing import Any, Dict, List, Optional

from mod_recommendations import _CURATED_TOP_PICKS
from search_engine import get_search_engine

logger = logging.getLogger(__name__)

# Preference options schema — (key, label, choices)
LIST_PREFERENCE_OPTIONS = [
    ('environment', 'Environment', [
        ('dark_fantasy', 'Dark fantasy'),
        ('vanilla_plus', 'Vanilla+'),
        ('high_fantasy', 'High fantasy'),
        ('survival', 'Survival'),
        ('horror', 'Horror'),
        ('sci_fi', 'Sci-fi'),
        ('any', 'Any'),
    ]),
    ('hair', 'Hair / character', [
        ('ks_hairdos', 'KS Hairdos'),
        ('apachii', 'Apachii'),
        ('vanilla_only', 'Vanilla only'),
        ('hdt_smp', 'HDT-SMP'),
        ('any', 'Any'),
    ]),
    ('body', 'Body', [
        ('cbbe', 'CBBE'),
        ('unp', 'UNP'),
        ('vanilla', 'Vanilla'),
        ('any', 'Any'),
    ]),
    ('combat', 'Combat', [
        ('vanilla', 'Vanilla'),
        ('souls_like', 'Souls-like'),
        ('action', 'Action'),
        ('immersive', 'Immersive'),
        ('any', 'Any'),
    ]),
    ('graphics', 'Graphics', [
        ('performance', 'Performance'),
        ('balanced', 'Balanced'),
        ('ultra', 'Ultra'),
        ('enb', 'ENB-focused'),
        ('any', 'Any'),
    ]),
    ('content', 'Content', [
        ('quest_heavy', 'Quest-heavy'),
        ('new_lands', 'New lands'),
        ('vanilla_plus', 'Vanilla+'),
        ('minimal', 'Minimal'),
        ('any', 'Any'),
    ]),
    ('stability', 'Stability', [
        ('max', 'Maximum stability'),
        ('balanced', 'Balanced'),
        ('experimental', 'Experimental OK'),
    ]),
]

# Game-specific preference keys (UI relevance by game)
_GAME_PREFERENCE_KEYS: Dict[str, List[str]] = {
    'skyrimse': ['environment', 'hair', 'body', 'combat', 'graphics', 'content', 'stability'],
    'skyrim': ['environment', 'hair', 'body', 'combat', 'graphics', 'content', 'stability'],
    'skyrimvr': ['environment', 'hair', 'body', 'combat', 'graphics', 'content', 'stability'],
    'oblivion': ['environment', 'combat', 'graphics', 'content', 'stability'],
    'fallout3': ['environment', 'combat', 'graphics', 'content', 'stability'],
    'falloutnv': ['environment', 'combat', 'graphics', 'content', 'stability'],
    'fallout4': ['environment', 'combat', 'graphics', 'content', 'stability'],
    'starfield': ['environment', 'combat', 'graphics', 'content', 'stability'],
}

# Per-game choice relevance overrides (keeps UI from showing nonsense values)
_GAME_PREFERENCE_CHOICE_ALLOWLIST: Dict[str, Dict[str, List[str]]] = {
    'fallout3': {
        'environment': ['sci_fi', 'survival', 'horror', 'any'],
        'content': ['quest_heavy', 'vanilla_plus', 'minimal', 'any'],
    },
    'falloutnv': {
        'environment': ['sci_fi', 'survival', 'horror', 'any'],
        'content': ['quest_heavy', 'vanilla_plus', 'minimal', 'any'],
    },
    'fallout4': {
        'environment': ['sci_fi', 'survival', 'horror', 'any'],
        'content': ['quest_heavy', 'vanilla_plus', 'minimal', 'any'],
    },
    'starfield': {
        'environment': ['sci_fi', 'any'],
        'content': ['quest_heavy', 'vanilla_plus', 'minimal', 'any'],
    },
    'oblivion': {
        'environment': ['dark_fantasy', 'vanilla_plus', 'high_fantasy', 'horror', 'any'],
        'content': ['quest_heavy', 'new_lands', 'vanilla_plus', 'minimal', 'any'],
    },
}

# Essential/base search terms by game (avoid cross-game leakage in generated lists)
_GAME_BASE_TERMS: Dict[str, List[str]] = {
    'skyrimse': ['unofficial patch', 'skyui', 'engine fixes', 'skse', 'address library'],
    'skyrim': ['unofficial patch', 'skyui', 'skse'],
    'skyrimvr': ['unofficial patch', 'vrik', 'skse vr'],
    'oblivion': ['unofficial oblivion patch', 'obse', 'oblivion stutter remover'],
    'fallout3': ['unofficial fallout 3 patch', 'fo3 edit', 'archiveinvalidated'],
    'falloutnv': ['yup', 'nvse', 'new vegas tick fix', '4gb patch'],
    'fallout4': ['unofficial fallout 4 patch', 'f4se', 'buffout', 'x-cell'],
    'starfield': ['starfield community patch', 'sfse', 'achievement enabler'],
}

# Search terms per preference value (game_id -> pref_key -> pref_value -> [terms])
_PREFERENCE_SEARCH_TERMS: Dict[str, Dict[str, Dict[str, List[str]]]] = {
    'skyrimse': {
        'environment': {
            'dark_fantasy': ['dark fantasy', 'gothic', 'gloomy', 'obsidian weathers', 'rustic'],
            'vanilla_plus': ['vanilla', 'vanilla plus', 'cutting room floor', 'ussep'],
            'high_fantasy': ['fantasy', 'magical', 'cathedral weathers'],
            'survival': ['survival', 'frostfall', 'campfire', 'ineed'],
            'horror': ['horror', 'dark', 'scary'],
            'sci_fi': [],
            'any': [],
        },
        'hair': {
            'ks_hairdos': ['ks hairdos', 'ks hair'],
            'apachii': ['apachii', 'apachii hair'],
            'vanilla_only': [],
            'hdt_smp': ['hdt', 'smp', 'physics'],
            'any': [],
        },
        'body': {
            'cbbe': ['cbbe', 'caliente'],
            'unp': ['unp', 'unpb'],
            'vanilla': [],
            'any': [],
        },
        'combat': {
            'vanilla': [],
            'souls_like': ['souls', 'combat', 'elden', 'dark souls'],
            'action': ['combat', 'attack', 'animation'],
            'immersive': ['immersive', 'combat', 'ai overhaul'],
            'any': [],
        },
        'graphics': {
            'performance': ['performance', 'fps', 'optimized', 'lightweight'],
            'balanced': ['smim', 'noble', 'skyland'],
            'ultra': ['4k', '8k', 'parallax', 'high res'],
            'enb': ['enb', 'preset', 'lighting'],
            'any': [],
        },
        'content': {
            'quest_heavy': ['quest', 'legacy of the dragonborn', 'lotd', 'beyond skyrim'],
            'new_lands': ['beyond skyrim', 'bruma', 'falskaar', 'wyrmstooth'],
            'vanilla_plus': ['vanilla', 'cutting room', 'crf'],
            'minimal': ['vanilla', 'patch'],
            'any': [],
        },
        'stability': {
            'max': ['engine fixes', 'bug fix', 'stability', 'crash fix'],
            'balanced': [],
            'experimental': [],
        },
    },
    'fallout4': {
        'environment': {
            'sci_fi': ['fallout', 'post apocalyptic'],
            'survival': ['survival mode', 'horizon', 'needs', 'hardcore'],
            'horror': ['dark', 'horror', 'ghoul', 'atmosphere'],
            'any': [],
        },
        'combat': {
            'vanilla': [],
            'souls_like': ['combat overhaul', 'difficulty', 'stamina'],
            'action': ['gunplay', 'combat', 'animations'],
            'immersive': ['immersive gameplay', 'realism', 'damage'],
            'any': [],
        },
        'graphics': {
            'performance': ['performance', 'optimized'],
            'balanced': ['texture', 'lighting'],
            'ultra': ['4k', 'high res'],
            'enb': ['enb', 'reshade', 'lighting'],
            'any': [],
        },
        'content': {
            'quest_heavy': ['quest', 'story', 'sim settlements'],
            'vanilla_plus': ['vanilla plus', 'quality of life', 'lore friendly'],
            'minimal': ['bugfix', 'lightweight', 'stability'],
            'any': [],
        },
        'stability': {
            'max': ['buffout', 'x-cell', 'engine fixes', 'crash'],
            'balanced': [],
            'experimental': [],
        },
    },
    'falloutnv': {
        'environment': {
            'sci_fi': ['new vegas', 'mojave', 'post apocalyptic'],
            'survival': ['hardcore mode', 'survival', 'needs'],
            'horror': ['dark', 'horror', 'night'],
            'any': [],
        },
        'combat': {
            'vanilla': [],
            'souls_like': ['combat overhaul', 'difficulty'],
            'action': ['gunplay', 'animations', 'combat'],
            'immersive': ['jsawyer', 'realistic', 'immersive'],
            'any': [],
        },
        'graphics': {
            'performance': ['performance', 'optimized', 'lightweight'],
            'balanced': ['nmc', 'texture', 'lighting'],
            'ultra': ['4k', 'high res', 'texture overhaul'],
            'enb': ['enb', 'reshade'],
            'any': [],
        },
        'content': {
            'quest_heavy': ['quest', 'new world', 'story'],
            'vanilla_plus': ['vanilla plus', 'quality of life'],
            'minimal': ['bugfix', 'lightweight'],
            'any': [],
        },
        'stability': {
            'max': ['nvac', '4gb patch', 'heap', 'stability'],
            'balanced': [],
            'experimental': [],
        },
    },
    'fallout3': {
        'environment': {
            'sci_fi': ['fallout 3', 'capital wasteland', 'post apocalyptic'],
            'survival': ['survival', 'hardcore', 'needs'],
            'horror': ['dark', 'horror', 'atmosphere'],
            'any': [],
        },
        'combat': {
            'vanilla': [],
            'souls_like': ['combat overhaul', 'difficulty'],
            'action': ['combat', 'gunplay'],
            'immersive': ['realism', 'immersive'],
            'any': [],
        },
        'graphics': {
            'performance': ['performance', 'optimized'],
            'balanced': ['texture', 'lighting'],
            'ultra': ['4k', 'high res'],
            'enb': ['enb', 'reshade'],
            'any': [],
        },
        'content': {
            'quest_heavy': ['quest', 'story', 'dlc'],
            'vanilla_plus': ['vanilla plus', 'quality of life'],
            'minimal': ['bugfix', 'lightweight'],
            'any': [],
        },
        'stability': {
            'max': ['stability', 'crash fix', '4gb patch'],
            'balanced': [],
            'experimental': [],
        },
    },
    'starfield': {
        'environment': {
            'sci_fi': ['starfield', 'space'],
            'any': [],
        },
        'combat': {
            'vanilla': [],
            'souls_like': ['hardcore', 'difficulty', 'combat'],
            'action': ['combat', 'gunplay', 'ship combat'],
            'immersive': ['immersive', 'realism', 'survival'],
            'any': [],
        },
        'graphics': {
            'performance': ['performance', 'optimized', 'dlss'],
            'balanced': ['texture', 'lighting'],
            'ultra': ['4k', '8k', 'high res'],
            'enb': ['reshade', 'lighting preset'],
            'any': [],
        },
        'content': {
            'quest_heavy': ['quest', 'mission', 'faction'],
            'vanilla_plus': ['vanilla plus', 'quality of life'],
            'minimal': ['bugfix', 'lightweight'],
            'any': [],
        },
        'stability': {
            'max': ['sfse', 'engine fix', 'stability'],
            'balanced': [],
            'experimental': [],
        },
    },
    'oblivion': {
        'environment': {
            'dark_fantasy': ['dark fantasy', 'oblivion atmosphere', 'darker nights'],
            'vanilla_plus': ['vanilla plus', 'quality of life', 'oblivion bugfix'],
            'high_fantasy': ['fantasy', 'magic overhaul', 'vibrant world'],
            'horror': ['horror', 'dark', 'creepy'],
            'any': [],
        },
        'combat': {
            'vanilla': [],
            'souls_like': ['combat overhaul', 'difficulty'],
            'action': ['combat', 'animations'],
            'immersive': ['immersive', 'realism', 'ai'],
            'any': [],
        },
        'graphics': {
            'performance': ['performance', 'optimized', 'lightweight'],
            'balanced': ['texture', 'lighting'],
            'ultra': ['4k', 'high res', 'texture overhaul'],
            'enb': ['enb', 'reshade'],
            'any': [],
        },
        'content': {
            'quest_heavy': ['quest', 'guild', 'story'],
            'new_lands': ['new lands', 'worldspace'],
            'vanilla_plus': ['vanilla plus', 'quality of life'],
            'minimal': ['bugfix', 'lightweight'],
            'any': [],
        },
        'stability': {
            'max': ['stability', 'crash fix', 'performance'],
            'balanced': [],
            'experimental': [],
        },
    },
}


def _get_terms_for_pref(game: str, pref_key: str, pref_value: str) -> List[str]:
    """Get search terms for a preference value."""
    game_prefs = _PREFERENCE_SEARCH_TERMS.get(game, {})
    key_prefs = game_prefs.get(pref_key, {})
    terms = key_prefs.get(pref_value, key_prefs.get('any', []))
    return terms if terms else []


def build_list_from_preferences(
    parser,
    game: str,
    nexus_slug: str,
    preferences: Dict[str, str],
    limit: int = 60,
    specs: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Build a mod list from user preferences.
    Uses LOOT search + preference-specific terms.
    Specs (cpu, gpu, vram_gb, etc.) influence performance vs ultra bias.
    Returns list of {name, reason, nexus_url, image_url}.
    """
    from mod_recommendations import MOD_PLACEHOLDER, _is_plugin, _norm, _url_enc

    specs = specs or {}
    vram = specs.get('vram_gb') or specs.get('vram')
    try:
        vram_num = int(vram) if vram else None
    except (ValueError, TypeError):
        vram_num = None
    favor_performance = vram_num is not None and vram_num < 8
    if favor_performance and preferences.get('graphics') == 'any':
        preferences = dict(preferences)
        preferences['graphics'] = 'performance'

    engine = get_search_engine(parser)
    nexus_base = f'https://www.nexusmods.com/games/{nexus_slug}/mods?keyword='
    seen = set()
    out: List[Dict[str, Any]] = []

    # 1) Always include game-specific base essentials
    base_terms = _GAME_BASE_TERMS.get(game, _GAME_BASE_TERMS.get('skyrimse', []))
    for term in base_terms:
        for r in engine.search(term, limit=2):
            name = r.mod_name
            if not _is_plugin(name):
                continue
            key = _norm(name)
            if key in seen:
                continue
            seen.add(key)
            out.append({
                'name': name,
                'reason': 'Essential',
                'nexus_url': nexus_base + _url_enc(name),
                'image_url': MOD_PLACEHOLDER,
            })
            if len(out) >= limit:
                return out[:limit]

    # 2) Preference-specific terms
    for pref_key, pref_value in (preferences or {}).items():
        if not pref_value or pref_value == 'any':
            continue
        terms = _get_terms_for_pref(game, pref_key, pref_value)
        for term in terms[:3]:  # Limit terms per pref
            for r in engine.search(term, limit=3):
                name = r.mod_name
                if not _is_plugin(name):
                    continue
                key = _norm(name)
                if key in seen:
                    continue
                seen.add(key)
                reason = pref_key.replace('_', ' ').title()
                out.append({
                    'name': name,
                    'reason': reason,
                    'nexus_url': nexus_base + _url_enc(name),
                    'image_url': MOD_PLACEHOLDER,
                })
                if len(out) >= limit:
                    return out[:limit]

    # 3) Fallback: curated top picks (category -> list of search terms)
    curated = _CURATED_TOP_PICKS.get(game, {})
    for category, terms in list(curated.items())[:4]:
        for term in (terms or [])[:2]:
            for r in engine.search(term, limit=2):
                name = r.mod_name
                if not _is_plugin(name):
                    continue
                key = _norm(name)
                if key in seen:
                    continue
                seen.add(key)
                out.append({
                    'name': name,
                    'reason': f'Top {category}',
                    'nexus_url': nexus_base + _url_enc(name),
                    'image_url': MOD_PLACEHOLDER,
                })
                if len(out) >= limit:
                    return out[:limit]

    return out[:limit]


def get_preference_options(game: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return preference options for UI, filtered for game relevance."""
    game_id = (game or '').lower()
    allowed_keys = _GAME_PREFERENCE_KEYS.get(game_id) or _GAME_PREFERENCE_KEYS.get('skyrimse', [])
    choice_overrides = _GAME_PREFERENCE_CHOICE_ALLOWLIST.get(game_id, {})

    out: List[Dict[str, Any]] = []
    for key, label, choices in LIST_PREFERENCE_OPTIONS:
        if key not in allowed_keys:
            continue
        allowed_values = set(choice_overrides.get(key, [v for v, _ in choices]))
        filtered_choices = [{'value': v, 'label': label_text} for v, label_text in choices if v in allowed_values]
        # Always keep "any" option as safe fallback.
        if not any(c['value'] == 'any' for c in filtered_choices):
            filtered_choices.append({'value': 'any', 'label': 'Any'})
        out.append({
            'key': key,
            'label': label,
            'choices': filtered_choices,
        })
    return out
