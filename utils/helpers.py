"""
utils/helpers.py
----------------
Shared utility functions used across modules and the Streamlit app.

Covers
------
- Number formatting  (currency, percentages, multiples, large-number shorthand)
- DataFrame helpers  (styling, export)
- Report generation  (text + CSV export to outputs/reports/)
- Date / time        (run timestamps)
- Validation         (guard-clause helpers reusable outside profile_engine)
"""

from __future__ import annotations

import os
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from utils.constants import (
    CURRENCY_SYMBOL,
    LARGE_NUMBER_UNIT,
    CRORE_UNIT,
    REPORTS_DIR,
)

# ---------------------------------------------------------------------------
# Number formatting
# ---------------------------------------------------------------------------

def fmt_currency(value: float, short: bool = False) -> str:
    """
    Format a numeric value as a currency string.

    Parameters
    ----------
    value : Numeric amount.
    short : If True, abbreviate to Lakhs (L) or Crores (Cr).

    Examples
    --------
    fmt_currency(1_500_000)         -> "₹15,00,000"
    fmt_currency(1_500_000, short=True) -> "₹15.00 L"
    fmt_currency(15_000_000, short=True) -> "₹1.50 Cr"
    """
    if short:
        if abs(value) >= CRORE_UNIT:
            return f"{CURRENCY_SYMBOL}{value / CRORE_UNIT:.2f} Cr"
        elif abs(value) >= LARGE_NUMBER_UNIT:
            return f"{CURRENCY_SYMBOL}{value / LARGE_NUMBER_UNIT:.2f} L"
    # Indian comma formatting: xx,xx,xxx
    return f"{CURRENCY_SYMBOL}{_indian_comma(value)}"


