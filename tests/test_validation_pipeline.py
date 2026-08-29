"""Comprehensive Validation Test Suite for Crop Mix Business Planner.

Tests:
1. Impact of Region/Location (Zone) and Season on water requirements, allocations, and profit.
2. Single-crop vs. Multi-crop per field allocation behavior under LP constraints.
3. Data quality checks for rotation matrix, EcoCrop DB, and soil suitability.
4. Constraint binding and resource bottleneck behavior.
"""

import pytest
from crop_mix.data.example_data import FarmInputs, CropParameters, FieldParameters, CropSoilRequirement, get_example_farm_data
from crop_mix.data.water_loader import EgyptWaterDataLoader
from crop_mix.data.rotation_loader import RotationMatrixLoader
from crop_mix.data.ecocrop_db import EcoCropDatabase
from crop_mix.models.optimizer_v4 import CropMixOptimizerV4
from crop_mix.models.soil_suitability import SoilSuitabilityEngine


@pytest.fixture
def water_loader():
    return EgyptWaterDataLoader()


@pytest.fixture
def rotation_loader():
    return RotationMatrixLoader()


@pytest.fixture
def ecocrop_db():
    return EcoCropDatabase()


@pytest.fixture
def optimizer_v4(rotation_loader):
    return CropMixOptimizerV4(rotation_loader=rotation_loader)


# --- 1. Location (Zone) & Season Impact Tests ---

def test_location_and_season_impact_on_water_requirements(water_loader):
    """Verify that location (Zone) and Season alter crop water requirements."""
    crop = "Wheat"
    
    # Delta (Winter) vs Upper Egypt (Winter)
    water_delta = water_loader.get_water_requirement(crop, zone="Delta", season="Winter")
    water_upper = water_loader.get_water_requirement(crop, zone="Upper Egypt", season="Winter")
    
    # Upper Egypt is hotter / drier so ET and seasonal water requirements should be higher or different
    assert water_delta > 0
    assert water_upper > 0
    assert water_delta != water_upper, f"Expected water req to differ between Delta ({water_delta}) and Upper Egypt ({water_upper})"


def test_location_and_season_impact_on_optimization_results(optimizer_v4, water_loader):
    """Verify that changing Zone & Season changes the optimization output (profit, water used, allocation)."""
    farm_base = get_example_farm_data()
    # Tight water budget to amplify differences
    farm_base.water_budget = 350000.0

    # Case A: Delta - Winter
    crops_delta = {}
    for name, crop in farm_base.crops.items():
        w_req = water_loader.get_water_requirement(name, zone="Delta", season="Winter")
        crops_delta[name] = CropParameters(
            name=crop.name,
            expected_yield=crop.expected_yield,
            price=crop.price,
            production_cost=crop.production_cost,
            water_requirement=w_req,
            labor_requirement=crop.labor_requirement,
            labor_cost_per_hour=crop.labor_cost_per_hour,
            fertilizer_requirement=crop.fertilizer_requirement,
            fertilizer_cost_per_kg=crop.fertilizer_cost_per_kg,
            soil_requirement=crop.soil_requirement,
        )
    farm_delta = FarmInputs(
        field_area=farm_base.field_area,
        water_budget=350000.0,
        labor_budget=farm_base.labor_budget,
        fertilizer_budget=farm_base.fertilizer_budget,
        crops=crops_delta,
        fields=farm_base.fields,
    )
    res_delta = optimizer_v4.solve(farm_delta)

    # Case B: Upper Egypt - Winter
    crops_upper = {}
    for name, crop in farm_base.crops.items():
        w_req = water_loader.get_water_requirement(name, zone="Upper Egypt", season="Winter")
        crops_upper[name] = CropParameters(
            name=crop.name,
            expected_yield=crop.expected_yield,
            price=crop.price,
            production_cost=crop.production_cost,
            water_requirement=w_req,
            labor_requirement=crop.labor_requirement,
            labor_cost_per_hour=crop.labor_cost_per_hour,
            fertilizer_requirement=crop.fertilizer_requirement,
            fertilizer_cost_per_kg=crop.fertilizer_cost_per_kg,
            soil_requirement=crop.soil_requirement,
        )
    farm_upper = FarmInputs(
        field_area=farm_base.field_area,
        water_budget=350000.0,
        labor_budget=farm_base.labor_budget,
        fertilizer_budget=farm_base.fertilizer_budget,
        crops=crops_upper,
        fields=farm_base.fields,
    )
    res_upper = optimizer_v4.solve(farm_upper)

    assert res_delta.is_feasible
    assert res_upper.is_feasible
    # Water requirement difference in Upper Egypt changes the objective or total water consumption
    assert res_delta.total_water_used != res_upper.total_water_used or res_delta.expected_profit != res_upper.expected_profit


# --- 2. Multi-Crop Allocation vs. Single-Crop Allocation per Field ---

