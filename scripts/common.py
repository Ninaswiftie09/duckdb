from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "docs" / "results"
CLEAN = "pickup IS NOT NULL AND year(pickup) = source_year AND month(pickup) = source_month AND trip_distance > 0 AND trip_distance <= 100 AND duration_minutes > 0 AND duration_minutes <= 180 AND total_amount > 0 AND total_amount <= 500"


def sql(name):
    return (ROOT / "sql" / f"{name}.sql").read_text(encoding="utf-8")


def files(years):
    return sorted(p.as_posix() for p in (ROOT / "data" / "raw").glob("*/*/*.parquet") if int(p.parent.name) in years)


def connect(path=":memory:"):
    con = duckdb.connect(str(path))
    con.execute("SET threads=4")
    con.execute("SET memory_limit='2GB'")
    return con


def views(con, sources):
    if not sources:
        raise ValueError("No Parquet files found")
    quoted = "[" + ",".join("'" + p.replace("'", "''") + "'" for p in sources) + "]"
    con.execute("CREATE OR REPLACE VIEW trips_raw AS " + sql("normalize").replace("{files}", quoted))
    con.execute("CREATE OR REPLACE VIEW trips_clean AS SELECT * FROM trips_raw WHERE " + CLEAN)
