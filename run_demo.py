"""Standalone execution script to run Version 3 Crop Mix Optimizer."""

import sys
from pathlib import Path

# Add src to sys.path
src_dir = Path(__file__).resolve().parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from crop_mix.data.example_data import get_example_farm_data
from crop_mix.models.soil_suitability import SoilSuitabilityEngine
from crop_mix.models.optimizer_v3 import CropMixOptimizerV3


def main():
    print("=" * 80)
    print("      CROP MIX OPTIMIZATION SYSTEM (VERSION 3 - FIELD SOIL SUITABILITY)")
    print("=" * 80)

    # Load dataset
    farm_inputs = get_example_farm_data()

    # 1. Field Soil Measurements
    print("\n1. FIELD SOIL MEASUREMENTS (SYNTHETIC TEST/DEMO VALUES)")
    print("-" * 80)
    df_fields = farm_inputs.fields_to_dataframe()
    print(df_fields.to_string())

    # 2. Crop Soil Requirements
    print("\n\n2. CROP SOIL REQUIREMENTS (SYNTHETIC TEST/DEMO VALUES)")
    print("-" * 80)
    print(f"{'Crop':<10} | {'pH Range':<12} | {'Max EC':<8} | {'Suitable Soil Textures'}")
    print("-" * 80)
    for crop_name, crop in farm_inputs.crops.items():
        req = crop.soil_requirement
        if req:
            ph_range = f"{req.min_ph:.1f} - {req.max_ph:.1f}"
            textures = ", ".join(req.suitable_textures)
            print(f"{crop_name:<10} | {ph_range:<12} | {req.max_ec:<8.1f} | {textures}")
        else:
            print(f"{crop_name:<10} | {'Any':<12} | {'Any':<8} | Any")

    # 3. Field x Crop Suitability Matrix
    print("\n\n3. FIELD × CROP SOIL SUITABILITY MATRIX (1 = Suitable, 0 = Unsuitable)")
    print("-" * 80)
    engine = SoilSuitabilityEngine()
    df_suitability = engine.get_suitability_dataframe(farm_inputs)
    print(df_suitability.to_string())

    # Solve V3 Optimization Problem
    optimizer = CropMixOptimizerV3()
    result = optimizer.solve(farm_inputs)

    # 4. Optimal Allocation by Field
    print("\n\n4. OPTIMAL ALLOCATION BY FIELD (hectares)")
    print("-" * 80)
    for field_name, allocations in result.crop_allocation.items():
        field_limit = result.field_land_limits[field_name]
        field_used = result.field_land_used[field_name]
        print(f"\n  [{field_name}] (Used: {field_used:.2f} / {field_limit:.2f} ha):")
        allocated_any = False
        for crop_name, ha in allocations.items():
            if ha > 0:
                allocated_any = True
                profit_ha = farm_inputs.crops[crop_name].profit_per_hectare
                print(f"    * {crop_name:<12}: {ha:>8.2f} ha  (Net Profit: ${ha * profit_ha:>10,.2f})")
        if not allocated_any:
            print("    * No crops allocated to this field.")

    # Resource Usages (Items 5 - 8)
    print("\n\nRESOURCE USAGE SUMMARY")
    print("-" * 80)
    print(f"5. Total Land Used       : {result.total_land_used:,.2f} / {farm_inputs.field_area:,.2f} hectares")
    print(f"6. Total Water Used      : {result.total_water_used:,.2f} / {result.water_budget_limit:,.2f} m^3")
    print(f"7. Total Labor Used      : {result.total_labor_used:,.2f} / {result.labor_budget_limit:,.2f} hours")
    print(f"8. Total Fertilizer Used : {result.total_fertilizer_used:,.2f} / {result.fertilizer_budget_limit:,.2f} kg")

    # Financial Breakdown (Items 9 - 13)
    print("\n\nFINANCIAL SUMMARY")
    print("-" * 80)
    print(f"9.  Total Expected Revenue    : ${result.total_expected_revenue:,.2f}")
    print(f"10. Total Production Cost     : ${result.total_production_cost:,.2f}")
    print(f"11. Total Labor Cost          : ${result.total_labor_cost:,.2f}")
    print(f"12. Total Fertilizer Cost     : ${result.total_fertilizer_cost:,.2f}")
    print(f"13. TOTAL EXPECTED NET PROFIT : ${result.expected_profit:,.2f}")
    print("=" * 80)


if __name__ == "__main__":
    main()
