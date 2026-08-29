"""
NetSage AI — Network Intelligence Dashboard
---------------------------------------------
A Streamlit dashboard for the NetSage AI network troubleshooting system.

This file ONLY renders the dashboard UI. It reads data/ai_results.csv and
never modifies AI diagnosis logic, the rule checker, human review logic,
or any CSV generation. It is fully data-driven: no statistic, category,
or count is hardcoded. Missing columns are hidden gracefully instead of
causing errors.

Run with:
    streamlit run dashboard/app.py
"""

from pathlib import Path

import pandas as pd
import streamlit as st
from PIL import Image

try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


# --------------------------------------------------------------------------
# Paths & Config
# --------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "ai_results.csv"
LOGO_FILE = BASE_DIR / "assets" / "netsage_logo.png"

LOGO_EXISTS = LOGO_FILE.exists()

# Brand palette — cyan / blue / purple, inspired by the NetSage AI logo.
ACCENT = "#3FBFF0"          # primary accent (cyan-blue)
ACCENT_PURPLE = "#8B6BF2"   # secondary accent (violet)
BG_MAIN = "#0A0E17"
BG_CARD = "#111826"
BG_CARD_ALT = "#161F30"
BORDER = "#232E42"
TEXT_MAIN = "#E7ECF5"
TEXT_MUTED = "#8B96AC"

STATUS_COLORS = {
    "accepted": "#3FE0A5",
    "edited": "#E8B339",
    "rejected": "#F0576B",
    "completed": "#3FE0A5",
    "pending": "#8B96AC",
    "likely match": "#3FE0A5",
    "needs human review": "#E8B339",
}

# page_icon must be set BEFORE any other Streamlit call. Use the local logo
# file (as a PIL Image, per Streamlit's supported page_icon types) so the
# browser tab favicon is the actual NetSage AI logo, not an emoji.
_page_icon = Image.open(LOGO_FILE) if LOGO_EXISTS else "🛰️"

st.set_page_config(
    page_title="NetSage AI Dashboard",
    page_icon=_page_icon,
    layout="wide",
    initial_sidebar_state="expanded",
)

if not LOGO_EXISTS:
    st.error(
        f"Logo not found at: {LOGO_FILE}\n\n"
        "Place the NetSage AI logo file at assets/netsage_logo.png "
        "(relative to the project root) and reload the dashboard."
    )
    st.stop()


# --------------------------------------------------------------------------
# Styling
# --------------------------------------------------------------------------

