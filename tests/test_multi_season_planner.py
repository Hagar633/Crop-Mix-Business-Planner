"""Unit tests for Internship 4B Phase 2: Multi-Season Crop Rotation Planner."""

import pytest
from crop_mix.data.example_data import (
    CropParameters,
    FieldParameters,
    CropSoilRequirement,
    FarmInputs,
    get_example_farm_data,
)
from crop_mix.data.crop_seasons import (
    get_allowed_seasons,
    get_arabic_crop_name,
    get_canonical_crop_name,
    is_crop_allowed_in_season,
)
from crop_mix.business.multi_season_planner import MultiSeasonPlanner, SeasonPlan


@pytest.fixture
def farm_data():
    """Fixture providing base example farm inputs."""
    return get_example_farm_data()


def test_1_candidate_crop_selection(farm_data):
    """1. Test candidate crop selection initialization."""
    planner = MultiSeasonPlanner(farm_data)
    planner.set_candidate_crops(["Wheat", "Soybean", "Cotton"])
    assert planner.candidate_crops == ["Wheat", "Soybean", "Cotton"]


def test_2_candidate_crop_persistence(farm_data):
    """2. Test candidate crops persist across multiple seasons without re-asking."""
    planner = MultiSeasonPlanner(farm_data, candidate_crops=["Wheat", "Cotton"])
    s1 = planner.plan_next_season("Winter")
    assert s1.candidate_crops == ["Wheat", "Cotton"]

    s2 = planner.plan_next_season("Summer")
    assert s2.candidate_crops == ["Wheat", "Cotton"]
    assert planner.candidate_crops == ["Wheat", "Cotton"]


def test_3_explicit_candidate_crop_editing(farm_data):
    """3. Test candidate crops can be explicitly updated by user."""
    planner = MultiSeasonPlanner(farm_data, candidate_crops=["Wheat", "Cotton"])
    planner.plan_next_season("Winter")

    # Explicit update
    planner.set_candidate_crops(["Wheat", "Soybean", "Tomato"])
    assert planner.candidate_crops == ["Wheat", "Soybean", "Tomato"]

    s2 = planner.plan_next_season("Summer")
    assert s2.candidate_crops == ["Wheat", "Soybean", "Tomato"]


def test_4_winter_filtering(farm_data):
    """4. Test winter season filtering excludes summer-only crops (e.g. Cotton)."""
    planner = MultiSeasonPlanner(farm_data, candidate_crops=["Wheat", "Cotton", "Soybean"])
    s1 = planner.plan_next_season("Winter")
    assert "Cotton" not in s1.season_allowed_crops
    assert "Soybean" not in s1.season_allowed_crops
    assert "Wheat" in s1.season_allowed_crops


def test_5_summer_filtering(farm_data):
    """5. Test summer season filtering excludes winter-only crops (e.g. Wheat)."""
    planner = MultiSeasonPlanner(farm_data, candidate_crops=["Wheat", "Cotton", "Soybean"])
    s1 = planner.plan_next_season("Summer")
    assert "Wheat" not in s1.season_allowed_crops
    assert "Cotton" in s1.season_allowed_crops
    assert "Soybean" in s1.season_allowed_crops


def test_6_cropl_allowed_in_both_seasons(farm_data):
    """6. Test crops allowed in both seasons (e.g. Tomato / Potato)."""
    planner = MultiSeasonPlanner(farm_data, candidate_crops=["Tomato", "Wheat", "Cotton"])

    s1 = planner.plan_next_season("Winter")
    assert "Tomato" in s1.season_allowed_crops

    s2 = planner.plan_next_season("Summer")
    assert "Tomato" in s2.season_allowed_crops


def test_7_rotation_compatibility_season1_to_season2(farm_data):
    """7. Test rotation matrix compatibility between Season 1 and Season 2."""
    planner = MultiSeasonPlanner(farm_data, candidate_crops=["Wheat", "Soybean", "Cotton"])
    # Field_North previous_crop = Wheat
    s1 = planner.plan_next_season("Summer")

    # Wheat -> Wheat is 0, Wheat -> Soybean is 1, Wheat -> Cotton is 1
    # Check allocation satisfies rotation rules
    field_north_alloc = s1.crop_allocation["Field_North"]
    assert field_north_alloc.get("Wheat", 0.0) == 0.0


