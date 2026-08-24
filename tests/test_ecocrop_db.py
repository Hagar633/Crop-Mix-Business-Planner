"""Unit tests for FAO EcoCrop Database integration."""

import pytest
from fastapi.testclient import TestClient
from crop_mix.data.ecocrop_db import EcoCropDatabase, EcoCropEntry
from crop_mix.data.example_data import CropSoilRequirement, CropParameters, FieldParameters, FarmInputs
from crop_mix.models.soil_suitability import SoilSuitabilityEngine
from crop_mix.models.optimizer_v3 import CropMixOptimizerV3
from crop_mix.app import app


@pytest.fixture
def db():
    return EcoCropDatabase()


@pytest.fixture
def client():
    return TestClient(app)


def test_ecocrop_db_load_and_lookup(db):
    wheat = db.get_crop("Wheat")
    assert wheat is not None
    assert wheat.name == "Wheat"
    assert wheat.min_ph == 5.5
    assert wheat.max_ph == 8.5
    assert wheat.max_ec == 2.5
    assert "Loam" in wheat.suitable_textures

    # Case insensitivity test
    cotton = db.get_crop("cOTToN")
    assert cotton is not None
    assert cotton.name == "Cotton"


def test_ecocrop_db_search(db):
    cereals = db.search_crops(category="Cereal")
    assert len(cereals) >= 4
    names = [c.name for c in cereals]
    assert "Wheat" in names
    assert "Corn" in names
    assert "Rice" in names
    assert "Barley" in names

    search_res = db.search_crops(query="solanum")
    assert len(search_res) >= 2  # Tomatoes and Potato


def test_ecocrop_conversions(db):
    potato_entry = db.get_crop("Potato")
    assert potato_entry is not None

    soil_req = potato_entry.to_soil_requirement()
    assert isinstance(soil_req, CropSoilRequirement)
    assert soil_req.min_ph == 4.8
    assert soil_req.max_ph == 7.5
    assert soil_req.max_ec == 1.7

    crop_param = potato_entry.to_crop_parameters(price_override=250.0)
    assert isinstance(crop_param, CropParameters)
    assert crop_param.name == "Potato"
    assert crop_param.price == 250.0
    assert crop_param.water_requirement == 4500.0


def test_ecocrop_soil_suitability_integration(db):
    rice_entry = db.get_crop("Rice")
    rice_param = rice_entry.to_crop_parameters()

    # Clay field with pH 6.0 and low salinity -> suitable for rice
    clay_field = FieldParameters(name="Paddy_Field", area=10.0, ph=6.0, ec=1.0, texture="Clay", organic_matter=3.0)
    assert SoilSuitabilityEngine.is_suitable(clay_field, rice_param) is True

    # Sandy field -> unsuitable for rice
    sandy_field = FieldParameters(name="Sand_Dune", area=10.0, ph=6.0, ec=1.0, texture="Sandy", organic_matter=1.0)
    assert SoilSuitabilityEngine.is_suitable(sandy_field, rice_param) is False


def test_ecocrop_api_endpoints(client):
    # Test list endpoint
    response = client.get("/api/ecocrop/crops")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 10

    # Test lookup endpoint
    resp_wheat = client.get("/api/ecocrop/lookup/Wheat")
    assert resp_wheat.status_code == 200
    wheat_data = resp_wheat.json()
    assert wheat_data["name"] == "Wheat"
    assert wheat_data["min_ph"] == 5.5
    assert wheat_data["water_requirement"] == 3500.0

    # Test 404 for unknown crop
    resp_unknown = client.get("/api/ecocrop/lookup/NonExistentCrop123")
    assert resp_unknown.status_code == 404


def test_optimizer_v3_with_ecocrop_data(db):
    # Build FarmInputs using EcoCrop species
    wheat = db.get_crop("Wheat").to_crop_parameters()
    barley = db.get_crop("Barley").to_crop_parameters()
    rice = db.get_crop("Rice").to_crop_parameters()

    crops = {"Wheat": wheat, "Barley": barley, "Rice": rice}

    fields = {
        "Field_1": FieldParameters(name="Field_1", area=30.0, ph=6.5, ec=1.0, texture="Loam", organic_matter=2.0),
        "Field_2": FieldParameters(name="Field_2", area=20.0, ph=5.5, ec=2.8, texture="Clay", organic_matter=2.5),
    }

    farm_inputs = FarmInputs(
        field_area=50.0,
        water_budget=200000.0,
        labor_budget=2000.0,
        fertilizer_budget=10000.0,
        crops=crops,
        fields=fields,
    )

    optimizer = CropMixOptimizerV3()
    result = optimizer.solve(farm_inputs)

    assert result.is_feasible is True
    assert result.total_land_used > 0
    assert result.expected_profit > 0
