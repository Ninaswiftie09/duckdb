import argparse
import json
import platform
import statistics
import time

import pandas as pd
import duckdb

from common import CLEAN, RESULTS, ROOT, connect, files, sql, views


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", nargs="+", type=int, default=[2024, 2026])
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    RESULTS.mkdir(parents=True, exist_ok=True)
    sources = sorted(files(args.years), key=lambda p: (p.split('/')[-2], p.split('/')[-1].split('_')[-1], p.split('/')[-3]))
    records = []
    builds = []
    for size in sorted(set([2, min(12, len(sources)), len(sources)])):
        subset = sources[:size]
        path = ROOT / "data" / "processed" / "benchmark.duckdb"
        con = connect(path)
        views(con, subset)
        print(f"Materializing {size} files", flush=True)
        start = time.perf_counter()
        con.execute("CREATE OR REPLACE TABLE trips_materialized AS SELECT * FROM trips_raw")
        build = time.perf_counter() - start
        rows = con.execute("SELECT count(*) FROM trips_materialized").fetchone()[0]
        print(f"Materialized {rows:,} rows in {build:.3f} seconds", flush=True)
        builds.append({"files": size, "rows": rows, "materialization_seconds": build})
        for name in ["monthly", "hourly", "payments"]:
            query = sql(name)
            timings = {"parquet": [], "duckdb": []}
            outputs = {}
            for mode in timings:
                source = "trips_raw" if mode == "parquet" else "trips_materialized"
                con.execute("CREATE OR REPLACE VIEW trips_clean AS SELECT * FROM " + source + " WHERE " + CLEAN)
                outputs[mode] = con.execute(query).fetchdf()
            pd.testing.assert_frame_equal(outputs["parquet"], outputs["duckdb"], check_exact=False, rtol=1e-9, atol=1e-7)
            for repeat in range(args.repeats):
                for mode in (["parquet", "duckdb"] if repeat % 2 == 0 else ["duckdb", "parquet"]):
                    source = "trips_raw" if mode == "parquet" else "trips_materialized"
                    con.execute("CREATE OR REPLACE VIEW trips_clean AS SELECT * FROM " + source + " WHERE " + CLEAN)
                    start = time.perf_counter()
                    con.execute(query).fetchall()
                    elapsed = time.perf_counter() - start
                    timings[mode].append(elapsed)
                    records.append({"files": size, "rows": rows, "query": name, "mode": mode, "repeat": repeat + 1, "seconds": elapsed})
            print(size, name, {mode: round(statistics.median(values), 3) for mode, values in timings.items()}, flush=True)
        con.close()
    frame = pd.DataFrame(records)
    frame.to_csv(RESULTS / "benchmark_runs.csv", index=False)
    frame.groupby(["files", "rows", "query", "mode"]).seconds.agg(["median", "min", "max"]).reset_index().to_csv(RESULTS / "benchmark_summary.csv", index=False)
    pd.DataFrame(builds).to_csv(RESULTS / "materialization.csv", index=False)
    (RESULTS / "benchmark_environment.json").write_text(json.dumps({"platform": platform.platform(), "python": platform.python_version(), "duckdb": duckdb.__version__, "years": args.years, "repeats": args.repeats, "threads": 4, "memory_limit": "2GB", "cache": "warm, one untimed run per query and mode; alternating timed order", "subsets": "file prefixes sorted by year, month, taxi", "sources": sources}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
