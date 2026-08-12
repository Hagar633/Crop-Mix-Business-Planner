"""Data structures and example dataset for Crop Mix Optimization (V1 and V2)."""

from dataclasses import dataclass, field
from typing import Dict
import pandas as pd


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
    """Overall farm inputs and resource budgets."""

    field_area: float  # Total available land area (hectares)
    water_budget: float  # Total available water budget (m^3)
    labor_budget: float = float("inf")  # Total available labor budget (hours)
    fertilizer_budget: float = float("inf")  # Total available fertilizer budget (kg)
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


def get_example_farm_data() -> FarmInputs:
    """Return an example dataset with synthetic TEST/DEMO values for V1 & V2 optimization testing.

    NOTE: All labor and fertilizer parameters below are synthetic TEST/DEMO values, not real agricultural data.
    """
    crops = {
        "Wheat": CropParameters(
            name="Wheat",
            expected_yield=4.5,
            price=220.0,
            production_cost=600.0,
            water_requirement=3500.0,
            # Synthetic TEST/DEMO values for labor and fertilizer:
            labor_requirement=15.0,  # hrs/ha
            labor_cost_per_hour=20.0,  # $/hr -> labor cost = $300/ha
            fertilizer_requirement=150.0,  # kg/ha
            fertilizer_cost_per_kg=1.50,  # $/kg -> fertilizer cost = $225/ha
        ),
        "Corn": CropParameters(
            name="Corn",
            expected_yield=9.0,
            price=190.0,
            production_cost=900.0,
            water_requirement=5500.0,
            # Synthetic TEST/DEMO values:
            labor_requirement=25.0,  # hrs/ha -> labor cost = $500/ha
            labor_cost_per_hour=20.0,
            fertilizer_requirement=200.0,  # kg/ha -> fertilizer cost = $300/ha
            fertilizer_cost_per_kg=1.50,
        ),
        "Soybeans": CropParameters(
            name="Soybeans",
            expected_yield=3.0,
            price=450.0,
            production_cost=650.0,
            water_requirement=4000.0,
            # Synthetic TEST/DEMO values:
            labor_requirement=18.0,  # hrs/ha -> labor cost = $360/ha
            labor_cost_per_hour=20.0,
            fertilizer_requirement=50.0,  # kg/ha -> fertilizer cost = $75/ha
            fertilizer_cost_per_kg=1.50,
        ),
        "Tomatoes": CropParameters(
            name="Tomatoes",
            expected_yield=35.0,
            price=120.0,
            production_cost=2500.0,
            water_requirement=6500.0,
            # Synthetic TEST/DEMO values:
            labor_requirement=120.0,  # hrs/ha -> labor cost = $2400/ha
            labor_cost_per_hour=20.0,
            fertilizer_requirement=250.0,  # kg/ha -> fertilizer cost = $375/ha
            fertilizer_cost_per_kg=1.50,
        ),
        "Cotton": CropParameters(
            name="Cotton",
            expected_yield=2.5,
            price=1100.0,
            production_cost=1200.0,
            water_requirement=5000.0,
            # Synthetic TEST/DEMO values:
            labor_requirement=30.0,  # hrs/ha -> labor cost = $600/ha
            labor_cost_per_hour=20.0,
            fertilizer_requirement=180.0,  # kg/ha -> fertilizer cost = $270/ha
            fertilizer_cost_per_kg=1.50,
        ),
    }

    return FarmInputs(
        field_area=100.0,  # hectares
        water_budget=400000.0,  # m^3
        labor_budget=2500.0,  # Synthetic TEST/DEMO hours budget
        fertilizer_budget=15000.0,  # Synthetic TEST/DEMO kg budget
        crops=crops,
    )
