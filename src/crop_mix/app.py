"""FastAPI web server for Crop Mix Business Planner.

Provides API endpoints for farm optimization, multi-season planning, and serves static web UI.
"""

import os
import math
from pathlib import Path
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from crop_mix.data.example_data import (
    FarmInputs,
    CropParameters,
    FieldParameters,
    CropSoilRequirement,
    get_example_farm_data,
)
from crop_mix.data.ecocrop_db import EcoCropDatabase
from crop_mix.models.soil_suitability import SoilSuitabilityEngine
from crop_mix.models.optimizer_v1 import CropMixOptimizerV1
from crop_mix.models.optimizer_v2 import CropMixOptimizerV2
from crop_mix.models.optimizer_v3 import CropMixOptimizerV3
from crop_mix.models.optimizer_v4 import CropMixOptimizerV4
from crop_mix.data.rotation_loader import RotationMatrixLoader
from crop_mix.data.water_loader import EgyptWaterDataLoader
from crop_mix.data.crop_seasons import (
    get_allowed_seasons,
    get_arabic_crop_name,
    get_canonical_crop_name,
    is_crop_allowed_in_season,
    CROP_ARABIC_NAMES,
)
from crop_mix.business.financial_projection import FinancialProjection
from crop_mix.business.multi_season_planner import MultiSeasonPlanner, SeasonPlan

ecocrop_db = EcoCropDatabase()
rotation_loader = RotationMatrixLoader()
water_loader = EgyptWaterDataLoader()

# Multi-season active session cache
active_multi_season_sessions: Dict[str, MultiSeasonPlanner] = {}


app = FastAPI(
    title="Crop Mix Business Planner API",
    description="Mathematical optimization REST API for agricultural crop mix planning.",
    version="0.2.0",
)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Pydantic Request Models ---

class SoilRequirementSchema(BaseModel):
    min_ph: float = 6.0
    max_ph: float = 8.0
    max_ec: float = 2.5
    suitable_textures: List[str] = ["Loam", "Clay", "Silt", "Sandy", "Sandy Loam"]


class CropSchema(BaseModel):
    name: str
    expected_yield: float = Field(..., gt=0, description="Yield in metric tons/ha")
    price: float = Field(..., ge=0, description="Price in EGP/ton")
    production_cost: float = Field(..., ge=0, description="Base production cost EGP/ha")
    water_requirement: float = Field(..., ge=0, description="Water requirement m^3/ha")
    labor_requirement: float = Field(0.0, ge=0, description="Labor hours/ha")
    labor_cost_per_hour: float = Field(20.0, ge=0, description="Labor cost EGP/hour")
    fertilizer_requirement: float = Field(0.0, ge=0, description="Fertilizer kg/ha")
    fertilizer_cost_per_kg: float = Field(1.5, ge=0, description="Fertilizer cost EGP/kg")
    soil_requirement: Optional[SoilRequirementSchema] = None


class FieldSchema(BaseModel):
    name: str
    area: float = Field(..., gt=0, description="Field area in hectares")
    ph: float = Field(6.5, ge=0, le=14, description="Soil pH measurement")
    ec: float = Field(1.0, ge=0, description="Soil EC salinity (dS/m)")
    texture: str = Field("Loam", description="Soil texture class")
    organic_matter: float = Field(2.0, ge=0, description="Organic matter %")
    previous_crop: Optional[str] = Field(None, description="Previous crop planted in field (V4)")


class OptimizationRequestSchema(BaseModel):
    version: str = Field("v4", description="Optimizer version: 'v1', 'v2', 'v3', or 'v4'")
    zone: str = Field("Delta", description="Egyptian region: Delta, Middle Egypt, Upper Egypt, Sinai / Reclaimed Lands")
    season: str = Field("Winter", description="Agricultural season: Winter, Summer, Nili, Perennial")
    water_budget: float = Field(..., ge=0, description="Available water budget in m^3")
    labor_budget: float = Field(2500.0, ge=0, description="Available labor budget in hours")
    fertilizer_budget: float = Field(15000.0, ge=0, description="Available fertilizer budget in kg")
    crops: List[CropSchema]
    fields: List[FieldSchema]


