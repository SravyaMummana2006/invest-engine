# 📊 Intelligent Investment Decision Engine

> A fintech-grade investment analysis system that models inflation, simulates market scenarios, and generates personalised portfolio recommendations — built as a production-quality Python + Streamlit application.

---

## Overview

The **Intelligent Investment Decision Engine** is a modular financial decision system that accepts a user's financial profile and outputs:

- A risk-adjusted **asset allocation** (equity / debt / gold)
- **Inflation-corrected** goal analysis using the Fisher equation
- **Three scenario simulations** (conservative, realistic, aggressive)
- **Instrument-level recommendations** with full reasoning narrative
- **Six interactive Plotly charts** for visual analysis
- **Exportable reports** in `.txt`, `.csv`, and `.json` formats

This project is structured as an internal fintech prototype — clean, modular, and scalable.

---

## Project Structure

```
investment-engine/
│── app.py                        # Streamlit application entry point
│── requirements.txt              # Python dependencies
│── README.md
│
├── data/
│   └── sample_profiles.csv       # 10 pre-built investor archetypes
│
├── modules/
│   ├── profile_engine.py         # Input validation & investor profile builder
│   ├── allocation_engine.py      # Risk × horizon × goal asset allocation logic
│   ├── inflation_engine.py       # FV inflation modelling & purchasing power erosion
│   ├── scenario_engine.py        # SIP + lump-sum scenario simulation (3 scenarios)
│   └── recommendation_engine.py  # Synthesis engine — narrative + instrument picks
│
├── utils/
│   ├── constants.py              # All magic numbers, labels, colours, thresholds
│   └── helpers.py                # Formatting, export, DataFrame utilities
│
├── visuals/
│   └── charts.py                 # Six Plotly chart factory functions
│
└── outputs/
    └── reports/                  # Auto-generated .txt / .csv / .json exports
```

---

## Quickstart

### 1. Clone / download the project

```bash
git clone https://github.com/your-org/investment-engine.git
cd investment-engine
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## Module Reference

### `modules/profile_engine.py`

Validates raw user inputs and returns a structured `InvestorProfile` dataclass.

```python
from modules.profile_engine import build_profile

profile = build_profile(
    age=30,
    monthly_income=100000,
    monthly_savings=20000,
    investment_goal="wealth",
    target_years=15,
    risk_appetite="high",
)
```

**Derived fields computed automatically:**
| Field | Description |
|---|---|
| `savings_rate` | `monthly_savings / monthly_income` |
| `annual_savings` | `monthly_savings × 12` |
| `horizon_category` | `short` / `medium` / `long` |

---

### `modules/allocation_engine.py`

Determines equity / debt / gold allocation using a data-driven matrix with goal overrides and an age-based glide path.

```python
from modules.allocation_engine import compute_allocation

allocation = compute_allocation(profile)
print(allocation.as_percentages())
# {"equity": 72.5, "debt": 18.0, "gold": 9.5}
print(allocation.rationale)
```

**Logic layers applied in order:**
1. Base matrix lookup (risk × horizon)
2. Goal-type additive override
3. Age glide-path taper (−0.5%/year equity after age 45)
4. Re-normalisation to sum = 1.0

---

### `modules/inflation_engine.py`

Models how inflation erodes purchasing power and inflates the target goal.

```python
from modules.inflation_engine import analyse_inflation

result = analyse_inflation(
    present_goal_value=5_000_000,
    goal_type="wealth",
    target_years=15,
    nominal_return_rate=0.12,
)
print(result.inflation_adjusted_goal)   # e.g. 11,983,176
print(result.real_return_rate)          # Fisher: (1.12 / 1.06) - 1
```

**Formula used:**

```
FV = PV × (1 + i)^n          ← Inflation-adjusted goal
Real Rate = (1 + r) / (1 + i) − 1   ← Fisher equation
```

**Goal-specific inflation rates:**
| Goal | Rate |
|---|---|
| Retirement | 6% |
| Home | 7% |
| Education | 8% |
| Wealth / Emergency | 6% |

---

### `modules/scenario_engine.py`

Simulates SIP + lump-sum corpus growth across three return scenarios.

```python
from modules.scenario_engine import run_all_scenarios

bundle = run_all_scenarios(profile)
print(bundle.realistic.maturity_value)
print(bundle.comparison_table())
```

**Scenarios:**
| Label | Annual Return |
|---|---|
| Conservative | 8% |
| Realistic | 12% |
| Aggressive | 15% |

**SIP formula used:**
```
FV = P × [((1 + r)^n − 1) / r] × (1 + r)
```

Also exposes `monthly_sip_required()` — the inverse solver that back-calculates the SIP needed to hit a target corpus.

---

### `modules/recommendation_engine.py`

Synthesises all engine outputs into a complete `RecommendationReport`.

```python
from modules.recommendation_engine import generate_recommendation

