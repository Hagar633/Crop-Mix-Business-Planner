"""Standalone execution script to run Version 1 Crop Mix Optimizer."""

import sys
from pathlib import Path

# Add src to sys.path
src_dir = Path(__file__).resolve().parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from crop_mix.data.example_data import get_example_farm_data
from crop_mix.models.optimizer_v1 import CropMixOptimizerV1


def main():
    print("=" * 60)
    print("      CROP MIX OPTIMIZATION SYSTEM (VERSION 1)")
    print("=" * 60)

    # 1. Load sample dataset
    farm_inputs = get_example_farm_data()
    print("\n--- FARM INPUTS ---")
    print(f"Total Field Area Available: {farm_inputs.field_area:,.2f} hectares")
    print(f"Total Water Budget Available: {farm_inputs.water_budget:,.2f} m^3\n")

    df_crops = farm_inputs.to_dataframe()
    print("Crops Dataset:")
    print(df_crops.to_string())

    # 2. Run Pyomo + HiGHS optimizer
    print("\n--- RUNNING OPTIMIZER (Pyomo + HiGHS) ---")
    optimizer = CropMixOptimizerV1()
    result = optimizer.solve(farm_inputs)

    # 3. Display results
    print("\n--- OPTIMIZATION RESULTS ---")
    print(f"Solver Status       : {result.status}")
    print(f"Is Feasible         : {result.is_feasible}")
    print(f"Expected Net Profit : ${result.expected_profit:,.2f}")
    print(f"Total Land Used     : {result.total_land_used:,.2f} / {result.field_area_limit:,.2f} ha")
    print(f"Total Water Used    : {result.total_water_used:,.2f} / {result.water_budget_limit:,.2f} m^3")

    print("\nOptimal Crop Allocation (hectares):")
    for crop, ha in result.crop_allocation.items():
        profit_contribution = ha * farm_inputs.crops[crop].profit_per_hectare
        water_consumed = ha * farm_inputs.crops[crop].water_requirement
        print(
            f"  - {crop:<12}: {ha:>8.2f} ha  "
            f"(Profit: ${profit_contribution:>10,.2f}, Water: {water_consumed:>10,.2f} m^3)"
        )
    print("=" * 60)


if __name__ == "__main__":
    main()
