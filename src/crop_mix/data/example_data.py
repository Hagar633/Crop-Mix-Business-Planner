"""Data structures and example dataset for Crop Mix Optimization (V1, V2, V3, and V4)."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import pandas as pd


@dataclass
class CropSoilRequirement:
    """Soil suitability requirements for a crop (V3/V4)."""

    min_ph: float  # Minimum acceptable soil pH
    max_ph: float  # Maximum acceptable soil pH
    max_ec: float  # Maximum tolerable electrical conductivity (dS/m)
    suitable_textures: List[str]  # List of acceptable soil texture classes


@dataclass
class FieldParameters:
    """Parameters and soil measurements for an individual farm field (V3/V4)."""

    name: str
    area: float  # Field area in Feddans
    ph: float  # Soil pH measurement
    ec: float  # Electrical conductivity (dS/m)
    texture: str  # Soil texture class (e.g. 'Loam', 'Clay', 'Sandy')
    organic_matter: float  # Soil organic matter percentage (%) - stored metadata
    previous_crop: Optional[str] = None  # Historical crop planted in prior season (V4)
    name_ar: Optional[str] = None  # Arabic display name for field


@dataclass
class CropParameters:
    """Parameters for a single crop."""

    name: str
    expected_yield: float  # Metric tons per feddan/ha
    price: float  # Price per metric ton ($/ton)
    production_cost: float  # Base production cost per feddan/ha
    water_requirement: float  # Water requirement per feddan/ha
    name_ar: Optional[str] = None  # Arabic display name for crop


    # V2 Extensions: Labor and Fertilizer
    labor_requirement: float = 0.0  # Labor required per hectare (hours/ha)
    labor_cost_per_hour: float = 0.0  # Cost per labor hour ($/hour)
    fertilizer_requirement: float = 0.0  # Fertilizer required per hectare (kg/ha)
    fertilizer_cost_per_kg: float = 0.0  # Cost per kg of fertilizer ($/kg)

    # V3 Extension: Soil suitability requirements
    soil_requirement: Optional[CropSoilRequirement] = None

    @property
    def revenue_per_hectare(self) -> float:
        """Calculate gross revenue per hectare ($/ha)."""
        return self.expected_yield * self.price

    @property
    def labor_cost_per_hectare(self) -> float:
        """Calculate labor cost per hectare ($/ha)."""
        return self.labor_requirement * self.labor_cost_per_hour

    @property
    def fertilizer_cost_per_hectare(self) -> float:
        """Calculate fertilizer cost per hectare ($/ha)."""
        return self.fertilizer_requirement * self.fertilizer_cost_per_kg

    @property
    def profit_per_hectare(self) -> float:
        """Calculate net profit per hectare ($/ha) after production, labor, and fertilizer costs."""
        return (
            self.revenue_per_hectare
            - self.production_cost
            - self.labor_cost_per_hectare
            - self.fertilizer_cost_per_hectare
        )


@dataclass
class FarmInputs:
    """Overall farm inputs, field definitions, and resource budgets."""

    field_area: float  # Total available land area (hectares)
    water_budget: float  # Total available water budget (m^3)
    labor_budget: float = float("inf")  # Total available labor budget (hours)
    fertilizer_budget: float = float("inf")  # Total available fertilizer budget (kg)
    crops: Dict[str, CropParameters] = field(default_factory=dict)
    fields: Dict[str, FieldParameters] = field(default_factory=dict)  # V3/V4 fields

    def to_dataframe(self) -> pd.DataFrame:
        """Convert crops data to a Pandas DataFrame."""
        records = []
        for name, crop in self.crops.items():
            records.append(
                {
                    "crop": name,
                    "expected_yield": crop.expected_yield,
                    "price": crop.price,
                    "revenue_per_ha": crop.revenue_per_hectare,
                    "production_cost_per_ha": crop.production_cost,
                    "water_req_m3_ha": crop.water_requirement,
                    "labor_req_hrs_ha": crop.labor_requirement,
                    "labor_cost_per_ha": crop.labor_cost_per_hectare,
                    "fertilizer_req_kg_ha": crop.fertilizer_requirement,
                    "fertilizer_cost_per_ha": crop.fertilizer_cost_per_hectare,
                    "net_profit_per_ha": crop.profit_per_hectare,
                }
            )
        return pd.DataFrame(records).set_index("crop")

    def fields_to_dataframe(self) -> pd.DataFrame:
        """Convert field data to a Pandas DataFrame (V3/V4)."""
        records = []
        for name, field_obj in self.fields.items():
            records.append(
                {
                    "field": name,
                    "area_ha": field_obj.area,
                    "ph": field_obj.ph,
                    "ec_ds_m": field_obj.ec,
                    "texture": field_obj.texture,
                    "organic_matter_pct": field_obj.organic_matter,
                    "previous_crop": field_obj.previous_crop,
                }
            )
        return pd.DataFrame(records).set_index("field")


def get_example_farm_data() -> FarmInputs:
    """Return an example preset dataset featuring popular Egyptian crops from our real datasets.

    All land areas are expressed in Egyptian Feddans (فدان) and crop rates are per Feddan.
    Water requirements use real measured data from 'egypt_crop_water_requirements.xlsx' (Delta region).
    """
    from crop_mix.data.water_loader import EgyptWaterDataLoader
    from crop_mix.data.ecocrop_db import EcoCropDatabase

    water_loader = EgyptWaterDataLoader()
    ecocrop_db = EcoCropDatabase()

    def get_soil_req(crop_name: str) -> Optional[CropSoilRequirement]:
        entry = ecocrop_db.get_crop(crop_name)
        return entry.to_soil_requirement() if entry else None

    crops = {


        "Wheat": CropParameters(
            name="Wheat",
            name_ar="قمح",
            expected_yield=2.5,
            price=12500.0,
            production_cost=8500.0,
            water_requirement=water_loader.get_water_requirement("Wheat", zone="Delta", season="Winter", unit="feddan"),
            labor_requirement=6.0,
            labor_cost_per_hour=20.0,
            fertilizer_requirement=65.0,
            fertilizer_cost_per_kg=1.50,
            soil_requirement=get_soil_req("Wheat"),
        ),
        "Yellow Corn": CropParameters(
            name="Yellow Corn",
            name_ar="الذرة الصفراء",
            expected_yield=4.0,
            price=13000.0,
            production_cost=9500.0,
            water_requirement=water_loader.get_water_requirement("Yellow Corn", zone="Delta", season="Summer", unit="feddan"),
            labor_requirement=10.0,
            labor_cost_per_hour=20.0,
            fertilizer_requirement=85.0,
            fertilizer_cost_per_kg=1.50,
            soil_requirement=get_soil_req("Corn"),
        ),
        "Soybean": CropParameters(
            name="Soybean",
            name_ar="فول صويا",
            expected_yield=1.3,
            price=25000.0,
            production_cost=7500.0,
            water_requirement=water_loader.get_water_requirement("Soybean", zone="Delta", season="Summer", unit="feddan"),
            labor_requirement=7.0,
            labor_cost_per_hour=20.0,
            fertilizer_requirement=25.0,
            fertilizer_cost_per_kg=1.50,
            soil_requirement=get_soil_req("Soybeans"),
        ),
        "Tomato": CropParameters(
            name="Tomato",
            name_ar="الطماطم",
            expected_yield=15.0,
            price=8000.0,
            production_cost=19000.0,
            water_requirement=water_loader.get_water_requirement("Tomato", zone="Delta", season="Winter", unit="feddan"),
            labor_requirement=50.0,
            labor_cost_per_hour=20.0,
            fertilizer_requirement=100.0,
            fertilizer_cost_per_kg=1.50,
            soil_requirement=get_soil_req("Tomatoes"),
        ),
        "Cotton": CropParameters(
            name="Cotton",
            name_ar="القطن",
            expected_yield=1.1,
            price=35000.0,
            production_cost=13000.0,
            water_requirement=water_loader.get_water_requirement("Cotton", zone="Delta", season="Summer", unit="feddan"),
            labor_requirement=12.0,
            labor_cost_per_hour=20.0,
            fertilizer_requirement=75.0,
            fertilizer_cost_per_kg=1.50,
            soil_requirement=get_soil_req("Cotton"),
        ),
    }

    fields = {

        "حوض الشمالي": FieldParameters(
            name="حوض الشمالي",
            area=100.0,
            ph=6.8,
            ec=1.2,
            texture="Loam",
            organic_matter=2.5,
            previous_crop="Wheat",
        ),
        "حوض القبلي": FieldParameters(
            name="حوض القبلي",
            area=80.0,
            ph=7.8,
            ec=3.5,
            texture="Clay",
            organic_matter=1.8,
            previous_crop="Soybean",
        ),
        "حوض الشرقية": FieldParameters(
            name="حوض الشرقية",
            area=60.0,
            ph=5.5,
            ec=0.8,
            texture="Sandy",
            organic_matter=1.2,
            previous_crop=None,
        ),
    }

    return FarmInputs(
        field_area=240.0,
        water_budget=500000.0,
        labor_budget=3000.0,
        fertilizer_budget=20000.0,
        crops=crops,
        fields=fields,
    )
