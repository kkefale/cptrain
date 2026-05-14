"""
Cape Town Rainfall Atlas
A polished, iOS Weather-inspired Streamlit dashboard for Cape Town rainfall data.
"""

__version__ = "1.0.0"

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# ── Auto-setup database on first run ────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DB_PATH  = BASE_DIR / "rainfall.db"

if not DB_PATH.exists():
    from setup_db import setup_database
    setup_database()

# ─── STATION REGISTRY ───────────────────────────────────────────────────────
STATIONS = [
    ("WEMMERSHOEK",  "Wemmershoek No.1 Dam",  "Wemmershoek",  "Franschhoek Mtns",   -33.891, 19.099),
    ("STEENBRAS",    "Steenbras No.1",          "Steenbras",    "Gordon's Bay",       -34.123, 18.849),
    ("VOELVLEI",     "Voëlvlei",                "Voëlvlei",     "Wellington",         -33.682, 19.034),
    ("THEEWATERS",   "Theewaterskloof",         "Theewaters",   "Overberg",           -34.055, 19.129),
    ("WOODHEAD",     "Woodhead Dam",            "Woodhead",     "Table Mountain",     -33.995, 18.420),
    ("NEWLANDS",     "Newlands",                "Newlands",     "Southern Suburbs",   -33.968, 18.463),
    ("WYNBERG",      "Wynberg",                 "Wynberg",      "Southern Suburbs",   -34.013, 18.472),
    ("CONSTANTIA",   "Constantia Nek",          "Const. Nek",   "Constantiaberg",     -34.027, 18.399),
    ("PLATTEKLOOF",  "Plattekloof",             "Plattekloof",  "Northern Suburbs",   -33.886, 18.578),
    ("BLKHTH_UPPER", "Blackheath Upper",        "Blkhth Upper", "Helderberg",         -33.924, 18.676),
    ("BLKHTH_LOWER", "Blackheath Lower",        "Blkhth Lower", "Helderberg",         -33.937, 18.683),
    ("GLEN_GARRY",   "Glen Garry",              "Glen Garry",   "Hout Bay Mtns",      -33.963, 18.445),
    ("TYGERBERG",    "Tygerberg",               "Tygerberg",    "Northern Suburbs",   -33.865, 18.625),
    ("FAURE",        "Faure",                   "Faure",        "Helderberg",         -34.052, 18.836),
    ("BROOKLANDS",   "Brooklands",              "Brooklands",   "Southern Suburbs",   -34.018, 18.487),
]

STATION_KEYS   = [s[0] for s in STATIONS]
STATION_NAME   = {s[0]: s[1] for s in STATIONS}
STATION_SHORT  = {s[0]: s[2] for s in STATIONS}
STATION_REGION = {s[0]: s[3] for s in STATIONS}
STATION_LAT    = {s[0]: s[4] for s in STATIONS}
STATION_LON    = {s[0]: s[5] for s in STATIONS}

DROUGHT_YEARS = [2015, 2016, 2017, 2018]
CAPE_TOWN_CENTER = (-33.93, 18.60)

MONTHS_SHORT = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

# Colour palette
C = {
    "bg":       "#07091A",
    "card":     "rgba(255,255,255,0.06)",
    "border":   "rgba(255,255,255,0.10)",
    "primary":  "#38BDF8",
    "secondary":"#818CF8",
    "accent":   "#06B6D4",
    "wet":      "#10B981",
    "dry":      "#F59E0B",
    "danger":   "#EF4444",
    "text":     "#F0F9FF",
    "sub":      "#94A3B8",
    "muted":    "#475569",
}

