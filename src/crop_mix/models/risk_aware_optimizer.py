"""CVaR-Aware Crop Mix Optimizer (Risk-Augmented Version 4).

This module extends the deterministic V4 optimizer with a CVaR
(Conditional Value at Risk) objective term using the Rockafellar-Uryasev
LP formulation.

Three planning modes are supported:
  - 'max_profit':  Pure expected profit maximization (equivalent to V4).
                   No CVaR penalty. Risk weight w = 1.0.
  - 'balanced':    Equal weight to expected profit and CVaR reduction.
                   Risk weight w = 0.5.
  - 'risk_aware':  Strong CVaR penalty; prioritizes downside protection.
                   Risk weight w = 0.2.

Rockafellar-Uryasev CVaR Formulation (LP extension):
    Let S = set of scenarios, p_s = scenario probability, α = confidence level.
    Let π_{s,c} = net profit per hectare for crop c in scenario s.

    Define:
        profit_s = Σ_{f,c} x[f,c] * π_{s,c}   (linear in x)
        CVaR_α  = ζ + (1/(1-α)) * Σ_s p_s * z_s

    Where z_s >= max(-profit_s - ζ, 0)  ↔  z_s >= -profit_s - ζ, z_s >= 0

    Objective (mixed):
        maximize  w * Σ_s p_s * profit_s  -  (1-w) * CVaR_α
        =         w * Σ_s p_s * profit_s  -  (1-w) * ζ  -  (1-w)/(1-α) * Σ_s p_s * z_s

    Subject to (CVaR auxiliary constraints):
        z_s + profit_s + ζ >= 0    ∀s  [i.e., z_s >= -profit_s - ζ]
        z_s >= 0                   ∀s
        ζ ∈ ℝ   (free variable — interpreted as -VaR)

    Plus all V4 hard constraints (field area, soil suitability, rotation,
    water, labor, fertilizer budgets).

All existing V4 hard constraints are PRESERVED in every mode. The CVaR
formulation only changes the objective function and adds auxiliary variables.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pyomo.environ as pyo

from crop_mix.data.example_data import FarmInputs
from crop_mix.data.rotation_loader import RotationMatrixLoader
from crop_mix.data.risk_scenarios import RiskScenario, RiskScenarioProvider, get_default_provider
from crop_mix.models.optimizer_v4 import OptimizationResultV4
from crop_mix.models.soil_suitability import SoilSuitabilityEngine
from crop_mix.business.risk_analysis import RiskAnalyzer, RiskMetrics, PlanRiskSummary


# Valid planning mode names
MODES = ("max_profit", "balanced", "risk_aware")

# Per-mode risk weights (w = weight on expected profit; (1-w) = weight on CVaR)
MODE_WEIGHTS: Dict[str, float] = {
    "max_profit": 1.0,   # No CVaR penalty
    "balanced":   0.5,   # Equal emphasis
    "risk_aware": 0.2,   # Dominant CVaR penalty
}

# Arabic display names for each mode
MODE_ARABIC: Dict[str, str] = {
    "max_profit": "أقصى ربح",
    "balanced":   "متوازن",
    "risk_aware": "واعٍ للمخاطر",
}

# CVaR confidence level
CVaR_ALPHA = 0.95


@dataclass
class RiskAwareOptimizationResult:
    """Output of the CVaR-aware optimizer for one planning mode.

    Extends OptimizationResultV4 with CVaR-specific fields.
    """

    # Core V4 fields
    mode: str                          # 'max_profit', 'balanced', or 'risk_aware'
    mode_arabic: str                   # Arabic display name
    weight_profit: float               # w (weight on expected profit)
    alpha: float                       # CVaR confidence level (e.g., 0.95)

    status: str
    is_feasible: bool
    crop_allocation: Dict[str, Dict[str, float]]   # field -> crop -> ha
    field_land_used: Dict[str, float]
    field_land_limits: Dict[str, float]
    total_land_used: float
    total_water_used: float
    water_budget_limit: float
    total_labor_used: float
    labor_budget_limit: float
    total_fertilizer_used: float
    fertilizer_budget_limit: float
    total_expected_revenue: float
    total_production_cost: float
    total_labor_cost: float
    total_fertilizer_cost: float
    expected_profit: float             # Deterministic expected profit (scenario-weighted)

    # CVaR-specific fields
    var_95: float                      # Value at Risk (95%)
    cvar_95: float                     # Conditional Value at Risk (95%)
    std_dev: float                     # Profit standard deviation across scenarios
    min_scenario_profit: float         # Worst-case scenario profit
    max_scenario_profit: float         # Best-case scenario profit
    scenario_profits: List[Dict]       # Per-scenario profit list

    # V4 constraint matrices
    soil_suitability_matrix: Dict[Tuple[str, str], int]
    rotation_suitability_matrix: Dict[Tuple[str, str], int]
    field_previous_crops: Dict[str, Optional[str]]
    solver_name: str = "highs"


class RiskAwareOptimizer:
    """CVaR-augmented crop mix optimizer.

    Builds a single Pyomo LP that includes both the standard V4 constraints
    AND the Rockafellar-Uryasev auxiliary CVaR variables, then solves it using
    the HiGHS LP solver.

    The optimizer is instantiated once and the `solve()` method can be called
    multiple times with different modes.
    """

    def __init__(
        self,
        solver_name: str = "appsi_highs",
        rotation_excel_path: str = "data/crop_rotation_matrix_v10_corrected.xlsx",
        rotation_loader: Optional[RotationMatrixLoader] = None,
        scenario_provider: Optional[RiskScenarioProvider] = None,
    ):
        self.solver_name = solver_name
        self.soil_engine = SoilSuitabilityEngine()
        self.rotation_loader = rotation_loader or RotationMatrixLoader(excel_path=rotation_excel_path)
        self.scenario_provider = scenario_provider or get_default_provider()
        self._scenarios: List[RiskScenario] = self.scenario_provider.get_scenarios()

    def solve(
        self,
        farm_inputs: FarmInputs,
        mode: str = "balanced",
        apply_soil_suitability: bool = True,
    ) -> RiskAwareOptimizationResult:
        """Formulate and solve the CVaR-augmented crop mix LP.

        Args:
            farm_inputs: Farm inputs (crops, fields, budgets) — same as V4.
            mode: Planning mode — 'max_profit', 'balanced', or 'risk_aware'.
            apply_soil_suitability: Whether to enforce soil suitability constraints.
                Should be True for Season 1 / current season; False for future seasons.

        Returns:
            RiskAwareOptimizationResult including allocation, CVaR metrics, and
            per-scenario profit breakdown.

        Raises:
            ValueError: If mode is not a valid planning mode.
        """
        if mode not in MODES:
            raise ValueError(f"Invalid mode '{mode}'. Valid options: {MODES}")

        w = MODE_WEIGHTS[mode]
        crop_names = list(farm_inputs.crops.keys())
        field_names = list(farm_inputs.fields.keys())
        scenario_ids = [s.scenario_id for s in self._scenarios]

        if not field_names:
            raise ValueError("FarmInputs must contain at least one field.")
        if not crop_names:
            raise ValueError("FarmInputs must contain at least one crop.")

        self.rotation_loader.validate_optimization_crops(crop_names)

        # Build soil suitability and rotation matrices (same as V4)
        if apply_soil_suitability:
            soil_matrix = self.soil_engine.calculate_suitability_matrix(farm_inputs)
        else:
            soil_matrix = {(f, c): 1 for f in field_names for c in crop_names}

        rotation_matrix: Dict[Tuple[str, str], int] = {}
        field_prev_crops: Dict[str, Optional[str]] = {}
        for f_name, f_obj in farm_inputs.fields.items():
            prev_c = f_obj.previous_crop
            field_prev_crops[f_name] = prev_c
            for c_name in crop_names:
                rot_fit = self.rotation_loader.get_rotation_suitability(prev_c, c_name)
                rotation_matrix[(f_name, c_name)] = rot_fit

        field_areas = {f: f_obj.area for f, f_obj in farm_inputs.fields.items()}

        # Build base resource requirement dicts
        water_req = {c: crop.water_requirement for c, crop in farm_inputs.crops.items()}
        labor_req = {c: crop.labor_requirement for c, crop in farm_inputs.crops.items()}
        fert_req = {c: crop.fertilizer_requirement for c, crop in farm_inputs.crops.items()}
        revenue_per_ha = {c: crop.revenue_per_hectare for c, crop in farm_inputs.crops.items()}
        prod_cost_per_ha = {c: crop.production_cost for c, crop in farm_inputs.crops.items()}
        labor_cost_per_ha = {c: crop.labor_cost_per_hectare for c, crop in farm_inputs.crops.items()}
        fert_cost_per_ha = {c: crop.fertilizer_cost_per_hectare for c, crop in farm_inputs.crops.items()}

        # Build scenario-level net profit per hectare: pi[scenario_id][crop_name]
        analyzer = RiskAnalyzer(farm_inputs, self.scenario_provider)
        pi: Dict[str, Dict[str, float]] = {}
        prob: Dict[str, float] = {}
        for s in self._scenarios:
            pi[s.scenario_id] = analyzer.get_scenario_profit_per_ha(s)
            prob[s.scenario_id] = s.probability

        alpha = CVaR_ALPHA
        one_minus_alpha = 1.0 - alpha  # 0.05

        # ---------------------------------------------------------------
        # Build Pyomo Model
        # ---------------------------------------------------------------
        model = pyo.ConcreteModel(name=f"CropMixRiskAware_{mode}")

        model.FIELDS = pyo.Set(initialize=field_names)
        model.CROPS = pyo.Set(initialize=crop_names)
        model.SCENARIOS = pyo.Set(initialize=scenario_ids)

        # Decision variables
        model.x = pyo.Var(model.FIELDS, model.CROPS, domain=pyo.NonNegativeReals)

        # CVaR auxiliary variables (only added when CVaR term is active)
        if w < 1.0:
            model.zeta = pyo.Var(domain=pyo.Reals)  # -VaR (free variable)
            model.z = pyo.Var(model.SCENARIOS, domain=pyo.NonNegativeReals)  # Excess loss
        else:
            # For max_profit mode, we still need placeholders for objective consistency
            model.zeta = pyo.Param(initialize=0.0)
            model.z = pyo.Param(model.SCENARIOS, initialize=0.0)

        # ---------------------------------------------------------------
        # Objective Function
        # ---------------------------------------------------------------
        # profit_s = Σ_{f,c} x[f,c] * pi[s][c]  (linear expression in x)
        # E[profit] = Σ_s p_s * profit_s = Σ_{f,c} x[f,c] * Σ_s p_s * pi[s][c]
        # CVaR = ζ + (1/(1-α)) * Σ_s p_s * z_s
        # Objective: maximize w * E[profit] - (1-w) * CVaR

        # Precompute expected profit coefficient per (field, crop)
        # Note: coefficient is the same for all fields (no field-specific per-ha adjustment)
        expected_profit_coef: Dict[str, float] = {
            c: sum(prob[s_id] * pi[s_id][c] for s_id in scenario_ids)
            for c in crop_names
        }

        if w < 1.0:
            def objective_rule(m):
                # E[profit] component
                ep = sum(
                    expected_profit_coef[c] * m.x[f, c]
                    for f in m.FIELDS
                    for c in m.CROPS
                )
                # CVaR component: ζ + (1/(1-α)) * Σ_s p_s * z_s
                cvar_term = m.zeta + (1.0 / one_minus_alpha) * sum(
                    prob[s_id] * m.z[s_id] for s_id in scenario_ids
                )
                return w * ep - (1.0 - w) * cvar_term

            model.objective = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

            # CVaR auxiliary constraints: z_s >= -profit_s - ζ  (i.e., z_s + profit_s + ζ >= 0)
            def cvar_cut_rule(m, s_id):
                profit_s = sum(pi[s_id][c] * m.x[f, c] for f in m.FIELDS for c in m.CROPS)
                return m.z[s_id] + profit_s + m.zeta >= 0.0

            model.cvar_cuts = pyo.Constraint(model.SCENARIOS, rule=cvar_cut_rule)

        else:
            # Pure max profit — no CVaR term
            def objective_rule_pure(m):
                return sum(
                    expected_profit_coef[c] * m.x[f, c]
                    for f in m.FIELDS
                    for c in m.CROPS
                )

            model.objective = pyo.Objective(rule=objective_rule_pure, sense=pyo.maximize)

        # ---------------------------------------------------------------
        # V4 Hard Constraints (identical to CropMixOptimizerV4.solve)
        # ---------------------------------------------------------------

        # (a) Per-field area constraint
        def field_area_rule(m, f):
            return sum(m.x[f, c] for c in m.CROPS) <= field_areas[f]

        model.field_area_con = pyo.Constraint(model.FIELDS, rule=field_area_rule)

        # (b) Soil suitability constraint
        if apply_soil_suitability:
            def soil_rule(m, f, c):
                return m.x[f, c] <= soil_matrix.get((f, c), 0) * field_areas[f]

            model.soil_con = pyo.Constraint(model.FIELDS, model.CROPS, rule=soil_rule)

        # (c) Crop rotation constraint
        def rotation_rule(m, f, c):
            return m.x[f, c] <= rotation_matrix.get((f, c), 0) * field_areas[f]

        model.rotation_con = pyo.Constraint(model.FIELDS, model.CROPS, rule=rotation_rule)

        # (d) Water budget constraint
        def water_rule(m):
            return sum(water_req[c] * m.x[f, c] for f in m.FIELDS for c in m.CROPS) <= farm_inputs.water_budget

        model.water_con = pyo.Constraint(rule=water_rule)

        # (e) Labor budget constraint
        def labor_rule(m):
            return sum(labor_req[c] * m.x[f, c] for f in m.FIELDS for c in m.CROPS) <= farm_inputs.labor_budget

        model.labor_con = pyo.Constraint(rule=labor_rule)

        # (f) Fertilizer budget constraint
        def fert_rule(m):
            return sum(fert_req[c] * m.x[f, c] for f in m.FIELDS for c in m.CROPS) <= farm_inputs.fertilizer_budget

        model.fert_con = pyo.Constraint(rule=fert_rule)

        # ---------------------------------------------------------------
        # Solve
        # ---------------------------------------------------------------
        solver = self._get_solver()
        results_obj = solver.solve(model)

        status_str = str(results_obj.solver.status) if hasattr(results_obj.solver, "status") else "unknown"
        term_cond = (
            str(results_obj.solver.termination_condition)
            if hasattr(results_obj.solver, "termination_condition")
            else str(results_obj.termination_condition) if hasattr(results_obj, "termination_condition") else "optimal"
        )

        is_feasible = (
            term_cond.lower() in ("optimal", "feasible")
            or status_str.lower() in ("ok", "optimal")
        )

        # ---------------------------------------------------------------
        # Extract allocation
        # ---------------------------------------------------------------
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

        # ---------------------------------------------------------------
        # Risk analysis on the resulting allocation
        # ---------------------------------------------------------------
        risk_metrics = analyzer.analyze(crop_allocation)

        # Build scenario profits list for API response
        scenario_profits_list = []
        for sp in risk_metrics.scenarios:
            scenario_profits_list.append({
                "scenario_id": sp.scenario_id,
                "scenario_name": sp.scenario_name,
                "scenario_name_arabic": sp.scenario_name_arabic,
                "category": sp.scenario_category,
                "severity": sp.scenario_severity,
                "probability": sp.probability,
                "net_profit": sp.net_profit,
            })

        return RiskAwareOptimizationResult(
            mode=mode,
            mode_arabic=MODE_ARABIC[mode],
            weight_profit=w,
            alpha=alpha,
            status=term_cond,
            is_feasible=is_feasible,
            crop_allocation=crop_allocation,
            field_land_used={f: round(v, 4) for f, v in field_land_used.items()},
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
            expected_profit=risk_metrics.expected_profit,
            var_95=risk_metrics.var_95,
            cvar_95=risk_metrics.cvar_95,
            std_dev=risk_metrics.std_dev,
            min_scenario_profit=risk_metrics.min_profit,
            max_scenario_profit=risk_metrics.max_profit,
            scenario_profits=scenario_profits_list,
            soil_suitability_matrix=soil_matrix,
            rotation_suitability_matrix=rotation_matrix,
            field_previous_crops=field_prev_crops,
            solver_name=self.solver_name,
        )

    def _get_solver(self):
        """Instantiate and return the HiGHS LP solver (same as V4)."""
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
