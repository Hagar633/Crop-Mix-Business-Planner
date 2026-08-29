"""Internship 4B Phase 1: Financial Projection Layer for Crop Mix Business Planner.

Consumes the crop mix recommendations from 4A optimization results and calculates field-level
and farm-level financial projections (revenue, costs, net profit, profit/ha, profit margin).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from crop_mix.data.example_data import FarmInputs, CropParameters
from crop_mix.models.optimizer_v4 import OptimizationResultV4


@dataclass
class FieldCropFinancial:
    """Financial projection breakdown for a single field and crop combination."""

    field_name: str
    crop_name: str
    allocated_area: float  # Hectares (ha)
    expected_revenue: float  # $
    production_cost: float  # $
    labor_cost: float  # $
    fertilizer_cost: float  # $
    total_cost: float  # $
    net_profit: float  # $
    profit_per_hectare: float  # $/ha
    profit_margin: float  # Ratio (e.g. 0.25 for 25%), 0.0 if expected_revenue is 0


@dataclass
class FarmFinancialSummary:
    """Aggregated farm-level financial summary."""

    total_area: float  # Total allocated hectares across all fields (ha)
    total_expected_revenue: float  # $
    total_production_cost: float  # $
    total_labor_cost: float  # $
    total_fertilizer_cost: float  # $
    total_cost: float  # $
    total_expected_net_profit: float  # $
    overall_profit_margin: float  # Ratio, 0.0 if total_expected_revenue is 0


@dataclass
class FinancialProjectionResult:
    """Complete result object containing field-level financial projections and farm summary."""

    field_projections: Dict[str, Dict[str, FieldCropFinancial]]  # field_name -> crop_name -> FieldCropFinancial
    farm_summary: FarmFinancialSummary


class FinancialProjection:
    """Financial projection engine for Internship 4B.

    Consumes FarmInputs and OptimizationResultV4 to calculate detailed financial breakdowns.
    Does NOT depend on Pyomo or solver libraries.
    """

    def calculate(
        self, farm_inputs: FarmInputs, result_v4: OptimizationResultV4
    ) -> FinancialProjectionResult:
        """Calculate field-level and farm-level financial projections.

        Args:
            farm_inputs: Input dataset containing crop parameters and field definitions.
            result_v4: Optimization result output from V4 optimizer.

        Returns:
            FinancialProjectionResult containing per-field breakdowns (where allocated_area > 0)
            and overall farm financial summary.
        """
        field_projections: Dict[str, Dict[str, FieldCropFinancial]] = {}

        total_area = 0.0
        total_revenue = 0.0
        total_prod_cost = 0.0
        total_labor_cost = 0.0
        total_fert_cost = 0.0

        for field_name, crop_allocations in result_v4.crop_allocation.items():
            field_projections[field_name] = {}
            for crop_name, area in crop_allocations.items():
                if area <= 0.0:
                    # Filter out zero allocation entries
                    continue

                crop_param: CropParameters = farm_inputs.crops[crop_name]

                # Reuse financial parameters directly from CropParameters
                rev = area * crop_param.expected_yield * crop_param.price
                prod_c = area * crop_param.production_cost
                labor_c = area * crop_param.labor_cost_per_hectare
                fert_c = area * crop_param.fertilizer_cost_per_hectare

                tot_c = prod_c + labor_c + fert_c
                net_p = rev - tot_c

                profit_per_ha = net_p / area if area > 0 else 0.0
                margin = net_p / rev if rev > 0 else 0.0

                proj = FieldCropFinancial(
                    field_name=field_name,
                    crop_name=crop_name,
                    allocated_area=round(area, 4),
                    expected_revenue=round(rev, 2),
                    production_cost=round(prod_c, 2),
                    labor_cost=round(labor_c, 2),
                    fertilizer_cost=round(fert_c, 2),
                    total_cost=round(tot_c, 2),
                    net_profit=round(net_p, 2),
                    profit_per_hectare=round(profit_per_ha, 2),
                    profit_margin=round(margin, 4),
                )
                field_projections[field_name][crop_name] = proj

                total_area += area
                total_revenue += rev
                total_prod_cost += prod_c
                total_labor_cost += labor_c
                total_fert_cost += fert_c

        total_tot_cost = total_prod_cost + total_labor_cost + total_fert_cost
        total_net_profit = total_revenue - total_tot_cost
        overall_margin = total_net_profit / total_revenue if total_revenue > 0 else 0.0

        farm_summary = FarmFinancialSummary(
            total_area=round(total_area, 4),
            total_expected_revenue=round(total_revenue, 2),
            total_production_cost=round(total_prod_cost, 2),
            total_labor_cost=round(total_labor_cost, 2),
            total_fertilizer_cost=round(total_fert_cost, 2),
            total_cost=round(total_tot_cost, 2),
            total_expected_net_profit=round(total_net_profit, 2),
            overall_profit_margin=round(overall_margin, 4),
        )

        return FinancialProjectionResult(
            field_projections=field_projections,
            farm_summary=farm_summary,
        )
