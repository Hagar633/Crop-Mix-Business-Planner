"""Extended test suite for Multi-Season Crop Planning and Financial Projection."""

import pytest
from fastapi.testclient import TestClient
from crop_mix.data.example_data import get_example_farm_data
from crop_mix.models.optimizer_v4 import CropMixOptimizerV4
from crop_mix.business.multi_season_planner import MultiSeasonPlanner
from crop_mix.business.financial_projection import FinancialProjection
from crop_mix.app import app


@pytest.fixture
def farm_data():
    return get_example_farm_data()


@pytest.fixture
def client():
    return TestClient(app)


def test_v4_default_solve_applies_soil_suitability(farm_data):
    """1. Test V4 default solve applies soil suitability (apply_soil_suitability=True)."""
    optimizer = CropMixOptimizerV4()
    res_default = optimizer.solve(farm_data)
    res_explicit = optimizer.solve(farm_data, apply_soil_suitability=True)

    assert res_default.is_feasible is True
    assert res_default.crop_allocation == res_explicit.crop_allocation
    # Soil suitability matrix should contain zeros for unsuitable pairs (e.g., Soybean on Field_East pH 5.5)
    assert res_default.soil_suitability_matrix.get(("Field_East", "Soybean"), 1) == 0


def test_v4_solve_apply_soil_suitability_false(farm_data):
    """2. Test V4 solve with apply_soil_suitability=False returns all 1s matrix and omits soil constraint."""
    optimizer = CropMixOptimizerV4()
    res = optimizer.solve(farm_data, apply_soil_suitability=False)

    assert res.is_feasible is True
    # All field/crop entries in soil matrix should be 1
    for (f, c), val in res.soil_suitability_matrix.items():
        assert val == 1


def test_seed_season_1_does_not_optimize(farm_data):
    """3. Test seed_season_1() registers Season 1 history without calling optimizer."""
    planner = MultiSeasonPlanner(farm_data, candidate_crops=["Wheat", "Soybean", "Cotton", "Tomato"])
    s1_rec = {"Field_North": "Wheat", "Field_South": "Tomato", "Field_East": "Cotton"}

    planner.seed_season_1(previous_crops=s1_rec, season_name="Winter", water_budget=350000.0)

    assert len(planner.seasons) == 1
    assert planner.seasons[0].season_number == 1
    assert planner.current_previous_crops["Field_North"] == "Wheat"
    assert planner.current_previous_crops["Field_South"] == "Tomato"
    assert planner.current_previous_crops["Field_East"] == "Cotton"
    assert planner.current_water_budget == 350000.0


def test_first_next_season_call_after_seed_returns_season_2(farm_data):
    """4. Test first call to plan_next_season() after seed_season_1() produces Season 2."""
    planner = MultiSeasonPlanner(farm_data, candidate_crops=["Wheat", "Soybean", "Cotton", "Tomato"])
    s1_rec = {"Field_North": "Wheat", "Field_South": "Tomato", "Field_East": "Cotton"}
    planner.seed_season_1(previous_crops=s1_rec, season_name="Winter")

    s2 = planner.plan_next_season("Summer")

    assert s2.season_number == 2
    assert s2.is_current_season is False
    assert "لم يتم استخدام خصائص التربة للموسم المستقبلي" in s2.explanation_note
    assert s2.previous_crops["Field_North"] == "Wheat"


def test_season_2_crop_failing_soil_can_be_allocated(farm_data):
    """5. Test crop failing Season 1 soil suitability (Soybean on Field_East pH 5.5) can be allocated in Season 2."""
    # Modify Field_East previous crop to Barley so rotation allows Soybean
    farm_data.fields["Field_East"].previous_crop = "Barley"

    planner = MultiSeasonPlanner(farm_data, candidate_crops=["Soybean", "Wheat", "Cotton", "Tomato"])
    s1_rec = {"Field_North": "Wheat", "Field_South": "Cotton", "Field_East": "Barley"}
    planner.seed_season_1(previous_crops=s1_rec, season_name="Winter")

    # Season 2 (Future - apply_soil_suitability=False)
    s2 = planner.plan_next_season("Summer")

    assert s2.season_number == 2
    assert s2.is_current_season is False
    # Check allocation is feasible
    assert s2.crop_allocation is not None


def test_rotation_enforced_in_season_2(farm_data):
    """6. Test rotation rules remain strictly enforced in Season 2."""
    planner = MultiSeasonPlanner(farm_data, candidate_crops=["Wheat", "Yellow Corn", "Soybean"])
    # Seed Field_North previous_crop = Wheat (Wheat -> Wheat is disallowed 0)
    s1_rec = {"Field_North": "Wheat", "Field_South": "Soybean", "Field_East": "Yellow Corn"}
    planner.seed_season_1(previous_crops=s1_rec, season_name="Winter")

    s2 = planner.plan_next_season("Winter")

    # Wheat -> Wheat is 0 -> Field_North must receive 0 Wheat in Season 2
    assert s2.crop_allocation["Field_North"].get("Wheat", 0.0) == 0.0


def test_season_filtering_enforced_in_season_2(farm_data):
    """7. Test season compatibility remains strictly enforced in Season 2."""
    planner = MultiSeasonPlanner(farm_data, candidate_crops=["Wheat", "Cotton"])
    s1_rec = {"Field_North": "Wheat", "Field_South": "Soybean", "Field_East": "Cotton"}
    planner.seed_season_1(previous_crops=s1_rec, season_name="Summer")

    s2 = planner.plan_next_season("Winter")

    # Cotton is Summer-only -> must be excluded in Winter (Season 2)
    assert "Cotton" not in s2.season_allowed_crops


