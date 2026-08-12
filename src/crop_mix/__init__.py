"""Crop Mix Optimization System package."""

from crop_mix.models.optimizer_v1 import CropMixOptimizerV1, OptimizationResult
from crop_mix.models.optimizer_v2 import CropMixOptimizerV2, OptimizationResultV2
from crop_mix.models.optimizer_v3 import CropMixOptimizerV3, OptimizationResultV3
from crop_mix.models.soil_suitability import SoilSuitabilityEngine
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
    "SoilSuitabilityEngine",
    "FarmInputs",
    "CropParameters",
    "FieldParameters",
    "CropSoilRequirement",
    "get_example_farm_data",
]
