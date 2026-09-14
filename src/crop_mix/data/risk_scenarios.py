"""Egyptian agricultural risk scenario database.

IMPORTANT DISCLAIMER:
Most scenario data in this module is SYNTHETIC and designed specifically
for risk-analysis demonstration purposes. It is NOT official historical
Egyptian agricultural data. The Market Price Downturn scenario is the
exception: its crop price multipliers and probability are loaded from the
offline FAOSTAT producer-price calibration artifacts.

Purpose:
    Provides a scientifically defensible scenario framework for
    demonstrating CVaR-based risk analysis in Egyptian crop mix planning,
    until additional historical yield/price time-series data becomes available.

Scenario Design Rationale:
    Egypt's agricultural sector faces recurring risk factors:
    - Nile water scarcity and irrigation stress during summer
    - Extreme heat events damaging summer crops (June–August)
    - Market price volatility for vegetables (especially tomato)
    - Import-linked fertilizer cost spikes
    - Cotton market exposure to global commodity prices
    - High water requirements for rice in a water-scarce country
    - Wheat's strategic importance with government-supported prices
      reducing market volatility
    - Perennial crops (orange) having dampened short-term yield shocks
      but exposure to long-term climate trends
"""

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


RISK_DATA_DIR = Path(__file__).resolve().parent / "risk"
MARKET_DOWNTURN_DATA = RISK_DATA_DIR / "processed" / "market_downturn.csv"
MARKET_SCENARIO_METADATA = RISK_DATA_DIR / "processed" / "scenario_metadata.csv"
FERTILIZER_INFLATION_DATA = RISK_DATA_DIR / "processed" / "input_cost_inflation.csv"
FERTILIZER_SCENARIO_METADATA = RISK_DATA_DIR / "processed" / "scenario_metadata.csv"


def _load_market_downturn_data() -> tuple[float, Dict[str, float]]:
    """Load offline-calibrated market probability and price multipliers."""
    if not MARKET_DOWNTURN_DATA.exists() or not MARKET_SCENARIO_METADATA.exists():
        raise FileNotFoundError(
            "Calibrated market-risk data is missing. Run "
            "python -m crop_mix.data.process_market_risk first."
        )

    with MARKET_SCENARIO_METADATA.open(newline="", encoding="utf-8") as handle:
        metadata = list(csv.DictReader(handle))
    market_row = next((row for row in metadata if row.get("scenario_id") == "market_downturn"), None)
    if market_row is None:
        raise ValueError("scenario_metadata.csv has no market_downturn row.")
    probability = float(market_row["probability"])
    if not 0 < probability < 1:
        raise ValueError(f"Calibrated market downturn probability is invalid: {probability}")

    with MARKET_DOWNTURN_DATA.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    multipliers = {row["crop"]: float(row["price_multiplier"]) for row in rows}
    if not multipliers or any(value <= 0 for value in multipliers.values()):
        raise ValueError("Calibrated market downturn multipliers must be positive.")
    return probability, multipliers


MARKET_DOWNTURN_PROBABILITY, MARKET_DOWNTURN_MULTIPLIERS = _load_market_downturn_data()


def _load_fertilizer_inflation_multiplier() -> float:
    """Load the offline-calibrated fertilizer-only stress multiplier."""
    if not FERTILIZER_INFLATION_DATA.exists() or not FERTILIZER_SCENARIO_METADATA.exists():
        raise FileNotFoundError(
            "Calibrated fertilizer-risk data is missing. Run "
            "python -m crop_mix.data.process_fertilizer_risk first."
        )
    with FERTILIZER_SCENARIO_METADATA.open(newline="", encoding="utf-8") as handle:
        metadata = list(csv.DictReader(handle))
    row = next((item for item in metadata if item.get("scenario_id") == "input_inflation"), None)
    if row is None or not row.get("fertilizer_cost_multiplier"):
        raise ValueError("scenario_metadata.csv has no calibrated input_inflation multiplier.")
    multiplier = float(row["fertilizer_cost_multiplier"])
    if multiplier <= 0:
        raise ValueError(f"Calibrated fertilizer multiplier is invalid: {multiplier}")
    return multiplier


FERTILIZER_INFLATION_MULTIPLIER = _load_fertilizer_inflation_multiplier()


