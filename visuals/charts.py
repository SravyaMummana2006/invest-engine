"""
visuals/charts.py
-----------------
All Plotly chart factory functions for the Streamlit dashboard.

Each function accepts pre-computed data structures from the engine modules
and returns a fully-configured plotly.graph_objects.Figure — zero Streamlit
coupling, fully testable in isolation.

Charts
------
1. portfolio_growth_chart     — Invested vs corpus value across all 3 scenarios
2. allocation_donut_chart     — Equity / Debt / Gold allocation breakdown
3. inflation_erosion_chart    — Purchasing power erosion over time
4. goal_gap_bar_chart         — Corpus vs inflation-adjusted goal comparison
5. scenario_comparison_bar    — Maturity value comparison across scenarios
6. sip_vs_returns_area_chart  — Stacked area: invested amount vs gains
"""

from __future__ import annotations

from typing import Dict, List

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from utils.constants import (
    ASSET_COLORS,
    SCENARIO_COLORS,
    COLOR_INVESTED,
    COLOR_ACCENT,
    COLOR_CARD_BG,
    COLOR_BACKGROUND,
    CURRENCY_SYMBOL,
)
from utils.helpers import fmt_currency

# ---------------------------------------------------------------------------
# Shared layout defaults
# ---------------------------------------------------------------------------

_FONT_FAMILY = "Inter, -apple-system, BlinkMacSystemFont, sans-serif"

_BASE_LAYOUT = dict(
    font=dict(family=_FONT_FAMILY, color="#E0E0E0", size=12),
    paper_bgcolor=COLOR_CARD_BG,
    plot_bgcolor=COLOR_CARD_BG,
    margin=dict(l=40, r=40, t=60, b=40),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        bordercolor="rgba(255,255,255,0.1)",
        borderwidth=1,
        font=dict(size=11),
    ),
    hoverlabel=dict(
        bgcolor="#1A1F2E",
        bordercolor=COLOR_ACCENT,
        font=dict(color="#FFFFFF", size=12),
    ),
)

_AXIS_STYLE = dict(
    showgrid=True,
    gridcolor="rgba(255,255,255,0.06)",
    zeroline=False,
    linecolor="rgba(255,255,255,0.15)",
    tickfont=dict(size=11, color="#A0A0A0"),
)


def _apply_base_layout(fig: go.Figure, title: str) -> go.Figure:
    """Apply consistent dark-theme layout to any figure."""
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=16, color="#FFFFFF", family=_FONT_FAMILY),
            x=0.0,
            xanchor="left",
        ),
        **_BASE_LAYOUT,
    )
    return fig


# ---------------------------------------------------------------------------
# 1. Portfolio growth chart — all 3 scenarios
# ---------------------------------------------------------------------------

def portfolio_growth_chart(
    growth_tables: Dict[str, pd.DataFrame],
    monthly_sip: float,
    seed_corpus: float,
) -> go.Figure:
    """
    Line chart showing corpus value growth over time for all three scenarios,
    with an 'invested amount' reference line.

    Parameters
    ----------
    growth_tables : Dict mapping scenario label -> growth DataFrame
                    (columns: year | invested_so_far | corpus_value | gains)
    monthly_sip   : Monthly SIP contribution amount.
    seed_corpus   : Initial lump-sum seed corpus.
    """
    fig = go.Figure()

    # Invested amount reference line (same for all scenarios)
    first_table = next(iter(growth_tables.values()))
    fig.add_trace(go.Scatter(
        x=first_table["year"],
        y=first_table["invested_so_far"],
        name="Invested Amount",
        mode="lines",
        line=dict(color=COLOR_INVESTED, width=2, dash="dot"),
        fill=None,
        hovertemplate="Year %{x}<br>Invested: " + CURRENCY_SYMBOL + "%{y:,.0f}<extra></extra>",
    ))

    # Scenario corpus lines
    for label, df in growth_tables.items():
        color = SCENARIO_COLORS.get(label, "#FFFFFF")
        fig.add_trace(go.Scatter(
            x=df["year"],
            y=df["corpus_value"],
            name=label.capitalize(),
            mode="lines+markers",
            line=dict(color=color, width=2.5),
            marker=dict(size=5, color=color),
            hovertemplate=(
                f"<b>{label.capitalize()}</b><br>"
                "Year %{x}<br>"
                "Corpus: " + CURRENCY_SYMBOL + "%{y:,.0f}<extra></extra>"
            ),
        ))

    fig.update_xaxes(title_text="Year", **_AXIS_STYLE)
    fig.update_yaxes(title_text=f"Value ({CURRENCY_SYMBOL})", **_AXIS_STYLE,
                     tickformat=".2s")
    _apply_base_layout(fig, "📈 Portfolio Growth — All Scenarios")
    return fig


