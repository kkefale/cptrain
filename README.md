# Cape Town Rainfall Atlas 🌧️

An interactive, iOS Weather-inspired dashboard exploring **25+ years of daily rainfall** across **15 City of Cape Town monitoring stations** (2000–2026).

[![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e.svg)](LICENSE)
[![Data: City of Cape Town](https://img.shields.io/badge/Data-City%20of%20Cape%20Town%20ODP-0EA5E9)](https://odp-cctegis.opendata.arcgis.com)

---

## Features

| Tab | What you get |
|-----|-------------|
| **Climate Baseline** | Station rankings + bubble map, seasonal cycle, polar rose, box plots, statistics table |
| **Year Explorer** | Year-by-year deep dives — calendar heatmap, monthly bars with historical IQR envelope, cumulative spaghetti, ranked totals |
| **Trends** | Z-score anomaly heatmap, linear trend lines, decadal analysis, seasonal shift, heavy-rain frequency, Joy Division ridgeline density |
| **Extremes** | Daily records, monthly anomaly heatmap, extreme event clusters, dry-spell streaks |

All panels feature narrative text explaining what the data means in plain language, and a cohesive iOS-inspired dark theme throughout.

---

## Quick Start

```bash
git clone https://github.com/<your-username>/cptrain.git
cd cptrain
pip install -r requirements.txt
streamlit run app.py
```

The SQLite database (`rainfall.db`) is built automatically from `cptrain.csv` on first run. No manual setup required.

To force a rebuild of the database:

```bash
python3 setup_db.py --force
```

---

## Project Structure

```
cptrain/
├── app.py              # Main Streamlit application (~1 850 lines)
├── setup_db.py         # CSV → SQLite ingestion script
├── cptrain.csv         # Source data (City of Cape Town, latin-1 encoded)
├── requirements.txt    # Python dependencies
├── .streamlit/
│   └── config.toml     # Streamlit theme + server configuration
├── LICENSE             # MIT licence (code)
└── README.md
```

`rainfall.db` is generated at runtime and is excluded from version control (see `.gitignore`).

---

## Data Source

Rainfall data is sourced from the **City of Cape Town Open Data Portal**:

- **Publisher:** City of Cape Town — Spatial Planning and Environment  
- **Portal:** <https://odp-cctegis.opendata.arcgis.com>  
- **Coverage:** 15 gauging stations across the greater Cape Town metropolitan area  
- **Period:** January 2000 – 2026 (monthly totals per station)  
- **Licence:** [City of Cape Town Open Data Licence](https://odp-cctegis.opendata.arcgis.com/pages/terms-of-use)

> The source data is used here for research, education, and public interest purposes. No claim of ownership over the underlying data is made.

---

## Deployment (Streamlit Community Cloud)

1. Push this repository to GitHub (the database is excluded; the CSV is included).  
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**.  
3. Set **Main file path** to `app.py`.  
4. Click **Deploy** — the database is auto-built from the CSV on the first run.

No secrets or environment variables are required.

---

## Requirements

| Package | Version |
|---------|---------|
| streamlit | ≥ 1.32.0 |
| plotly | ≥ 5.18.0 |
| pandas | ≥ 2.0.0 |
| numpy | ≥ 1.24.0 |

---

## Versioning

This project follows [Semantic Versioning](https://semver.org/).  
See [CHANGELOG.md](CHANGELOG.md) for release history.

Current version: **1.0.0**

---

## Licence

**Code** — [MIT Licence](LICENSE) © 2026  
**Data** — City of Cape Town Open Data Licence (see [Data Source](#data-source) above)