@dataclass
class CropRiskProfile:
    """Per-crop multipliers for a specific economic/environmental scenario.

    All multipliers are dimensionless factors applied to base crop parameters:
    - yield_multiplier: fraction of expected base yield (0.5 = 50% yield loss)
    - price_multiplier: fraction of expected market price (0.7 = 30% price drop)
    - production_cost_multiplier: factor for base production costs
    - labor_cost_multiplier: factor for labor costs
    - fertilizer_cost_multiplier: factor for fertilizer costs

    Values are always > 0. A value of 1.0 means no change from baseline.
    """

    crop_name: str
    yield_multiplier: float = 1.0
    price_multiplier: float = 1.0
    production_cost_multiplier: float = 1.0
    labor_cost_multiplier: float = 1.0
    fertilizer_cost_multiplier: float = 1.0

    def validate(self) -> None:
        """Validate that all multipliers are positive."""
        for attr in [
            "yield_multiplier",
            "price_multiplier",
            "production_cost_multiplier",
            "labor_cost_multiplier",
            "fertilizer_cost_multiplier",
        ]:
            val = getattr(self, attr)
            if val <= 0:
                raise ValueError(
                    f"CropRiskProfile for '{self.crop_name}': "
                    f"'{attr}' must be > 0, got {val}."
                )


@dataclass
class RiskScenario:
    """A single economic/environmental stress scenario for CVaR analysis.

    Attributes:
        scenario_id: Unique string identifier.
        name: Short human-readable name (Arabic or English).
        name_arabic: Arabic display name.
        description: English description of the scenario.
        description_arabic: Arabic description for the UI.
        probability: Probability weight (0 < p <= 1, sum across scenarios == 1).
        risk_category: High-level category (e.g. 'Water', 'Market', 'Climate').
        severity: 'Low', 'Medium', 'High', 'Extreme'.
        crop_profiles: Per-crop multiplier profiles keyed by canonical crop name.
        default_yield_multiplier: Used for crops not listed in crop_profiles.
        default_price_multiplier: Default price factor for unlisted crops.
        default_production_cost_multiplier: Default for unlisted crops.
        default_labor_cost_multiplier: Default for unlisted crops.
        default_fertilizer_cost_multiplier: Default for unlisted crops.
    """

    scenario_id: str
    name: str
    name_arabic: str
    description: str
    description_arabic: str
    probability: float
    risk_category: str
    severity: str
    crop_profiles: Dict[str, CropRiskProfile] = field(default_factory=dict)
    # Fallback defaults for crops not explicitly profiled
    default_yield_multiplier: float = 1.0
    default_price_multiplier: float = 1.0
    default_production_cost_multiplier: float = 1.0
    default_labor_cost_multiplier: float = 1.0
    default_fertilizer_cost_multiplier: float = 1.0

    def get_crop_profile(self, crop_name: str) -> CropRiskProfile:
        """Return the risk profile for a crop, falling back to scenario defaults."""
        if crop_name in self.crop_profiles:
            return self.crop_profiles[crop_name]
        return CropRiskProfile(
            crop_name=crop_name,
            yield_multiplier=self.default_yield_multiplier,
            price_multiplier=self.default_price_multiplier,
            production_cost_multiplier=self.default_production_cost_multiplier,
            labor_cost_multiplier=self.default_labor_cost_multiplier,
            fertilizer_cost_multiplier=self.default_fertilizer_cost_multiplier,
        )

    def validate(self) -> None:
        """Validate probability and all crop profile multipliers."""
        if not (0 < self.probability <= 1.0):
            raise ValueError(
                f"Scenario '{self.scenario_id}': probability must be in (0, 1], "
                f"got {self.probability}."
            )
        for name, profile in self.crop_profiles.items():
            profile.validate()


class RiskScenarioProvider:
    """Abstract base for scenario providers.

    Subclass this to replace the synthetic provider with a historical
    data provider when real time-series data becomes available.
    """

    def get_scenarios(self) -> List[RiskScenario]:
        raise NotImplementedError

    def validate(self) -> None:
        scenarios = self.get_scenarios()
        if not scenarios:
            raise ValueError("Scenario database cannot be empty.")
        for s in scenarios:
            s.validate()
        total_prob = sum(s.probability for s in scenarios)
        if abs(total_prob - 1.0) > 1e-6:
            raise ValueError(
                f"Scenario probabilities must sum to 1.0; got {total_prob:.6f}."
            )


