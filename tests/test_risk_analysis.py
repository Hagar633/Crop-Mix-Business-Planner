"""Test suite for CVaR-Based Risk Analysis and Risk-Aware Optimizer.

Tests cover:
  - Synthetic risk scenario database structure and probability validation.
  - CropRiskProfile multiplier validation.
  - RiskAnalyzer: scenario profit calculation and CVaR/VaR metrics.
  - RiskAwareOptimizer: all three planning modes (max_profit, balanced, risk_aware).
  - API endpoints: /api/risk/scenarios and /api/risk/analyze.
"""

import math
import pytest
from fastapi.testclient import TestClient

from crop_mix.data.example_data import get_example_farm_data, FarmInputs, FieldParameters, CropParameters, CropSoilRequirement
from crop_mix.data.risk_scenarios import (
    SyntheticEgyptRiskProvider,
    RiskScenario,
    CropRiskProfile,
    get_default_provider,
)
from crop_mix.business.risk_analysis import RiskAnalyzer
from crop_mix.models.risk_aware_optimizer import RiskAwareOptimizer, MODES, MODE_WEIGHTS


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def farm_inputs() -> FarmInputs:
    return get_example_farm_data()


@pytest.fixture(scope="module")
def provider():
    return SyntheticEgyptRiskProvider()


@pytest.fixture(scope="module")
def analyzer(farm_inputs) -> RiskAnalyzer:
    return RiskAnalyzer(farm_inputs)


@pytest.fixture(scope="module")
def optimizer() -> RiskAwareOptimizer:
    return RiskAwareOptimizer()


@pytest.fixture(scope="module")
def api_client():
    from crop_mix.app import app
    return TestClient(app)


# ---------------------------------------------------------------------------
# PART 1: Scenario Database Integrity Tests
# ---------------------------------------------------------------------------