def test_single_crop_allocation_when_unconstrained(optimizer_v4):
    """When a single crop is far more profitable and resources are abundant, 100% of field goes to that 1 crop."""
    crops = {
        "Wheat": CropParameters(
            name="Wheat", expected_yield=4.5, price=12500, production_cost=20000,
            water_requirement=3500, labor_requirement=15, labor_cost_per_hour=20,
            fertilizer_requirement=150, fertilizer_cost_per_kg=1.5
        ),
        "Soybean": CropParameters(
            name="Soybean", expected_yield=3.0, price=25000, production_cost=18000,
            water_requirement=4000, labor_requirement=18, labor_cost_per_hour=20,
            fertilizer_requirement=50, fertilizer_cost_per_kg=1.5
        )
    }
    fields = {
        "Field_1": FieldParameters(name="Field_1", area=100.0, ph=6.8, ec=1.0, texture="Loam", organic_matter=2.0, previous_crop=None)
    }
    # Infinite/Huge budgets
    farm = FarmInputs(field_area=100.0, water_budget=1e6, labor_budget=1e6, fertilizer_budget=1e6, crops=crops, fields=fields)
    res = optimizer_v4.solve(farm)

    alloc = res.crop_allocation["Field_1"]
    # Soybean profit per ha = 3*25000 - 18000 - 18*20 - 50*1.5 = 56,565 EGP/ha vs Wheat = 35,725 EGP/ha
    # Unconstrained LP should allocate ALL 100 ha to Soybean (single crop allocation)
    assert alloc["Soybean"] == pytest.approx(100.0, abs=1e-2)
    assert alloc["Wheat"] == pytest.approx(0.0, abs=1e-2)


def test_multi_crop_allocation_when_resource_constrained(optimizer_v4):
    """When resource budgets (e.g. water/fertilizer) are binding, a single field can be SPLIT between multiple crops."""
    # Crop A: High profit (50,000 EGP/ha), but high water (10,000 m3/ha)
    # Crop B: Lower profit (30,000 EGP/ha), but low water (2,000 m3/ha)
    crops = {
        "Tomato": CropParameters(
            name="Tomato", expected_yield=30.0, price=5000, production_cost=40000,
            water_requirement=10000.0, labor_requirement=50, labor_cost_per_hour=20,
            fertilizer_requirement=100, fertilizer_cost_per_kg=1.5
        ),
        "Wheat": CropParameters(
            name="Wheat", expected_yield=4.0, price=15000, production_cost=15000,
            water_requirement=2000.0, labor_requirement=15, labor_cost_per_hour=20,
            fertilizer_requirement=100, fertilizer_cost_per_kg=1.5
        )
    }
    # Field area = 10 ha
    fields = {
        "Field_1": FieldParameters(name="Field_1", area=10.0, ph=6.8, ec=1.0, texture="Loam", organic_matter=2.0, previous_crop=None)
    }
    # Water budget = 50,000 m3 (Not enough for 10 ha of Tomato which needs 100,000 m3, but more than enough for Wheat)
    # Optimal split: x_Tomato * 10000 + x_Wheat * 2000 = 50000, x_Tomato + x_Wheat <= 10
    # Solution: x_Tomato = 3.75 ha, x_Wheat = 6.25 ha (Multi-crop allocation within the same field!)
    farm = FarmInputs(field_area=10.0, water_budget=50000.0, labor_budget=1e6, fertilizer_budget=1e6, crops=crops, fields=fields)
    res = optimizer_v4.solve(farm)

    alloc = res.crop_allocation["Field_1"]
    assert alloc["Tomato"] > 0.0, "Tomato should be allocated partially"
    assert alloc["Wheat"] > 0.0, "Wheat should be allocated partially"
    assert alloc["Tomato"] + alloc["Wheat"] == pytest.approx(10.0, abs=1e-2)
    assert res.total_water_used == pytest.approx(50000.0, abs=1e-2)


# --- 3. Data Quality & Rotation Matrix Validation ---

def test_rotation_matrix_data_quality(rotation_loader):
    """Ensure rotation matrix loader enforces symmetry, binary values, and perennial classifications."""
    # 1. 53 crops recognized
    assert len(rotation_loader.matrix_crops) >= 50
    
    # 2. Check rotational rule: Wheat after Soybean is recommended (1)
    suit_good = rotation_loader.get_rotation_suitability("Soybean", "Wheat")
    assert suit_good == 1

    # 3. Check rotational rule: Dry Onion after Dry Onion is disallowed (0) to prevent soil disease
    suit_bad = rotation_loader.get_rotation_suitability("Fully Mature (Dry) Onion", "Fully Mature (Dry) Onion")
    assert suit_bad == 0


    # 4. Check perennial rule: Citrus (Tree) to Annual (Tomato) is disallowed (0)
    if "Citrus" in rotation_loader.matrix_crops:
        perennial_to_annual = rotation_loader.get_rotation_suitability("Citrus", "Tomato")
        assert perennial_to_annual == 0


def test_soil_suitability_filter(optimizer_v4):
    """Verify that unsuited soil chemistry (e.g. high salinity EC) strictly prevents crop allocation."""
    farm = get_example_farm_data()
    # Set حوض القبلي to extremely high salinity (EC = 15.0 dS/m)
    farm.fields["حوض القبلي"].ec = 15.0

    res = optimizer_v4.solve(farm)
    
    # Check that crops with low EC tolerance (like Tomato max_ec=1.5, Corn max_ec=2.0) are NOT allocated to حوض القبلي
    alloc_south = res.crop_allocation["حوض القبلي"]
    assert alloc_south.get("Tomato", 0.0) == 0.0
    assert alloc_south.get("Yellow Corn", 0.0) == 0.0



def test_invalid_crop_name_raises_clear_error(rotation_loader):
    """Ensure unregistered crop names raise clear Error."""
    with pytest.raises(ValueError, match="missing from the Rotation Matrix"):
        rotation_loader.validate_optimization_crops(["InvalidFakeCrop123"])
