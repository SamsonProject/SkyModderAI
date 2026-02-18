"""
Bethesda Research Database — Game-Specific Knowledge

Curated knowledge about Bethesda games, their engines, common issues,
modding patterns, and community best practices.

Sources:
- LOOT masterlist data
- Community wikis (UESP, Fallout Wiki)
- Nexus Mods documentation
- Reddit communities (r/skyrimmods, r/fo4mods)
- Bethesda modding Discord servers
"""

# =============================================================================
# Game Engine Knowledge
# =============================================================================

ENGINE_KNOWLEDGE = {
    "skyrimse": {
        "engine": "Creation Engine 1 (64-bit)",
        "engine_limit": 60,  # FPS cap without fixes
        "plugin_limit": 254,
        "light_plugin_limit": 4096,
        "save_game_size_limit_mb": 64,  # Soft limit before instability
        "memory_limits": {
            "default_ram_mb": 4096,  # Default allocation
            "max_ram_mb": 8192,  # With ENBoost/SKSE
            "vram_heavy_mods": ["ENB", "4K textures", "DynDOLOD"],
        },
        "common_issues": [
            {
                "name": "CTD on startup",
                "causes": ["Missing master", "Load order violation", "Script conflict"],
                "solutions": [
                    "Check for missing requirements",
                    "Run LOOT to sort load order",
                    "Disable mods one by one to isolate"
                ]
            },
            {
                "name": "Infinite loading screens",
                "causes": ["Script lag", "Missing assets", "Cell conflicts"],
                "solutions": [
                    "Increase papyrus tuning",
                    "Check for missing dependencies",
                    "Clean save with Fallrim Tools"
                ]
            },
            {
                "name": "Audio crackling",
                "causes": ["High FPS", "Audio overhaul conflicts"],
                "solutions": [
                    "Cap FPS to 60",
                    "Disable audio overhaul mods",
                    "Update audio drivers"
                ]
            },
            {
                "name": "Stuttering in cities",
                "causes": ["CPU bottleneck", "Too many NPCs", "High grass density"],
                "solutions": [
                    "Reduce NPC density",
                    "Lower grass density",
                    "Use performance city mods"
                ]
            }
        ],
        "essential_mods": [
            "SKSE64",
            "Address Library for SKSE Plugins",
            "Unofficial Skyrim Special Edition Patch",
            "SSE Display Tweaks",
            "Bug Fixes SSE",
            "Engine Fixes",
        ],
        "recommended_limits": {
            "max_mods_conservative": 150,
            "max_mods_moderate": 300,
            "max_mods_extreme": 500,
            "max_plugins": 254,
            "max_esl_mods": 4096,
        }
    },
    "skyrim": {
        "engine": "Creation Engine 1 (32-bit)",
        "engine_limit": 60,
        "plugin_limit": 254,
        "memory_limits": {
            "default_ram_mb": 2048,  # 32-bit limit
            "max_ram_mb": 4096,  # With ENBoost
        },
        "common_issues": [
            {"name": "CTD", "causes": ["Memory limit", "Missing master"]},
            {"name": "Save bloat", "causes": ["Script-heavy mods", "Long playthroughs"]}
        ],
        "essential_mods": [
            "SKSE",
            "SKSE Memory Patch",
            "Unofficial Skyrim Legendary Edition Patch",
            "ENBoost",
        ],
    },
    "skyrimvr": {
        "engine": "Creation Engine 1 (VR branch)",
        "engine_limit": None,  # No hard cap, target 90+ for VR
        "plugin_limit": 254,
        "common_issues": [
            {"name": "Motion sickness", "causes": ["Low FPS", "FOV issues"]},
            {"name": "Controller conflicts", "causes": ["Input mod conflicts"]}
        ],
        "essential_mods": [
            "Skyrim VR",
            "SKSE64 VR",
            "VRIK",
            "VR Address Library",
            "Unofficial Skyrim Special Edition Patch",
        ],
    },
    "fallout4": {
        "engine": "Creation Engine 1 (FO4 branch)",
        "engine_limit": 60,
        "plugin_limit": 254,
        "common_issues": [
            {"name": "Workshop script lag", "causes": ["Too many workshop objects"]},
            {"name": "Density flickering", "causes": ["LOD issues"]}
        ],
        "essential_mods": [
            "F4SE",
            "Address Library for F4SE",
            "Unofficial Fallout 4 Patch",
            "Fallout 4 Script Extender",
        ],
    },
    "fallout4vr": {
        "engine": "Creation Engine 1 (FO4 VR branch)",
        "engine_limit": None,
        "plugin_limit": 254,
        "essential_mods": [
            "Fallout 4 VR",
            "F4SE VR",
            "VRIK",
            "Unofficial Fallout 4 Patch",
        ],
    },
    "fallout3": {
        "engine": "Gamebryo (Fallout 3 branch)",
        "engine_limit": 60,
        "plugin_limit": 254,
        "common_issues": [
            {"name": "Games for Windows Live issues", "causes": ["GFWL conflicts"]},
            {"name": "Memory crashes", "causes": ["32-bit limit"]}
        ],
        "essential_mods": [
            "FOSE",
            "Fallout 3 Script Extender",
        ],
    },
    "falloutnv": {
        "engine": "Gamebryo (Fallout NV branch)",
        "engine_limit": 60,
        "plugin_limit": 254,
        "common_issues": [
            {"name": "Crash on New Vegas menu", "causes": ["4GB patch needed"]},
            {"name": "Hard crash in game", "causes": ["NVAC needed"]}
        ],
        "essential_mods": [
            "NVSE",
            "New Vegas 4GB Patch",
            "New Vegas AntiCrash (NVAC)",
            "Yukichigai Unofficial Patch (YUP)",
        ],
    },
    "oblivion": {
        "engine": "Gamebryo (Oblivion branch)",
        "engine_limit": 60,
        "plugin_limit": 254,
        "common_issues": [
            {"name": "Missing lips", "causes": ["Race mod conflicts"]},
            {"name": "Water flickering", "causes": ["Water mod conflicts"]}
        ],
        "essential_mods": [
            "OBSE",
            "Oblivion Script Extender",
            "Unofficial Oblivion Patch",
        ],
    },
    "starfield": {
        "engine": "Creation Engine 2",
        "engine_limit": None,
        "plugin_limit": 254,
        "common_issues": [
            {"name": "Stuttering", "causes": ["Shader compilation", "Asset streaming"]},
            {"name": "High CPU usage", "causes": ["Engine inefficiency"]}
        ],
        "essential_mods": [
            "SFSE",
            "Starfield Script Extender",
            "Starfield Community Patch",
        ],
    },
}