# ---------------------------------------------------------------------------
# 2. Allocation donut chart
# ---------------------------------------------------------------------------

def allocation_donut_chart(allocation_dict: Dict[str, float]) -> go.Figure:
    """
    Donut chart for equity / debt / gold allocation.

    Parameters
    ----------
    allocation_dict : {"equity": 65.0, "debt": 25.0, "gold": 10.0}
                      Values should be percentages (0–100).
    """
    labels = [k.capitalize() for k in allocation_dict.keys()]
    values = list(allocation_dict.values())
    colors = [ASSET_COLORS.get(k, "#888888") for k in allocation_dict.keys()]

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker=dict(colors=colors, line=dict(color=COLOR_CARD_BG, width=3)),
        textinfo="label+percent",
        textfont=dict(size=13, color="#FFFFFF"),
        hovertemplate="<b>%{label}</b><br>Allocation: %{value:.1f}%<extra></extra>",
        pull=[0.03, 0.03, 0.03],
    ))

    fig.update_layout(
        annotations=[dict(
            text="Portfolio<br>Mix",
            x=0.5, y=0.5,
            font=dict(size=14, color="#FFFFFF", family=_FONT_FAMILY),
            showarrow=False,
        )],
        showlegend=True,
        **_BASE_LAYOUT,
    )

    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20))

    fig.update_layout(title=dict(
        text="🥧 Asset Allocation",
        font=dict(size=16, color="#FFFFFF"),
        x=0.0, xanchor="left",
    ))
    return fig


# ---------------------------------------------------------------------------
# 3. Inflation erosion chart
# ---------------------------------------------------------------------------

def inflation_erosion_chart(erosion_table: pd.DataFrame) -> go.Figure:
    """
    Dual-axis chart: nominal goal cost (bar) + purchasing power decay (line).

    Parameters
    ----------
    erosion_table : DataFrame from inflation_engine.build_erosion_table()
                    columns: year | nominal_goal | purchasing_power | cumulative_inflation_pct
    """
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Nominal goal bars
    fig.add_trace(go.Bar(
        x=erosion_table["year"],
        y=erosion_table["nominal_goal"],
        name="Inflation-Adjusted Goal Cost",
        marker_color=COLOR_ACCENT,
        opacity=0.75,
        hovertemplate="Year %{x}<br>Cost: " + CURRENCY_SYMBOL + "%{y:,.0f}<extra></extra>",
    ), secondary_y=False)

    # Purchasing power line
    fig.add_trace(go.Scatter(
        x=erosion_table["year"],
        y=erosion_table["purchasing_power"],
        name="Purchasing Power of Today's Money",
        mode="lines+markers",
        line=dict(color="#E74C3C", width=2.5),
        marker=dict(size=5),
        hovertemplate="Year %{x}<br>Purchasing Power: " + CURRENCY_SYMBOL + "%{y:,.0f}<extra></extra>",
    ), secondary_y=True)

    fig.update_xaxes(title_text="Year", **_AXIS_STYLE)
    fig.update_yaxes(title_text=f"Nominal Goal ({CURRENCY_SYMBOL})",
                     secondary_y=False, **_AXIS_STYLE, tickformat=".2s")
    fig.update_yaxes(title_text=f"Purchasing Power ({CURRENCY_SYMBOL})",
                     secondary_y=True, **_AXIS_STYLE, tickformat=".2s")

    _apply_base_layout(fig, "💸 Inflation Erosion — Purchasing Power Over Time")
    return fig


# ---------------------------------------------------------------------------
# 4. Goal gap bar chart
# ---------------------------------------------------------------------------

