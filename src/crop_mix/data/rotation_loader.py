"""Loader and validator for Excel crop rotation matrix and perennial classifications (V4)."""

import os
from typing import Dict, List, Optional, Set, Tuple
import pandas as pd


class RotationMatrixLoader:
    """Loads, validates, and queries the crop rotation matrix dataset."""

    def __init__(self, excel_path: Optional[str] = None):
        from pathlib import Path
        if excel_path is None:
            default_path = Path(__file__).resolve().parent / "crop_rotation_matrix_v10_corrected.xlsx"
            if default_path.exists():
                self.excel_path = str(default_path)
            else:
                self.excel_path = "data/crop_rotation_matrix_v10_corrected.xlsx"
        else:
            self.excel_path = excel_path

        if not os.path.exists(self.excel_path):
            # Fallback path if running from subfolder
            alt_path = os.path.join("src", "crop_mix", "data", "crop_rotation_matrix_v10_corrected.xlsx")
            if os.path.exists(alt_path):
                self.excel_path = alt_path
            else:
                raise FileNotFoundError(f"Rotation matrix Excel workbook not found at '{self.excel_path}' or '{alt_path}'.")


        self._load_and_validate()

    @staticmethod
    def normalize_name(name: str) -> str:
        """Normalize a crop name string by stripping leading/trailing whitespace and collapsing internal spaces."""
        if not name:
            return ""
        return " ".join(str(name).strip().split())

    def _load_and_validate(self):
        """Read and validate the Rotation Matrix and Crop Classification sheets."""
        xl = pd.ExcelFile(self.excel_path)
        if "Rotation Matrix" not in xl.sheet_names:
            raise ValueError(f"Sheet 'Rotation Matrix' missing from '{self.excel_path}'.")
        if "Crop Classification" not in xl.sheet_names:
            raise ValueError(f"Sheet 'Crop Classification' missing from '{self.excel_path}'.")

        # 1. Load Crop Classification
        df_class = pd.read_excel(self.excel_path, sheet_name="Crop Classification")
        if "Crop (English)" not in df_class.columns or "Tree_or_Perennial" not in df_class.columns:
            raise ValueError("Crop Classification sheet must contain 'Crop (English)' and 'Tree_or_Perennial' columns.")

        self.perennial_map: Dict[str, bool] = {}
        self.family_map: Dict[str, str] = {}
        self.arabic_map: Dict[str, str] = {}
        self.english_map: Dict[str, str] = {}

        for _, row in df_class.iterrows():
            crop_name = self.normalize_name(row["Crop (English)"])
            is_perennial = str(row["Tree_or_Perennial"]).strip().lower() == "yes"
            self.perennial_map[crop_name] = is_perennial
            if "Crop_Family" in df_class.columns:
                self.family_map[crop_name] = self.normalize_name(row["Crop_Family"])
            
            if "Crop (Arabic) / اسم المحصول" in df_class.columns and pd.notna(row["Crop (Arabic) / اسم المحصول"]):
                ar_name = self.normalize_name(row["Crop (Arabic) / اسم المحصول"])
                self.arabic_map[crop_name] = ar_name
                self.english_map[ar_name] = crop_name
                self.english_map[ar_name.lower()] = crop_name

        # 2. Load Rotation Matrix
        df_matrix = pd.read_excel(self.excel_path, sheet_name="Rotation Matrix")

        # Column headers start from Column index 2
        raw_col_headers = [self.normalize_name(c) for c in df_matrix.columns[2:]]
        # Clean column names (strip pandas duplicate suffixes if any, e.g., 'Wheat.1' -> 'Wheat')
        col_crops_clean = [c.split(".")[0].strip() for c in raw_col_headers]

        # Row headers start from row index 1 (row 0 is Arabic names header row)
        row_crops_raw = df_matrix.iloc[1:, 0].dropna().tolist()
        row_crops_clean = [self.normalize_name(c) for c in row_crops_raw]

        # Check A: Header validation (missing headers)
        if not row_crops_clean or not col_crops_clean:
            raise ValueError("Rotation Matrix sheet contains missing row or column crop headers.")

        # Check B: Duplicate check (BEFORE symmetry check)
        if len(raw_col_headers) != len(set(raw_col_headers)) or len(col_crops_clean) != len(set(col_crops_clean)):
            duplicates = sorted(list(set([c for c in col_crops_clean if col_crops_clean.count(c) > 1])))
            raise ValueError(f"Duplicate column crop names found in Rotation Matrix: {duplicates}")

        if len(row_crops_clean) != len(set(row_crops_clean)):
            duplicates = sorted(list(set([c for c in row_crops_clean if row_crops_clean.count(c) > 1])))
            raise ValueError(f"Duplicate row crop names found in Rotation Matrix: {duplicates}")

        # Check C: Row / Column Symmetry Check
        row_set = set(row_crops_clean)
        col_set = set(col_crops_clean)
        if row_set != col_set:
            only_in_rows = sorted(list(row_set - col_set))
            only_in_cols = sorted(list(col_set - row_set))
            raise ValueError(
                f"Rotation Matrix row crops and column crops do not match! "
                f"Present only in rows: {only_in_rows}; Present only in columns: {only_in_cols}"
            )

        self.matrix_crops: Set[str] = row_set

        # Case-normalized lookup dictionary mapping lowercased crop name -> exact matrix crop name
        self.normalized_lookup: Dict[str, str] = {
            c.lower(): c for c in self.matrix_crops
        }

        # Check D: Value binary validation (0 or 1 strictly)
        matrix_values = df_matrix.iloc[1 : 1 + len(row_crops_clean), 2 : 2 + len(col_crops_clean)].values
        self.matrix_dict: Dict[Tuple[str, str], int] = {}
        invalid_cells = []

        for r_idx, prev_c in enumerate(row_crops_clean):
            for c_idx, next_c in enumerate(col_crops_clean):
                val = matrix_values[r_idx, c_idx]
                if pd.isna(val) or val not in (0, 1):
                    invalid_cells.append(f"Row '{prev_c}', Col '{next_c}' = {val}")
                else:
                    self.matrix_dict[(prev_c, next_c)] = int(val)

        if invalid_cells:
            raise ValueError(
                f"Rotation Matrix contains non-binary values (not strictly 0 or 1) in {len(invalid_cells)} cell(s): "
                + ", ".join(invalid_cells[:5])
                + ("..." if len(invalid_cells) > 5 else "")
            )

    def resolve_crop_name(self, crop_name: str) -> str:
        """Resolve a crop name string (English or Arabic) to canonical Rotation Matrix name.

        Raises a clear ValueError if the crop cannot be matched.
        """
        clean_name = self.normalize_name(crop_name)
        if clean_name in self.matrix_crops:
            return clean_name

        # Check if Arabic crop name provided
        if clean_name in self.english_map:
            return self.english_map[clean_name]
        if clean_name.lower() in self.english_map:
            return self.english_map[clean_name.lower()]

        lower_name = clean_name.lower()
        if lower_name in self.normalized_lookup:
            return self.normalized_lookup[lower_name]

        raise ValueError(
            f"Crop '{crop_name}' could not be matched in the Rotation Matrix. "
            f"Please verify spelling against official matrix crop names."
        )


    def validate_optimization_crops(self, optimization_crops: List[str]):
        """Ensure every optimization crop exists in the rotation matrix.

        Fails loudly with a clear error identifying any unmatched crop.
        """
        missing = []
        for crop in optimization_crops:
            try:
                self.resolve_crop_name(crop)
            except ValueError:
                missing.append(crop)

        if missing:
            raise ValueError(
                f"Optimization dataset contains crop(s) missing from the Rotation Matrix: {missing}. "
                f"Please update crop names to match the Excel rotation matrix source of truth."
            )

    def is_perennial(self, crop_name: str) -> bool:
        """Check if a crop is classified as a Tree/Fruit Perennial."""
        canonical = self.resolve_crop_name(crop_name)
        return self.perennial_map.get(canonical, False)

    def get_rotation_suitability(self, previous_crop: Optional[str], next_crop: str) -> int:
        """Determine rotation suitability (1 = allowed, 0 = disallowed).

        Normalizes names and resolves canonical crop entries.
        Fails loudly if any crop cannot be matched.
        """
        next_canonical = self.resolve_crop_name(next_crop)

        if previous_crop is None or str(previous_crop).strip() == "" or str(previous_crop).strip().lower() == "none":
            # No previous crop / no history -> unconstrained
            return 1

        prev_canonical = self.resolve_crop_name(previous_crop)

        is_prev_tree = self.is_perennial(prev_canonical)
        is_next_tree = self.is_perennial(next_canonical)

        # Perennial / Tree Rules
        if is_prev_tree:
            if prev_canonical == next_canonical:
                # Perennial continuation: allowed if matrix value == 1
                return self.matrix_dict.get((prev_canonical, next_canonical), 0)
            else:
                # Established perennial -> different perennial or annual: disallowed (0)
                return 0
        else:
            if is_next_tree:
                # Annual -> new perennial establishment: disallowed (0) in seasonal model
                return 0
            else:
                # Annual -> annual: return matrix lookup
                return self.matrix_dict.get((prev_canonical, next_canonical), 0)