report = generate_recommendation(profile, allocation, inflation_res, bundle)

print(report.sip_sufficient)              # True / False
print(report.recommended_monthly_sip)     # Required SIP
print(report.full_narrative)              # Full reasoning text
print(report.key_insights)               # List of insight strings
print(report.equity_instruments)          # Recommended equity products
```

---

### `visuals/charts.py`

Six Plotly chart factory functions — no Streamlit dependency, fully testable.

| Function | Description |
|---|---|
| `portfolio_growth_chart()` | Corpus growth lines for all 3 scenarios |
| `allocation_donut_chart()` | Equity / debt / gold donut |
| `inflation_erosion_chart()` | Dual-axis: nominal goal cost + purchasing power |
| `goal_gap_bar_chart()` | Corpus vs inflation-adjusted goal per scenario |
| `scenario_comparison_bar()` | Invested vs maturity grouped bars |
| `sip_vs_returns_area_chart()` | Stacked area: capital + gains over time |

---

### `utils/constants.py`

Single source of truth for all configuration values. Import from here — never hard-code numbers in business logic.

```python
from utils.constants import RETURN_REALISTIC, GOAL_INFLATION_RATES, COLOR_ACCENT
```

---

### `utils/helpers.py`

Formatting and export utilities.

```python
from utils.helpers import fmt_currency, fmt_percent, export_recommendation_txt

fmt_currency(1_500_000, short=True)   # "₹15.00 L"
fmt_currency(15_000_000, short=True)  # "₹1.50 Cr"
fmt_percent(0.125)                    # "12.5%"
```

**Export functions:**
```python
export_recommendation_txt(narrative, insights, warnings, profile_summary)
export_growth_table_csv(df, scenario_label)
export_summary_json(report.to_dict())
```

All files are written to `outputs/reports/` with timestamped filenames.

---

## Sample Profiles

Ten pre-built investor archetypes in `data/sample_profiles.csv`:

| Profile | Age | Risk | Goal | Horizon |
|---|---|---|---|---|
| Young Professional | 27 | High | Wealth | 15yr |
| Conservative Saver | 45 | Low | Retirement | 20yr |
| Balanced Family | 35 | Medium | Home | 7yr |
| Education Planner | 40 | Medium | Education | 8yr |
| Near-Retiree | 58 | Low | Retirement | 7yr |
| Aggressive Investor | 30 | High | Wealth | 20yr |
| Emergency Builder | 25 | Low | Emergency | 2yr |
| Mid-Career Switcher | 38 | Medium | Wealth | 12yr |
| Home Upgrader | 42 | Medium | Home | 5yr |
| Retirement Optimizer | 50 | Medium | Retirement | 10yr |

Load any profile instantly from the sidebar's **Load Sample Profile** expander.

---

## Tech Stack

| Library | Version | Purpose |
|---|---|---|
| `streamlit` | 1.32.0 | Web application framework |
| `pandas` | 2.2.1 | DataFrame operations & export |
| `numpy` | 1.26.4 | Vectorised financial calculations |
| `plotly` | 5.20.0 | Interactive chart rendering |

---

## Design Principles

**Modularity** — Each engine module has a single responsibility and a clean public API. Modules are independently importable and testable.

**No magic numbers** — All thresholds, rates, and configuration values live in `utils/constants.py`.

**Data-driven logic** — Allocation matrices and goal overrides are dictionaries, not if/else chains. Adding a new risk level or goal type requires only a new dict entry.

**Separation of concerns** — Charts have zero Streamlit coupling. Engines have zero chart coupling. `app.py` is the only file that knows both exist.

**Production-ready exports** — Every analysis run can be persisted to disk in three formats for audit, reporting, or downstream pipeline use.

---

## Extending the Engine

**Add a new goal type:**
1. Add to `GOAL_TYPES` in `constants.py`
2. Add inflation rate to `GOAL_INFLATION_RATES`
3. Add override delta to `_GOAL_OVERRIDES` in `allocation_engine.py`
4. Add strategy label to `_GOAL_STRATEGY` in `recommendation_engine.py`

**Add a new scenario:**
1. Add to `SCENARIOS` dict in `scenario_engine.py`
2. Add colour to `SCENARIO_COLORS`
3. Extend `ScenarioBundle` dataclass

**Add a new asset class:**
1. Add weight to allocation matrix in `allocation_engine.py`
2. Add colour to `ASSET_COLORS` in `constants.py`
3. Add instrument list to `recommendation_engine.py`

---

## Disclaimer

This application is for **informational and educational purposes only**. It does not constitute financial advice. Past market returns do not guarantee future performance. Consult a SEBI-registered investment advisor before making investment decisions.

---

*Built with Python · Streamlit · Pandas · NumPy · Plotly*