def _indian_comma(value: float) -> str:
    """Apply Indian numbering system comma placement."""
    is_negative = value < 0
    value = abs(value)
    integer_part = int(value)
    decimal_part = round(value - integer_part, 2)

    s = str(integer_part)
    if len(s) <= 3:
        result = s
    else:
        last_three = s[-3:]
        remaining  = s[:-3]
        groups = []
        while len(remaining) > 2:
            groups.append(remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.append(remaining)
        groups.reverse()
        result = ",".join(groups) + "," + last_three

    if decimal_part > 0:
        result += f".{int(decimal_part * 100):02d}"

    return ("-" if is_negative else "") + result


def fmt_percent(value: float, decimals: int = 1) -> str:
    """Format a decimal fraction as a percentage string. e.g. 0.125 -> '12.5%'"""
    return f"{value * 100:.{decimals}f}%"


def fmt_multiple(value: float) -> str:
    """Format a return multiple. e.g. 3.456 -> '3.46x'"""
    return f"{value:.2f}x"


def fmt_number(value: float, decimals: int = 0) -> str:
    """Plain number formatting with comma separators."""
    return f"{value:,.{decimals}f}"


# ---------------------------------------------------------------------------
# DataFrame utilities
# ---------------------------------------------------------------------------

def style_growth_table(df: pd.DataFrame) -> pd.io.formats.style.Styler:
    """
    Apply consistent Pandas Styler formatting to a scenario growth table.

    Expects columns: year | invested_so_far | corpus_value | gains | gains_pct
    """
    return (
        df.style
        .format({
            "invested_so_far": lambda v: fmt_currency(v, short=True),
            "corpus_value":    lambda v: fmt_currency(v, short=True),
            "gains":           lambda v: fmt_currency(v, short=True),
            "gains_pct":       lambda v: f"{v:.1f}%",
        })
        .set_properties(**{"text-align": "right"})
        .set_table_styles([{
            "selector": "th",
            "props": [("text-align", "center"), ("font-weight", "bold")],
        }])
        .background_gradient(subset=["corpus_value"], cmap="Greens")
    )


def growth_table_display_names(df: pd.DataFrame) -> pd.DataFrame:
    """Rename growth table columns to human-friendly display names."""
    return df.rename(columns={
        "year":           "Year",
        "invested_so_far": "Invested (Cumulative)",
        "corpus_value":   "Corpus Value",
        "gains":          "Unrealised Gains",
        "gains_pct":      "Gain %",
    })


def comparison_table_display(df: pd.DataFrame) -> pd.DataFrame:
    """
    Format the scenario comparison table values for display.
    Input columns: Scenario | Annual Return | Total Invested | Maturity Value |
                   Total Returns | Return Multiple
    """
    df = df.copy()
    for col in ["Total Invested", "Maturity Value", "Total Returns"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda v: fmt_currency(v, short=True))
    return df


# ---------------------------------------------------------------------------
# Timestamp
# ---------------------------------------------------------------------------

def run_timestamp() -> str:
    """Return a filesystem-safe timestamp string for file naming."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def display_timestamp() -> str:
    """Return a human-readable timestamp for report headers."""
    return datetime.now().strftime("%d %B %Y, %H:%M")


# ---------------------------------------------------------------------------
# Report export
# ---------------------------------------------------------------------------

def ensure_reports_dir() -> Path:
    """Create the reports output directory if it does not exist."""
    path = Path(REPORTS_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def export_recommendation_txt(
    narrative: str,
    insights: List[str],
    warnings: List[str],
    profile_summary: str,
    filename: Optional[str] = None,
) -> Path:
    """
    Write the full recommendation narrative to a .txt report file.

    Parameters
    ----------
    narrative       : Full narrative text from recommendation_engine.
    insights        : List of key insight strings.
    warnings        : List of risk warning strings.
    profile_summary : One-line profile summary.
    filename        : Optional custom filename (without extension).

    Returns
    -------
    Path to the written file.
    """
    reports_dir = ensure_reports_dir()
    ts = filename or f"recommendation_{run_timestamp()}"
    filepath = reports_dir / f"{ts}.txt"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("  INTELLIGENT INVESTMENT DECISION ENGINE — RECOMMENDATION REPORT\n")
        f.write(f"  Generated: {display_timestamp()}\n")
        f.write("=" * 70 + "\n\n")

        f.write("INVESTOR PROFILE\n")
        f.write("-" * 40 + "\n")
        f.write(profile_summary + "\n\n")

        f.write("INVESTMENT NARRATIVE\n")
        f.write("-" * 40 + "\n")
        f.write(narrative + "\n\n")

        f.write("KEY INSIGHTS\n")
        f.write("-" * 40 + "\n")
        for i, insight in enumerate(insights, 1):
            f.write(f"  {i}. {insight}\n")
        f.write("\n")

        f.write("RISK WARNINGS\n")
        f.write("-" * 40 + "\n")
        for warning in warnings:
            f.write(f"  ⚠  {warning}\n")
        f.write("\n")

        f.write("=" * 70 + "\n")
        f.write("  DISCLAIMER: This report is for informational purposes only.\n")
        f.write("  It does not constitute financial advice. Consult a SEBI-registered\n")
        f.write("  investment advisor before making investment decisions.\n")
        f.write("=" * 70 + "\n")

    return filepath


def export_growth_table_csv(
    df: pd.DataFrame,
    scenario_label: str,
    filename: Optional[str] = None,
) -> Path:
    """
    Export a scenario growth table to CSV.

    Parameters
    ----------
    df             : Growth table DataFrame.
    scenario_label : e.g. 'realistic'
    filename       : Optional custom filename (without extension).

    Returns
    -------
    Path to the written CSV file.
    """
    reports_dir = ensure_reports_dir()
    ts = filename or f"growth_{scenario_label}_{run_timestamp()}"
    filepath = reports_dir / f"{ts}.csv"
    df.to_csv(filepath, index=False)
    return filepath


def export_summary_json(summary_dict: Dict[str, Any], filename: Optional[str] = None) -> Path:
    """
    Export the recommendation summary dict as JSON for downstream consumption.

    Parameters
    ----------
    summary_dict : Dict from RecommendationReport.to_dict().
    filename     : Optional custom filename (without extension).

    Returns
    -------
    Path to the written JSON file.
    """
    reports_dir = ensure_reports_dir()
    ts = filename or f"summary_{run_timestamp()}"
    filepath = reports_dir / f"{ts}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(summary_dict, f, indent=2, default=str)
    return filepath


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def is_positive(value: float, label: str = "value") -> None:
    """Raise ValueError if value is not strictly positive."""
    if value <= 0:
        raise ValueError(f"{label} must be positive. Got: {value}")


def is_in_range(value: float, low: float, high: float, label: str = "value") -> None:
    """Raise ValueError if value is outside [low, high]."""
    if not (low <= value <= high):
        raise ValueError(f"{label} must be between {low} and {high}. Got: {value}")


def is_one_of(value: str, valid: set, label: str = "value") -> None:
    """Raise ValueError if value is not in the valid set."""
    if value not in valid:
        raise ValueError(f"{label} must be one of {valid}. Got: {value!r}")
