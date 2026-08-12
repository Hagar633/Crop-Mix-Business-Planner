# Crop-Mix-Business-Planner

A crop-mix optimization solver that recommends how to allocate farm land among different crops while maximizing expected profit.

The project uses **Python, Pyomo, and the HiGHS solver**.

## Current Version

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
- Field × crop suitability

The optimizer prevents crops from being allocated to fields where they are unsuitable.

## Optimization

The model maximizes:

Expected Net Profit

subject to:

Land availability
Water availability
Labor availability
Fertilizer availability
Soil suitability

The current model is a continuous Linear Programming (LP) model solved using Pyomo + HiGHS.

Project Structure
src/crop_mix/
├── data/
│   └── example_data.py
└── models/
    ├── optimizer_v1.py
    ├── optimizer_v2.py
    ├── optimizer_v3.py
    └── soil_suitability.py

tests/
├── test_optimizer_v1.py
├── test_optimizer_v2.py
├── test_optimizer_v3.py
└── test_soil_suitability.py

run_demo.py
Run

Install dependencies:

pip install -r requirements.txt

Run tests:

.venv\Scripts\python.exe -m pytest tests/

Run the demo:

.venv\Scripts\python.exe run_demo.py
Current Status
V1 ✅
V2 ✅
V3 ✅

The current soil and crop requirement values are synthetic test/demo data.

Future Work

Planned additions include:
Crop rotation
Seasonal constraints
Real agricultural data
Frontend
API
Optional LLM explanation layer

Crop rotation
Seasonal constraints
Real agricultural data
Frontend
API
