"""Unit tests for Internship 4B Financial Projection Layer."""

import pytest
from crop_mix.data.example_data import CropParameters, FieldParameters, FarmInputs
from crop_mix.models.optimizer_v4 import OptimizationResultV4
from crop_mix.business.financial_projection import FinancialProjection, FieldCropFinancial


@pytest.fixture
def sample_data():
    """Small hand-built test data for easy verification."""
    crop_wheat = CropParameters(
        name="Wheat",
        expected_yield=4.0,  # tons/ha
        price=200.0,  # $/ton -> revenue = 800 $/ha
        production_cost=300.0,  # $/ha
        water_requirement=1000.0,
        labor_requirement=10.0,
        labor_cost_per_hour=10.0,  # labor cost = 100 $/ha
        fertilizer_requirement=50.0,
        fertilizer_cost_per_kg=2.0,  # fertilizer cost = 100 $/ha
        # total cost per ha = 300 + 100 + 100 = 500 $/ha
        # net profit per ha = 800 - 500 = 300 $/ha
    )

    crop_corn = CropParameters(
        name="Yellow Corn",
        expected_yield=10.0,  # tons/ha
        price=100.0,  # $/ton -> revenue = 1000 $/ha
        production_cost=400.0,  # $/ha
        water_requirement=2000.0,
        labor_requirement=20.0,
        labor_cost_per_hour=10.0,  # labor cost = 200 $/ha
        fertilizer_requirement=100.0,
        fertilizer_cost_per_kg=1.0,  # fertilizer cost = 100 $/ha
        # total cost per ha = 400 + 200 + 100 = 700 $/ha
        # net profit per ha = 1000 - 700 = 300 $/ha
    )

    farm_inputs = FarmInputs(
        field_area=50.0,
        water_budget=100000.0,
        crops={"Wheat": crop_wheat, "Yellow Corn": crop_corn},
        fields={
            "F1": FieldParameters(name="F1", area=30.0, ph=7.0, ec=1.0, texture="Loam", organic_matter=2.0),
            "F2": FieldParameters(name="F2", area=20.0, ph=7.0, ec=1.0, texture="Loam", organic_matter=2.0),
        },
    )

    result_v4 = OptimizationResultV4(
        status="optimal",
        is_feasible=True,
        crop_allocation={
            "F1": {"Wheat": 10.0, "Yellow Corn": 0.0},  # 10 ha Wheat, 0 ha Corn
            "F2": {"Wheat": 0.0, "Yellow Corn": 5.0},   # 0 ha Wheat, 5 ha Corn
        },
        field_land_used={"F1": 10.0, "F2": 5.0},
        field_land_limits={"F1": 30.0, "F2": 20.0},
        total_land_used=15.0,
        total_water_used=20000.0,
        water_budget_limit=100000.0,
        total_labor_used=200.0,
        labor_budget_limit=1000.0,
        total_fertilizer_used=1000.0,
        fertilizer_budget_limit=5000.0,
        total_expected_revenue=13000.0,
        total_production_cost=5000.0,
        total_labor_cost=2000.0,
        total_fertilizer_cost=1500.0,
        expected_profit=4500.0,
        soil_suitability_matrix={("F1", "Wheat"): 1, ("F1", "Yellow Corn"): 1, ("F2", "Wheat"): 1, ("F2", "Yellow Corn"): 1},
        rotation_suitability_matrix={("F1", "Wheat"): 1, ("F1", "Yellow Corn"): 1, ("F2", "Wheat"): 1, ("F2", "Yellow Corn"): 1},
        field_previous_crops={"F1": None, "F2": None},
    )

    return farm_inputs, result_v4


def test_revenue_calculation(sample_data):
    """1. Test revenue calculation: 10 ha * 4.0 tons/ha * $200/ton = $8,000."""
    farm_inputs, result_v4 = sample_data
    calc = FinancialProjection()
    res = calc.calculate(farm_inputs, result_v4)

    wheat_f1 = res.field_projections["F1"]["Wheat"]
    assert wheat_f1.expected_revenue == pytest.approx(8000.0)


