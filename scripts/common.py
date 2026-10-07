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
    con.execute("SET preserve_insertion_order=false")
    return con


def views(con, sources):
    if not sources:
        raise ValueError("No Parquet files found")
    quoted = "[" + ",".join("'" + p.replace("'", "''") + "'" for p in sources) + "]"
    query = sql("normalize").replace("{files}", quoted)
    columns = {row[0] for row in con.execute(f"DESCRIBE SELECT * FROM read_parquet({quoted}, union_by_name=true)").fetchall()}
    for column in ["tpep_pickup_datetime", "tpep_dropoff_datetime", "lpep_pickup_datetime", "lpep_dropoff_datetime"]:
        if column not in columns:
            query = query.replace(column, "CAST(NULL AS TIMESTAMP)")
    if "cbd_congestion_fee" not in columns:
        query = query.replace("cbd_congestion_fee", "CAST(NULL AS DOUBLE) AS cbd_congestion_fee")
    con.execute("CREATE OR REPLACE VIEW trips_raw AS " + query)
    con.execute("CREATE OR REPLACE VIEW trips_clean AS SELECT * FROM trips_raw WHERE " + CLEAN)