class StartMultiSeasonRequest(BaseModel):
    session_id: str = Field("default", description="Session identifier")
    candidate_crops: List[str] = Field(..., description="List of candidate crop names")
    season_1_recommendation: Optional[Dict[str, Optional[str]]] = Field(None, description="Field -> recommended crop from Season 1")
    current_season_name: Optional[str] = Field("Winter", description="Current season name")
    water_budget: Optional[float] = Field(None, ge=0)
    labor_budget: Optional[float] = Field(None, ge=0)
    fertilizer_budget: Optional[float] = Field(None, ge=0)
    farm_request: Optional[OptimizationRequestSchema] = None


class NextSeasonRequest(BaseModel):
    session_id: str = Field("default", description="Session identifier")
    season_name: str = Field("Winter", description="Agricultural season to plan ('Winter', 'Summer', 'Nili')")
    water_budget: Optional[float] = Field(None, ge=0)
    labor_budget: Optional[float] = Field(None, ge=0)
    fertilizer_budget: Optional[float] = Field(None, ge=0)
    candidate_crops: Optional[List[str]] = Field(None, description="Optional explicit candidate crops update")


# --- Helper Functions ---

def build_farm_inputs(req: OptimizationRequestSchema) -> FarmInputs:
    """Convert API request payload into internal FarmInputs dataclass."""
    crops_dict = {}
    for c in req.crops:
        soil_req = None
        if c.soil_requirement:
            soil_req = CropSoilRequirement(
                min_ph=c.soil_requirement.min_ph,
                max_ph=c.soil_requirement.max_ph,
                max_ec=c.soil_requirement.max_ec,
                suitable_textures=c.soil_requirement.suitable_textures,
            )

        water_req = c.water_requirement
        if water_req <= 0:
            water_req = water_loader.get_water_requirement(c.name, zone=req.zone, season=req.season)

        canonical_name = get_canonical_crop_name(c.name)

        crops_dict[canonical_name] = CropParameters(
            name=canonical_name,
            expected_yield=c.expected_yield,
            price=c.price,
            production_cost=c.production_cost,
            water_requirement=water_req,
            labor_requirement=c.labor_requirement,
            labor_cost_per_hour=c.labor_cost_per_hour,
            fertilizer_requirement=c.fertilizer_requirement,
            fertilizer_cost_per_kg=c.fertilizer_cost_per_kg,
            soil_requirement=soil_req,
        )

    fields_dict = {}
    total_field_area = 0.0
    for f in req.fields:
        fields_dict[f.name] = FieldParameters(
            name=f.name,
            area=f.area,
            ph=f.ph,
            ec=f.ec,
            texture=f.texture,
            organic_matter=f.organic_matter,
            previous_crop=get_canonical_crop_name(f.previous_crop) if f.previous_crop else None,
        )
        total_field_area += f.area

    if not fields_dict:
        total_field_area = sum(f.area for f in req.fields) if req.fields else 100.0

    return FarmInputs(
        field_area=total_field_area,
        water_budget=req.water_budget,
        labor_budget=req.labor_budget,
        fertilizer_budget=req.fertilizer_budget,
        crops=crops_dict,
        fields=fields_dict,
    )


def compute_suitability_explanations(farm_inputs: FarmInputs) -> List[Dict[str, Any]]:
    """Compute detailed suitability reasons for each field-crop pair."""
    engine = SoilSuitabilityEngine()
    details = []

    for f_name, f_obj in farm_inputs.fields.items():
        for c_name, c_obj in farm_inputs.crops.items():
            suitable = engine.is_suitable(f_obj, c_obj)
            reasons = []

            req = c_obj.soil_requirement
            if req:
                if f_obj.ph < req.min_ph:
                    reasons.append(f"pH {f_obj.ph} < min required {req.min_ph}")
                elif f_obj.ph > req.max_ph:
                    reasons.append(f"pH {f_obj.ph} > max tolerated {req.max_ph}")

                if f_obj.ec > req.max_ec:
                    reasons.append(f"Salinity EC {f_obj.ec} > max tolerated {req.max_ec} dS/m")

                if req.suitable_textures and f_obj.texture not in req.suitable_textures:
                    reasons.append(
                        f"Texture '{f_obj.texture}' not in suitable list ({', '.join(req.suitable_textures)})"
                    )

            reason_str = "Suitable" if suitable else "; ".join(reasons)
            details.append({
                "field": f_name,
                "crop": c_name,
                "crop_arabic": get_arabic_crop_name(c_name),
                "suitable": suitable,
                "reason": reason_str,
            })

    return details