def goal_gap_bar_chart(gap_data: Dict[str, float], scenario_labels: List[str],
                       maturity_values: List[float]) -> go.Figure:
    """
    Horizontal grouped bar comparing projected corpus (per scenario)
    against the inflation-adjusted goal.

    Parameters
    ----------
    gap_data        : Dict from recommendation_engine.goal_gap()
    scenario_labels : ["Conservative", "Realistic", "Aggressive"]
    maturity_values : Matching list of maturity values per scenario
    """
    adjusted_goal = gap_data["adjusted_goal"]

    fig = go.Figure()

    # Scenario corpus bars
    bar_colors = [
        SCENARIO_COLORS["conservative"],
        SCENARIO_COLORS["realistic"],
        SCENARIO_COLORS["aggressive"],
    ]

    fig.add_trace(go.Bar(
        name="Projected Corpus",
        x=scenario_labels,
        y=maturity_values,
        marker_color=bar_colors,
        text=[fmt_currency(v, short=True) for v in maturity_values],
        textposition="outside",
        textfont=dict(size=11, color="#FFFFFF"),
        hovertemplate="<b>%{x}</b><br>Corpus: " + CURRENCY_SYMBOL + "%{y:,.0f}<extra></extra>",
    ))

    # Inflation-adjusted goal reference line
    fig.add_hline(
        y=adjusted_goal,
        line_dash="dash",
        line_color="#F1C40F",
        line_width=2,
        annotation_text=f"Goal: {fmt_currency(adjusted_goal, short=True)}",
        annotation_position="top right",
        annotation_font=dict(color="#F1C40F", size=12),
    )

    fig.update_xaxes(title_text="Scenario", **_AXIS_STYLE)
    fig.update_yaxes(title_text=f"Corpus Value ({CURRENCY_SYMBOL})", **_AXIS_STYLE,
                     tickformat=".2s")
    _apply_base_layout(fig, "🎯 Projected Corpus vs Inflation-Adjusted Goal")
    return fig


# ---------------------------------------------------------------------------
# 5. Scenario comparison bar
# ---------------------------------------------------------------------------

def scenario_comparison_bar(comparison_df: pd.DataFrame) -> go.Figure:
    """
    Grouped bar: Total Invested vs Maturity Value per scenario.

    Parameters
    ----------
    comparison_df : Raw (numeric) comparison DataFrame from ScenarioBundle.
                    Must have columns: Scenario | Total Invested | Maturity Value
    """
    scenarios = comparison_df["Scenario"].tolist()

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="Total Invested",
        x=scenarios,
        y=comparison_df["Total Invested"],
        marker_color=COLOR_INVESTED,
        hovertemplate="<b>%{x}</b><br>Invested: " + CURRENCY_SYMBOL + "%{y:,.0f}<extra></extra>",
    ))

    fig.add_trace(go.Bar(
        name="Maturity Value",
        x=scenarios,
        y=comparison_df["Maturity Value"],
        marker_color=[
            SCENARIO_COLORS["conservative"],
            SCENARIO_COLORS["realistic"],
            SCENARIO_COLORS["aggressive"],
        ],
        hovertemplate="<b>%{x}</b><br>Maturity: " + CURRENCY_SYMBOL + "%{y:,.0f}<extra></extra>",
    ))

    fig.update_layout(barmode="group")
    fig.update_xaxes(title_text="Scenario", **_AXIS_STYLE)
    fig.update_yaxes(title_text=f"Value ({CURRENCY_SYMBOL})", **_AXIS_STYLE,
                     tickformat=".2s")
    _apply_base_layout(fig, "📊 Scenario Comparison — Invested vs Maturity Value")
    return fig


# ---------------------------------------------------------------------------
# 6. SIP vs returns stacked area chart
# ---------------------------------------------------------------------------

def sip_vs_returns_area_chart(
    growth_table: pd.DataFrame,
    scenario_label: str,
) -> go.Figure:
    """
    Stacked area chart showing cumulative invested amount and unrealised
    gains building over time for the primary (risk-matched) scenario.

    Parameters
    ----------
    growth_table   : Growth DataFrame for a single scenario.
    scenario_label : e.g. "realistic"
    """
    color = SCENARIO_COLORS.get(scenario_label, COLOR_ACCENT)

    fig = go.Figure()

    # Invested amount layer (base)
    fig.add_trace(go.Scatter(
        x=growth_table["year"],
        y=growth_table["invested_so_far"],
        name="Capital Invested",
        mode="lines",
        stackgroup="one",
        line=dict(width=0),
        fillcolor="rgba(149,165,166,0.5)",
        hovertemplate="Year %{x}<br>Invested: " + CURRENCY_SYMBOL + "%{y:,.0f}<extra></extra>",
    ))

    # Gains layer (stacked on top)
    fig.add_trace(go.Scatter(
        x=growth_table["year"],
        y=growth_table["gains"],
        name="Unrealised Gains",
        mode="lines",
        stackgroup="one",
        line=dict(width=0),
        fillcolor=f"rgba{tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (0.65,)}",
        hovertemplate="Year %{x}<br>Gains: " + CURRENCY_SYMBOL + "%{y:,.0f}<extra></extra>",
    ))

    fig.update_xaxes(title_text="Year", **_AXIS_STYLE)
    fig.update_yaxes(title_text=f"Value ({CURRENCY_SYMBOL})", **_AXIS_STYLE,
                     tickformat=".2s")
    _apply_base_layout(
        fig,
        f"📉 Capital Invested vs Gains — {scenario_label.capitalize()} Scenario",
    )
    return fig
