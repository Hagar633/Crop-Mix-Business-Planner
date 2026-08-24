"""Unit tests for Version 3 Crop Mix Optimizer (Field-Level Allocation & Soil Suitability)."""

import pytest
from crop_mix.data.example_data import (
    CropParameters,
    CropSoilRequirement,
    FieldParameters,
    FarmInputs,
    get_example_farm_data,
)
from crop_mix.models.optimizer_v3 import CropMixOptimizerV3


def test_v3_optimizer_optimal_status_and_profit():
    """Verify V3 optimizer solves successfully and calculates correct total profit."""
    farm_inputs = get_example_farm_data()
    optimizer = CropMixOptimizerV3()
    result = optimizer.solve(farm_inputs)

    assert result.is_feasible, f"V3 Solver failed with status: {result.status}"
    assert result.status.lower() in ("optimal", "feasible")
    assert result.expected_profit > 0.0

    # Verify financial identity: Net Profit = Revenue - ProdCost - LaborCost - FertCost
    calc_net = (
        result.total_expected_revenue
        - result.total_production_cost
        - result.total_labor_cost
        - result.total_fertilizer_cost
    )
    assert result.expected_profit == pytest.approx(calc_net, rel=1e-3)


def test_field_area_constraints():
    """Verify that per-field allocations do not exceed each individual field's area."""
    farm_inputs = get_example_farm_data()
    optimizer = CropMixOptimizerV3()
    result = optimizer.solve(farm_inputs)

    for f_name, allocated_ha in result.field_land_used.items():
        limit = result.field_land_limits[f_name]
        assert allocated_ha <= limit + 1e-4, f"Field {f_name} exceeded area limit: {allocated_ha} > {limit}"


def test_unsuitable_crop_zero_allocation_constraint():
    """EXPLICIT TEST: Verify that a crop with suitability=0 NEVER receives positive allocation on that field."""
    # Setup: Field_Acidic has pH=5.0. SensitiveCrop requires min pH 6.5 -> suitability=0.
    farm = FarmInputs(
        field_area=50.0,
        water_budget=1_000_000.0,
        labor_budget=100_000.0,
        fertilizer_budget=100_000.0,
        fields={
            "Field_Acidic": FieldParameters(
                name="Field_Acidic",
                area=50.0,
                ph=5.0,  # Highly acidic
                ec=1.0,
                texture="Loam",
                organic_matter=2.0,
            )
        },
        crops={
            "SensitiveHighProfitCrop": CropParameters(
                name="SensitiveHighProfitCrop",
                expected_yield=100.0,  # Extremely profitable
                price=1000.0,
                production_cost=100.0,
                water_requirement=10.0,
                soil_requirement=CropSoilRequirement(
                    min_ph=6.5,  # Unsuitable for pH 5.0!
                    max_ph=7.5,
                    max_ec=2.0,
                    suitable_textures=["Loam"],
                ),
            ),
            "TolerantLowProfitCrop": CropParameters(
                name="TolerantLowProfitCrop",
                expected_yield=2.0,
                price=100.0,
                production_cost=50.0,
                water_requirement=10.0,
                soil_requirement=CropSoilRequirement(
                    min_ph=4.5,  # Suitable for pH 5.0
                    max_ph=7.5,
                    max_ec=2.0,
                    suitable_textures=["Loam"],
                ),
            ),
        },
    )

    optimizer = CropMixOptimizerV3()
    result = optimizer.solve(farm)

    assert result.is_feasible

    # Verify suitability matrix is 0 for SensitiveHighProfitCrop on Field_Acidic
    assert result.suitability_matrix[("Field_Acidic", "SensitiveHighProfitCrop")] == 0
    assert result.suitability_matrix[("Field_Acidic", "TolerantLowProfitCrop")] == 1

    # CRITICAL ASSERTION: Sensitive crop allocation MUST be exactly 0.0
    sensitive_alloc = result.crop_allocation["Field_Acidic"]["SensitiveHighProfitCrop"]
    assert sensitive_alloc == 0.0, (
        f"Unsuitable crop received non-zero allocation: {sensitive_alloc} ha!"
    )

    # Tolerant crop can receive allocation
    tolerant_alloc = result.crop_allocation["Field_Acidic"]["TolerantLowProfitCrop"]
    assert tolerant_alloc > 0.0