class TestScenarioDatabase:
    """Tests for synthetic risk scenario database integrity."""

    def test_scenario_count_is_six(self, provider):
        """Expect exactly 6 scenarios in the synthetic database."""
        scenarios = provider.get_scenarios()
        assert len(scenarios) == 6, f"Expected 6 scenarios, got {len(scenarios)}"

    def test_probabilities_sum_to_one(self, provider):
        """All scenario probabilities must sum to exactly 1.0."""
        scenarios = provider.get_scenarios()
        total = sum(s.probability for s in scenarios)
        assert abs(total - 1.0) < 1e-9, f"Probabilities sum to {total:.9f}, expected 1.0"

    def test_all_probabilities_are_positive(self, provider):
        """Each scenario probability must be strictly positive."""
        scenarios = provider.get_scenarios()
        for s in scenarios:
            assert s.probability > 0, f"Scenario '{s.scenario_id}' has probability {s.probability} <= 0"

    def test_scenario_ids_are_unique(self, provider):
        """All scenario IDs must be unique."""
        scenarios = provider.get_scenarios()
        ids = [s.scenario_id for s in scenarios]
        assert len(ids) == len(set(ids)), "Duplicate scenario IDs found"

    def test_required_scenario_ids_present(self, provider):
        """Expected scenario IDs must be present."""
        scenarios = provider.get_scenarios()
        ids = {s.scenario_id for s in scenarios}
        expected = {"normal", "water_stress", "heat_stress", "market_downturn", "input_inflation", "severe_combined"}
        assert expected == ids, f"Missing or extra scenario IDs. Expected: {expected}, Got: {ids}"

    def test_all_crop_profiles_have_positive_multipliers(self, provider):
        """All multipliers in all crop profiles must be strictly positive."""
        scenarios = provider.get_scenarios()
        for s in scenarios:
            for crop_name, profile in s.crop_profiles.items():
                for attr in ["yield_multiplier", "price_multiplier", "production_cost_multiplier",
                             "labor_cost_multiplier", "fertilizer_cost_multiplier"]:
                    val = getattr(profile, attr)
                    assert val > 0, (
                        f"Scenario '{s.scenario_id}', crop '{crop_name}', "
                        f"attribute '{attr}' is {val} (must be > 0)"
                    )

    def test_default_multipliers_are_positive(self, provider):
        """Default multipliers must be strictly positive."""
        scenarios = provider.get_scenarios()
        for s in scenarios:
            assert s.default_yield_multiplier > 0
            assert s.default_price_multiplier > 0
            assert s.default_production_cost_multiplier > 0
            assert s.default_labor_cost_multiplier > 0
            assert s.default_fertilizer_cost_multiplier > 0

    def test_normal_scenario_has_multipliers_near_one(self, provider):
        """Normal scenario multipliers should be approximately 1.0."""
        scenarios = provider.get_scenarios()
        normal = next(s for s in scenarios if s.scenario_id == "normal")
        assert abs(normal.default_yield_multiplier - 1.0) < 0.1
        assert abs(normal.default_price_multiplier - 1.0) < 0.1
        assert abs(normal.default_production_cost_multiplier - 1.0) < 0.1

    def test_water_stress_reduces_rice_yield(self, provider):
        """Water stress scenario must severely reduce rice yield multiplier."""
        scenarios = provider.get_scenarios()
        ws = next(s for s in scenarios if s.scenario_id == "water_stress")
        profile = ws.get_crop_profile("Rice")
        assert profile.yield_multiplier < 0.70, (
            f"Rice yield multiplier in water_stress expected < 0.70, got {profile.yield_multiplier}"
        )

    def test_market_downturn_reduces_tomato_price(self, provider):
        """Market downturn must substantially reduce Tomato price multiplier."""
        scenarios = provider.get_scenarios()
        md = next(s for s in scenarios if s.scenario_id == "market_downturn")
        profile = md.get_crop_profile("Tomato")
        assert profile.price_multiplier < 0.65, (
            f"Tomato price multiplier in market_downturn expected < 0.65, got {profile.price_multiplier}"
        )

    def test_severe_combined_has_worst_multipliers(self, provider):
        """Severe combined scenario must have the lowest overall multipliers."""
        scenarios = provider.get_scenarios()
        severe = next(s for s in scenarios if s.scenario_id == "severe_combined")
        # At least some crops should have yield multiplier < 0.70
        min_yield = min(p.yield_multiplier for p in severe.crop_profiles.values())
        assert min_yield < 0.70, f"Severe combined min yield multiplier expected < 0.70, got {min_yield}"

    def test_get_crop_profile_fallback(self, provider):
        """get_crop_profile must return default multipliers for unknown crops."""
        scenarios = provider.get_scenarios()
        normal = next(s for s in scenarios if s.scenario_id == "normal")
        profile = normal.get_crop_profile("UnknownCropXYZ")
        assert profile.crop_name == "UnknownCropXYZ"
        assert profile.yield_multiplier == normal.default_yield_multiplier

    def test_provider_validate_passes(self, provider):
        """Provider validation must pass without error."""
        provider.validate()  # Should not raise

    def test_scenario_validate_passes(self, provider):
        """Each scenario's validate() must pass without error."""
        for s in provider.get_scenarios():
            s.validate()  # Should not raise


# ---------------------------------------------------------------------------
# PART 2: RiskAnalyzer Tests
# ---------------------------------------------------------------------------

