"""Standalone execution script to run Version 4 Crop Mix Optimizer and Internship 4B Financial Projection."""

import sys
from pathlib import Path

# Add src to sys.path
src_dir = Path(__file__).resolve().parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from crop_mix.data.example_data import get_example_farm_data
from crop_mix.models.optimizer_v4 import CropMixOptimizerV4
from crop_mix.business.financial_projection import FinancialProjection


def main():
    print("=" * 85)
    print("  CROP MIX OPTIMIZATION SYSTEM (VERSION 4 - CROP ROTATION & SOIL SUITABILITY)")
    print("=" * 85)

    # Load dataset
    farm_inputs = get_example_farm_data()

    # 1. Field Soil Measurements & Previous Crop History
    print("\n1. FIELD DATA & HISTORICAL PREVIOUS CROPS (TEST/DEMO DATA)")
    print("-" * 85)
    df_fields = farm_inputs.fields_to_dataframe()
    print(df_fields.to_string())

    # 2. Crop Soil Requirements
    print("\n\n2. CROP SOIL REQUIREMENTS")
    print("-" * 85)
    print(f"{'Crop':<15} | {'pH Range':<12} | {'Max EC':<8} | {'Suitable Soil Textures'}")
    print("-" * 85)
    for crop_name, crop in farm_inputs.crops.items():
        req = crop.soil_requirement
        if req:
            ph_range = f"{req.min_ph:.1f} - {req.max_ph:.1f}"
            textures = ", ".join(req.suitable_textures)
            print(f"{crop_name:<15} | {ph_range:<12} | {req.max_ec:<8.1f} | {textures}")

    # Solve V4 Optimization Problem (Crop Rotation + Soil Suitability + Budgets)
    optimizer = CropMixOptimizerV4()
    result = optimizer.solve(farm_inputs)

    # 3. Field x Crop Rotation Suitability Matrix
    print("\n\n3. CROP ROTATION SUITABILITY MATRIX BY FIELD (1 = Recommended, 0 = Disallowed)")
    print("-" * 85)
    crop_names = list(farm_inputs.crops.keys())
    print(f"{'Field (Prev Crop)':<28} | " + " | ".join(f"{c:<11}" for c in crop_names))
    print("-" * 85)
    for f_name in farm_inputs.fields.keys():
        prev_c = result.field_previous_crops[f_name] or "None"
        label = f"{f_name} ({prev_c})"
        row_str = f"{label:<28} | " + " | ".join(
            f"{result.rotation_suitability_matrix[(f_name, c)]:^11}" for c in crop_names
        )
        print(row_str)

    # 4. Optimal Allocation by Field
    print("\n\n4. OPTIMAL ALLOCATION BY FIELD (hectares)")
    print("-" * 85)
    for field_name, allocations in result.crop_allocation.items():
        field_limit = result.field_land_limits[field_name]
        field_used = result.field_land_used[field_name]
        prev_c = result.field_previous_crops[field_name] or "None (New/Fallow)"
        print(f"\n  [{field_name}] (Prev Crop: {prev_c}) - (Used: {field_used:.2f} / {field_limit:.2f} ha):")
        allocated_any = False
        for crop_name, ha in allocations.items():
            if ha > 0:
                allocated_any = True
                profit_ha = farm_inputs.crops[crop_name].profit_per_hectare
                print(f"    * {crop_name:<15}: {ha:>8.2f} ha  (Net Profit Contribution: ${ha * profit_ha:>10,.2f})")
        if not allocated_any:
            print("    * No crops allocated to this field.")

    # Resource Usages
    print("\n\nRESOURCE USAGE SUMMARY")
    print("-" * 85)
    print(f"Total Land Used       : {result.total_land_used:,.2f} / {farm_inputs.field_area:,.2f} hectares")
    print(f"Total Water Used      : {result.total_water_used:,.2f} / {result.water_budget_limit:,.2f} m^3")
    print(f"Total Labor Used      : {result.total_labor_used:,.2f} / {result.labor_budget_limit:,.2f} hours")
    print(f"Total Fertilizer Used : {result.total_fertilizer_used:,.2f} / {result.fertilizer_budget_limit:,.2f} kg")

    # Optimization Financial Breakdown
    print("\n\n4A OPTIMIZER FINANCIAL SUMMARY")
    print("-" * 85)
    print(f"Total Expected Revenue    : ${result.total_expected_revenue:,.2f}")
    print(f"Total Production Cost     : ${result.total_production_cost:,.2f}")
    print(f"Total Labor Cost          : ${result.total_labor_cost:,.2f}")
    print(f"Total Fertilizer Cost     : ${result.total_fertilizer_cost:,.2f}")
    print(f"TOTAL EXPECTED NET PROFIT : ${result.expected_profit:,.2f}")
    print("=" * 85)

    # ---------------------------------------------------------------------------------
    # INTERNSHIP 4B - FINANCIAL PROJECTION
    # ---------------------------------------------------------------------------------
    print("\n\n" + "=" * 85)
    print("  INTERNSHIP 4B - FINANCIAL PROJECTION (BUSINESS TRACK)")
    print("=" * 85)

    projection_engine = FinancialProjection()
    fin_result = projection_engine.calculate(farm_inputs, result)

    print("\nFIELD-LEVEL FINANCIAL PROJECTION (TEST/DEMO DATA)")
    print("-" * 85)
    for field_name, crop_map in fin_result.field_projections.items():
        if not crop_map:
            print(f"\n{field_name}")
            print("  (No crops allocated)")
            continue
        print(f"\n{field_name}")
        for crop_name, proj in crop_map.items():
            margin_pct = proj.profit_margin * 100.0
            print(f"    Crop: {crop_name}")
            print(f"    Area: {proj.allocated_area:.2f} ha")
            print(f"    Expected Revenue: ${proj.expected_revenue:,.2f}")
            print(f"    Production Cost: ${proj.production_cost:,.2f}")
            print(f"    Labor Cost: ${proj.labor_cost:,.2f}")
            print(f"    Fertilizer Cost: ${proj.fertilizer_cost:,.2f}")
            print(f"    Total Cost: ${proj.total_cost:,.2f}")
            print(f"    Net Profit: ${proj.net_profit:,.2f}")
            print(f"    Profit / ha: ${proj.profit_per_hectare:,.2f} / ha")
            print(f"    Profit Margin: {margin_pct:.2f}%")

    print("\n" + "-" * 85)
    print("FARM FINANCIAL SUMMARY (TEST/DEMO DATA)")
    print("-" * 85)
    summary = fin_result.farm_summary
    overall_margin_pct = summary.overall_profit_margin * 100.0
    print(f"Total Area: {summary.total_area:.2f} ha")
    print(f"Total Expected Revenue: ${summary.total_expected_revenue:,.2f}")
    print(f"Total Production Cost: ${summary.total_production_cost:,.2f}")
    print(f"Total Labor Cost: ${summary.total_labor_cost:,.2f}")
    print(f"Total Fertilizer Cost: ${summary.total_fertilizer_cost:,.2f}")
    print(f"Total Cost: ${summary.total_cost:,.2f}")
    print(f"Total Expected Net Profit: ${summary.total_expected_net_profit:,.2f}")
    print(f"Overall Profit Margin: {overall_margin_pct:.2f}%")
    print("=" * 85)


if __name__ == "__main__":
    main()
