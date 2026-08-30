"""Unit tests for Feddan (فدان) vs. Hectare unit handling."""

import pytest
from crop_mix.data.water_loader import EgyptWaterDataLoader
from crop_mix.data.example_data import get_example_farm_data


def test_water_requirement_feddan_vs_ha_conversion():
    """Verify 1 mm depth equals 10 m^3/ha and 4.2 m^3/feddan (exact 0.42 ratio)."""
    loader = EgyptWaterDataLoader()
    
    water_ha = loader.get_water_requirement("Wheat", zone="Delta", season="Winter", unit="ha")
    water_feddan = loader.get_water_requirement("Wheat", zone="Delta", season="Winter", unit="feddan")
    
    assert water_ha > 0
    assert water_feddan > 0
    assert water_feddan == pytest.approx(water_ha * 0.42, rel=1e-3)


def test_preset_farm_data_feddan_units():
    """Verify preset farm data uses Egyptian Feddan areas and per-Feddan crop parameters."""
    farm = get_example_farm_data()
    
    # 3 Fields totaling 240 feddans
    assert farm.field_area == 240.0
    assert len(farm.fields) == 3
    assert "حوض الشمالي" in farm.fields
    assert "حوض القبلي" in farm.fields
    assert "حوض الشرقية" in farm.fields

    # Crop water requirement per feddan is less than per ha
    wheat = farm.crops["Wheat"]
    assert wheat.water_requirement > 0
    assert wheat.expected_yield == 2.5  # 2.5 tons/feddan