def compute_rotation_explanations(farm_inputs: FarmInputs) -> List[Dict[str, Any]]:
    """Compute detailed crop rotation suitability reasons for each field-crop pair (V4)."""
    details = []
    for f_name, f_obj in farm_inputs.fields.items():
        prev_c = f_obj.previous_crop
        for c_name in farm_inputs.crops.keys():
            try:
                suitability = rotation_loader.get_rotation_suitability(prev_c, c_name)
                is_suitable = suitability == 1
            except Exception as exc:
                is_suitable = False
                reason_str = f"Unmatched crop: {exc}"
            else:
                if prev_c is None or not str(prev_c).strip() or str(prev_c).lower() == "none":
                    reason_str = "No previous crop history (unconstrained)"
                elif is_suitable:
                    reason_str = f"Recommended rotation after '{get_arabic_crop_name(prev_c)}'"
                else:
                    reason_str = f"Agronomically disallowed succession after '{get_arabic_crop_name(prev_c)}'"

            details.append({
                "field": f_name,
                "crop": c_name,
                "crop_arabic": get_arabic_crop_name(c_name),
                "previous_crop": prev_c or "None",
                "previous_crop_arabic": get_arabic_crop_name(prev_c) if prev_c else "لا يوجد",
                "suitable": is_suitable,
                "reason": reason_str,
            })
    return details


def sanitize_val(val: float) -> Optional[float]:
    """Convert float('inf') or NaN to None for JSON compliance."""
    if val is None or math.isinf(val) or math.isnan(val):
        return None
    return round(val, 2)


def identify_binding_constraints(
    total_land: float, land_limit: float,
    total_water: float, water_limit: float,
    total_labor: float, labor_limit: Optional[float],
    total_fert: float, fert_limit: Optional[float],
    tolerance: float = 0.001
) -> List[Dict[str, Any]]:
    """Analyze resource usages against limits to identify binding bottleneck constraints."""
    constraints = []

    def check_res(name: str, used: float, limit: Optional[float], unit: str):
        if limit is None or math.isinf(limit) or limit <= 0:
            pct = 0.0
            is_binding = False
            lim_val = None
        else:
            pct = round((used / limit) * 100.0, 1)
            is_binding = abs(used - limit) / max(1.0, limit) <= tolerance or used >= limit - 1e-4
            lim_val = round(limit, 2)

        constraints.append({
            "resource": name,
            "used": round(used, 2),
            "limit": lim_val,
            "unit": unit,
            "utilization_pct": min(100.0, pct),
            "is_binding": is_binding,
            "status": "Binding Bottleneck" if is_binding else "Sufficient",
        })

    check_res("Land Area", total_land, land_limit, "ha")
    check_res("Water Budget", total_water, water_limit, "m^3")
    check_res("Labor Budget", total_labor, labor_limit, "hours")
    check_res("Fertilizer Budget", total_fert, fert_limit, "kg")

    return constraints


# --- API Endpoints ---

