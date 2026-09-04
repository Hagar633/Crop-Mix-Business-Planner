"""Crop Season and Arabic Metadata Mapping for Multi-Season Planning."""

from typing import Dict, List, Optional

# Mapping canonical English crop names to allowed agricultural seasons
# Allowed values in season lists: "Winter", "Summer", "Nili", "Perennial"
CROP_SEASON_MAPPING: Dict[str, List[str]] = {
    "Wheat": ["Winter"],
    "Yellow Corn": ["Summer"],
    "Soybean": ["Summer"],
    "Tomato": ["Winter", "Summer", "Nili"],
    "Cotton": ["Summer"],
    "Potato": ["Winter", "Summer", "Nili"],
    "Onion": ["Winter", "Summer"],
    "Fully Mature (Dry) Onion": ["Winter", "Summer"],
    "Black-Seed Onion": ["Winter"],
    "Green Onion (Single Harvest)": ["Winter", "Summer"],
    "Barley": ["Winter"],
    "Orange": ["Winter", "Summer", "Nili", "Perennial"],
    "Rice": ["Summer"],
    "Sugar Beet": ["Winter"],
    "Sugarcane": ["Summer", "Perennial"],
    "Alfalfa": ["Winter", "Summer", "Nili", "Perennial"],
}

# Arabic name translation dictionary for UI display
CROP_ARABIC_NAMES: Dict[str, str] = {
    "Wheat": "قمح",
    "Yellow Corn": "ذرة صفراء",
    "Soybean": "فول صويا",
    "Tomato": "طماطم",
    "Cotton": "قطن",
    "Potato": "بطاطس",
    "Onion": "بصل",
    "Fully Mature (Dry) Onion": "بصل جاف",
    "Black-Seed Onion": "بصل حبة البركة",
    "Green Onion (Single Harvest)": "بصل أخضر",
    "Barley": "شعير",
    "Orange": "برتقال",
    "Rice": "أرز",
    "Sugar Beet": "بنجر السكر",
    "Sugarcane": "قصب السكر",
    "Alfalfa": "برسيم حجازي",
}

# Reverse lookup mapping from Arabic name to canonical English crop name
CROP_ENGLISH_LOOKUP: Dict[str, str] = {v.strip().lower(): k for k, v in CROP_ARABIC_NAMES.items()}
for k in CROP_SEASON_MAPPING.keys():
    CROP_ENGLISH_LOOKUP[k.strip().lower()] = k


def get_allowed_seasons(crop_name: str) -> List[str]:
    """Retrieve list of allowed agricultural seasons for a crop."""
    canonical = get_canonical_crop_name(crop_name)
    return CROP_SEASON_MAPPING.get(canonical, ["Winter", "Summer", "Nili"])


def get_arabic_crop_name(crop_name: str) -> str:
    """Retrieve Arabic display name for a canonical English crop name."""
    canonical = get_canonical_crop_name(crop_name)
    return CROP_ARABIC_NAMES.get(canonical, crop_name)


def get_canonical_crop_name(crop_name: str) -> str:
    """Resolve an English or Arabic crop name string to its canonical English crop name."""
    if not crop_name:
        return ""
    clean = str(crop_name).strip().lower()
    return CROP_ENGLISH_LOOKUP.get(clean, crop_name.strip())


def is_crop_allowed_in_season(crop_name: str, season_name: str) -> bool:
    """Check whether a crop is agronomically allowed in the specified season."""
    seasons = get_allowed_seasons(crop_name)
    season_clean = season_name.strip().capitalize()
    return (
        season_clean in seasons
        or "Perennial" in seasons
        or "All" in seasons
    )
