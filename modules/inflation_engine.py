"""
inflation_engine.py
-------------------
Models inflation's impact on investment goals and purchasing power.

Responsibilities
----------------
1. Adjust a future goal amount to its inflation-corrected present value.
2. Compute the real (inflation-adjusted) return rate for a given nominal return.
3. Generate a year-by-year inflation erosion table for visualisation.
4. Provide goal-specific inflation rate assumptions grounded in real-world data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Constants – default inflation assumptions
# ---------------------------------------------------------------------------

# General consumer price inflation (CPI) baseline
DEFAULT_INFLATION_RATE: float = 0.06          # 6 % per annum

# Goal-specific inflation rates (some goals inflate faster than CPI)
GOAL_INFLATION_RATES: Dict[str, float] = {
    "retirement": 0.06,   # general living-cost inflation
    "home":       0.07,   # real-estate inflation tends to outpace CPI
    "education":  0.08,   # education inflation historically higher
    "wealth":     0.06,   # benchmark against CPI
    "emergency":  0.06,   # liquid fund should beat CPI
}


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------

@dataclass
class InflationResult:
    present_goal_value: float          # what the user typed as goal
    inflation_rate: float              # rate used for this goal type
    target_years: int
    inflation_adjusted_goal: float     # FV = PV * (1 + i)^n
    real_return_rate: float            # given a nominal rate
    nominal_rate_used: float           # the nominal rate passed in
    erosion_table: pd.DataFrame        # year-by-year purchasing power table

    def summary(self) -> str:
        return (
            f"Goal of {self.present_goal_value:,.0f} will require "
            f"{self.inflation_adjusted_goal:,.0f} in {self.target_years} year(s) "
            f"at {self.inflation_rate * 100:.1f}% annual inflation. "
            f"Real return rate (vs nominal {self.nominal_rate_used * 100:.1f}%): "
            f"{self.real_return_rate * 100:.2f}%."
        )


# ---------------------------------------------------------------------------
# Core formulas
# ---------------------------------------------------------------------------

def future_value(present_value: float, inflation_rate: float, years: int) -> float:
    """
    FV = PV * (1 + i)^n

    Computes the inflation-adjusted future cost of a goal.

    Parameters
    ----------
    present_value   : Today's goal amount.
    inflation_rate  : Annual inflation rate (decimal, e.g. 0.06 for 6%).
    years           : Investment horizon in years.

    Returns
    -------
    Inflation-adjusted future value.
    """
    if present_value <= 0:
        raise ValueError("present_value must be positive.")
    if inflation_rate < 0:
        raise ValueError("inflation_rate cannot be negative.")
    if years < 0:
        raise ValueError("years cannot be negative.")

    return present_value * ((1 + inflation_rate) ** years)


def real_return_rate(nominal_rate: float, inflation_rate: float) -> float:
    """
    Fisher equation: real rate = (1 + nominal) / (1 + inflation) - 1

    Parameters
    ----------
    nominal_rate    : Gross/nominal annual return rate (decimal).
    inflation_rate  : Annual inflation rate (decimal).

    Returns
    -------
    Real (inflation-adjusted) return rate.
    """
    if inflation_rate <= -1:
        raise ValueError("inflation_rate cannot be ≤ -1.")
    return (1 + nominal_rate) / (1 + inflation_rate) - 1


# ---------------------------------------------------------------------------
# Erosion table
# ---------------------------------------------------------------------------

def build_erosion_table(
    present_goal_value: float,
    inflation_rate: float,
    years: int,
) -> pd.DataFrame:
    """
    Build a year-by-year table showing:
    - Nominal goal cost (inflated)
    - Purchasing power of today's money
    - Cumulative inflation multiplier

    Parameters
    ----------
    present_goal_value : Today's target corpus.
    inflation_rate     : Annual inflation rate (decimal).
    years              : Number of years to project.

    Returns
    -------
    pd.DataFrame with columns:
        year | nominal_goal | purchasing_power | cumulative_inflation_factor
    """
    year_range = np.arange(0, years + 1)
    factors = (1 + inflation_rate) ** year_range

    nominal_goal       = present_goal_value * factors
    purchasing_power   = present_goal_value / factors   # erosion of today's ₹1
    cum_inflation_pct  = (factors - 1) * 100

    return pd.DataFrame({
        "year":                       year_range.astype(int),
        "nominal_goal":               np.round(nominal_goal, 2),
        "purchasing_power":           np.round(purchasing_power, 2),
        "cumulative_inflation_pct":   np.round(cum_inflation_pct, 2),
    })


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyse_inflation(
    present_goal_value: float,
    goal_type: str,
    target_years: int,
    nominal_return_rate: float = 0.12,
    override_inflation_rate: float | None = None,
) -> InflationResult:
    """
    Full inflation analysis for a given goal.

    Parameters
    ----------
    present_goal_value      : User's stated goal amount in today's money.
    goal_type               : One of retirement | home | education | wealth | emergency.
    target_years            : Years until the goal is needed.
    nominal_return_rate     : Expected nominal annual return (default 12%).
    override_inflation_rate : If provided, bypasses the goal-specific default.

    Returns
    -------
    InflationResult dataclass with all computed fields and an erosion table.
    """

    # Resolve inflation rate
    infl_rate: float = (
        override_inflation_rate
        if override_inflation_rate is not None
        else GOAL_INFLATION_RATES.get(goal_type, DEFAULT_INFLATION_RATE)
    )

    # Core computations
    fv        = future_value(present_goal_value, infl_rate, target_years)
    real_rate = real_return_rate(nominal_return_rate, infl_rate)
    table     = build_erosion_table(present_goal_value, infl_rate, target_years)

    return InflationResult(
        present_goal_value=present_goal_value,
        inflation_rate=infl_rate,
        target_years=target_years,
        inflation_adjusted_goal=round(fv, 2),
        real_return_rate=round(real_rate, 6),
        nominal_rate_used=nominal_return_rate,
        erosion_table=table,
    )


def goal_gap(
    inflation_result: InflationResult,
    projected_corpus: float,
) -> Dict[str, float]:
    """
    Compute how much the projected corpus falls short of (or exceeds)
    the inflation-adjusted goal.

    Parameters
    ----------
    inflation_result  : Output from analyse_inflation().
    projected_corpus  : Expected corpus at end of investment period.

    Returns
    -------
    Dict with keys: adjusted_goal | projected_corpus | gap | gap_pct
    """
    adjusted_goal = inflation_result.inflation_adjusted_goal
    gap           = projected_corpus - adjusted_goal
    gap_pct       = (gap / adjusted_goal) * 100 if adjusted_goal else 0.0

    return {
        "adjusted_goal":    round(adjusted_goal,   2),
        "projected_corpus": round(projected_corpus, 2),
        "gap":              round(gap,   2),
        "gap_pct":          round(gap_pct, 2),
    }
