"""Unit tests for EgyptWaterDataLoader module."""

import pytest
from crop_mix.data.water_loader import EgyptWaterDataLoader


@pytest.fixture
def loader():
    return EgyptWaterDataLoader()


def test_loader_initialization(loader):
    assert loader is not None
    assert not loader._ready_lookup.empty
    assert not loader._et_range.empty


def test_wheat_water_requirement_by_zone(loader):
    # Wheat in Delta, Winter
    wheat_delta = loader.get_water_requirement("Wheat", zone="Delta", season="Winter")
    # Wheat in Upper Egypt, Winter
    wheat_upper = loader.get_water_requirement("Wheat", zone="Upper Egypt", season="Winter")
    
    assert wheat_delta > 0
    assert wheat_upper > 0
    # Upper Egypt has higher ETo / water demand than Delta
    assert wheat_upper > wheat_delta


def test_maize_alias_water_requirement(loader):
    # Yellow Corn, White Corn, Sweet Corn should alias to Maize
    water_yellow = loader.get_water_requirement("Yellow Corn", zone="Delta", season="Summer")
    water_maize = loader.get_water_requirement("Maize", zone="Delta", season="Summer")

    assert water_yellow > 0
    assert water_yellow == water_maize


def test_crop_water_info_dict(loader):
    info = loader.get_all_crop_water_info(zone="Delta", season="Winter")
    assert isinstance(info, dict)
    assert len(info) > 0
    assert "Wheat" in info
