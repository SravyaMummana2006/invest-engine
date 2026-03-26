"""
utils/constants.py
------------------
Central registry of all application-wide constants, thresholds, labels,
and configuration values.  Import from here — never hard-code magic numbers
in business logic modules.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Application metadata
# ---------------------------------------------------------------------------

APP_NAME        = "Intelligent Investment Decision Engine"
APP_VERSION     = "1.0.0"
APP_DESCRIPTION = (
    "A fintech-grade portfolio analyser that models inflation, "
    "simulates market scenarios, and generates personalised investment recommendations."
)

# ---------------------------------------------------------------------------
# Currency / locale
# ---------------------------------------------------------------------------

CURRENCY_SYMBOL   = "₹"
CURRENCY_LOCALE   = "en_IN"
LARGE_NUMBER_UNIT = 100_000        # 1 Lakh
CRORE_UNIT        = 10_000_000    # 1 Crore

# ---------------------------------------------------------------------------
# Scenario return rates
# ---------------------------------------------------------------------------

RETURN_CONSERVATIVE: float = 0.08
RETURN_REALISTIC:    float = 0.12
RETURN_AGGRESSIVE:   float = 0.15

SCENARIO_LABELS = {
    "conservative": "Conservative (8%)",
    "realistic":    "Realistic (12%)",
    "aggressive":   "Aggressive (15%)",
}

# ---------------------------------------------------------------------------
# Inflation defaults
# ---------------------------------------------------------------------------

DEFAULT_INFLATION_RATE: float = 0.06

GOAL_INFLATION_RATES = {
    "retirement": 0.06,
    "home":       0.07,
    "education":  0.08,
    "wealth":     0.06,
    "emergency":  0.06,
}

# ---------------------------------------------------------------------------
# Risk levels
# ---------------------------------------------------------------------------

RISK_LEVELS              = ["low", "medium", "high"]
RISK_LEVEL_DISPLAY       = {"low": "Low 🛡️", "medium": "Medium ⚖️", "high": "High 🚀"}

# ---------------------------------------------------------------------------
# Goal types
# ---------------------------------------------------------------------------

GOAL_TYPES = ["retirement", "home", "education", "wealth", "emergency"]

GOAL_TYPE_DISPLAY = {
    "retirement": "Retirement 🏖️",
    "home":       "Home Purchase 🏠",
    "education":  "Education 🎓",
    "wealth":     "Wealth Creation 💰",
    "emergency":  "Emergency Fund 🆘",
}

GOAL_TYPE_ICONS = {
    "retirement": "🏖️",
    "home":       "🏠",
    "education":  "🎓",
    "wealth":     "💰",
    "emergency":  "🆘",
}

# ---------------------------------------------------------------------------
# Horizon categories
# ---------------------------------------------------------------------------

HORIZON_SHORT_MAX  = 3      # years
HORIZON_MEDIUM_MAX = 7      # years
# > 7 years = long

HORIZON_LABELS = {
    "short":  "Short-term  (≤ 3 years)",
    "medium": "Medium-term (4–7 years)",
    "long":   "Long-term   (8+ years)",
}

# ---------------------------------------------------------------------------
# Allocation engine
# ---------------------------------------------------------------------------

GLIDE_PATH_THRESHOLD_AGE           = 45
GLIDE_PATH_EQUITY_TAPER_PER_YEAR   = 0.005
GLIDE_PATH_MAX_TAPER               = 0.20
EQUITY_FLOOR                       = 0.05   # minimum equity weight after taper
ASSET_DRIFT_REBALANCE_THRESHOLD    = 0.05   # trigger rebalance at ±5% drift

# ---------------------------------------------------------------------------
# Recommendation engine
# ---------------------------------------------------------------------------

HEALTHY_SAVINGS_RATE     = 0.20     # 20 % of income
ANNUAL_SIP_STEP_UP_RATE  = 0.10     # recommend 10 % annual SIP step-up
MIN_EMERGENCY_FUND_MONTHS = 6       # months of expenses as emergency fund

# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------

PAGE_TITLE = "Investment Decision Engine"
PAGE_ICON  = "📊"
LAYOUT     = "wide"

# Sidebar slider ranges
AGE_MIN, AGE_MAX, AGE_DEFAULT                       = 18,  80,  30
INCOME_MIN, INCOME_MAX, INCOME_DEFAULT              = 10_000, 10_000_000, 100_000
SAVINGS_MIN, SAVINGS_MAX, SAVINGS_DEFAULT           = 1_000,  5_000_000,  20_000
TARGET_YEARS_MIN, TARGET_YEARS_MAX, TARGET_YEARS_DEF = 1, 40, 10
GOAL_AMOUNT_MIN, GOAL_AMOUNT_MAX, GOAL_AMOUNT_DEF   = 100_000, 100_000_000, 5_000_000

# ---------------------------------------------------------------------------
# Chart colours
# ---------------------------------------------------------------------------

COLOR_CONSERVATIVE = "#4A90D9"   # steel blue
COLOR_REALISTIC    = "#27AE60"   # emerald green
COLOR_AGGRESSIVE   = "#E74C3C"   # coral red
COLOR_INVESTED     = "#95A5A6"   # silver grey
COLOR_EQUITY       = "#E67E22"   # warm orange
COLOR_DEBT         = "#2980B9"   # ocean blue
COLOR_GOLD         = "#F1C40F"   # gold yellow
COLOR_BACKGROUND   = "#0F1117"   # Streamlit dark bg
COLOR_CARD_BG      = "#1E2130"   # card surface
COLOR_ACCENT       = "#00D4FF"   # bright cyan accent

SCENARIO_COLORS = {
    "conservative": COLOR_CONSERVATIVE,
    "realistic":    COLOR_REALISTIC,
    "aggressive":   COLOR_AGGRESSIVE,
}

ASSET_COLORS = {
    "equity": COLOR_EQUITY,
    "debt":   COLOR_DEBT,
    "gold":   COLOR_GOLD,
}

# ---------------------------------------------------------------------------
# Output paths
# ---------------------------------------------------------------------------

REPORTS_DIR       = "outputs/reports"
SAMPLE_PROFILES   = "data/sample_profiles.csv"