@app.get("/api/preset")
def get_preset_farm():
    """Return default example farm input dataset."""
    inputs = get_example_farm_data()

    crops_list = []
    for name, c in inputs.crops.items():
        soil_req = None
        if c.soil_requirement:
            soil_req = {
                "min_ph": c.soil_requirement.min_ph,
                "max_ph": c.soil_requirement.max_ph,
                "max_ec": c.soil_requirement.max_ec,
                "suitable_textures": c.soil_requirement.suitable_textures,
            }

        crops_list.append({
            "name": c.name,
            "name_arabic": get_arabic_crop_name(c.name),
            "allowed_seasons": get_allowed_seasons(c.name),
            "expected_yield": c.expected_yield,
            "price": c.price,
            "production_cost": c.production_cost,
            "water_requirement": c.water_requirement,
            "labor_requirement": c.labor_requirement,
            "labor_cost_per_hour": c.labor_cost_per_hour,
            "fertilizer_requirement": c.fertilizer_requirement,
            "fertilizer_cost_per_kg": c.fertilizer_cost_per_kg,
            "soil_requirement": soil_req,
            "revenue_per_ha": c.revenue_per_hectare,
            "profit_per_ha": c.profit_per_hectare,
        })

    fields_list = []
    for name, f in inputs.fields.items():
        fields_list.append({
            "name": f.name,
            "area": f.area,
            "ph": f.ph,
            "ec": f.ec,
            "texture": f.texture,
            "organic_matter": f.organic_matter,
            "previous_crop": f.previous_crop,
            "previous_crop_arabic": get_arabic_crop_name(f.previous_crop) if f.previous_crop else "لا يوجد",
        })

    return {
        "water_budget": inputs.water_budget,
        "labor_budget": inputs.labor_budget,
        "fertilizer_budget": inputs.fertilizer_budget,
        "total_field_area": inputs.field_area,
        "crops": crops_list,
        "fields": fields_list,
    }


@app.get("/api/ecocrop/crops")
def list_ecocrop_species(q: Optional[str] = None, category: Optional[str] = None):
    """Return available crop species from FAO EcoCrop database."""
    if q or category:
        results = ecocrop_db.search_crops(query=q or "", category=category)
        return [
            {
                "name": entry.name,
                "name_arabic": get_arabic_crop_name(entry.name),
                "scientific_name": entry.scientific_name,
                "category": entry.category,
                "min_ph": entry.min_ph,
                "max_ph": entry.max_ph,
                "max_ec": entry.max_ec,
                "suitable_textures": entry.suitable_textures,
                "water_requirement": entry.water_requirement,
                "default_expected_yield": getattr(entry, "default_expected_yield", 5.0),
                "default_price": getattr(entry, "default_price", 400.0),
                "default_production_cost": getattr(entry, "default_production_cost", 500.0),
            }
            for entry in results
        ]
    return ecocrop_db.list_all()


@app.get("/api/ecocrop/lookup/{crop_name}")
def get_ecocrop_details(crop_name: str):
    """Lookup specific FAO EcoCrop entry details by crop name."""
    entry = ecocrop_db.get_crop(crop_name)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Crop '{crop_name}' not found in EcoCrop DB.")
    return {
        "name": entry.name,
        "name_arabic": get_arabic_crop_name(entry.name),
        "scientific_name": entry.scientific_name,
        "category": entry.category,
        "min_ph": entry.min_ph,
        "opt_min_ph": entry.opt_min_ph,
        "opt_max_ph": entry.opt_max_ph,
        "max_ph": entry.max_ph,
        "max_ec": entry.max_ec,
        "suitable_textures": entry.suitable_textures,
        "water_requirement": entry.water_requirement,
        "min_temp": entry.min_temp,
        "max_temp": entry.max_temp,
        "crop_cycle_days": entry.crop_cycle_max_days,
        "default_expected_yield": getattr(entry, "default_expected_yield", 5.0),
        "default_price": getattr(entry, "default_price", 400.0),
        "default_production_cost": getattr(entry, "default_production_cost", 500.0),
    }


@app.get("/api/rotation/matrix")
def get_rotation_matrix_info():
    """Return available crop list and rotation matrix metadata (V4)."""
    crops = sorted(list(rotation_loader.matrix_crops))
    return {
        "crops": crops,
        "perennial_map": rotation_loader.perennial_map,
        "family_map": rotation_loader.family_map,
    }


@app.get("/api/water/zones")
def get_water_zones():
    """Return available Egyptian agricultural zones and seasons."""
    return {
        "zones": water_loader.VALID_ZONES,
        "seasons": water_loader.VALID_SEASONS,
    }