# =============================================================================
# Mod Compatibility Patterns
# =============================================================================

COMPATIBILITY_PATTERNS = {
    # Skyrim SE
    "skyrimse": {
        "always_incompatible": [
            ("SkyUI", "SkyUI SE"),  # Same mod, different versions
            ("Ordinator", "Vokriin"),  # Both overhaul perks
            ("Immersive Citizens", "Open Cities"),  # City conflicts
        ],
        "requires_patches": [
            ("Ordinator", "Alternate Start", "Ordinator - Alternate Start Patch"),
            ("Immersive Citizens", "Open Cities", "ICC - Open Cities Patch"),
            ("Requiem", "SkyUI", "Requiem - SkyUI Patch"),
        ],
        "load_order_rules": [
            ("Unofficial Patch", "Everything", "Always load first"),
            ("City mods", "NPC mods", "Cities before NPCs"),
            ("Weather mods", "Lighting mods", "Weather before lighting"),
        ],
    },
    # Fallout 4
    "fallout4": {
        "always_incompatible": [
            ("Sim Settlements", "Sim Settlements 2"),  # Major version conflict
        ],
        "requires_patches": [
            ("Armor Keywords", "Weapon Keywords", "AWKCR Patch"),
        ],
    },
}

# =============================================================================
# Performance Recommendations by Hardware Tier
# =============================================================================