def test_season_1_recommendation_becomes_season_2_previous_crop(farm_data):
    """8. Test Season 1 recommendation becomes Season 2 previous_crop."""
    planner = MultiSeasonPlanner(farm_data, candidate_crops=["Wheat", "Cotton", "Soybean", "Tomato"])
    s1_rec = {"Field_North": "Tomato", "Field_South": "Cotton", "Field_East": "Soybean"}
    planner.seed_season_1(previous_crops=s1_rec, season_name="Winter")

    s2 = planner.plan_next_season("Summer")

    assert s2.previous_crops["Field_North"] == "Tomato"
    assert s2.previous_crops["Field_South"] == "Cotton"
    assert s2.previous_crops["Field_East"] == "Soybean"


def test_season_2_recommendation_becomes_season_3_previous_crop(farm_data):
    """9. Test Season 2 recommendation becomes Season 3 previous_crop."""
    planner = MultiSeasonPlanner(farm_data, candidate_crops=["Wheat", "Cotton", "Soybean", "Tomato"])
    s1_rec = {"Field_North": "Tomato", "Field_South": "Cotton", "Field_East": "Soybean"}
    planner.seed_season_1(previous_crops=s1_rec, season_name="Winter")

    s2 = planner.plan_next_season("Summer")
    s3 = planner.plan_next_season("Winter")

    for f_name in farm_data.fields.keys():
        s2_alloc = s2.crop_allocation[f_name]
        best_crop = max(s2_alloc.items(), key=lambda x: x[1])[0] if any(v > 0 for v in s2_alloc.values()) else None
        if best_crop:
            assert s3.previous_crops[f_name] == best_crop


def test_candidate_crops_persist(farm_data):
    """10. Test candidate crops pool persists across seasons."""
    planner = MultiSeasonPlanner(farm_data, candidate_crops=["Wheat", "Cotton"])
    s1_rec = {"Field_North": "Wheat", "Field_South": "Cotton", "Field_East": "Wheat"}
    planner.seed_season_1(previous_crops=s1_rec)

    s2 = planner.plan_next_season("Summer")
    assert s2.candidate_crops == ["Wheat", "Cotton"]

    s3 = planner.plan_next_season("Winter")
    assert s3.candidate_crops == ["Wheat", "Cotton"]


def test_budget_carry_forward_and_editing(farm_data):
    """11. Test initial budgets carry forward and user edits persist as defaults."""
    planner = MultiSeasonPlanner(farm_data, candidate_crops=["Wheat", "Cotton", "Soybean"])
    s1_rec = {"Field_North": "Wheat", "Field_South": "Cotton", "Field_East": "Soybean"}
    planner.seed_season_1(previous_crops=s1_rec, water_budget=400000.0)

    # Season 2 edited budget = 350000.0
    s2 = planner.plan_next_season("Summer", water_budget=350000.0)
    assert s2.water_budget == 350000.0

    # Season 3 un-edited -> should carry forward 350000.0
    s3 = planner.plan_next_season("Winter")
    assert s3.water_budget == 350000.0


def test_one_season_per_call(farm_data):
    """12. Test plan_next_season() generates exactly one season per call."""
    planner = MultiSeasonPlanner(farm_data, candidate_crops=["Wheat", "Cotton"])
    s1_rec = {"Field_North": "Wheat", "Field_South": "Cotton", "Field_East": "Wheat"}
    planner.seed_season_1(previous_crops=s1_rec)
    assert len(planner.seasons) == 1

    planner.plan_next_season("Summer")
    assert len(planner.seasons) == 2

    planner.plan_next_season("Winter")
    assert len(planner.seasons) == 3


def test_financial_projection_in_api_optimize(client):
    """13. Test /api/optimize returns financial_projection in V4 payload."""
    payload = {
        "version": "v4",
        "zone": "Delta",
        "season": "Winter",
        "water_budget": 400000,
        "labor_budget": 2500,
        "fertilizer_budget": 15000,
        "crops": [
            {
                "name": "Wheat",
                "expected_yield": 6.5,
                "price": 12000,
                "production_cost": 25000,
                "water_requirement": 4500,
                "labor_requirement": 20,
                "fertilizer_requirement": 150,
            }
        ],
        "fields": [
            {
                "name": "Field_1",
                "area": 10.0,
                "ph": 7.0,
                "ec": 1.0,
                "texture": "Loam",
                "organic_matter": 2.0,
                "previous_crop": "None",
            }
        ],
    }
    response = client.post("/api/optimize", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "financial_projection" in data
    assert "farm_summary" in data["financial_projection"]
    assert "field_projections" in data["financial_projection"]
    assert data["financial_projection"]["farm_summary"]["total_expected_revenue"] > 0


def test_multi_season_start_api_seeds_season_1(client):
    """14. Test /api/multi-season/start seeds Season 1 and returns next_season_number == 2."""
    payload = {
        "session_id": "test_session_1",
        "candidate_crops": ["Wheat", "Soybean", "Cotton"],
        "season_1_recommendation": {
            "Field_1": "Wheat",
            "Field_2": "Cotton",
        },
        "current_season_name": "Winter",
        "water_budget": 380000,
    }
    response = client.post("/api/multi-season/start", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["next_season_number"] == 2
    assert data["current_previous_crops"]["Field_1"] == "Wheat"
    assert data["current_previous_crops"]["Field_2"] == "Cotton"


def test_multi_season_start_without_allocations_still_starts_at_season_2(client):
    """A fallow current-season result must not make future planning restart at Season 1."""
    payload = {
        "session_id": "test_empty_current_recommendation",
        "candidate_crops": ["Wheat", "Cotton"],
        "season_1_recommendation": {},
        "current_season_name": "Winter",
    }
    response = client.post("/api/multi-season/start", json=payload)
    assert response.status_code == 200
    assert response.json()["next_season_number"] == 2
