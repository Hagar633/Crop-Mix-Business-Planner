# 🗄️ Database & API Integration Guide

This document defines the relational database architecture and API communication contract for the **Crop Mix Business Planner**.

---

## 1. Relational Database Schema (`docs/schema.sql`)

The database is designed for PostgreSQL / MySQL / SQL Server and comprises 6 relational tables:

```mermaid
erDiagram
    FARMS ||--o{ FIELDS : "contains"
    FARMS ||--o{ CROPS : "owns custom"
    FARMS ||--o{ OPTIMIZATION_PLANS : "executes"
    OPTIMIZATION_PLANS ||--o{ PLAN_FIELD_ALLOCATIONS : "allocates"
    FIELDS ||--o{ PLAN_FIELD_ALLOCATIONS : "receives"
    CROPS ||--o{ PLAN_FIELD_ALLOCATIONS : "planted in"

    FARMS {
        uuid id PK
        string name
        string zone
        numeric total_area_feddans
        numeric water_budget_m3
        numeric labor_budget_hours
        numeric fertilizer_budget_kg
    }

    FIELDS {
        uuid id PK
        uuid farm_id FK
        string name_en
        string name_ar
        numeric area_feddans
        numeric soil_ph
        numeric soil_ec_ds_m
        string soil_texture
        string previous_crop_name
    }

    CROPS {
        uuid id PK
        uuid farm_id FK
        string name_en
        string name_ar
        numeric expected_yield_tons_per_feddan
        numeric price_egp_per_ton
        numeric production_cost_egp_per_feddan
        numeric water_requirement_m3_per_feddan
        numeric labor_requirement_hours_per_feddan
        numeric fertilizer_requirement_kg_per_feddan
    }

    CROP_ROTATION_MATRIX {
        uuid id PK
        string previous_crop_name
        string candidate_crop_name
        int suitability_score
    }

    OPTIMIZATION_PLANS {
        uuid id PK
        uuid farm_id FK
        string season
        string optimizer_version
        string status
        boolean is_feasible
        numeric net_profit_egp
        jsonb binding_constraints
        text ai_synthesis_explanation
    }

    PLAN_FIELD_ALLOCATIONS {
        uuid id PK
        uuid plan_id FK
        uuid field_id FK
        uuid crop_id FK
        numeric allocated_area_feddans
        numeric expected_profit_contribution_egp
    }
```

---

## 2. Table Summary

| Table | Description | Primary Key | Foreign Keys |
|---|---|---|---|
| **`farms`** | Stores farm metadata, Egyptian regional zone, and global seasonal resource budgets. | `id` (UUID) | None |
| **`fields`** | Land parcel boundaries, soil chemistry (pH, EC salinity, texture), and crop history. | `id` (UUID) | `farm_id` $\to$ `farms(id)` |
| **`crops`** | Financial benchmarks, water/labor/fertilizer requirements, and soil tolerance bounds. | `id` (UUID) | `farm_id` $\to$ `farms(id)` (NULL for global catalog) |
| **`crop_rotation_matrix`** | Source of truth rotation suitability scores (0 or 1) between previous & next crop. | `id` (UUID) | None |
| **`optimization_plans`** | Historical record of executed optimization runs, status, financials, and AI notes. | `id` (UUID) | `farm_id` $\to$ `farms(id)` |
| **`plan_field_allocations`** | Exact feddan allocations of crops to fields for a saved optimization plan. | `id` (UUID) | `plan_id` $\to$ `optimization_plans(id)`, `field_id`, `crop_id` |

---

## 3. Postman Collection (`docs/postman_collection.json`)

The accompanying Postman Collection (`docs/postman_collection.json`) provides ready-to-import requests for:

1. **Farm Management & Budgets**
   - `POST /api/farms` — Create farm & set resource budgets
   - `GET /api/farms/:farm_id` — Fetch farm profile & registered fields
2. **Fields & Soil Measurements**
   - `POST /api/farms/:farm_id/fields` — Add land parcel & soil chemistry
   - `GET /api/farms/:farm_id/fields` — List all farm fields
3. **Crop Catalog & Rotation Matrix**
   - `GET /api/ecocrop/crops` — Fetch EcoCrop catalog
   - `GET /api/rotation/matrix` — Fetch rotation suitability rules
4. **Optimization Engine & Plan Storage**
   - `POST /api/optimize` — Run Pyomo + HiGHS V4 Optimizer
   - `POST /api/plans` — Save optimization plan & allocations to DB
   - `GET /api/plans/:plan_id` — Retrieve historical plan

---

## 4. How the Teams Interact

```mermaid
sequenceDiagram
    autonumber
    actor Farmer as Web UI / User
    participant DBTeam as Database API (DB Team)
    participant OptEngine as Optimization Engine (FastAPI)

    Farmer->>DBTeam: 1. Save/Load Farm, Fields & Crops
    DBTeam-->>Farmer: Return Farm Data & Soil Measurements
    Farmer->>OptEngine: 2. POST /api/optimize (Fields, Crops, Budgets)
    OptEngine->>OptEngine: Execute Pyomo + HiGHS LP Solver V4
    OptEngine-->>Farmer: 3. Return Optimal Allocations & Net Profit
    Farmer->>DBTeam: 4. POST /api/plans (Save Final Plan & Allocations)
    DBTeam-->>Farmer: 5. Return Saved Plan ID
```
