# Crop-Mix-Business-Planner

An agricultural decision-support and crop-mix optimization system that recommends how to allocate farm land among crops while considering **profitability, water, labor, fertilizer, soil suitability, crop rotation, multi-season planning, and financial risk**.

Built with **Python, Pyomo, HiGHS, FastAPI, JavaScript, and LLM-based explanations**.

The system is designed around Egyptian agricultural conditions, with an **Arabic-first interface** and support for Egyptian agricultural terminology and **feddan/hectare unit conversion**.

---

## Key Features

*  Crop-mix optimization
*  Multi-field farm planning
*  Water budget constraints
*  Labor budget constraints
*  Fertilizer budget constraints
*  Field-level soil suitability
*  Crop rotation constraints
*  Multi-season planning
*  Profit and financial projections
*  Risk analysis using VaR and CVaR
*  Scenario-based risk optimization
*  Arabic-first agricultural interface
*  Feddan/hectare unit conversion
*  LLM-generated explanations of optimization results
*  FastAPI backend
*  Docker/Render deployment support

---

# Crop-Mix-Business-Planner

A crop-mix optimization solver that recommends how to allocate farm land among different crops while maximizing expected profit.

Built using **Python, Pyomo, and HiGHS**.

## Versions

### V1 — Basic Optimization

Considers:
- Land availability
- Water budget
- Crop yield
- Crop price
- Production cost

### V2 — Labor & Fertilizer

Adds:
- Labor requirements and costs
- Fertilizer requirements and costs
- Labor budget
- Fertilizer budget

### V3 — Field & Soil Suitability

Adds:
- Multiple fields
- Field-level crop allocation
- Soil pH
- Soil EC
- Soil texture
- Crop soil requirements

The system checks whether each crop is suitable for each field and prevents unsuitable crops from being allocated.

### V4 — Crop Rotation + Financial Forecasting

Adds:
- Previous-crop rotation constraints
- Rotation suitability matrix by field
- Financial projection summaries per field
- Multi-season planning support
- Arabic crop naming and UI display handling

## Optimization

The model maximizes:

**Expected Net Profit**

subject to:

- Land availability
- Water availability
- Labor availability
- Fertilizer availability
- Soil suitability
- Crop rotation restrictions

The current model is a **continuous Linear Programming (LP)** model solved using **Pyomo + HiGHS**.

## Project Structure

```text
Crop-Mix-Business-Planner/
│
├── src/
│   └── crop_mix/
│       ├── business/
│       │   ├── financial_projection.py
│       │   └── multi_season_planner.py
│       ├── data/
│       │   ├── example_data.py
│       │   ├── crop_seasons.py
│       │   └── rotation_loader.py
│       ├── models/
│       │   ├── optimizer_v1.py
│       │   ├── optimizer_v2.py
│       │   ├── optimizer_v3.py
│       │   ├── optimizer_v4.py
│       │   └── soil_suitability.py
│       └── services/
│           └── llm_explainer.py
│
├── tests/
├── run_demo.py
├── requirements.txt
├── pyproject.toml
└── README.md
```

The solver takes field, water-budget, and yield-estimate inputs, then returns a crop-mix recommendation with clear resource-bottleneck and agronomic explanations.
