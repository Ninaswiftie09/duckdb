import json

import pandas as pd

from common import RESULTS, ROOT


def main():
    manifests = [json.loads((ROOT / "docs" / name).read_text(encoding="utf-8")) for name in ["download_2026.json", "download_2024_2026.json", "download_2024_2025_2026.json"]]
    for previous, current in zip(manifests, manifests[1:]):
        old = {item["file"]: item["sha256"] for item in previous["files"]}
        new = {item["file"]: item["sha256"] for item in current["files"]}
        assert all(new[path] == digest for path, digest in old.items())
    manifest = manifests[-1]
    output = RESULTS / "2024_2025_2026"
    coverage = pd.read_csv(output / "coverage.csv")
    expected_rows = sum(item["rows"] for item in manifest["files"])
    assert coverage.rows.sum() == expected_rows
    assert coverage.files.sum() == manifest["verified_files"] == manifest["expected_files"]
    assert set(coverage.source_year) == {2024, 2025, 2026}
    assert set(coverage.taxi) == {"yellow", "green"}
    totals = {name: int(pd.read_csv(output / f"{name}.csv").trips.sum()) for name in ["monthly", "hourly", "payments"]}
    assert len(set(totals.values())) == 1
    assert totals["monthly"] <= expected_rows
    benchmark = pd.read_csv(RESULTS / "benchmark_runs.csv")
    assert len(benchmark) == 54
    assert len(benchmark.files.unique()) == 3
    assert set(benchmark["mode"]) == {"parquet", "duckdb"}
    assert set(benchmark["query"]) == {"monthly", "hourly", "payments"}
    assert benchmark.seconds.gt(0).all()
    dashboard = json.loads((ROOT / "docs" / "dashboard" / "metabase_validation.json").read_text(encoding="utf-8"))
    assert len(dashboard["cards"]) == 6
    assert all(card["status"] == "completed" and card["rows"] > 0 for card in dashboard["cards"])
    (ROOT / "docs" / "validation.json").write_text(json.dumps({"published_files": manifest["verified_files"], "raw_rows": expected_rows, "clean_rows": totals["monthly"], "excluded_rows": expected_rows - totals["monthly"], "incremental_hashes_unchanged": True, "indicator_totals_match": True, "benchmark_timed_runs": len(benchmark), "metabase_cards_verified": len(dashboard["cards"])}, indent=2), encoding="utf-8")
    print("Lab verification passed")


if __name__ == "__main__":
    main()
