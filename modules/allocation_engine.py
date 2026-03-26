"""
allocation_engine.py
--------------------
Determines the optimal asset allocation (equity / debt / gold) based on the
investor's risk appetite, horizon, age, and goal type.

Design philosophy
-----------------
- Allocation matrices are data-driven, not hard-coded if/else chains.
- Age-based glide path applies a tapering adjustment so older investors
  automatically shift toward capital preservation.
- Goal-type overrides fine-tune the base allocation for domain-specific logic
  (e.g., emergency funds stay 100 % in debt-equivalent instruments).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from modules.profile_engine import InvestorProfile

# ---------------------------------------------------------------------------
# Types & constants
# ---------------------------------------------------------------------------

AssetClass = str  # "equity" | "debt" | "gold"

# Base allocation matrix: risk_level -> horizon -> (equity%, debt%, gold%)
# Weights always sum to 1.0
_BASE_ALLOCATION: Dict[str, Dict[str, tuple[float, float, float]]] = {
    "low": {
        "short":  (0.10, 0.80, 0.10),
        "medium": (0.20, 0.70, 0.10),
        "long":   (0.30, 0.60, 0.10),
    },
    "medium": {
        "short":  (0.30, 0.55, 0.15),
        "medium": (0.50, 0.40, 0.10),
        "long":   (0.65, 0.25, 0.10),
    },
    "high": {
        "short":  (0.50, 0.40, 0.10),
        "medium": (0.70, 0.20, 0.10),
        "long":   (0.80, 0.10, 0.10),
    },
}

# Goal-type overrides: additive delta applied to (equity, debt, gold)
# Values represent percentage-point shifts; rows sum to 0.
_GOAL_OVERRIDES: Dict[str, tuple[float, float, float]] = {
    "retirement": ( 0.05, -0.05,  0.00),  # slightly more equity for long compounding
    "home":       (-0.05,  0.05,  0.00),  # capital safety matters more
    "education":  ( 0.00,  0.00,  0.00),  # neutral
    "wealth":     ( 0.10, -0.05, -0.05),  # aggressive equity push
    "emergency":  (-0.15,  0.15,  0.00),  # maximum liquidity / safety
}

# Age glide-path: for every year above 45, reduce equity by this fraction
_GLIDE_PATH_THRESHOLD_AGE = 45
_GLIDE_PATH_EQUITY_TAPER_PER_YEAR = 0.005   # 0.5 % per year above 45
_GLIDE_PATH_MAX_TAPER = 0.20                 # cap taper at 20 %


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------

@dataclass
class AllocationResult:
    equity: float    # 0.0 – 1.0
    debt: float
    gold: float
    rationale: str

    def to_dict(self) -> dict:
        return {
            "equity": round(self.equity * 100, 2),
            "debt":   round(self.debt   * 100, 2),
            "gold":   round(self.gold   * 100, 2),
        }

    def as_percentages(self) -> Dict[str, float]:
        return self.to_dict()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _apply_glide_path(equity: float, age: int) -> float:
    """Taper equity allocation for investors older than the threshold age."""
    if age <= _GLIDE_PATH_THRESHOLD_AGE:
        return equity
    excess_years = age - _GLIDE_PATH_THRESHOLD_AGE
    taper = min(excess_years * _GLIDE_PATH_EQUITY_TAPER_PER_YEAR, _GLIDE_PATH_MAX_TAPER)
    return max(equity - taper, 0.05)   # equity floor at 5 %


def _normalise(equity: float, debt: float, gold: float) -> tuple[float, float, float]:
    """Ensure the three weights sum exactly to 1.0 after adjustments."""
    total = equity + debt + gold
    if total == 0:
        return (0.0, 1.0, 0.0)
    return (equity / total, debt / total, gold / total)


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_allocation(profile: InvestorProfile) -> AllocationResult:
    """
    Compute a personalised asset allocation from the investor profile.

    Steps
    -----
    1. Look up the base allocation matrix (risk × horizon).
    2. Apply goal-type additive override.
    3. Apply age-based glide-path taper on equity.
    4. Re-normalise weights to sum to 1.0.
    5. Build a human-readable rationale string.

    Parameters
    ----------
    profile : InvestorProfile
        Populated profile from profile_engine.build_profile().

    Returns
    -------
    AllocationResult with equity / debt / gold weights and rationale text.
    """

    # Step 1 – base allocation
    base_equity, base_debt, base_gold = (
        _BASE_ALLOCATION[profile.risk_appetite][profile.horizon_category]
    )

    # Step 2 – goal override
    d_equity, d_debt, d_gold = _GOAL_OVERRIDES.get(profile.investment_goal, (0, 0, 0))
    adj_equity = _clamp(base_equity + d_equity)
    adj_debt   = _clamp(base_debt   + d_debt)
    adj_gold   = _clamp(base_gold   + d_gold)

    # Step 3 – age glide path
    adj_equity = _apply_glide_path(adj_equity, profile.age)

    # Step 4 – normalise
    equity, debt, gold = _normalise(adj_equity, adj_debt, adj_gold)

    # Step 5 – rationale
    rationale = _build_rationale(profile, equity, debt, gold)

    return AllocationResult(
        equity=round(equity, 4),
        debt=round(debt,   4),
        gold=round(gold,   4),
        rationale=rationale,
    )


def _build_rationale(
    profile: InvestorProfile,
    equity: float,
    debt: float,
    gold: float,
) -> str:
    """Generate a plain-English explanation of the allocation decision."""

    lines: list[str] = []

    # Risk appetite
    risk_map = {
        "low":    "a conservative risk appetite, prioritising capital preservation",
        "medium": "a balanced risk appetite, seeking growth with moderate safety",
        "high":   "an aggressive risk appetite, maximising long-term growth potential",
    }
    lines.append(f"The investor has {risk_map[profile.risk_appetite]}.")

    # Horizon
    horizon_map = {
        "short":  "short investment horizon (≤ 3 years) limits equity exposure to protect principal",
        "medium": "medium horizon (4–7 years) allows a balanced equity–debt mix",
        "long":   "long horizon (8+ years) supports a higher equity weighting for compounding gains",
    }
    lines.append(f"The {horizon_map[profile.horizon_category]}.")

    # Goal nuance
    goal_map = {
        "retirement": "Retirement planning benefits from sustained equity growth over decades.",
        "home":       "A home-purchase goal demands higher capital safety, increasing debt allocation.",
        "education":  "Education funding requires predictable returns; allocation is kept balanced.",
        "wealth":     "Pure wealth creation justifies maximum equity exposure.",
        "emergency":  "Emergency funds require immediate liquidity; near-full debt allocation applies.",
    }
    lines.append(goal_map.get(profile.investment_goal, ""))

    # Age note
    if profile.age > _GLIDE_PATH_THRESHOLD_AGE:
        lines.append(
            f"An age-based glide path has reduced equity by "
            f"{(profile.age - _GLIDE_PATH_THRESHOLD_AGE) * _GLIDE_PATH_EQUITY_TAPER_PER_YEAR * 100:.1f} "
            f"percentage points to protect accumulated wealth as retirement approaches."
        )

    # Final allocation summary
    lines.append(
        f"Resulting allocation — Equity: {equity*100:.1f}%, "
        f"Debt: {debt*100:.1f}%, Gold: {gold*100:.1f}%."
    )

    return " ".join(lines)