def test_production_cost_calculation(sample_data):
    """2. Test production cost calculation: 10 ha * $300/ha = $3,000."""
    farm_inputs, result_v4 = sample_data
    calc = FinancialProjection()
    res = calc.calculate(farm_inputs, result_v4)

    wheat_f1 = res.field_projections["F1"]["Wheat"]
    assert wheat_f1.production_cost == pytest.approx(3000.0)


def test_labor_cost_calculation(sample_data):
    """3. Test labor cost calculation: 10 ha * (10 hrs/ha * $10/hr) = $1,000."""
    farm_inputs, result_v4 = sample_data
    calc = FinancialProjection()
    res = calc.calculate(farm_inputs, result_v4)

    wheat_f1 = res.field_projections["F1"]["Wheat"]
    assert wheat_f1.labor_cost == pytest.approx(1000.0)


def test_fertilizer_cost_calculation(sample_data):
    """4. Test fertilizer cost calculation: 10 ha * (50 kg/ha * $2/kg) = $1,000."""
    farm_inputs, result_v4 = sample_data
    calc = FinancialProjection()
    res = calc.calculate(farm_inputs, result_v4)

    wheat_f1 = res.field_projections["F1"]["Wheat"]
    assert wheat_f1.fertilizer_cost == pytest.approx(1000.0)


def test_total_cost_calculation(sample_data):
    """5. Test total cost calculation: 3000 + 1000 + 1000 = $5,000."""
    farm_inputs, result_v4 = sample_data
    calc = FinancialProjection()
    res = calc.calculate(farm_inputs, result_v4)

    wheat_f1 = res.field_projections["F1"]["Wheat"]
    assert wheat_f1.total_cost == pytest.approx(5000.0)


def test_net_profit_calculation(sample_data):
    """6. Test net profit calculation: 8000 - 5000 = $3,000."""
    farm_inputs, result_v4 = sample_data
    calc = FinancialProjection()
    res = calc.calculate(farm_inputs, result_v4)

    wheat_f1 = res.field_projections["F1"]["Wheat"]
    assert wheat_f1.net_profit == pytest.approx(3000.0)


def test_profit_per_hectare_calculation(sample_data):
    """7. Test profit per hectare calculation: $3000 / 10 ha = $300/ha."""
    farm_inputs, result_v4 = sample_data
    calc = FinancialProjection()
    res = calc.calculate(farm_inputs, result_v4)

    wheat_f1 = res.field_projections["F1"]["Wheat"]
    assert wheat_f1.profit_per_hectare == pytest.approx(300.0)


def test_profit_margin_calculation(sample_data):
    """8. Test profit margin calculation: $3000 / $8000 = 0.375 (37.5%)."""
    farm_inputs, result_v4 = sample_data
    calc = FinancialProjection()
    res = calc.calculate(farm_inputs, result_v4)

    wheat_f1 = res.field_projections["F1"]["Wheat"]
    assert wheat_f1.profit_margin == pytest.approx(0.375)


def test_field_level_projection_structure(sample_data):
    """9. Test field-level projection preserves per-field breakdown."""
    farm_inputs, result_v4 = sample_data
    calc = FinancialProjection()
    res = calc.calculate(farm_inputs, result_v4)

    assert "F1" in res.field_projections
    assert "Wheat" in res.field_projections["F1"]

    assert "F2" in res.field_projections
    assert "Yellow Corn" in res.field_projections["F2"]

    corn_f2 = res.field_projections["F2"]["Yellow Corn"]
    # Corn F2: 5 ha * 10 tons * $100 = $5000 revenue
    # total cost = 5 * 700 = $3500 cost -> net profit = $1500
    assert corn_f2.expected_revenue == pytest.approx(5000.0)
    assert corn_f2.net_profit == pytest.approx(1500.0)


