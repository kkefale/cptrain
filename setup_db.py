#!/usr/bin/env python3
"""
setup_db.py — Parse cptrain.csv and load into SQLite database.
Run directly: python3 setup_db.py
"""

import csv
import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
CSV_PATH = BASE_DIR / "cptrain.csv"
DB_PATH  = BASE_DIR / "rainfall.db"

# (csv_col_idx, key, display_name, short_name, region, lat, lon)
STATIONS = [
    ( 1, "WEMMERSHOEK",  "Wemmershoek No.1 Dam",  "Wemmershoek",  "Franschhoek Mountains",  -33.891, 19.099),
    ( 3, "STEENBRAS",    "Steenbras No.1",          "Steenbras",    "Gordon's Bay",           -34.123, 18.849),
    ( 5, "VOELVLEI",     "Voëlvlei",                "Voëlvlei",     "Wellington",             -33.682, 19.034),
    ( 7, "THEEWATERS",   "Theewaterskloof",         "Theewaters",   "Overberg",               -34.055, 19.129),
    ( 9, "WOODHEAD",     "Woodhead Dam",            "Woodhead",     "Table Mountain",         -33.995, 18.420),
    (13, "NEWLANDS",     "Newlands",                "Newlands",     "Southern Suburbs",       -33.968, 18.463),
    (15, "WYNBERG",      "Wynberg",                 "Wynberg",      "Southern Suburbs",       -34.013, 18.472),
    (17, "CONSTANTIA",   "Constantia Nek",          "Const. Nek",   "Constantiaberg",         -34.027, 18.399),
    (19, "PLATTEKLOOF",  "Plattekloof",             "Plattekloof",  "Northern Suburbs",       -33.886, 18.578),
    (21, "BLKHTH_UPPER", "Blackheath Upper",        "Blkhth Upper", "Helderberg",             -33.924, 18.676),
    (23, "BLKHTH_LOWER", "Blackheath Lower",        "Blkhth Lower", "Helderberg",             -33.937, 18.683),
    (25, "GLEN_GARRY",   "Glen Garry",              "Glen Garry",   "Hout Bay Mountains",     -33.963, 18.445),
    (27, "TYGERBERG",    "Tygerberg",               "Tygerberg",    "Northern Suburbs",       -33.865, 18.625),
    (29, "FAURE",        "Faure",                   "Faure",        "Helderberg",             -34.052, 18.836),
    (31, "BROOKLANDS",   "Brooklands",              "Brooklands",   "Southern Suburbs",       -34.018, 18.487),
]


def setup_database(force: bool = False) -> int:
    """Parse CSV and create SQLite database. Returns number of rows inserted."""
    if DB_PATH.exists() and not force:
        print(f"✓ Database already exists at {DB_PATH}")
        return 0

    print(f"Building database from {CSV_PATH} …")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.executescript("""
        DROP TABLE IF EXISTS rainfall;
        DROP TABLE IF EXISTS stations;

        CREATE TABLE stations (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            key         TEXT    NOT NULL UNIQUE,
            name        TEXT    NOT NULL,
            short_name  TEXT,
            region      TEXT,
            lat         REAL,
            lon         REAL
        );

        CREATE TABLE rainfall (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            station_key TEXT    NOT NULL,
            date        TEXT    NOT NULL,   -- ISO YYYY-MM-DD
            rainfall_mm REAL    NOT NULL,
            UNIQUE (station_key, date)
        );

        CREATE INDEX idx_rf_date    ON rainfall(date);
        CREATE INDEX idx_rf_station ON rainfall(station_key);
        CREATE INDEX idx_rf_sd      ON rainfall(station_key, date);
    """)

    # Insert station metadata
    for col_idx, key, name, short, region, lat, lon in STATIONS:
        c.execute(
            "INSERT INTO stations (key, name, short_name, region, lat, lon) "
            "VALUES (?,?,?,?,?,?)",
            (key, name, short, region, lat, lon),
        )

    col_map = {col_idx: key for col_idx, key, *_ in STATIONS}
    rows_inserted = 0

    with open(CSV_PATH, "r", encoding="latin-1") as f:
        reader = csv.reader(f)
        next(reader)  # skip header row
        for row in reader:
            if not row or not row[0].strip():
                continue
            try:
                date_raw = row[0].strip().replace("-Sept-", "-Sep-")
                d = datetime.strptime(date_raw, "%d-%b-%y")
                date_str = d.strftime("%Y-%m-%d")
            except ValueError:
                continue

            for col_idx, key in col_map.items():
                if col_idx >= len(row):
                    continue
                val_str = row[col_idx].strip()
                if not val_str:
                    continue
                try:
                    val = float(val_str)
                    # Reject obvious monthly/cumulative totals
                    if val > 600:
                        continue
                    c.execute(
                        "INSERT OR REPLACE INTO rainfall "
                        "(station_key, date, rainfall_mm) VALUES (?,?,?)",
                        (key, date_str, val),
                    )
                    rows_inserted += 1
                except ValueError:
                    continue

    conn.commit()
    conn.close()
    print(f"✓ Database ready: {rows_inserted:,} readings across {len(STATIONS)} stations.")
    return rows_inserted


if __name__ == "__main__":
    import sys
    force = "--force" in sys.argv
    setup_database(force=force)
