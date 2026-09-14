"""CVaR-Based Risk Analysis Engine for Crop Mix Business Planner.

This module implements the Conditional Value at Risk (CVaR) risk analysis layer
on top of the existing V4 deterministic crop mix optimizer. It computes
scenario-level profit distributions and standard financial risk metrics
for a given crop allocation plan.

CVaR Formulation (Rockafellar-Uryasev):
    Given a loss distribution L_s = -Profit_s and confidence level α:
    VaR_α   = α-quantile of loss distribution
    CVaR_α  = E[L | L >= VaR_α]  (expected loss in the tail)

    For a discrete probability distribution with scenarios s ∈ S:
    CVaR_α = (1 / (1-α)) * Σ_{s: L_s >= VaR_α} p_s * L_s  [adjusted for boundary]

Data flow:
    FarmInputs + crop_allocation → scenario profits → RiskMetrics (CVaR, VaR, std)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from crop_mix.data.example_data import FarmInputs
from crop_mix.data.risk_scenarios import RiskScenario, RiskScenarioProvider, get_default_provider


@dataclass
class ScenarioProfit:
    """Net profit realized in a single risk scenario given a crop allocation."""

    scenario_id: str
    scenario_name: str
    scenario_name_arabic: str
    scenario_category: str
    scenario_severity: str
    probability: float
    net_profit: float  # Scenario-specific net profit in EGP


@dataclass
class RiskMetrics:
    """Financial risk metrics for a crop allocation plan across all scenarios.

    Attributes:
        expected_profit: Probability-weighted average net profit across all scenarios.
        var_95: Value-at-Risk at 95% confidence. The profit level not exceeded by
            the worst 5% of scenarios (i.e., 5% of scenarios produce profit <= VaR).
        cvar_95: Conditional Value-at-Risk (CVaR / Expected Shortfall) at 95% confidence.
            The average profit in the worst 5% of scenarios.
        min_profit: Worst-case scenario profit.
        max_profit: Best-case scenario profit.
        std_dev: Standard deviation of scenario profits.
        scenarios: Per-scenario profit breakdown.
    """

    expected_profit: float
    var_95: float
    cvar_95: float
    min_profit: float
    max_profit: float
    std_dev: float
    scenarios: List[ScenarioProfit]


@dataclass
class PlanRiskSummary:
    """Complete risk summary for a single crop allocation plan.

    Attributes:
        plan_type: 'max_profit', 'balanced', or 'risk_aware'.
        plan_type_arabic: Arabic display name for the plan type.
        allocation: crop_allocation dict - field -> crop -> hectares allocated.
        metrics: Computed risk metrics (CVaR, VaR, expected profit, etc.).
    """

    plan_type: str
    plan_type_arabic: str
    allocation: Dict[str, Dict[str, float]]
    metrics: RiskMetrics


class RiskAnalyzer:
    """Computes CVaR-based risk metrics for a given crop allocation.

    This class is a pure analytical layer. It takes a fixed crop allocation
    (from any source — the V4 optimizer, the risk-aware optimizer, or manually
    specified) and evaluates its performance across all risk scenarios.

    It does NOT run any optimization. It only analyzes existing allocations.

    DISCLAIMER: Most scenario probabilities and multipliers are synthetic
    demonstration values. The market downturn is calibrated from offline
    FAOSTAT producer-price data; see risk_scenarios.py for the full disclaimer.
    """

    ALPHA = 0.95  # CVaR confidence level (95%)

    def __init__(
        self,
        farm_inputs: FarmInputs,
        provider: Optional[RiskScenarioProvider] = None,
    ):
        self.farm_inputs = farm_inputs
        self.provider = provider or get_default_provider()
        self._scenarios: List[RiskScenario] = self.provider.get_scenarios()

    @property
    def scenarios(self) -> List[RiskScenario]:
        return self._scenarios

    # ------------------------------------------------------------------
    # Core profit calculation
    # ------------------------------------------------------------------

    def compute_scenario_profit(
        self,
        allocation: Dict[str, Dict[str, float]],
        scenario: RiskScenario,
    ) -> float:
        """Compute total farm net profit under a specific scenario.

        Args:
            allocation: crop_allocation dict (field -> crop -> area in ha).
            scenario: The risk scenario with per-crop multipliers.

        Returns:
            Total net profit (EGP) under the given scenario.
        """
        total_profit = 0.0

        for field_name, crop_areas in allocation.items():
            for crop_name, area in crop_areas.items():
                if area <= 0.0:
                    continue

                crop = self.farm_inputs.crops.get(crop_name)
                if crop is None:
                    continue

                profile = scenario.get_crop_profile(crop_name)

                # Apply scenario multipliers to each cost/revenue component
                scenario_revenue_per_ha = (
                    crop.expected_yield * profile.yield_multiplier
                    * crop.price * profile.price_multiplier
                )
                scenario_prod_cost_per_ha = crop.production_cost * profile.production_cost_multiplier
                scenario_labor_cost_per_ha = crop.labor_cost_per_hectare * profile.labor_cost_multiplier
                scenario_fert_cost_per_ha = crop.fertilizer_cost_per_hectare * profile.fertilizer_cost_multiplier

                scenario_net_profit_per_ha = (
                    scenario_revenue_per_ha
                    - scenario_prod_cost_per_ha
                    - scenario_labor_cost_per_ha
                    - scenario_fert_cost_per_ha
                )

                total_profit += area * scenario_net_profit_per_ha

        return total_profit

    # ------------------------------------------------------------------
    # Risk metrics computation
    # ------------------------------------------------------------------

    def analyze(self, allocation: Dict[str, Dict[str, float]]) -> RiskMetrics:
        """Compute complete risk metrics for the given crop allocation.

        Args:
            allocation: crop_allocation dict (field -> crop -> area in ha).

        Returns:
            RiskMetrics with expected_profit, VaR, CVaR, std_dev, and
            per-scenario profit breakdown.
        """
        scenario_profits: List[ScenarioProfit] = []

        for s in self._scenarios:
            profit = self.compute_scenario_profit(allocation, s)
            scenario_profits.append(
                ScenarioProfit(
                    scenario_id=s.scenario_id,
                    scenario_name=s.name,
                    scenario_name_arabic=s.name_arabic,
                    scenario_category=s.risk_category,
                    scenario_severity=s.severity,
                    probability=s.probability,
                    net_profit=round(profit, 2),
                )
            )

        return self._compute_metrics(scenario_profits)

    def _compute_metrics(self, scenario_profits: List[ScenarioProfit]) -> RiskMetrics:
        """Compute statistical risk metrics from the scenario profit distribution."""
        # Expected profit (probability-weighted)
        expected = sum(sp.probability * sp.net_profit for sp in scenario_profits)

        # Sort by profit ascending (worst first) for VaR / CVaR computation
        sorted_by_profit = sorted(scenario_profits, key=lambda sp: sp.net_profit)

        # VaR at alpha = 95%: find profit at the (1-alpha) = 5% tail
        # The loss distribution: loss_s = -profit_s
        # VaR_alpha (of profit) = -VaR_alpha(of loss)
        # = the profit level not exceeded by the worst (1-alpha) fraction
        alpha = self.ALPHA
        tail_prob = 1.0 - alpha  # 0.05

        # Walk through scenarios from worst profit upward until cumulative
        # probability >= tail_prob to find VaR boundary
        cumulative_prob = 0.0
        var_95 = sorted_by_profit[0].net_profit  # worst case as default
        for sp in sorted_by_profit:
            cumulative_prob += sp.probability
            var_95 = sp.net_profit
            if cumulative_prob >= tail_prob - 1e-9:
                break

        # CVaR at alpha = 95%: E[profit | profit <= VaR_95]
        # Using the precise Rockafellar-Uryasev formula for discrete distributions:
        # CVaR_α = (1/(1-α)) * sum over scenarios where profit <= VaR of p_s * profit_s
        #          + adjustment for boundary case
        tail_total_prob = 0.0
        tail_weighted_profit = 0.0
        for sp in sorted_by_profit:
            if sp.net_profit <= var_95 + 1e-6:
                tail_total_prob += sp.probability
                tail_weighted_profit += sp.probability * sp.net_profit
            else:
                break

        # Adjust for the boundary case where we may have slightly exceeded tail_prob
        if tail_total_prob > tail_prob + 1e-9:
            # Scale back the boundary scenario contribution proportionally
            excess_prob = tail_total_prob - tail_prob
            # Subtract the excess probability * VaR from the weighted sum
            tail_weighted_profit -= excess_prob * var_95
            tail_total_prob = tail_prob

        cvar_95 = tail_weighted_profit / tail_prob if tail_prob > 0 else var_95

        # Standard deviation
        variance = sum(sp.probability * (sp.net_profit - expected) ** 2 for sp in scenario_profits)
        std_dev = math.sqrt(variance)

        min_profit = min(sp.net_profit for sp in scenario_profits)
        max_profit = max(sp.net_profit for sp in scenario_profits)

        return RiskMetrics(
            expected_profit=round(expected, 2),
            var_95=round(var_95, 2),
            cvar_95=round(cvar_95, 2),
            min_profit=round(min_profit, 2),
            max_profit=round(max_profit, 2),
            std_dev=round(std_dev, 2),
            scenarios=scenario_profits,
        )

    # ------------------------------------------------------------------
    # Convenience: compute scenario profit per ha per crop (for optimizer use)
    # ------------------------------------------------------------------

    def get_scenario_profit_per_ha(self, scenario: RiskScenario) -> Dict[str, float]:
        """Compute net profit per hectare for each crop under the given scenario.

        Returns:
            Dict mapping crop_name -> scenario net profit per ha (EGP/ha).
        """
        result = {}
        for crop_name, crop in self.farm_inputs.crops.items():
            profile = scenario.get_crop_profile(crop_name)
            revenue = crop.expected_yield * profile.yield_multiplier * crop.price * profile.price_multiplier
            prod_cost = crop.production_cost * profile.production_cost_multiplier
            labor_cost = crop.labor_cost_per_hectare * profile.labor_cost_multiplier
            fert_cost = crop.fertilizer_cost_per_hectare * profile.fertilizer_cost_multiplier
            result[crop_name] = revenue - prod_cost - labor_cost - fert_cost
        return result
