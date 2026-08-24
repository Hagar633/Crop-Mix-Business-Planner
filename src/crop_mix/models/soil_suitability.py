"""Soil Suitability Engine for Crop Mix Optimization (V3).

Evaluates field soil measurements against crop soil requirements to determine field-crop suitability (0 or 1).
"""

from typing import Dict, Tuple, List, Optional
import pandas as pd
from crop_mix.data.example_data import FieldParameters, CropParameters, FarmInputs


class SoilSuitabilityEngine:
    """Evaluates soil suitability for field-crop combinations."""

    @staticmethod
    def is_suitable(field_obj: FieldParameters, crop_obj: CropParameters) -> bool:
        """Check if a crop is suitable for a specific field based on soil parameters.

        Suitability criteria:
        - field.ph >= crop.min_ph
        - field.ph <= crop.max_ph
        - field.ec <= crop.max_ec
        - field.texture in crop.suitable_textures

        If crop has no soil requirement defined, it defaults to suitable (True).
        """
        req = crop_obj.soil_requirement
        if req is None:
            return True

        # pH range check
        if field_obj.ph < req.min_ph or field_obj.ph > req.max_ph:
            return False

        # Salinity (EC) check
        if field_obj.ec > req.max_ec:
            return False

        # Soil texture check
        if req.suitable_textures and field_obj.texture not in req.suitable_textures:
            return False

        return True

    def calculate_suitability_matrix(
        self, farm_inputs: FarmInputs
    ) -> Dict[Tuple[str, str], int]:
        """Calculate binary suitability matrix for all field-crop pairs.

        Returns:
            Dictionary mapping (field_name, crop_name) -> 1 (suitable) or 0 (unsuitable).
        """
        matrix = {}
        for field_name, field_obj in farm_inputs.fields.items():
            for crop_name, crop_obj in farm_inputs.crops.items():
                suitable = self.is_suitable(field_obj, crop_obj)
                matrix[(field_name, crop_name)] = 1 if suitable else 0
        return matrix

    def get_suitability_dataframe(self, farm_inputs: FarmInputs) -> pd.DataFrame:
        """Return suitability matrix as a pandas DataFrame formatted for visualization."""
        matrix = self.calculate_suitability_matrix(farm_inputs)
        field_names = list(farm_inputs.fields.keys())
        crop_names = list(farm_inputs.crops.keys())

        df_data = []
        for f in field_names:
            row = {"field": f}
            for c in crop_names:
                row[c] = matrix.get((f, c), 0)
            df_data.append(row)

        return pd.DataFrame(df_data).set_index("field")
