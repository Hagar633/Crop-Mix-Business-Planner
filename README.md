# Crop-Mix-Business-Planner

An agricultural decision-support and crop-mix optimization system that recommends how to allocate farm land among crops while considering **profitability, water, labor, fertilizer, soil suitability, crop rotation, multi-season planning, and financial risk**.

Built with **Python, Pyomo, HiGHS, FastAPI, JavaScript, and LLM-based explanations**.

The system is designed around Egyptian agricultural conditions, with an **Arabic-first interface** and support for Egyptian agricultural terminology and **feddan/hectare unit conversion**.

---

## Key Features

* 🌱 Crop-mix optimization
* 🚜 Multi-field farm planning
* 💧 Water budget constraints
* 👷 Labor budget constraints
* 🧪 Fertilizer budget constraints
* 🌍 Field-level soil suitability
* 🔄 Crop rotation constraints
* 📅 Multi-season planning
* 💰 Profit and financial projections
* ⚠️ Risk analysis using VaR and CVaR
* 📊 Scenario-based risk optimization
* 🇪🇬 Arabic-first agricultural interface
* 📐 Feddan/hectare unit conversion
* 🤖 LLM-generated explanations of optimization results
* 🌐 FastAPI backend
* 🐳 Docker/Render deployment support

---

# Optimization Versions

## V1 — Basic Optimization

The initial crop-mix optimization model.

Considers:

* Land availability
* Water budget
* Crop yield
* Crop price
* Production cost

The objective is to maximize total net profit.

---

## V2 — Labor & Fertilizer

Adds resource constraints and costs for:

* Labor requirements
* Fertilizer requirements
* Labor costs
* Fertilizer costs
* Labor budget
* Fertilizer budget

The model remains a continuous Linear Programming (LP) problem.

---

## V3 — Field & Soil Suitability

Introduces field-level agricultural planning.

Adds:

* Multiple fields
* Field-level crop allocation
* Soil pH
* Soil EC/salinity
* Soil texture
* Organic matter
* Crop soil requirements
* Field-level soil suitability

The system determines whether a crop can be grown on a particular field and prevents unsuitable allocations.

---

## V4 — Agricultural Planning

V4 extends the model from a basic crop-mix optimizer into a more complete agricultural planning system.

### Field-level planning

Each field can have its own:

* Area
* Soil properties
* Previous crop
* Crop suitability
* Crop allocation

### Crop Rotation

The model considers the previous crop on each field when determining whether the next crop is allowed.

The system exposes the underlying engineering information through:

* Crop rotation matrices
* Field-level rotation feasibility
* Soil suitability matrices
* Constraint analysis

### Resource Constraints

V4 simultaneously considers:

* Land
* Water
* Labor
* Fertilizer

while maintaining the existing continuous LP formulation.

---

# Multi-Season Planning

The system supports planning across agricultural seasons.

Crops are associated with agricultural seasons such as:

* Winter crops
* Summer crops
* Perennial crops
* All-year crops

Multi-season planning considers:

* Crop season
* Crop rotation
* Profitability
* Resource budgets
* Field allocation

The system can generate season-by-season planning and financial projections.

---

# Financial Projection

The business-planning layer extends optimization results into financial analysis.

It can estimate:

* Revenue
* Production costs
* Labor costs
* Fertilizer costs
* Net profit
* Multi-season financial performance

This allows the optimization result to be interpreted as a practical farm business plan rather than only as an allocation matrix.

---

# Risk & CVaR Optimization

The project includes a scenario-based financial risk framework.

Instead of evaluating a crop allocation only under normal conditions, the system evaluates the resulting farm profit under multiple scenarios.

Current scenarios include:

* Normal Conditions
* Water Stress
* Heat Stress
* Market Price Downturn
* Input Cost Inflation
* Severe Combined Stress

Each scenario can modify factors such as:

* Crop yield
* Crop selling price
* Production cost
* Labor cost
* Fertilizer cost

The system calculates:

### Expected Profit

The probability-weighted profit across scenarios.

### VaR

Value at Risk, representing a selected downside profit threshold.

### CVaR

Conditional Value at Risk, representing the expected outcome in the worst part of the scenario distribution.

The risk-aware optimizer uses the **Rockafellar–Uryasev CVaR formulation** while maintaining a Linear Programming structure.

Risk strategies currently include:

* **Maximum Profit**
* **Balanced**
* **Risk Aware**

This allows users to compare a profit-maximizing strategy against strategies that place greater emphasis on downside protection.

---

# Risk Data & Scenario Assumptions

The risk framework supports both historical/processed data and scenario-based parameters.

Some current scenario parameters are based on available historical or research data, while other parameters are currently **synthetic or assumption-based due to limited reliable historical data availability**.

These assumptions are explicitly treated as prototype scenario parameters rather than statistically validated future probabilities.

The architecture is designed so that improved historical datasets can later replace the current scenario parameters without changing the core CVaR optimization model.

Current processed risk data includes sources such as:

* Historical market price information
* Fertilizer/input-cost information
* Scenario metadata

Future calibration can incorporate additional:

* Historical crop yields
* Weather and temperature data
* Water availability data
* Market prices
* Agricultural input prices
* Historical stress events

---

# LLM-Based Explanations

The project includes an LLM explanation layer that translates optimization results into more understandable agricultural/business insights.

The LLM can help explain:

* Why particular crops were selected
* Why resources became binding
* How risk affects the recommended plan
* What the optimization results mean
* Important constraints and trade-offs

The LLM is an **explanation layer**, not the optimization engine.

The mathematical optimization remains deterministic and is performed by the Pyomo/HiGHS models.

