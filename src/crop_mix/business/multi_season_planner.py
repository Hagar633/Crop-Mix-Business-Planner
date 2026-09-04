"""Internship 4B Phase 2: Multi-Season Crop Rotation Planner.

Provides rolling, sequential multi-season agricultural planning.
Consumes 4A V4 Crop Mix Optimizer and 4B Phase 1 Financial Projection engine additively.

CRITICAL AGRICULTURAL DESIGN RULES:
1. Soil Suitability: Active for Season 1 (current measured soil data).
   DISABLED for Season 2+ (future soil pH/EC/texture are unknown).
2. Rolling Execution: Plans ONE season per call to plan_next_season(). Never auto-generates all seasons.
3. Candidate Crop Pool: Selected ONCE at session start and persisted across all future seasons unless explicitly edited.
4. History & Budget Carry-Forward: Recommended crop per field becomes previous_crop for next season. Active budgets carry forward as defaults.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
import copy

from crop_mix.data.example_data import (
    FarmInputs,
    CropParameters,
    FieldParameters,
    CropSoilRequirement,
)
from crop_mix.data.rotation_loader import RotationMatrixLoader
from crop_mix.data.crop_seasons import (
    get_allowed_seasons,
    get_arabic_crop_name,
    get_canonical_crop_name,
    is_crop_allowed_in_season,
)
from crop_mix.models.optimizer_v4 import CropMixOptimizerV4, OptimizationResultV4
from crop_mix.business.financial_projection import FinancialProjection, FinancialProjectionResult


@dataclass
class SeasonPlan:
    """Represents a single planned season within a multi-season planning session."""

    season_number: int  # 1, 2, 3...
    season_name: str  # e.g. "Winter", "Summer", "Nili"
    previous_crops: Dict[str, Optional[str]]  # field_name -> previous crop name
    candidate_crops: List[str]  # Candidate crop list used for planning
    season_allowed_crops: List[str]  # Sub-list of candidate crops allowed in this season
    water_budget: float  # Available water budget m^3
    labor_budget: float  # Available labor budget hours
    fertilizer_budget: float  # Available fertilizer budget kg
    crop_allocation: Dict[str, Dict[str, float]]  # field_name -> crop_name -> allocated ha
    financial_projection: FinancialProjectionResult  # 4B Financial projection breakdown
    resource_usage: Dict[str, float]  # land_used, water_used, labor_used, fertilizer_used
    is_current_season: bool  # True for Season 1, False for Season 2+
    explanation_note: str  # Note on soil suitability enforcement


@dataclass
class MultiSeasonPlan:
    """Overall state container for a multi-season rolling planning session."""

    candidate_crops: List[str]
    seasons: List[SeasonPlan] = field(default_factory=list)
    current_previous_crops: Dict[str, Optional[str]] = field(default_factory=dict)
    current_water_budget: float = 0.0
    current_labor_budget: float = 0.0
    current_fertilizer_budget: float = 0.0


class MultiSeasonPlanner:
    """Rolling Multi-Season Agricultural Planning Engine (Internship 4B Phase 2)."""

    def __init__(
        self,
        farm_inputs: FarmInputs,
        rotation_loader: Optional[RotationMatrixLoader] = None,
        candidate_crops: Optional[List[str]] = None,
    ):
        """Initialize MultiSeasonPlanner with base farm inputs and rotation loader.

        Args:
            farm_inputs: Base farm inputs dataclass (fields, crops, initial budgets).
            rotation_loader: Optional RotationMatrixLoader instance.
            candidate_crops: Optional initial list of candidate crops.
        """
        self.base_farm_inputs = copy.deepcopy(farm_inputs)
        self.rotation_loader = rotation_loader or RotationMatrixLoader()
        self.optimizer = CropMixOptimizerV4(rotation_loader=self.rotation_loader)
        self.financial_engine = FinancialProjection()

        # State management
        self.candidate_crops: List[str] = []
        self.seasons: List[SeasonPlan] = []

        # Current rolling state
        self.current_previous_crops: Dict[str, Optional[str]] = {
            f_name: f_obj.previous_crop
            for f_name, f_obj in self.base_farm_inputs.fields.items()
        }
        self.current_water_budget: float = self.base_farm_inputs.water_budget
        self.current_labor_budget: float = self.base_farm_inputs.labor_budget
        self.current_fertilizer_budget: float = self.base_farm_inputs.fertilizer_budget

        if candidate_crops:
            self.set_candidate_crops(candidate_crops)

    def set_candidate_crops(self, crop_names: List[str]):
        """Set and validate the candidate crop pool.

        Selected once at session start and persisted across seasons unless explicitly edited.

        Fails loudly if crop list is empty or contains unknown/unmatched crops.
        """
        if not crop_names:
            raise ValueError("Candidate crop list cannot be empty. Please select at least one crop.")

        canonical_list = []
        seen = set()
        for name in crop_names:
            canonical = get_canonical_crop_name(name)
            if canonical not in self.base_farm_inputs.crops:
                raise ValueError(
                    f"Crop '{name}' (canonical: '{canonical}') is not present in the farm crop dataset."
                )
            # Validate rotation matrix existence
            self.rotation_loader.resolve_crop_name(canonical)

            if canonical not in seen:
                canonical_list.append(canonical)
                seen.add(canonical)

        self.candidate_crops = canonical_list

    def seed_season_1(
        self,
        previous_crops: Dict[str, Optional[str]],
        season_name: str = "Winter",
        water_budget: Optional[float] = None,
        labor_budget: Optional[float] = None,
        fertilizer_budget: Optional[float] = None,
    ):
        """Register completed Season 1 recommendation into rolling planner state without re-running optimizer.

        Args:
            previous_crops: Mapping of field_name -> recommended crop from Season 1.
            season_name: Season name for Season 1 (e.g. "Winter").
            water_budget: Optional initial water budget.
            labor_budget: Optional initial labor budget.
            fertilizer_budget: Optional initial fertilizer budget.
        """
        if water_budget is not None and water_budget >= 0:
            self.current_water_budget = water_budget
        if labor_budget is not None and labor_budget >= 0:
            self.current_labor_budget = labor_budget
        if fertilizer_budget is not None and fertilizer_budget >= 0:
            self.current_fertilizer_budget = fertilizer_budget

        for f_name, crop_name in previous_crops.items():
            if crop_name and str(crop_name).strip() and str(crop_name).lower() != "none":
                self.current_previous_crops[f_name] = crop_name

        dummy_financial = FinancialProjectionResult(
            field_projections={},
            farm_summary=FinancialProjectionResult.__dataclass_fields__["farm_summary"].type(
                total_area=0.0,
                total_expected_revenue=0.0,
                total_production_cost=0.0,
                total_labor_cost=0.0,
                total_fertilizer_cost=0.0,
                total_cost=0.0,
                total_expected_net_profit=0.0,
                overall_profit_margin=0.0,
            ),
        )

        s1_plan = SeasonPlan(
            season_number=1,
            season_name=season_name,
            previous_crops=copy.deepcopy(previous_crops),
            candidate_crops=list(self.candidate_crops),
            season_allowed_crops=[],
            water_budget=self.current_water_budget,
            labor_budget=self.current_labor_budget,
            fertilizer_budget=self.current_fertilizer_budget,
            crop_allocation={},
            financial_projection=dummy_financial,
            resource_usage={
                "land_used": 0.0,
                "water_used": 0.0,
                "labor_used": 0.0,
                "fertilizer_used": 0.0,
            },
            is_current_season=True,
            explanation_note="تم استخدام خصائص التربة الحالية (pH، الملوحة، القوام) بالإضافة للدورة الزراعية والميزانية المتاحة.",
        )
        self.seasons = [s1_plan]

    def plan_next_season(
        self,
        season_name: str,
        water_budget: Optional[float] = None,
        labor_budget: Optional[float] = None,
        fertilizer_budget: Optional[float] = None,
    ) -> SeasonPlan:
        """Plan ONE next season in the rolling sequence.

        Args:
            season_name: Agricultural season name ("Winter", "Summer", "Nili", "Perennial").
            water_budget: Optional user-edited water budget m^3.
            labor_budget: Optional user-edited labor budget hours.
            fertilizer_budget: Optional user-edited fertilizer budget kg.

        Returns:
            SeasonPlan containing allocation, financial projection, resource usage, and state.
        """
        if not self.candidate_crops:
            raise ValueError(
                "Candidate crops have not been selected. Please call set_candidate_crops() before planning."
            )

        season_number = len(self.seasons) + 1
        is_current_season = (season_number == 1)

        # Budget resolution: User-edited budget overrides previous default; update rolling default
        if water_budget is not None and water_budget >= 0:
            self.current_water_budget = water_budget
        if labor_budget is not None and labor_budget >= 0:
            self.current_labor_budget = labor_budget
        if fertilizer_budget is not None and fertilizer_budget >= 0:
            self.current_fertilizer_budget = fertilizer_budget

        active_water = self.current_water_budget
        active_labor = self.current_labor_budget
        active_fert = self.current_fertilizer_budget

        # Step 1: Filter candidate crops by season compatibility
        season_allowed_crops = [
            c for c in self.candidate_crops
            if is_crop_allowed_in_season(c, season_name)
        ]

        if not season_allowed_crops:
            raise ValueError(
                f"None of the selected candidate crops {self.candidate_crops} can be grown in season '{season_name}'."
            )

        # Step 2: Build tailored FarmInputs payload for V4 Optimizer
        season_crops: Dict[str, CropParameters] = {}
        for c_name in season_allowed_crops:
            base_crop = self.base_farm_inputs.crops[c_name]
            season_crops[c_name] = CropParameters(
                name=base_crop.name,
                expected_yield=base_crop.expected_yield,
                price=base_crop.price,
                production_cost=base_crop.production_cost,
                water_requirement=base_crop.water_requirement,
                labor_requirement=base_crop.labor_requirement,
                labor_cost_per_hour=base_crop.labor_cost_per_hour,
                fertilizer_requirement=base_crop.fertilizer_requirement,
                fertilizer_cost_per_kg=base_crop.fertilizer_cost_per_kg,
                soil_requirement=base_crop.soil_requirement,
            )

        season_fields: Dict[str, FieldParameters] = {}
        total_field_area = 0.0
        for f_name, base_field in self.base_farm_inputs.fields.items():
            prev_crop = self.current_previous_crops.get(f_name, None)
            season_fields[f_name] = FieldParameters(
                name=base_field.name,
                area=base_field.area,
                ph=base_field.ph,
                ec=base_field.ec,
                texture=base_field.texture,
                organic_matter=base_field.organic_matter,
                previous_crop=prev_crop,
            )
            total_field_area += base_field.area

        season_farm_inputs = FarmInputs(
            field_area=total_field_area,
            water_budget=active_water,
            labor_budget=active_labor,
            fertilizer_budget=active_fert,
            crops=season_crops,
            fields=season_fields,
        )

        # Step 3: Solve optimization problem via V4 Optimizer
        opt_result: OptimizationResultV4 = self.optimizer.solve(
            season_farm_inputs,
            apply_soil_suitability=is_current_season
        )

        if not opt_result.is_feasible:
            raise RuntimeError(f"Optimization failed for season {season_name}: {opt_result.status}")

        # Step 4: Calculate 4B Financial Projection
        fin_result: FinancialProjectionResult = self.financial_engine.calculate(
            season_farm_inputs, opt_result
        )

        # Explanation note regarding soil suitability
        if is_current_season:
            explanation = (
                "تم استخدام خصائص التربة الحالية (pH، الملوحة، القوام) بالإضافة للدورة الزراعية والميزانية المتاحة."
            )
        else:
            explanation = (
                "المواسم المستقبلية: لم يتم استخدام خصائص التربة للموسم المستقبلي لعدم توفر قياسات مستقبلية. تم التخطيط باستخدام الدورة الزراعية والإنتاجية والميزانية المتاحة."
            )

        # Build SeasonPlan record
        plan = SeasonPlan(
            season_number=season_number,
            season_name=season_name,
            previous_crops=copy.deepcopy(self.current_previous_crops),
            candidate_crops=list(self.candidate_crops),
            season_allowed_crops=season_allowed_crops,
            water_budget=active_water,
            labor_budget=active_labor,
            fertilizer_budget=active_fert,
            crop_allocation=opt_result.crop_allocation,
            financial_projection=fin_result,
            resource_usage={
                "land_used": opt_result.total_land_used,
                "water_used": opt_result.total_water_used,
                "labor_used": opt_result.total_labor_used,
                "fertilizer_used": opt_result.total_fertilizer_used,
            },
            is_current_season=is_current_season,
            explanation_note=explanation,
        )

        # Step 5: Update rolling state for the NEXT season
        # Update per-field previous crop history to the primary allocated crop in this season
        for f_name, allocations in opt_result.crop_allocation.items():
            best_crop = None
            best_area = 0.0
            for c_name, alloc_ha in allocations.items():
                if alloc_ha > best_area:
                    best_area = alloc_ha
                    best_crop = c_name

            if best_crop and best_area > 0:
                self.current_previous_crops[f_name] = best_crop

        self.seasons.append(plan)
        return plan

    def get_session_state(self) -> MultiSeasonPlan:
        """Return the overall multi-season plan session container."""
        return MultiSeasonPlan(
            candidate_crops=list(self.candidate_crops),
            seasons=self.seasons,
            current_previous_crops=copy.deepcopy(self.current_previous_crops),
            current_water_budget=self.current_water_budget,
            current_labor_budget=self.current_labor_budget,
            current_fertilizer_budget=self.current_fertilizer_budget,
        )
