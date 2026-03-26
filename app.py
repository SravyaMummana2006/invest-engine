"""
app.py
------
Intelligent Investment Decision Engine — Streamlit Application

Entry point. Orchestrates all engine modules and renders the full
dashboard: inputs → profile → allocation → inflation → scenarios →
recommendations → charts → export.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

# ── Engine modules ──────────────────────────────────────────────────────────
from modules.profile_engine      import build_profile, InvestorProfile
from modules.allocation_engine   import compute_allocation
from modules.inflation_engine    import analyse_inflation
from modules.scenario_engine     import run_all_scenarios
from modules.recommendation_engine import generate_recommendation

# ── Visuals & utilities ─────────────────────────────────────────────────────
from visuals.charts import (
    portfolio_growth_chart,
    allocation_donut_chart,
    inflation_erosion_chart,
    goal_gap_bar_chart,
    scenario_comparison_bar,
    sip_vs_returns_area_chart,
)
from utils.helpers import (
    fmt_currency,
    fmt_percent,
    fmt_multiple,
    export_recommendation_txt,
    export_growth_table_csv,
    export_summary_json,
)
from utils.constants import (
    APP_NAME, APP_VERSION,
    CURRENCY_SYMBOL,
    GOAL_TYPE_DISPLAY, GOAL_TYPE_ICONS,
    RISK_LEVEL_DISPLAY,
    SCENARIO_COLORS,
    AGE_MIN, AGE_MAX, AGE_DEFAULT,
    INCOME_MIN, INCOME_MAX, INCOME_DEFAULT,
    SAVINGS_MIN, SAVINGS_MAX, SAVINGS_DEFAULT,
    TARGET_YEARS_MIN, TARGET_YEARS_MAX, TARGET_YEARS_DEF,
    GOAL_AMOUNT_MIN, GOAL_AMOUNT_MAX, GOAL_AMOUNT_DEF,
    SAMPLE_PROFILES,
)

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Investment Decision Engine",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Global reset ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    color: #E2E8F0;
}

/* ── App background ── */
.stApp {
    background: #080C14;
    background-image:
        radial-gradient(ellipse 80% 50% at 20% 10%, rgba(0,180,255,0.06) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 80% 90%, rgba(0,255,160,0.04) 0%, transparent 55%);
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0D1117 !important;
    border-right: 1px solid rgba(255,255,255,0.06);
}
[data-testid="stSidebar"] .stSlider > div > div > div {
    background: #00B4FF !important;
}

/* ── Header ── */
.ide-header {
    padding: 2rem 0 1.5rem;
    border-bottom: 1px solid rgba(255,255,255,0.07);
    margin-bottom: 2rem;
}
.ide-header h1 {
    font-family: 'DM Serif Display', serif;
    font-size: 2.6rem;
    font-weight: 400;
    background: linear-gradient(135deg, #FFFFFF 0%, #00B4FF 60%, #00FFA3 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 0.4rem 0;
    line-height: 1.15;
}
.ide-header p {
    color: #64748B;
    font-size: 0.95rem;
    font-weight: 300;
    margin: 0;
    letter-spacing: 0.02em;
}
.ide-version {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: #00B4FF;
    background: rgba(0,180,255,0.1);
    border: 1px solid rgba(0,180,255,0.2);
    padding: 2px 8px;
    border-radius: 4px;
    margin-left: 0.5rem;
    vertical-align: middle;
}

/* ── Metric cards ── */
.metric-card {
    background: linear-gradient(135deg, #111827 0%, #0F172A 100%);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    text-align: center;
    transition: border-color 0.2s;
}
.metric-card:hover { border-color: rgba(0,180,255,0.3); }
.metric-label {
    font-size: 0.72rem;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 500;
    margin-bottom: 0.4rem;
}
.metric-value {
    font-family: 'DM Serif Display', serif;
    font-size: 1.6rem;
    color: #F1F5F9;
    line-height: 1.1;
}
.metric-sub {
    font-size: 0.72rem;
    color: #475569;
    margin-top: 0.2rem;
    font-family: 'JetBrains Mono', monospace;
}

/* ── Section headers ── */
.section-header {
    font-family: 'DM Serif Display', serif;
    font-size: 1.35rem;
    color: #F1F5F9;
    margin: 2rem 0 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid rgba(255,255,255,0.06);
}

/* ── Insight cards ── */
.insight-card {
    background: #0D1117;
    border: 1px solid rgba(0,180,255,0.15);
    border-left: 3px solid #00B4FF;
    border-radius: 8px;
    padding: 0.85rem 1.1rem;
    margin-bottom: 0.6rem;
    font-size: 0.88rem;
    color: #CBD5E1;
    line-height: 1.55;
}

/* ── Warning cards ── */
.warning-card {
    background: #0D1117;
    border: 1px solid rgba(251,191,36,0.2);
    border-left: 3px solid #F59E0B;
    border-radius: 8px;
    padding: 0.85rem 1.1rem;
    margin-bottom: 0.6rem;
    font-size: 0.88rem;
    color: #FDE68A;
    line-height: 1.55;
}

/* ── Success / danger badges ── */
.badge-success {
    display: inline-block;
    background: rgba(34,197,94,0.15);
    color: #4ADE80;
    border: 1px solid rgba(34,197,94,0.3);
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.04em;
}
.badge-danger {
    display: inline-block;
    background: rgba(239,68,68,0.15);
    color: #F87171;
    border: 1px solid rgba(239,68,68,0.3);
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.04em;
}

/* ── Narrative block ── */
.narrative-block {
    background: #0A0F1A;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 1.4rem 1.6rem;
    font-size: 0.9rem;
    color: #94A3B8;
    line-height: 1.75;
    white-space: pre-wrap;
}

/* ── Instrument chips ── */
.chip-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 0.4rem; }
.chip {
    background: rgba(0,180,255,0.08);
    border: 1px solid rgba(0,180,255,0.2);
    color: #7DD3FC;
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.78rem;
    font-weight: 500;
}
.chip-debt {
    background: rgba(99,179,237,0.08);
    border-color: rgba(99,179,237,0.2);
    color: #93C5FD;
}
.chip-gold {
    background: rgba(251,191,36,0.08);
    border-color: rgba(251,191,36,0.2);
    color: #FDE68A;
}

/* ── Divider ── */
.ide-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.07), transparent);
    margin: 2rem 0;
}

/* ── Streamlit overrides ── */
div[data-testid="stSelectbox"] label,
div[data-testid="stSlider"] label,
div[data-testid="stNumberInput"] label {
    font-size: 0.8rem !important;
    color: #94A3B8 !important;
    font-weight: 500 !important;
    letter-spacing: 0.03em !important;
    text-transform: uppercase !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.88rem;
    color: #64748B;
}
.stTabs [aria-selected="true"] {
    color: #00B4FF !important;
}
div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #0369A1, #0EA5E9) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.03em !important;
    padding: 0.5rem 1.5rem !important;
    transition: opacity 0.2s !important;
}
div[data-testid="stButton"] > button:hover { opacity: 0.85 !important; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _metric_card(label: str, value: str, sub: str = "") -> str:
    sub_html = f'<div class="metric-sub">{sub}</div>' if sub else ""
    return f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {sub_html}
    </div>"""