---

# Engineering Details

The application exposes technical details behind the optimization result, including:

### Crop Rotation Matrix

Shows rotation feasibility for each field and candidate crop based on the field's previous crop.

### Soil Suitability Matrix

Shows field × crop soil suitability based on the existing soil suitability model.

### Constraint Analysis

Reports resource consumption and identifies important/binding constraints, including:

* Land Area
* Water Budget
* Labor Budget
* Fertilizer Budget

This provides transparency into why the optimizer produces a particular plan.

---

# Mathematical Model

The core optimization is formulated as a **continuous Linear Programming (LP)** model.

Decision variable:

```text
x[f,c] = area of crop c allocated to field f
```

The objective maximizes expected net profit:

```text
maximize  Σ x[f,c] × expected_profit[c]
```

subject to constraints such as:

```text
Σ crop_area[f,c] ≤ field_area[f]
```

```text
Σ water_requirement[c] × x[f,c] ≤ water_budget
```

```text
Σ labor_requirement[c] × x[f,c] ≤ labor_budget
```

```text
Σ fertilizer_requirement[c] × x[f,c] ≤ fertilizer_budget
```

plus field-level:

```text
soil suitability
crop rotation
```

constraints.

The risk-aware formulation additionally incorporates scenario profits and CVaR.

---

# Technology Stack

### Optimization

* Python
* Pyomo
* HiGHS
* Linear Programming
* CVaR / Risk Optimization

### Backend

* FastAPI
* Uvicorn

### Frontend

* HTML
* CSS
* JavaScript
* Arabic-first UI

### AI

* LLM-based result explanations

### Data

* CSV-based agricultural datasets
* Processed scenario datasets
* Historical/research-derived parameters where available

### Deployment

* Docker
* Render

---

# Project Structure

```text
Crop-Mix-Business-Planner/
│
├── src/
│   └── crop_mix/
│       │
│       ├── business/
│       │   └── risk_analysis.py
│       │
│       ├── data/
│       │   ├── example_data.py
│       │   ├── rotation_loader.py
│       │   ├── water_loader.py
│       │   ├── risk_scenarios.py
│       │   └── risk/
│       │       └── processed/
│       │           ├── input_cost_inflation.csv
│       │           ├── market_downturn.csv
│       │           └── scenario_metadata.csv
│       │
│       ├── models/
│       │   ├── optimizer_v1.py
│       │   ├── optimizer_v2.py
│       │   ├── optimizer_v3.py
│       │   ├── optimizer_v4.py
│       │   └── risk_aware_optimizer.py
│       │
│       ├── services/
│       │   └── llm_explainer.py
│       │
│       ├── static/
│       │   ├── index.html
│       │   ├── app.js
│       │   └── styles.css
│       │
│       └── app.py
│
├── tests/
│   ├── test_optimizer_v1.py
│   ├── test_optimizer_v2.py
│   ├── test_optimizer_v3.py
│   ├── test_optimizer_v4.py
│   ├── test_risk_analysis.py
│   ├── test_rotation_loader.py
│   ├── test_llm_explainer.py
│   ├── test_unit_conversions.py
│   └── test_validation_pipeline.py
│
├── app.py
├── run_demo.py
├── Dockerfile
├── Procfile
├── render.yaml
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

# Running the Project

Install the dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
python app.py
```

Or run the development/demo application according to the project's configured entry point.

The application provides the agricultural planning interface through the FastAPI backend and frontend.

---

# Testing

Run the test suite with:

```bash
python -m pytest -q
```

Frontend JavaScript syntax can be checked with:

```bash
node --check src/crop_mix/static/app.js
```

Git whitespace validation:

```bash
git diff --check
```

---

# Design Principles

The project follows several important design principles:

### 1. Optimization remains mathematical

The LLM does not replace the optimizer.

### 2. Canonical internal identifiers

English/canonical identifiers are maintained internally for the optimization and data-processing layers.

Arabic names are used primarily at the UI/display boundary.

### 3. Transparent assumptions

Where reliable historical data is unavailable, scenario parameters are explicitly treated as assumptions rather than presented as validated statistics.

### 4. Replaceable data layer

Risk parameters and agricultural datasets can be recalibrated as better historical data becomes available without redesigning the optimization architecture.

### 5. Explainable optimization

The application exposes the engineering reasoning behind the recommended plan through resource analysis, rotation matrices, soil suitability matrices, risk metrics, and LLM-generated explanations.

---

# Current Status

The project currently integrates:

* V1–V4 optimization
* Field-level planning
* Soil suitability
* Crop rotation
* Multi-season planning
* Financial projections
* Risk/CVaR analysis
* Scenario-based risk optimization
* Arabic agricultural UI
* Feddan/hectare conversion
* LLM explanations
* Docker/Render deployment configuration

The risk-analysis layer is currently a **prototype** in terms of data calibration. Some scenarios use synthetic assumptions because sufficient historical agricultural risk data is not yet available.

The optimization architecture is designed to support future calibration using larger historical datasets.

---

# Future Improvements

Potential future improvements include:

* Historical Egyptian weather integration
* Historical crop-yield calibration
* More detailed water-stress modeling
* Crop-specific fertilizer usage and price data
* Field-specific climate/risk factors
* Larger historical scenario databases
* Historical backtesting of risk strategies
* Probability calibration from historical observations
* More robust CVaR confidence levels
* Additional crops and Egyptian agricultural regions
* Improved multi-season economic forecasting
* Production-ready database integration
* Advanced Monte Carlo risk simulation

---

## License

This project is currently developed as an agricultural optimization and decision-support prototype.
