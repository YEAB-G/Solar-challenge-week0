import io
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from scipy import stats

# =========================
# App Config
# =========================
st.set_page_config(
    page_title="Solar Sites — Week 0 Dashboard",
    page_icon="🌞",
    layout="wide"
)

DATA_DIR = Path("data")
DEFAULT_FILES = {
    "Benin": DATA_DIR / "benin_clean.csv",
    "Sierra Leone": DATA_DIR / "sierra_leone_clean.csv",
    "Togo": DATA_DIR / "togo_clean.csv",
}

REQ_COLS = ["Timestamp", "GHI", "DNI", "DHI"]  # minimal columns the app expects


# =========================
# Helpers
# =========================
@st.cache_data(show_spinner=False)
def load_clean_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "Timestamp" in df.columns:
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
    return df

@st.cache_data(show_spinner=False)
def read_uploaded_csv(file) -> pd.DataFrame:
    df = pd.read_csv(file)
    if "Timestamp" in df.columns:
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
    return df

def validate_columns(df: pd.DataFrame, needed: List[str]) -> List[str]:
    return [c for c in needed if c not in df.columns]

def summarise(df: pd.DataFrame, metrics: List[str]) -> pd.DataFrame:
    return (
        df.groupby("Country")[metrics]
          .agg(["mean", "median", "std", "count"])
          .round(2)
    )

def filter_by_date(df: pd.DataFrame, start, end) -> pd.DataFrame:
    if "Timestamp" not in df or start is None or end is None:
        return df
    m = df["Timestamp"].between(start, end, inclusive="both")
    return df.loc[m].copy()


# =========================
# Sidebar — Data Sources
# =========================
st.sidebar.header("📦 Data Sources")

use_uploaded = st.sidebar.checkbox("Use uploaded CSVs instead of local cleaned files", value=False)

dfs = []
missing_sources = []

if use_uploaded:
    st.sidebar.write("Upload **cleaned** CSVs (with Timestamp, GHI/DNI/DHI):")
    up_benin = st.sidebar.file_uploader("Benin CSV", type=["csv"], key="up_benin")
    up_sl    = st.sidebar.file_uploader("Sierra Leone CSV", type=["csv"], key="up_sl")
    up_togo  = st.sidebar.file_uploader("Togo CSV", type=["csv"], key="up_togo")

    uploads = {
        "Benin": up_benin,
        "Sierra Leone": up_sl,
        "Togo": up_togo
    }
    for country, file in uploads.items():
        if file is not None:
            df = read_uploaded_csv(file)
            df["Country"] = country
            dfs.append(df)
        else:
            missing_sources.append(country)
else:
    for country, path in DEFAULT_FILES.items():
        if path.exists():
            df = load_clean_csv(path)
            df["Country"] = country
            dfs.append(df)
        else:
            missing_sources.append(country)

if missing_sources:
    st.sidebar.warning("Missing: " + ", ".join(missing_sources))

if not dfs:
    st.stop()

all_df = pd.concat(dfs, ignore_index=True)

# quick sanity: check columns
missing_cols = validate_columns(all_df, REQ_COLS + ["Country"])
if missing_cols:
    st.error(f"Your data is missing required column(s): {missing_cols}")
    st.stop()

# =========================
# Sidebar — Controls
# =========================
st.sidebar.header("⚙️ Controls")

metric = st.sidebar.selectbox("Metric", ["GHI", "DNI", "DHI"], index=0)

countries = sorted(all_df["Country"].dropna().unique().tolist())
chosen_countries = st.sidebar.multiselect("Countries", countries, default=countries)

# Timestamp filter
min_ts = pd.to_datetime(all_df["Timestamp"]).min()
max_ts = pd.to_datetime(all_df["Timestamp"]).max()
date_range = st.sidebar.date_input(
    "Date range",
    value=(min_ts.date(), max_ts.date()),
    min_value=min_ts.date(),
    max_value=max_ts.date()
)

# Safety in case user clears selection
if not chosen_countries:
    st.warning("Please select at least one country.")
    st.stop()