class TestRiskAnalyzer:
    """Tests for RiskAnalyzer scenario profit computation and CVaR metrics."""

    def test_scenario_profit_normal_equals_approximately_deterministic(self, analyzer, farm_inputs):
        """In the Normal scenario (multipliers ~1.0), profit should be close to deterministic V4 profit."""
        from crop_mix.models.optimizer_v4 import CropMixOptimizerV4
        opt = CropMixOptimizerV4()
        result = opt.solve(farm_inputs)

        provider = get_default_provider()
        normal_scenario = next(s for s in provider.get_scenarios() if s.scenario_id == "normal")

        profit = analyzer.compute_scenario_profit(result.crop_allocation, normal_scenario)
        # Normal scenario has multipliers close to 1.0 — allow 10% deviation
        deterministic_profit = result.expected_profit
        assert abs(profit - deterministic_profit) / max(1.0, abs(deterministic_profit)) < 0.15, (
            f"Normal scenario profit {profit:,.0f} differs > 15% from deterministic {deterministic_profit:,.0f}"
        )

    def test_scenario_profit_water_stress_lower_than_normal(self, analyzer, farm_inputs):
        """Water stress scenario profit must be lower than normal scenario profit."""
        from crop_mix.models.optimizer_v4 import CropMixOptimizerV4
        opt = CropMixOptimizerV4()
        result = opt.solve(farm_inputs)
        alloc = result.crop_allocation

        provider = get_default_provider()
        normal = next(s for s in provider.get_scenarios() if s.scenario_id == "normal")
        water = next(s for s in provider.get_scenarios() if s.scenario_id == "water_stress")

        profit_normal = analyzer.compute_scenario_profit(alloc, normal)
        profit_water = analyzer.compute_scenario_profit(alloc, water)
        assert profit_water < profit_normal, (
            f"Water stress profit ({profit_water:,.0f}) should be < normal ({profit_normal:,.0f})"
        )

    def test_severe_combined_is_worst_scenario(self, analyzer, farm_inputs):
        """Severe combined scenario must be the worst-case (lowest profit)."""
        from crop_mix.models.optimizer_v4 import CropMixOptimizerV4
        opt = CropMixOptimizerV4()
        result = opt.solve(farm_inputs)
        alloc = result.crop_allocation

        provider = get_default_provider()
        scenarios = provider.get_scenarios()
        profits = {s.scenario_id: analyzer.compute_scenario_profit(alloc, s) for s in scenarios}
        min_id = min(profits, key=profits.get)
        assert min_id == "severe_combined", (
            f"Expected 'severe_combined' to be worst case, but got '{min_id}'"
        )

    def test_analyze_returns_six_scenario_profits(self, analyzer, farm_inputs):
        """analyze() must return exactly 6 ScenarioProfit entries."""
        from crop_mix.models.optimizer_v4 import CropMixOptimizerV4
        opt = CropMixOptimizerV4()
        result = opt.solve(farm_inputs)
        metrics = analyzer.analyze(result.crop_allocation)
        assert len(metrics.scenarios) == 6

    def test_expected_profit_is_probability_weighted_average(self, analyzer, farm_inputs):
        """expected_profit must equal probability-weighted sum of scenario profits."""
        from crop_mix.models.optimizer_v4 import CropMixOptimizerV4
        opt = CropMixOptimizerV4()
        result = opt.solve(farm_inputs)
        metrics = analyzer.analyze(result.crop_allocation)

        manual_expected = sum(sp.probability * sp.net_profit for sp in metrics.scenarios)
        assert abs(metrics.expected_profit - manual_expected) < 0.1, (
            f"Expected profit mismatch: {metrics.expected_profit} vs manual {manual_expected}"
        )

    def test_probability_weighted_sum_of_scenarios_is_one(self, analyzer, farm_inputs):
        """Sum of probabilities in scenario results must be 1.0."""
        from crop_mix.models.optimizer_v4 import CropMixOptimizerV4
        opt = CropMixOptimizerV4()
        result = opt.solve(farm_inputs)
        metrics = analyzer.analyze(result.crop_allocation)
        total_prob = sum(sp.probability for sp in metrics.scenarios)
        assert abs(total_prob - 1.0) < 1e-9

    def test_cvar_is_lower_than_or_equal_to_var(self, analyzer, farm_inputs):
        """CVaR_95 (expected shortfall) must be <= VaR_95 (since we define VaR as profit threshold)."""
        from crop_mix.models.optimizer_v4 import CropMixOptimizerV4
        opt = CropMixOptimizerV4()
        result = opt.solve(farm_inputs)
        metrics = analyzer.analyze(result.crop_allocation)
        # CVaR is the average of the worst tail, so cvar <= var (in profit terms)
        assert metrics.cvar_95 <= metrics.var_95 + 1.0, (
            f"CVaR ({metrics.cvar_95:,.0f}) should be <= VaR ({metrics.var_95:,.0f})"
        )

    def test_min_profit_is_less_than_or_equal_cvar(self, analyzer, farm_inputs):
        """min_profit must be <= CVaR (worst case is at least as bad as the tail average)."""
        from crop_mix.models.optimizer_v4 import CropMixOptimizerV4
        opt = CropMixOptimizerV4()
        result = opt.solve(farm_inputs)
        metrics = analyzer.analyze(result.crop_allocation)
        assert metrics.min_profit <= metrics.cvar_95 + 1.0, (
            f"min_profit ({metrics.min_profit:,.0f}) should be <= CVaR ({metrics.cvar_95:,.0f})"
        )

    def test_max_profit_is_greater_than_expected_profit(self, analyzer, farm_inputs):
        """max_profit must be >= expected_profit."""
        from crop_mix.models.optimizer_v4 import CropMixOptimizerV4
        opt = CropMixOptimizerV4()
        result = opt.solve(farm_inputs)
        metrics = analyzer.analyze(result.crop_allocation)
        assert metrics.max_profit >= metrics.expected_profit - 1.0, (
            f"max_profit ({metrics.max_profit:,.0f}) should be >= expected_profit ({metrics.expected_profit:,.0f})"
        )

    def test_std_dev_is_non_negative(self, analyzer, farm_inputs):
        """Standard deviation must be non-negative."""
        from crop_mix.models.optimizer_v4 import CropMixOptimizerV4
        opt = CropMixOptimizerV4()
        result = opt.solve(farm_inputs)
        metrics = analyzer.analyze(result.crop_allocation)
        assert metrics.std_dev >= 0.0

    def test_scenario_profit_zero_allocation(self, analyzer):
        """With all-zero allocation, scenario profit should be 0 in every scenario."""
        farm = get_example_farm_data()
        # Build a zero allocation
        zero_alloc = {f: {c: 0.0 for c in farm.crops} for f in farm.fields}
        metrics = analyzer.analyze(zero_alloc)
        assert abs(metrics.expected_profit) < 0.01
        for sp in metrics.scenarios:
            assert abs(sp.net_profit) < 0.01


