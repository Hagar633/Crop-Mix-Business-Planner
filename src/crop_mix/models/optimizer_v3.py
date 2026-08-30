"""Version 3 Optimizer for Crop Mix Business Planner.

Formulates field-level continuous Linear Programming (LP) optimization subject to:
- Field land area limits
- Soil suitability constraints (pH, EC, texture)
- Global farm water, labor, and fertilizer budgets
Solves using Pyomo and HiGHS.
"""

from dataclasses import dataclass
from typing import Dict, Tuple, Any
import pyomo.environ as pyo
from crop_mix.data.example_data import FarmInputs
from crop_mix.models.soil_suitability import SoilSuitabilityEngine


@dataclass
class OptimizationResultV3:
    """Output results from Version 3 optimizer (field-level allocation & financials)."""

    status: str
    is_feasible: bool
    crop_allocation: Dict[str, Dict[str, float]]  # field_name -> crop_name -> hectares
    field_land_used: Dict[str, float]  # field_name -> total allocated ha
    field_land_limits: Dict[str, float]  # field_name -> area limit ha
    total_land_used: float  # sum of all allocated ha across fields
    total_water_used: float  # total m^3 water used
    water_budget_limit: float  # available water budget
    total_labor_used: float  # total labor hours used
    labor_budget_limit: float  # available labor budget
    total_fertilizer_used: float  # total fertilizer kg used
    fertilizer_budget_limit: float  # available fertilizer budget
    total_expected_revenue: float  # total gross revenue ($)
    total_production_cost: float  # total base production cost ($)
    total_labor_cost: float  # total labor cost ($)
    total_fertilizer_cost: float  # total fertilizer cost ($)
    expected_profit: float  # total net profit ($)
    suitability_matrix: Dict[Tuple[str, str], int]  # (field, crop) -> 1 or 0
    solver_name: str = "highs"