@app.get("/api/water/lookup/{crop_name}")
def get_crop_water_requirement(crop_name: str, zone: str = "Delta", season: str = "Winter"):
    """Lookup water requirement (m^3/ha) for a crop in a specific zone and season."""
    req_m3_ha = water_loader.get_water_requirement(crop_name, zone=zone, season=season)
    return {
        "crop": crop_name,
        "zone": zone,
        "season": season,
        "water_requirement": req_m3_ha,
    }


@app.post("/api/optimize")
def run_optimization(req: OptimizationRequestSchema):
    """Run optimization algorithm (V1, V2, V3, or V4) for provided farm inputs."""
    if not req.crops:
        raise HTTPException(status_code=400, detail="At least one crop must be defined.")

    farm_inputs = build_farm_inputs(req)

    version = req.version.lower()
    if version == "v1":
        optimizer = CropMixOptimizerV1()
        res = optimizer.solve(farm_inputs)

        total_revenue = sum(
            ha * farm_inputs.crops[c].revenue_per_hectare for c, ha in res.crop_allocation.items()
        )
        total_prod_cost = sum(
            ha * farm_inputs.crops[c].production_cost for c, ha in res.crop_allocation.items()
        )

        field_allocations = {"All_Fields": res.crop_allocation}
        binding = identify_binding_constraints(
            total_land=res.total_land_used, land_limit=res.field_area_limit,
            total_water=res.total_water_used, water_limit=res.water_budget_limit,
            total_labor=0.0, labor_limit=None,
            total_fert=0.0, fert_limit=None,
        )

        return {
            "version": "V1 (Aggregate Basic)",
            "status": res.status,
            "is_feasible": res.is_feasible,
            "expected_profit": res.expected_profit,
            "total_expected_revenue": round(total_revenue, 2),
            "total_production_cost": round(total_prod_cost, 2),
            "total_labor_cost": 0.0,
            "total_fertilizer_cost": 0.0,
            "total_land_used": res.total_land_used,
            "field_area_limit": res.field_area_limit,
            "total_water_used": res.total_water_used,
            "water_budget_limit": res.water_budget_limit,
            "total_labor_used": 0.0,
            "labor_budget_limit": None,
            "total_fertilizer_used": 0.0,
            "fertilizer_budget_limit": None,
            "crop_allocation_summary": res.crop_allocation,
            "field_allocations": field_allocations,
            "suitability_details": [],
            "binding_constraints": binding,
        }

    elif version == "v2":
        optimizer = CropMixOptimizerV2()
        res = optimizer.solve(farm_inputs)

        total_revenue = sum(
            ha * farm_inputs.crops[c].revenue_per_hectare for c, ha in res.crop_allocation.items()
        )
        total_prod_cost = sum(
            ha * farm_inputs.crops[c].production_cost for c, ha in res.crop_allocation.items()
        )
        total_labor_cost = sum(
            ha * farm_inputs.crops[c].labor_cost_per_hectare for c, ha in res.crop_allocation.items()
        )
        total_fert_cost = sum(
            ha * farm_inputs.crops[c].fertilizer_cost_per_hectare for c, ha in res.crop_allocation.items()
        )

        field_allocations = {"All_Fields": res.crop_allocation}
        binding = identify_binding_constraints(
            total_land=res.total_land_used, land_limit=res.field_area_limit,
            total_water=res.total_water_used, water_limit=res.water_budget_limit,
            total_labor=res.total_labor_used, labor_limit=res.labor_budget_limit,
            total_fert=res.total_fertilizer_used, fert_limit=res.fertilizer_budget_limit,
        )

        return {
            "version": "V2 (Resource Budgets)",
            "status": res.status,
            "is_feasible": res.is_feasible,
            "expected_profit": res.expected_profit,
            "total_expected_revenue": round(total_revenue, 2),
            "total_production_cost": round(total_prod_cost, 2),
            "total_labor_cost": round(total_labor_cost, 2),
            "total_fertilizer_cost": round(total_fert_cost, 2),
            "total_land_used": res.total_land_used,
            "field_area_limit": res.field_area_limit,
            "total_water_used": res.total_water_used,
            "water_budget_limit": res.water_budget_limit,
            "total_labor_used": res.total_labor_used,
            "labor_budget_limit": res.labor_budget_limit,
            "total_fertilizer_used": res.total_fertilizer_used,
            "fertilizer_budget_limit": res.fertilizer_budget_limit,
            "crop_allocation_summary": res.crop_allocation,
            "field_allocations": field_allocations,
            "suitability_details": [],
            "binding_constraints": binding,
        }

    elif version == "v3":
        if not req.fields:
            raise HTTPException(status_code=400, detail="Version 3 requires at least one field definition.")

        optimizer = CropMixOptimizerV3()
        res = optimizer.solve(farm_inputs)

        summary_crop_alloc: Dict[str, float] = {}
        for c in farm_inputs.crops.keys():
            summary_crop_alloc[c] = sum(
                res.crop_allocation[f].get(c, 0.0) for f in farm_inputs.fields.keys()
            )

        suitability_details = compute_suitability_explanations(farm_inputs)

        binding = identify_binding_constraints(
            total_land=res.total_land_used, land_limit=sum(f.area for f in farm_inputs.fields.values()),
            total_water=res.total_water_used, water_limit=res.water_budget_limit,
            total_labor=res.total_labor_used, labor_limit=res.labor_budget_limit,
            total_fert=res.total_fertilizer_used, fert_limit=res.fertilizer_budget_limit,
        )

        return {
            "version": "V3 (Soil Suitability)",
            "status": res.status,
            "is_feasible": res.is_feasible,
            "expected_profit": res.expected_profit,
            "total_expected_revenue": res.total_expected_revenue,
            "total_production_cost": res.total_production_cost,
            "total_labor_cost": res.total_labor_cost,
            "total_fertilizer_cost": res.total_fertilizer_cost,
            "total_land_used": res.total_land_used,
            "field_area_limit": sum(f.area for f in farm_inputs.fields.values()),
            "total_water_used": res.total_water_used,
            "water_budget_limit": res.water_budget_limit,
            "total_labor_used": res.total_labor_used,
            "labor_budget_limit": sanitize_val(res.labor_budget_limit),
            "total_fertilizer_used": res.total_fertilizer_used,
            "fertilizer_budget_limit": sanitize_val(res.fertilizer_budget_limit),
            "crop_allocation_summary": summary_crop_alloc,
            "field_allocations": res.crop_allocation,
            "field_land_used": res.field_land_used,
            "field_land_limits": res.field_land_limits,
            "suitability_details": suitability_details,
            "binding_constraints": binding,
        }

    elif version == "v4":
        if not req.fields:
            raise HTTPException(status_code=400, detail="Version 4 requires at least one field definition.")

        optimizer = CropMixOptimizerV4(rotation_loader=rotation_loader)
        res = optimizer.solve(farm_inputs)

        # 4B Phase 1 Financial Projection calculation
        financial_engine = FinancialProjection()
        fin_res = financial_engine.calculate(farm_inputs, res)

        summary_crop_alloc: Dict[str, float] = {}
        for c in farm_inputs.crops.keys():
            summary_crop_alloc[c] = sum(
                res.crop_allocation[f].get(c, 0.0) for f in farm_inputs.fields.keys()
            )

        suitability_details = compute_suitability_explanations(farm_inputs)
        rotation_details = compute_rotation_explanations(farm_inputs)

        binding = identify_binding_constraints(
            total_land=res.total_land_used, land_limit=sum(f.area for f in farm_inputs.fields.values()),
            total_water=res.total_water_used, water_limit=res.water_budget_limit,
            total_labor=res.total_labor_used, labor_limit=res.labor_budget_limit,
            total_fert=res.total_fertilizer_used, fert_limit=res.fertilizer_budget_limit,
        )

        fin_field_dict = {}
        for f_name, c_map in fin_res.field_projections.items():
            fin_field_dict[f_name] = {}
            for c_name, p in c_map.items():
                fin_field_dict[f_name][c_name] = {
                    "field_name": p.field_name,
                    "crop_name": p.crop_name,
                    "crop_name_arabic": get_arabic_crop_name(p.crop_name),
                    "allocated_area": p.allocated_area,
                    "expected_revenue": p.expected_revenue,
                    "production_cost": p.production_cost,
                    "labor_cost": p.labor_cost,
                    "fertilizer_cost": p.fertilizer_cost,
                    "total_cost": p.total_cost,
                    "net_profit": p.net_profit,
                    "profit_per_hectare": p.profit_per_hectare,
                    "profit_margin": p.profit_margin,
                    "profit_margin_pct": round(p.profit_margin * 100.0, 2),
                }

        return {
            "version": "V4 (Soil Suitability + Crop Rotation)",
            "status": res.status,
            "is_feasible": res.is_feasible,
            "expected_profit": res.expected_profit,
            "total_expected_revenue": res.total_expected_revenue,
            "total_production_cost": res.total_production_cost,
            "total_labor_cost": res.total_labor_cost,
            "total_fertilizer_cost": res.total_fertilizer_cost,
            "total_land_used": res.total_land_used,
            "field_area_limit": sum(f.area for f in farm_inputs.fields.values()),
            "total_water_used": res.total_water_used,
            "water_budget_limit": res.water_budget_limit,
            "total_labor_used": res.total_labor_used,
            "labor_budget_limit": sanitize_val(res.labor_budget_limit),
            "total_fertilizer_used": res.total_fertilizer_used,
            "fertilizer_budget_limit": sanitize_val(res.fertilizer_budget_limit),
            "crop_allocation_summary": summary_crop_alloc,
            "field_allocations": res.crop_allocation,
            "field_land_used": res.field_land_used,
            "field_land_limits": res.field_land_limits,
            "suitability_details": suitability_details,
            "rotation_details": rotation_details,
            "field_previous_crops": res.field_previous_crops,
            "binding_constraints": binding,
            "financial_projection": {
                "farm_summary": {
                    "total_area": fin_res.farm_summary.total_area,
                    "total_expected_revenue": fin_res.farm_summary.total_expected_revenue,
                    "total_production_cost": fin_res.farm_summary.total_production_cost,
                    "total_labor_cost": fin_res.farm_summary.total_labor_cost,
                    "total_fertilizer_cost": fin_res.farm_summary.total_fertilizer_cost,
                    "total_cost": fin_res.farm_summary.total_cost,
                    "total_expected_net_profit": fin_res.farm_summary.total_expected_net_profit,
                    "overall_profit_margin": fin_res.farm_summary.overall_profit_margin,
                    "overall_profit_margin_pct": round(fin_res.farm_summary.overall_profit_margin * 100.0, 2),
                },
                "field_projections": fin_field_dict,
            },
        }

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported version '{version}'.")


