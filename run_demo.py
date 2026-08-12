"""Standalone execution script to run Version 2 Crop Mix Optimizer."""

import sys
from pathlib import Path

# Add src to sys.path
src_dir = Path(__file__).resolve().parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from crop_mix.data.example_data import get_example_farm_data
from crop_mix.models.optimizer_v2 import CropMixOptimizerV2


def main():
    print("=" * 75)
    print("      CROP MIX OPTIMIZATION SYSTEM (VERSION 2 - LABOR & FERTILIZER)")
    print("=" * 75)

    # 1. Load sample dataset with synthetic labor/fertilizer test parameters
    farm_inputs = get_example_farm_data()
    print("\n--- FARM RESOURCE BUDGETS (INPUTS) ---")
    print(f"  Field Area Available     : {farm_inputs.field_area:,.2f} hectares")
    print(f"  Water Budget Available   : {farm_inputs.water_budget:,.2f} m^3")
    print(f"  Labor Budget Available   : {farm_inputs.labor_budget:,.2f} hours (TEST/DEMO VALUE)")
    print(f"  Fertilizer Budget Avail. : {farm_inputs.fertilizer_budget:,.2f} kg (TEST/DEMO VALUE)\n")

    # 2. Display Per-Hectare Crop Financial & Requirement Parameters
    print("--- CROP PARAMETERS (PER HECTARE) ---")
    print(f"{'Crop':<10} | {'Rev ($/ha)':<11} | {'ProdCost':<9} | {'LaborCost':<9} | {'FertCost':<9} | {'NetProfit':<10}")
    print("-" * 75)
    for name, crop in farm_inputs.crops.items():
        print(
            f"{name:<10} | ${crop.revenue_per_hectare:>10,.2f} | "
            f"${crop.production_cost:>8,.2f} | ${crop.labor_cost_per_hectare:>8,.2f} | "
            f"${crop.fertilizer_cost_per_hectare:>8,.2f} | ${crop.profit_per_hectare:>9,.2f}"
        )

    # 3. Run Pyomo + HiGHS continuous LP optimizer V2
    print("\n--- RUNNING OPTIMIZER V2 (Pyomo + HiGHS Continuous LP) ---")
    optimizer = CropMixOptimizerV2()
    result = optimizer.solve(farm_inputs)

    # 4. Display Results
    print("\n--- OPTIMIZATION RESULTS ---")
    print(f"Solver Status            : {result.status}")
    print(f"Is Feasible              : {result.is_feasible}")
    print("-" * 75)
    print("FINANCIAL SUMMARY:")
    print(f"  Total Expected Revenue : ${result.total_expected_revenue:,.2f}")
    print(f"  Total Production Cost  : ${result.total_production_cost:,.2f}")
    print(f"  Total Labor Cost       : ${result.total_labor_cost:,.2f}")
    print(f"  Total Fertilizer Cost  : ${result.total_fertilizer_cost:,.2f}")
    print(f"  Total Expected Net Profit : ${result.expected_profit:,.2f}")

    print("\nRESOURCE USAGE METRICS:")
    print(f"  Land Used / Available  : {result.total_land_used:,.2f} / {result.field_area_limit:,.2f} hectares")
    print(f"  Water Used / Available : {result.total_water_used:,.2f} / {result.water_budget_limit:,.2f} m^3")
    print(f"  Labor Used / Available : {result.total_labor_used:,.2f} / {result.labor_budget_limit:,.2f} hours")
    print(f"  Fertilizer Used / Avail: {result.total_fertilizer_used:,.2f} / {result.fertilizer_budget_limit:,.2f} kg")

    print("\nOPTIMAL CROP ALLOCATION (hectares):")
    for crop, ha in result.crop_allocation.items():
        crop_param = farm_inputs.crops[crop]
        profit_contrib = ha * crop_param.profit_per_hectare
        print(
            f"  - {crop:<12}: {ha:>8.2f} ha  "
            f"(Net Profit Contribution: ${profit_contrib:>10,.2f})"
        )
    print("=" * 75)


if __name__ == "__main__":
    main()
