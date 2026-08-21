"""Unit tests for FastAPI REST API endpoints."""

import pytest
from fastapi.testclient import TestClient
from crop_mix.app import app

client = TestClient(app)


def test_get_preset_farm():
    response = client.get("/api/preset")
    assert response.status_code == 200
    data = response.json()

    assert "water_budget" in data
    assert "labor_budget" in data
    assert "fertilizer_budget" in data
    assert len(data["crops"]) >= 3
    assert len(data["fields"]) >= 3


def test_optimize_v3_endpoint():
    preset_resp = client.get("/api/preset")
    preset_data = preset_resp.json()

    payload = {
        "version": "v3",
        "water_budget": preset_data["water_budget"],
        "labor_budget": preset_data["labor_budget"],
        "fertilizer_budget": preset_data["fertilizer_budget"],
        "crops": preset_data["crops"],
        "fields": preset_data["fields"],
    }

    response = client.post("/api/optimize", json=payload)
    assert response.status_code == 200
    res = response.json()

    assert res["is_feasible"] is True
    assert res["expected_profit"] > 0
    assert "field_allocations" in res
    assert "suitability_details" in res
    assert len(res["suitability_details"]) == len(preset_data["fields"]) * len(preset_data["crops"])
    assert "binding_constraints" in res


def test_optimize_v2_endpoint():
    preset_resp = client.get("/api/preset")
    preset_data = preset_resp.json()

    payload = {
        "version": "v2",
        "water_budget": preset_data["water_budget"],
        "labor_budget": preset_data["labor_budget"],
        "fertilizer_budget": preset_data["fertilizer_budget"],
        "crops": preset_data["crops"],
        "fields": preset_data["fields"],
    }

    response = client.post("/api/optimize", json=payload)
    assert response.status_code == 200
    res = response.json()

    assert res["is_feasible"] is True
    assert res["expected_profit"] > 0
    assert "total_labor_used" in res


def test_optimize_v1_endpoint():
    preset_resp = client.get("/api/preset")
    preset_data = preset_resp.json()

    payload = {
        "version": "v1",
        "water_budget": preset_data["water_budget"],
        "labor_budget": preset_data["labor_budget"],
        "fertilizer_budget": preset_data["fertilizer_budget"],
        "crops": preset_data["crops"],
        "fields": preset_data["fields"],
    }

    response = client.post("/api/optimize", json=payload)
    assert response.status_code == 200
    res = response.json()

    assert res["is_feasible"] is True
    assert res["expected_profit"] > 0


def test_optimize_v4_endpoint():
    preset_resp = client.get("/api/preset")
    preset_data = preset_resp.json()

    payload = {
        "version": "v4",
        "water_budget": preset_data["water_budget"],
        "labor_budget": preset_data["labor_budget"],
        "fertilizer_budget": preset_data["fertilizer_budget"],
        "crops": preset_data["crops"],
        "fields": preset_data["fields"],
    }

    response = client.post("/api/optimize", json=payload)
    assert response.status_code == 200
    res = response.json()

    assert res["is_feasible"] is True
    assert res["expected_profit"] > 0
    assert "field_allocations" in res
    assert "suitability_details" in res
    assert "rotation_details" in res
    assert "field_previous_crops" in res
    assert len(res["rotation_details"]) == len(preset_data["fields"]) * len(preset_data["crops"])
    assert "binding_constraints" in res


def test_rotation_matrix_endpoint():
    response = client.get("/api/rotation/matrix")
    assert response.status_code == 200
    data = response.json()

    assert "crops" in data
    assert "perennial_map" in data
    assert "family_map" in data
    assert "Wheat" in data["crops"]
    assert len(data["crops"]) >= 50


def test_optimize_validation_errors():
    # Empty crops
    payload = {
        "version": "v4",
        "water_budget": 100000,
        "crops": [],
        "fields": [{"name": "F1", "area": 10.0}],
    }
    response = client.post("/api/optimize", json=payload)
    assert response.status_code == 400
