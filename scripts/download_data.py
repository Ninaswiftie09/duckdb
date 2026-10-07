import argparse
import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page"
BASE = "https://d37ci6vzurychx.cloudfront.net/trip-data"


def session():
    client = requests.Session()
    client.headers['User-Agent'] = 'Mozilla/5.0'
    client.mount("https://", HTTPAdapter(max_retries=Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])))
    return client


def acquire(item):
    taxi, year, month = item
    name = f"{taxi}_tripdata_{year}-{month}.parquet"
    path = ROOT / "data" / "raw" / taxi / year / name
    path.parent.mkdir(parents=True, exist_ok=True)
    status = "existing"
    if not path.exists():
        temporary = path.with_suffix(".part")
        try:
            with session().get(f"{BASE}/{name}", stream=True, timeout=(20, 120)) as response:
                response.raise_for_status()
                with temporary.open("wb") as output:
                    for block in response.iter_content(1024 * 1024):
                        output.write(block)
                expected = response.headers.get("Content-Length")
                if expected and temporary.stat().st_size != int(expected):
                    raise ValueError(f"Incomplete download: {name}")
            pq.ParquetFile(temporary)
            temporary.replace(path)
            status = "downloaded"
        finally:
            temporary.unlink(missing_ok=True)
    metadata = pq.ParquetFile(path).metadata
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    print(f"{status}: {name} ({metadata.num_rows:,} rows)", flush=True)
    return {"taxi": taxi, "year": int(year), "month": int(month), "file": path.relative_to(ROOT).as_posix(), "url": f"{BASE}/{name}", "status": status, "bytes": path.stat().st_size, "rows": metadata.num_rows, "sha256": digest}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", nargs="+", type=int, default=[2026])
    parser.add_argument("--taxi", choices=["all", "yellow", "green"], default="all")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    response = session().get(SOURCE, timeout=60)
    response.raise_for_status()
    published = set(re.findall(r"(yellow|green)_tripdata_(\d{4})-(\d{2})\.parquet", response.text))
    wanted = sorted(item for item in published if int(item[1]) in args.years and (args.taxi == "all" or item[0] == args.taxi))
    for year in args.years:
        for taxi in (["yellow", "green"] if args.taxi == "all" else [args.taxi]):
            months = [int(m) for t, y, m in wanted if t == taxi and int(y) == year]
            if not months or (year < 2026 and len(months) != 12):
                raise ValueError(f"Incomplete published inventory: {taxi} {year}: {months}")
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        files = list(executor.map(acquire, wanted))
    manifest = {"checked_at_utc": datetime.now(timezone.utc).isoformat(), "source": SOURCE, "years": args.years, "expected_files": len(wanted), "verified_files": len(files), "files": files, "unpublished": [f"{taxi} {year}-{month:02d}" for year in args.years for taxi in (["yellow", "green"] if args.taxi == "all" else [args.taxi]) for month in range(1, 13) if (taxi, str(year), f"{month:02d}") not in published]}
    output = ROOT / "docs" / f"download_{'_'.join(map(str, args.years))}.json"
    output.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Verified {len(files)}/{len(wanted)} published files. Manifest: {output}")


if __name__ == "__main__":
    main()
