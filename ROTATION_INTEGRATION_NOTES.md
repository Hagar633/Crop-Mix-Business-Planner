# Rotation Integration Notes (Step 0 - Inspection Summary)

This document summarizes the codebase architecture, existing optimization mechanics (V1, V2, V3), and the Excel crop rotation dataset prior to implementing Feature V4 (Crop Rotation).

---

## 1. Repository Structure & Existing Implementations

### Codebase Organization
- `src/crop_mix/data/example_data.py`: Data models (`CropParameters`, `FieldParameters`, `CropSoilRequirement`, `FarmInputs`) and synthetic test datasets.
- `src/crop_mix/models/`:
  - `optimizer_v1.py`: Farm-level land ($A$) & water ($W$) LP optimizer (`CropMixOptimizerV1`).
  - `optimizer_v2.py`: Extended farm-level LP optimizer adding labor ($L$) and fertilizer ($F$) monetary cost subtractions and physical budget constraints (`CropMixOptimizerV2`).
  - `optimizer_v3.py`: Field-level continuous LP optimizer ($x_{f,c} \ge 0$) incorporating soil suitability filtering (`CropMixOptimizerV3`).
  - `soil_suitability.py`: Standalone engine evaluating pH, EC, and soil texture rules to build binary suitability matrix $S_{f,c} \in \{0, 1\}$.
- `data/crop_rotation_matrix_v10_corrected.xlsx`: Source of truth Excel workbook containing crop rotation rules, classification, and 53x53 rotation matrix.
- `tests/`: Comprehensive test suite for V1, V2, V3, and soil suitability.
- `run_demo.py`: Standalone CLI demonstration script.

### Key Technical Details of V1 - V3
- **Optimization Solver**: Pyomo (`pyomo.environ`) with HiGHS open-source solver (`highspy` / `appsi_highs`).
- **Decision Variables**:
  - V1 & V2: Farm-level continuous variables $x_c \ge 0$ (hectares allocated to crop $c$).
  - V3: Field-level continuous variables $x_{f,c} \ge 0$ (hectares of field $f$ allocated to crop $c$).
- **Objective Function**: Maximize expected net farm profit $\max \sum \pi_c \, x_{f,c}$.
- **Constraints Handling**: Solved simultaneously as continuous LP models in Pyomo.

---

## 2. Excel Rotation Dataset Structure (`crop_rotation_matrix_v10_corrected.xlsx`)

The Excel workbook contains 6 sheets:
1. `Rotation Matrix`: 53x53 binary matrix of `Previous Crop (English)` (rows) vs `Next Crop (English)` (columns).
   - `1` = Agronomically recommended rotation for Egypt.
   - `0` = Not recommended / agronomically undesirable.
2. `Crop Classification`: 53 crops mapped with `Crop_Family` (e.g. Cereals, Legumes, Alliums, Solanaceae) and `Tree_or_Perennial` ("Yes" or "No").
3. `Rotation Rules`: Summary of 10 agronomic rules governing same-crop, cross-family, and perennial transitions.
4. `Legend`: Defines 1 (suitable) and 0 (not suitable).
5. `Same-Crop Rationale`: Agronomic justifications for same-crop continuous planting rules.
6. `Corrections Log v10`: Documented corrections for specific crop pairs.

---

## 3. Agronomic & Perennial Rotation Rules

### Critical Matrix Semantics
- Matrix value `1` means agronomically GOOD/recommended rotation, NOT mere physical possibility.
- `0` means not recommended (e.g., Onion $\to$ Onion = 0; Potato $\to$ Tomato = 0).

### Perennial / Tree Crop Rules (`Tree_or_Perennial == 'Yes'`)
- Established perennial $\to$ same perennial: Allowed if matrix = 1 (orchard continuation).
- Established perennial $\to$ different perennial: Disallowed (0) (orchard replacement is not a seasonal rotation).
- Established perennial $\to$ annual crop: Disallowed (0) while orchard is standing.
- Annual crop $\to$ new perennial establishment: Disallowed (0) in the single-season rotation model (out of scope for normal seasonal rotation).

---

## 4. Crop Naming Reconciliation & Validation Rules

### Discovered Naming Mismatches
Comparing the synthetic crops in `example_data.py` against `Crop Classification`:
- `Wheat` $\to$ Matched (`Wheat`).
- `Cotton` $\to$ Matched (`Cotton`).
- `Corn` $\to$ Named `Yellow Corn` (or `White Corn` / `Sweet Corn`) in matrix.
- `Soybeans` $\to$ Named `Soybean` (singular) in matrix.
- `Tomatoes` $\to$ Named `Tomato` (singular) in matrix.

### Validation Rules to Implement in Loader (`RotationMatrixLoader`)
1. Fail loudly if row/column names are missing or duplicate.
2. Fail loudly if matrix values contain non-binary entries (not 0 or 1).
3. Fail loudly if any crop in the optimization dataset is missing from the rotation matrix.
