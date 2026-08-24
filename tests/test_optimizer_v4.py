"""Unit tests for Version 4 Crop Mix Optimizer (Crop Rotation integration)."""

import pytest
from crop_mix.data.example_data import (
    CropParameters,
    CropSoilRequirement,
    FieldParameters,
    FarmInputs,
    get_example_farm_data,
)
from crop_mix.models.optimizer_v4 import CropMixOptimizerV4


def test_v4_optimizer_optimal_status_and_profit():
    """Verify V4 optimizer finds a feasible optimal solution on example farm dataset."""
    farm_inputs = get_example_farm_data()
    optimizer = CropMixOptimizerV4()
    result = optimizer.solve(farm_inputs)

    assert result.is_feasible, f"V4 Solver failed with status: {result.status}"
    assert result.status.lower() in ("optimal", "feasible")
    assert result.expected_profit > 0.0


def test_no_previous_crop_unconstrained_by_rotation():
    """Verify a field with no previous crop (None) is unconstrained by rotation logic."""
    farm_inputs = get_example_farm_data()
    # Field_East has previous_crop = None
    optimizer = CropMixOptimizerV4()
    result = optimizer.solve(farm_inputs)

    assert result.is_feasible
    assert result.field_previous_crops["Field_East"] is None
    # For Field_East, all crops should have rotation_suitability == 1
    for crop in farm_inputs.crops.keys():
        assert result.rotation_suitability_matrix[("Field_East", crop)] == 1


def test_annual_to_perennial_disallowed_in_lp_solve():
    """EXPLICIT TEST (Correction 5): Verify LP solve prevents allocating a field with an annual previous crop to a perennial crop."""
    # Field_Annual has previous_crop = "Wheat" (annual).
    # Orange is a Tree/Fruit Perennial.
    farm = FarmInputs(
        field_area=50.0,
        water_budget=1_000_000.0,
        labor_budget=100_000.0,
        fertilizer_budget=100_000.0,
        fields={
            "Field_Annual": FieldParameters(
                name="Field_Annual",
                area=50.0,
                ph=7.0,
                ec=1.0,
                texture="Loam",
                organic_matter=2.0,
                previous_crop="Wheat",  # Annual
            )
        },
        crops={
            "Orange": CropParameters(
                name="Orange",
                expected_yield=200.0,  # Extremely profitable
                price=500.0,
                production_cost=100.0,
                water_requirement=10.0,
                soil_requirement=CropSoilRequirement(min_ph=5.0, max_ph=8.5, max_ec=3.0, suitable_textures=["Loam"]),
            ),
            "Soybean": CropParameters(
                name="Soybean",
                expected_yield=3.0,
                price=450.0,
                production_cost=650.0,
                water_requirement=4000.0,
                soil_requirement=CropSoilRequirement(min_ph=5.0, max_ph=8.5, max_ec=3.0, suitable_textures=["Loam"]),
            ),
        },
    )

    optimizer = CropMixOptimizerV4()
    result = optimizer.solve(farm)

    assert result.is_feasible

    # Rotation matrix value for Wheat -> Orange MUST be 0
    assert result.rotation_suitability_matrix[("Field_Annual", "Orange")] == 0

    # CRITICAL ASSERTION: Orange allocation on Field_Annual MUST be 0.0
    orange_alloc = result.crop_allocation["Field_Annual"]["Orange"]
    assert orange_alloc == 0.0, f"Perennial crop received non-zero allocation on annual previous crop field: {orange_alloc} ha"


def test_rotation_combined_with_soil_suitability():
    """Verify simultaneous enforcement of rotation suitability AND soil suitability."""
    # Field_X: previous_crop = "Wheat". Soil pH = 5.5 (Acidic).
    # Crop 1: Soybean (Rotation from Wheat = 1, but Soil pH 5.5 < min pH 6.0 -> Soil = 0) -> Allocation MUST be 0.
    # Crop 2: Cotton (Rotation from Wheat = 1, Soil pH 5.5 >= min pH 5.5 -> Soil = 1) -> Allowed.
    farm = FarmInputs(
        field_area=40.0,
        water_budget=500_000.0,
        labor_budget=50_000.0,
        fertilizer_budget=50_000.0,
        fields={
            "Field_X": FieldParameters(
                name="Field_X",
                area=40.0,
                ph=5.5,
                ec=1.0,
                texture="Sandy",
                organic_matter=1.5,
                previous_crop="Wheat",
            )
        },
        crops={
            "Soybean": CropParameters(
                name="Soybean",
                expected_yield=5.0,
                price=1000.0,
                production_cost=100.0,
                water_requirement=100.0,
                soil_requirement=CropSoilRequirement(min_ph=6.0, max_ph=7.5, max_ec=2.5, suitable_textures=["Sandy"]),
            ),
            "Cotton": CropParameters(
                name="Cotton",
                expected_yield=2.5,
                price=1100.0,
                production_cost=1200.0,
                water_requirement=5000.0,
                soil_requirement=CropSoilRequirement(min_ph=5.5, max_ph=8.5, max_ec=4.0, suitable_textures=["Sandy"]),
            ),
        },
    )

    optimizer = CropMixOptimizerV4()
    result = optimizer.solve(farm)

    assert result.is_feasible
    assert result.soil_suitability_matrix[("Field_X", "Soybean")] == 0
    assert result.rotation_suitability_matrix[("Field_X", "Soybean")] == 1

    # Soybean fails soil suitability -> allocation must be 0.0
    assert result.crop_allocation["Field_X"]["Soybean"] == 0.0
    # Cotton passes both -> receives allocation
    assert result.crop_allocation["Field_X"]["Cotton"] > 0.0


def test_independent_per_field_previous_crops():
    """Verify each field's previous crop constraint is applied independently."""
    farm = get_example_farm_data()
    optimizer = CropMixOptimizerV4()
    result = optimizer.solve(farm)

    assert result.is_feasible
    assert result.field_previous_crops["Field_North"] == "Wheat"
    assert result.field_previous_crops["Field_South"] == "Soybean"
    assert result.field_previous_crops["Field_East"] is None


def test_infeasible_scenario_handling():
    """Verify joint constraint eliminating all crop options returns proper solution status."""
    # Field where soil + rotation eliminates all crops or resource budget limits allocation
    farm = FarmInputs(
        field_area=10.0,
        water_budget=1.0,  # Impossible water budget of 1 m^3 for 3500 m^3/ha crop
        labor_budget=1.0,
        fertilizer_budget=1.0,
        fields={
            "F1": FieldParameters(name="F1", area=10.0, ph=7.0, ec=1.0, texture="Loam", organic_matter=2.0, previous_crop="Wheat")
        },
        crops={
            "Wheat": CropParameters(
                name="Wheat",
                expected_yield=4.5,
                price=220.0,
                production_cost=600.0,
                water_requirement=3500.0,
                labor_requirement=15.0,
                fertilizer_requirement=150.0,
                soil_requirement=CropSoilRequirement(min_ph=6.0, max_ph=8.0, max_ec=2.5, suitable_textures=["Loam"]),
            )
        },
    )

    optimizer = CropMixOptimizerV4()
    result = optimizer.solve(farm)

    # Allocates 0 hectares to satisfy 1 m^3 water budget -> solution is feasible with 0 allocation
    assert result.is_feasible
    assert result.total_land_used == 0.0
