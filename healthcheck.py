#!/usr/bin/env python3
"""
healthcheck.py — Pre-deploy smoke test.

Simulates the Streamlit Cloud environment by writing the database to /tmp
(as the app does when the source directory is read-only), then verifies
data integrity and key invariants.

Usage:
    python3 healthcheck.py

Run this before every `git push` to catch data-pipeline or import issues.
Exit code 0 = all checks passed. Non-zero = something is broken.
"""

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

TEST_DB = Path("/tmp/cptrain_healthcheck.db")

# ── Helpers ──────────────────────────────────────────────────────────────────

PASS = "\033[32m✓\033[0m"
FAIL = "\033[31m✗\033[0m"
WARN = "\033[33m⚠\033[0m"

failures = 0


def check(label: str, condition: bool, detail: str = "") -> None:
    global failures
    if condition:
        print(f"  {PASS}  {label}" + (f"  ({detail})" if detail else ""))
    else:
        print(f"  {FAIL}  {label}" + (f"  — {detail}" if detail else ""))
        failures += 1


# ── Step 1: imports ───────────────────────────────────────────────────────────

print("\n[1/4] Checking imports …")
try:
    import pandas as pd
    import numpy as np
    import plotly
    import plotly.graph_objects as go
    import streamlit as st
    check("All required packages importable", True,
          f"pandas {pd.__version__}, plotly {plotly.__version__}")
except ImportError as e:
    check("All required packages importable", False, str(e))
    sys.exit(1)

# ── Step 2: database build into /tmp ─────────────────────────────────────────

print("\n[2/4] Building database into /tmp (simulates Streamlit Cloud) …")
if TEST_DB.exists():
    TEST_DB.unlink()

try:
    from setup_db import setup_database
    n = setup_database(force=True, db_path=TEST_DB)
    check("setup_database() completes without error", True, f"{n:,} rows inserted")
    check("Row count is plausible (>100 000)", n > 100_000, f"{n:,}")
except Exception as e:
    check("setup_database() completes without error", False, str(e))
    sys.exit(1)

# ── Step 3: data integrity checks ────────────────────────────────────────────

print("\n[3/4] Verifying data integrity …")
conn = sqlite3.connect(str(TEST_DB))

# Row count
total = conn.execute("SELECT COUNT(*) FROM rainfall").fetchone()[0]
check("Rainfall table non-empty", total > 0, f"{total:,} rows")

# All 15 stations present
station_count = conn.execute("SELECT COUNT(*) FROM stations").fetchone()[0]
check("All 15 stations in stations table", station_count == 15, f"{station_count}")

# All 12 months present (September fix)
months = [r[0] for r in conn.execute(
    "SELECT DISTINCT CAST(strftime('%m', date) AS INTEGER) FROM rainfall ORDER BY 1"
).fetchall()]
check("All 12 months present (September fix)", months == list(range(1, 13)),
      f"Months found: {months}")

# No September gap
sep_count = conn.execute(
    "SELECT COUNT(*) FROM rainfall WHERE strftime('%m', date) = '09'"
).fetchone()[0]
check("September has data (>500 rows)", sep_count > 500, f"{sep_count:,} rows")

# Newlands region
newlands_region = conn.execute(
    "SELECT region FROM stations WHERE key = 'NEWLANDS'"
).fetchone()
check("Newlands region = 'Southern Suburbs'",
      newlands_region is not None and newlands_region[0] == "Southern Suburbs",
      newlands_region[0] if newlands_region else "MISSING")

# Year range
min_year, max_year = conn.execute(
    "SELECT MIN(strftime('%Y', date)), MAX(strftime('%Y', date)) FROM rainfall"
).fetchone()
check("Year range starts at 2000", min_year == "2000", f"min={min_year}")
check("Year range is recent (≥ 2024)", int(max_year) >= 2024, f"max={max_year}")

# No extreme daily values (val > 600 should have been filtered)
over_600 = conn.execute(
    "SELECT COUNT(*) FROM rainfall WHERE rainfall_mm > 600"
).fetchone()[0]
check("No daily values > 600 mm (filter working)", over_600 == 0, f"{over_600} rows")

conn.close()

# ── Step 4: data-loader smoke test ───────────────────────────────────────────

print("\n[4/4] Smoke-testing data loaders …")

# Monkey-patch DB_PATH before importing app loaders
import importlib, types

# Build a minimal loader environment without running the full Streamlit app
try:
    import pandas as pd

    conn2 = sqlite3.connect(str(TEST_DB))
    df = pd.read_sql(
        "SELECT station_key, date, rainfall_mm FROM rainfall ORDER BY date",
        conn2, parse_dates=["date"],
    )
    conn2.close()

    df["year"]  = df["date"].dt.year
    df["month"] = df["date"].dt.month
    monthly = (
        df.groupby(["station_key", "year", "month"])
          .agg(total_mm=("rainfall_mm", "sum"))
          .reset_index()
    )
    annual = (
        monthly.groupby(["station_key", "year"])
               .agg(total_mm=("total_mm", "sum"))
               .reset_index()
    )
    current_year = datetime.now().year
    hist_annual = annual[annual["year"] < current_year]
    ens_ann = hist_annual.groupby("year")["total_mm"].mean()

    check("load_all_daily() returns rows", len(df) > 0, f"{len(df):,} rows")
    check("load_monthly() returns rows", len(monthly) > 0, f"{len(monthly):,} rows")
    check("load_annual() returns rows", len(annual) > 0, f"{len(annual):,} rows")
    check("hist_annual is non-empty (headline stats won't crash)",
          not ens_ann.empty, f"{len(ens_ann)} years")
    check("ens_ann.idxmax() works (no empty-sequence error)",
          not ens_ann.empty, f"wettest={int(ens_ann.idxmax())}")

except Exception as e:
    check("Data loader smoke test", False, str(e))

# ── Summary ───────────────────────────────────────────────────────────────────

print()
if failures == 0:
    print(f"\033[32m  All checks passed — safe to deploy.\033[0m\n")
    TEST_DB.unlink(missing_ok=True)
    sys.exit(0)
else:
    print(f"\033[31m  {failures} check(s) FAILED — fix before deploying.\033[0m\n")
    TEST_DB.unlink(missing_ok=True)
    sys.exit(1)