# --- Internship 4B Phase 2: Multi-Season API Endpoints ---

@app.post("/api/multi-season/start")
def start_multi_season(req: StartMultiSeasonRequest):
    """Initialize a rolling multi-season planning session using completed Season 1 recommendation."""
    if not req.candidate_crops:
        raise HTTPException(status_code=400, detail="candidate_crops list cannot be empty.")

    if req.farm_request:
        farm_inputs = build_farm_inputs(req.farm_request)
    else:
        farm_inputs = get_example_farm_data()

    try:
        planner = MultiSeasonPlanner(farm_inputs, rotation_loader=rotation_loader)
        planner.set_candidate_crops(req.candidate_crops)

        # The multi-season workflow always begins after the completed current
        # season. Seed it even when the optimizer recommended fallow land only.
        planner.seed_season_1(
            previous_crops=req.season_1_recommendation or {},
            season_name=req.current_season_name or "Winter",
            water_budget=req.water_budget,
            labor_budget=req.labor_budget,
            fertilizer_budget=req.fertilizer_budget,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    active_multi_season_sessions[req.session_id] = planner

    return {
        "session_id": req.session_id,
        "candidate_crops": planner.candidate_crops,
        "candidate_crops_arabic": [get_arabic_crop_name(c) for c in planner.candidate_crops],
        "current_previous_crops": planner.current_previous_crops,
        "current_previous_crops_arabic": {
            f: get_arabic_crop_name(c) if c else "لا يوجد"
            for f, c in planner.current_previous_crops.items()
        },
        "current_water_budget": planner.current_water_budget,
        "current_labor_budget": planner.current_labor_budget,
        "current_fertilizer_budget": planner.current_fertilizer_budget,
        "next_season_number": len(planner.seasons) + 1,
        "message": "تم بدء جلسة التخطيط متعدد المواسم بنجاح.",
    }


@app.post("/api/multi-season/next-season")
def plan_next_season(req: NextSeasonRequest):
    """Plan ONE next season in the rolling sequence."""
    planner = active_multi_season_sessions.get(req.session_id)
    if not planner:
        farm_inputs = get_example_farm_data()
        planner = MultiSeasonPlanner(farm_inputs, rotation_loader=rotation_loader)
        c_list = req.candidate_crops or list(farm_inputs.crops.keys())
        planner.set_candidate_crops(c_list)
        active_multi_season_sessions[req.session_id] = planner
    elif req.candidate_crops:
        planner.set_candidate_crops(req.candidate_crops)

    try:
        plan: SeasonPlan = planner.plan_next_season(
            season_name=req.season_name,
            water_budget=req.water_budget,
            labor_budget=req.labor_budget,
            fertilizer_budget=req.fertilizer_budget,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "session_id": req.session_id,
        "season_number": plan.season_number,
        "season_name": plan.season_name,
        "is_current_season": plan.is_current_season,
        "explanation_note": plan.explanation_note,
        "candidate_crops": plan.candidate_crops,
        "candidate_crops_arabic": [get_arabic_crop_name(c) for c in plan.candidate_crops],
        "season_allowed_crops": plan.season_allowed_crops,
        "season_allowed_crops_arabic": [get_arabic_crop_name(c) for c in plan.season_allowed_crops],
        "previous_crops": plan.previous_crops,
        "previous_crops_arabic": {
            f: get_arabic_crop_name(c) if c else "لا يوجد"
            for f, c in plan.previous_crops.items()
        },
        "next_previous_crops": planner.current_previous_crops,
        "next_previous_crops_arabic": {
            f: get_arabic_crop_name(c) if c else "لا يوجد"
            for f, c in planner.current_previous_crops.items()
        },
        "water_budget": plan.water_budget,
        "labor_budget": plan.labor_budget,
        "fertilizer_budget": plan.fertilizer_budget,
        "crop_allocation": plan.crop_allocation,
        "resource_usage": plan.resource_usage,
        "financial_summary": {
            "total_area": plan.financial_projection.farm_summary.total_area,
            "total_expected_revenue": plan.financial_projection.farm_summary.total_expected_revenue,
            "total_production_cost": plan.financial_projection.farm_summary.total_production_cost,
            "total_labor_cost": plan.financial_projection.farm_summary.total_labor_cost,
            "total_fertilizer_cost": plan.financial_projection.farm_summary.total_fertilizer_cost,
            "total_cost": plan.financial_projection.farm_summary.total_cost,
            "total_expected_net_profit": plan.financial_projection.farm_summary.total_expected_net_profit,
            "overall_profit_margin_pct": round(plan.financial_projection.farm_summary.overall_profit_margin * 100.0, 2),
        },
        "field_financials": plan.financial_projection.field_projections,
    }


from fastapi.responses import FileResponse

# --- Serve Static UI Files ---
static_dir = Path(__file__).resolve().parent / "static"


@app.get("/")
def read_index():
    return FileResponse(static_dir / "index.html")


@app.get("/styles.css")
def read_styles():
    return FileResponse(static_dir / "styles.css", media_type="text/css")


@app.get("/app.js")
def read_js():
    return FileResponse(static_dir / "app.js", media_type="application/javascript")


app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