HARDWARE_RECOMMENDATIONS = {
    "low_end": {
        "gpu_examples": ["GTX 1050", "GTX 1650", "RX 560"],
        "vram_range": "2-4GB",
        "recommendations": [
            "Use 1K-2K texture mods maximum",
            "Avoid ENB or use very lightweight presets",
            "Limit grass density",
            "Use performance-oriented LOD mods",
            "Avoid heavy weather mods",
            "Target mod count: 50-100",
        ],
    },
    "mid_range": {
        "gpu_examples": ["GTX 1060", "GTX 1660", "RX 5600", "RTX 3050"],
        "vram_range": "6-8GB",
        "recommendations": [
            "2K textures are safe",
            "Lightweight ENB or ReShade",
            "Moderate grass density",
            "DynDOLOD medium settings",
            "Target mod count: 100-250",
        ],
    },
    "high_end": {
        "gpu_examples": ["RTX 3060", "RTX 3070", "RX 6700", "RX 6800"],
        "vram_range": "10-12GB",
        "recommendations": [
            "2K-4K textures acceptable",
            "Medium ENB presets",
            "High grass density OK",
            "DynDOLOD high settings",
            "Target mod count: 250-400",
        ],
    },
    "enthusiast": {
        "gpu_examples": ["RTX 3080", "RTX 3090", "RTX 4070+", "RX 6900+", "RX 7900+"],
        "vram_range": "16-24GB",
        "recommendations": [
            "4K textures safe",
            "Heavy ENB acceptable",
            "Ultra grass density",
            "DynDOLOD ultra settings",
            "Target mod count: 400+",
        ],
    },
}

# =============================================================================
# Community Resources & Wikis
# =============================================================================

COMMUNITY_RESOURCES = {
    "skyrimse": {
        "wikis": [
            {"name": "UESP", "url": "https://en.uesp.net/wiki/Skyrim:Skyrim", "description": "Most reliable wiki"},
            {"name": "Skyrim Wiki", "url": "https://skyrim.fandom.com", "description": "Community wiki"},
        ],
        "communities": [
            {"name": "r/skyrimmods", "url": "https://reddit.com/r/skyrimmods", "members": "500k+"},
            {"name": "Nexus Forums", "url": "https://forums.nexusmods.com", "active": True},
        ],
        "guides": [
            {"name": "Modding Wiki", "url": "https://modding.wiki", "focus": "Technical guides"},
            {"name": "Step Project", "url": "https://stepmodifications.org", "focus": "Step-by-step guides"},
        ],
    },
    "fallout4": {
        "wikis": [
            {"name": "Fallout Wiki", "url": "https://fallout.fandom.com", "description": "Comprehensive wiki"},
        ],
        "communities": [
            {"name": "r/fo4mods", "url": "https://reddit.com/r/fo4mods", "members": "100k+"},
        ],
    },
}

# =============================================================================
# Common Mod Acronyms & Terms
# =============================================================================

MOD_ACRONYMS = {
    # Skyrim
    "USSEP": "Unofficial Skyrim Special Edition Patch",
    "USLEEP": "Unofficial Skyrim Legendary Edition Patch",
    "SKSE": "Skyrim Script Extender",
    "SKSE64": "SKSE for 64-bit Skyrim",
    "ENB": "ENBSeries (post-processing)",
    "SMIM": "Static Mesh Improvement Mod",
    "LOD": "Level of Detail",
    "DynDOLOD": "Dynamic Distant LOD",
    "CTD": "Crash to Desktop",
    "ILS": "Infinite Loading Screen",
    "NPC": "Non-Player Character",
    "ESM": "Elder Scrolls Master (master plugin)",
    "ESP": "Elder Scrolls Plugin",
    "ESL": "Elder Scrolls Light (light plugin)",
    # Fallout
    "F4SE": "Fallout 4 Script Extender",
    "FOSE": "Fallout 3 Script Extender",
    "NVSE": "New Vegas Script Extender",
    "YUP": "Yukichigai Unofficial Patch",
    "NVAC": "New Vegas AntiCrash",
    # General
    "LOOT": "Load Order Optimization Tool",
    "MO2": "Mod Organizer 2",
    "Vortex": "Nexus Mod Manager",
    "WABBAJACK": "Automated mod list installer",
}

# =============================================================================
# INI Tuning Recommendations
# =============================================================================