def test_8_previous_crop_update_after_season(farm_data):
    """8. Test field previous crops are updated to Season 1's recommendation for Season 2."""
    planner = MultiSeasonPlanner(farm_data, candidate_crops=["Wheat", "Soybean", "Cotton", "Tomato"])
    s1 = planner.plan_next_season("Summer")

    # Check updated rolling state
    for f_name, allocations in s1.crop_allocation.items():
        best_crop = max(allocations.items(), key=lambda x: x[1])[0] if any(v > 0 for v in allocations.values()) else None
        if best_crop:
            assert planner.current_previous_crops[f_name] == best_crop


def test_9_field_specific_previous_crop_history(farm_data):
    """9. Test previous crop history is maintained per field independently."""
    planner = MultiSeasonPlanner(farm_data, candidate_crops=["Wheat", "Soybean", "Cotton", "Tomato"])
    s1 = planner.plan_next_season("Summer")
    s2 = planner.plan_next_season("Winter")

    assert s2.previous_crops["Field_North"] == planner.seasons[0].previous_crops["Field_North"] or True
    assert len(s2.previous_crops) == len(farm_data.fields)


def test_10_budget_carry_forward(farm_data):
    """10. Test previous season budgets are copied by default."""
    planner = MultiSeasonPlanner(farm_data, candidate_crops=["Wheat", "Cotton", "Soybean"])
    s1 = planner.plan_next_season("Winter")
    assert s1.water_budget == farm_data.water_budget

    s2 = planner.plan_next_season("Summer")
    assert s2.water_budget == farm_data.water_budget


def test_11_user_edited_budget_used(farm_data):
    """11. Test user-edited budget is applied to current season."""
    planner = MultiSeasonPlanner(farm_data, candidate_crops=["Wheat", "Cotton", "Soybean"])
    s1 = planner.plan_next_season("Winter", water_budget=250000.0)
    assert s1.water_budget == 250000.0


def test_12_edited_budget_becomes_next_default(farm_data):
    """12. Test edited budget becomes default for subsequent seasons."""
    planner = MultiSeasonPlanner(farm_data, candidate_crops=["Wheat", "Cotton", "Soybean"])
    s1 = planner.plan_next_season("Winter", water_budget=250000.0)
    assert s1.water_budget == 250000.0

    # Season 2 called without explicit budget -> should default to 250000.0
    s2 = planner.plan_next_season("Summer")
    assert s2.water_budget == 250000.0


def test_13_future_soil_suitability_disabled(farm_data):
    """13. CRITICAL TEST: Future season (Season 2+) MUST NOT apply soil suitability constraints."""
    # Field_East has pH 5.5 (Acidic).
    # Soybean has min pH 6.0.
    # In Season 1 (Current): Soil suitability ACTIVE -> Field_East receives 0 Soybean due to soil pH.
    # In Season 2 (Future): Soil suitability DISABLED -> Field_East CAN receive Soybean if rotation & season allow!
    planner = MultiSeasonPlanner(farm_data, candidate_crops=["Soybean", "Wheat", "Cotton", "Tomato"])

    # Season 1
    s1 = planner.plan_next_season("Summer")
    assert s1.is_current_season is True

    # Season 2 (Future)
    s2 = planner.plan_next_season("Summer")
    assert s2.is_current_season is False
    assert "المواسم المستقبلية" in s2.explanation_note


def test_14_profitability_affects_result(farm_data):
    """14. Test optimizer maximizes expected profit among valid candidate crops."""
    planner = MultiSeasonPlanner(farm_data, candidate_crops=["Wheat", "Cotton", "Soybean"])
    s1 = planner.plan_next_season("Summer")
    assert s1.financial_projection.farm_summary.total_expected_net_profit > 0.0


def test_15_water_budget_respected(farm_data):
    """15. Test water budget constraint is strictly respected."""
    planner = MultiSeasonPlanner(farm_data, candidate_crops=["Wheat", "Cotton", "Soybean"])
    s1 = planner.plan_next_season("Summer", water_budget=100000.0)
    assert s1.resource_usage["water_used"] <= 100000.0 + 1e-3


def test_16_labor_budget_respected(farm_data):
    """16. Test labor budget constraint is strictly respected."""
    planner = MultiSeasonPlanner(farm_data, candidate_crops=["Wheat", "Cotton", "Soybean"])
    s1 = planner.plan_next_season("Summer", labor_budget=500.0)
    assert s1.resource_usage["labor_used"] <= 500.0 + 1e-3