class SyntheticEgyptRiskProvider(RiskScenarioProvider):
    """Synthetic Egyptian agricultural risk scenario provider.

    DISCLAIMER: All data is SYNTHETIC for demonstration purposes only.
    Not official Egyptian agricultural statistics.

    Scenario Design Logic:
    -----------------------
    Six scenarios are defined to cover the major risk drivers in Egyptian
    agriculture. Probabilities are synthetic assumptions:

    1. Normal (p=0.45): Most common outcome. Modest variability.
       Rationale: In any given season, favorable conditions are the baseline.

    2. Water Stress (p=0.18): Insufficient irrigation due to reduced Nile
       flow or groundwater depletion. Affects high-water-demand crops most.
       Rationale: Water scarcity is Egypt's #1 agricultural challenge; 18%
       probability reflects meaningful but not dominant frequency.

    3. Heat Stress (p=0.12): Extreme summer heat (>42°C) damaging yields.
       Affects summer crops; wheat is winter-planted so less vulnerable.
       Rationale: Climate data shows increasing frequency of heat events.

    4. Market Price Downturn (p=0.12): Commodity price collapse due to
       oversupply or reduced export demand. Especially severe for tomato,
       cotton, and soybeans, which have volatile markets.
       Rationale: Egyptian farmers regularly face price swings; 12% captures
       a meaningful annual probability.

    5. Input Cost Inflation (p=0.08): Fertilizer and energy price spikes
       (e.g. from global supply disruptions). Affects all crops but most
       severely those with high fertilizer requirements.
       Rationale: Fertilizer prices are linked to global natural gas; cost
       spikes have been observed.

    6. Severe Combined Stress (p=0.05): Rare but catastrophic combination
       of poor yields AND market downturn AND cost inflation.
       Rationale: Tail-risk event; 5% captures the extreme downside tail
       that CVaR is specifically designed to measure.

    Total: 0.45 + 0.18 + 0.12 + 0.12 + 0.08 + 0.05 = 1.00
    """

    def get_scenarios(self) -> List[RiskScenario]:
        return _SYNTHETIC_EGYPT_SCENARIOS