def _load_sample_profiles() -> pd.DataFrame | None:
    try:
        return pd.read_csv(SAMPLE_PROFILES)
    except FileNotFoundError:
        return None


# ── Sidebar — inputs ─────────────────────────────────────────────────────────

def render_sidebar() -> dict:
    with st.sidebar:
        st.markdown("""
        <div style="padding: 1rem 0 1.5rem;">
            <div style="font-family:'DM Serif Display',serif;font-size:1.2rem;color:#F1F5F9;">
                Investor Profile
            </div>
            <div style="font-size:0.75rem;color:#475569;margin-top:0.25rem;">
                Configure your financial parameters
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Sample profile loader ────────────────────────────────────────────
        sample_df = _load_sample_profiles()
        use_sample = False
        selected_sample = None

        if sample_df is not None:
            with st.expander("📂 Load Sample Profile", expanded=False):
                profile_names = ["— Select —"] + sample_df["profile_name"].tolist()
                chosen = st.selectbox("Profile", profile_names, label_visibility="collapsed")
                if chosen != "— Select —":
                    selected_sample = sample_df[sample_df["profile_name"] == chosen].iloc[0]
                    use_sample = True
                    st.caption(f"💡 {selected_sample.get('notes', '')}")

        st.markdown('<div class="ide-divider"></div>', unsafe_allow_html=True)

        # ── Personal details ─────────────────────────────────────────────────
        age = st.slider(
            "Age",
            AGE_MIN, AGE_MAX,
            int(selected_sample["age"]) if use_sample else AGE_DEFAULT,
        )
        monthly_income = st.number_input(
            f"Monthly Income ({CURRENCY_SYMBOL})",
            min_value=float(INCOME_MIN),
            max_value=float(INCOME_MAX),
            value=float(selected_sample["monthly_income"]) if use_sample else float(INCOME_DEFAULT),
            step=5000.0,
            format="%.0f",
        )
        monthly_savings = st.number_input(
            f"Monthly Savings / SIP ({CURRENCY_SYMBOL})",
            min_value=float(SAVINGS_MIN),
            max_value=float(SAVINGS_MAX),
            value=float(selected_sample["monthly_savings"]) if use_sample else float(SAVINGS_DEFAULT),
            step=1000.0,
            format="%.0f",
        )

        st.markdown('<div class="ide-divider"></div>', unsafe_allow_html=True)

        # ── Goal details ─────────────────────────────────────────────────────
        goal_options = list(GOAL_TYPE_DISPLAY.keys())
        goal_labels  = list(GOAL_TYPE_DISPLAY.values())
        default_goal = (
            goal_options.index(selected_sample["investment_goal"])
            if use_sample else goal_options.index("wealth")
        )
        investment_goal = st.selectbox(
            "Investment Goal",
            options=goal_options,
            format_func=lambda x: GOAL_TYPE_DISPLAY[x],
            index=default_goal,
        )

        goal_amount = st.number_input(
            f"Target Goal Amount ({CURRENCY_SYMBOL})",
            min_value=float(GOAL_AMOUNT_MIN),
            max_value=float(GOAL_AMOUNT_MAX),
            value=float(selected_sample["goal_amount"]) if use_sample else float(GOAL_AMOUNT_DEF),
            step=100000.0,
            format="%.0f",
        )

        target_years = st.slider(
            "Investment Horizon (Years)",
            TARGET_YEARS_MIN, TARGET_YEARS_MAX,
            int(selected_sample["target_years"]) if use_sample else TARGET_YEARS_DEF,
        )

        st.markdown('<div class="ide-divider"></div>', unsafe_allow_html=True)

        # ── Risk ─────────────────────────────────────────────────────────────
        risk_options = ["low", "medium", "high"]
        default_risk = (
            risk_options.index(selected_sample["risk_appetite"])
            if use_sample else 1
        )
        risk_appetite = st.select_slider(
            "Risk Appetite",
            options=risk_options,
            value=risk_options[default_risk],
            format_func=lambda x: RISK_LEVEL_DISPLAY[x],
        )

        st.markdown('<div class="ide-divider"></div>', unsafe_allow_html=True)

        analyse_btn = st.button("⚡ Generate Analysis", use_container_width=True)

    return {
        "age":             age,
        "monthly_income":  monthly_income,
        "monthly_savings": monthly_savings,
        "investment_goal": investment_goal,
        "goal_amount":     goal_amount,
        "target_years":    target_years,
        "risk_appetite":   risk_appetite,
        "analyse":         analyse_btn,
    }


# ── Main dashboard ────────────────────────────────────────────────────────────

def render_dashboard(inputs: dict) -> None:

    # ── Header ───────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="ide-header">
        <h1>{APP_NAME} <span class="ide-version">v{APP_VERSION}</span></h1>
        <p>Inflation-aware · Scenario-simulated · Personalised portfolio intelligence</p>
    </div>
    """, unsafe_allow_html=True)

    if not inputs["analyse"]:
        _render_landing()
        return

    # ── Run engines ──────────────────────────────────────────────────────────
    with st.spinner("Running analysis engines…"):
        try:
            profile = build_profile(
                age=inputs["age"],
                monthly_income=inputs["monthly_income"],
                monthly_savings=inputs["monthly_savings"],
                investment_goal=inputs["investment_goal"],
                target_years=inputs["target_years"],
                risk_appetite=inputs["risk_appetite"],
            )
            allocation     = compute_allocation(profile)
            inflation_res  = analyse_inflation(
                present_goal_value=inputs["goal_amount"],
                goal_type=inputs["investment_goal"],
                target_years=inputs["target_years"],
                nominal_return_rate=0.12,
            )
            scenario_bundle = run_all_scenarios(profile)
            report          = generate_recommendation(
                profile, allocation, inflation_res, scenario_bundle
            )
        except ValueError as e:
            st.error(f"⚠️ Input error: {e}")
            return

    # ── KPI row ──────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">📌 Key Metrics</div>', unsafe_allow_html=True)

    primary   = report.primary_scenario
    gap_data  = report.goal_gap_analysis
    gap_color = "#4ADE80" if report.sip_sufficient else "#F87171"
    gap_sign  = "+" if gap_data["gap"] >= 0 else ""

    cols = st.columns(5)
    cards = [
        ("Projected Corpus",   fmt_currency(primary.maturity_value, short=True),
         f"{primary.label.capitalize()} scenario"),
        ("Total Invested",     fmt_currency(primary.total_invested, short=True),
         f"SIP + seed over {profile.target_years}yr"),
        ("Return Multiple",    fmt_multiple(primary.return_multiple),
         f"{primary.annual_return*100:.0f}% p.a."),
        ("Inflation-Adj Goal", fmt_currency(gap_data["adjusted_goal"], short=True),
         f"{inflation_res.inflation_rate*100:.0f}% inflation applied"),
        ("Goal Gap",
         f'<span style="color:{gap_color}">{gap_sign}{fmt_currency(gap_data["gap"], short=True)}</span>',
         f'{gap_sign}{gap_data["gap_pct"]:.1f}% vs target'),
    ]
    for col, (lbl, val, sub) in zip(cols, cards):
        col.markdown(_metric_card(lbl, val, sub), unsafe_allow_html=True)

    st.markdown('<div class="ide-divider"></div>', unsafe_allow_html=True)

    # ── SIP sufficiency banner ───────────────────────────────────────────────
    if report.sip_sufficient:
        st.markdown(
            '<span class="badge-success">✅ SIP SUFFICIENT — Current savings meet the inflation-adjusted goal</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<span class="badge-danger">⚠ SIP SHORTFALL — Increase monthly SIP by '
            f'{fmt_currency(report.sip_top_up_required, short=True)} '
            f'to {fmt_currency(report.recommended_monthly_sip, short=True)}/month</span>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Tabs ─────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Growth Projections",
        "🥧 Allocation",
        "💸 Inflation Analysis",
        "📋 Recommendations",
        "📤 Export",
    ])

    # ════════════════════════════════════════════════════════════════════════
    # TAB 1 — Growth Projections
    # ════════════════════════════════════════════════════════════════════════
    with tab1:
        st.markdown('<div class="section-header">Portfolio Growth — All Scenarios</div>',
                    unsafe_allow_html=True)

        growth_tables = {
            "conservative": scenario_bundle.conservative.growth_table,
            "realistic":    scenario_bundle.realistic.growth_table,
            "aggressive":   scenario_bundle.aggressive.growth_table,
        }
        st.plotly_chart(
            portfolio_growth_chart(growth_tables, profile.monthly_savings, profile.annual_savings),
            use_container_width=True,
        )

        st.markdown('<div class="section-header">Capital Invested vs Gains</div>',
                    unsafe_allow_html=True)
        st.plotly_chart(
            sip_vs_returns_area_chart(primary.growth_table, primary.label),
            use_container_width=True,
        )

        st.markdown('<div class="section-header">Scenario Comparison</div>',
                    unsafe_allow_html=True)
        # Build numeric comparison df
        cmp_df_raw = pd.DataFrame([
            {
                "Scenario":       r.label.capitalize(),
                "Total Invested": r.total_invested,
                "Maturity Value": r.maturity_value,
            }
            for r in scenario_bundle.all_results()
        ])
        st.plotly_chart(scenario_comparison_bar(cmp_df_raw), use_container_width=True)

        # Comparison table
        st.markdown('<div class="section-header">Scenario Summary Table</div>',
                    unsafe_allow_html=True)
        display_df = scenario_bundle.comparison_table().copy()
        for col in ["Total Invested", "Maturity Value", "Total Returns"]:
            display_df[col] = display_df[col].apply(lambda v: fmt_currency(float(v), short=True))
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    # ════════════════════════════════════════════════════════════════════════
    # TAB 2 — Allocation
    # ════════════════════════════════════════════════════════════════════════
    with tab2:
        col_a, col_b = st.columns([1, 1])

        with col_a:
            st.markdown('<div class="section-header">Asset Allocation</div>',
                        unsafe_allow_html=True)
            st.plotly_chart(
                allocation_donut_chart(allocation.as_percentages()),
                use_container_width=True,
            )

        with col_b:
            st.markdown('<div class="section-header">Allocation Rationale</div>',
                        unsafe_allow_html=True)
            st.markdown(
                f'<div class="narrative-block">{allocation.rationale}</div>',
                unsafe_allow_html=True,
            )

            st.markdown('<div class="section-header">Recommended Instruments</div>',
                        unsafe_allow_html=True)

            st.markdown("**Equity**")
            chips = "".join(f'<span class="chip">{i}</span>' for i in report.equity_instruments)
            st.markdown(f'<div class="chip-row">{chips}</div>', unsafe_allow_html=True)

            st.markdown("<br>**Debt**", unsafe_allow_html=True)
            chips = "".join(f'<span class="chip chip-debt">{i}</span>' for i in report.debt_instruments)
            st.markdown(f'<div class="chip-row">{chips}</div>', unsafe_allow_html=True)

            st.markdown("<br>**Gold**", unsafe_allow_html=True)
            chips = "".join(f'<span class="chip chip-gold">{i}</span>' for i in report.gold_instruments)
            st.markdown(f'<div class="chip-row">{chips}</div>', unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    # TAB 3 — Inflation Analysis
    # ════════════════════════════════════════════════════════════════════════
    with tab3:
        st.markdown('<div class="section-header">Purchasing Power Erosion</div>',
                    unsafe_allow_html=True)
        st.plotly_chart(
            inflation_erosion_chart(inflation_res.erosion_table),
            use_container_width=True,
        )

        st.markdown('<div class="section-header">Goal Gap Analysis</div>',
                    unsafe_allow_html=True)
        scenario_labels  = ["Conservative", "Realistic", "Aggressive"]
        maturity_values  = [
            scenario_bundle.conservative.maturity_value,
            scenario_bundle.realistic.maturity_value,
            scenario_bundle.aggressive.maturity_value,
        ]
        st.plotly_chart(
            goal_gap_bar_chart(gap_data, scenario_labels, maturity_values),
            use_container_width=True,
        )

        # Inflation metrics row
        col1, col2, col3 = st.columns(3)
        col1.markdown(_metric_card(
            "Inflation Rate Used",
            fmt_percent(inflation_res.inflation_rate),
            f"{inputs['investment_goal'].capitalize()} goal rate",
        ), unsafe_allow_html=True)
        col2.markdown(_metric_card(
            "Nominal Return",
            fmt_percent(inflation_res.nominal_rate_used),
            "Realistic scenario",
        ), unsafe_allow_html=True)
        col3.markdown(_metric_card(
            "Real Return Rate",
            fmt_percent(inflation_res.real_return_rate),
            "Fisher-adjusted",
        ), unsafe_allow_html=True)

        st.markdown('<div class="section-header">Inflation Erosion Table</div>',
                    unsafe_allow_html=True)
        disp = inflation_res.erosion_table.copy()
        disp["nominal_goal"]     = disp["nominal_goal"].apply(lambda v: fmt_currency(v, short=True))
        disp["purchasing_power"] = disp["purchasing_power"].apply(lambda v: fmt_currency(v, short=True))
        disp.columns = ["Year", "Nominal Goal Cost", "Purchasing Power", "Cumulative Inflation %"]
        st.dataframe(disp, use_container_width=True, hide_index=True)

    # ════════════════════════════════════════════════════════════════════════
    # TAB 4 — Recommendations
    # ════════════════════════════════════════════════════════════════════════
    with tab4:
        st.markdown(
            f'<div class="section-header">Strategy: {report.strategy_label}</div>',
            unsafe_allow_html=True,
        )

        st.markdown('<div class="section-header">Key Insights</div>', unsafe_allow_html=True)
        for insight in report.key_insights:
            st.markdown(f'<div class="insight-card">💡 {insight}</div>',
                        unsafe_allow_html=True)

        st.markdown('<div class="section-header">Risk Warnings</div>', unsafe_allow_html=True)
        for warning in report.risk_warnings:
            st.markdown(f'<div class="warning-card">{warning}</div>',
                        unsafe_allow_html=True)

        st.markdown('<div class="section-header">Full Investment Narrative</div>',
                    unsafe_allow_html=True)
        st.markdown(
            f'<div class="narrative-block">{report.full_narrative}</div>',
            unsafe_allow_html=True,
        )

    # ════════════════════════════════════════════════════════════════════════
    # TAB 5 — Export
    # ════════════════════════════════════════════════════════════════════════
    with tab5:
        st.markdown('<div class="section-header">Export Reports</div>', unsafe_allow_html=True)
        st.markdown(
            "Download generated reports to `outputs/reports/`. "
            "All files are timestamped for audit trail purposes.",
        )

        col_e1, col_e2, col_e3 = st.columns(3)

        with col_e1:
            if st.button("📄 Export Narrative (.txt)", use_container_width=True):
                path = export_recommendation_txt(
                    narrative=report.full_narrative,
                    insights=report.key_insights,
                    warnings=report.risk_warnings,
                    profile_summary=report.profile_summary,
                )
                st.success(f"Saved: `{path}`")

        with col_e2:
            if st.button("📊 Export Growth Table (.csv)", use_container_width=True):
                path = export_growth_table_csv(
                    df=primary.growth_table,
                    scenario_label=primary.label,
                )
                st.success(f"Saved: `{path}`")

        with col_e3:
            if st.button("🗂 Export Summary (.json)", use_container_width=True):
                path = export_summary_json(report.to_dict())
                st.success(f"Saved: `{path}`")

        st.markdown('<div class="ide-divider"></div>', unsafe_allow_html=True)
        st.markdown(
            '<p style="font-size:0.75rem;color:#334155;text-align:center;">'
            'This output is for informational purposes only and does not constitute '
            'financial advice. Consult a SEBI-registered investment advisor before '
            'making investment decisions.'
            '</p>',
            unsafe_allow_html=True,
        )


# ── Landing state (before analysis) ─────────────────────────────────────────

def _render_landing() -> None:
    st.markdown("""
    <div style="max-width:640px;margin:4rem auto;text-align:center;padding:2rem;">
        <div style="font-size:3.5rem;margin-bottom:1rem;">📊</div>
        <div style="font-family:'DM Serif Display',serif;font-size:1.6rem;color:#F1F5F9;margin-bottom:1rem;">
            Configure your profile to begin
        </div>
        <div style="color:#475569;font-size:0.9rem;line-height:1.7;margin-bottom:2rem;">
            Set your age, income, savings, goal, and risk appetite in the sidebar.
            The engine will model inflation, simulate three market scenarios, and
            generate a personalised investment recommendation.
        </div>
        <div style="display:flex;justify-content:center;gap:2rem;flex-wrap:wrap;margin-top:1.5rem;">
            <div style="background:#0D1117;border:1px solid rgba(255,255,255,0.07);border-radius:10px;padding:1rem 1.5rem;min-width:130px;">
                <div style="font-size:1.5rem">🧮</div>
                <div style="font-size:0.78rem;color:#64748B;margin-top:0.4rem;">Inflation<br>Modelling</div>
            </div>
            <div style="background:#0D1117;border:1px solid rgba(255,255,255,0.07);border-radius:10px;padding:1rem 1.5rem;min-width:130px;">
                <div style="font-size:1.5rem">📉</div>
                <div style="font-size:0.78rem;color:#64748B;margin-top:0.4rem;">Scenario<br>Simulation</div>
            </div>
            <div style="background:#0D1117;border:1px solid rgba(255,255,255,0.07);border-radius:10px;padding:1rem 1.5rem;min-width:130px;">
                <div style="font-size:1.5rem">🎯</div>
                <div style="font-size:0.78rem;color:#64748B;margin-top:0.4rem;">Portfolio<br>Allocation</div>
            </div>
            <div style="background:#0D1117;border:1px solid rgba(255,255,255,0.07);border-radius:10px;padding:1rem 1.5rem;min-width:130px;">
                <div style="font-size:1.5rem">💡</div>
                <div style="font-size:0.78rem;color:#64748B;margin-top:0.4rem;">AI-grade<br>Recommendations</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    inputs = render_sidebar()
    render_dashboard(inputs)


if __name__ == "__main__":
    main()
