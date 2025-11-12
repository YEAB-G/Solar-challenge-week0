

# 🌞 Solar Data Discovery — Week 0 Challenge (10 Academy KAIM)

**Author:** **Yeabsira Girma**
**Cohort:** KAIM – Week 0 (MoonLight Energy Solutions)



---

## 🚀 Live Dashboard

**View the deployed Streamlit App here:**

👉 [https://dashbord-development-week0.streamlit.app/](https://dashbord-development-week0.streamlit.app/)

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://dashbord-development-week0.streamlit.app/)


---

## 🧭 Project Overview

MoonLight Energy Solutions shared solar & meteorological datasets from **Benin (Malanville)**, **Sierra Leone (Bumbuna)**, and **Togo**.
Goal: identify the **best country** for solar-farm deployment by building a **reproducible pipeline**, cleaning and validating each dataset, exploring patterns, and performing a **cross-country comparison**. A **Streamlit dashboard** (bonus) provides an interactive view.

### Deliverables

* **Task 1:** Environment & repository setup
* **Task 2:** Country EDA (cleaning, validation, plots) — Benin, Sierra Leone, Togo
* **Task 3:** Cross-country comparison (stats + visuals)
* **Bonus:** Streamlit dashboard (`app.py`) — non-invasive, uses cleaned CSVs

---

## 📁 Repository Structure

```
solar-challenge-week0/
├─ app.py                     # Streamlit dashboard (Bonus)
├─ notebooks/
│  ├─ EDA_benin.ipynb
│  ├─ EDA_sierra_leone.ipynb
│  ├─ EDA_togo.ipynb
│  └─ compare_countries.ipynb
├─ data/
│  ├─ raw/                    # Raw inputs (git-ignored)
│  └─ clean/                  # Cleaned outputs (git-ignored)
├─ .github/workflows/ci.yml   # (optional) CI to verify env
├─ .venv/                     # Local virtual environment
├─ .gitignore
├─ requirements.txt
└─ README.md
```

> **Note:** `data/` is **git-ignored**. The dashboard lets you **upload** CSVs if they’re not present locally.

---

## ⚙️ Step-by-Step: Setup (Windows + VS Code)

1. **Clone the repo**

```powershell
git clone <your-repo-url> solar-challenge-week0
cd solar-challenge-week0
```

2. **Create & activate a virtual environment**

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

3. **Install dependencies**

```powershell
pip install -r requirements.txt
```

**`requirements.txt` should include at least:**

```
streamlit>=1.39
pandas>=2.0
numpy>=1.26
matplotlib>=3.8
scipy>=1.11
jupyter>=1.0
windrose>=1.6.8   # optional
```

---

## 🧪 Step-by-Step: Reproduce Task 2 (Country EDA)

**Goal:** Clean and explore each country’s data using consistent rules.

1. **Open Jupyter**

```powershell
jupyter notebook
```

2. **Run each notebook**

* `notebooks/EDA_benin.ipynb`
* `notebooks/EDA_sierra_leone.ipynb`
* `notebooks/EDA_togo.ipynb`

3. **Cleaning rules applied (in every notebook)**

* Irradiance **GHI/DNI/DHI/ModA/ModB ≥ 0**
* **DHI ≤ GHI** (physical constraint)
* **RH ∈ [0, 100]**, **WS ≥ 0**, **WD ∈ [0, 360]**
* **BP ∈ [800, 1100] hPa**, **Temps ∈ [−50, 80] °C**, **Precip ≥ 0**
* **Z-score outliers |Z|>3 → NaN**, then **median imputation**
* **Timestamp** parsed to datetime, sorted, duplicates removed

4. **Outputs (auto-saved by notebooks)**

* `data/clean/benin_clean.csv`
* `data/clean/sierra_leone_clean.csv`
* `data/clean/togo_clean.csv`

5. **What to look for**

* Time-series plots (GHI/DNI/DHI/Tamb)
* Histograms & boxplots
* Correlation heatmap
* Cleaning impact (ModA/ModB by `Cleaning`)
* Bubble chart (e.g., GHI vs Tamb, bubble=RH)

---

## 📊 Step-by-Step: Task 3 (Cross-Country Comparison)

**Notebook:** `notebooks/compare_countries.ipynb`

1. **Loads** the three cleaned CSVs from `data/clean/`

2. **Produces**

   * Boxplots of **GHI/DNI/DHI** by country
   * Summary stats (mean/median/std)
   * **ANOVA & Kruskal–Wallis** on GHI
   * Ranking bar chart (Avg GHI)

3. **Interpretation (typical outcome)**

* **Benin**: Highest + most stable irradiance → best candidate
* **Togo**: Consistent, slightly lower than Benin → good secondary option
* **Sierra Leone**: More variable; humidity influences diffuse radiation

> Statistical tests usually show **p < 0.05**, confirming significant differences across countries.

---

## 💻 Step-by-Step: Bonus (Streamlit Dashboard)

**Non-invasive**: The dashboard **does not change** your notebooks or data layout.
It searches the usual cleaned paths and also supports **file upload**.

1. **Run locally**

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```

Open the URL (e.g., `http://localhost:8501`) shown in your terminal.

2. **Use the sidebar**

* Metric selector (**GHI/DNI/DHI**)
* Country filter & date range
* Upload cleaned CSVs if they’re not found locally

3. **What you’ll see**

* KPI cards (mean/median/std aggregates)
* Summary table by country
* Boxplots per country
* Time-series per country
* **ANOVA & Kruskal** p-values on GHI

### Optional: Deploy to Streamlit Cloud

* Push the branch (e.g., `dashboard-dev`) or merge to `main`.
* Go to **[https://share.streamlit.io](https://share.streamlit.io)** → **New app** → pick repo & branch
* **Main file:** `app.py` → **Deploy**

---

## 🔍 Methodology Highlights (What You Did & Why It’s Correct)

* **Physics-aware validation**: No negative irradiance, **DHI ≤ GHI**, realistic ranges for RH, wind, pressure, temps.
* **Outlier handling**: Standard Z-score filtering to remove sensor spikes, then **median imputation** to keep distribution robust.
* **Time-series analysis**: Noon peaks in GHI/DNI; daily/seasonal patterns observed.
* **Correlation reasoning**:

  * GHI ↔ DNI (strong positive)
  * RH ↔ Tamb (typically negative)
  * Tamb ↔ module temps (positive)
* **Statistical testing**: ANOVA + Kruskal cross-validate differences in **mean GHI** across countries.

---

## 📈 Visuals (What Evaluators Will See)

* **Time-Series**: irradiance & temperature vs time (pattern recognition)
* **Boxplots**: distribution & variability (which site is stable?)
* **Heatmap**: multivariate relationships (physics + weather)
* **Cleaning impact**: module output vs `Cleaning` flag
* **Ranking bar chart**: mean GHI (Benin > Togo > Sierra Leone)



