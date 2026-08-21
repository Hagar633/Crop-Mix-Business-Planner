"""Crop Mix Optimization System package."""

from crop_mix.models.optimizer_v1 import CropMixOptimizerV1, OptimizationResult
from crop_mix.models.optimizer_v2 import CropMixOptimizerV2, OptimizationResultV2
from crop_mix.models.optimizer_v3 import CropMixOptimizerV3, OptimizationResultV3
from crop_mix.models.optimizer_v4 import CropMixOptimizerV4, OptimizationResultV4
from crop_mix.models.soil_suitability import SoilSuitabilityEngine
from crop_mix.data.rotation_loader import RotationMatrixLoader
from crop_mix.data.example_data import (
    FarmInputs,
    CropParameters,
    FieldParameters,
    CropSoilRequirement,
    get_example_farm_data,
)

__all__ = [
    "CropMixOptimizerV1",
    "OptimizationResult",
    "CropMixOptimizerV2",
    "OptimizationResultV2",
    "CropMixOptimizerV3",
    "OptimizationResultV3",
    "CropMixOptimizerV4",
    "OptimizationResultV4",
    "SoilSuitabilityEngine",
    "RotationMatrixLoader",
    "FarmInputs",
    "CropParameters",
    "FieldParameters",
    "CropSoilRequirement",
    "get_example_farm_data",
]
