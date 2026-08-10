"""Data structures and hardcoded example dataset for Version 1 optimizer."""

from dataclasses import dataclass, field
from typing import Dict
import pandas as pd


@dataclass
class CropParameters:
    """Parameters for a single crop."""

    name: str
    expected_yield: float  # Metric tons per hectare
    price: float  # Price per metric ton ($/ton)
    production_cost: float  # Production cost per hectare ($/ha)
    water_requirement: float  # Water requirement per hectare (m^3/ha)

    @property
    def profit_per_hectare(self) -> float:
        """Calculate net profit per hectare ($/ha)."""
        return (self.expected_yield * self.price) - self.production_cost


@dataclass
class FarmInputs:
    """Overall farm inputs and resource budgets."""

    field_area: float  # Total available land area (hectares)
    water_budget: float  # Total available water budget (m^3)
    crops: Dict[str, CropParameters] = field(default_factory=dict)

    def to_dataframe(self) -> pd.DataFrame:
        """Convert crops data to a Pandas DataFrame."""
        records = []
        for name, crop in self.crops.items():
            records.append(
                {
                    "crop": name,
                    "expected_yield": crop.expected_yield,
                    "price": crop.price,
                    "production_cost": crop.production_cost,
                    "water_requirement": crop.water_requirement,
                    "profit_per_hectare": crop.profit_per_hectare,
                }
            )
        return pd.DataFrame(records).set_index("crop")


def get_example_farm_data() -> FarmInputs:
    """Return a hardcoded example dataset for testing and demonstration.

    Example setup:
    - 100 hectares of land available.
    - 400,000 m^3 of water budget available.
    - Crops: Wheat, Corn, Soybeans, Tomatoes, Cotton.
    """
    crops = {
        "Wheat": CropParameters(
            name="Wheat",
            expected_yield=4.5,
            price=220.0,
            production_cost=600.0,
            water_requirement=3500.0,
        ),
        "Corn": CropParameters(
            name="Corn",
            expected_yield=9.0,
            price=190.0,
            production_cost=900.0,
            water_requirement=5500.0,
        ),
        "Soybeans": CropParameters(
            name="Soybeans",
            expected_yield=3.0,
            price=450.0,
            production_cost=650.0,
            water_requirement=4000.0,
        ),
        "Tomatoes": CropParameters(
            name="Tomatoes",
            expected_yield=35.0,
            price=120.0,
            production_cost=2500.0,
            water_requirement=6500.0,
        ),
        "Cotton": CropParameters(
            name="Cotton",
            expected_yield=2.5,
            price=1100.0,
            production_cost=1200.0,
            water_requirement=5000.0,
        ),
    }

    return FarmInputs(
        field_area=100.0,
        water_budget=400000.0,
        crops=crops,
    )
