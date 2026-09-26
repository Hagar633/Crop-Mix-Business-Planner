-- =============================================================================
-- CROP MIX BUSINESS PLANNER - DATABASE SCHEMA DDL (PostgreSQL Compatible)
-- Version: 2.0.0
-- Purpose: Complete schema for Crop Registry (Option 1), Farm Management,
--          Soil Parameters, EcoCrop Profiles, Water Requirements, Crop Rotation,
--          Optimization Results, Multi-Season Plans, and Risk Scenarios.
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- MODULE 1: MASTER CROP REGISTRY
-- Single Source of Truth for all 53 recognized agricultural crops.
-- Implements Option 1 (Centralized Master Crop Registry).
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Table 1: CROPS (Canonical Master Registry)
-- Canonical 53-crop list with scientific classification, economic benchmarks,
-- and EcoCrop soil + climate tolerances. Indexed by auto-resolved canonical name.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS crops (
    id                              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    canonical_name_en               VARCHAR(100) NOT NULL UNIQUE,
    canonical_name_ar               VARCHAR(100) NOT NULL,
    scientific_name                 VARCHAR(150) NOT NULL,
    crop_family                     VARCHAR(100),
    category                        VARCHAR(50) NOT NULL
        CHECK (category IN ('Cereal', 'Legume', 'Vegetable', 'Fruit',
                            'Oilseed', 'Fiber', 'Forage', 'Sugar',
                            'Medicinal/Aromatic')),
    is_perennial                    BOOLEAN NOT NULL DEFAULT FALSE,

    -- EcoCrop Soil & Climate tolerances
    ecocrop_species_reference       VARCHAR(100),  -- Linked species name in EcoCrop DB
    min_ph                          NUMERIC(4, 2) NOT NULL DEFAULT 5.5
        CHECK (min_ph BETWEEN 0 AND 14),
    opt_min_ph                      NUMERIC(4, 2)
        CHECK (opt_min_ph BETWEEN 0 AND 14),
    opt_max_ph                      NUMERIC(4, 2)
        CHECK (opt_max_ph BETWEEN 0 AND 14),
    max_ph                          NUMERIC(4, 2) NOT NULL DEFAULT 8.5
        CHECK (max_ph BETWEEN 0 AND 14),
    max_ec_ds_m                     NUMERIC(5, 2) NOT NULL DEFAULT 2.5
        CHECK (max_ec_ds_m >= 0),
    suitable_textures               TEXT[] NOT NULL DEFAULT ARRAY['Loam', 'Clay', 'Silt', 'Sandy Loam'],
    min_temp_c                      NUMERIC(5, 2),
    opt_min_temp_c                  NUMERIC(5, 2),
    opt_max_temp_c                  NUMERIC(5, 2),
    max_temp_c                      NUMERIC(5, 2),
    crop_cycle_min_days             SMALLINT,
    crop_cycle_max_days             SMALLINT,

    -- Water requirement database key (links to crop_water_requirements)
    water_key                       VARCHAR(100),
    is_water_proxy                  BOOLEAN NOT NULL DEFAULT FALSE,
    water_proxy_reference           TEXT,   -- Plain-text explanation of the proxy source

    -- Economic benchmarks per feddan (used as fallback defaults)
    default_expected_yield_ton_fed  NUMERIC(8, 2) DEFAULT 5.0,
    default_price_egp_per_ton       NUMERIC(10, 2) DEFAULT 10000.0,
    default_production_cost_egp_fed NUMERIC(10, 2) DEFAULT 8000.0,

    created_at                      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at                      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE crops IS 'Master Crop Registry (Option 1): canonical 53-crop single source of truth with soil/climate tolerances.';
COMMENT ON COLUMN crops.canonical_name_en IS 'Unique canonical English crop name. Always use this for FK references.';
COMMENT ON COLUMN crops.ecocrop_species_reference IS 'EcoCrop curated DB species name for soil/climate lookup.';
COMMENT ON COLUMN crops.water_key IS 'Key into crop_water_requirements table; may be a proxy species.';
COMMENT ON COLUMN crops.is_water_proxy IS 'True when water data belongs to a related species used as proxy.';

-- -----------------------------------------------------------------------------
-- Table 2: CROP_ALIASES
-- Synonym, plural, Arabic, spelling-variant, and dataset-specific alias registry.
-- Allows any external string to be resolved to a canonical crop_id.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS crop_aliases (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    crop_id     UUID NOT NULL REFERENCES crops(id) ON DELETE CASCADE,
    alias_name  VARCHAR(200) NOT NULL,
    source_system VARCHAR(50) NOT NULL DEFAULT 'manual'
        CHECK (source_system IN ('ecocrop', 'water_table', 'rotation', 'seasons', 'arabic', 'user_input', 'manual')),
    match_type  VARCHAR(30) NOT NULL DEFAULT 'exact'
        CHECK (match_type IN ('exact', 'plural', 'proxy', 'synonym', 'subspecies', 'translation', 'spelling')),
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_alias UNIQUE (alias_name)
);

COMMENT ON TABLE crop_aliases IS 'Synonym registry enabling any spelling, Arabic name, or alias to resolve to canonical crop_id.';
COMMENT ON COLUMN crop_aliases.source_system IS 'Which data source introduced this alias.';
COMMENT ON COLUMN crop_aliases.match_type IS 'Classification of how this alias relates to the canonical name.';

-- -----------------------------------------------------------------------------
-- Table 3: CROP_SEASONS
-- Allowed agricultural seasons per canonical crop.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS crop_seasons (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    crop_id     UUID NOT NULL REFERENCES crops(id) ON DELETE CASCADE,
    season      VARCHAR(20) NOT NULL
        CHECK (season IN ('Winter', 'Summer', 'Nili', 'Perennial')),
    notes       TEXT,
    CONSTRAINT unique_crop_season UNIQUE (crop_id, season)
);

COMMENT ON TABLE crop_seasons IS 'Allowable agricultural calendar seasons for each canonical crop.';

-- -----------------------------------------------------------------------------
-- Table 4: CROP_WATER_REQUIREMENTS
-- Measured Egyptian water requirements from egypt_crop_water_requirements.xlsx.
-- Per zone, per season, per crop (or proxy crop).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS crop_water_requirements (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    crop_id                     UUID NOT NULL REFERENCES crops(id) ON DELETE CASCADE,
    water_key                   VARCHAR(100) NOT NULL,  -- Water table lookup key (proxy or direct)
    zone                        VARCHAR(60) NOT NULL
        CHECK (zone IN ('Delta', 'Middle Egypt', 'Upper Egypt', 'Sinai / Reclaimed Lands')),
    season                      VARCHAR(20) NOT NULL
        CHECK (season IN ('Winter', 'Summer', 'Nili', 'Perennial')),
    gross_water_req_mm          NUMERIC(8, 2),    -- Gross seasonal water requirement (mm)
    net_water_req_mm            NUMERIC(8, 2),    -- Net effective rainfall-adjusted requirement (mm)
    gross_water_req_m3_feddan   NUMERIC(10, 2),   -- Converted to m³/feddan (1 mm = 4.2 m³/feddan)
    net_water_req_m3_feddan     NUMERIC(10, 2),
    et_range_min_mm             NUMERIC(8, 2),    -- Seasonal ETcrop range lower bound (mm)
    et_range_max_mm             NUMERIC(8, 2),    -- Seasonal ETcrop range upper bound (mm)
    data_source                 VARCHAR(100) DEFAULT 'egypt_crop_water_requirements.xlsx',
    is_proxy_estimate           BOOLEAN NOT NULL DEFAULT FALSE,
    proxy_note                  TEXT,
    created_at                  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_crop_zone_season UNIQUE (crop_id, zone, season)
);

COMMENT ON TABLE crop_water_requirements IS 'Egyptian measured water requirements per crop, zone, and season (m³/feddan).';
COMMENT ON COLUMN crop_water_requirements.is_proxy_estimate IS 'True if water data is derived from a related species proxy.';

-- -----------------------------------------------------------------------------
-- Table 5: CROP_ROTATION_MATRIX
-- Rotation suitability between all 53x53 preceding-to-candidate crop pairs.
-- Loaded from crop_rotation_matrix_v10_corrected.xlsx.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS crop_rotation_matrix (
    id                   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    preceding_crop_id    UUID NOT NULL REFERENCES crops(id) ON DELETE CASCADE,
    candidate_crop_id    UUID NOT NULL REFERENCES crops(id) ON DELETE CASCADE,
    suitability_score    SMALLINT NOT NULL CHECK (suitability_score IN (0, 1)),
    agronomic_notes      TEXT,
    created_at           TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_rotation_pair UNIQUE (preceding_crop_id, candidate_crop_id)
);

COMMENT ON TABLE crop_rotation_matrix IS 'Agronomic rotation suitability matrix (0=disallowed, 1=recommended) for all 53 crops.';

-- =============================================================================
-- MODULE 2: FARM MANAGEMENT
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Table 6: FARMS
-- Farm entity with geographic location and seasonal resource budgets.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS farms (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                        VARCHAR(255) NOT NULL,
    owner_name                  VARCHAR(255),
    zone                        VARCHAR(100) NOT NULL DEFAULT 'Delta'
        CHECK (zone IN ('Delta', 'Middle Egypt', 'Upper Egypt', 'Sinai / Reclaimed Lands')),
    total_area_feddans          NUMERIC(10, 2) NOT NULL CHECK (total_area_feddans > 0),
    water_budget_m3             NUMERIC(12, 2) NOT NULL CHECK (water_budget_m3 >= 0),
    labor_budget_hours          NUMERIC(10, 2) NOT NULL DEFAULT 2500.0 CHECK (labor_budget_hours >= 0),
    fertilizer_budget_kg        NUMERIC(10, 2) NOT NULL DEFAULT 15000.0 CHECK (fertilizer_budget_kg >= 0),
    labor_rate_egp_per_hour     NUMERIC(8, 2) NOT NULL DEFAULT 20.0 CHECK (labor_rate_egp_per_hour >= 0),
    fertilizer_rate_egp_per_kg  NUMERIC(8, 2) NOT NULL DEFAULT 1.50 CHECK (fertilizer_rate_egp_per_kg >= 0),
    created_at                  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at                  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE farms IS 'Farm entity with region, total area, and available resource budgets per planning cycle.';
COMMENT ON COLUMN farms.zone IS 'Egyptian regional zone affecting water requirements and climate.';
COMMENT ON COLUMN farms.total_area_feddans IS 'Total land area in Egyptian Feddans (1 Feddan = 4200 m²).';

-- -----------------------------------------------------------------------------
-- Table 7: FIELDS
-- Individual field parcels with soil measurements and rotation history.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fields (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    farm_id                 UUID NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
    name_en                 VARCHAR(255) NOT NULL,
    name_ar                 VARCHAR(255),
    area_feddans            NUMERIC(10, 2) NOT NULL CHECK (area_feddans > 0),
    soil_ph                 NUMERIC(4, 2) NOT NULL DEFAULT 6.5 CHECK (soil_ph BETWEEN 0 AND 14),
    soil_ec_ds_m            NUMERIC(5, 2) NOT NULL DEFAULT 1.0 CHECK (soil_ec_ds_m >= 0),
    soil_texture            VARCHAR(50) NOT NULL DEFAULT 'Loam'
        CHECK (soil_texture IN ('Loam', 'Clay', 'Silt', 'Sandy', 'Sandy Loam')),
    organic_matter_pct      NUMERIC(4, 2) NOT NULL DEFAULT 2.0 CHECK (organic_matter_pct >= 0),
    previous_crop_id        UUID REFERENCES crops(id) ON DELETE SET NULL,
    previous_season         VARCHAR(20)
        CHECK (previous_season IN ('Winter', 'Summer', 'Nili', 'Perennial')),
    created_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_field_name_per_farm UNIQUE (farm_id, name_en)
);

COMMENT ON TABLE fields IS 'Field parcels belonging to a farm with soil chemistry and crop rotation history.';
COMMENT ON COLUMN fields.previous_crop_id IS 'FK to crops.id for crop planted in previous season (used for rotation constraint).';
COMMENT ON COLUMN fields.soil_ec_ds_m IS 'Soil salinity in dS/m. Compared against crops.max_ec_ds_m for suitability filter.';

-- =============================================================================
-- MODULE 3: OPTIMIZATION PLANS
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Table 8: OPTIMIZATION_PLANS
-- Output summary and financial performance from LP optimization runs.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS optimization_plans (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    farm_id                     UUID NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
    season                      VARCHAR(20) NOT NULL DEFAULT 'Winter'
        CHECK (season IN ('Winter', 'Summer', 'Nili', 'Perennial')),
    optimizer_version           VARCHAR(20) NOT NULL DEFAULT 'v4',
    status                      VARCHAR(50) NOT NULL,
    is_feasible                 BOOLEAN NOT NULL DEFAULT TRUE,
    total_land_used_feddans     NUMERIC(10, 2) NOT NULL,
    total_water_used_m3         NUMERIC(12, 2) NOT NULL,
    total_labor_used_hours      NUMERIC(10, 2) NOT NULL,
    total_fertilizer_used_kg    NUMERIC(10, 2) NOT NULL,
    total_expected_revenue_egp  NUMERIC(14, 2) NOT NULL,
    total_production_cost_egp   NUMERIC(14, 2) NOT NULL,
    total_labor_cost_egp        NUMERIC(14, 2) NOT NULL,
    total_fertilizer_cost_egp   NUMERIC(14, 2) NOT NULL,
    net_profit_egp              NUMERIC(14, 2) NOT NULL,
    binding_constraints         JSONB,
    ai_synthesis_explanation    TEXT,
    created_at                  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE optimization_plans IS 'Historical record of LP optimization runs with aggregate financials and constraints.';

-- -----------------------------------------------------------------------------
-- Table 9: PLAN_FIELD_ALLOCATIONS
-- Field-by-field crop allocation breakdown for a specific optimization plan.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS plan_field_allocations (
    id                              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_id                         UUID NOT NULL REFERENCES optimization_plans(id) ON DELETE CASCADE,
    field_id                        UUID NOT NULL REFERENCES fields(id) ON DELETE CASCADE,
    crop_id                         UUID NOT NULL REFERENCES crops(id) ON DELETE CASCADE,
    allocated_area_feddans          NUMERIC(10, 2) NOT NULL CHECK (allocated_area_feddans >= 0),
    water_used_m3                   NUMERIC(12, 2),
    labor_used_hours                NUMERIC(10, 2),
    fertilizer_used_kg              NUMERIC(10, 2),
    expected_revenue_egp            NUMERIC(14, 2),
    production_cost_egp             NUMERIC(14, 2),
    labor_cost_egp                  NUMERIC(14, 2),
    fertilizer_cost_egp             NUMERIC(14, 2),
    net_profit_egp                  NUMERIC(14, 2),
    profit_margin_pct               NUMERIC(6, 2),
    soil_suitable                   BOOLEAN DEFAULT TRUE,
    rotation_suitable               BOOLEAN DEFAULT TRUE,
    created_at                      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_field_crop_per_plan UNIQUE (plan_id, field_id, crop_id)
);

COMMENT ON TABLE plan_field_allocations IS 'Per-field, per-crop area allocations and financial breakdown within an optimization plan.';

-- =============================================================================
-- MODULE 4: MULTI-SEASON PLANNING
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Table 10: MULTI_SEASON_SESSIONS
-- Container for rolling multi-season planning sessions.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS multi_season_sessions (
    id                              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    farm_id                         UUID NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
    session_key                     VARCHAR(100) NOT NULL,   -- Application-level session identifier
    candidate_crops_list            TEXT[],                  -- Canonical crop names selected at session start
    current_season_number           SMALLINT NOT NULL DEFAULT 1,
    current_water_budget_m3         NUMERIC(12, 2),
    current_labor_budget_hours      NUMERIC(10, 2),
    current_fertilizer_budget_kg    NUMERIC(10, 2),
    status                          VARCHAR(30) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'completed', 'archived')),
    created_at                      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at                      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_session_per_farm UNIQUE (farm_id, session_key)
);

COMMENT ON TABLE multi_season_sessions IS 'Rolling multi-season planning session tracking candidate crops and current budgets.';

-- -----------------------------------------------------------------------------
-- Table 11: SEASON_PLANS
-- Results of each planned season within a multi-season session.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS season_plans (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id                  UUID NOT NULL REFERENCES multi_season_sessions(id) ON DELETE CASCADE,
    optimization_plan_id        UUID REFERENCES optimization_plans(id) ON DELETE SET NULL,
    season_number               SMALLINT NOT NULL,
    season_name                 VARCHAR(20) NOT NULL
        CHECK (season_name IN ('Winter', 'Summer', 'Nili', 'Perennial')),
    is_current_season           BOOLEAN NOT NULL DEFAULT FALSE,  -- TRUE only for Season 1 (soil suitability active)
    soil_suitability_active     BOOLEAN NOT NULL DEFAULT FALSE,  -- Disabled for Season 2+
    water_budget_m3             NUMERIC(12, 2) NOT NULL,
    labor_budget_hours          NUMERIC(10, 2) NOT NULL,
    fertilizer_budget_kg        NUMERIC(10, 2) NOT NULL,
    total_area_used_feddans     NUMERIC(10, 2),
    total_water_used_m3         NUMERIC(12, 2),
    total_labor_used_hours      NUMERIC(10, 2),
    total_fertilizer_used_kg    NUMERIC(10, 2),
    total_expected_revenue_egp  NUMERIC(14, 2),
    total_production_cost_egp   NUMERIC(14, 2),
    total_labor_cost_egp        NUMERIC(14, 2),
    total_fertilizer_cost_egp   NUMERIC(14, 2),
    net_profit_egp              NUMERIC(14, 2),
    profit_margin_pct           NUMERIC(6, 2),
    explanation_note            TEXT,
    created_at                  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_season_per_session UNIQUE (session_id, season_number)
);

COMMENT ON TABLE season_plans IS 'One planned season within a rolling multi-season session. Soil suitability active only for Season 1.';

-- -----------------------------------------------------------------------------
-- Table 12: SEASON_FIELD_ALLOCATIONS
-- Per-field crop allocations for a specific season plan.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS season_field_allocations (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    season_plan_id              UUID NOT NULL REFERENCES season_plans(id) ON DELETE CASCADE,
    field_id                    UUID NOT NULL REFERENCES fields(id) ON DELETE CASCADE,
    crop_id                     UUID NOT NULL REFERENCES crops(id) ON DELETE CASCADE,
    preceding_crop_id           UUID REFERENCES crops(id) ON DELETE SET NULL, -- Previous season crop (for rotation check)
    allocated_area_feddans      NUMERIC(10, 2) NOT NULL CHECK (allocated_area_feddans >= 0),
    net_profit_egp              NUMERIC(14, 2),
    rotation_suitable           BOOLEAN DEFAULT TRUE,
    soil_suitable               BOOLEAN DEFAULT TRUE,
    created_at                  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_season_field_crop UNIQUE (season_plan_id, field_id, crop_id)
);

COMMENT ON TABLE season_field_allocations IS 'Per-field, per-crop allocations for a single season plan, including rotation history chain.';

-- =============================================================================
-- MODULE 5: RISK SCENARIO ANALYSIS (CVaR)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Table 13: RISK_SCENARIOS
-- Catalog of economic/environmental stress scenarios for CVaR analysis.
-- Includes both synthetic scenarios and FAOSTAT-calibrated market data.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS risk_scenarios (
    id                              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scenario_id                     VARCHAR(50) NOT NULL UNIQUE,  -- e.g. 'normal', 'water_stress', 'market_downturn'
    name_en                         VARCHAR(150) NOT NULL,
    name_ar                         VARCHAR(150),
    description_en                  TEXT,
    description_ar                  TEXT,
    probability                     NUMERIC(6, 5) NOT NULL CHECK (probability > 0 AND probability <= 1),
    risk_category                   VARCHAR(50) NOT NULL
        CHECK (risk_category IN ('Baseline', 'Water', 'Climate', 'Market', 'Input', 'Combined')),
    severity                        VARCHAR(20) NOT NULL
        CHECK (severity IN ('Low', 'Medium', 'High', 'Extreme')),
    is_calibrated                   BOOLEAN NOT NULL DEFAULT FALSE,  -- TRUE if from FAOSTAT/official data
    data_source                     VARCHAR(200),
    -- Default multipliers for crops not explicitly listed in risk_scenario_crop_profiles
    default_yield_multiplier        NUMERIC(5, 3) NOT NULL DEFAULT 1.0,
    default_price_multiplier        NUMERIC(5, 3) NOT NULL DEFAULT 1.0,
    default_production_cost_mult    NUMERIC(5, 3) NOT NULL DEFAULT 1.0,
    default_labor_cost_mult         NUMERIC(5, 3) NOT NULL DEFAULT 1.0,
    default_fertilizer_cost_mult    NUMERIC(5, 3) NOT NULL DEFAULT 1.0,
    created_at                      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE risk_scenarios IS 'CVaR stress scenario catalog. Probabilities must sum to 1.0 across all active scenarios.';
COMMENT ON COLUMN risk_scenarios.is_calibrated IS 'TRUE if scenario data comes from FAOSTAT or official statistical sources.';

-- -----------------------------------------------------------------------------
-- Table 14: RISK_SCENARIO_CROP_PROFILES
-- Per-crop multipliers within each risk scenario.
-- Crops not listed use the scenario default multipliers.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS risk_scenario_crop_profiles (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scenario_id                 UUID NOT NULL REFERENCES risk_scenarios(id) ON DELETE CASCADE,
    crop_id                     UUID NOT NULL REFERENCES crops(id) ON DELETE CASCADE,
    yield_multiplier            NUMERIC(5, 3) NOT NULL DEFAULT 1.0 CHECK (yield_multiplier > 0),
    price_multiplier            NUMERIC(5, 3) NOT NULL DEFAULT 1.0 CHECK (price_multiplier > 0),
    production_cost_mult        NUMERIC(5, 3) NOT NULL DEFAULT 1.0 CHECK (production_cost_mult > 0),
    labor_cost_mult             NUMERIC(5, 3) NOT NULL DEFAULT 1.0 CHECK (labor_cost_mult > 0),
    fertilizer_cost_mult        NUMERIC(5, 3) NOT NULL DEFAULT 1.0 CHECK (fertilizer_cost_mult > 0),
    notes                       TEXT,
    created_at                  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_scenario_crop UNIQUE (scenario_id, crop_id)
);

COMMENT ON TABLE risk_scenario_crop_profiles IS 'Per-crop stress multipliers for a specific risk scenario. Unlisted crops use scenario defaults.';

-- -----------------------------------------------------------------------------
-- Table 15: RISK_ANALYSIS_RESULTS
-- Stored CVaR analysis outputs per farm/plan, comparing risk modes.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS risk_analysis_results (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    farm_id                     UUID NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
    plan_id                     UUID REFERENCES optimization_plans(id) ON DELETE SET NULL,
    season                      VARCHAR(20) NOT NULL
        CHECK (season IN ('Winter', 'Summer', 'Nili', 'Perennial')),
    analysis_mode               VARCHAR(30) NOT NULL
        CHECK (analysis_mode IN ('max_profit', 'balanced', 'risk_averse')),
    alpha_cvar                  NUMERIC(4, 3) NOT NULL DEFAULT 0.95,  -- Confidence level for CVaR (e.g. 0.95)
    weight_profit               NUMERIC(4, 3),  -- Profit weight in objective (0-1)
    weight_cvar                 NUMERIC(4, 3),  -- CVaR weight in objective (0-1)
    expected_profit_egp         NUMERIC(14, 2),
    var_95_egp                  NUMERIC(14, 2),  -- Value-at-Risk at 95% confidence
    cvar_95_egp                 NUMERIC(14, 2),  -- Conditional VaR (Expected Shortfall)
    std_dev_egp                 NUMERIC(14, 2),
    min_scenario_profit_egp     NUMERIC(14, 2),
    max_scenario_profit_egp     NUMERIC(14, 2),
    scenario_profits            JSONB,           -- Dict of scenario_id -> profit
    total_land_used_feddans     NUMERIC(10, 2),
    total_water_used_m3         NUMERIC(12, 2),
    status                      VARCHAR(50),
    is_feasible                 BOOLEAN,
    created_at                  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE risk_analysis_results IS 'CVaR risk analysis output comparing max_profit, balanced, and risk_averse optimization modes.';
COMMENT ON COLUMN risk_analysis_results.cvar_95_egp IS 'Expected profit in the worst 5% of scenarios (Conditional VaR at 95%).';

-- =============================================================================
-- MODULE 6: FARM-SPECIFIC CROP PARAMETERS
-- Allow farm-level overrides of default crop economic parameters.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Table 16: FARM_CROP_PARAMETERS
-- Farm-specific crop economic parameters, overriding global crop defaults.
-- NULL farm_id = global catalog entry. Non-NULL = farm override.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS farm_crop_parameters (
    id                              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    farm_id                         UUID REFERENCES farms(id) ON DELETE CASCADE,  -- NULL = global default
    crop_id                         UUID NOT NULL REFERENCES crops(id) ON DELETE CASCADE,
    expected_yield_ton_fed          NUMERIC(8, 2) NOT NULL CHECK (expected_yield_ton_fed > 0),
    price_egp_per_ton               NUMERIC(10, 2) NOT NULL CHECK (price_egp_per_ton >= 0),
    production_cost_egp_per_fed     NUMERIC(10, 2) NOT NULL CHECK (production_cost_egp_per_fed >= 0),
    water_requirement_m3_per_fed    NUMERIC(10, 2) NOT NULL CHECK (water_requirement_m3_per_fed >= 0),
    labor_requirement_hrs_per_fed   NUMERIC(8, 2) DEFAULT 0.0,
    fertilizer_requirement_kg_per_fed NUMERIC(8, 2) DEFAULT 0.0,
    created_at                      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_farm_crop UNIQUE (farm_id, crop_id)
);

COMMENT ON TABLE farm_crop_parameters IS 'Farm-specific economic parameters for crops. NULL farm_id = global default catalog.';

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_crops_canonical_name ON crops(canonical_name_en);
CREATE INDEX IF NOT EXISTS idx_crops_category ON crops(category);
CREATE INDEX IF NOT EXISTS idx_crops_is_perennial ON crops(is_perennial);

CREATE INDEX IF NOT EXISTS idx_crop_aliases_crop_id ON crop_aliases(crop_id);
CREATE INDEX IF NOT EXISTS idx_crop_aliases_name ON crop_aliases(alias_name);

CREATE INDEX IF NOT EXISTS idx_crop_seasons_crop_id ON crop_seasons(crop_id);
CREATE INDEX IF NOT EXISTS idx_crop_seasons_season ON crop_seasons(season);

CREATE INDEX IF NOT EXISTS idx_water_reqs_crop_id ON crop_water_requirements(crop_id);
CREATE INDEX IF NOT EXISTS idx_water_reqs_zone_season ON crop_water_requirements(zone, season);
CREATE INDEX IF NOT EXISTS idx_water_reqs_water_key ON crop_water_requirements(water_key);

CREATE INDEX IF NOT EXISTS idx_rotation_preceding ON crop_rotation_matrix(preceding_crop_id);
CREATE INDEX IF NOT EXISTS idx_rotation_candidate ON crop_rotation_matrix(candidate_crop_id);
CREATE INDEX IF NOT EXISTS idx_rotation_score ON crop_rotation_matrix(suitability_score);

CREATE INDEX IF NOT EXISTS idx_fields_farm_id ON fields(farm_id);
CREATE INDEX IF NOT EXISTS idx_fields_prev_crop ON fields(previous_crop_id);

CREATE INDEX IF NOT EXISTS idx_plans_farm_id ON optimization_plans(farm_id);
CREATE INDEX IF NOT EXISTS idx_plans_season ON optimization_plans(season);
CREATE INDEX IF NOT EXISTS idx_allocations_plan_id ON plan_field_allocations(plan_id);
CREATE INDEX IF NOT EXISTS idx_allocations_field_id ON plan_field_allocations(field_id);
CREATE INDEX IF NOT EXISTS idx_allocations_crop_id ON plan_field_allocations(crop_id);

CREATE INDEX IF NOT EXISTS idx_multi_sessions_farm ON multi_season_sessions(farm_id);
CREATE INDEX IF NOT EXISTS idx_season_plans_session ON season_plans(session_id);
CREATE INDEX IF NOT EXISTS idx_season_alloc_plan ON season_field_allocations(season_plan_id);
CREATE INDEX IF NOT EXISTS idx_season_alloc_field ON season_field_allocations(field_id);

CREATE INDEX IF NOT EXISTS idx_risk_scenarios_scenario_id ON risk_scenarios(scenario_id);
CREATE INDEX IF NOT EXISTS idx_risk_profiles_scenario ON risk_scenario_crop_profiles(scenario_id);
CREATE INDEX IF NOT EXISTS idx_risk_profiles_crop ON risk_scenario_crop_profiles(crop_id);
CREATE INDEX IF NOT EXISTS idx_risk_results_farm ON risk_analysis_results(farm_id);
CREATE INDEX IF NOT EXISTS idx_risk_results_mode ON risk_analysis_results(analysis_mode);

CREATE INDEX IF NOT EXISTS idx_farm_crop_params_farm ON farm_crop_parameters(farm_id);
CREATE INDEX IF NOT EXISTS idx_farm_crop_params_crop ON farm_crop_parameters(crop_id);

-- =============================================================================
-- CANONICAL SEED DATA: RISK SCENARIOS (6 scenarios, probability sum = 1.0)
-- =============================================================================
INSERT INTO risk_scenarios (scenario_id, name_en, name_ar, description_en, probability,
    risk_category, severity, is_calibrated, data_source,
    default_yield_multiplier, default_price_multiplier,
    default_production_cost_mult, default_labor_cost_mult, default_fertilizer_cost_mult)
VALUES
    ('normal',          'Normal Conditions',        'ظروف عادية',
     'Typical season: yields and prices near expected values.',
     0.4500, 'Baseline', 'Low', FALSE, 'synthetic_model',
     1.00, 1.00, 1.00, 1.00, 1.00),

    ('water_stress',    'Water Stress',             'إجهاد مائي',
     'Nile flow reduction or groundwater depletion causing irrigation shortfall.',
     0.1800, 'Water',    'High', FALSE, 'synthetic_model',
     0.80, 0.90, 1.05, 1.00, 1.00),

    ('heat_stress',     'Extreme Heat Stress',      'إجهاد حرارة شديدة',
     'Temperatures above 42°C damaging summer crop yields.',
     0.1200, 'Climate',  'High', FALSE, 'synthetic_model',
     0.80, 1.00, 1.00, 1.05, 1.00),

    ('market_downturn', 'Market Price Downturn',    'انخفاض أسعار السوق',
     'Commodity price collapse due to oversupply or reduced export demand.',
     0.1200, 'Market',   'High', TRUE,  'FAOSTAT producer price calibration',
     1.00, 0.75, 1.00, 1.00, 1.00),

    ('input_inflation', 'Input Cost Inflation',     'تضخم تكاليف المدخلات',
     'Fertilizer and energy price spikes from global supply disruptions.',
     0.0800, 'Input',    'Medium', TRUE, 'FAOSTAT/FAO fertilizer price data',
     1.00, 1.00, 1.10, 1.05, 1.45),

    ('severe_combined', 'Severe Combined Stress',   'ضغط مركب شديد',
     'Rare catastrophic combination of yield loss, price collapse, and cost inflation.',
     0.0500, 'Combined', 'Extreme', FALSE, 'synthetic_tail_risk',
     0.60, 0.70, 1.20, 1.10, 1.40)

ON CONFLICT (scenario_id) DO NOTHING;

-- =============================================================================
-- USEFUL VIEWS
-- =============================================================================

-- View: Resolve any alias to canonical crop info
CREATE OR REPLACE VIEW crop_alias_lookup AS
SELECT
    ca.alias_name,
    ca.source_system,
    ca.match_type,
    c.id            AS crop_id,
    c.canonical_name_en,
    c.canonical_name_ar,
    c.scientific_name,
    c.crop_family,
    c.category,
    c.is_perennial,
    c.water_key,
    c.is_water_proxy
FROM crop_aliases ca
JOIN crops c ON ca.crop_id = c.id;

COMMENT ON VIEW crop_alias_lookup IS 'Resolves any alias string to full canonical crop metadata.';

-- View: Water requirements with crop metadata
CREATE OR REPLACE VIEW crop_water_summary AS
SELECT
    c.canonical_name_en,
    c.canonical_name_ar,
    c.category,
    w.zone,
    w.season,
    w.gross_water_req_m3_feddan,
    w.net_water_req_m3_feddan,
    w.is_proxy_estimate,
    w.proxy_note
FROM crop_water_requirements w
JOIN crops c ON w.crop_id = c.id;

COMMENT ON VIEW crop_water_summary IS 'Water requirements per crop, zone, and season with canonical names.';

-- View: Multi-season financial rollup per session
CREATE OR REPLACE VIEW multi_season_summary AS
SELECT
    mss.id AS session_id,
    mss.session_key,
    f.name AS farm_name,
    f.zone,
    COUNT(sp.id) AS seasons_planned,
    SUM(sp.total_expected_revenue_egp) AS cumulative_revenue_egp,
    SUM(sp.net_profit_egp) AS cumulative_profit_egp,
    AVG(sp.profit_margin_pct) AS avg_profit_margin_pct,
    mss.status,
    mss.created_at
FROM multi_season_sessions mss
JOIN farms f ON mss.farm_id = f.id
LEFT JOIN season_plans sp ON sp.session_id = mss.id
GROUP BY mss.id, mss.session_key, f.name, f.zone, mss.status, mss.created_at;

COMMENT ON VIEW multi_season_summary IS 'Rolling financial rollup for each multi-season planning session.';