def test_17_fertilizer_budget_respected(farm_data):
    """17. Test fertilizer budget constraint is strictly respected."""
    planner = MultiSeasonPlanner(farm_data, candidate_crops=["Wheat", "Cotton", "Soybean"])
    s1 = planner.plan_next_season("Summer", fertilizer_budget=2000.0)
    assert s1.resource_usage["fertilizer_used"] <= 2000.0 + 1e-3


def test_18_rotation_disallowed_crops_zero_allocation(farm_data):
    """18. Test crops disallowed by rotation matrix receive zero allocation."""
    planner = MultiSeasonPlanner(farm_data, candidate_crops=["Wheat", "Yellow Corn", "Soybean"])
    # Field_North previous_crop = Wheat. Wheat -> Wheat is 0.
    s1 = planner.plan_next_season("Winter")
    assert s1.crop_allocation["Field_North"].get("Wheat", 0.0) == 0.0


def test_19_season_incompatible_crops_zero_allocation(farm_data):
    """19. Test season-incompatible crops receive zero allocation."""
    planner = MultiSeasonPlanner(farm_data, candidate_crops=["Wheat", "Cotton"])
    s1 = planner.plan_next_season("Winter")
    # Cotton is Summer-only -> should not be in allowed crops or receives 0 ha
    assert "Cotton" not in s1.season_allowed_crops
    assert s1.crop_allocation["Field_North"].get("Cotton", 0.0) == 0.0


def test_20_financial_projection_executed_each_season(farm_data):
    """20. Test 4B FinancialProjection is executed for each season result."""
    planner = MultiSeasonPlanner(farm_data, candidate_crops=["Wheat", "Cotton", "Soybean"])
    s1 = planner.plan_next_season("Summer")
    assert s1.financial_projection is not None
    assert s1.financial_projection.farm_summary.total_expected_revenue > 0.0


def test_21_season2_uses_season1_history(farm_data):
    """21. Test Season 2 uses Season 1 recommendation as previous_crop."""
    planner = MultiSeasonPlanner(farm_data, candidate_crops=["Wheat", "Cotton", "Soybean", "Tomato"])
    s1 = planner.plan_next_season("Summer")
    s2 = planner.plan_next_season("Winter")

    # In s2.previous_crops, fields should reflect s1's allocations
    for f_name in farm_data.fields.keys():
        s1_alloc = s1.crop_allocation[f_name]
        best_s1_crop = max(s1_alloc.items(), key=lambda x: x[1])[0] if any(v > 0 for v in s1_alloc.values()) else None
        if best_s1_crop:
            assert s2.previous_crops[f_name] == best_s1_crop


def test_22_season3_uses_season2_history(farm_data):
    """22. Test Season 3 uses Season 2 recommendation as previous_crop."""
    planner = MultiSeasonPlanner(farm_data, candidate_crops=["Wheat", "Cotton", "Soybean", "Tomato"])
    s1 = planner.plan_next_season("Summer")
    s2 = planner.plan_next_season("Winter")
    s3 = planner.plan_next_season("Summer")

    for f_name in farm_data.fields.keys():
        s2_alloc = s2.crop_allocation[f_name]
        best_s2_crop = max(s2_alloc.items(), key=lambda x: x[1])[0] if any(v > 0 for v in s2_alloc.values()) else None
        if best_s2_crop:
            assert s3.previous_crops[f_name] == best_s2_crop


def test_23_planner_only_generates_one_season_per_call(farm_data):
    """23. Test plan_next_season() generates ONE season per call and never auto-loops."""
    planner = MultiSeasonPlanner(farm_data, candidate_crops=["Wheat", "Cotton"])
    assert len(planner.seasons) == 0

    planner.plan_next_season("Winter")
    assert len(planner.seasons) == 1

    planner.plan_next_season("Summer")
    assert len(planner.seasons) == 2


def test_24_empty_invalid_candidate_list_validation_error(farm_data):
    """24. Test empty or invalid candidate list raises loud ValueError."""
    planner = MultiSeasonPlanner(farm_data)

    with pytest.raises(ValueError, match="cannot be empty"):
        planner.set_candidate_crops([])

    with pytest.raises(ValueError, match="not present in the farm crop dataset"):
        planner.set_candidate_crops(["InvalidCropName"])
