"""
scenario_engine.py
------------------
Simulates portfolio growth across three market scenarios:
  - Conservative  (8%  annual return)
  - Realistic     (12% annual return)
  - Aggressive    (15% annual return)

Each scenario models:
  1. SIP (Systematic Investment Plan) monthly contributions compounding.
  2. Lump-sum seed corpus compounding (first-year savings used as seed).
  3. Year-by-year invested amount vs. maturity value breakdown.
  4. A summary DataFrame suitable for downstream charting and reporting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

import numpy as np
import pandas as pd

from modules.profile_engine import InvestorProfile

# ---------------------------------------------------------------------------
# Scenario definitions
# ---------------------------------------------------------------------------

SCENARIOS: Dict[str, float] = {
    "conservative": 0.08,
    "realistic":    0.12,
    "aggressive":   0.15,
}

SCENARIO_COLORS: Dict[str, str] = {
    "conservative": "#4A90D9",
    "realistic":    "#27AE60",
    "aggressive":   "#E74C3C",
}


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ScenarioResult:
    """Holds the full projection for a single scenario."""
    label: str
    annual_return: float
    monthly_return: float
    total_invested: float
    maturity_value: float
    total_returns: float
    return_multiple: float          # maturity_value / total_invested
    growth_table: pd.DataFrame      # year | invested_so_far | corpus_value | gains

    def summary(self) -> str:
        return (
            f"[{self.label.upper()}] Return: {self.annual_return * 100:.0f}% p.a. | "
            f"Invested: {self.total_invested:,.0f} | "
            f"Maturity: {self.maturity_value:,.0f} | "
            f"Multiple: {self.return_multiple:.2f}x"
        )


@dataclass
class ScenarioBundle:
    """Container for all three scenario results."""
    conservative: ScenarioResult
    realistic:    ScenarioResult
    aggressive:   ScenarioResult
    monthly_sip:  float
    target_years: int
    seed_corpus:  float

    def all_results(self) -> List[ScenarioResult]:
        return [self.conservative, self.realistic, self.aggressive]

    def comparison_table(self) -> pd.DataFrame:
        rows = []
        for r in self.all_results():
            rows.append({
                "Scenario":        r.label.capitalize(),
                "Annual Return":   f"{r.annual_return * 100:.0f}%",
                "Total Invested":  round(r.total_invested, 2),
                "Maturity Value":  round(r.maturity_value, 2),
                "Total Returns":   round(r.total_returns, 2),
                "Return Multiple": f"{r.return_multiple:.2f}x",
            })
        return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# SIP + lump-sum compounding engine
# ---------------------------------------------------------------------------

def _sip_future_value(
    monthly_sip: float,
    monthly_rate: float,
    months: int,
) -> float:
    """
    Standard SIP future value formula:
        FV = P * [((1 + r)^n - 1) / r] * (1 + r)

    Parameters
    ----------
    monthly_sip   : Fixed monthly investment amount.
    monthly_rate  : Monthly interest rate (annual / 12).
    months        : Total number of SIP instalments.

    Returns
    -------
    Corpus value at end of SIP period.
    """
    if monthly_rate == 0:
        return monthly_sip * months
    return (
        monthly_sip
        * (((1 + monthly_rate) ** months - 1) / monthly_rate)
        * (1 + monthly_rate)
    )


def _lump_sum_future_value(
    principal: float,
    annual_rate: float,
    years: int,
) -> float:
    """Standard compound interest: FV = P * (1 + r)^n"""
    return principal * ((1 + annual_rate) ** years)


# ---------------------------------------------------------------------------
# Year-by-year growth table
# ---------------------------------------------------------------------------

def _build_growth_table(
    monthly_sip: float,
    seed_corpus: float,
    annual_rate: float,
    target_years: int,
) -> pd.DataFrame:
    """
    Generate a year-by-year breakdown of:
      - Cumulative amount invested (SIP contributions + seed)
      - Portfolio corpus value
      - Unrealised gains

    Parameters
    ----------
    monthly_sip   : Monthly SIP contribution.
    seed_corpus   : Initial lump-sum at year 0.
    annual_rate   : Annual return rate for this scenario.
    target_years  : Total investment horizon.

    Returns
    -------
    pd.DataFrame with columns: year | invested_so_far | corpus_value | gains | gains_pct
    """
    monthly_rate = annual_rate / 12
    records: List[dict] = []

    for yr in range(1, target_years + 1):
        months = yr * 12
        sip_corpus  = _sip_future_value(monthly_sip, monthly_rate, months)
        seed_grown  = _lump_sum_future_value(seed_corpus, annual_rate, yr)
        corpus      = sip_corpus + seed_grown
        invested    = (monthly_sip * months) + seed_corpus
        gains       = corpus - invested
        gains_pct   = (gains / invested * 100) if invested > 0 else 0.0

        records.append({
            "year":           yr,
            "invested_so_far": round(invested, 2),
            "corpus_value":    round(corpus,   2),
            "gains":           round(gains,    2),
            "gains_pct":       round(gains_pct, 2),
        })

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Single scenario runner
# ---------------------------------------------------------------------------

def _run_scenario(
    label: str,
    annual_rate: float,
    monthly_sip: float,
    seed_corpus: float,
    target_years: int,
) -> ScenarioResult:
    """Build a complete ScenarioResult for one return assumption."""

    monthly_rate  = annual_rate / 12
    total_months  = target_years * 12

    sip_corpus    = _sip_future_value(monthly_sip, monthly_rate, total_months)
    seed_grown    = _lump_sum_future_value(seed_corpus, annual_rate, target_years)
    maturity      = sip_corpus + seed_grown
    total_invested = (monthly_sip * total_months) + seed_corpus
    total_returns  = maturity - total_invested
    multiple       = maturity / total_invested if total_invested > 0 else 0.0

    growth_table = _build_growth_table(monthly_sip, seed_corpus, annual_rate, target_years)

    return ScenarioResult(
        label=label,
        annual_return=annual_rate,
        monthly_return=monthly_rate,
        total_invested=round(total_invested, 2),
        maturity_value=round(maturity,       2),
        total_returns=round(total_returns,   2),
        return_multiple=round(multiple,      4),
        growth_table=growth_table,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_all_scenarios(profile: InvestorProfile) -> ScenarioBundle:
    """
    Simulate all three scenarios for the given investor profile.

    The seed corpus is the investor's first-year annual savings (lump-sum proxy).
    Monthly SIP = profile.monthly_savings.

    Parameters
    ----------
    profile : InvestorProfile from profile_engine.build_profile().

    Returns
    -------
    ScenarioBundle containing conservative, realistic, and aggressive results.
    """
    monthly_sip  = profile.monthly_savings
    seed_corpus  = profile.annual_savings       # first-year savings as seed
    target_years = profile.target_years

    results = {
        label: _run_scenario(label, rate, monthly_sip, seed_corpus, target_years)
        for label, rate in SCENARIOS.items()
    }

    return ScenarioBundle(
        conservative=results["conservative"],
        realistic=results["realistic"],
        aggressive=results["aggressive"],
        monthly_sip=monthly_sip,
        target_years=target_years,
        seed_corpus=seed_corpus,
    )


def get_scenario_by_risk(bundle: ScenarioBundle, risk_appetite: str) -> ScenarioResult:
    """
    Map risk appetite to the most appropriate scenario result.

    low    -> conservative
    medium -> realistic
    high   -> aggressive
    """
    mapping = {
        "low":    bundle.conservative,
        "medium": bundle.realistic,
        "high":   bundle.aggressive,
    }
    return mapping.get(risk_appetite, bundle.realistic)


def monthly_sip_required(
    target_corpus: float,
    annual_rate: float,
    years: int,
) -> float:
    """
    Back-solve for the monthly SIP needed to reach a target corpus.

    Inverse of the SIP FV formula:
        P = FV * r / [((1 + r)^n - 1) * (1 + r)]

    Parameters
    ----------
    target_corpus : Desired corpus at end of period.
    annual_rate   : Expected annual return rate.
    years         : Investment horizon in years.

    Returns
    -------
    Required monthly SIP amount.
    """
    monthly_rate = annual_rate / 12
    months       = years * 12

    if monthly_rate == 0:
        return target_corpus / months

    denominator = (((1 + monthly_rate) ** months - 1) / monthly_rate) * (1 + monthly_rate)
    return round(target_corpus / denominator, 2) if denominator > 0 else 0.0