RAIN_SCALE = [
    [0.0,  "#07091A"],
    [0.05, "#0C1E3C"],
    [0.2,  "#0369A1"],
    [0.4,  "#0EA5E9"],
    [0.65, "#38BDF8"],
    [0.85, "#7DD3FC"],
    [1.0,  "#E0F2FE"],
]

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Cape Town Rainfall Atlas",
    page_icon="🌧️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── CSS ────────────────────────────────────────────────────────────────────
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"], * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* ── Background ── */
    .stApp {
        background: linear-gradient(170deg, #07091A 0%, #0B1628 35%, #0C1A2E 65%, #07091A 100%) !important;
        background-attachment: fixed !important;
    }
    .stApp > header { background: transparent !important; }

    /* ── Hide chrome ── */
    #MainMenu, footer, header { visibility: hidden; }
    .stDeployButton { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }

    /* ── Main container ── */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        max-width: 1400px !important;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px !important;
        background: rgba(255,255,255,0.05) !important;
        border-radius: 14px !important;
        padding: 4px !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        width: fit-content !important;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px !important;
        padding: 8px 22px !important;
        color: rgba(255,255,255,0.5) !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        border: none !important;
        background: transparent !important;
        transition: all 0.2s ease !important;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(56,189,248,0.18) !important;
        color: #38BDF8 !important;
        border: 1px solid rgba(56,189,248,0.3) !important;
    }
    .stTabs [data-baseweb="tab-highlight"] { display: none !important; }
    .stTabs [data-baseweb="tab-border"] { display: none !important; }

    /* ── Metrics ── */
    [data-testid="stMetric"] {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.10) !important;
        border-radius: 18px !important;
        padding: 20px 24px !important;
        transition: transform 0.2s, box-shadow 0.2s !important;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4) !important;
    }
    [data-testid="stMetricValue"] {
        color: #F0F9FF !important;
        font-size: 2.0rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
    }
    [data-testid="stMetricLabel"] {
        color: #94A3B8 !important;
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
    }
    [data-testid="stMetricDelta"] {
        font-size: 0.85rem !important;
        font-weight: 500 !important;
    }

    /* ── Selectbox ── */
    .stSelectbox > label { color: #94A3B8 !important; font-size: 0.8rem !important; font-weight: 600 !important; text-transform: uppercase !important; letter-spacing: 0.06em !important; }
    .stSelectbox [data-baseweb="select"] > div:first-child {
        background: rgba(255,255,255,0.07) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 12px !important;
        color: white !important;
    }

    /* ── Multiselect ── */
    .stMultiSelect > label { color: #94A3B8 !important; font-size: 0.8rem !important; font-weight: 600 !important; text-transform: uppercase !important; letter-spacing: 0.06em !important; }
    .stMultiSelect [data-baseweb="select"] > div {
        background: rgba(255,255,255,0.07) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 12px !important;
    }

    /* ── Slider ── */
    .stSlider > label { color: #94A3B8 !important; font-size: 0.8rem !important; font-weight: 600 !important; text-transform: uppercase !important; letter-spacing: 0.06em !important; }

    /* ── Divider ── */
    hr { border: none !important; border-top: 1px solid rgba(255,255,255,0.07) !important; margin: 1.5rem 0 !important; }

    /* ── Headings ── */
    h1 { color: #F0F9FF !important; font-size: 2.2rem !important; font-weight: 800 !important; letter-spacing: -0.03em !important; }
    h2 { color: #E2E8F0 !important; font-size: 1.4rem !important; font-weight: 700 !important; letter-spacing: -0.02em !important; }
    h3 { color: #CBD5E1 !important; font-size: 1.1rem !important; font-weight: 600 !important; }
    p  { color: #94A3B8 !important; }

    /* ── Dataframe ── */
    [data-testid="stDataFrame"] { border-radius: 14px !important; overflow: hidden !important; }

    /* ── Custom card component ── */
    .rain-card {
        background: rgba(255,255,255,0.055);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 20px;
        padding: 18px 20px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        height: 100%;
    }
    .rain-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.5);
        border-color: rgba(56,189,248,0.25);
    }
    .rain-card .region {
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.10em;
        color: #64748B;
        margin-bottom: 4px;
    }
    .rain-card .station-name {
        font-size: 15px;
        font-weight: 600;
        color: #CBD5E1;
        margin-bottom: 12px;
    }
    .rain-card .rainfall-value {
        font-size: 36px;
        font-weight: 800;
        letter-spacing: -0.03em;
        color: #F0F9FF;
        line-height: 1;
        margin-bottom: 4px;
    }
    .rain-card .rainfall-unit {
        font-size: 14px;
        font-weight: 500;
        color: #94A3B8;
        margin-bottom: 10px;
    }
    .rain-card .badge {
        display: inline-block;
        font-size: 12px;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 20px;
    }
    .rain-card .badge.above {
        background: rgba(16,185,129,0.15);
        color: #10B981;
        border: 1px solid rgba(16,185,129,0.3);
    }
    .rain-card .badge.below {
        background: rgba(245,158,11,0.15);
        color: #F59E0B;
        border: 1px solid rgba(245,158,11,0.3);
    }
    .rain-card .badge.neutral {
        background: rgba(148,163,184,0.15);
        color: #94A3B8;
        border: 1px solid rgba(148,163,184,0.3);
    }
    .rain-card .bar-track {
        background: rgba(255,255,255,0.07);
        border-radius: 6px;
        height: 4px;
        margin-top: 12px;
        overflow: hidden;
    }
    .rain-card .bar-fill {
        height: 4px;
        border-radius: 6px;
        background: linear-gradient(90deg, #0EA5E9, #818CF8);
    }

    /* ── Hero section ── */
    .hero-section {
        background: linear-gradient(135deg, rgba(14,165,233,0.12) 0%, rgba(129,140,248,0.08) 100%);
        border: 1px solid rgba(56,189,248,0.15);
        border-radius: 28px;
        padding: 36px 40px;
        margin-bottom: 28px;
        position: relative;
        overflow: hidden;
    }
    .hero-section::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -10%;
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(56,189,248,0.08) 0%, transparent 70%);
        border-radius: 50%;
    }
    .hero-title {
        font-size: 42px;
        font-weight: 800;
        color: #F0F9FF;
        letter-spacing: -0.04em;
        line-height: 1.1;
        margin: 0;
    }
    .hero-subtitle {
        font-size: 16px;
        color: #64748B;
        margin-top: 6px;
        font-weight: 400;
    }
    .hero-date {
        font-size: 14px;
        font-weight: 600;
        color: #38BDF8;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 8px;
    }

    /* ── Section headers ── */
    .section-header {
        font-size: 13px;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.10em;
        margin: 24px 0 14px 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .section-header::after {
        content: '';
        flex: 1;
        height: 1px;
        background: rgba(255,255,255,0.07);
    }

    /* ── Info box ── */
    .info-box {
        background: rgba(56,189,248,0.08);
        border: 1px solid rgba(56,189,248,0.2);
        border-radius: 14px;
        padding: 14px 18px;
        color: #7DD3FC;
        font-size: 13px;
        font-weight: 500;
        margin: 12px 0;
    }

    /* ── Drought banner ── */
    .drought-banner {
        background: rgba(245,158,11,0.10);
        border: 1px solid rgba(245,158,11,0.25);
        border-radius: 14px;
        padding: 14px 18px;
        color: #FCD34D;
        font-size: 13px;
        font-weight: 500;
        margin: 12px 0;
    }

    /* ── Narrative editorial blocks ── */
    .narrative {
        background: rgba(15,23,42,0.65);
        border-left: 3px solid rgba(56,189,248,0.45);
        border-radius: 0 20px 20px 0;
        padding: 20px 28px;
        margin: 18px 0 28px 0;
        color: #94A3B8;
        font-size: 15px;
        line-height: 1.85;
        font-weight: 400;
        letter-spacing: 0.015em;
        font-style: italic;
    }
    .narrative b, .narrative strong { color: #E2E8F0; font-style: normal; }
    .narrative em { color: #CBD5E1; font-weight: 600; }
    .narrative .hi  { color: #38BDF8; font-style: normal; font-weight: 700; }
    .narrative .amber { color: #F59E0B; font-style: normal; font-weight: 600; }
    .narrative .green { color: #34D399; font-style: normal; font-weight: 600; }

    /* ── Scrollable table wrapper ── */
    .table-wrapper { max-height: 420px; overflow-y: auto; }
    .table-wrapper::-webkit-scrollbar { width: 6px; }
    .table-wrapper::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 6px; }
    </style>
    """, unsafe_allow_html=True)


# ─── DB HELPERS ─────────────────────────────────────────────────────────────
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


@st.cache_data(ttl=3600, show_spinner=False)
def load_all_daily() -> pd.DataFrame:
    with get_conn() as conn:
        df = pd.read_sql(
            "SELECT station_key, date, rainfall_mm FROM rainfall ORDER BY date",
            conn, parse_dates=["date"],
        )
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def load_monthly() -> pd.DataFrame:
    """Monthly totals per station per year-month."""
    df = load_all_daily().copy()
    df["year"]  = df["date"].dt.year
    df["month"] = df["date"].dt.month
    monthly = (
        df.groupby(["station_key", "year", "month"])
          .agg(total_mm=("rainfall_mm", "sum"), reading_days=("rainfall_mm", "count"))
          .reset_index()
    )
    monthly["ym"] = pd.to_datetime(monthly[["year","month"]].assign(day=1))
    return monthly


@st.cache_data(ttl=3600, show_spinner=False)
def load_climatology() -> pd.DataFrame:
    """Historical monthly averages (exclude most recent partial year)."""
    monthly = load_monthly()
    current_year = datetime.now().year
    hist = monthly[monthly["year"] < current_year]
    clim = (
        hist.groupby(["station_key", "month"])
            .agg(avg_mm=("total_mm", "mean"), years_count=("year", "count"))
            .reset_index()
    )
    return clim


@st.cache_data(ttl=3600, show_spinner=False)
def load_annual() -> pd.DataFrame:
    """Annual totals per station."""
    monthly = load_monthly()
    annual = (
        monthly.groupby(["station_key", "year"])
               .agg(total_mm=("total_mm", "sum"), reading_days=("reading_days","sum"))
               .reset_index()
    )
    return annual


@st.cache_data(ttl=3600, show_spinner=False)
def load_top_days(station_key: str, n: int = 15) -> pd.DataFrame:
    with get_conn() as conn:
        df = pd.read_sql(
            "SELECT date, rainfall_mm FROM rainfall WHERE station_key=? "
            "ORDER BY rainfall_mm DESC LIMIT ?",
            conn, params=(station_key, n), parse_dates=["date"],
        )
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def load_station_meta() -> pd.DataFrame:
    with get_conn() as conn:
        df = pd.read_sql("SELECT * FROM stations", conn)
    return df


# ─── CHART HELPERS ──────────────────────────────────────────────────────────
def dark_fig(fig: go.Figure, height: int = 380) -> go.Figure:
    """Apply consistent dark iOS styling to any Plotly figure."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Helvetica Neue, sans-serif", color="#94A3B8", size=12),
        height=height,
        margin=dict(l=0, r=0, t=28, b=0),
        legend=dict(
            bgcolor="rgba(255,255,255,0.04)",
            bordercolor="rgba(255,255,255,0.1)",
            borderwidth=1,
            font=dict(size=11, color="#94A3B8"),
        ),
        xaxis=dict(
            gridcolor="rgba(255,255,255,0.05)",
            linecolor="rgba(255,255,255,0.08)",
            tickfont=dict(color="#475569", size=11),
            showgrid=True,
            zeroline=False,
        ),
        yaxis=dict(
            gridcolor="rgba(255,255,255,0.05)",
            linecolor="rgba(255,255,255,0.08)",
            tickfont=dict(color="#475569", size=11),
            showgrid=True,
            zeroline=False,
        ),
    )
    return fig


PALETTE = [
    "#38BDF8","#818CF8","#34D399","#F472B6","#FBBF24",
    "#A78BFA","#6EE7B7","#F97316","#60A5FA","#E879F9",
    "#4ADE80","#FB923C","#94A3B8","#2DD4BF","#FCD34D",
]


def section(icon: str, title: str):
    st.markdown(
        f'<div class="section-header">{icon}&nbsp;{title}</div>',
        unsafe_allow_html=True,
    )


def narrate(html: str):
    """Render an editorial narrative block between charts."""
    st.markdown(f'<div class="narrative">{html}</div>', unsafe_allow_html=True)


# ─── EXTRA CACHED DATA ──────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def load_daily_cumulative(station_key: str) -> dict[int, np.ndarray]:
    """Per-year day-of-year cumulative rainfall for spaghetti chart."""
    daily = load_all_daily()
    st_d  = daily[daily["station_key"] == station_key].copy()
    st_d["year"] = st_d["date"].dt.year
    st_d["doy"]  = st_d["date"].dt.dayofyear
    result: dict[int, np.ndarray] = {}
    for yr, grp in st_d.groupby("year"):
        full = pd.DataFrame({"doy": range(1, 366)})
        merged = full.merge(grp[["doy", "rainfall_mm"]], on="doy", how="left").fillna(0)
        result[int(yr)] = merged["rainfall_mm"].cumsum().values
    return result


@st.cache_data(ttl=3600, show_spinner=False)
def load_dry_streaks(station_key: str) -> pd.DataFrame:
    """Max consecutive zero-rainfall days per year for one station."""
    daily = load_all_daily()
    st_d  = daily[daily["station_key"] == station_key].copy()
    st_d["year"] = st_d["date"].dt.year
    rows = []
    for yr, grp in st_d.groupby("year"):
        vals = grp.sort_values("date")["rainfall_mm"].values
        max_s = cur_s = 0
        for v in vals:
            if v == 0:
                cur_s += 1
                max_s = max(max_s, cur_s)
            else:
                cur_s = 0
        rows.append({"year": int(yr), "max_dry_days": max_s})
    return pd.DataFrame(rows)


# ─── TAB 1: CLIMATE BASELINE ────────────────────────────────────────────────
def tab_climate_baseline():
    """Long-term averages, seasonal cycle, and station comparison."""
    monthly = load_monthly()
    clim    = load_climatology()
    annual  = load_annual()
    current_year = datetime.now().year
    hist_annual  = annual[annual["year"] < current_year]

    # ── Hero ─────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="hero-section">
        <div class="hero-date">Historical Archive · 2000 – 2025 · 15 Stations</div>
        <div class="hero-title">🌧️ Cape Town<br>Rainfall Atlas</div>
        <div class="hero-subtitle">
            26-year daily rainfall record &nbsp;·&nbsp; 127,000+ readings &nbsp;·&nbsp;
            City of Cape Town monitoring network
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Headline stats ────────────────────────────────────────────────────────
    ens_ann  = hist_annual.groupby("year")["total_mm"].mean()
    wettest  = int(ens_ann.idxmax())
    driest   = int(ens_ann.idxmin())
    cv       = ens_ann.std() / ens_ann.mean() * 100
    avg_rain = ens_ann.mean()

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Ensemble Annual Average", f"{avg_rain:.0f} mm",
                  "Mean of 15 stations, 2000–2025")
    with k2:
        st.metric("Wettest Year on Record", str(wettest),
                  f"{ens_ann.max():.0f} mm")
    with k3:
        st.metric("Driest Year on Record", str(driest),
                  f"{ens_ann.min():.0f} mm")
    with k4:
        st.metric("Inter-Annual Variability (CV)", f"{cv:.0f}%",
                  "Std dev / mean — higher = less reliable")

    _n_yrs = len(hist_annual["year"].unique())
    narrate(
        f"This atlas documents <b>{_n_yrs} years</b> of daily rainfall across "
        f"<b>15 monitoring stations</b>, spanning sea-level suburbs to the crest "
        f"of Table Mountain — a distance of barely 30\u202fkm yet a vertical rise "
        f"of nearly 1,000\u202fmetres. The <span class='hi'>{avg_rain:.0f}\u202fmm "
        f"ensemble average</span> conceals a dramatic range: <b>{wettest}</b> delivered "
        f"<span class='hi'>{ens_ann.max():.0f}\u202fmm</span> while <b>{driest}</b> "
        f"managed just <span class='amber'>{ens_ann.min():.0f}\u202fmm</span> \u2014 "
        f"a <b>{ens_ann.max()-ens_ann.min():.0f}\u202fmm swing</b> between the wettest "
        f"and driest years on record. At <span class='hi'>{cv:.0f}%</span> coefficient "
        f"of variation, Cape Town's year-to-year rainfall is among the most unpredictable "
        f"of any major city on earth."
    )

    # ── Station annual average ranking ────────────────────────────────────────
    section("🏅", "Average Annual Rainfall by Station — Ranked")

    stn_avgs = (
        hist_annual.groupby("station_key")["total_mm"].mean()
        .reset_index().rename(columns={"total_mm": "avg_mm"})
    )
    stn_avgs["name"]   = stn_avgs["station_key"].map(STATION_SHORT)
    stn_avgs["region"] = stn_avgs["station_key"].map(STATION_REGION)
    stn_avgs           = stn_avgs.sort_values("avg_mm")

    fig_rank = go.Figure(go.Bar(
        x=stn_avgs["avg_mm"],
        y=stn_avgs["name"],
        orientation="h",
        marker=dict(
            color=stn_avgs["avg_mm"],
            colorscale=[[0,"#0C2A4A"],[0.4,"#0369A1"],[0.7,"#0EA5E9"],[1,"#7DD3FC"]],
            cornerradius=5,
        ),
        text=[f"{v:.0f} mm" for v in stn_avgs["avg_mm"]],
        textposition="outside",
        textfont=dict(color="#CBD5E1", size=11),
        hovertemplate="<b>%{y}</b><br>%{x:.0f} mm / year avg<extra></extra>",
    ))
    fig_rank.update_layout(
        xaxis=dict(title="Average annual rainfall (mm)", range=[0, stn_avgs["avg_mm"].max() * 1.18]),
        yaxis=dict(tickfont=dict(size=12, color="#94A3B8")),
        margin=dict(l=0, r=0, t=10, b=0),
    )
    col_rank, col_map = st.columns([1, 1])
    with col_rank:
        dark_fig(fig_rank, 500)
        st.plotly_chart(fig_rank, width="stretch")
    with col_map:
        fig_map = go.Figure(go.Scattermapbox(
            lat=[STATION_LAT[k] for k in stn_avgs["station_key"]],
            lon=[STATION_LON[k] for k in stn_avgs["station_key"]],
            mode="markers",
            marker=go.scattermapbox.Marker(
                size=[max(9, v / 32) for v in stn_avgs["avg_mm"]],
                color=stn_avgs["avg_mm"].tolist(),
                colorscale=[[0,"#0C2A4A"],[0.4,"#0369A1"],[0.7,"#0EA5E9"],[1,"#7DD3FC"]],
                cmin=stn_avgs["avg_mm"].min(),
                cmax=stn_avgs["avg_mm"].max(),
                colorbar=dict(
                    title=dict(text="mm / yr", font=dict(color="#94A3B8", size=9)),
                    thickness=10, len=0.65,
                    tickfont=dict(color="#94A3B8", size=9),
                ),
                opacity=0.88,
            ),
            text=stn_avgs["name"].tolist(),
            customdata=stn_avgs["avg_mm"].tolist(),
            hovertemplate="<b>%{text}</b><br>%{customdata:.0f} mm / yr avg<extra></extra>",
        ))
        fig_map.update_layout(
            mapbox=dict(
                style="carto-darkmatter",
                center=dict(lat=-33.93, lon=18.65),
                zoom=8.8,
            ),
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="#0F172A",
            height=500,
        )
        st.plotly_chart(fig_map, width="stretch")

    st.markdown(
        '<div class="info-box">💡 Rainfall increases sharply with altitude. '
        'Table Mountain stations (Woodhead, Newlands) receive 3–4× more rain than '
        'low-lying coastal or inland stations — a defining feature of Cape Town\'s orographic rainfall.</div>',
        unsafe_allow_html=True,
    )
    _top_stn = stn_avgs.nlargest(1, "avg_mm").iloc[0]
    _bot_stn = stn_avgs.nsmallest(1, "avg_mm").iloc[0]
    _orog_ratio = _top_stn["avg_mm"] / _bot_stn["avg_mm"]
    narrate(
        f"The altitude gradient is ruthless. <b>{_top_stn['name']}</b>, clinging to "
        f"the south-western slopes of Table Mountain, receives "
        f"<span class='hi'>{_top_stn['avg_mm']:.0f}&#8239;mm per year</span> on average "
        f"&#8212; <span class='hi'>{_orog_ratio:.1f}&times; more</span> than "
        f"<b>{_bot_stn['name']}</b>, despite the two stations being separated by "
        f"less than 40&#8239;kilometres. The same winter cold fronts sweep the entire "
        f"peninsula, but the mountains intercept, lift, and wring moisture from every "
        f"passing system &#8212; a process called <em>orographic enhancement</em> that "
        f"concentrates rainfall at precisely the elevation where the city's reservoirs sit."
    )

    # ── Seasonal cycle ────────────────────────────────────────────────────────
    section("🍂", "Seasonal Cycle — Monthly Climatology (2000–2025)")

    col_chart, col_note = st.columns([3, 1])
    with col_chart:
        fig_sea = go.Figure()
        for i, key in enumerate(STATION_KEYS):
            d = clim[clim["station_key"] == key].sort_values("month")
            fig_sea.add_trace(go.Scatter(
                x=[MONTHS_SHORT[m-1] for m in d["month"]],
                y=d["avg_mm"],
                name=STATION_SHORT[key],
                line=dict(color=PALETTE[i % len(PALETTE)], width=1.8),
                mode="lines",
                opacity=0.85,
                hovertemplate=f"<b>{STATION_SHORT[key]}</b><br>%{{x}}: %{{y:.0f}} mm avg<extra></extra>",
            ))
        fig_sea.update_layout(
            yaxis_title="Average monthly rainfall (mm)",
            legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.01,
                        font=dict(size=10)),
        )
        dark_fig(fig_sea, 380)
        st.plotly_chart(fig_sea, width="stretch")

    with col_note:
        st.markdown("""
        <div style="height:32px"></div>
        <div class="rain-card">
            <div class="region">Cape Town Climate</div>
            <div class="station-name">Mediterranean Pattern</div>
            <div style="color:#CBD5E1;font-size:13px;line-height:1.8;margin-top:12px">
                🌧️ <b>Winter (May–Sep)</b><br>
                70–80% of annual rain<br>falls in these 5 months.<br><br>
                ☀️ <b>Summer (Nov–Mar)</b><br>
                Hot and dry. &lt;15% of<br>annual total.<br><br>
                🍂 <b>Shoulder (Apr, Oct)</b><br>
                Transitional months with<br>increasing variability.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Seasonal Nightingale rose ──────────────────────────────────────────────
    section("🌹", "Seasonal Rainfall Rose — Cape Town's Mediterranean Fingerprint")

    col_pol, col_pdesc = st.columns([2, 1])
    with col_pol:
        ens_clim = clim.groupby("month")["avg_mm"].mean().reset_index().sort_values("month")
        fig_pol  = go.Figure()
        # Each station as a semi-transparent filled spoke
        for i, key in enumerate(STATION_KEYS):
            d   = clim[clim["station_key"] == key].sort_values("month")
            c   = PALETTE[i % len(PALETTE)]
            rgb = f"{int(c[1:3],16)},{int(c[3:5],16)},{int(c[5:7],16)}"
            v   = d["avg_mm"].tolist()
            m   = [MONTHS_SHORT[mo - 1] for mo in d["month"]]
            fig_pol.add_trace(go.Scatterpolar(
                r=v + [v[0]], theta=m + [m[0]],
                mode="lines",
                line=dict(color=c, width=1.3),
                fill="toself", fillcolor=f"rgba({rgb},0.07)",
                name=STATION_SHORT[key], opacity=0.75,
                hovertemplate=f"<b>{STATION_SHORT[key]}</b><br>%{{theta}}: %{{r:.0f}} mm avg<extra></extra>",
            ))
        # Bold ensemble average
        ev = ens_clim["avg_mm"].tolist()
        em = [MONTHS_SHORT[m - 1] for m in ens_clim["month"]]
        fig_pol.add_trace(go.Scatterpolar(
            r=ev + [ev[0]], theta=em + [em[0]],
            mode="lines+markers",
            line=dict(color="#FFFFFF", width=3),
            marker=dict(size=5, color="#FFFFFF"),
            name="Ensemble avg",
            hovertemplate="<b>Ensemble</b><br>%{theta}: %{r:.0f} mm avg<extra></extra>",
        ))
        fig_pol.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    tickfont=dict(color="#64748B", size=10),
                    gridcolor="rgba(255,255,255,0.07)",
                    linecolor="rgba(255,255,255,0.08)",
                    tickangle=45,
                ),
                angularaxis=dict(
                    tickfont=dict(color="#F0F9FF", size=13),
                    linecolor="rgba(255,255,255,0.10)",
                    gridcolor="rgba(255,255,255,0.05)",
                    direction="clockwise",
                    rotation=90,  # Jan at top
                ),
                bgcolor="rgba(0,0,0,0)",
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            height=480,
            legend=dict(
                orientation="v", yanchor="top", y=1.02, xanchor="left", x=1.02,
                font=dict(size=10, color="#94A3B8"),
            ),
            margin=dict(l=30, r=140, t=20, b=20),
        )
        st.plotly_chart(fig_pol, width="stretch")

    with col_pdesc:
        st.markdown("""
        <div style="height:56px"></div>
        <div class="rain-card">
            <div class="region">How to Read</div>
            <div class="station-name">Seasonal Rose</div>
            <div style="color:#CBD5E1;font-size:13px;line-height:1.8;margin-top:12px">
                Each <b>spoke</b> represents a month.
                Distance from centre =
                average rainfall in mm.<br><br>
                A <b>lopsided</b> rose signals
                a strongly seasonal climate.
                A <b>near-circle</b> means
                year-round rainfall.<br><br>
                Cape Town's dramatic
                <b>June–August wedge</b> and
                collapsed summer side
                is the textbook
                <em>Mediterranean fingerprint</em>.<br><br>
                <b style="color:#fff">White line</b> =
                15-station ensemble average.
            </div>
        </div>
        """, unsafe_allow_html=True)

    _clim_ens = clim.groupby("month")["avg_mm"].mean().reset_index()
    _winter_pct = (_clim_ens[_clim_ens["month"].isin([5,6,7,8,9])]["avg_mm"].sum()
                   / _clim_ens["avg_mm"].sum() * 100)
    narrate(
        f"The rose makes visible what meteorologists call Cape Town's "
        f"<em>Mediterranean signature</em>: a rainfall pattern dominated by five "
        f"winter months that together deliver <span class='hi'>{_winter_pct:.0f}%</span> "
        f"of the annual total. This is not merely a statistical artefact &#8212; it is "
        f"the fundamental constraint governing the city's water supply. The reservoirs "
        f"must fill between May and September to sustain a full year of consumption. "
        f"When drought interrupts that filling cycle, the deficit cannot be recovered "
        f"until the next winter &#8212; creating the multi-year cascade that nearly "
        f"emptied the dams in 2018."
    )

    # ── Monthly variability box plots ─────────────────────────────────────────
    section("📦", "Monthly Rainfall Distribution — Year-to-Year Variability (Ensemble)")

    ens_mon = monthly[monthly["year"] < current_year].groupby(
        ["year","month"])["total_mm"].mean().reset_index()

    fig_box = go.Figure()
    for m in range(1, 13):
        d = ens_mon[ens_mon["month"] == m]["total_mm"]
        c = PALETTE[(m - 1) % len(PALETTE)]
        r, g, b = int(c[1:3],16), int(c[3:5],16), int(c[5:7],16)
        fig_box.add_trace(go.Box(
            y=d, name=MONTHS_SHORT[m-1],
            marker_color=c,
            line_color=c,
            fillcolor=f"rgba({r},{g},{b},0.15)",
            boxmean="sd",
            hovertemplate="<b>%{x}</b><br>%{y:.0f} mm<extra></extra>",
            showlegend=False,
        ))
    fig_box.update_layout(
        yaxis_title="Monthly rainfall (mm, 15-station avg)",
        xaxis=dict(tickfont=dict(size=12)),
    )
    dark_fig(fig_box, 380)
    st.plotly_chart(fig_box, width="stretch")

    # ── Station statistics table ───────────────────────────────────────────────
    section("📋", "Station Statistics Summary — 2000 to 2025")

    stats = []
    for key in STATION_KEYS:
        sa = hist_annual[hist_annual["station_key"] == key]
        if sa.empty:
            continue
        stats.append({
            "Station":        STATION_SHORT[key],
            "Region":         STATION_REGION[key],
            "Annual Avg (mm)": round(sa["total_mm"].mean(), 0),
            "Std Dev (mm)":    round(sa["total_mm"].std(), 0),
            "CV (%)":          round(sa["total_mm"].std() / sa["total_mm"].mean() * 100, 1),
            "Wettest Year":    int(sa.nlargest(1,"total_mm")["year"].values[0]),
            "Wettest (mm)":    round(sa["total_mm"].max(), 0),
            "Driest Year":     int(sa.nsmallest(1,"total_mm")["year"].values[0]),
            "Driest (mm)":     round(sa["total_mm"].min(), 0),
        })
    sdf = pd.DataFrame(stats).sort_values("Annual Avg (mm)", ascending=False)
    st.dataframe(
        sdf, width="stretch", hide_index=True,
        column_config={
            "Annual Avg (mm)": st.column_config.ProgressColumn(
                format="%.0f mm", min_value=0, max_value=2500),
            "Std Dev (mm)":   st.column_config.NumberColumn(format="%.0f mm"),
            "CV (%)":         st.column_config.NumberColumn(format="%.1f%%"),
            "Wettest (mm)":   st.column_config.NumberColumn(format="%.0f mm"),
            "Driest (mm)":    st.column_config.NumberColumn(format="%.0f mm"),
        },
    )


# ─── TAB 2: YEAR EXPLORER ────────────────────────────────────────────────────
def tab_year_explorer():
    """Pick any year and see it in full historical context."""
    monthly = load_monthly()
    annual  = load_annual()
    clim    = load_climatology()
    current_year = datetime.now().year

    hist_annual = annual[annual["year"] < current_year]
    available   = sorted(hist_annual["year"].unique().tolist())

    # ── Controls ─────────────────────────────────────────────────────────────
    col_yr, col_stn = st.columns([2, 2])
    with col_yr:
        sel_year = st.select_slider(
            "Select year to explore",
            options=available,
            value=2017,
        )
    with col_stn:
        sel_name = st.selectbox(
            "Reference station",
            options=[STATION_NAME[k] for k in STATION_KEYS],
            index=0,
        )
    sel_key = next(k for k in STATION_KEYS if STATION_NAME[k] == sel_name)

    # ── Ensemble annual ranking ───────────────────────────────────────────────
    ens_ann = (
        hist_annual.groupby("year")["total_mm"].mean()
        .reset_index().sort_values("total_mm", ascending=False).reset_index(drop=True)
    )
    ens_ann["rank"] = ens_ann.index + 1
    ens_mean = ens_ann["total_mm"].mean()

    row      = ens_ann[ens_ann["year"] == sel_year].iloc[0]
    sel_tot  = row["total_mm"]
    sel_rank = int(row["rank"])
    anomaly  = sel_tot - ens_mean
    pct_anom = anomaly / ens_mean * 100
    pct_ile  = (len(available) - sel_rank) / len(available) * 100
    n_yrs    = len(available)
    sfx      = "th" if 11 <= sel_rank <= 13 else {1:"st",2:"nd",3:"rd"}.get(sel_rank%10,"th")
    classif  = ("Very Wet" if pct_ile >= 80 else "Wet" if pct_ile >= 60 else
                "Near-Normal" if pct_ile >= 40 else "Dry" if pct_ile >= 20 else "Very Dry")

    # ── KPIs ─────────────────────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Ensemble Annual Total", f"{sel_tot:.0f} mm",
                  "15-station average")
    with k2:
        st.metric("Historical Rank", f"{sel_rank}{sfx} wettest",
                  f"out of {n_yrs} complete years")
    with k3:
        st.metric("Departure from Average", f"{anomaly:+.0f} mm",
                  f"{pct_anom:+.0f}%", delta_color="normal")
    with k4:
        st.metric("Classification", classif,
                  f"{pct_ile:.0f}th percentile")

    st.markdown("<br>", unsafe_allow_html=True)

    # Dynamic year narrative
    if sel_year in DROUGHT_YEARS:
        _yr_lead = (
            f"<span class='amber'>{sel_year} was one of the four consecutive drought years</span> "
            f"that drove Cape Town to the edge of Day Zero &#8212; a scenario where the city was "
            f"weeks from cutting all municipal water supplies. Dam levels fell below 20% of capacity "
            f"that winter. Level 6B restrictions limited residents to just 50&#8239;litres per day."
        )
    elif pct_ile >= 80:
        _yr_lead = (
            f"<span class='hi'>{sel_year} was an exceptional year for Cape Town's water supply.</span> "
            f"Ranking as the <b>{sel_rank}{sfx} wettest year</b> in {n_yrs} years on record, it "
            f"delivered rainfall well above what the city needs to sustain annual consumption &#8212; "
            f"and helped rebuild the reservoir buffer after the preceding dry cycle."
        )
    elif pct_ile <= 20:
        _yr_lead = (
            f"<span class='amber'>{sel_year} ranked among the driest years on record</span> &#8212; "
            f"a year when water managers would have been watching monthly inflows with mounting concern, "
            f"and the prospect of multi-year deficit accumulation would have become urgent."
        )
    else:
        _direction = "above" if anomaly > 0 else "below"
        _shade     = "hi" if anomaly > 0 else "amber"
        _yr_lead   = (
            f"At <span class='{_shade}'>{sel_tot:.0f}&#8239;mm</span>, {sel_year} came in "
            f"<b>{abs(anomaly):.0f}&#8239;mm ({abs(pct_anom):.0f}%) {_direction} the long-term average</b> &#8212; "
            f"the {sel_rank}{sfx} wettest of {n_yrs} complete years. "
            f"A year without a dramatic headline, but in a city as water-constrained as Cape Town, "
            f"even near-normal years carry real weight in the multi-year reservoir accounting."
        )
    narrate(
        _yr_lead + " The charts below map this year in full detail: "
        "day-by-day, month-by-month, and against every other year in the record."
    )

    # ── Daily rainfall calendar heatmap ──────────────────────────────────────
    section("📅", f"Daily Rainfall Calendar — {sel_year}  ·  {sel_name}")

    all_daily_raw = load_all_daily()
    daily_yr = all_daily_raw[
        (all_daily_raw["station_key"] == sel_key) &
        (all_daily_raw["date"].dt.year == sel_year)
    ].copy()

    if not daily_yr.empty:
        daily_yr["month"] = daily_yr["date"].dt.month
        daily_yr["dom"]   = daily_yr["date"].dt.day
        pivot_cal = (
            daily_yr
            .pivot_table(index="month", columns="dom", values="rainfall_mm", aggfunc="sum")
            .reindex(index=range(1, 13), columns=range(1, 32))
        )
        z_cap = max(50.0, float(daily_yr["rainfall_mm"].quantile(0.97)))
        fig_cal = go.Figure(go.Heatmap(
            z=pivot_cal.values,
            x=[str(d) for d in range(1, 32)],
            y=[MONTHS_SHORT[m - 1] for m in range(1, 13)],
            colorscale=[
                [0.000, "#07091A"],
                [0.001, "#07091A"],
                [0.025, "#0C2A4A"],
                [0.12,  "#0369A1"],
                [0.40,  "#0EA5E9"],
                [0.70,  "#38BDF8"],
                [1.000, "#E0F2FE"],
            ],
            zmin=0, zmax=z_cap,
            hoverongaps=False,
            hovertemplate="<b>%{y} %{x}</b><br>%{z:.1f} mm<extra></extra>",
            colorbar=dict(
                title="mm/day",
                tickfont=dict(color="#94A3B8"),
                title_font=dict(color="#94A3B8"),
                len=0.85, thickness=12,
            ),
        ))
        fig_cal.update_layout(
            yaxis=dict(autorange="reversed"),
            xaxis=dict(
                title="Day of month", tickmode="linear", dtick=1,
                tickfont=dict(size=10),
            ),
            margin=dict(l=0, r=60, t=10, b=30),
        )
        dark_fig(fig_cal, 340)
        st.plotly_chart(fig_cal, width="stretch")
        ann_total = daily_yr["rainfall_mm"].sum()
        rain_days = int((daily_yr["rainfall_mm"] > 0).sum())
        top_day   = daily_yr.nlargest(1, "rainfall_mm").iloc[0]
        st.markdown(
            f'<div class="info-box">📅 {sel_year} at {STATION_SHORT[sel_key]}: '
            f'<b>{ann_total:.0f} mm</b> total &nbsp;·&nbsp; '
            f'<b>{rain_days}</b> rain days &nbsp;·&nbsp; '
            f'Largest single day: <b>{top_day["rainfall_mm"]:.0f} mm</b> '
            f'on <b>{top_day["date"].strftime("%d %b")}</b></div>',
            unsafe_allow_html=True,
        )

    # ── Monthly bar + historical envelope ────────────────────────────────────
    section("📊", f"Monthly Rainfall — {sel_year} vs Historical Range ({sel_name})")

    yr_mon  = monthly[(monthly["station_key"] == sel_key) & (monthly["year"] == sel_year)]
    cl_mon  = clim[clim["station_key"] == sel_key]
    all_mon = monthly[(monthly["station_key"] == sel_key) & (monthly["year"].isin(available))]

    mstats = (
        all_mon.groupby("month")["total_mm"]
        .agg(p10=lambda x: x.quantile(.10), p25=lambda x: x.quantile(.25),
             med="median", p75=lambda x: x.quantile(.75), p90=lambda x: x.quantile(.90))
        .reset_index()
    )
    base = pd.DataFrame({"month": range(1,13)})
    yf   = base.merge(yr_mon[["month","total_mm"]],   on="month", how="left")
    mf   = base.merge(mstats, on="month", how="left")
    cf   = base.merge(cl_mon[["month","avg_mm"]],      on="month", how="left")
    labs = [MONTHS_SHORT[m-1] for m in range(1,13)]

    fig = go.Figure()
    # P10-P90 outer range (floating bar)
    fig.add_trace(go.Bar(
        x=labs,
        y=(mf["p90"] - mf["p10"]).tolist(),
        base=mf["p10"].tolist(),
        marker=dict(color="rgba(56,189,248,0.09)", line=dict(width=0)),
        name="10–90th pct range", hoverinfo="skip",
    ))
    # P25-P75 IQR (floating bar, slightly more opaque)
    fig.add_trace(go.Bar(
        x=labs,
        y=(mf["p75"] - mf["p25"]).tolist(),
        base=mf["p25"].tolist(),
        marker=dict(color="rgba(56,189,248,0.22)", line=dict(width=0)),
        name="25–75th pct (IQR)", hoverinfo="skip",
    ))
    # Median line
    fig.add_trace(go.Scatter(
        x=labs, y=mf["med"].tolist(), mode="lines",
        line=dict(color="rgba(148,163,184,0.55)", width=1.5, dash="dot"),
        name="Historical median",
    ))
    # Selected year bars — blue if ≥ avg, amber if below
    bar_col = [
        "#38BDF8" if (not pd.isna(yf.iloc[i]["total_mm"]) and
                      not pd.isna(cf.iloc[i]["avg_mm"]) and
                      yf.iloc[i]["total_mm"] >= cf.iloc[i]["avg_mm"])
        else "#F59E0B"
        for i in range(12)
    ]
    fig.add_trace(go.Bar(
        x=labs, y=yf["total_mm"], name=str(sel_year),
        marker=dict(color=bar_col, opacity=0.88, cornerradius=5),
        hovertemplate=f"<b>%{{x}} {sel_year}</b><br>%{{y:.0f}} mm<extra></extra>",
    ))
    fig.update_layout(
        barmode="overlay",
        yaxis_title="Monthly rainfall (mm)",
        legend=dict(orientation="h", yanchor="top", y=1.12, xanchor="left", x=0),
    )
    dark_fig(fig, 380)
    st.plotly_chart(fig, width="stretch")

    # ── Cumulative rainfall spaghetti ─────────────────────────────────────────
    section("📈", f"Cumulative Rainfall — {sel_year} vs All Years ({sel_name})")

    cumul = load_daily_cumulative(sel_key)
    other_years = {yr: v for yr, v in cumul.items() if yr in available and yr != sel_year}
    all_arr  = np.array(list(other_years.values()))
    med_c    = np.nanmedian(all_arr, axis=0) if len(all_arr) else None
    p25_c    = np.nanpercentile(all_arr, 25, axis=0) if len(all_arr) else None
    p75_c    = np.nanpercentile(all_arr, 75, axis=0) if len(all_arr) else None
    days     = list(range(1, 366))

    fig_c = go.Figure()
    # Spaghetti — other years
    for yr, c in other_years.items():
        is_d = yr in DROUGHT_YEARS
        fig_c.add_trace(go.Scatter(
            x=days, y=c.tolist(), mode="lines",
            line=dict(color="rgba(245,158,11,0.25)" if is_d else "rgba(148,163,184,0.10)",
                      width=1.2 if is_d else 0.8),
            showlegend=False,
            hovertemplate=f"<b>{yr}</b> · Day %{{x}}<br>%{{y:.0f}} mm cumul.<extra></extra>",
        ))
    # IQR band
    if med_c is not None:
        fig_c.add_trace(go.Scatter(
            x=days + days[::-1],
            y=p75_c.tolist() + p25_c.tolist()[::-1],
            fill="toself", fillcolor="rgba(56,189,248,0.07)",
            line=dict(width=0), name="25–75th pct range", hoverinfo="skip",
        ))
        fig_c.add_trace(go.Scatter(
            x=days, y=med_c.tolist(), mode="lines",
            line=dict(color="rgba(148,163,184,0.55)", width=2, dash="dot"),
            name="Historical median",
        ))
    # Selected year
    if sel_year in cumul:
        sel_col = "#38BDF8" if anomaly >= 0 else "#F59E0B"
        fig_c.add_trace(go.Scatter(
            x=days, y=cumul[sel_year].tolist(), mode="lines",
            line=dict(color=sel_col, width=3),
            name=str(sel_year),
            hovertemplate=f"<b>{sel_year}</b> · Day %{{x}}<br>%{{y:.0f}} mm<extra></extra>",
        ))
    # Month ticks
    month_starts = [1,32,60,91,121,152,182,213,244,274,305,335]
    fig_c.update_xaxes(tickvals=month_starts, ticktext=MONTHS_SHORT, title="Month")
    fig_c.update_layout(
        yaxis_title="Cumulative rainfall (mm)",
        legend=dict(orientation="h", yanchor="top", y=1.12, xanchor="left", x=0),
    )
    dark_fig(fig_c, 420)
    st.plotly_chart(fig_c, width="stretch")

    # ── All years ranked bar ──────────────────────────────────────────────────
    section("🏆", "All Complete Years Ranked — Wettest to Driest (Ensemble)")

    ranked = ens_ann.sort_values("total_mm", ascending=False).reset_index(drop=True)
    bar_colors = [
        "#F59E0B" if yr in DROUGHT_YEARS else
        ("#38BDF8" if yr == sel_year else "#1E3A5F")
        for yr in ranked["year"]
    ]
    fig_r = go.Figure(go.Bar(
        x=ranked["year"].astype(str), y=ranked["total_mm"],
        marker=dict(color=bar_colors, cornerradius=4),
        hovertemplate="<b>%{x}</b><br>%{y:.0f} mm<extra></extra>",
    ))
    fig_r.add_hline(
        y=ens_mean, line_dash="dot", line_color="rgba(148,163,184,0.45)",
        annotation_text=f"avg {ens_mean:.0f} mm",
        annotation_font_color="#64748B", annotation_font_size=11,
    )
    fig_r.update_layout(
        xaxis=dict(tickangle=45),
        yaxis_title="Annual rainfall (mm, 15-stn avg)",
        showlegend=False,
    )
    dark_fig(fig_r, 340)
    st.plotly_chart(fig_r, width="stretch")
    st.markdown(
        f'<div class="info-box">🔍 <b style="color:#38BDF8">{sel_year}</b> highlighted &nbsp;·&nbsp; '
        '<b style="color:#F59E0B">Amber</b> = Day Zero drought years 2015–2018</div>',
        unsafe_allow_html=True,
    )
    narrate(
        f"The ranked bar puts {sel_year} in the company of every other complete year in the record. "
        f"Notice how the <span class='amber'>amber drought years cluster</span> "
        f"at the dry end &#8212; not randomly scattered, but <b>consecutive</b>, which is "
        f"what makes a Cape Town-style drought so dangerous: each winter deficit layers on top "
        f"of the last, and the reservoirs cannot recover between seasons. "
        f"Conversely, the wettest years also tend to arrive in runs. When the large-scale "
        f"atmospheric patterns that steer cold fronts southward persist, the city can receive "
        f"several above-average winters in succession &#8212; and it is those clusters of "
        f"wet years that ultimately restore the system."
    )


# ─── TAB 3: TRENDS & CHANGE ──────────────────────────────────────────────────
def tab_trends():
    """Long-term trend analysis, anomaly index, decadal and seasonal shifts."""
    monthly = load_monthly()
    annual  = load_annual()
    clim    = load_climatology()
    daily   = load_all_daily()
    current_year = datetime.now().year
    hist_annual  = annual[annual["year"] < current_year]

    # ── Standardised Precipitation Anomaly Index ──────────────────────────────
    section("📉", "Standardised Precipitation Anomaly Index — 2000 to 2025")

    ens_ann = hist_annual.groupby("year")["total_mm"].mean().reset_index().sort_values("year")
    mu, sig = ens_ann["total_mm"].mean(), ens_ann["total_mm"].std()
    ens_ann["z"] = (ens_ann["total_mm"] - mu) / sig
    ens_ann["run5"] = ens_ann["z"].rolling(5, center=True).mean()

    z_colors = [
        "#0EA5E9" if z >= 1.0 else "#38BDF8" if z >= 0 else
        "#F97316" if z >= -1.0 else "#DC2626"
        for z in ens_ann["z"]
    ]
    fig_spi = go.Figure()
    fig_spi.add_hline(y=0,  line_color="rgba(255,255,255,0.12)", line_width=1)
    fig_spi.add_hline(y=1,  line_color="rgba(56,189,248,0.18)",  line_dash="dot", line_width=1)
    fig_spi.add_hline(y=-1, line_color="rgba(239,68,68,0.18)",   line_dash="dot", line_width=1)
    fig_spi.add_hrect(y0=1,  y1=3,  fillcolor="rgba(14,165,233,0.04)",  line_width=0)
    fig_spi.add_hrect(y0=-3, y1=-1, fillcolor="rgba(239,68,68,0.04)",   line_width=0)
    fig_spi.add_vrect(x0=2014.5, x1=2018.5,
                      fillcolor="rgba(245,158,11,0.06)", line_width=0,
                      annotation_text="Day Zero Drought", annotation_position="top left",
                      annotation_font_color="#F59E0B", annotation_font_size=11)
    fig_spi.add_trace(go.Bar(
        x=ens_ann["year"], y=ens_ann["z"],
        marker=dict(color=z_colors, cornerradius=4),
        name="Annual anomaly",
        hovertemplate="<b>%{x}</b><br>Z = %{y:.2f}σ  (%{customdata:.0f} mm)<extra></extra>",
        customdata=ens_ann["total_mm"],
    ))
    fig_spi.add_trace(go.Scatter(
        x=ens_ann["year"], y=ens_ann["run5"], mode="lines",
        line=dict(color="#F0F9FF", width=2.5),
        name="5-year running avg",
        hovertemplate="5yr avg: %{y:.2f}σ<extra></extra>",
    ))
    fig_spi.update_layout(
        yaxis_title="Standardised anomaly (σ)",
        xaxis=dict(dtick=2),
        legend=dict(orientation="h", yanchor="top", y=1.1, xanchor="right", x=1),
        annotations=[dict(
            x=0.01, y=0.97, xref="paper", yref="paper",
            text="🔵 Blue = wetter than avg &nbsp; 🔴 Red/orange = drier than avg",
            font=dict(size=11, color="#64748B"), showarrow=False,
        )],
    )
    dark_fig(fig_spi, 400)
    st.plotly_chart(fig_spi, width="stretch")

    _drought_z   = ens_ann[ens_ann["year"].isin(DROUGHT_YEARS)]["z"].mean()
    _drought_tot = ens_ann[ens_ann["year"].isin(DROUGHT_YEARS)]["total_mm"].mean()
    _deficit_4yr = (mu - _drought_tot) * 4
    _below_n     = int((ens_ann["z"] < 0).sum())
    narrate(
        f"The standardised anomaly index distils 26 years of rainfall into a single, "
        f"scannable signal. Each bar answers: <em>how unusual was this year?</em> "
        f"During the four drought years 2015&#8211;2018, the ensemble anomaly averaged "
        f"<span class='amber'>{_drought_z:.2f}&#963; below the long-term mean</span> &#8212; "
        f"a four-year streak that, under random conditions, has a probability of less than 1% "
        f"of occurring. The combined shortfall equated to roughly "
        f"<span class='amber'>{_deficit_4yr:.0f}&#8239;mm of missing rainfall</span> "
        f"across the network. Recovery came slowly: 2021 and 2023 finally pushed the anomaly "
        f"back above +1&#963;, refilling reservoirs that had been at crisis levels since 2017. "
        f"In total, <b>{_below_n} of {len(ens_ann)} years</b> fell below the long-term mean."
    )

    # ── Linear trend on annual totals ─────────────────────────────────────────
    section("📐", "Annual Rainfall Trend with Linear Fit — 2000 to 2025")

    from numpy.polynomial import polynomial as P

    col1, col2 = st.columns([3, 1])
    with col1:
        fig_trend = go.Figure()
        for yr in DROUGHT_YEARS:
            fig_trend.add_vrect(x0=yr-0.5, x1=yr+0.5,
                                fillcolor="rgba(245,158,11,0.07)", line_width=0)
        fig_trend.add_trace(go.Bar(
            x=ens_ann["year"], y=ens_ann["total_mm"],
            marker=dict(
                color=ens_ann["total_mm"],
                colorscale=[[0,"#7C2D12"],[0.35,"#F59E0B"],[0.55,"#475569"],[0.72,"#0EA5E9"],[1,"#7DD3FC"]],
                cmin=ens_ann["total_mm"].min() * 0.8,
                cmax=ens_ann["total_mm"].max() * 1.1,
                cornerradius=4,
            ),
            name="Annual total",
            hovertemplate="<b>%{x}</b><br>%{y:.0f} mm<extra></extra>",
        ))
        zfit   = P.polyfit(ens_ann["year"], ens_ann["total_mm"], 1)
        tfit   = P.polyval(ens_ann["year"], zfit)
        fig_trend.add_trace(go.Scatter(
            x=ens_ann["year"], y=tfit, mode="lines",
            line=dict(color="#EF4444", width=2.5, dash="dash"),
            name="Linear trend",
        ))
        fig_trend.add_hline(
            y=mu, line_dash="dot", line_color="rgba(148,163,184,0.4)",
            annotation_text=f"mean {mu:.0f} mm",
            annotation_font_color="#64748B", annotation_font_size=11,
        )
        fig_trend.update_layout(
            xaxis=dict(dtick=2), yaxis_title="mm / year",
            legend=dict(orientation="h", yanchor="top", y=1.1, xanchor="right", x=1),
        )
        dark_fig(fig_trend, 340)
        st.plotly_chart(fig_trend, width="stretch")

    with col2:
        slope = zfit[1]
        dir_  = "decreasing" if slope < 0 else "increasing"
        col   = "#EF4444" if slope < 0 else "#10B981"
        st.markdown(f"""
        <div style="height:48px"></div>
        <div class="rain-card">
            <div class="region">Trend Analysis</div>
            <div class="station-name">15-Station Ensemble</div>
            <div style="margin-top:16px">
                <div style="font-size:32px;font-weight:800;color:{col};letter-spacing:-0.03em">
                    {slope:+.1f}
                </div>
                <div style="color:#94A3B8;font-size:13px;margin-top:2px">mm per year</div>
            </div>
            <div style="color:{col};font-size:13px;font-weight:600;margin-top:10px">
                Rainfall is <b>{dir_}</b><br>at {abs(slope):.1f} mm/year
            </div>
            <div style="color:#475569;font-size:12px;margin-top:8px">
                Over 25 years: {slope*25:+.0f} mm total shift
            </div>
        </div>
        """, unsafe_allow_html=True)

    _slope_sign  = "amber" if slope < 0 else "hi"
    _total_shift = slope * len(ens_ann)
    narrate(
        f"A linear trend of <span class='{_slope_sign}'>{slope:+.1f}&#8239;mm per year</span> "
        f"over {len(ens_ann)} years translates to a total shift of "
        f"<span class='{_slope_sign}'>{_total_shift:+.0f}&#8239;mm</span> across the full record. "
        f"Whether this constitutes a statistically significant drying signal &#8212; "
        f"or reflects the natural multi-decadal oscillations common to Mediterranean climates "
        f"&#8212; is a question the data alone cannot answer. What is clear is that "
        f"the 2010s were markedly drier than the 2000s, and the post-drought recovery "
        f"of the early 2020s has not yet fully restored the long-term baseline that "
        f"characterised the first decade of the record."
    )

    # ── Decadal comparison ────────────────────────────────────────────────────
    section("📊", "Decadal Average Annual Rainfall by Station")

    sel_stns = st.multiselect(
        "Filter stations",
        options=[STATION_NAME[k] for k in STATION_KEYS],
        default=["Theewaterskloof","Wemmershoek No.1 Dam","Woodhead Dam","Newlands","Tygerberg"],
        key="dec_stns",
    )
    if not sel_stns:
        sel_stns = [STATION_NAME[k] for k in STATION_KEYS[:5]]
    sel_dec_keys = [k for k in STATION_KEYS if STATION_NAME[k] in sel_stns]

    decades = {"2000s (2000–09)": (2000,2009), "2010s (2010–19)": (2010,2019), "2020s (2020–25)": (2020,2025)}
    dec_rows = []
    for lbl, (y0,y1) in decades.items():
        for key in sel_dec_keys:
            d = hist_annual[(hist_annual["station_key"]==key) & hist_annual["year"].between(y0,y1)]
            dec_rows.append({"Decade": lbl, "Station": STATION_SHORT[key], "avg_mm": d["total_mm"].mean()})
    ddf = pd.DataFrame(dec_rows)
    fig_dec = px.bar(
        ddf, x="Station", y="avg_mm", color="Decade", barmode="group",
        color_discrete_sequence=["#0369A1","#0EA5E9","#7DD3FC"],
        labels={"avg_mm": "Average Annual mm"},
    )
    fig_dec.update_traces(marker_cornerradius=4)
    fig_dec.update_layout(
        legend=dict(orientation="h", yanchor="top", y=1.1, xanchor="left", x=0),
        yaxis_title="mm / year",
    )
    dark_fig(fig_dec, 360)
    st.plotly_chart(fig_dec, width="stretch")

    # ── Seasonal shift by decade ──────────────────────────────────────────────
    section("🍂", "Seasonal Pattern Shift by Decade")

    col_s1, col_s2 = st.columns([2, 1])
    with col_s1:
        sea_stn = st.selectbox(
            "Station",
            options=[STATION_NAME[k] for k in STATION_KEYS],
            index=4, key="sea_stn",
        )
    sea_key = next(k for k in STATION_KEYS if STATION_NAME[k] == sea_stn)

    dec_sea_rows = []
    for lbl, (y0, y1) in {"2000–09":(2000,2009),"2010–19":(2010,2019),"2020–25":(2020,2025)}.items():
        d = monthly[(monthly["station_key"]==sea_key) & monthly["year"].between(y0,y1)]
        ma = d.groupby("month")["total_mm"].mean().reset_index()
        ma["decade"] = lbl
        dec_sea_rows.append(ma)
    dss = pd.concat(dec_sea_rows)

    fig_ss = go.Figure()
    for i, lbl in enumerate(["2000–09","2010–19","2020–25"]):
        d = dss[dss["decade"]==lbl].sort_values("month")
        fig_ss.add_trace(go.Scatter(
            x=[MONTHS_SHORT[m-1] for m in d["month"]], y=d["total_mm"],
            name=lbl, mode="lines+markers",
            line=dict(color=["#0369A1","#0EA5E9","#7DD3FC"][i], width=2.5),
            marker=dict(size=6),
        ))
    fig_ss.update_layout(
        yaxis_title="Average monthly rainfall (mm)",
        legend=dict(orientation="h", yanchor="top", y=1.1, xanchor="right", x=1),
    )
    dark_fig(fig_ss, 340)
    st.plotly_chart(fig_ss, width="stretch")

    # ── Heavy rain days per year ──────────────────────────────────────────────
    section("⛈️", "Annual Frequency of Heavy Rain Days (threshold selectable)")

    col_t, col_m = st.columns([2, 2])
    with col_t:
        thresh = st.select_slider("Daily rainfall threshold (mm)",
                                   options=[5, 10, 20, 50, 100], value=20,
                                   key="thresh_trend")
    hist_daily = daily[daily["date"].dt.year < current_year].copy()
    hist_daily["year"] = hist_daily["date"].dt.year
    heavy = hist_daily[hist_daily["rainfall_mm"] >= thresh]
    hct   = heavy.groupby("year").size().reset_index(name="count")
    with col_m:
        st.metric(f"Avg days ≥{thresh}mm / year",
                  f"{hct['count'].mean():.0f}",
                  f"Total: {hct['count'].sum():,} station-days")

    zh  = P.polyfit(hct["year"], hct["count"], 1)
    trh = P.polyval(hct["year"], zh)
    fig_h = go.Figure()
    for yr in DROUGHT_YEARS:
        fig_h.add_vrect(x0=yr-0.5, x1=yr+0.5,
                        fillcolor="rgba(245,158,11,0.07)", line_width=0)
    fig_h.add_trace(go.Bar(
        x=hct["year"], y=hct["count"],
        marker=dict(
            color=hct["count"],
            colorscale=[[0,"#1E3A5F"],[0.5,"#0EA5E9"],[1,"#38BDF8"]],
            cornerradius=4,
        ),
        hovertemplate=f"<b>%{{x}}</b><br>%{{y}} station-days ≥{thresh}mm<extra></extra>",
        name="Heavy rain days",
    ))
    fig_h.add_trace(go.Scatter(
        x=hct["year"], y=trh, mode="lines",
        line=dict(color="#EF4444", width=2, dash="dash"),
        name="Trend",
    ))
    fig_h.update_layout(
        yaxis_title=f"Station-days with ≥{thresh}mm", xaxis=dict(dtick=2),
        legend=dict(orientation="h", yanchor="top", y=1.1, xanchor="right", x=1),
    )
    dark_fig(fig_h, 320)
    st.plotly_chart(fig_h, width="stretch")

    # ── Joy Division ridge chart ──────────────────────────────────────────────
    section("〰️", "Seasonal Ridge Chart — All Years Stacked (Joy Division View)")

    ridge_name = st.selectbox(
        "Station for ridge chart",
        options=[STATION_NAME[k] for k in STATION_KEYS],
        index=5, key="ridge_stn",
    )
    ridge_key  = next(k for k in STATION_KEYS if STATION_NAME[k] == ridge_name)
    ridge_mon  = monthly[
        (monthly["station_key"] == ridge_key) &
        (monthly["year"] < current_year)
    ].copy()
    years_rd = sorted(ridge_mon["year"].unique())
    max_val  = ridge_mon["total_mm"].max()
    spacing  = max_val * 0.30
    months_x = [MONTHS_SHORT[m - 1] for m in range(1, 13)]

    fig_ridge = go.Figure()
    tick_vals, tick_text = [], []
    for i, yr in enumerate(years_rd):
        yd = ridge_mon[ridge_mon["year"] == yr].sort_values("month")
        if len(yd) < 10:
            continue
        offset    = i * spacing
        y_vals    = yd["total_mm"].tolist()
        y_data    = [v + offset for v in y_vals]
        y_base    = [offset] * 12
        is_drt    = yr in DROUGHT_YEARS
        col       = "#F59E0B" if is_drt else PALETTE[i % len(PALETTE)]
        rgb       = f"{int(col[1:3],16)},{int(col[3:5],16)},{int(col[5:7],16)}"
        tick_vals.append(offset)
        tick_text.append(str(yr))
        # Baseline — must be added FIRST so the data trace can fill toward it
        fig_ridge.add_trace(go.Scatter(
            x=months_x, y=y_base,
            mode="lines", line=dict(color=f"rgba({rgb},0.35)", width=0.5),
            showlegend=False, hoverinfo="skip",
        ))
        # Data trace — fill="tonexty" fills down to the baseline trace above
        fig_ridge.add_trace(go.Scatter(
            x=months_x, y=y_data,
            mode="lines",
            line=dict(color=col, width=1.6 if is_drt else 1.2),
            fill="tonexty",
            fillcolor=f"rgba({rgb},{0.35 if is_drt else 0.22})",
            name=str(yr) if is_drt else "",
            showlegend=is_drt,
            hovertemplate=f"<b>{yr}</b> %{{x}}: %{{customdata:.0f}} mm<extra></extra>",
            customdata=y_vals,
        ))

    ridge_h = max(580, len(years_rd) * 26)
    fig_ridge.update_layout(
        height=ridge_h,
        yaxis=dict(
            tickvals=tick_vals, ticktext=tick_text,
            tickfont=dict(size=10, color="#64748B"),
            gridcolor="rgba(255,255,255,0.03)",
        ),
        xaxis=dict(tickfont=dict(size=12, color="#94A3B8")),
        showlegend=True,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0,
            font=dict(size=11, color="#F59E0B"),
            title=dict(text="Drought years  ", font=dict(color="#F59E0B", size=11)),
        ),
        margin=dict(l=50, r=20, t=30, b=30),
    )
    dark_fig(fig_ridge, ridge_h)
    st.plotly_chart(fig_ridge, width="stretch")
    st.markdown(
        '<div class="info-box">Each ridge is one year. Ridge height above the year baseline = monthly rainfall in mm. '
        '<b style="color:#F59E0B">Amber ridges</b> = Day Zero drought years (2015–2018) — note the collapsed June–Sep peaks.</div>',
        unsafe_allow_html=True,
    )


# ─── TAB 4: EXTREMES ─────────────────────────────────────────────────────────
def tab_extremes():
    """Records, monthly anomaly heatmap, extreme events, and dry spells."""
    daily   = load_all_daily()
    monthly = load_monthly()
    annual  = load_annual()
    clim    = load_climatology()
    current_year = datetime.now().year
    hist_annual  = annual[annual["year"] < current_year]
    hist_daily   = daily[daily["date"].dt.year < current_year].copy()

    # ── All-time station records ──────────────────────────────────────────────
    section("🏆", "All-Time Station Records (2000–2025)")

    records = []
    for key in STATION_KEYS:
        sa = hist_annual[hist_annual["station_key"] == key]
        sd = hist_daily[hist_daily["station_key"] == key]
        if sa.empty or sd.empty:
            continue
        top_day = sd.nlargest(1, "rainfall_mm")
        records.append({
            "Station":          STATION_SHORT[key],
            "Region":           STATION_REGION[key],
            "Record Day (mm)":  top_day["rainfall_mm"].values[0],
            "Record Date":      top_day["date"].dt.strftime("%d %b %Y").values[0],
            "Wettest Year":     int(sa.nlargest(1,"total_mm")["year"].values[0]),
            "Wettest (mm)":     round(sa["total_mm"].max(), 0),
            "Driest Year":      int(sa.nsmallest(1,"total_mm")["year"].values[0]),
            "Driest (mm)":      round(sa["total_mm"].min(), 0),
            "Annual Avg (mm)":  round(sa["total_mm"].mean(), 0),
        })
    rdf = pd.DataFrame(records).sort_values("Annual Avg (mm)", ascending=False)
    st.dataframe(
        rdf, width="stretch", hide_index=True,
        column_config={
            "Record Day (mm)":  st.column_config.NumberColumn(format="%.0f mm"),
            "Wettest (mm)":     st.column_config.NumberColumn(format="%.0f mm"),
            "Driest (mm)":      st.column_config.NumberColumn(format="%.0f mm"),
            "Annual Avg (mm)":  st.column_config.ProgressColumn(
                format="%.0f mm", min_value=0, max_value=2500),
        },
    )
    if not rdf.empty:
        _top_rec = rdf.nlargest(1, "Record Day (mm)").iloc[0]
        narrate(
            f"Records are not just numbers &#8212; they mark the moments when Cape Town's weather "
            f"revealed its extremes. The single-day record across all 15 stations is "
            f"<span class='hi'>{_top_rec['Record Day (mm)']:.0f}&#8239;mm</span> at "
            f"<b>{_top_rec['Station']}</b> on <b>{_top_rec['Record Date']}</b> &#8212; "
            f"equivalent to a year's rainfall for many drier cities, delivered in 24&#8239;hours. "
            f"Yet the same network that produces flood records also endures its driest winters "
            f"on record in the same locations. In Mediterranean climates, "
            f"<em>intensity and scarcity coexist</em>: the infrequent storms that arrive "
            f"must carry the weight of an entire season."
        )

    # ── Monthly anomaly heatmap ───────────────────────────────────────────────
    section("🌡️", "Monthly Rainfall Anomaly Heatmap — All Years × All Months (Ensemble %)")

    st.markdown(
        '<div class="info-box">🔵 Blue = wetter than historical average &nbsp;·&nbsp; '
        '🔴 Red = drier than average &nbsp;·&nbsp; Values show % departure. '
        'Amber outlines = Day Zero drought years.</div>',
        unsafe_allow_html=True,
    )

    mon_hist = monthly[monthly["year"] < current_year].copy()
    mon_hist = mon_hist.merge(clim[["station_key","month","avg_mm"]],
                              on=["station_key","month"], how="left")
    mon_hist["pct_anom"] = (
        (mon_hist["total_mm"] / mon_hist["avg_mm"] * 100 - 100).clip(-90, 200)
    )
    ens_anom = mon_hist.groupby(["year","month"])["pct_anom"].mean().reset_index()
    pivot    = ens_anom.pivot_table(index="year", columns="month", values="pct_anom")
    pivot.columns = [MONTHS_SHORT[c-1] for c in pivot.columns]

    fig_heat = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=[
            [0.00, "#7C2D12"], [0.15, "#DC2626"], [0.30, "#F97316"],
            [0.43, "#FCD34D"], [0.50, "#0F172A"],
            [0.57, "#BAE6FD"], [0.70, "#0EA5E9"],
            [0.85, "#0369A1"], [1.00, "#1E3A8A"],
        ],
        zmid=0, zmin=-70, zmax=130,
        hoverongaps=False,
        hovertemplate="<b>%{y} %{x}</b><br>%{z:+.0f}% vs avg<extra></extra>",
        colorbar=dict(
            title="% vs avg",
            tickfont=dict(color="#94A3B8"), title_font=dict(color="#94A3B8"),
            len=0.8, thickness=14,
        ),
    ))
    for yr in DROUGHT_YEARS:
        if yr in pivot.index.tolist():
            fig_heat.add_shape(
                type="rect", x0=-0.5, x1=11.5,
                y0=yr - 0.5, y1=yr + 0.5,
                line=dict(color="rgba(245,158,11,0.8)", width=2),
            )
    dark_fig(fig_heat, 560)
    fig_heat.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_heat, width="stretch")

    narrate(
        "The heatmap is a 26-year calendar of rainfall fortune. "
        "Scan down any column and you read a month's entire history; "
        "scan across any row and you read a year's personality. "
        "The four <span class='amber'>amber-outlined rows</span> &#8212; 2015 to 2018 &#8212; "
        "tell the drought story more viscerally than any number: an unbroken horizontal "
        "band of red and orange spanning nearly every winter month across four consecutive years. "
        "This is what makes a Cape Town-style drought so insidious: it is not one bad season "
        "but a slow, multi-year erosion of the system that demands an equally sustained "
        "recovery. The contrasting deep-blue band of 2021&#8211;2023 marks that recovery."
    )

    # ── Ranked years ─────────────────────────────────────────────────────────
    section("📊", "All Years Ranked by Annual Rainfall")

    ens_ann = (
        hist_annual.groupby("year")["total_mm"].mean()
        .reset_index().sort_values("total_mm", ascending=False).reset_index(drop=True)
    )
    ens_ann["rank"] = ens_ann.index + 1
    ens_mean = ens_ann["total_mm"].mean()
    ens_std  = ens_ann["total_mm"].std()
    ens_ann["z"] = (ens_ann["total_mm"] - ens_mean) / ens_std

    col_wet, col_dry = st.columns(2)
    with col_wet:
        st.markdown('<div class="section-header">💧 Top 5 Wettest Years</div>', unsafe_allow_html=True)
        top5 = ens_ann.head(5)[["rank","year","total_mm","z"]].rename(
            columns={"total_mm":"Avg (mm)","z":"Z-score"})
        top5["Avg (mm)"] = top5["Avg (mm)"].round(0)
        top5["Z-score"]  = top5["Z-score"].round(2)
        st.dataframe(top5, width="stretch", hide_index=True)
    with col_dry:
        st.markdown('<div class="section-header">🔥 Top 5 Driest Years</div>', unsafe_allow_html=True)
        bot5 = ens_ann.tail(5).sort_values("total_mm")[["rank","year","total_mm","z"]].rename(
            columns={"total_mm":"Avg (mm)","z":"Z-score"})
        bot5["Avg (mm)"] = bot5["Avg (mm)"].round(0)
        bot5["Z-score"]  = bot5["Z-score"].round(2)
        st.dataframe(bot5, width="stretch", hide_index=True)

    fig_rnk = go.Figure(go.Bar(
        x=ens_ann.sort_values("total_mm", ascending=False)["year"].astype(str),
        y=ens_ann.sort_values("total_mm", ascending=False)["total_mm"],
        marker=dict(
            color=ens_ann.sort_values("total_mm", ascending=False)["z"],
            colorscale=[[0,"#7C2D12"],[0.3,"#F59E0B"],[0.5,"#475569"],[0.7,"#0EA5E9"],[1,"#7DD3FC"]],
            cmid=0, cornerradius=4,
        ),
        hovertemplate="<b>%{x}</b><br>%{y:.0f} mm<extra></extra>",
    ))
    fig_rnk.add_hline(
        y=ens_mean, line_dash="dot", line_color="rgba(148,163,184,0.4)",
        annotation_text=f"avg {ens_mean:.0f} mm",
        annotation_font_color="#64748B", annotation_font_size=11,
    )
    fig_rnk.update_layout(
        xaxis=dict(tickangle=45), yaxis_title="Annual rainfall (mm)",
        showlegend=False,
    )
    dark_fig(fig_rnk, 320)
    st.plotly_chart(fig_rnk, width="stretch")

    # ── Extreme event counts ──────────────────────────────────────────────────
    section("⛈️", "Annual Count of Extreme Rainfall Events by Threshold")

    col_th, _ = st.columns([2, 2])
    with col_th:
        thresh2 = st.select_slider(
            "Threshold (mm/day)", options=[10, 20, 50, 100], value=50, key="thresh_ext"
        )
    hist_daily["year"] = hist_daily["date"].dt.year
    ext = hist_daily[hist_daily["rainfall_mm"] >= thresh2]
    ect = ext.groupby("year").size().reset_index(name="count")

    fig_ext = go.Figure(go.Bar(
        x=ect["year"], y=ect["count"],
        marker=dict(
            color=ect["count"],
            colorscale=[[0,"#1E3A5F"],[1,"#38BDF8"]],
            cornerradius=4,
        ),
        hovertemplate=f"<b>%{{x}}</b><br>%{{y}} days ≥{thresh2}mm<extra></extra>",
    ))
    for yr in DROUGHT_YEARS:
        fig_ext.add_vrect(x0=yr-0.5, x1=yr+0.5,
                          fillcolor="rgba(245,158,11,0.07)", line_width=0)
    fig_ext.update_layout(
        yaxis_title=f"Station-days ≥{thresh2} mm", xaxis=dict(dtick=2),
    )
    dark_fig(fig_ext, 300)
    st.plotly_chart(fig_ext, width="stretch")

    # ── Longest dry spells ────────────────────────────────────────────────────
    section("🌵", "Longest Annual Dry Spell — Max Consecutive Zero-Rain Days")

    dry_stn = st.selectbox(
        "Station for dry-spell analysis",
        options=[STATION_NAME[k] for k in STATION_KEYS],
        index=5, key="dry_stn",
    )
    dry_key = next(k for k in STATION_KEYS if STATION_NAME[k] == dry_stn)

    dry_df = load_dry_streaks(dry_key)
    dry_df = dry_df[dry_df["year"] < current_year]

    fig_dry = go.Figure(go.Bar(
        x=dry_df["year"], y=dry_df["max_dry_days"],
        marker=dict(
            color=dry_df["max_dry_days"],
            colorscale=[[0,"#064E3B"],[0.3,"#059669"],[0.6,"#F59E0B"],[1,"#DC2626"]],
            cornerradius=4,
        ),
        hovertemplate="<b>%{x}</b><br>%{y} consecutive dry days<extra></extra>",
    ))
    for yr in DROUGHT_YEARS:
        fig_dry.add_vrect(x0=yr-0.5, x1=yr+0.5,
                          fillcolor="rgba(245,158,11,0.07)", line_width=0)
    fig_dry.add_hline(
        y=dry_df["max_dry_days"].mean(), line_dash="dot",
        line_color="rgba(148,163,184,0.4)",
        annotation_text=f"avg {dry_df['max_dry_days'].mean():.0f} days",
        annotation_font_color="#64748B", annotation_font_size=11,
    )
    fig_dry.update_layout(
        yaxis_title="Max consecutive dry days", xaxis=dict(dtick=2),
    )
    dark_fig(fig_dry, 320)
    st.plotly_chart(fig_dry, width="stretch")

    st.markdown(
        '<div class="drought-banner">⚠️ Dry spell lengths reflect station recording patterns — '
        'stations that only record on rainy days will show inflated streak lengths. '
        'Compare across stations with similar recording practices.</div>',
        unsafe_allow_html=True,
    )


# ─── MAIN ────────────────────────────────────────────────────────────────────
def main():
    inject_css()

    tab1, tab2, tab3, tab4 = st.tabs([
        "  📊  Climate Baseline  ",
        "  🔍  Year Explorer  ",
        "  📉  Trends & Change  ",
        "  ⚡  Extremes  ",
    ])

    with tab1:
        tab_climate_baseline()
    with tab2:
        tab_year_explorer()
    with tab3:
        tab_trends()
    with tab4:
        tab_extremes()

    st.markdown(f"""
    <div style="text-align:center;margin-top:60px;padding:24px 0;
                border-top:1px solid rgba(255,255,255,0.06);
                color:#334155;font-size:12px;font-weight:500;">
        Cape Town Rainfall Atlas v{__version__} &nbsp;&middot;&nbsp;
        Data: <a href="https://odp-cctegis.opendata.arcgis.com" target="_blank"
            rel="noopener noreferrer" style="color:#475569;">City of Cape Town Open Data Portal</a>
        (2000&#8239;&#8211;&#8239;2026) &nbsp;&middot;&nbsp;
        15 monitoring stations &nbsp;&middot;&nbsp;
        Built with Streamlit &amp; Plotly
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
