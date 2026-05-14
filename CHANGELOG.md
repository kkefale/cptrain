# Changelog

All notable changes to this project are documented here.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);  
versioning follows [Semantic Versioning](https://semver.org/).

---

## [1.0.0] — 2026-05-14

### Added
- Initial public release
- **Climate Baseline tab** — station rankings with interactive bubble map, seasonal cycle, polar rose, box plots, statistics table
- **Year Explorer tab** — calendar heatmap, monthly bars with historical IQR envelope (floating bar range), cumulative spaghetti, ranked annual totals
- **Trends tab** — Z-score anomaly heatmap, linear trend lines, decadal analysis, seasonal shift, heavy-rain frequency, Joy Division ridgeline density
- **Extremes tab** — daily records, monthly anomaly heatmap with drought-year highlighting, extreme event clusters, dry-spell streaks
- Narrative prose blocks on all four tabs
- iOS Weather-inspired dark theme via custom CSS
- Auto-database creation from CSV on first run (`setup_db.py`)
- Streamlit Community Cloud deployment configuration

### Fixed
- September data missing: CSV uses `Sept` (4 chars); normalised to `Sep` before `strptime`
- Newlands station region corrected from "City Bowl" to "Southern Suburbs"
- Monthly anomaly heatmap drought-year outlines placed at correct y-coordinates (year values, not list indices)
- Monthly bar chart historical range replaced from closed-polygon fill to floating `go.Bar(base=)` traces, eliminating the September gap artefact
- Ridgeline chart year-filter threshold relaxed from 12 to 10 months for robustness

### Data
- Source: City of Cape Town Open Data Portal (<https://odp-cctegis.opendata.arcgis.com>)
- 15 monitoring stations, January 2000 – 2026
- 138 782 daily readings