class CropMixOptimizerV3:
    """Pyomo-based field-level continuous Linear Programming (LP) optimizer (Version 3)."""

    def __init__(self, solver_name: str = "appsi_highs"):
        self.solver_name = solver_name
        self.suitability_engine = SoilSuitabilityEngine()

    def solve(self, farm_inputs: FarmInputs) -> OptimizationResultV3:
        """Formulate and solve field-level crop mix optimization problem.

        Args:
            farm_inputs: Input dataclass containing field parameters, water/labor/fertilizer budgets, and crops.

        Returns:
            OptimizationResultV3 with per-field crop allocations, suitability matrix, and financial/resource totals.
        """
        # 1. Create Pyomo Concrete Model
        model = pyo.ConcreteModel(name="CropMixOptimization_V3")

        field_names = list(farm_inputs.fields.keys())
        crop_names = list(farm_inputs.crops.keys())

        if not field_names:
            raise ValueError("FarmInputs must contain at least one field in fields dict.")
        if not crop_names:
            raise ValueError("FarmInputs must contain at least one crop in crops dict.")

        # Compute suitability matrix (field x crop -> 1 or 0)
        suitability_matrix = self.suitability_engine.calculate_suitability_matrix(farm_inputs)

        # Lookup dictionaries for crop parameters
        profit_per_ha = {c: crop.profit_per_hectare for c, crop in farm_inputs.crops.items()}
        revenue_per_ha = {c: crop.revenue_per_hectare for c, crop in farm_inputs.crops.items()}
        prod_cost_per_ha = {c: crop.production_cost for c, crop in farm_inputs.crops.items()}
        labor_cost_per_ha = {c: crop.labor_cost_per_hectare for c, crop in farm_inputs.crops.items()}
        fert_cost_per_ha = {c: crop.fertilizer_cost_per_hectare for c, crop in farm_inputs.crops.items()}

        water_req = {c: crop.water_requirement for c, crop in farm_inputs.crops.items()}
        labor_req = {c: crop.labor_requirement for c, crop in farm_inputs.crops.items()}
        fert_req = {c: crop.fertilizer_requirement for c, crop in farm_inputs.crops.items()}

        field_areas = {f: f_obj.area for f, f_obj in farm_inputs.fields.items()}

        # 2. Pyomo Sets
        model.FIELDS = pyo.Set(initialize=field_names)
        model.CROPS = pyo.Set(initialize=crop_names)

        # 3. Decision Variables: x[field, crop] >= 0 (continuous hectares)
        model.x = pyo.Var(model.FIELDS, model.CROPS, domain=pyo.NonNegativeReals)

        # 4. Objective Function: Maximize total net profit across all fields
        def profit_obj_rule(m):
            return sum(
                profit_per_ha[c] * m.x[f, c]
                for f in m.FIELDS
                for c in m.CROPS
            )

        model.profit_obj = pyo.Objective(rule=profit_obj_rule, sense=pyo.maximize)

        # 5. Constraints
        # (a) Per-Field Area Constraint: sum_c x[f, c] <= field.area
        def field_area_rule(m, f):
            return sum(m.x[f, c] for c in m.CROPS) <= field_areas[f]

        model.field_area_con = pyo.Constraint(model.FIELDS, rule=field_area_rule)

        # (b) Soil Suitability Constraint: x[f, c] <= suitability[f, c] * field.area
        def suitability_rule(m, f, c):
            is_fit = suitability_matrix.get((f, c), 0)
            return m.x[f, c] <= is_fit * field_areas[f]

        model.suitability_con = pyo.Constraint(model.FIELDS, model.CROPS, rule=suitability_rule)

        # (c) Global Water Budget Constraint
        def water_budget_rule(m):
            return (
                sum(water_req[c] * m.x[f, c] for f in m.FIELDS for c in m.CROPS)
                <= farm_inputs.water_budget
            )

        model.water_budget_con = pyo.Constraint(rule=water_budget_rule)

        # (d) Global Labor Budget Constraint
        def labor_budget_rule(m):
            return (
                sum(labor_req[c] * m.x[f, c] for f in m.FIELDS for c in m.CROPS)
                <= farm_inputs.labor_budget
            )

        model.labor_budget_con = pyo.Constraint(rule=labor_budget_rule)

        # (e) Global Fertilizer Budget Constraint
        def fertilizer_budget_rule(m):
            return (
                sum(fert_req[c] * m.x[f, c] for f in m.FIELDS for c in m.CROPS)
                <= farm_inputs.fertilizer_budget
            )

        model.fertilizer_budget_con = pyo.Constraint(rule=fertilizer_budget_rule)

        # 6. Solve using HiGHS
        try:
            solver = self._get_solver()
            results = solver.solve(model)
        except Exception as e:
            import logging
            logging.warning(f"Optimization via Pyomo/HiGHS failed: {e}. Falling back to pure Python Simplex solver.")
            class MockRotationLoader:
                def get_rotation_suitability(self, prev, curr):
                    return 1
            from crop_mix.models.fallback_solver import FallbackOptimizerV4
            fallback = FallbackOptimizerV4(self.soil_engine, MockRotationLoader())
            res_dict = fallback.solve(farm_inputs)
            res_dict["suitability_matrix"] = res_dict.pop("soil_suitability_matrix")
            res_dict.pop("rotation_suitability_matrix", None)
            res_dict.pop("field_previous_crops", None)
            return OptimizationResultV3(**res_dict)



        status_str = str(results.solver.status) if hasattr(results.solver, "status") else "unknown"
        term_cond = (
            str(results.solver.termination_condition)
            if hasattr(results.solver, "termination_condition")
            else str(results.termination_condition) if hasattr(results, "termination_condition") else "optimal"
        )

        is_feasible = (
            term_cond.lower() in ("optimal", "feasible")
            or status_str.lower() in ("ok", "optimal")
        )

        # Extract results
        crop_allocation: Dict[str, Dict[str, float]] = {f: {} for f in field_names}
        field_land_used: Dict[str, float] = {f: 0.0 for f in field_names}

        total_land = 0.0
        total_water = 0.0
        total_labor = 0.0
        total_fert = 0.0

        total_revenue = 0.0
        total_prod_cost = 0.0
        total_labor_cost = 0.0
        total_fert_cost = 0.0

        for f in field_names:
            for c in crop_names:
                val = pyo.value(model.x[f, c]) if model.x[f, c].value is not None else 0.0
                val = max(0.0, round(val, 4))
                crop_allocation[f][c] = val

                field_land_used[f] += val
                total_land += val

                total_water += val * water_req[c]
                total_labor += val * labor_req[c]
                total_fert += val * fert_req[c]

                total_revenue += val * revenue_per_ha[c]
                total_prod_cost += val * prod_cost_per_ha[c]
                total_labor_cost += val * labor_cost_per_ha[c]
                total_fert_cost += val * fert_cost_per_ha[c]

        expected_profit = pyo.value(model.profit_obj) if model.profit_obj is not None else 0.0

        return OptimizationResultV3(
            status=term_cond,
            is_feasible=is_feasible,
            crop_allocation=crop_allocation,
            field_land_used={f: round(val, 4) for f, val in field_land_used.items()},
            field_land_limits=field_areas,
            total_land_used=round(total_land, 4),
            total_water_used=round(total_water, 4),
            water_budget_limit=farm_inputs.water_budget,
            total_labor_used=round(total_labor, 4),
            labor_budget_limit=farm_inputs.labor_budget,
            total_fertilizer_used=round(total_fert, 4),
            fertilizer_budget_limit=farm_inputs.fertilizer_budget,
            total_expected_revenue=round(total_revenue, 2),
            total_production_cost=round(total_prod_cost, 2),
            total_labor_cost=round(total_labor_cost, 2),
            total_fertilizer_cost=round(total_fert_cost, 2),
            expected_profit=round(expected_profit, 2),
            suitability_matrix=suitability_matrix,
            solver_name=self.solver_name,
        )

    def _get_solver(self):
        """Instantiate Pyomo HiGHS solver instance."""
        try:
            solver = pyo.SolverFactory(self.solver_name)
            if solver.available():
                return solver
        except Exception:
            pass

        for alt in ["appsi_highs", "highs", "highspy"]:
            try:
                solver = pyo.SolverFactory(alt)
                if solver.available():
                    self.solver_name = alt
                    return solver
            except Exception:
                continue

        raise RuntimeError(
            "HiGHS solver is not available. Ensure `highspy` is installed (`pip install highspy`)."
        )