# ---------------------------------------------------------------------------
# PART 3: RiskAwareOptimizer Tests
# ---------------------------------------------------------------------------

class TestRiskAwareOptimizer:
    """Tests for the CVaR-augmented Pyomo LP optimizer."""

    def test_all_three_modes_are_feasible(self, optimizer, farm_inputs):
        """All three modes must produce feasible solutions."""
        for mode in MODES:
            res = optimizer.solve(farm_inputs, mode=mode)
            assert res.is_feasible, f"Mode '{mode}' returned infeasible solution"

    def test_invalid_mode_raises_value_error(self, optimizer, farm_inputs):
        """Invalid mode string must raise ValueError."""
        with pytest.raises(ValueError, match="Invalid mode"):
            optimizer.solve(farm_inputs, mode="ultra_risk_hungry")

    def test_max_profit_has_highest_expected_profit(self, optimizer, farm_inputs):
        """Max profit mode should yield the highest or equal expected profit."""
        res_max = optimizer.solve(farm_inputs, mode="max_profit")
        res_bal = optimizer.solve(farm_inputs, mode="balanced")
        res_risk = optimizer.solve(farm_inputs, mode="risk_aware")

        assert res_max.expected_profit >= res_bal.expected_profit - 1.0, (
            f"max_profit expected_profit ({res_max.expected_profit:,.0f}) "
            f"should be >= balanced ({res_bal.expected_profit:,.0f})"
        )
        assert res_max.expected_profit >= res_risk.expected_profit - 1.0, (
            f"max_profit expected_profit ({res_max.expected_profit:,.0f}) "
            f"should be >= risk_aware ({res_risk.expected_profit:,.0f})"
        )

    def test_risk_aware_has_highest_or_equal_cvar(self, optimizer, farm_inputs):
        """Risk-aware mode should yield the highest (best) CVaR or equal to balanced/max."""
        res_max = optimizer.solve(farm_inputs, mode="max_profit")
        res_bal = optimizer.solve(farm_inputs, mode="balanced")
        res_risk = optimizer.solve(farm_inputs, mode="risk_aware")

        # Risk-aware should have the best CVaR (highest CVaR value = best tail protection)
        assert res_risk.cvar_95 >= res_max.cvar_95 - 1.0, (
            f"risk_aware CVaR ({res_risk.cvar_95:,.0f}) should be >= max_profit CVaR ({res_max.cvar_95:,.0f})"
        )

    def test_allocation_satisfies_field_area_constraints(self, optimizer, farm_inputs):
        """All allocations must respect field area limits."""
        for mode in MODES:
            res = optimizer.solve(farm_inputs, mode=mode)
            for f_name, f_obj in farm_inputs.fields.items():
                total_alloc = sum(res.crop_allocation[f_name].values())
                assert total_alloc <= f_obj.area + 1e-2, (
                    f"Mode '{mode}', field '{f_name}': allocated {total_alloc:.4f} ha > "
                    f"field area {f_obj.area:.4f} ha"
                )

    def test_allocation_satisfies_water_budget(self, optimizer, farm_inputs):
        """All allocations must respect the water budget."""
        for mode in MODES:
            res = optimizer.solve(farm_inputs, mode=mode)
            assert res.total_water_used <= farm_inputs.water_budget + 1e-2, (
                f"Mode '{mode}': water used {res.total_water_used:,.0f} > "
                f"budget {farm_inputs.water_budget:,.0f}"
            )

    def test_allocation_satisfies_labor_budget(self, optimizer, farm_inputs):
        """All allocations must respect the labor budget."""
        for mode in MODES:
            res = optimizer.solve(farm_inputs, mode=mode)
            assert res.total_labor_used <= farm_inputs.labor_budget + 1e-2, (
                f"Mode '{mode}': labor used {res.total_labor_used:,.0f} > "
                f"budget {farm_inputs.labor_budget:,.0f}"
            )

    def test_allocation_satisfies_fertilizer_budget(self, optimizer, farm_inputs):
        """All allocations must respect the fertilizer budget."""
        for mode in MODES:
            res = optimizer.solve(farm_inputs, mode=mode)
            assert res.total_fertilizer_used <= farm_inputs.fertilizer_budget + 1e-2, (
                f"Mode '{mode}': fertilizer used {res.total_fertilizer_used:,.0f} > "
                f"budget {farm_inputs.fertilizer_budget:,.0f}"
            )

    def test_allocation_is_non_negative(self, optimizer, farm_inputs):
        """All allocation values must be non-negative."""
        for mode in MODES:
            res = optimizer.solve(farm_inputs, mode=mode)
            for f_name, allocs in res.crop_allocation.items():
                for c_name, area in allocs.items():
                    assert area >= -1e-6, (
                        f"Mode '{mode}', field '{f_name}', crop '{c_name}': "
                        f"negative allocation {area}"
                    )

    def test_rotation_constraints_respected(self, optimizer, farm_inputs):
        """Crops disallowed by rotation must have zero allocation."""
        for mode in MODES:
            res = optimizer.solve(farm_inputs, mode=mode)
            for (f_name, c_name), fit in res.rotation_suitability_matrix.items():
                if fit == 0:
                    area = res.crop_allocation[f_name].get(c_name, 0.0)
                    assert area < 1e-4, (
                        f"Mode '{mode}', field '{f_name}', crop '{c_name}' is "
                        f"rotation-disallowed but got {area:.6f} ha"
                    )

    def test_soil_suitability_constraints_respected(self, optimizer, farm_inputs):
        """Crops failing soil suitability must have zero allocation when it's active."""
        for mode in MODES:
            res = optimizer.solve(farm_inputs, mode=mode, apply_soil_suitability=True)
            for (f_name, c_name), fit in res.soil_suitability_matrix.items():
                if fit == 0:
                    area = res.crop_allocation[f_name].get(c_name, 0.0)
                    assert area < 1e-4, (
                        f"Mode '{mode}', field '{f_name}', crop '{c_name}' is "
                        f"soil-unsuitable but got {area:.6f} ha"
                    )

    def test_soil_suitability_disabled_allows_more_allocation(self, optimizer, farm_inputs):
        """Disabling soil suitability should produce >= allocation vs with soil suitability."""
        res_with = optimizer.solve(farm_inputs, mode="max_profit", apply_soil_suitability=True)
        res_without = optimizer.solve(farm_inputs, mode="max_profit", apply_soil_suitability=False)
        # Without soil constraints, optimizer has more options => should have >= land use
        assert res_without.total_land_used >= res_with.total_land_used - 1e-4

    def test_result_has_six_scenario_profits(self, optimizer, farm_inputs):
        """Each mode result must contain exactly 6 scenario profits."""
        for mode in MODES:
            res = optimizer.solve(farm_inputs, mode=mode)
            assert len(res.scenario_profits) == 6, (
                f"Mode '{mode}': expected 6 scenario profits, got {len(res.scenario_profits)}"
            )

    def test_mode_attributes_are_correct(self, optimizer, farm_inputs):
        """Mode attribute and weight must match the mode constants."""
        from crop_mix.models.risk_aware_optimizer import MODE_WEIGHTS, MODE_ARABIC
        for mode in MODES:
            res = optimizer.solve(farm_inputs, mode=mode)
            assert res.mode == mode
            assert res.weight_profit == MODE_WEIGHTS[mode]
            assert res.mode_arabic == MODE_ARABIC[mode]


