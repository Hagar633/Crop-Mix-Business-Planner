"""Crop Season and Arabic Metadata Mapping for Multi-Season Planning.

Synchronized with Centralized Master Crop Registry (crop_registry.py).
Provides Arabic display names, allowed season calendars, and canonical name resolution
for all 53 agricultural crops.
"""

from typing import Dict, List, Optional
from crop_mix.data.crop_registry import (
    CROP_REGISTRY,
    get_canonical_crop_name as _registry_canonical_name,
    get_arabic_crop_name as _registry_arabic_name,
    get_allowed_seasons as _registry_allowed_seasons,
    is_crop_allowed_in_season as _registry_is_allowed,
)

# Mapping canonical English crop names to allowed agricultural seasons (all 53 crops)
CROP_SEASON_MAPPING: Dict[str, List[str]] = {
    c.canonical_name_en: list(c.allowed_seasons)
    for c in CROP_REGISTRY.values()
}

# Arabic name translation dictionary for UI display (all 53 crops)
CROP_ARABIC_NAMES: Dict[str, str] = {
    c.canonical_name_en: c.canonical_name_ar
    for c in CROP_REGISTRY.values()
}

# Add historical aliases to dictionaries for backwards compatibility
_LEGACY_ALIASES: Dict[str, str] = {
    "Onion": "بصل",
    "Alfalfa": "برسيم حجازي",
}
for k, v in _LEGACY_ALIASES.items():
    if k not in CROP_ARABIC_NAMES:
        CROP_ARABIC_NAMES[k] = v
    if k not in CROP_SEASON_MAPPING:
        CROP_SEASON_MAPPING[k] = ["Winter", "Summer", "Nili", "Perennial"]

# Reverse lookup mapping from Arabic / lower English name to canonical English crop name
CROP_ENGLISH_LOOKUP: Dict[str, str] = {v.strip().lower(): k for k, v in CROP_ARABIC_NAMES.items()}
for k in CROP_SEASON_MAPPING.keys():
    CROP_ENGLISH_LOOKUP[k.strip().lower()] = k


def get_allowed_seasons(crop_name: str) -> List[str]:
    """Retrieve list of allowed agricultural seasons for a crop."""
    return _registry_allowed_seasons(crop_name)


def get_arabic_crop_name(crop_name: str) -> str:
    """Retrieve Arabic display name for a canonical English crop name."""
    return _registry_arabic_name(crop_name)


def get_canonical_crop_name(crop_name: str) -> str:
    """Resolve an English or Arabic crop name string to its canonical English crop name."""
    return _registry_canonical_name(crop_name)


def is_crop_allowed_in_season(crop_name: str, season_name: str) -> bool:
    """Check whether a crop is agronomically allowed in the specified season."""
    return _registry_is_allowed(crop_name, season_name)
