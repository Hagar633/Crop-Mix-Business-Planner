"""Unit tests for Version 1 Crop Mix Optimizer."""

import pytest
from crop_mix.data.example_data import CropParameters, FarmInputs, get_example_farm_data
from crop_mix.models.optimizer_v1 import CropMixOptimizerV1


def test_profit_per_hectare_calculation():
    """Verify profit per hectare derived parameter calculation."""
    # Wheat: 4.5 tons/ha * $220/ton - $600/ha = $990 - $600 = $390/ha
    wheat = CropParameters(
        name="Wheat",
        expected_yield=4.5,
        price=220.0,
        production_cost=600.0,
        water_requirement=3500.0,
    )
    assert wheat.profit_per_hectare == pytest.approx(390.0)


def test_optimizer_returns_feasible_solution():
    """Verify that the optimizer finds a feasible optimal solution on example dataset."""
    farm_inputs = get_example_farm_data()
    optimizer = CropMixOptimizerV1()

    result = optimizer.solve(farm_inputs)

    # 1. Solution is feasible & optimal
    assert result.is_feasible, f"Optimizer failed with status: {result.status}"

    # 2. Total land used does not exceed available field area
    assert result.total_land_used <= farm_inputs.field_area + 1e-4

    # 3. Total water used does not exceed water budget
    assert result.total_water_used <= farm_inputs.water_budget + 1.0

    # 4. Allocations are non-negative
    for crop, ha in result.crop_allocation.items():
        assert ha >= 0.0, f"Allocation for {crop} is negative: {ha}"

    # 5. Profit is strictly positive
    assert result.expected_profit > 0.0

    # 6. Verify hand-calculated upper bound matching
    # Check that land used matches sum of allocations
    sum_allocations = sum(result.crop_allocation.values())
    assert result.total_land_used == pytest.approx(sum_allocations, abs=1e-3)


def test_optimizer_respects_water_constraint():
    """Verify that a tight water budget restricts water-heavy crops."""
    # Create farm with very limited water (e.g. 10,000 m^3 for 100 ha)
    farm = FarmInputs(
        field_area=100.0,
        water_budget=10000.0,
        crops={
            "WaterIntensiveCrop": CropParameters(
                name="WaterIntensiveCrop",
                expected_yield=10.0,
                price=500.0,
                production_cost=1000.0,
                water_requirement=5000.0,  # 5000 m^3 / ha -> max 2 ha possible
            ),
            "DroughtResistantCrop": CropParameters(
                name="DroughtResistantCrop",
                expected_yield=2.0,
                price=300.0,
                production_cost=200.0,
                water_requirement=100.0,  # 100 m^3 / ha
            ),
        },
    )

    optimizer = CropMixOptimizerV1()
    result = optimizer.solve(farm)

    assert result.is_feasible
    assert result.total_water_used <= farm.water_budget + 1e-4
    assert result.crop_allocation["WaterIntensiveCrop"] <= 2.0 + 1e-4