def test_v3_water_constraint_binding():
    """Verify global water budget constraint is respected across all fields."""
    farm = FarmInputs(
        field_area=100.0,
        water_budget=15000.0,  # Strict water budget
        labor_budget=100_000.0,
        fertilizer_budget=100_000.0,
        fields={
            "F1": FieldParameters(name="F1", area=50.0, ph=7.0, ec=1.0, texture="Loam", organic_matter=2.0),
            "F2": FieldParameters(name="F2", area=50.0, ph=7.0, ec=1.0, texture="Loam", organic_matter=2.0),
        },
        crops={
            "ThirstyCrop": CropParameters(
                name="ThirstyCrop",
                expected_yield=10.0,
                price=500.0,
                production_cost=500.0,
                water_requirement=5000.0,  # 5,000 m^3/ha -> max 3 ha total across all fields
            )
        },
    )

    optimizer = CropMixOptimizerV3()
    result = optimizer.solve(farm)

    assert result.is_feasible
    assert result.total_water_used <= farm.water_budget + 1e-4
    assert result.total_land_used == pytest.approx(3.0, abs=1e-3)


def test_v3_labor_constraint_binding():
    """Verify global labor budget constraint is respected across all fields."""
    farm = FarmInputs(
        field_area=100.0,
        water_budget=1_000_000.0,
        labor_budget=200.0,  # 200 hours available -> max 10 ha of 20 hrs/ha crop
        fertilizer_budget=100_000.0,
        fields={
            "F1": FieldParameters(name="F1", area=50.0, ph=7.0, ec=1.0, texture="Loam", organic_matter=2.0),
            "F2": FieldParameters(name="F2", area=50.0, ph=7.0, ec=1.0, texture="Loam", organic_matter=2.0),
        },
        crops={
            "LaborCrop": CropParameters(
                name="LaborCrop",
                expected_yield=10.0,
                price=500.0,
                production_cost=500.0,
                water_requirement=100.0,
                labor_requirement=20.0,
                labor_cost_per_hour=10.0,
            )
        },
    )

    optimizer = CropMixOptimizerV3()
    result = optimizer.solve(farm)

    assert result.is_feasible
    assert result.total_labor_used <= farm.labor_budget + 1e-4
    assert result.total_land_used == pytest.approx(10.0, abs=1e-3)


def test_v3_fertilizer_constraint_binding():
    """Verify global fertilizer budget constraint is respected across all fields."""
    farm = FarmInputs(
        field_area=100.0,
        water_budget=1_000_000.0,
        labor_budget=100_000.0,
        fertilizer_budget=500.0,  # 500 kg available -> max 5 ha of 100 kg/ha crop
        fields={
            "F1": FieldParameters(name="F1", area=50.0, ph=7.0, ec=1.0, texture="Loam", organic_matter=2.0),
            "F2": FieldParameters(name="F2", area=50.0, ph=7.0, ec=1.0, texture="Loam", organic_matter=2.0),
        },
        crops={
            "FertCrop": CropParameters(
                name="FertCrop",
                expected_yield=10.0,
                price=500.0,
                production_cost=500.0,
                water_requirement=100.0,
                fertilizer_requirement=100.0,
                fertilizer_cost_per_kg=2.0,
            )
        },
    )

    optimizer = CropMixOptimizerV3()
    result = optimizer.solve(farm)

    assert result.is_feasible
    assert result.total_fertilizer_used <= farm.fertilizer_budget + 1e-4
    assert result.total_land_used == pytest.approx(5.0, abs=1e-3)
