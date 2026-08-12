"""Version 2 Optimizer for Crop Mix Business Planner.

Extends optimization with Labor and Fertilizer physical constraints and monetary cost subtractions
using Pyomo continuous Linear Programming (LP) and HiGHS solver.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import pyomo.environ as pyo
from crop_mix.data.example_data import FarmInputs


@dataclass
class OptimizationResultV2:
    """Output results from Version 2 optimizer with financial breakdown and 4 resource metrics."""

    status: str
    is_feasible: bool
    crop_allocation: Dict[str, float]  # crop_name -> hectares allocated
    total_expected_revenue: float  # total gross revenue ($)
    total_production_cost: float  # total base production cost ($)
    total_labor_cost: float  # total labor cost ($)
    total_fertilizer_cost: float  # total fertilizer cost ($)
    expected_profit: float  # total net profit ($)
    total_land_used: float  # hectares used
    field_area_limit: float  # available land (ha)
    total_water_used: float  # m^3 water used
    water_budget_limit: float  # available water (m^3)
    total_labor_used: float  # labor hours used
    labor_budget_limit: float  # available labor (hours)
    total_fertilizer_used: float  # kg fertilizer used
    fertilizer_budget_limit: float  # available fertilizer (kg)
    solver_name: str = "highs"


class CropMixOptimizerV2:
    """Pyomo-based continuous Linear Programming (LP) optimizer (Version 2)."""

    def __init__(self, solver_name: str = "appsi_highs"):
        self.solver_name = solver_name

    def solve(self, farm_inputs: FarmInputs) -> OptimizationResultV2:
        """Formulate and solve the V2 crop mix optimization problem.

        Args:
            farm_inputs: Input dataclass containing field area, water budget, labor budget,
                        fertilizer budget, and crop parameters.

        Returns:
            OptimizationResultV2 containing detailed allocations, financials, and resource usage metrics.
        """
        # 1. Create Pyomo Concrete Model
        model = pyo.ConcreteModel(name="CropMixOptimization_V2")

        crop_names = list(farm_inputs.crops.keys())
        if not crop_names:
            raise ValueError("FarmInputs must contain at least one crop.")

        # Parameter lookup maps
        revenue_per_ha = {
            name: crop.revenue_per_hectare for name, crop in farm_inputs.crops.items()
        }
        prod_cost_per_ha = {
            name: crop.production_cost for name, crop in farm_inputs.crops.items()
        }
        labor_cost_per_ha = {
            name: crop.labor_cost_per_hectare for name, crop in farm_inputs.crops.items()
        }
        fert_cost_per_ha = {
            name: crop.fertilizer_cost_per_hectare for name, crop in farm_inputs.crops.items()
        }
        profit_per_ha = {
            name: crop.profit_per_hectare for name, crop in farm_inputs.crops.items()
        }
        water_req = {
            name: crop.water_requirement for name, crop in farm_inputs.crops.items()
        }
        labor_req = {
            name: crop.labor_requirement for name, crop in farm_inputs.crops.items()
        }
        fert_req = {
            name: crop.fertilizer_requirement for name, crop in farm_inputs.crops.items()
        }

        # 2. Pyomo Sets
        model.CROPS = pyo.Set(initialize=crop_names)

        # 3. Decision Variable: x[c] >= 0 (continuous hectares)
        model.x = pyo.Var(model.CROPS, domain=pyo.NonNegativeReals)

        # 4. Objective Function: Maximize expected net profit
        def profit_objective_rule(m):
            return sum(profit_per_ha[c] * m.x[c] for c in m.CROPS)

        model.profit_obj = pyo.Objective(rule=profit_objective_rule, sense=pyo.maximize)

        # 5. Constraints
        # Land Constraint
        def land_area_rule(m):
            return sum(m.x[c] for c in m.CROPS) <= farm_inputs.field_area

        model.land_area_con = pyo.Constraint(rule=land_area_rule)

        # Water Constraint
        def water_budget_rule(m):
            return sum(water_req[c] * m.x[c] for c in m.CROPS) <= farm_inputs.water_budget

        model.water_budget_con = pyo.Constraint(rule=water_budget_rule)

        # Labor Constraint
        def labor_budget_rule(m):
            return sum(labor_req[c] * m.x[c] for c in m.CROPS) <= farm_inputs.labor_budget

        model.labor_budget_con = pyo.Constraint(rule=labor_budget_rule)

        # Fertilizer Constraint
        def fertilizer_budget_rule(m):
            return sum(fert_req[c] * m.x[c] for c in m.CROPS) <= farm_inputs.fertilizer_budget

        model.fertilizer_budget_con = pyo.Constraint(rule=fertilizer_budget_rule)

        # 6. Solve using HiGHS
        solver = self._get_solver()
        results = solver.solve(model)

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
        crop_allocation = {}
        total_land = 0.0
        total_water = 0.0
        total_labor = 0.0
        total_fert = 0.0

        total_revenue = 0.0
        total_prod_cost = 0.0
        total_labor_cost = 0.0
        total_fert_cost = 0.0

        for c in crop_names:
            val = pyo.value(model.x[c]) if model.x[c].value is not None else 0.0
            val = max(0.0, round(val, 4))
            crop_allocation[c] = val

            total_land += val
            total_water += val * water_req[c]
            total_labor += val * labor_req[c]
            total_fert += val * fert_req[c]

            total_revenue += val * revenue_per_ha[c]
            total_prod_cost += val * prod_cost_per_ha[c]
            total_labor_cost += val * labor_cost_per_ha[c]
            total_fert_cost += val * fert_cost_per_ha[c]

        expected_profit = pyo.value(model.profit_obj) if model.profit_obj is not None else 0.0

        return OptimizationResultV2(
            status=term_cond,
            is_feasible=is_feasible,
            crop_allocation=crop_allocation,
            total_expected_revenue=round(total_revenue, 2),
            total_production_cost=round(total_prod_cost, 2),
            total_labor_cost=round(total_labor_cost, 2),
            total_fertilizer_cost=round(total_fert_cost, 2),
            expected_profit=round(expected_profit, 2),
            total_land_used=round(total_land, 4),
            field_area_limit=farm_inputs.field_area,
            total_water_used=round(total_water, 4),
            water_budget_limit=farm_inputs.water_budget,
            total_labor_used=round(total_labor, 4),
            labor_budget_limit=farm_inputs.labor_budget,
            total_fertilizer_used=round(total_fert, 4),
            fertilizer_budget_limit=farm_inputs.fertilizer_budget,
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