INI_RECOMMENDATIONS = {
    "skyrimse": {
        "performance": {
            "file": "SkyrimPrefs.ini",
            "settings": [
                {"section": "[Display]", "key": "iShadowMapResolution", "value": "1024", "note": "Lower for performance"},
                {"section": "[Grass]", "key": "iMaxGrassTypesPerTexure", "value": "3", "note": "Reduce for FPS"},
                {"section": "[Grass]", "key": "iMinGrassSize", "value": "120", "note": "Higher = less grass"},
            ]
        },
        "stability": {
            "file": "Skyrim.ini",
            "settings": [
                {"section": "[General]", "key": "fFlickeringLightDistance", "value": "4096.0000", "note": "Fix flickering"},
                {"section": "[SaveGame]", "key": "SCharIndex", "value": "0", "note": "Prevent save issues"},
            ]
        },
        "papyrus": {
            "file": "Skyrim.ini",
            "settings": [
                {"section": "[Papyrus]", "key": "fUpdateBudgetMS", "value": "1.2", "note": "Script performance"},
                {"section": "[Papyrus]", "key": "iMaxMemoryPageSize", "value": "8192", "note": "Memory limit"},
                {"section": "[Papyrus]", "key": "iMinMemoryPageSize", "value": "128", "note": "Memory minimum"},
            ]
        },
    },
}


def get_game_info(game_id: str) -> dict:
    """Get comprehensive game information."""
    return ENGINE_KNOWLEDGE.get(game_id, {})


def get_common_issues(game_id: str) -> list:
    """Get common issues for a game."""
    game_info = get_game_info(game_id)
    return game_info.get("common_issues", [])


def get_essential_mods(game_id: str) -> list:
    """Get essential/starter mods for a game."""
    game_info = get_game_info(game_id)
    return game_info.get("essential_mods", [])


def get_hardware_recommendations(vram_gb: float = None, gpu_name: str = None) -> dict:
    """Get hardware-based recommendations."""
    if vram_gb:
        if vram_gb <= 4:
            return HARDWARE_RECOMMENDATIONS["low_end"]
        elif vram_gb <= 8:
            return HARDWARE_RECOMMENDATIONS["mid_range"]
        elif vram_gb <= 12:
            return HARDWARE_RECOMMENDATIONS["high_end"]
        else:
            return HARDWARE_RECOMMENDATIONS["enthusiast"]
    
    if gpu_name:
        gpu_lower = gpu_name.lower()
        for tier, data in HARDWARE_RECOMMENDATIONS.items():
            for example in data["gpu_examples"]:
                if example.lower() in gpu_lower:
                    return data
    
    return HARDWARE_RECOMMENDATIONS["mid_range"]


def get_acronym_definition(acronym: str) -> str:
    """Get definition of modding acronym."""
    return MOD_ACRONYMS.get(acronym.upper(), "Unknown acronym")


def get_compatibility_info(game_id: str, mod_a: str, mod_b: str) -> dict:
    """Get compatibility information between two mods."""
    patterns = COMPATIBILITY_PATTERNS.get(game_id, {})
    
    # Check incompatibility
    for pair in patterns.get("always_incompatible", []):
        if (mod_a.lower() in pair[0].lower() and mod_b.lower() in pair[1].lower()) or \
           (mod_b.lower() in pair[0].lower() and mod_a.lower() in pair[1].lower()):
            return {"compatible": False, "reason": "Known incompatibility"}
    
    # Check patch requirements
    for req in patterns.get("requires_patches", []):
        if (mod_a.lower() in req[0].lower() and mod_b.lower() in req[1].lower()) or \
           (mod_b.lower() in req[0].lower() and mod_a.lower() in req[1].lower()):
            return {"compatible": True, "requires_patch": req[2]}
    
    return {"compatible": True, "reason": "No known conflicts"}


def get_ini_recommendations(game_id: str, category: str = "performance") -> list:
    """Get INI tuning recommendations."""
    game_inis = INI_RECOMMENDATIONS.get(game_id, {})
    return game_inis.get(category, [])


def get_community_resources(game_id: str) -> dict:
    """Get community resources for a game."""
    return COMMUNITY_RESOURCES.get(game_id, {})