def inject_css() -> None:
    """Inject a minimal, professional dark NOC-style theme."""
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {BG_MAIN};
            color: {TEXT_MAIN};
        }}

        section[data-testid="stSidebar"] {{
            background-color: {BG_CARD};
            border-right: 1px solid {BORDER};
        }}

        [data-testid="stMetric"] {{
            background-color: {BG_CARD};
            border: 1px solid {BORDER};
            border-radius: 10px;
            padding: 14px 16px;
        }}
        [data-testid="stMetricLabel"] {{
            color: {TEXT_MUTED};
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }}
        [data-testid="stMetricValue"] {{
            color: {TEXT_MAIN};
        }}

        .ns-header-wrap {{
            padding: 16px 22px;
            background: linear-gradient(135deg, {BG_CARD} 0%, {BG_CARD_ALT} 100%);
            border: 1px solid {BORDER};
            border-radius: 10px;
            margin-bottom: 8px;
        }}
        .ns-header-title {{
            font-size: 1.55rem;
            font-weight: 800;
            letter-spacing: 0.02em;
            margin: 0;
            line-height: 1.2;
            background: linear-gradient(90deg, {ACCENT} 0%, {ACCENT_PURPLE} 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .ns-header-subtitle {{
            font-size: 0.85rem;
            color: {TEXT_MUTED};
            margin-top: 2px;
        }}
        .ns-header-status {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.78rem;
            color: {ACCENT};
            font-weight: 600;
            letter-spacing: 0.03em;
        }}
        .ns-status-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: {ACCENT};
            display: inline-block;
            box-shadow: 0 0 6px {ACCENT};
        }}
        .ns-case-count {{
            font-size: 0.78rem;
            color: {TEXT_MUTED};
            margin-top: 3px;
        }}
        .ns-divider {{
            border: none;
            border-top: 1px solid {BORDER};
            margin: 6px 0 20px 0;
        }}

        .ns-card {{
            background-color: {BG_CARD};
            border: 1px solid {BORDER};
            border-radius: 10px;
            padding: 16px 18px;
            margin-bottom: 14px;
        }}
        .ns-section-title {{
            font-size: 0.92rem;
            font-weight: 700;
            color: {TEXT_MAIN};
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }}

        .ns-badge {{
            display: inline-block;
            padding: 2px 10px;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.02em;
        }}

        .ns-pipeline-step {{
            flex: 1;
            text-align: center;
            background-color: {BG_CARD_ALT};
            border: 1px solid {BORDER};
            border-radius: 10px;
            padding: 14px 8px;
        }}
        .ns-pipeline-value {{
            font-size: 1.6rem;
            font-weight: 700;
            color: {ACCENT};
        }}
        .ns-pipeline-label {{
            font-size: 0.75rem;
            color: {TEXT_MUTED};
            text-transform: uppercase;
            letter-spacing: 0.03em;
            margin-top: 4px;
        }}

        .ns-code {{
            background-color: #070A10;
            border: 1px solid {BORDER};
            border-radius: 6px;
            padding: 10px 14px;
            font-family: "Courier New", monospace;
            color: {ACCENT};
            font-size: 0.9rem;
        }}

        .ns-muted {{
            color: {TEXT_MUTED};
            font-size: 0.85rem;
        }}

        .ns-sidebar-brand-title {{
            font-size: 1.05rem;
            font-weight: 800;
            letter-spacing: 0.03em;
            color: {TEXT_MAIN};
            line-height: 1.15;
        }}
        .ns-sidebar-brand-subtitle {{
            font-size: 0.74rem;
            color: {TEXT_MUTED};
        }}

        div[data-testid="stDataFrame"] {{
            border: 1px solid {BORDER};
            border-radius: 10px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def badge(value: str) -> str:
    """Render a small colored status badge for a given value."""
    if value is None or str(value).strip() == "":
        return ""
    key = str(value).strip().lower()
    color = STATUS_COLORS.get(key, TEXT_MUTED)
    return (
        f'<span class="ns-badge" style="background-color:{color}22;'
        f'color:{color};border:1px solid {color}55;">{value}</span>'
    )


# --------------------------------------------------------------------------
# Data loading
# --------------------------------------------------------------------------

@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    """Load the AI results CSV. Returns an empty DataFrame if unavailable."""
    if not path.exists():
        return pd.DataFrame()
    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()
    if df.empty:
        return df
    # Normalize whitespace-only cells and NaNs for safe display/filtering.
    df = df.fillna("")
    for column in df.columns:
        if df[column].dtype == object:
            df[column] = df[column].astype(str).str.strip()
    return df


def col(df: pd.DataFrame, name: str):
    """Return the column name if it exists in df, else None."""
    return name if name in df.columns else None


def unique_values(df: pd.DataFrame, column: str) -> list:
    """Return sorted, non-empty unique values for a column, if it exists."""
    if column not in df.columns:
        return []
    values = [v for v in df[column].unique().tolist() if str(v).strip() != ""]
    return sorted(values)


# --------------------------------------------------------------------------
# Metrics
# --------------------------------------------------------------------------

def calculate_metrics(df: pd.DataFrame) -> dict:
    """Compute all KPI values dynamically from the (filtered) dataframe."""
    metrics = {"total": len(df)}

    review_status_col = col(df, "review_status")
    decision_col = col(df, "reviewer_decision")

    completed = 0
    if review_status_col:
        completed = int((df[review_status_col].str.lower() == "completed").sum())
    metrics["completed"] = completed

    for decision in ("accepted", "edited", "rejected"):
        if decision_col:
            metrics[decision] = int((df[decision_col].str.lower() == decision).sum())
        else:
            metrics[decision] = 0

    if completed > 0:
        metrics["agreement_rate"] = round((metrics["accepted"] / completed) * 100, 1)
    else:
        metrics["agreement_rate"] = 0.0

    return metrics


# --------------------------------------------------------------------------
# Sidebar
# --------------------------------------------------------------------------

def render_sidebar(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """Render sidebar navigation + filters. Returns (filtered_df, page)."""
    with st.sidebar:
        brand_cols = st.columns([1, 3])
        with brand_cols[0]:
            st.image(str(LOGO_FILE), width=44)
        with brand_cols[1]:
            st.markdown(
                f"""
                <div style="padding-top:2px;">
                    <div class="ns-sidebar-brand-title">NetSage AI</div>
                    <div class="ns-sidebar-brand-subtitle">Network Intelligence</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        page = st.radio(
            "Navigation",
            ["Overview", "Case Explorer", "Human Review"],
            label_visibility="collapsed",
        )

        st.markdown("---")
        st.markdown("**Filters**")

        if df.empty:
            st.caption("No data loaded.")
            return df, page

        filtered = df.copy()

        issue_col = col(df, "issue_type")
        if issue_col:
            options = unique_values(df, issue_col)
            selected = st.multiselect("Issue Type", options, default=[])
            if selected:
                filtered = filtered[filtered[issue_col].isin(selected)]

        severity_col = col(df, "severity")
        if severity_col:
            options = unique_values(df, severity_col)
            selected = st.multiselect("Severity", options, default=[])
            if selected:
                filtered = filtered[filtered[severity_col].isin(selected)]

        review_status_col = col(df, "review_status")
        if review_status_col:
            options = unique_values(df, review_status_col)
            selected = st.multiselect("Review Status", options, default=[])
            if selected:
                filtered = filtered[filtered[review_status_col].isin(selected)]

        decision_col = col(df, "reviewer_decision")
        if decision_col:
            options = unique_values(df, decision_col)
            selected = st.multiselect("Reviewer Decision", options, default=[])
            if selected:
                filtered = filtered[filtered[decision_col].isin(selected)]

        if st.button("Reset Filters", use_container_width=True):
            st.rerun()

        return filtered, page


# --------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------

def render_header(total_cases: int) -> None:
    """
    Header layout: [LOGO]  NetSage AI
                          Network Troubleshooting & AI Diagnosis Dashboard
    followed by a subtle divider. Logo is rendered with st.image() from the
    local project asset — no base64, no remote URLs.
    """
    st.markdown('<div class="ns-header-wrap">', unsafe_allow_html=True)

    logo_col, title_col, status_col = st.columns([0.6, 5, 2])

    with logo_col:
        st.image(str(LOGO_FILE), width=56)

    with title_col:
        st.markdown(
            f"""
            <div class="ns-header-title">NetSage AI</div>
            <div class="ns-header-subtitle">Network Troubleshooting &amp; AI Diagnosis Dashboard</div>
            <div class="ns-case-count">{total_cases} case(s) in current view</div>
            """,
            unsafe_allow_html=True,
        )

    with status_col:
        st.markdown(
            f"""
            <div style="display:flex; height:100%; align-items:center; justify-content:flex-end;">
                <div class="ns-header-status">
                    <span class="ns-status-dot"></span> SYSTEM OPERATIONAL
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<hr class="ns-divider" />', unsafe_allow_html=True)


# --------------------------------------------------------------------------
# KPI cards
# --------------------------------------------------------------------------

def render_kpi_cards(metrics: dict) -> None:
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total AI Results", metrics["total"])
    c2.metric("Reviews Completed", metrics["completed"])
    c3.metric("Accepted", metrics["accepted"])
    c4.metric("Edited", metrics["edited"])
    c5.metric("Rejected", metrics["rejected"])
    c6.metric("AI Agreement Rate", f"{metrics['agreement_rate']}%")


# --------------------------------------------------------------------------
# Charts
# --------------------------------------------------------------------------

def render_charts(df: pd.DataFrame) -> None:
    left, right = st.columns(2)

    issue_col = col(df, "issue_type")
    severity_col = col(df, "severity")

    with left:
        st.markdown('<div class="ns-card">', unsafe_allow_html=True)
        st.markdown('<div class="ns-section-title">Issue Type Distribution</div>', unsafe_allow_html=True)
        if issue_col and not df.empty:
            counts = df[df[issue_col] != ""][issue_col].value_counts().sort_values()
            if not counts.empty:
                if PLOTLY_AVAILABLE:
                    fig = go.Figure(
                        go.Bar(
                            x=counts.values,
                            y=counts.index,
                            orientation="h",
                            marker_color=ACCENT,
                        )
                    )
                    fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font_color=TEXT_MAIN,
                        margin=dict(l=10, r=10, t=10, b=10),
                        height=300,
                        xaxis=dict(gridcolor=BORDER),
                        yaxis=dict(gridcolor=BORDER),
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.bar_chart(counts)
            else:
                st.markdown('<span class="ns-muted">No issue type data available.</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="ns-muted">Issue type field not present in data.</span>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="ns-card">', unsafe_allow_html=True)
        st.markdown('<div class="ns-section-title">Severity Distribution</div>', unsafe_allow_html=True)
        if severity_col and not df.empty:
            counts = df[df[severity_col] != ""][severity_col].value_counts()
            if not counts.empty:
                if PLOTLY_AVAILABLE:
                    fig = go.Figure(
                        go.Pie(
                            labels=counts.index,
                            values=counts.values,
                            hole=0.55,
                            marker=dict(colors=[ACCENT, ACCENT_PURPLE, "#F0576B", "#3FE0A5", "#8B96AC"]),
                        )
                    )
                    fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        font_color=TEXT_MAIN,
                        margin=dict(l=10, r=10, t=10, b=10),
                        height=300,
                        showlegend=True,
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.bar_chart(counts)
            else:
                st.markdown('<span class="ns-muted">No severity data available.</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="ns-muted">Severity field not present in data.</span>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


def render_ai_vs_human(df: pd.DataFrame, metrics: dict) -> None:
    decision_col = col(df, "reviewer_decision")

    st.markdown('<div class="ns-card">', unsafe_allow_html=True)
    st.markdown('<div class="ns-section-title">AI vs Human Review</div>', unsafe_allow_html=True)

    if not decision_col or df.empty:
        st.markdown('<span class="ns-muted">Reviewer decision field not present in data.</span>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        return

    total_decided = metrics["accepted"] + metrics["edited"] + metrics["rejected"]
    chart_col, stats_col = st.columns([2, 1])

    with chart_col:
        labels = ["Accepted", "Edited", "Rejected"]
        values = [metrics["accepted"], metrics["edited"], metrics["rejected"]]
        if total_decided > 0 and PLOTLY_AVAILABLE:
            fig = go.Figure(
                go.Bar(
                    x=labels,
                    y=values,
                    marker_color=["#3FE0A5", "#E8B339", "#F0576B"],
                )
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color=TEXT_MAIN,
                margin=dict(l=10, r=10, t=10, b=10),
                height=260,
                yaxis=dict(gridcolor=BORDER),
            )
            st.plotly_chart(fig, use_container_width=True)
        elif total_decided > 0:
            st.bar_chart(pd.Series(values, index=labels))
        else:
            st.markdown('<span class="ns-muted">No reviewer decisions recorded yet.</span>', unsafe_allow_html=True)

    with stats_col:
        for label, key in (("Accepted", "accepted"), ("Edited", "edited"), ("Rejected", "rejected")):
            pct = round((metrics[key] / total_decided) * 100, 1) if total_decided > 0 else 0.0
            st.markdown(
                f"""
                <div style="display:flex; justify-content:space-between; padding:6px 0;
                            border-bottom:1px solid {BORDER};">
                    <span>{label}</span>
                    <span style="color:{TEXT_MUTED};">{pct}%</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown(
            f"""
            <div style="margin-top:14px; text-align:center;">
                <div style="font-size:1.8rem; font-weight:800; color:{ACCENT};">
                    {metrics['agreement_rate']}%
                </div>
                <div class="ns-muted">Overall Agreement Rate</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


def render_pipeline(metrics: dict) -> None:
    st.markdown('<div class="ns-card">', unsafe_allow_html=True)
    st.markdown('<div class="ns-section-title">Review Pipeline</div>', unsafe_allow_html=True)

    steps = [
        ("AI Diagnoses", metrics["total"]),
        ("Reviews Completed", metrics["completed"]),
        ("Accepted", metrics["accepted"]),
        ("Edited", metrics["edited"]),
        ("Rejected", metrics["rejected"]),
    ]

    cols = st.columns(len(steps) * 2 - 1)
    idx = 0
    for i, (label, value) in enumerate(steps):
        with cols[idx]:
            st.markdown(
                f"""
                <div class="ns-pipeline-step">
                    <div class="ns-pipeline-value">{value}</div>
                    <div class="ns-pipeline-label">{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        idx += 1
        if i < len(steps) - 1:
            with cols[idx]:
                st.markdown(
                    '<div style="text-align:center; padding-top:22px; color:%s;">&rarr;</div>' % TEXT_MUTED,
                    unsafe_allow_html=True,
                )
            idx += 1

    st.markdown("</div>", unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Case Explorer
# --------------------------------------------------------------------------

DISPLAY_COLUMN_MAP = {
    "case_id": "Case ID",
    "issue_type": "Issue Type",
    "severity": "Severity",
    "agreement": "Agreement",
    "review_status": "Review Status",
    "reviewer_decision": "Reviewer Decision",
    "confidence": "Confidence",
}


def render_case_explorer(df: pd.DataFrame) -> None:
    st.markdown('<div class="ns-section-title" style="font-size:1.1rem; margin-bottom:14px;">Case Explorer</div>', unsafe_allow_html=True)

    if df.empty:
        st.markdown('<span class="ns-muted">No diagnosis data available.</span>', unsafe_allow_html=True)
        return

    case_id_col = col(df, "case_id")

    search_term = st.text_input("Search Case ID", placeholder="e.g. CASE-014")
    view = df.copy()
    if search_term and case_id_col:
        view = view[view[case_id_col].str.contains(search_term, case=False, na=False)]

    display_cols = [c for c in DISPLAY_COLUMN_MAP if c in view.columns]
    if not display_cols:
        st.markdown('<span class="ns-muted">No displayable columns found.</span>', unsafe_allow_html=True)
        return

    table = view[display_cols].rename(columns=DISPLAY_COLUMN_MAP)
    st.dataframe(table, use_container_width=True, hide_index=True, height=380)
    st.caption(f"Showing {len(table)} of {len(df)} case(s).")


# --------------------------------------------------------------------------
# Case Details
# --------------------------------------------------------------------------

def render_case_details(df: pd.DataFrame) -> None:
    st.markdown('<div class="ns-section-title" style="font-size:1.1rem; margin-bottom:14px;">Case Details</div>', unsafe_allow_html=True)

    if df.empty:
        st.markdown('<span class="ns-muted">No diagnosis data available.</span>', unsafe_allow_html=True)
        return

    case_id_col = col(df, "case_id")
    if not case_id_col:
        st.markdown('<span class="ns-muted">case_id field not present in data.</span>', unsafe_allow_html=True)
        return

    case_ids = df[case_id_col].tolist()
    selected_id = st.selectbox("Select Case", case_ids)
    row = df[df[case_id_col] == selected_id].iloc[0]

    def field(name: str):
        return row[name] if name in df.columns and str(row[name]).strip() != "" else None

    # Ticket-style header: Case ID, Issue Type, Severity badge.
    case_issue = field("issue_type")
    case_severity = field("severity")
    header_bits = " &nbsp;·&nbsp; ".join(
        b for b in [
            f'<span style="color:{TEXT_MUTED};">{case_issue}</span>' if case_issue else "",
            badge(case_severity) if case_severity else "",
        ] if b
    )
    st.markdown(
        f"""
        <div class="ns-card" style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap;">
            <div style="font-size:1.15rem; font-weight:800; color:{TEXT_MAIN};">CASE {selected_id}</div>
            <div>{header_bits}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    info_col1, info_col2 = st.columns(2)

    with info_col1:
        st.markdown('<div class="ns-card">', unsafe_allow_html=True)
        st.markdown('<div class="ns-section-title">Case Information</div>', unsafe_allow_html=True)
        info_fields = [
            ("Case ID", field("case_id")),
            ("Issue Type", field("issue_type")),
            ("Severity", field("severity")),
            ("Confidence", field("confidence")),
            ("OSI Layer", field("osi_layer")),
            ("Concept", field("concept")),
        ]
        any_shown = False
        for label, value in info_fields:
            if value is not None:
                any_shown = True
                st.markdown(f"**{label}:** {value}")
        if not any_shown:
            st.markdown('<span class="ns-muted">No case information fields available.</span>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        root_cause = field("root_cause")
        if root_cause is not None:
            st.markdown('<div class="ns-card">', unsafe_allow_html=True)
            st.markdown('<div class="ns-section-title">AI Diagnosis</div>', unsafe_allow_html=True)
            st.markdown(f"**Root Cause:** {root_cause}")
            st.markdown("</div>", unsafe_allow_html=True)

        evidence = field("evidence")
        if evidence is not None:
            st.markdown('<div class="ns-card">', unsafe_allow_html=True)
            st.markdown('<div class="ns-section-title">Evidence</div>', unsafe_allow_html=True)
            st.markdown(evidence)
            st.markdown("</div>", unsafe_allow_html=True)

        next_command = field("next_command")
        if next_command is not None:
            st.markdown('<div class="ns-card">', unsafe_allow_html=True)
            st.markdown('<div class="ns-section-title">Next Command</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="ns-code">{next_command}</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        fix = field("fix") or field("fix_steps")
        if fix is not None:
            st.markdown('<div class="ns-card">', unsafe_allow_html=True)
            st.markdown('<div class="ns-section-title">Recommended Fix</div>', unsafe_allow_html=True)
            st.markdown(fix)
            st.markdown("</div>", unsafe_allow_html=True)

    with info_col2:
        review_status = field("review_status")
        reviewer_decision = field("reviewer_decision")
        reviewer_notes = field("reviewer_notes")

        if review_status is not None or reviewer_decision is not None or reviewer_notes is not None:
            st.markdown('<div class="ns-card">', unsafe_allow_html=True)
            st.markdown('<div class="ns-section-title">Human Review</div>', unsafe_allow_html=True)
            if review_status is not None:
                st.markdown(f"**Review Status:** {badge(review_status)}", unsafe_allow_html=True)
            if reviewer_decision is not None:
                st.markdown(f"**Decision:** {badge(reviewer_decision)}", unsafe_allow_html=True)
            if reviewer_notes is not None:
                st.markdown(f"**Reviewer Notes:** {reviewer_notes}")
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown('<div class="ns-card">', unsafe_allow_html=True)
            st.markdown('<div class="ns-section-title">Human Review</div>', unsafe_allow_html=True)
            st.markdown('<span class="ns-muted">No human review data available for this case.</span>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------

def render_overview(df: pd.DataFrame) -> None:
    metrics = calculate_metrics(df)
    render_kpi_cards(metrics)
    st.write("")
    render_charts(df)
    st.write("")
    row_col1, row_col2 = st.columns(2)
    with row_col1:
        render_ai_vs_human(df, metrics)
    with row_col2:
        render_pipeline(metrics)


def render_human_review_page(df: pd.DataFrame) -> None:
    metrics = calculate_metrics(df)
    render_ai_vs_human(df, metrics)
    st.write("")
    render_case_explorer(df)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main() -> None:
    inject_css()

    if not DATA_FILE.exists():
        render_header(0)
        st.markdown(
            f"""
            <div class="ns-card">
                <div class="ns-section-title">Data Source Unavailable</div>
                <span class="ns-muted">
                    Could not locate <code>data/ai_results.csv</code>. Run the AI diagnosis
                    pipeline to generate results, then reload this dashboard.
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    df = load_data(DATA_FILE)

    filtered_df, page = render_sidebar(df)

    render_header(len(filtered_df))

    if df.empty:
        st.markdown(
            '<div class="ns-card"><span class="ns-muted">No diagnosis data available.</span></div>',
            unsafe_allow_html=True,
        )
        return

    if page == "Overview":
        render_overview(filtered_df)
    elif page == "Case Explorer":
        render_case_explorer(filtered_df)
        st.write("")
        render_case_details(filtered_df)
    elif page == "Human Review":
        render_human_review_page(filtered_df)


if __name__ == "__main__":
    main()
