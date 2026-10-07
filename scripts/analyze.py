import argparse
import json

from common import RESULTS, ROOT, connect, files, sql, views


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", nargs="+", type=int, default=[2024, 2025, 2026])
    parser.add_argument("--only", nargs="+", choices=["coverage", "quality", "monthly", "hourly", "payments", "distribution", "zones", "comparable", "schema", "sample"])
    args = parser.parse_args()
    output = RESULTS / "_".join(map(str, args.years))
    output.mkdir(parents=True, exist_ok=True)
    con = connect()
    sources = files(args.years)
    views(con, sources)
    queries = {name: sql(name) for name in ["coverage", "quality", "monthly", "hourly", "payments", "distribution", "zones", "comparable"]}
    queries["schema"] = sql("schema").replace("{files}", "[" + ",".join("'" + p.replace("'", "''") + "'" for p in sources) + "]")
    queries["sample"] = sql("sample")
    for name, query in queries.items():
        if args.only and name not in args.only:
            continue
        frame = con.execute(query).fetchdf()
        frame.to_csv(output / f"{name}.csv", index=False)
        print(name, frame.shape, flush=True)
    (output / "execution.json").write_text(json.dumps({"years": args.years, "files": len(sources), "duckdb": con.execute("SELECT version()").fetchone()[0], "sources": [str(ROOT / p) for p in sources]}, indent=2), encoding="utf-8")
    con.close()


if __name__ == "__main__":
    main()
