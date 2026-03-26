"""
recommendation_engine.py
------------------------
Synthesises outputs from all upstream engines into a cohesive, human-readable
investment recommendation report.

Responsibilities
----------------
1. Select the primary scenario aligned with the investor's risk appetite.
2. Determine whether the current SIP is sufficient to meet the inflation-
   adjusted goal — and if not, compute the required top-up.
3. Generate instrument-level recommendations (which specific products to use
   within each asset class).
4. Produce a structured RecommendationReport with full narrative reasoning.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from modules.profile_engine import InvestorProfile
from modules.allocation_engine import AllocationResult
from modules.inflation_engine import InflationResult, goal_gap
from modules.scenario_engine import (
    ScenarioBundle,
    ScenarioResult,
    get_scenario_by_risk,
    monthly_sip_required,
)

# ---------------------------------------------------------------------------
# Instrument universe
# ---------------------------------------------------------------------------

# Recommended instruments per asset class × risk level
_EQUITY_INSTRUMENTS: Dict[str, List[str]] = {
    "low":    ["Large-Cap Index Fund (Nifty 50)", "ELSS Tax-Saver Fund"],
    "medium": ["Flexi-Cap Mutual Fund", "Large & Mid-Cap Fund", "Nifty Next 50 Index"],
    "high":   ["Small-Cap Fund", "Sectoral / Thematic Fund", "Direct Equity (Blue-Chip)"],
}

_DEBT_INSTRUMENTS: Dict[str, List[str]] = {
    "low":    ["Liquid Fund", "Short-Duration Debt Fund", "PPF (Public Provident Fund)"],
    "medium": ["Corporate Bond Fund", "Banking & PSU Debt Fund", "RBI Floating Rate Bond"],
    "high":   ["Dynamic Bond Fund", "Credit Risk Fund", "G-Sec / Gilt Fund"],
}

_GOLD_INSTRUMENTS: List[str] = [
    "Sovereign Gold Bond (SGB)",
    "Gold ETF",
    "Multi-Asset Fund (gold tranche)",
]

# Goal-specific SIP strategy labels
_GOAL_STRATEGY: Dict[str, str] = {
    "retirement": "Retirement SIP — long-horizon equity compounding with gradual debt shift",
    "home":       "Goal-Based SIP — capital-protected growth targeting down-payment corpus",
    "education":  "Education SIP — time-bound, inflation-beating balanced portfolio",
    "wealth":     "Wealth Creation SIP — aggressive equity allocation for maximum CAGR",
    "emergency":  "Liquid Emergency Corpus — capital preservation in overnight / liquid funds",
}


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------

@dataclass
class RecommendationReport:
    """Full investment recommendation for the investor."""

    profile_summary:        str
    primary_scenario:       ScenarioResult
    allocation_rationale:   str
    goal_gap_analysis:      Dict[str, float]
    sip_sufficient:         bool
    recommended_monthly_sip: float
    sip_top_up_required:    float              # 0 if already sufficient
    strategy_label:         str
    equity_instruments:     List[str]
    debt_instruments:       List[str]
    gold_instruments:       List[str]
    key_insights:           List[str]
    risk_warnings:          List[str]
    full_narrative:         str

    def to_dict(self) -> dict:
        return {
            "profile_summary":         self.profile_summary,
            "primary_scenario_label":  self.primary_scenario.label,
            "maturity_value":          self.primary_scenario.maturity_value,
            "total_invested":          self.primary_scenario.total_invested,
            "return_multiple":         self.primary_scenario.return_multiple,
            "inflation_adjusted_goal": self.goal_gap_analysis["adjusted_goal"],
            "projected_corpus":        self.goal_gap_analysis["projected_corpus"],
            "gap":                     self.goal_gap_analysis["gap"],
            "gap_pct":                 self.goal_gap_analysis["gap_pct"],
            "sip_sufficient":          self.sip_sufficient,
            "recommended_monthly_sip": self.recommended_monthly_sip,
            "sip_top_up_required":     self.sip_top_up_required,
            "strategy_label":          self.strategy_label,
        }


# ---------------------------------------------------------------------------
# Narrative builders
# ---------------------------------------------------------------------------

def _build_key_insights(
    profile: InvestorProfile,
    scenario: ScenarioResult,
    gap_data: Dict[str, float],
    sip_sufficient: bool,
    required_sip: float,
) -> List[str]:
    """Generate a concise bullet-point list of actionable insights."""
    insights: List[str] = []

    insights.append(
        f"At a {scenario.annual_return * 100:.0f}% annual return ({scenario.label} scenario), "
        f"your projected corpus is {scenario.maturity_value:,.0f} over {profile.target_years} year(s)."
    )

    insights.append(
        f"Your total capital invested (SIP + seed) will be {scenario.total_invested:,.0f}, "
        f"generating a {scenario.return_multiple:.2f}x return multiple."
    )

    if sip_sufficient:
        surplus = gap_data["gap"]
        insights.append(
            f"Your current monthly SIP of {profile.monthly_savings:,.0f} is SUFFICIENT. "
            f"Expected surplus over goal: {surplus:,.0f} ({gap_data['gap_pct']:.1f}%)."
        )
    else:
        insights.append(
            f"Your current SIP of {profile.monthly_savings:,.0f}/month falls SHORT of the "
            f"inflation-adjusted goal by {abs(gap_data['gap']):,.0f} ({abs(gap_data['gap_pct']):.1f}%). "
            f"Recommended SIP: {required_sip:,.0f}/month "
            f"(top-up of {required_sip - profile.monthly_savings:,.0f}/month)."
        )

    insights.append(
        f"Inflation will inflate your {profile.investment_goal} goal from "
        f"{gap_data['adjusted_goal'] / ((1.06 ** profile.target_years)):,.0f} today "
        f"to {gap_data['adjusted_goal']:,.0f} in {profile.target_years} year(s)."
    )

    if profile.savings_rate < 0.20:
        insights.append(
            f"Your savings rate is {profile.savings_rate * 100:.1f}% — below the recommended 20%. "
            "Consider reducing discretionary spending to accelerate goal achievement."
        )
    else:
        insights.append(
            f"Your savings rate of {profile.savings_rate * 100:.1f}% is healthy and goal-supportive."
        )

    return insights


def _build_risk_warnings(
    profile: InvestorProfile,
    allocation: AllocationResult,
    sip_sufficient: bool,
) -> List[str]:
    """Flag relevant risk considerations for the investor."""
    warnings: List[str] = []

    if profile.risk_appetite == "high" and profile.horizon_category == "short":
        warnings.append(
            "HIGH RISK + SHORT HORIZON: Equity markets can be volatile over short periods. "
            "A market downturn near your goal date could significantly erode corpus value."
        )

    if allocation.equity > 0.70 and profile.age > 50:
        warnings.append(
            f"Equity allocation of {allocation.equity * 100:.1f}% is aggressive for age {profile.age}. "
            "Consider a more conservative glide path to protect accumulated wealth."
        )

    if not sip_sufficient:
        warnings.append(
            "GOAL SHORTFALL DETECTED: Without increasing your SIP, you may not meet your "
            "inflation-adjusted target. Review your budget or extend the investment horizon."
        )

    if profile.investment_goal == "emergency" and allocation.equity > 0.10:
        warnings.append(
            "Emergency funds should remain liquid. Avoid locking funds in equity instruments "
            "that may require 3–5 years to recover from a market correction."
        )

    if not warnings:
        warnings.append(
            "No critical risk flags detected. Maintain SIP discipline and review annually."
        )

    return warnings


def _build_full_narrative(
    profile: InvestorProfile,
    allocation: AllocationResult,
    scenario: ScenarioResult,
    gap_data: Dict[str, float],
    sip_sufficient: bool,
    required_sip: float,
    strategy_label: str,
    equity_instruments: List[str],
    debt_instruments: List[str],
) -> str:
    """Compose the full paragraph-form investment narrative."""

    horizon_phrase = {
        "short":  "a short-term horizon of under 3 years",
        "medium": "a medium-term horizon of 4–7 years",
        "long":   "a long-term horizon of 8 or more years",
    }[profile.horizon_category]

    sip_note = (
        f"The current monthly SIP of {profile.monthly_savings:,.0f} is projected to be sufficient, "
        f"with an estimated surplus of {gap_data['gap']:,.0f} over the inflation-adjusted goal."
        if sip_sufficient else
        f"The current monthly SIP of {profile.monthly_savings:,.0f} is insufficient. "
        f"To meet the inflation-adjusted goal of {gap_data['adjusted_goal']:,.0f}, "
        f"a monthly SIP of {required_sip:,.0f} is recommended — "
        f"a top-up of {required_sip - profile.monthly_savings:,.0f}/month."
    )

    equity_list  = ", ".join(equity_instruments)
    debt_list    = ", ".join(debt_instruments)

    narrative = (
        f"Based on the investor's profile — age {profile.age}, "
        f"{profile.risk_appetite} risk appetite, and {horizon_phrase} — "
        f"the recommended strategy is: {strategy_label}.\n\n"

        f"{allocation.rationale}\n\n"

        f"Under the {scenario.label} scenario (assuming {scenario.annual_return * 100:.0f}% "
        f"annual return), the projected corpus at the end of {profile.target_years} year(s) "
        f"is {scenario.maturity_value:,.0f} against a total invested amount of "
        f"{scenario.total_invested:,.0f}, yielding a {scenario.return_multiple:.2f}x return multiple.\n\n"

        f"{sip_note}\n\n"

        f"For the equity tranche ({allocation.equity * 100:.1f}%), the following instruments "
        f"are recommended: {equity_list}. "
        f"For the debt tranche ({allocation.debt * 100:.1f}%): {debt_list}. "
        f"Gold exposure ({allocation.gold * 100:.1f}%) should be maintained via "
        f"Sovereign Gold Bonds or Gold ETFs for liquidity and inflation hedging.\n\n"

        f"It is strongly advised to review this allocation annually, step up the SIP by "
        f"at least 10% per year in line with income growth, and rebalance the portfolio "
        f"if any asset class drifts more than 5% from the target allocation."
    )

    return narrative


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_recommendation(
    profile: InvestorProfile,
    allocation: AllocationResult,
    inflation_result: InflationResult,
    scenario_bundle: ScenarioBundle,
) -> RecommendationReport:
    """
    Produce a full RecommendationReport by combining all engine outputs.

    Parameters
    ----------
    profile           : InvestorProfile from profile_engine.
    allocation        : AllocationResult from allocation_engine.
    inflation_result  : InflationResult from inflation_engine.
    scenario_bundle   : ScenarioBundle from scenario_engine.

    Returns
    -------
    RecommendationReport with narrative, instruments, insights, and warnings.
    """

    # 1. Select primary scenario
    primary = get_scenario_by_risk(scenario_bundle, profile.risk_appetite)

    # 2. Goal gap analysis
    gap_data = goal_gap(inflation_result, primary.maturity_value)

    # 3. SIP sufficiency check
    sip_sufficient = gap_data["gap"] >= 0

    # 4. Required SIP (back-solved against inflation-adjusted goal)
    required_sip = monthly_sip_required(
        target_corpus=inflation_result.inflation_adjusted_goal,
        annual_rate=primary.annual_return,
        years=profile.target_years,
    )
    # Subtract seed corpus contribution to isolate SIP requirement
    seed_fv = profile.annual_savings * ((1 + primary.annual_return) ** profile.target_years)
    net_sip_required = monthly_sip_required(
        target_corpus=max(inflation_result.inflation_adjusted_goal - seed_fv, 0),
        annual_rate=primary.annual_return,
        years=profile.target_years,
    )
    top_up = max(net_sip_required - profile.monthly_savings, 0.0)

    # 5. Instrument recommendations
    equity_instruments = _EQUITY_INSTRUMENTS.get(profile.risk_appetite, [])
    debt_instruments   = _DEBT_INSTRUMENTS.get(profile.risk_appetite, [])
    gold_instruments   = _GOLD_INSTRUMENTS

    # 6. Strategy label
    strategy_label = _GOAL_STRATEGY.get(profile.investment_goal, "Balanced SIP Strategy")

    # 7. Key insights
    key_insights = _build_key_insights(
        profile, primary, gap_data, sip_sufficient, net_sip_required
    )

    # 8. Risk warnings
    risk_warnings = _build_risk_warnings(profile, allocation, sip_sufficient)

    # 9. Full narrative
    from modules.profile_engine import profile_summary
    p_summary = profile_summary(profile)

    narrative = _build_full_narrative(
        profile, allocation, primary, gap_data,
        sip_sufficient, net_sip_required, strategy_label,
        equity_instruments, debt_instruments,
    )

    return RecommendationReport(
        profile_summary=p_summary,
        primary_scenario=primary,
        allocation_rationale=allocation.rationale,
        goal_gap_analysis=gap_data,
        sip_sufficient=sip_sufficient,
        recommended_monthly_sip=round(net_sip_required, 2),
        sip_top_up_required=round(top_up, 2),
        strategy_label=strategy_label,
        equity_instruments=equity_instruments,
        debt_instruments=debt_instruments,
        gold_instruments=gold_instruments,
        key_insights=key_insights,
        risk_warnings=risk_warnings,
        full_narrative=narrative,
    )
