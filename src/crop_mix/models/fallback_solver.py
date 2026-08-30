"""Fallback Simplex Solver in pure Python/Numpy for Crop Mix Business Planner.

Solves the linear programming models (V1, V2, V3, V4) without relying on Pyomo or external solver binaries (like HiGHS).
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from crop_mix.data.example_data import FarmInputs


def solve_simplex_lp(c: np.ndarray, A: np.ndarray, b: np.ndarray) -> Tuple[str, float, np.ndarray]:
    """Solve the LP: Maximize c^T x subject to A x <= b, x >= 0.

    Uses standard Phase 2 Simplex method, assuming b >= 0.
    """
    m, n = A.shape
    tableau = np.zeros((m + 1, n + m + 1))
    tableau[:m, :n] = A
    tableau[:m, n:n+m] = np.eye(m)
    tableau[:m, -1] = b
    tableau[-1, :n] = -c

    basis = list(range(n, n + m))

    max_iter = 5000
    for iteration in range(max_iter):
        obj_row = tableau[-1, :-1]
        col = np.argmin(obj_row)
        if obj_row[col] >= -1e-9:
            # Optimal
            break

        ratios = []
        for i in range(m):
            val = tableau[i, col]
            if val > 1e-9:
                ratios.append(tableau[i, -1] / val)
            else:
                ratios.append(float("inf"))

        row = np.argmin(ratios)
        if ratios[row] == float("inf"):
            return "unbounded", 0.0, np.zeros(n)

        # Pivot operation
        pivot_val = tableau[row, col]
        tableau[row, :] /= pivot_val
        for i in range(m + 1):
            if i != row:
                factor = tableau[i, col]
                tableau[i, :] -= factor * tableau[row, :]

        basis[row] = col
    else:
        return "max_iterations", 0.0, np.zeros(n)

    # Extract variable values
    x = np.zeros(n)
    for i, b_var in enumerate(basis):
        if b_var < n:
            x[b_var] = tableau[i, -1]

    opt_val = tableau[-1, -1]
    return "optimal", opt_val, x


class FallbackOptimizerV4:
    """Fallback solver that solves V4 crop mix optimization using pure Python/Numpy Simplex."""

    def __init__(self, soil_engine, rotation_loader):
        self.soil_engine = soil_engine
        self.rotation_loader = rotation_loader

    def solve(self, farm_inputs: FarmInputs) -> Dict[str, Any]:
        """Formulate and solve V4 LP model using the custom Simplex solver."""
        crop_names = list(farm_inputs.crops.keys())
        field_names = list(farm_inputs.fields.keys())

        # 1. Compute suitability matrices
        soil_matrix = self.soil_engine.calculate_suitability_matrix(farm_inputs)
        rotation_matrix: Dict[Tuple[str, str], int] = {}
        for f_name, f_obj in farm_inputs.fields.items():
            prev_c = f_obj.previous_crop
            for c_name in crop_names:
                rotation_matrix[(f_name, c_name)] = self.rotation_loader.get_rotation_suitability(prev_c, c_name)

        # 2. Map variables (field, crop) -> column index k
        var_map: List[Tuple[str, str]] = []
        idx_map: Dict[Tuple[str, str], int] = {}
        k = 0
        for f in field_names:
            for c in crop_names:
                var_map.append((f, c))
                idx_map[(f, c)] = k
                k += 1

        n_vars = len(var_map)

        # 3. Formulate objective function (Maximize Profit)
        c = np.zeros(n_vars)
        for idx, (f, c_name) in enumerate(var_map):
            c[idx] = farm_inputs.crops[c_name].profit_per_hectare

        # 4. Formulate constraints
        A_list = []
        b_list = []

        # (a) Per-Field Area constraints: sum_c x_{f,c} <= area_f
        for f in field_names:
            row = np.zeros(n_vars)
            for c_name in crop_names:
                row[idx_map[(f, c_name)]] = 1.0
            A_list.append(row)
            b_list.append(farm_inputs.fields[f].area)

        # (b) Soil & Rotation Suitability constraints: x_{f,c} <= suitability_{f,c} * area_f
        for f in field_names:
            for c_name in crop_names:
                soil_fit = soil_matrix.get((f, c_name), 0)
                rot_fit = rotation_matrix.get((f, c_name), 0)
                suitability = min(soil_fit, rot_fit)
                
                row = np.zeros(n_vars)
                row[idx_map[(f, c_name)]] = 1.0
                A_list.append(row)
                b_list.append(suitability * farm_inputs.fields[f].area)

        # (c) Global Water Budget constraint: sum_{f,c} water_req_c * x_{f,c} <= water_budget
        row = np.zeros(n_vars)
        for f, c_name in var_map:
            row[idx_map[(f, c_name)]] = farm_inputs.crops[c_name].water_requirement
        A_list.append(row)
        b_list.append(farm_inputs.water_budget)

        # (d) Global Labor Budget constraint: sum_{f,c} labor_req_c * x_{f,c} <= labor_budget
        row = np.zeros(n_vars)
        for f, c_name in var_map:
            row[idx_map[(f, c_name)]] = farm_inputs.crops[c_name].labor_requirement
        A_list.append(row)
        b_list.append(farm_inputs.labor_budget)

        # (e) Global Fertilizer Budget constraint: sum_{f,c} fert_req_c * x_{f,c} <= fertilizer_budget
        row = np.zeros(n_vars)
        for f, c_name in var_map:
            row[idx_map[(f, c_name)]] = farm_inputs.crops[c_name].fertilizer_requirement
        A_list.append(row)
        b_list.append(farm_inputs.fertilizer_budget)

        A = np.array(A_list)
        b = np.array(b_list)

        # 5. Solve using Simplex
        status, opt_val, x_vals = solve_simplex_lp(c, A, b)

        # 6. Extract allocation dictionary
        crop_allocation: Dict[str, Dict[str, float]] = {f: {c: 0.0 for c in crop_names} for f in field_names}
        field_land_used: Dict[str, float] = {f: 0.0 for f in field_names}
        total_land = 0.0
        total_water = 0.0
        total_labor = 0.0
        total_fert = 0.0
        total_revenue = 0.0
        total_prod_cost = 0.0
        total_labor_cost = 0.0
        total_fert_cost = 0.0

        for idx, val in enumerate(x_vals):
            f, c_name = var_map[idx]
            val = round(max(0.0, val), 4)
            crop_allocation[f][c_name] = val
            field_land_used[f] += val
            total_land += val

            crop = farm_inputs.crops[c_name]
            total_water += val * crop.water_requirement
            total_labor += val * crop.labor_requirement
            total_fert += val * crop.fertilizer_requirement

            total_revenue += val * crop.revenue_per_hectare
            total_prod_cost += val * crop.production_cost
            total_labor_cost += val * crop.labor_cost_per_hectare
            total_fert_cost += val * crop.fertilizer_cost_per_hectare

        is_feasible = status == "optimal"

        return {
            "status": "optimal" if is_feasible else status,
            "is_feasible": is_feasible,
            "crop_allocation": crop_allocation,
            "field_land_used": {f: round(val, 4) for f, val in field_land_used.items()},
            "field_land_limits": {f: f_obj.area for f, f_obj in farm_inputs.fields.items()},
            "total_land_used": round(total_land, 4),
            "total_water_used": round(total_water, 4),
            "water_budget_limit": farm_inputs.water_budget,
            "total_labor_used": round(total_labor, 4),
            "labor_budget_limit": farm_inputs.labor_budget,
            "total_fertilizer_used": round(total_fert, 4),
            "fertilizer_budget_limit": farm_inputs.fertilizer_budget,
            "total_expected_revenue": round(total_revenue, 2),
            "total_production_cost": round(total_prod_cost, 2),
            "total_labor_cost": round(total_labor_cost, 2),
            "total_fertilizer_cost": round(total_fert_cost, 2),
            "expected_profit": round(opt_val, 2),
            "soil_suitability_matrix": soil_matrix,
            "rotation_suitability_matrix": rotation_matrix,
            "field_previous_crops": {f: f_obj.previous_crop for f, f_obj in farm_inputs.fields.items()},
            "solver_name": "simplex_fallback",
        }
