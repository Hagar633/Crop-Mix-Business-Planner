"""Unit tests for RotationMatrixLoader data loading, validation, and agronomic rules (V4)."""

import pytest
import pandas as pd
from crop_mix.data.rotation_loader import RotationMatrixLoader


@pytest.fixture
def loader():
    """Fixture initializing RotationMatrixLoader from default Excel dataset."""
    return RotationMatrixLoader()


def test_valid_rotation_matrix_loading(loader):
    """Verify that a valid rotation matrix is loaded successfully."""
    assert loader is not None
    assert len(loader.matrix_crops) == 53
    assert len(loader.perennial_map) == 53


def test_crop_name_normalization_and_resolution(loader):
    """Verify crop name normalization (whitespace and case robustness) and loud error for unmatched crops."""
    # Extra whitespace and lowercase matching
    assert loader.resolve_crop_name("  wheat  ") == "Wheat"
    assert loader.resolve_crop_name("yellow corn") == "Yellow Corn"
    assert loader.resolve_crop_name("SOYBEAN") == "Soybean"

    # Unmatched crop fails loudly
    with pytest.raises(ValueError, match="could not be matched in the Rotation Matrix"):
        loader.resolve_crop_name("UnmatchedUnknownCrop")


def test_row_column_symmetry_check(tmp_path):
    """Verify that a matrix with asymmetrical row and column crop sets raises ValueError at load time."""
    excel_file = tmp_path / "asymmetric_matrix.xlsx"

    df_class = pd.DataFrame({
        "Crop (English)": ["Wheat", "Barley", "Corn"],
        "Tree_or_Perennial": ["No", "No", "No"]
    })

    # Rows have Wheat & Barley, but Cols have Wheat & Corn
    df_matrix = pd.DataFrame([
        ["Arabic", "Arabic Header", "Wheat", "Corn"],
        ["Wheat", "قمح", 1, 0],
        ["Barley", "شعير", 0, 1]
    ], columns=["Previous Crop (English)", "Unnamed: 1", "Wheat", "Corn"])

    with pd.ExcelWriter(excel_file) as writer:
        df_matrix.to_excel(writer, sheet_name="Rotation Matrix", index=False)
        df_class.to_excel(writer, sheet_name="Crop Classification", index=False)

    with pytest.raises(ValueError, match="row crops and column crops do not match"):
        RotationMatrixLoader(excel_path=str(excel_file))


def test_duplicate_row_column_validation_error(tmp_path):
    """Verify that duplicate crop names in rows or columns raise ValueError."""
    excel_file = tmp_path / "duplicate_matrix.xlsx"

    df_class = pd.DataFrame({
        "Crop (English)": ["Wheat", "Barley"],
        "Tree_or_Perennial": ["No", "No"]
    })

    # Duplicate column 'Wheat'
    df_matrix = pd.DataFrame([
        ["Arabic", "Arabic Header", "Wheat", "Wheat"],
        ["Wheat", "قمح", 1, 0],
        ["Barley", "شعير", 0, 1]
    ], columns=["Previous Crop (English)", "Unnamed: 1", "Wheat", "Wheat"])

    with pd.ExcelWriter(excel_file) as writer:
        df_matrix.to_excel(writer, sheet_name="Rotation Matrix", index=False)
        df_class.to_excel(writer, sheet_name="Crop Classification", index=False)

    with pytest.raises(ValueError, match="Duplicate column crop names"):
        RotationMatrixLoader(excel_path=str(excel_file))


def test_non_binary_matrix_value_validation_error(tmp_path):
    """Verify that non-binary matrix values (e.g. 2, 99, NaN) raise ValueError at load time."""
    excel_file = tmp_path / "invalid_values_matrix.xlsx"

    df_class = pd.DataFrame({
        "Crop (English)": ["Wheat", "Barley"],
        "Tree_or_Perennial": ["No", "No"]
    })

    df_matrix = pd.DataFrame([
        ["Arabic", "Arabic Header", "Wheat", "Barley"],
        ["Wheat", "قمح", 1, 99],  # Invalid 99
        ["Barley", "شعير", 0, 1]
    ], columns=["Previous Crop (English)", "Unnamed: 1", "Wheat", "Barley"])

    with pd.ExcelWriter(excel_file) as writer:
        df_matrix.to_excel(writer, sheet_name="Rotation Matrix", index=False)
        df_class.to_excel(writer, sheet_name="Crop Classification", index=False)

    with pytest.raises(ValueError, match="non-binary values"):
        RotationMatrixLoader(excel_path=str(excel_file))


def test_optimization_crop_absent_from_rotation_matrix_error(loader):
    """Verify that an optimization crop absent from the rotation matrix raises loud ValueError."""
    opt_crops = ["Wheat", "NonExistentCrop"]
    with pytest.raises(ValueError, match=r"Optimization dataset contains crop\(s\) missing from the Rotation Matrix"):
        loader.validate_optimization_crops(opt_crops)


def test_same_crop_rotation_allowed(loader):
    """Verify same-crop rotation where matrix = 1 (e.g. Rice -> Rice)."""
    assert loader.get_rotation_suitability("Rice", "Rice") == 1


def test_same_crop_rotation_disallowed(loader):
    """Verify same-crop rotation where matrix = 0 (e.g. Fully Mature (Dry) Onion -> Fully Mature (Dry) Onion)."""
    assert loader.get_rotation_suitability("Fully Mature (Dry) Onion", "Fully Mature (Dry) Onion") == 0


def test_onion_cross_forms_disallowed(loader):
    """Verify cross-type onion forms -> each other = 0."""
    assert loader.get_rotation_suitability("Black-Seed Onion", "Fully Mature (Dry) Onion") == 0
    assert loader.get_rotation_suitability("Green Onion (Single Harvest)", "Black-Seed Onion") == 0


def test_cereal_legume_transitions(loader):
    """Verify cereal <-> legume transitions allowed per matrix."""
    assert loader.get_rotation_suitability("Wheat", "Soybean") == 1
    assert loader.get_rotation_suitability("Soybean", "Wheat") == 1


def test_same_family_disallowed_transition(loader):
    """Verify generally-disallowed same-family transition (e.g. Potato -> Tomato = 0)."""
    assert loader.get_rotation_suitability("Potato", "Tomato") == 0


def test_perennial_continuation_allowed(loader):
    """Verify established perennial continuation allowed (Orange -> Orange = 1)."""
    assert loader.get_rotation_suitability("Orange", "Orange") == 1


def test_perennial_to_different_perennial_disallowed(loader):
    """Verify established perennial -> different perennial disallowed (Mango -> Banana = 0)."""
    assert loader.get_rotation_suitability("Mango", "Banana") == 0


def test_perennial_to_annual_disallowed(loader):
    """Verify established perennial -> annual crop disallowed (Orange -> Wheat = 0)."""
    assert loader.get_rotation_suitability("Orange", "Wheat") == 0


def test_annual_to_new_perennial_disallowed(loader):
    """Verify annual -> new perennial establishment disallowed in seasonal model (Wheat -> Orange = 0)."""
    assert loader.get_rotation_suitability("Wheat", "Orange") == 0
