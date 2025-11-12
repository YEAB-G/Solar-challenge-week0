# app.py — Week 0 Dashboard (non-invasive)
from pathlib import Path
from typing import Dict, List
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from scipy import stats

st.set_page_config(page_title="Week 0 — Solar Dashboard", page_icon="🌞", layout="wide")

# --- Robust file discovery: try several folders & alternative filenames ---
BASE = Path(__file__).parent
CANDIDATE_DIRS = [
    BASE / "data" / "clean",
    BASE / "notebook" / "data",
    BASE / "data",
]

# common cleaned filenames (include Sierra Leone typo fallback)
FILENAME_CHOICES = {
    "Benin": ["benin_clean.csv"],
    "Sierra Leone": ["sierra_leone_clean.csv", "sierraleon_clean.csv"],
    "Togo": ["togo_clean.csv"],
}

def find_first_existing(paths: List[Path]) -> Path | None:
    for p in paths:
        if p.exists():
            return p
    return None

def discover_files() -> Dict[str, Path | None]:
    found = {}
    for country, names in FILENAME_CHOICES.items():
        candidates = []
        for d in CANDIDATE_DIRS:
            for n in names:
                candidates.append(d / n)
        found[country] = find_first_existing(candidates)
    return found

DEFAULT = discover_files()

# --- Sidebar: choose data source (local or upload) ---
st.sidebar.header("📦 Data Source")
use_upload = st.sidebar.checkbox("Use uploaded CSVs (override local files)", value=False)

def load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "Timestamp" in df.columns:
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
    return df

def load_uploaded(file) -> pd.DataFrame:
    df = pd.read_csv(file)
    if "Timestamp" in df.columns:
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
    return df

data_frames = []
missing = []

if use_upload:
    st.sidebar.write("Upload your **cleaned** CSVs (with Timestamp, GHI/DNI/DHI)")
    up_benin = st.sidebar.file_uploader("Benin CSV", type=["csv"], key="benin_up")
    up_sl    = st.sidebar.file_uploader("Sierra Leone CSV", type=["csv"], key="sl_up")
    up_togo  = st.sidebar.file_uploader("Togo CSV", type=["csv"], key="togo_up")
    uploads = {"Benin": up_benin, "Sierra Leone": up_sl, "Togo": up_togo}
    for ctry, f in uploads.items():
        if f is not None:
            df = load_uploaded(f)
            df["Country"] = ctry
            data_frames.append(df)
        else:
            missing.append(ctry)
else:
    for ctry, p in DEFAULT.items():
        if p is not None:
            df = load_csv(p)
            df["Country"] = ctry
            data_frames.append(df)
        else:
            missing.append(ctry)

if missing:
    st.sidebar.warning("Missing: " + ", ".join(missing))

if not data_frames:
    st.stop()

all_df = pd.concat(data_frames, ignore_index=True)

# --- Controls ---
st.sidebar.header("⚙️ Controls")
metric = st.sidebar.selectbox("Metric", [m for m in ["GHI","DNI","DHI"] if m in all_df.columns], index=0)
countries = sorted(all_df["Country"].dropna().unique().tolist())
selected = st.sidebar.multiselect("Countries", countries, default=countries)

if not selected:
    st.warning("Please select at least one country.")
    st.stop()

all_df = all_df[all_df["Country"].isin(selected)].copy()

# Date range
if "Timestamp" in all_df.columns:
    tmin, tmax = pd.to_datetime(all_df["Timestamp"]).min(), pd.to_datetime(all_df["Timestamp"]).max()
    dr = st.sidebar.date_input("Date range", value=(tmin.date(), tmax.date()), min_value=tmin.date(), max_value=tmax.date())
    if isinstance(dr, (list, tuple)) and len(dr) == 2:
        d0, d1 = pd.to_datetime(dr[0]), pd.to_datetime(dr[1])
        all_df = all_df[(all_df["Timestamp"] >= d0) & (all_df["Timestamp"] <= d1)]

st.title("🌞 Week 0 — Cross-Country Solar Dashboard")
st.caption("Benin • Sierra Leone • Togo  |  Cleaned data only (non-invasive).")

# --- KPI Cards ---
def safe_mean(s): return float(np.nanmean(s)) if len(s) else np.nan
g = all_df.groupby("Country")[metric]
k1 = safe_mean(g.mean())
k2 = safe_mean(g.median())
k3 = safe_mean(g.std())

c1, c2, c3 = st.columns(3)
c1.metric(f"Avg of Country Means ({metric})", f"{k1:,.1f}")
c2.metric(f"Median of Country Medians ({metric})", f"{k2:,.1f}")
c3.metric(f"Avg of Country Stds ({metric})", f"{k3:,.1f}")

st.markdown("---")

# --- Summary Table ---
st.subheader("📊 Summary Statistics")
metrics = [m for m in ["GHI","DNI","DHI"] if m in all_df.columns]
summary = all_df.groupby("Country")[metrics].agg(["mean","median","std","count"]).round(2)
st.dataframe(summary, use_container_width=True)

# --- Boxplot ---
st.subheader(f"🧰 Boxplot — {metric} by Country")
fig1, ax1 = plt.subplots(figsize=(6.5,4.2))
data = [all_df.loc[all_df["Country"]==c, metric].dropna() for c in selected]
ax1.boxplot(data, labels=selected)
ax1.set_ylabel(metric); ax1.set_title(f"{metric} by Country"); ax1.grid(alpha=0.3)
st.pyplot(fig1, use_container_width=True)

# --- Time Series ---
st.subheader(f"⏱ Time Series — {metric} over Time")
if "Timestamp" in all_df.columns:
    for ctry in selected:
        sub = all_df[(all_df["Country"]==ctry) & all_df[metric].notna()].sort_values("Timestamp")
        if sub.empty: continue
        fig_ts, ax_ts = plt.subplots(figsize=(7,2.6))
        ax_ts.plot(sub["Timestamp"], sub[metric])
        ax_ts.set_title(f"{ctry} — {metric} over time"); ax_ts.set_xlabel("Timestamp"); ax_ts.set_ylabel(metric); ax_ts.grid(alpha=0.3)
        st.pyplot(fig_ts, use_container_width=True)
else:
    st.info("No Timestamp column found; time-series view disabled.")

# --- Statistical Tests on GHI ---
st.subheader("🧪 Statistical Tests — Country Differences (GHI)")
if "GHI" in all_df.columns:
    groups = [all_df.loc[all_df["Country"]==c, "GHI"].dropna() for c in selected]
    if len(groups) >= 2 and all(len(g) >= 3 for g in groups):
        try:
            ftest = stats.f_oneway(*groups)
            kwtest = stats.kruskal(*groups)
            st.write(f"**ANOVA on GHI**: F = `{ftest.statistic:.3f}`, p = `{ftest.pvalue:.4g}`")
            st.write(f"**Kruskal–Wallis on GHI**: H = `{kwtest.statistic:.3f}`, p = `{kwtest.pvalue:.4g}`")
            if ftest.pvalue < 0.05 or kwtest.pvalue < 0.05:
                st.success("Significant differences detected (p < 0.05).")
            else:
                st.info("No significant differences detected at α = 0.05.")
        except Exception as e:
            st.warning(f"Tests failed: {e}")
    else:
        st.info("Not enough observations per selected country (need ≥ 3 each).")
else:
    st.warning("GHI column not found in the data.")


