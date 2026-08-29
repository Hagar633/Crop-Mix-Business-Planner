"""Unit tests for LLM Explanation Service."""

import os
import pytest
from crop_mix.services.llm_explainer import CropMixLLMExplainer


@pytest.fixture
def mock_opt_result():
    return {
        "version": "V4 (Soil Suitability + Crop Rotation)",
        "status": "optimal",
        "is_feasible": True,
        "expected_profit": 350000.0,
        "total_expected_revenue": 500000.0,
        "total_production_cost": 100000.0,
        "total_labor_cost": 30000.0,
        "total_fertilizer_cost": 20000.0,
        "total_land_used": 50.0,
        "field_area_limit": 50.0,
        "total_water_used": 200000.0,
        "water_budget_limit": 200000.0,
        "crop_allocation_summary": {"Wheat": 30.0, "Soybean": 20.0},
        "field_allocations": {
            "Field_North": {"Wheat": 30.0, "Soybean": 0.0},
            "Field_South": {"Wheat": 0.0, "Soybean": 20.0},
        },
        "binding_constraints": [
            {"resource": "Water Budget", "used": 200000.0, "limit": 200000.0, "utilization_pct": 100.0, "is_binding": True},
            {"resource": "Land Area", "used": 50.0, "limit": 50.0, "utilization_pct": 100.0, "is_binding": True},
        ]
    }


def test_explainer_agronomic_fallback(mock_opt_result):
    """Test explainer generates valid fallback markdown explanation when no API key is provided."""
    explainer = CropMixLLMExplainer(api_key="invalid_dummy_key_for_test")
    res_ar = explainer.generate_explanation(mock_opt_result, lang="ar")
    
    assert res_ar is not None
    assert "explanation_markdown" in res_ar
    assert len(res_ar["explanation_markdown"]) > 50
    assert "provider" in res_ar

    res_en = explainer.generate_explanation(mock_opt_result, lang="en")
    assert "explanation_markdown" in res_en
    assert len(res_en["explanation_markdown"]) > 50


def test_explainer_prompt_builder(mock_opt_result):
    """Test prompt builder produces structured prompt with farm metrics."""
    explainer = CropMixLLMExplainer()
    prompt_ar = explainer._build_prompt(mock_opt_result, lang="ar")
    assert "350,000" in prompt_ar or "350000" in prompt_ar
    assert "Field_North" in prompt_ar
    assert "قمح" in prompt_ar


    prompt_en = explainer._build_prompt(mock_opt_result, lang="en")
    assert "Field_South" in prompt_en
    assert "Soybean" in prompt_en
