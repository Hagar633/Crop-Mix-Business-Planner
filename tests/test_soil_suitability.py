"""Unit tests for Soil Suitability Engine (V3)."""

import pytest
from crop_mix.data.example_data import CropParameters, CropSoilRequirement, FieldParameters
from crop_mix.models.soil_suitability import SoilSuitabilityEngine


@pytest.fixture
def sample_crop():
    """Sample crop requiring pH 6.0-7.5, max EC 2.0, textures ['Loam', 'Clay']."""
    return CropParameters(
        name="TestCrop",
        expected_yield=5.0,
        price=100.0,
        production_cost=200.0,
        water_requirement=1000.0,
        soil_requirement=CropSoilRequirement(
            min_ph=6.0,
            max_ph=7.5,
            max_ec=2.0,
            suitable_textures=["Loam", "Clay"],
        ),
    )


def test_suitable_field(sample_crop):
    """Verify that a field meeting all pH, EC, and texture criteria is suitable."""
    field_obj = FieldParameters(
        name="PerfectField",
        area=10.0,
        ph=6.8,  # Within 6.0 - 7.5
        ec=1.2,  # <= 2.0
        texture="Loam",  # In ['Loam', 'Clay']
        organic_matter=2.0,
    )
    assert SoilSuitabilityEngine.is_suitable(field_obj, sample_crop) is True


def test_ph_below_minimum(sample_crop):
    """Verify field with pH below minimum is marked unsuitable."""
    field_obj = FieldParameters(
        name="AcidicField",
        area=10.0,
        ph=5.5,  # < 6.0
        ec=1.0,
        texture="Loam",
        organic_matter=2.0,
    )
    assert SoilSuitabilityEngine.is_suitable(field_obj, sample_crop) is False


def test_ph_above_maximum(sample_crop):
    """Verify field with pH above maximum is marked unsuitable."""
    field_obj = FieldParameters(
        name="AlkalineField",
        area=10.0,
        ph=8.2,  # > 7.5
        ec=1.0,
        texture="Loam",
        organic_matter=2.0,
    )
    assert SoilSuitabilityEngine.is_suitable(field_obj, sample_crop) is False


def test_ec_too_high(sample_crop):
    """Verify field with electrical conductivity exceeding maximum is marked unsuitable."""
    field_obj = FieldParameters(
        name="SalineField",
        area=10.0,
        ph=6.8,
        ec=3.5,  # > 2.0
        texture="Loam",
        organic_matter=2.0,
    )
    assert SoilSuitabilityEngine.is_suitable(field_obj, sample_crop) is False


def test_unsuitable_texture(sample_crop):
    """Verify field with unlisted soil texture is marked unsuitable."""
    field_obj = FieldParameters(
        name="SandyField",
        area=10.0,
        ph=6.8,
        ec=1.0,
        texture="Sandy",  # Not in ['Loam', 'Clay']
        organic_matter=2.0,
    )
    assert SoilSuitabilityEngine.is_suitable(field_obj, sample_crop) is False