def test_farm_level_totals(sample_data):
    """10. Test farm-level aggregated totals."""
    farm_inputs, result_v4 = sample_data
    calc = FinancialProjection()
    res = calc.calculate(farm_inputs, result_v4)

    summary = res.farm_summary
    assert summary.total_area == pytest.approx(15.0)  # 10 ha Wheat + 5 ha Corn
    assert summary.total_expected_revenue == pytest.approx(13000.0)  # 8000 + 5000
    assert summary.total_production_cost == pytest.approx(5000.0)  # 3000 + 2000
    assert summary.total_labor_cost == pytest.approx(2000.0)  # 1000 + 1000
    assert summary.total_fertilizer_cost == pytest.approx(1500.0)  # 1000 + 500
    assert summary.total_cost == pytest.approx(8500.0)  # 5000 + 2000 + 1500
    assert summary.total_expected_net_profit == pytest.approx(4500.0)  # 13000 - 8500
    assert summary.overall_profit_margin == pytest.approx(round(4500.0 / 13000.0, 4))


def test_sum_of_field_profits_equals_farm_total(sample_data):
    """11. Test that the sum of field/crop net profits strictly equals farm total net profit."""
    farm_inputs, result_v4 = sample_data
    calc = FinancialProjection()
    res = calc.calculate(farm_inputs, result_v4)

    field_net_sum = sum(
        proj.net_profit
        for field_map in res.field_projections.values()
        for proj in field_map.values()
    )
    assert res.farm_summary.total_expected_net_profit == pytest.approx(field_net_sum)


def test_zero_allocation_filtered_out(sample_data):
    """12. Test that zero allocation entries (area == 0) are NOT included in field projections."""
    farm_inputs, result_v4 = sample_data
    calc = FinancialProjection()
    res = calc.calculate(farm_inputs, result_v4)

    # In F1, Yellow Corn was allocated 0 ha -> should not be in F1 map
    assert "Yellow Corn" not in res.field_projections["F1"]
    # In F2, Wheat was allocated 0 ha -> should not be in F2 map
    assert "Wheat" not in res.field_projections["F2"]


def test_zero_revenue_safe_division():
    """13. Test that zero expected revenue handles profit margin safely without division-by-zero."""
    crop_free = CropParameters(
        name="FreeCrop",
        expected_yield=0.0,  # 0 yield -> 0 revenue
        price=100.0,
        production_cost=50.0,
        water_requirement=100.0,
    )

    farm_inputs = FarmInputs(
        field_area=10.0,
        water_budget=10000.0,
        crops={"FreeCrop": crop_free},
        fields={"F1": FieldParameters(name="F1", area=10.0, ph=7.0, ec=1.0, texture="Loam", organic_matter=2.0)},
    )

    result_v4 = OptimizationResultV4(
        status="optimal",
        is_feasible=True,
        crop_allocation={"F1": {"FreeCrop": 5.0}},
        field_land_used={"F1": 5.0},
        field_land_limits={"F1": 10.0},
        total_land_used=5.0,
        total_water_used=500.0,
        water_budget_limit=10000.0,
        total_labor_used=0.0,
        labor_budget_limit=1000.0,
        total_fertilizer_used=0.0,
        fertilizer_budget_limit=5000.0,
        total_expected_revenue=0.0,
        total_production_cost=250.0,
        total_labor_cost=0.0,
        total_fertilizer_cost=0.0,
        expected_profit=-250.0,
        soil_suitability_matrix={("F1", "FreeCrop"): 1},
        rotation_suitability_matrix={("F1", "FreeCrop"): 1},
        field_previous_crops={"F1": None},
    )

    calc = FinancialProjection()
    res = calc.calculate(farm_inputs, result_v4)

    proj = res.field_projections["F1"]["FreeCrop"]
    assert proj.expected_revenue == 0.0
    assert proj.profit_margin == 0.0  # Handled safely without error!
    assert res.farm_summary.overall_profit_margin == 0.0
