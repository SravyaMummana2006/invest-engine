"""
profile_engine.py
-----------------
Responsible for ingesting raw user inputs, validating them, and returning
a structured financial profile dictionary that all downstream modules consume.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Literal

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

RiskLevel = Literal["low", "medium", "high"]
GoalType = Literal["retirement", "home", "education", "wealth", "emergency"]


# ---------------------------------------------------------------------------
# Profile dataclass
# ---------------------------------------------------------------------------

@dataclass
class InvestorProfile:
    """Immutable representation of a user's financial profile."""

    age: int
    monthly_income: float          # INR / USD – currency-agnostic
    monthly_savings: float
    investment_goal: GoalType
    target_years: int
    risk_appetite: RiskLevel

    # Derived fields (populated by build_profile)
    savings_rate: float = 0.0      # monthly_savings / monthly_income
    annual_savings: float = 0.0
    total_investable: float = 0.0  # present value of lump-sum + SIP corpus
    horizon_category: str = ""     # short / medium / long

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

_VALID_GOALS: set[str] = {"retirement", "home", "education", "wealth", "emergency"}
_VALID_RISK: set[str] = {"low", "medium", "high"}


def _validate_inputs(
    age: int,
    monthly_income: float,
    monthly_savings: float,
    investment_goal: str,
    target_years: int,
    risk_appetite: str,
) -> None:
    """Raise ValueError with a descriptive message on bad input."""

    if not (18 <= age <= 80):
        raise ValueError(f"Age must be between 18 and 80. Got: {age}")

    if monthly_income <= 0:
        raise ValueError("Monthly income must be positive.")

    if monthly_savings < 0:
        raise ValueError("Monthly savings cannot be negative.")

    if monthly_savings > monthly_income:
        raise ValueError("Monthly savings cannot exceed monthly income.")

    if investment_goal not in _VALID_GOALS:
        raise ValueError(
            f"investment_goal must be one of {_VALID_GOALS}. Got: {investment_goal!r}"
        )

    if not (1 <= target_years <= 40):
        raise ValueError(f"target_years must be between 1 and 40. Got: {target_years}")

    if risk_appetite not in _VALID_RISK:
        raise ValueError(
            f"risk_appetite must be one of {_VALID_RISK}. Got: {risk_appetite!r}"
        )


# ---------------------------------------------------------------------------
# Horizon classification
# ---------------------------------------------------------------------------

def _classify_horizon(target_years: int) -> str:
    """Bucket investment horizon into human-readable category."""
    if target_years <= 3:
        return "short"
    elif target_years <= 7:
        return "medium"
    else:
        return "long"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_profile(
    age: int,
    monthly_income: float,
    monthly_savings: float,
    investment_goal: str,
    target_years: int,
    risk_appetite: str,
) -> InvestorProfile:
    """
    Validate inputs and return a fully-populated InvestorProfile.

    Parameters
    ----------
    age               : Investor's current age (18–80).
    monthly_income    : Gross monthly income.
    monthly_savings   : Amount saved / available to invest each month.
    investment_goal   : One of retirement | home | education | wealth | emergency.
    target_years      : Number of years until the goal is needed.
    risk_appetite     : low | medium | high.

    Returns
    -------
    InvestorProfile dataclass instance.
    """

    # --- Validate ---
    _validate_inputs(
        age, monthly_income, monthly_savings,
        investment_goal, target_years, risk_appetite,
    )

    # --- Derived metrics ---
    savings_rate = round(monthly_savings / monthly_income, 4)
    annual_savings = monthly_savings * 12
    # Simple proxy: total investable = 1 year of savings as seed corpus
    total_investable = annual_savings

    horizon_category = _classify_horizon(target_years)

    return InvestorProfile(
        age=age,
        monthly_income=monthly_income,
        monthly_savings=monthly_savings,
        investment_goal=investment_goal,           # type: ignore[arg-type]
        target_years=target_years,
        risk_appetite=risk_appetite,               # type: ignore[arg-type]
        savings_rate=savings_rate,
        annual_savings=annual_savings,
        total_investable=total_investable,
        horizon_category=horizon_category,
    )


def profile_summary(profile: InvestorProfile) -> str:
    """Return a one-paragraph human-readable summary of the profile."""
    return (
        f"Investor aged {profile.age} with a monthly income of {profile.monthly_income:,.0f} "
        f"saves {profile.monthly_savings:,.0f}/month ({profile.savings_rate * 100:.1f}% savings rate). "
        f"Goal: {profile.investment_goal.upper()} in {profile.target_years} year(s) "
        f"({profile.horizon_category}-term horizon). "
        f"Risk appetite: {profile.risk_appetite.upper()}."
    )
