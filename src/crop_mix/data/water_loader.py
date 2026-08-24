"""Water Requirement Data Loader for Egyptian Agricultural Crops.

Loads and queries measured and estimated crop water requirements from
'egypt_crop_water_requirements.xlsx'.
"""

import math
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd


# Standard alias map for unifying crop names across EcoCrop, Rotation Matrix, and Water Data
ALIAS_MAP: Dict[str, str] = {
    "Yellow Corn": "Maize",
    "White Corn": "Maize",
    "Sweet Corn": "Maize",
    "Corn": "Maize",
    "Soybean": "Soybeans",
    "Tomatoes": "Tomato",
    "Potatoes": "Potato",
    "Fully Mature (Dry) Onion": "Onion (dry)",
    "Black-Seed Onion": "Onion (dry)",
    "Green Onion (Single Harvest)": "Onion (dry)",
    "Onions": "Onion (dry)",
    "Onion": "Onion (dry)",
    "Egyptian Clover / Berseem": "Berseem clover",
    "Alfalfa": "Berseem clover",
    "Baladi Fava Bean (Complementary)": "Faba beans (proxy: Beans dry/Pulses)",
    "Baladi Fava Bean (Single-Cut)": "Faba beans (proxy: Beans dry/Pulses)",
    "Common Bean": "Greenbeans",
    "Beans": "Greenbeans",
    "Sugar Beet": "Sugarbeet",
    "Sugar beet": "Sugarbeet",
    "Sugarcane": "Sugarcane (12-month ratoon)",
    "Oilseed Sunflower": "Sunflower",
    "Eggplant / Aubergine": "Eggplant",
}


