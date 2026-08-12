"""Data structures and example dataset for Crop Mix Optimization (V1, V2, and V3)."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import pandas as pd


@dataclass
class CropSoilRequirement:
    """Soil suitability requirements for a crop (V3)."""

    min_ph: float  # Minimum acceptable soil pH
    max_ph: float  # Maximum acceptable soil pH
    max_ec: float  # Maximum tolerable electrical conductivity (dS/m)
    suitable_textures: List[str]  # List of acceptable soil texture classes


@dataclass
class FieldParameters:
    """Parameters and soil measurements for an individual farm field (V3)."""

    name: str
    area: float  # Field area in hectares
    ph: float  # Soil pH measurement
    ec: float  # Electrical conductivity (dS/m)
    texture: str  # Soil texture class (e.g. 'Loam', 'Clay', 'Sandy')
    organic_matter: float  # Soil organic matter percentage (%) - stored metadata


@dataclass
class CropParameters:
    """Parameters for a single crop."""

    name: str
    expected_yield: float  # Metric tons per hectare
    price: float  # Price per metric ton ($/ton)
    production_cost: float  # Base production cost per hectare ($/ha)
    water_requirement: float  # Water requirement per hectare (m^3/ha)

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
    fields: Dict[str, FieldParameters] = field(default_factory=dict)  # V3 fields

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
        """Convert field data to a Pandas DataFrame (V3)."""
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
                }
            )
        return pd.DataFrame(records).set_index("field")


def get_example_farm_data() -> FarmInputs:
    """Return an example dataset with synthetic TEST/DEMO values for V1, V2 & V3 optimization testing.

    NOTE: All labor, fertilizer, field soil measurements, and crop soil requirements below are synthetic
    TEST/DEMO values, not real agricultural recommendations.
    """
    crops = {
        "Wheat": CropParameters(
            name="Wheat",
            expected_yield=4.5,
            price=220.0,
            production_cost=600.0,
            water_requirement=3500.0,
            labor_requirement=15.0,
            labor_cost_per_hour=20.0,
            fertilizer_requirement=150.0,
            fertilizer_cost_per_kg=1.50,
            soil_requirement=CropSoilRequirement(
                min_ph=6.0,
                max_ph=8.0,
                max_ec=2.5,
                suitable_textures=["Loam", "Clay", "Silt"],
            ),
        ),
        "Corn": CropParameters(
            name="Corn",
            expected_yield=9.0,
            price=190.0,
            production_cost=900.0,
            water_requirement=5500.0,
            labor_requirement=25.0,
            labor_cost_per_hour=20.0,
            fertilizer_requirement=200.0,
            fertilizer_cost_per_kg=1.50,
            soil_requirement=CropSoilRequirement(
                min_ph=5.8,
                max_ph=7.2,
                max_ec=2.0,
                suitable_textures=["Loam", "Sandy Loam", "Clay"],
            ),
        ),
        "Soybeans": CropParameters(
            name="Soybeans",
            expected_yield=3.0,
            price=450.0,
            production_cost=650.0,
            water_requirement=4000.0,
            labor_requirement=18.0,
            labor_cost_per_hour=20.0,
            fertilizer_requirement=50.0,
            fertilizer_cost_per_kg=1.50,
            soil_requirement=CropSoilRequirement(
                min_ph=6.0,
                max_ph=7.5,
                max_ec=2.5,
                suitable_textures=["Loam", "Silt", "Sandy"],
            ),
        ),
        "Tomatoes": CropParameters(
            name="Tomatoes",
            expected_yield=35.0,
            price=120.0,
            production_cost=2500.0,
            water_requirement=6500.0,
            labor_requirement=120.0,
            labor_cost_per_hour=20.0,
            fertilizer_requirement=250.0,
            fertilizer_cost_per_kg=1.50,
            soil_requirement=CropSoilRequirement(
                min_ph=6.0,
                max_ph=7.0,
                max_ec=1.5,
                suitable_textures=["Loam", "Sandy"],
            ),
        ),
        "Cotton": CropParameters(
            name="Cotton",
            expected_yield=2.5,
            price=1100.0,
            production_cost=1200.0,
            water_requirement=5000.0,
            labor_requirement=30.0,
            labor_cost_per_hour=20.0,
            fertilizer_requirement=180.0,
            fertilizer_cost_per_kg=1.50,
            soil_requirement=CropSoilRequirement(
                min_ph=5.5,
                max_ph=8.5,
                max_ec=4.0,
                suitable_textures=["Loam", "Clay", "Sandy"],
            ),
        ),
    }

    # Synthetic TEST/DEMO fields with varied soil characteristics
    fields = {
        "Field_North": FieldParameters(
            name="Field_North",
            area=40.0,
            ph=6.8,  # Ideal pH for most crops
            ec=1.2,  # Low salinity
            texture="Loam",  # Suitable for all crops
            organic_matter=2.5,
        ),
        "Field_South": FieldParameters(
            name="Field_South",
            area=35.0,
            ph=7.8,  # Slightly alkaline
            ec=3.5,  # Higher salinity (restricts sensitive crops like Tomatoes & Corn)
            texture="Clay",  # Restricts Tomatoes and Soybeans
            organic_matter=1.8,
        ),
        "Field_East": FieldParameters(
            name="Field_East",
            area=25.0,
            ph=5.5,  # Acidic (restricts Wheat, Corn, Soybeans, Tomatoes; suitable for Cotton)
            ec=0.8,  # Low salinity
            texture="Sandy",  # Restricts Wheat
            organic_matter=1.2,
        ),
    }

    return FarmInputs(
        field_area=100.0,  # Total sum of field areas (40 + 35 + 25 = 100)
        water_budget=400000.0,
        labor_budget=2500.0,
        fertilizer_budget=15000.0,
        crops=crops,
        fields=fields,
    )