def _build_scenarios() -> List[RiskScenario]:
    """Construct the synthetic Egyptian agricultural risk scenario database."""

    # Preserve the relative weights of the remaining synthetic scenarios after
    # replacing the market scenario with its empirical historical estimate.
    synthetic_non_market_total = 0.45 + 0.18 + 0.12 + 0.08 + 0.05
    non_market_scale = (1.0 - MARKET_DOWNTURN_PROBABILITY) / synthetic_non_market_total

    # -----------------------------------------------------------------------
    # SCENARIO 1: Normal / Baseline Conditions (p=0.45)
    # Most seasons in Egypt fall near this baseline. Small positive deviations
    # are common; crop yields and prices are close to expected values.
    # -----------------------------------------------------------------------
    s1 = RiskScenario(
        scenario_id="normal",
        name="Normal Conditions",
        name_arabic="ظروف عادية",
        description=(
            "Typical season: yields and prices close to expected values. "
            "Mild favourable deviations possible."
        ),
        description_arabic=(
            "موسم عادي: المحاصيل والأسعار قريبة من القيم المتوقعة. "
            "انحرافات إيجابية طفيفة محتملة."
        ),
        probability=0.45 * non_market_scale,
        risk_category="Baseline",
        severity="Low",
        default_yield_multiplier=1.00,
        default_price_multiplier=1.00,
        default_production_cost_multiplier=1.00,
        default_labor_cost_multiplier=1.00,
        default_fertilizer_cost_multiplier=1.00,
        crop_profiles={
            "Wheat":       CropRiskProfile("Wheat",       1.02, 1.00, 1.00, 1.00, 1.00),
            "Barley":      CropRiskProfile("Barley",      1.01, 1.00, 1.00, 1.00, 1.00),
            "Yellow Corn": CropRiskProfile("Yellow Corn", 1.00, 1.02, 1.00, 1.00, 1.00),
            "Soybean":     CropRiskProfile("Soybean",     1.00, 1.00, 1.00, 1.00, 1.00),
            "Tomato":      CropRiskProfile("Tomato",      1.00, 1.05, 1.00, 1.00, 1.00),
            "Cotton":      CropRiskProfile("Cotton",      1.00, 1.00, 1.00, 1.00, 1.00),
            "Rice":        CropRiskProfile("Rice",        1.00, 1.00, 1.00, 1.00, 1.00),
            "Potato":      CropRiskProfile("Potato",      1.01, 1.00, 1.00, 1.00, 1.00),
            "Sugar Beet":  CropRiskProfile("Sugar Beet",  1.00, 1.00, 1.00, 1.00, 1.00),
            "Alfalfa":     CropRiskProfile("Alfalfa",     1.00, 1.00, 1.00, 1.00, 1.00),
            "Orange":      CropRiskProfile("Orange",      1.00, 1.02, 1.00, 1.00, 1.00),
        },
    )

    # -----------------------------------------------------------------------
    # SCENARIO 2: Water Stress (p=0.18)
    # Reduced Nile flow or groundwater, causing irrigation shortfall.
    # High-water-demand crops (Rice, Cotton, Tomato, Sugarcane) suffer most.
    # Wheat has moderate sensitivity because it is irrigated in winter.
    # -----------------------------------------------------------------------
    s2 = RiskScenario(
        scenario_id="water_stress",
        name="Water Stress",
        name_arabic="إجهاد مائي",
        description=(
            "Reduced irrigation availability. High-water-demand crops "
            "suffer significant yield losses. Low-demand crops are less affected. "
            "Production costs slightly elevated due to water pricing/pumping."
        ),
        description_arabic=(
            "انخفاض مياه الري. تعاني المحاصيل عالية الاستهلاك المائي من خسائر "
            "كبيرة في الغلة. تكاليف الإنتاج ترتفع قليلاً بسبب تكاليف ضخ المياه."
        ),
        probability=0.18 * non_market_scale,
        risk_category="Water",
        severity="High",
        default_yield_multiplier=0.88,
        default_price_multiplier=1.00,
        default_production_cost_multiplier=1.05,
        default_labor_cost_multiplier=1.00,
        default_fertilizer_cost_multiplier=1.00,
        crop_profiles={
            # High water demand crops — most affected
            "Rice":        CropRiskProfile("Rice",        0.55, 1.05, 1.10, 1.00, 1.00),
            "Cotton":      CropRiskProfile("Cotton",      0.70, 1.00, 1.08, 1.00, 1.00),
            "Tomato":      CropRiskProfile("Tomato",      0.72, 1.08, 1.08, 1.00, 1.00),
            "Yellow Corn": CropRiskProfile("Yellow Corn", 0.74, 1.00, 1.07, 1.00, 1.00),
            "Sugar Beet":  CropRiskProfile("Sugar Beet",  0.76, 1.00, 1.06, 1.00, 1.00),
            "Alfalfa":     CropRiskProfile("Alfalfa",     0.75, 1.00, 1.06, 1.00, 1.00),
            # Moderate water demand crops
            "Soybean":     CropRiskProfile("Soybean",     0.82, 1.00, 1.05, 1.00, 1.00),
            "Potato":      CropRiskProfile("Potato",      0.83, 1.00, 1.05, 1.00, 1.00),
            "Orange":      CropRiskProfile("Orange",      0.85, 1.00, 1.06, 1.00, 1.00),
            # Lower water demand crops — less affected
            "Wheat":       CropRiskProfile("Wheat",       0.88, 1.00, 1.04, 1.00, 1.00),
            "Barley":      CropRiskProfile("Barley",      0.90, 1.00, 1.03, 1.00, 1.00),
        },
    )

    # -----------------------------------------------------------------------
    # SCENARIO 3: Heat Stress (p=0.12)
    # Extreme summer heat events damage summer-planted crops.
    # Wheat is winter-planted and mostly escaped by harvest time.
    # Tomato, Yellow Corn, Cotton, Rice suffer from heat stress in summer.
    # -----------------------------------------------------------------------
    s3 = RiskScenario(
        scenario_id="heat_stress",
        name="Heat Stress",
        name_arabic="إجهاد حراري",
        description=(
            "Extreme heat events (>42°C) during growing season damage summer crops. "
            "Winter crops less affected. Production costs increase due to "
            "additional cooling/irrigation measures."
        ),
        description_arabic=(
            "موجات حر شديدة (>42°C) تضر بالمحاصيل الصيفية. "
            "المحاصيل الشتوية أقل تأثراً. ترتفع التكاليف الإنتاجية "
            "بسبب زيادة الري والمعالجة."
        ),
        probability=0.12 * non_market_scale,
        risk_category="Climate",
        severity="High",
        default_yield_multiplier=0.85,
        default_price_multiplier=1.00,
        default_production_cost_multiplier=1.08,
        default_labor_cost_multiplier=1.05,
        default_fertilizer_cost_multiplier=1.00,
        crop_profiles={
            # Summer crops most vulnerable to extreme heat
            "Tomato":      CropRiskProfile("Tomato",      0.65, 1.12, 1.12, 1.08, 1.00),
            "Cotton":      CropRiskProfile("Cotton",      0.72, 1.00, 1.10, 1.05, 1.00),
            "Yellow Corn": CropRiskProfile("Yellow Corn", 0.74, 1.00, 1.08, 1.05, 1.00),
            "Rice":        CropRiskProfile("Rice",        0.76, 1.05, 1.10, 1.05, 1.00),
            "Soybean":     CropRiskProfile("Soybean",     0.77, 1.00, 1.07, 1.05, 1.00),
            # Partially exposed crops
            "Potato":      CropRiskProfile("Potato",      0.80, 1.05, 1.08, 1.03, 1.00),
            "Alfalfa":     CropRiskProfile("Alfalfa",     0.82, 1.00, 1.06, 1.03, 1.00),
            "Sugar Beet":  CropRiskProfile("Sugar Beet",  0.83, 1.00, 1.06, 1.03, 1.00),
            # Perennial / winter crops — lower heat exposure
            "Orange":      CropRiskProfile("Orange",      0.85, 1.00, 1.08, 1.04, 1.00),
            # Winter grain crops are harvested before peak heat
            "Wheat":       CropRiskProfile("Wheat",       0.95, 1.00, 1.03, 1.02, 1.00),
            "Barley":      CropRiskProfile("Barley",      0.95, 1.00, 1.03, 1.02, 1.00),
        },
    )

    # -----------------------------------------------------------------------
    # SCENARIO 4: Market Price Downturn
    # The probability and crop price multipliers are calibrated offline from
    # FAOSTAT producer prices. Yields and costs are unchanged by this market-only shock.
    # -----------------------------------------------------------------------
    s4 = RiskScenario(
        scenario_id="market_downturn",
        name="Market Price Downturn",
        name_arabic="انخفاض أسعار السوق",
        description=(
            "Commodity price collapse due to oversupply or reduced demand. "
            "Vegetable and export crops most affected. Cereals partially "
            "protected by government price-support mechanisms."
        ),
        description_arabic=(
            "انهيار أسعار السلع بسبب الإفراط في الإنتاج أو انخفاض الطلب. "
            "المحاصيل الخضرية والتصديرية الأشد تأثراً. الحبوب محمية جزئياً "
            "بآليات دعم الأسعار الحكومية."
        ),
        probability=MARKET_DOWNTURN_PROBABILITY,
        risk_category="Market",
        severity="High",
        default_yield_multiplier=1.00,
        default_price_multiplier=1.00,
        default_production_cost_multiplier=1.00,
        default_labor_cost_multiplier=1.00,
        default_fertilizer_cost_multiplier=1.00,
        crop_profiles={
            crop: CropRiskProfile(
                crop,
                yield_multiplier=1.00,
                price_multiplier=multiplier,
                production_cost_multiplier=1.00,
                labor_cost_multiplier=1.00,
                fertilizer_cost_multiplier=1.00,
            )
            for crop, multiplier in MARKET_DOWNTURN_MULTIPLIERS.items()
        },
    )

    # -----------------------------------------------------------------------
    # SCENARIO 5: Input Cost Inflation (p=0.08)
    # Fertilizer, energy, and agrochemical prices spike.
    # High-fertilizer crops (Tomato, Yellow Corn, Cotton) most affected.
    # Yields unchanged; this is purely a cost shock.
    # -----------------------------------------------------------------------
    s5 = RiskScenario(
        scenario_id="input_inflation",
        name="Input Cost Inflation",
        name_arabic="تضخم تكاليف المدخلات",
        description=(
            "Fertilizer, fuel, and agrochemical prices spike significantly. "
            "High-input crops suffer the largest margin compression. "
            "Yields are not directly affected."
        ),
        description_arabic=(
            "ارتفاع حاد في أسعار الأسمدة والوقود والمبيدات. "
            "المحاصيل عالية المدخلات تعاني من أشد ضغط على الهامش. "
            "لا تتأثر الغلة بشكل مباشر."
        ),
        probability=0.08 * non_market_scale,
        risk_category="Cost",
        severity="Medium",
        default_yield_multiplier=1.00,
        default_price_multiplier=1.00,
        default_production_cost_multiplier=1.00,
        default_labor_cost_multiplier=1.00,
        default_fertilizer_cost_multiplier=FERTILIZER_INFLATION_MULTIPLIER,
        crop_profiles={
            crop: CropRiskProfile(
                crop,
                yield_multiplier=1.00,
                price_multiplier=1.00,
                production_cost_multiplier=1.00,
                labor_cost_multiplier=1.00,
                fertilizer_cost_multiplier=FERTILIZER_INFLATION_MULTIPLIER,
            )
            for crop in [
                "Tomato", "Yellow Corn", "Cotton", "Sugar Beet", "Rice",
                "Orange", "Potato", "Wheat", "Barley", "Soybean", "Alfalfa",
            ]
        },
    )

    # -----------------------------------------------------------------------
    # SCENARIO 6: Severe Combined Stress (p=0.05)
    # Rare but catastrophic: poor yields + market collapse + cost inflation.
    # This is the TAIL RISK scenario that CVaR is specifically designed to capture.
    # -----------------------------------------------------------------------
    s6 = RiskScenario(
        scenario_id="severe_combined",
        name="Severe Combined Stress",
        name_arabic="إجهاد شديد متزامن",
        description=(
            "Rare catastrophic event: simultaneous yield shock, market price "
            "collapse, and input cost spike. Represents the extreme tail risk "
            "that CVaR is designed to quantify."
        ),
        description_arabic=(
            "حدث كارثي نادر: صدمة غلة وانهيار أسعار وارتفاع تكاليف متزامنة. "
            "يمثل مخاطر الذيل القصوى التي يهدف CVaR إلى قياسها."
        ),
        probability=0.05 * non_market_scale,
        risk_category="Combined",
        severity="Extreme",
        default_yield_multiplier=0.60,
        default_price_multiplier=0.65,
        default_production_cost_multiplier=1.40,
        default_labor_cost_multiplier=1.25,
        default_fertilizer_cost_multiplier=1.70,
        crop_profiles={
            # Highest combined stress
            "Tomato":      CropRiskProfile("Tomato",      0.45, 0.48, 1.45, 1.30, 1.80),
            "Cotton":      CropRiskProfile("Cotton",      0.52, 0.55, 1.42, 1.25, 1.72),
            "Rice":        CropRiskProfile("Rice",        0.48, 0.62, 1.42, 1.25, 1.72),
            "Yellow Corn": CropRiskProfile("Yellow Corn", 0.55, 0.62, 1.40, 1.25, 1.72),
            "Soybean":     CropRiskProfile("Soybean",     0.58, 0.60, 1.38, 1.22, 1.60),
            "Potato":      CropRiskProfile("Potato",      0.55, 0.58, 1.40, 1.25, 1.70),
            "Orange":      CropRiskProfile("Orange",      0.65, 0.62, 1.40, 1.25, 1.70),
            "Sugar Beet":  CropRiskProfile("Sugar Beet",  0.62, 0.68, 1.38, 1.22, 1.68),
            "Alfalfa":     CropRiskProfile("Alfalfa",     0.65, 0.70, 1.35, 1.20, 1.60),
            # Cereals partly protected by government floors
            "Wheat":       CropRiskProfile("Wheat",       0.70, 0.78, 1.32, 1.18, 1.52),
            "Barley":      CropRiskProfile("Barley",      0.72, 0.80, 1.30, 1.18, 1.48),
        },
    )

    # Validate total probability = 1.0
    total = s1.probability + s2.probability + s3.probability + s4.probability + s5.probability + s6.probability
    assert abs(total - 1.0) < 1e-9, f"Scenario probabilities must sum to 1.0; got {total}"

    return [s1, s2, s3, s4, s5, s6]


# Module-level singleton scenario list
_SYNTHETIC_EGYPT_SCENARIOS: List[RiskScenario] = _build_scenarios()


def get_default_provider() -> SyntheticEgyptRiskProvider:
    """Return the default synthetic Egyptian risk scenario provider."""
    return SyntheticEgyptRiskProvider()
