"""Unit tests for Version 2 Crop Mix Optimizer (Labor & Fertilizer extension)."""

import pytest
from crop_mix.data.example_data import CropParameters, FarmInputs, get_example_farm_data
from crop_mix.models.optimizer_v2 import CropMixOptimizerV2


def test_labor_cost_calculation():
    """Verify per-hectare labor cost calculation."""
    crop = CropParameters(
        name="TestCrop",
        expected_yield=5.0,
        price=100.0,
        production_cost=200.0,
        water_requirement=1000.0,
        labor_requirement=25.0,  # 25 hrs/ha
        labor_cost_per_hour=18.50,  # $18.50/hr
        fertilizer_requirement=0.0,
        fertilizer_cost_per_kg=0.0,
    )
    # labor_cost = 25 * 18.50 = 462.50 $/ha
    assert crop.labor_cost_per_hectare == pytest.approx(462.50)


def test_fertilizer_cost_calculation():
    """Verify per-hectare fertilizer cost calculation."""
    crop = CropParameters(
        name="TestCrop",
        expected_yield=5.0,
        price=100.0,
        production_cost=200.0,
        water_requirement=1000.0,
        labor_requirement=0.0,
        labor_cost_per_hour=0.0,
        fertilizer_requirement=120.0,  # 120 kg/ha
        fertilizer_cost_per_kg=2.25,  # $2.25/kg
    )
    # fertilizer_cost = 120 * 2.25 = 270.00 $/ha
    assert crop.fertilizer_cost_per_hectare == pytest.approx(270.00)


def test_net_profit_calculation():
    """Verify per-hectare net profit calculation considering revenue, prod cost, labor cost, and fertilizer cost."""
    crop = CropParameters(
        name="Cotton",
        expected_yield=2.5,
        price=1100.0,  # revenue = 2750 $/ha
        production_cost=1200.0,  # prod_cost = 1200 $/ha
        water_requirement=5000.0,
        labor_requirement=30.0,
        labor_cost_per_hour=20.0,  # labor_cost = 600 $/ha
        fertilizer_requirement=180.0,
        fertilizer_cost_per_kg=1.50,  # fert_cost = 270 $/ha
    )
    # revenue = 2750.0
    # profit = 2750.0 - 1200.0 - 600.0 - 270.0 = 680.0 $/ha
    assert crop.revenue_per_hectare == pytest.approx(2750.0)
    assert crop.profit_per_hectare == pytest.approx(680.0)


def test_v2_optimizer_solver_status_and_total_profit():
    """Verify V2 optimizer finds feasible optimal solution and correctly computes total profit."""
    farm_inputs = get_example_farm_data()
    optimizer = CropMixOptimizerV2()
    result = optimizer.solve(farm_inputs)

    assert result.is_feasible, f"Solver failed with status: {result.status}"
    assert result.status.lower() in ("optimal", "feasible")
    assert result.expected_profit > 0.0

    # Verify net profit equals total revenue minus all cost components
    calculated_net = (
        result.total_expected_revenue
        - result.total_production_cost
        - result.total_labor_cost
        - result.total_fertilizer_cost
    )
    assert result.expected_profit == pytest.approx(calculated_net, rel=1e-3)


def test_land_constraint_binding():
    """Verify that land constraint limits allocation when land is the bottleneck."""
    farm = FarmInputs(
        field_area=50.0,  # Tight land budget
        water_budget=1_000_000.0,
        labor_budget=100_000.0,
        fertilizer_budget=100_000.0,
        crops={
            "HighProfitCrop": CropParameters(
                name="HighProfitCrop",
                expected_yield=10.0,
                price=500.0,
                production_cost=1000.0,
                water_requirement=100.0,
                labor_requirement=1.0,
                labor_cost_per_hour=10.0,
                fertilizer_requirement=1.0,
                fertilizer_cost_per_kg=1.0,
            )
        },
    )
    optimizer = CropMixOptimizerV2()
    result = optimizer.solve(farm)

    assert result.is_feasible
    assert result.total_land_used == pytest.approx(50.0, abs=1e-3)
    assert result.total_land_used <= farm.field_area + 1e-4


def test_water_constraint_binding():
    """Verify water constraint limits allocation when water is the bottleneck."""
    farm = FarmInputs(
        field_area=100.0,
        water_budget=10000.0,  # 10,000 m^3 -> max 2 ha of 5,000 m^3/ha crop
        labor_budget=100_000.0,
        fertilizer_budget=100_000.0,
        crops={
            "ThirstyCrop": CropParameters(
                name="ThirstyCrop",
                expected_yield=10.0,
                price=500.0,
                production_cost=1000.0,
                water_requirement=5000.0,
                labor_requirement=1.0,
                labor_cost_per_hour=10.0,
                fertilizer_requirement=1.0,
                fertilizer_cost_per_kg=1.0,
            )
        },
    )
    optimizer = CropMixOptimizerV2()
    result = optimizer.solve(farm)

    assert result.is_feasible
    assert result.total_water_used <= farm.water_budget + 1e-4
    assert result.crop_allocation["ThirstyCrop"] == pytest.approx(2.0, abs=1e-3)


def test_labor_constraint_binding():
    """Verify labor constraint limits allocation when labor hours are the bottleneck."""
    farm = FarmInputs(
        field_area=100.0,
        water_budget=1_000_000.0,
        labor_budget=500.0,  # 500 hours available -> max 10 ha of 50 hrs/ha crop
        fertilizer_budget=100_000.0,
        crops={
            "LaborIntensiveCrop": CropParameters(
                name="LaborIntensiveCrop",
                expected_yield=10.0,
                price=500.0,
                production_cost=1000.0,
                water_requirement=100.0,
                labor_requirement=50.0,  # 50 hrs/ha
                labor_cost_per_hour=15.0,
                fertilizer_requirement=1.0,
                fertilizer_cost_per_kg=1.0,
            )
        },
    )
    optimizer = CropMixOptimizerV2()
    result = optimizer.solve(farm)

    assert result.is_feasible
    assert result.total_labor_used <= farm.labor_budget + 1e-4
    assert result.crop_allocation["LaborIntensiveCrop"] == pytest.approx(10.0, abs=1e-3)


def test_fertilizer_constraint_binding():
    """Verify fertilizer constraint limits allocation when fertilizer is the bottleneck."""
    farm = FarmInputs(
        field_area=100.0,
        water_budget=1_000_000.0,
        labor_budget=100_000.0,
        fertilizer_budget=1200.0,  # 1200 kg available -> max 6 ha of 200 kg/ha crop
        crops={
            "FertilizerHeavyCrop": CropParameters(
                name="FertilizerHeavyCrop",
                expected_yield=10.0,
                price=500.0,
                production_cost=1000.0,
                water_requirement=100.0,
                labor_requirement=1.0,
                labor_cost_per_hour=10.0,
                fertilizer_requirement=200.0,  # 200 kg/ha
                fertilizer_cost_per_kg=2.0,
            )
        },
    )
    optimizer = CropMixOptimizerV2()
    result = optimizer.solve(farm)

    assert result.is_feasible
    assert result.total_fertilizer_used <= farm.fertilizer_budget + 1e-4
    assert result.crop_allocation["FertilizerHeavyCrop"] == pytest.approx(6.0, abs=1e-3)