class EgyptWaterDataLoader:
    """Repository for querying crop water requirements in m^3/ha for Egyptian zones and seasons."""

    VALID_ZONES: List[str] = [
        "Delta",
        "Middle Egypt",
        "Upper Egypt",
        "Sinai / Reclaimed Lands",
    ]

    VALID_SEASONS: List[str] = [
        "Winter",
        "Summer",
        "Nili",
        "Perennial",
    ]

    def __init__(self, excel_path: Optional[Path] = None):
        if excel_path is None:
            excel_path = Path(__file__).resolve().parent / "egypt_crop_water_requirements.xlsx"
        
        self.excel_path = excel_path
        self._ready_lookup: pd.DataFrame = pd.DataFrame()
        self._et_range: pd.DataFrame = pd.DataFrame()
        self._load_data()

    def _load_data(self) -> None:
        """Parse Excel sheets into internal dataframes."""
        if not self.excel_path.exists():
            return

        try:
            # Load Ready_Lookup_Water_by_Crop
            df_ready = pd.read_excel(self.excel_path, sheet_name="Ready_Lookup_Water_by_Crop", header=3)
            df_ready = df_ready.dropna(subset=["Crop"]).copy()
            
            # Filter out header/footer commentary text rows
            filter_mask = ~df_ready["Crop"].astype(str).str.contains(
                "Known data gap|All Estimated|m3/feddan|NIWR =", na=False
            )
            df_ready = df_ready[filter_mask].copy()

            df_ready["Crop_Clean"] = df_ready["Crop"].astype(str).str.strip()
            df_ready["Season_Clean"] = df_ready["Season"].astype(str).str.strip()
            df_ready["Zone_Clean"] = df_ready["Zone"].astype(str).str.strip()
            
            # Normalize crop names
            df_ready["Crop_Norm"] = df_ready["Crop_Clean"].map(lambda x: ALIAS_MAP.get(x, x))
            self._ready_lookup = df_ready

            # Load Seasonal_ETcrop_Range
            df_et = pd.read_excel(self.excel_path, sheet_name="Seasonal_ETcrop_Range")
            df_et["Crop_Clean"] = df_et["Crop"].astype(str).str.strip()
            df_et["Crop_Norm"] = df_et["Crop_Clean"].map(lambda x: ALIAS_MAP.get(x, x))
            self._et_range = df_et

        except Exception as exc:
            print(f"Warning: Failed to load Egypt water requirement data: {exc}")

    def normalize_crop_name(self, crop_name: str) -> str:
        """Map crop name to standardized water database entry key."""
        clean = crop_name.strip()
        return ALIAS_MAP.get(clean, clean)

    def get_water_requirement(
        self,
        crop_name: str,
        zone: str = "Delta",
        season: str = "Winter",
        default_fallback: float = 4000.0,
    ) -> float:
        """Return water requirement in m^3/ha for a given crop, zone, and season.

        Units conversion:
        1 mm depth = 10 m^3/ha
        """
        norm_crop = self.normalize_crop_name(crop_name)
        clean_crop = crop_name.strip()
        clean_zone = zone.strip() if zone else "Delta"
        clean_season = season.strip() if season else "Winter"

        if not self._ready_lookup.empty:
            # 1. Exact match on normalized crop name, zone, and season
            mask = (
                (self._ready_lookup["Crop_Norm"].str.lower() == norm_crop.lower())
                & (self._ready_lookup["Zone_Clean"].str.lower().str.contains(clean_zone.lower()))
                & (self._ready_lookup["Season_Clean"].str.lower().str.contains(clean_season.lower()))
            )
            matches = self._ready_lookup[mask]
            if not matches.empty:
                val_mm = matches.iloc[0]["Estimated seasonal water requirement (mm)"]
                if pd.notna(val_mm) and val_mm > 0:
                    return float(val_mm) * 10.0

            # 2. Match on crop and zone (any season)
            mask_zone = (
                (self._ready_lookup["Crop_Norm"].str.lower() == norm_crop.lower())
                & (self._ready_lookup["Zone_Clean"].str.lower().str.contains(clean_zone.lower()))
            )
            matches_zone = self._ready_lookup[mask_zone]
            if not matches_zone.empty:
                val_mm = matches_zone.iloc[0]["Estimated seasonal water requirement (mm)"]
                if pd.notna(val_mm) and val_mm > 0:
                    return float(val_mm) * 10.0

            # 3. Match on crop (any zone/season) in Ready Lookup
            mask_crop = self._ready_lookup["Crop_Norm"].str.lower() == norm_crop.lower()
            matches_crop = self._ready_lookup[mask_crop]
            if not matches_crop.empty:
                val_mm = matches_crop.iloc[0]["Estimated seasonal water requirement (mm)"]
                if pd.notna(val_mm) and val_mm > 0:
                    return float(val_mm) * 10.0

        # 4. Fallback to Seasonal_ETcrop_Range sheet (FAO24 ET range midpoint)
        if not self._et_range.empty:
            mask_et = (self._et_range["Crop_Norm"].str.lower() == norm_crop.lower()) | (
                self._et_range["Crop_Clean"].str.lower().str.contains(norm_crop.lower(), regex=False)
            )
            matches_et = self._et_range[mask_et]
            if not matches_et.empty:
                min_mm = matches_et.iloc[0]["Seasonal ETcrop Min (mm)"]
                max_mm = matches_et.iloc[0]["Seasonal ETcrop Max (mm)"]
                if pd.notna(min_mm) and pd.notna(max_mm):
                    avg_mm = (float(min_mm) + float(max_mm)) / 2.0
                    return avg_mm * 10.0

        return default_fallback

    def get_all_crop_water_info(self, zone: str = "Delta", season: str = "Winter") -> Dict[str, float]:
        """Return water requirement dictionary for all known crops in specified zone and season."""
        known_crops = set()
        if not self._ready_lookup.empty:
            known_crops.update(self._ready_lookup["Crop_Clean"].unique())
        if not self._et_range.empty:
            known_crops.update(self._et_range["Crop_Clean"].unique())

        res = {}
        for c in known_crops:
            res[c] = self.get_water_requirement(c, zone=zone, season=season)
        return res
