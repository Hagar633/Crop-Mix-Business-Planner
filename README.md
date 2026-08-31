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

## Optimization

The model maximizes:

**Expected Net Profit**

subject to:

- Land availability
- Water availability
- Labor availability
- Fertilizer availability
- Soil suitability

The current model is a **continuous Linear Programming (LP)** model solved using **Pyomo + HiGHS**.

## Project Structure

```text
Crop-Mix-Business-Planner/
│
├── src/
│   └── crop_mix/
│       ├── data/
│       │   └── example_data.py
│       │
│       └── models/
│           ├── optimizer_v1.py
│           ├── optimizer_v2.py
│           ├── optimizer_v3.py
│           └── soil_suitability.py
│
├── tests/
│   ├── test_optimizer_v1.py
│   ├── test_optimizer_v2.py
│   ├── test_optimizer_v3.py
│   └── test_soil_suitability.py
│
├── run_demo.py
├── requirements.txt
├── pyproject.toml
└── README.md
```
