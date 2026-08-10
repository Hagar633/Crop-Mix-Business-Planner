"""Version 1 Optimizer for Crop Mix Business Planner.

Uses Pyomo and HiGHS solver to maximize expected net profit subject to land and water constraints.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import pyomo.environ as pyo
from crop_mix.data.example_data import FarmInputs


@dataclass
class OptimizationResult:
    """Output results from Version 1 optimizer."""

    status: str
    is_feasible: bool
    crop_allocation: Dict[str, float]  # crop_name -> hectares allocated
    expected_profit: float  # total expected net profit ($)
    total_land_used: float  # total hectares allocated
    total_water_used: float  # total m^3 water used
    field_area_limit: float  # available land constraint (ha)
    water_budget_limit: float  # available water constraint (m^3)
    solver_name: str = "highs"


class CropMixOptimizerV1:
    """Pyomo-based MILP optimizer for Crop Mix allocation (Version 1)."""

    def __init__(self, solver_name: str = "appsi_highs"):
        self.solver_name = solver_name

    def solve(self, farm_inputs: FarmInputs) -> OptimizationResult:
        """Formulate and solve the crop mix optimization problem.

        Args:
            farm_inputs: Input dataclass containing field area, water budget, and crop parameters.

        Returns:
            OptimizationResult containing crop allocation, total profit, land used, and water used.
        """
        # 1. Create Pyomo Concrete Model
        model = pyo.ConcreteModel(name="CropMixOptimization_V1")

        crop_names = list(farm_inputs.crops.keys())
        if not crop_names:
            raise ValueError("FarmInputs must contain at least one crop.")

        # Derived profit per hectare ($/ha) and water requirement (m^3/ha) per crop
        profit_per_ha = {
            name: crop.profit_per_hectare for name, crop in farm_inputs.crops.items()
        }
        water_req = {
            name: crop.water_requirement for name, crop in farm_inputs.crops.items()
        }

        # 2. Pyomo Sets
        model.CROPS = pyo.Set(initialize=crop_names)

        # 3. Decision Variables: x[crop] >= 0 (hectares)
        model.x = pyo.Var(model.CROPS, domain=pyo.NonNegativeReals)

        # 4. Objective Function: Maximize expected profit
        def profit_objective_rule(m):
            return sum(profit_per_ha[c] * m.x[c] for c in m.CROPS)

        model.profit_obj = pyo.Objective(rule=profit_objective_rule, sense=pyo.maximize)

        # 5. Constraints
        # Total land area constraint: total allocated area <= field area
        def land_area_rule(m):
            return sum(m.x[c] for c in m.CROPS) <= farm_inputs.field_area

        model.land_area_con = pyo.Constraint(rule=land_area_rule)

        # Total water consumption constraint: total water <= water budget
        def water_budget_rule(m):
            return sum(water_req[c] * m.x[c] for c in m.CROPS) <= farm_inputs.water_budget

        model.water_budget_con = pyo.Constraint(rule=water_budget_rule)

        # 6. Solve using HiGHS
        solver = self._get_solver()
        results = solver.solve(model)

        # Check solver termination status
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

        # Extract values
        crop_allocation = {}
        total_land = 0.0
        total_water = 0.0

        for c in crop_names:
            val = pyo.value(model.x[c]) if model.x[c].value is not None else 0.0
            # Clean up tiny floating point residuals close to 0
            val = max(0.0, round(val, 4))
            crop_allocation[c] = val
            total_land += val
            total_water += val * water_req[c]

        expected_profit = pyo.value(model.profit_obj) if model.profit_obj is not None else 0.0

        return OptimizationResult(
            status=term_cond,
            is_feasible=is_feasible,
            crop_allocation=crop_allocation,
            expected_profit=round(expected_profit, 2),
            total_land_used=round(total_land, 4),
            total_water_used=round(total_water, 4),
            field_area_limit=farm_inputs.field_area,
            water_budget_limit=farm_inputs.water_budget,
            solver_name=self.solver_name,
        )

    def _get_solver(self):
        """Instantiate Pyomo HiGHS solver instance."""
        # Try requested solver factory first, then fall back to standard highspy interface
        try:
            solver = pyo.SolverFactory(self.solver_name)
            if solver.available():
                return solver
        except Exception:
            pass

        # Fallbacks
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
