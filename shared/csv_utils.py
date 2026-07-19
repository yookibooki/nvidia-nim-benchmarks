import csv
import os
from pathlib import Path


def write_benchmark_csv(output_path: str | Path, results: list, intelligence: dict[str, str] | None = None) -> None:
    if intelligence is None:
        intelligence = {}
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Model", "Provider", "Intelligence", "Latency", "TPS"])
        writer.writerows(r.row(intelligence) for r in results)


def read_benchmark_csv(csv_path: str | Path) -> list[dict]:
    if not os.path.exists(csv_path):
        return []
    with open(csv_path) as f:
        return list(csv.DictReader(f))


def merge_provider_csvs(provider_dirs: list[str | Path], output_path: str | Path) -> None:
    all_rows = []
    for provider_dir in provider_dirs:
        csv_path = Path(provider_dir) / "data" / "tps.csv"
        if csv_path.exists():
            all_rows.extend(read_benchmark_csv(csv_path))
    if not all_rows:
        print("[warn] No data found in any provider directories")
        return
    fieldnames = ["Model", "Provider", "Intelligence", "Latency", "TPS"]
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"Merged {len(all_rows)} rows from {len(provider_dirs)} providers into {output_path}")
