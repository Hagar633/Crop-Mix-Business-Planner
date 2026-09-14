-- =============================================================================
-- CROP MIX BUSINESS PLANNER - DATABASE SCHEMA DDL (PostgreSQL Compatible)
-- Version: 1.0.0
-- Purpose: Schema for Farm Management, Soil Parameters, Crop Rotation, and Optimization Results
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- -----------------------------------------------------------------------------
-- Table 1: FARMS
-- Stores farm metadata, geographic location, and seasonal resource budgets
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS farms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    owner_name VARCHAR(255),
    zone VARCHAR(100) NOT NULL DEFAULT 'Delta' 
        CHECK (zone IN ('Delta', 'Middle Egypt', 'Upper Egypt', 'Sinai / Reclaimed Lands')),
    total_area_feddans NUMERIC(10, 2) NOT NULL CHECK (total_area_feddans > 0),
    water_budget_m3 NUMERIC(12, 2) NOT NULL CHECK (water_budget_m3 >= 0),
    labor_budget_hours NUMERIC(10, 2) NOT NULL DEFAULT 2500.0 CHECK (labor_budget_hours >= 0),
    fertilizer_budget_kg NUMERIC(10, 2) NOT NULL DEFAULT 15000.0 CHECK (fertilizer_budget_kg >= 0),
    labor_rate_egp_per_hour NUMERIC(8, 2) NOT NULL DEFAULT 20.0 CHECK (labor_rate_egp_per_hour >= 0),
    fertilizer_rate_egp_per_kg NUMERIC(8, 2) NOT NULL DEFAULT 1.50 CHECK (fertilizer_rate_egp_per_kg >= 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE farms IS 'Stores farm entity details, region, and available resource budgets.';
COMMENT ON COLUMN farms.zone IS 'Egyptian regional zone: Delta, Middle Egypt, Upper Egypt, Sinai / Reclaimed Lands';
COMMENT ON COLUMN farms.total_area_feddans IS 'Total farm land capacity in Egyptian Feddans (1 Feddan = 4200 m2)';

-- -----------------------------------------------------------------------------
-- Table 2: FIELDS
-- Stores individual land parcel boundaries, soil chemistry, and crop history
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fields (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    farm_id UUID NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
    name_en VARCHAR(255) NOT NULL,
    name_ar VARCHAR(255),
    area_feddans NUMERIC(10, 2) NOT NULL CHECK (area_feddans > 0),
    soil_ph NUMERIC(4, 2) NOT NULL DEFAULT 6.5 CHECK (soil_ph BETWEEN 0 AND 14),
    soil_ec_ds_m NUMERIC(5, 2) NOT NULL DEFAULT 1.0 CHECK (soil_ec_ds_m >= 0),
    soil_texture VARCHAR(50) NOT NULL DEFAULT 'Loam'
        CHECK (soil_texture IN ('Loam', 'Clay', 'Silt', 'Sandy', 'Sandy Loam')),
    organic_matter_pct NUMERIC(4, 2) NOT NULL DEFAULT 2.0 CHECK (organic_matter_pct >= 0),
    previous_crop_name VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_field_name_per_farm UNIQUE (farm_id, name_en)
);

COMMENT ON TABLE fields IS 'Field parcels belonging to a farm with soil chemistry and rotation history.';
COMMENT ON COLUMN fields.soil_ec_ds_m IS 'Electrical Conductivity measuring soil salinity in dS/m.';
COMMENT ON COLUMN fields.previous_crop_name IS 'Name of crop cultivated in previous season (used for rotation matrix checks).';

-- -----------------------------------------------------------------------------
-- Table 3: CROPS & AGRONOMIC PARAMETERS
-- Catalog of crops, market prices, cost structures, and soil tolerance bounds
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS crops (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    farm_id UUID REFERENCES farms(id) ON DELETE CASCADE, -- NULL means global standard crop catalog
    name_en VARCHAR(100) NOT NULL,
    name_ar VARCHAR(100) NOT NULL,
    category VARCHAR(50) DEFAULT 'General'
        CHECK (category IN ('Cereal', 'Vegetable', 'Legume', 'Fruit', 'Oilseed', 'Fiber', 'Forage', 'General')),
    expected_yield_tons_per_feddan NUMERIC(8, 2) NOT NULL CHECK (expected_yield_tons_per_feddan > 0),
    price_egp_per_ton NUMERIC(10, 2) NOT NULL CHECK (price_egp_per_ton >= 0),
    production_cost_egp_per_feddan NUMERIC(10, 2) NOT NULL CHECK (production_cost_egp_per_feddan >= 0),
    water_requirement_m3_per_feddan NUMERIC(10, 2) NOT NULL CHECK (water_requirement_m3_per_feddan >= 0),
    labor_requirement_hours_per_feddan NUMERIC(8, 2) DEFAULT 0.0 CHECK (labor_requirement_hours_per_feddan >= 0),
    fertilizer_requirement_kg_per_feddan NUMERIC(8, 2) DEFAULT 0.0 CHECK (fertilizer_requirement_kg_per_feddan >= 0),
    min_ph NUMERIC(4, 2) DEFAULT 4.5 CHECK (min_ph BETWEEN 0 AND 14),
    max_ph NUMERIC(4, 2) DEFAULT 8.5 CHECK (max_ph BETWEEN 0 AND 14),
    max_ec_ds_m NUMERIC(5, 2) DEFAULT 3.5 CHECK (max_ec_ds_m >= 0),
    suitable_textures TEXT[] DEFAULT ARRAY['Loam', 'Clay', 'Silt', 'Sandy', 'Sandy Loam'],
    is_perennial BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_crop_name_per_scope UNIQUE (farm_id, name_en)
);

COMMENT ON TABLE crops IS 'Agronomic parameters, financial benchmarks, and soil tolerance bounds for crops.';

-- -----------------------------------------------------------------------------
-- Table 4: CROP ROTATION SUITABILITY MATRIX
-- Matrix mapping previous crop to candidate next crop suitability (0 or 1)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS crop_rotation_matrix (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    previous_crop_name VARCHAR(100) NOT NULL,
    candidate_crop_name VARCHAR(100) NOT NULL,
    suitability_score SMALLINT NOT NULL CHECK (suitability_score IN (0, 1)),
    agronomic_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_rotation_pair UNIQUE (previous_crop_name, candidate_crop_name)
);

COMMENT ON TABLE crop_rotation_matrix IS 'Agri-source of truth matrix dictating allowable crop sequences.';

-- -----------------------------------------------------------------------------
-- Table 5: OPTIMIZATION PLANS (RUN HISTORY)
-- Output summary, financial performance, and AI synthesis from optimization runs
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS optimization_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    farm_id UUID NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
    season VARCHAR(50) NOT NULL DEFAULT 'Winter'
        CHECK (season IN ('Winter', 'Summer', 'Nili', 'Perennial')),
    optimizer_version VARCHAR(20) NOT NULL DEFAULT 'v4',
    status VARCHAR(50) NOT NULL,
    is_feasible BOOLEAN NOT NULL DEFAULT TRUE,
    total_land_used_feddans NUMERIC(10, 2) NOT NULL,
    total_water_used_m3 NUMERIC(12, 2) NOT NULL,
    total_labor_used_hours NUMERIC(10, 2) NOT NULL,
    total_fertilizer_used_kg NUMERIC(10, 2) NOT NULL,
    total_expected_revenue_egp NUMERIC(14, 2) NOT NULL,
    total_production_cost_egp NUMERIC(14, 2) NOT NULL,
    total_labor_cost_egp NUMERIC(14, 2) NOT NULL,
    total_fertilizer_cost_egp NUMERIC(14, 2) NOT NULL,
    net_profit_egp NUMERIC(14, 2) NOT NULL,
    binding_constraints JSONB,
    ai_synthesis_explanation TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE optimization_plans IS 'Historical record of executed mathematical optimization runs and overall financials.';

-- -----------------------------------------------------------------------------
-- Table 6: PLAN FIELD ALLOCATIONS
-- Field-by-field crop allocations for a specific optimization plan
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS plan_field_allocations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_id UUID NOT NULL REFERENCES optimization_plans(id) ON DELETE CASCADE,
    field_id UUID NOT NULL REFERENCES fields(id) ON DELETE CASCADE,
    crop_id UUID NOT NULL REFERENCES crops(id) ON DELETE CASCADE,
    allocated_area_feddans NUMERIC(10, 2) NOT NULL CHECK (allocated_area_feddans >= 0),
    expected_profit_contribution_egp NUMERIC(14, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_field_crop_per_plan UNIQUE (plan_id, field_id, crop_id)
);

COMMENT ON TABLE plan_field_allocations IS 'Exact feddan allocations of crops to fields for a given optimization plan.';

-- -----------------------------------------------------------------------------
-- INDEXES FOR PERFORMANCE OPTIMIZATION
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_fields_farm_id ON fields(farm_id);
CREATE INDEX IF NOT EXISTS idx_crops_farm_id ON crops(farm_id);
CREATE INDEX IF NOT EXISTS idx_crops_name_en ON crops(name_en);
CREATE INDEX IF NOT EXISTS idx_rotation_prev_cand ON crop_rotation_matrix(previous_crop_name, candidate_crop_name);
CREATE INDEX IF NOT EXISTS idx_plans_farm_id ON optimization_plans(farm_id);
CREATE INDEX IF NOT EXISTS idx_allocations_plan_id ON plan_field_allocations(plan_id);
CREATE INDEX IF NOT EXISTS idx_allocations_field_id ON plan_field_allocations(field_id);