# Filter by country & time
df_view = all_df[all_df["Country"].isin(chosen_countries)].copy()
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start_date = pd.to_datetime(date_range[0])
    end_date = pd.to_datetime(date_range[1])
    df_view = filter_by_date(df_view, start_date, end_date)

st.title("🌞 Solar Sites — Week 0 Dashboard")
st.caption("Benin • Sierra Leone • Togo  |  Cleaned data • Boxplots • Summary • ANOVA/Kruskal  |  Powered by Streamlit")

# =========================
# KPI Cards
# =========================
k1 = df_view.groupby("Country")[metric].mean().mean()
k2 = df_view.groupby("Country")[metric].median().median()
k3 = df_view.groupby("Country")[metric].std().mean()
c1, c2, c3 = st.columns(3)
c1.metric(f"Avg of Country Means ({metric})", f"{k1:,.1f}")
c2.metric(f"Median of Country Medians ({metric})", f"{k2:,.1f}")
c3.metric(f"Avg of Country Stds ({metric})", f"{k3:,.1f}")

st.markdown("---")

# =========================
# Summary Table
# =========================
st.subheader("📊 Summary Statistics")
metrics = [m for m in ["GHI", "DNI", "DHI"] if m in df_view.columns]
summary = summarise(df_view, metrics)
st.dataframe(summary, use_container_width=True)

# =========================
# Boxplot by Country
# =========================
st.subheader(f"🧰 Boxplot — {metric} by Country")
fig1, ax1 = plt.subplots(figsize=(6.5, 4.5))
data = [df_view.loc[df_view["Country"] == c, metric].dropna() for c in chosen_countries]
ax1.boxplot(data, labels=chosen_countries)
ax1.set_ylabel(metric)
ax1.set_title(f"{metric} by Country")
ax1.grid(alpha=0.3)
st.pyplot(fig1, use_container_width=True)

# =========================
# Time Series
# =========================
st.subheader(f"⏱️ Time Series — {metric} over Time")
for ctry in chosen_countries:
    sub = df_view[df_view["Country"] == ctry].dropna(subset=["Timestamp", metric]).sort_values("Timestamp")
    if sub.empty:
        continue
    fig_ts, ax_ts = plt.subplots(figsize=(7, 2.8))
    ax_ts.plot(sub["Timestamp"], sub[metric])
    ax_ts.set_title(f"{ctry} — {metric} over time")
    ax_ts.set_xlabel("Timestamp")
    ax_ts.set_ylabel(metric)
    ax_ts.grid(alpha=0.3)
    st.pyplot(fig_ts, use_container_width=True)

# =========================
# ANOVA & Kruskal on GHI
# =========================
st.subheader("🧪 Statistical Tests — Country Differences (GHI)")
if "GHI" in df_view.columns:
    groups = [df_view.loc[df_view["Country"] == c, "GHI"].dropna() for c in chosen_countries]
    if all(len(g) >= 3 for g in groups) and len(groups) >= 2:
        try:
            ftest = stats.f_oneway(*groups)
            kwtest = stats.kruskal(*groups)
            st.write(f"**ANOVA on GHI**: F = `{ftest.statistic:.3f}`, p = `{ftest.pvalue:.4g}`")
            st.write(f"**Kruskal–Wallis on GHI**: H = `{kwtest.statistic:.3f}`, p = `{kwtest.pvalue:.4g}`")
            if ftest.pvalue < 0.05 or kwtest.pvalue < 0.05:
                st.success("Result: Significant differences detected between countries (p < 0.05).")
            else:
                st.info("Result: No significant differences detected at α = 0.05.")
        except Exception as e:
            st.warning(f"Statistical tests could not run: {e}")
    else:
        st.info("Not enough data per selected country to run tests (need ≥ 3 observations each).")
else:
    st.warning("GHI column not found.")

st.markdown("---")
st.caption("Note: Cleaned data assumed to follow Week 0 Task 2 rules (non-negative irradiance, DHI≤GHI, RH 0–100, etc.).")