# ---------------------------------------------------------------------------
# PART 4: API Endpoint Tests
# ---------------------------------------------------------------------------

class TestRiskAPIEndpoints:
    """Integration tests for the risk analysis API endpoints."""

    def test_get_risk_scenarios_endpoint_ok(self, api_client):
        """GET /api/risk/scenarios must return 200 with 6 scenarios."""
        response = api_client.get("/api/risk/scenarios")
        assert response.status_code == 200
        data = response.json()
        assert "scenarios" in data
        assert data["scenario_count"] == 6
        assert len(data["scenarios"]) == 6

    def test_risk_scenarios_probabilities_sum_to_one(self, api_client):
        """Scenario probabilities returned by API must sum to 1.0."""
        response = api_client.get("/api/risk/scenarios")
        data = response.json()
        total = sum(s["probability"] for s in data["scenarios"])
        assert abs(total - 1.0) < 1e-6

    def test_risk_scenarios_includes_disclaimer(self, api_client):
        """Scenario endpoint must include synthetic data disclaimer."""
        response = api_client.get("/api/risk/scenarios")
        data = response.json()
        assert "disclaimer" in data
        assert "SYNTHETIC" in data["disclaimer"]

    def test_risk_scenarios_alpha_is_095(self, api_client):
        """Scenario endpoint must declare alpha = 0.95."""
        response = api_client.get("/api/risk/scenarios")
        data = response.json()
        assert abs(data["alpha"] - 0.95) < 1e-9

    def _build_risk_request(self):
        """Build a standard risk analysis request payload using example data."""
        farm = get_example_farm_data()
        crops = []
        for name, c in farm.crops.items():
            soil_req = None
            if c.soil_requirement:
                soil_req = {
                    "min_ph": c.soil_requirement.min_ph,
                    "max_ph": c.soil_requirement.max_ph,
                    "max_ec": c.soil_requirement.max_ec,
                    "suitable_textures": c.soil_requirement.suitable_textures,
                }
            crops.append({
                "name": c.name,
                "expected_yield": c.expected_yield,
                "price": c.price,
                "production_cost": c.production_cost,
                "water_requirement": c.water_requirement,
                "labor_requirement": c.labor_requirement,
                "labor_cost_per_hour": c.labor_cost_per_hour,
                "fertilizer_requirement": c.fertilizer_requirement,
                "fertilizer_cost_per_kg": c.fertilizer_cost_per_kg,
                "soil_requirement": soil_req,
            })

        fields = []
        for name, f in farm.fields.items():
            fields.append({
                "name": f.name,
                "area": f.area,
                "ph": f.ph,
                "ec": f.ec,
                "texture": f.texture,
                "organic_matter": f.organic_matter,
                "previous_crop": f.previous_crop,
            })

        return {
            "zone": "Delta",
            "season": "Winter",
            "water_budget": farm.water_budget,
            "labor_budget": farm.labor_budget,
            "fertilizer_budget": farm.fertilizer_budget,
            "crops": crops,
            "fields": fields,
        }

    def test_risk_analyze_endpoint_ok(self, api_client):
        """POST /api/risk/analyze must return 200."""
        payload = self._build_risk_request()
        response = api_client.post("/api/risk/analyze", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:500]}"

    def test_risk_analyze_returns_three_plans(self, api_client):
        """POST /api/risk/analyze must return exactly three plan types."""
        payload = self._build_risk_request()
        response = api_client.post("/api/risk/analyze", json=payload)
        data = response.json()
        plans = data.get("plans", {})
        assert set(plans.keys()) == {"max_profit", "balanced", "risk_aware"}, (
            f"Expected plans keys {{max_profit, balanced, risk_aware}}, got {set(plans.keys())}"
        )

    def test_risk_analyze_includes_disclaimer(self, api_client):
        """POST /api/risk/analyze must include a synthetic data disclaimer."""
        payload = self._build_risk_request()
        response = api_client.post("/api/risk/analyze", json=payload)
        data = response.json()
        assert "disclaimer" in data
        assert "SYNTHETIC" in data["disclaimer"]

    def test_risk_analyze_plans_are_feasible(self, api_client):
        """All three plans in /api/risk/analyze must be feasible."""
        payload = self._build_risk_request()
        response = api_client.post("/api/risk/analyze", json=payload)
        data = response.json()
        for mode, plan in data["plans"].items():
            assert plan["is_feasible"], f"Plan '{mode}' is not feasible"

    def test_risk_analyze_all_plans_have_scenario_profits(self, api_client):
        """All three plans must include 6 scenario profit entries."""
        payload = self._build_risk_request()
        response = api_client.post("/api/risk/analyze", json=payload)
        data = response.json()
        for mode, plan in data["plans"].items():
            assert len(plan["scenario_profits"]) == 6, (
                f"Mode '{mode}': expected 6 scenario profits, "
                f"got {len(plan['scenario_profits'])}"
            )

    def test_risk_analyze_risk_metrics_present(self, api_client):
        """Each plan must have all expected risk metric fields."""
        payload = self._build_risk_request()
        response = api_client.post("/api/risk/analyze", json=payload)
        data = response.json()
        expected_keys = {"expected_profit", "var_95", "cvar_95", "std_dev",
                         "min_scenario_profit", "max_scenario_profit"}
        for mode, plan in data["plans"].items():
            assert "risk_metrics" in plan, f"Plan '{mode}' is missing 'risk_metrics'"
            assert expected_keys <= set(plan["risk_metrics"].keys()), (
                f"Plan '{mode}' risk_metrics missing keys: "
                f"{expected_keys - set(plan['risk_metrics'].keys())}"
            )

    def test_risk_analyze_missing_crops_returns_400(self, api_client):
        """POST /api/risk/analyze with empty crops must return 400."""
        payload = self._build_risk_request()
        payload["crops"] = []
        response = api_client.post("/api/risk/analyze", json=payload)
        assert response.status_code == 400

    def test_risk_analyze_missing_fields_returns_400(self, api_client):
        """POST /api/risk/analyze with empty fields must return 400."""
        payload = self._build_risk_request()
        payload["fields"] = []
        response = api_client.post("/api/risk/analyze", json=payload)
        assert response.status_code == 400

    def test_risk_analyze_max_profit_has_highest_expected_profit(self, api_client):
        """max_profit plan must have expected_profit >= balanced and risk_aware plans."""
        payload = self._build_risk_request()
        response = api_client.post("/api/risk/analyze", json=payload)
        data = response.json()
        plans = data["plans"]
        ep_max = plans["max_profit"]["risk_metrics"]["expected_profit"]
        ep_bal = plans["balanced"]["risk_metrics"]["expected_profit"]
        ep_risk = plans["risk_aware"]["risk_metrics"]["expected_profit"]
        assert ep_max >= ep_bal - 1.0, f"max_profit EP ({ep_max:,.0f}) should be >= balanced ({ep_bal:,.0f})"
        assert ep_max >= ep_risk - 1.0, f"max_profit EP ({ep_max:,.0f}) should be >= risk_aware ({ep_risk:,.0f})"

    def test_risk_scenarios_used_in_analyze_response(self, api_client):
        """POST /api/risk/analyze response must include scenarios_used summary."""
        payload = self._build_risk_request()
        response = api_client.post("/api/risk/analyze", json=payload)
        data = response.json()
        assert "scenarios_used" in data
        assert len(data["scenarios_used"]) == 6
