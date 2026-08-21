"""FAO EcoCrop Database module for Crop Mix Business Planner.

Provides agronomic species data, climate parameters, and soil suitability rules
derived from the FAO EcoCrop database to automate crop parameter generation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from crop_mix.data.example_data import CropSoilRequirement, CropParameters


@dataclass
class EcoCropEntry:
    """Ecological and soil requirements for a plant species from FAO EcoCrop."""

    name: str
    scientific_name: str
    category: List[str]  # e.g., 'Cereal', 'Vegetable', 'Fiber', 'Oilseed', 'Legume', 'Fruit', 'Forage'
    min_ph: float
    opt_min_ph: float
    opt_max_ph: float
    max_ph: float
    max_ec: float  # Maximum tolerable electrical conductivity (dS/m)
    suitable_textures: List[str]  # e.g. ['Loam', 'Clay', 'Silt', 'Sandy', 'Sandy Loam']
    water_requirement: Optional[float] = None  # Seasonal water requirement (m^3/ha)
    min_temp: Optional[float] = None  # Absolute minimum temperature (°C)
    opt_min_temp: Optional[float] = None  # Optimal minimum temperature (°C)
    opt_max_temp: Optional[float] = None  # Optimal maximum temperature (°C)
    max_temp: Optional[float] = None  # Absolute maximum temperature (°C)
    crop_cycle_min_days: Optional[int] = None  # Typical crop cycle duration in days
    crop_cycle_max_days: Optional[int] = None  # Typical crop cycle duration in days

    
    # I commented these as they are not ECOCrop data related
    
    # default_expected_yield: float  # Benchmark yield (metric tons/ha)
    # default_price: float  # Benchmark selling price ($/ton)
    # default_production_cost: float  # Benchmark base production cost ($/ha)
    
    
    
    def to_soil_requirement(self) -> Optional[CropSoilRequirement]:
        """Convert EcoCrop entry to CropSoilRequirement, or None if pH data is missing.

        Returning None (rather than fabricating a range) lets SoilSuitabilityEngine's
        existing behavior apply: a crop with no soil_requirement is treated as suitable
        everywhere — accurate for a species EcoCrop never studied, instead of quietly
        guessing at a pH tolerance.
        """
        if self.min_ph is None or self.max_ph is None:
            return None

        return CropSoilRequirement(
            min_ph=self.min_ph,
            max_ph=self.max_ph,
            max_ec=self.max_ec if self.max_ec is not None else float("inf"),
            suitable_textures=list(self.suitable_textures) if self.suitable_textures else [],
        )


    def to_crop_parameters(
        self,
        expected_yield: float,
        price: float,
        production_cost: float,
        water_requirement: Optional[float] = None,
        labor_req: float = 20.0,
        labor_rate: float = 20.0,
        fert_req: float = 100.0,
        fert_rate: float = 1.5,
    ) -> CropParameters:
        """Convert EcoCrop entry into CropParameters.

        yield/price/production_cost are now REQUIRED — EcoCrop has no economic data,
        so these must come from the yield-estimation API (or the user) rather than
        a hardcoded default.
        """
        water = water_requirement if water_requirement is not None else self.water_requirement
        if water is None:
            raise ValueError(
                f"No water requirement available for '{self.name}' from EcoCrop; "
                f"pass water_requirement explicitly."
            )

        return CropParameters(
            name=self.name,
            expected_yield=expected_yield,
            price=price,
            production_cost=production_cost,
            water_requirement=water,
            labor_requirement=labor_req,
            labor_cost_per_hour=labor_rate,
            fertilizer_requirement=fert_req,
            fertilizer_cost_per_kg=fert_rate,
            soil_requirement=self.to_soil_requirement(),
        )


class EcoCropDatabase:
    """FAO EcoCrop database repository with search & lookup capabilities."""

    def __init__(self, db_connection=None):
        self._crops: Dict[str, EcoCropEntry] = {}
        if db_connection:
            self._load_from_database(db_connection)  ## when we connect to the database
        else:
            self._load_default_database()  # fallback for local dev/testing
            
            
            
    def _load_from_database(self, conn):
        """Populate self._crops once from the DB, at startup."""
        rows = conn.execute("SELECT * FROM ecocrop_species").fetchall()
        for row in rows:
            entry = EcoCropEntry(**row_to_entry_fields(row))
            self._crops[entry.name.lower()] = entry

    def _load_default_database(self):
        """Populate database with curated FAO EcoCrop species entries."""
        entries = [
                EcoCropEntry(
                    name="Wheat",
                    scientific_name="Triticum aestivum",
                    category=["Cereal"],
                    min_ph=5.5,
                    opt_min_ph=6.0,
                    opt_max_ph=7.5,
                    max_ph=8.5,
                    max_ec=2.5,
                    suitable_textures=["Loam", "Clay", "Silt", "Sandy Loam"],
                    water_requirement=3500.0,
                    min_temp=5.0,
                    opt_min_temp=15.0,
                    opt_max_temp=25.0,
                    max_temp=35.0,
                    crop_cycle_min_days=120,
                    crop_cycle_max_days=120,
                ),
                EcoCropEntry(
                    name="Corn",
                    scientific_name="Zea mays",
                    category=["Cereal"],
                    min_ph=5.5,
                    opt_min_ph=5.8,
                    opt_max_ph=7.2,
                    max_ph=8.0,
                    max_ec=2.0,
                    suitable_textures=["Loam", "Sandy Loam", "Clay", "Silt"],
                    water_requirement=5500.0,
                    min_temp=10.0,
                    opt_min_temp=18.0,
                    opt_max_temp=30.0,
                    max_temp=38.0,
                    crop_cycle_min_days=130,
                    crop_cycle_max_days=130,
                ),
                EcoCropEntry(
                    name="Soybeans",
                    scientific_name="Glycine max",
                    category=["Legume"],
                    min_ph=5.8,
                    opt_min_ph=6.0,
                    opt_max_ph=7.5,
                    max_ph=8.0,
                    max_ec=2.5,
                    suitable_textures=["Loam", "Silt", "Sandy Loam", "Clay"],
                    water_requirement=4000.0,
                    min_temp=10.0,
                    opt_min_temp=20.0,
                    opt_max_temp=30.0,
                    max_temp=40.0,
                    crop_cycle_min_days=110,
                    crop_cycle_max_days=110,
                ),
                EcoCropEntry(
                    name="Tomatoes",
                    scientific_name="Solanum lycopersicum",
                    category=["Vegetable"],
                    min_ph=5.5,
                    opt_min_ph=6.0,
                    opt_max_ph=7.0,
                    max_ph=7.5,
                    max_ec=1.5,
                    suitable_textures=["Loam", "Sandy Loam", "Sandy"],
                    water_requirement=6500.0,
                    min_temp=12.0,
                    opt_min_temp=20.0,
                    opt_max_temp=27.0,
                    max_temp=35.0,
                    crop_cycle_min_days=100,
                    crop_cycle_max_days=100,
                ),
                EcoCropEntry(
                    name="Cotton",
                    scientific_name="Gossypium hirsutum",
                    category=["Fiber"],
                    min_ph=5.2,
                    opt_min_ph=5.8,
                    opt_max_ph=8.0,
                    max_ph=8.7,
                    max_ec=4.0,
                    suitable_textures=["Loam", "Clay", "Sandy Loam", "Sandy"],
                    water_requirement=5000.0,
                    min_temp=15.0,
                    opt_min_temp=22.0,
                    opt_max_temp=32.0,
                    max_temp=42.0,
                    crop_cycle_min_days=160,
                    crop_cycle_max_days=160,
                ),
                EcoCropEntry(
                    name="Rice",
                    scientific_name="Oryza sativa",
                    category=["Cereal"],
                    min_ph=4.5,
                    opt_min_ph=5.5,
                    opt_max_ph=7.0,
                    max_ph=8.0,
                    max_ec=3.0,
                    suitable_textures=["Clay", "Loam", "Silt"],
                    water_requirement=12000.0,
                    min_temp=12.0,
                    opt_min_temp=22.0,
                    opt_max_temp=32.0,
                    max_temp=40.0,
                    crop_cycle_min_days=120,
                    crop_cycle_max_days=120,
                ),
                EcoCropEntry(
                    name="Barley",
                    scientific_name="Hordeum vulgare",
                    category=["Cereal"],
                    min_ph=6.0,
                    opt_min_ph=6.5,
                    opt_max_ph=8.2,
                    max_ph=8.5,
                    max_ec=4.5,
                    suitable_textures=["Loam", "Sandy Loam", "Clay"],
                    water_requirement=3000.0,
                    min_temp=3.0,
                    opt_min_temp=12.0,
                    opt_max_temp=22.0,
                    max_temp=32.0,
                    crop_cycle_min_days=90,
                    crop_cycle_max_days=90,
                ),
                EcoCropEntry(
                    name="Potato",
                    scientific_name="Solanum tuberosum",
                    category=["Vegetable"],
                    min_ph=4.8,
                    opt_min_ph=5.5,
                    opt_max_ph=6.5,
                    max_ph=7.5,
                    max_ec=1.7,
                    suitable_textures=["Loam", "Sandy Loam", "Sandy"],
                    water_requirement=4500.0,
                    min_temp=7.0,
                    opt_min_temp=15.0,
                    opt_max_temp=20.0,
                    max_temp=30.0,
                    crop_cycle_min_days=110,
                    crop_cycle_max_days=110,
                ),
                EcoCropEntry(
                    name="Sugarcane",
                    scientific_name="Saccharum officinarum",
                    category=["Sugar"],
                    min_ph=5.0,
                    opt_min_ph=6.0,
                    opt_max_ph=7.5,
                    max_ph=8.5,
                    max_ec=2.0,
                    suitable_textures=["Loam", "Clay", "Sandy Loam"],
                    water_requirement=15000.0,
                    min_temp=15.0,
                    opt_min_temp=24.0,
                    opt_max_temp=34.0,
                    max_temp=45.0,
                    crop_cycle_min_days=360,
                    crop_cycle_max_days=360,
                ),
                EcoCropEntry(
                    name="Sunflower",
                    scientific_name="Helianthus annuus",
                    category=["Oilseed"],
                    min_ph=5.6,
                    opt_min_ph=6.0,
                    opt_max_ph=7.5,
                    max_ph=8.0,
                    max_ec=3.0,
                    suitable_textures=["Loam", "Sandy Loam", "Clay"],
                    water_requirement=4200.0,
                    min_temp=8.0,
                    opt_min_temp=18.0,
                    opt_max_temp=28.0,
                    max_temp=38.0,
                    crop_cycle_min_days=105,
                    crop_cycle_max_days=105,
                ),
                EcoCropEntry(
                    name="Alfalfa",
                    scientific_name="Medicago sativa",
                    category=["Forage"],
                    min_ph=6.2,
                    opt_min_ph=6.5,
                    opt_max_ph=7.8,
                    max_ph=8.5,
                    max_ec=2.0,
                    suitable_textures=["Loam", "Silt", "Sandy Loam"],
                    water_requirement=7000.0,
                    min_temp=5.0,
                    opt_min_temp=15.0,
                    opt_max_temp=25.0,
                    max_temp=35.0,
                    crop_cycle_min_days=90,
                    crop_cycle_max_days=90,
                ),
                EcoCropEntry(
                    name="Onion",
                    scientific_name="Allium cepa",
                    category=["Vegetable"],
                    min_ph=5.8,
                    opt_min_ph=6.0,
                    opt_max_ph=7.0,
                    max_ph=7.8,
                    max_ec=1.2,
                    suitable_textures=["Loam", "Sandy Loam"],
                    water_requirement=4000.0,
                    min_temp=7.0,
                    opt_min_temp=13.0,
                    opt_max_temp=24.0,
                    max_temp=32.0,
                    crop_cycle_min_days=130,
                    crop_cycle_max_days=130,
                ),
                EcoCropEntry(
                    name="Pepper",
                    scientific_name="Capsicum annuum",
                    category=["Vegetable"],
                    min_ph=5.5,
                    opt_min_ph=6.0,
                    opt_max_ph=7.0,
                    max_ph=7.5,
                    max_ec=1.5,
                    suitable_textures=["Loam", "Sandy Loam"],
                    water_requirement=5500.0,
                    min_temp=12.0,
                    opt_min_temp=20.0,
                    opt_max_temp=28.0,
                    max_temp=35.0,
                    crop_cycle_min_days=110,
                    crop_cycle_max_days=110,
                ),
            ]
        
        for entry in entries:
            self._crops[entry.name.lower()] = entry

    def get_crop(self, name: str) -> Optional[EcoCropEntry]:
        """Look up an EcoCrop entry by crop name (case-insensitive)."""
        return self._crops.get(name.lower().strip())

    def search_crops(self, query: str = "", category: Optional[str] = None) -> List[EcoCropEntry]:
        """Search crops by query string matching name/scientific_name or category."""
        results = []
        q = query.lower().strip()
        cat = category.lower().strip() if category else None

        for entry in self._crops.values():
            matches_query = (
                not q
                or q in entry.name.lower()
                or q in entry.scientific_name.lower()
                or any(q in c.lower() for c in entry.category)
            )
            matches_cat = not cat or cat in [c.lower() for c in entry.category]
            if matches_query and matches_cat:
                results.append(entry)

        return results

    def list_all(self) -> List[Dict[str, Any]]:
        """Return summary list of all available EcoCrop entries."""
        return [
            {
                "name": entry.name,
                "scientific_name": entry.scientific_name,
                "category": entry.category,
                "min_ph": entry.min_ph,
                "max_ph": entry.max_ph,
                "max_ec": entry.max_ec,
                "suitable_textures": entry.suitable_textures,
                "water_requirement": entry.water_requirement,
                "min_temp": entry.min_temp,
                "max_temp": entry.max_temp,
                "crop_cycle_days": entry.crop_cycle_days
            }
            for entry in self._crops.values()
        ]
