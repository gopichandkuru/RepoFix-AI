import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import List

from repo_engine.ingest import ingest_directory


def run_fixture_baseline(fixtures_dir: Path, output_jsonl: Path) -> List[dict]:
    fixtures_dir = Path(fixtures_dir)
    output_jsonl = Path(output_jsonl)
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)

    records = []
    for task_file in sorted(fixtures_dir.glob("*/task.json")):
        task = json.loads(task_file.read_text(encoding="utf-8"))
        repo_dir = task_file.parent / "repo"

        start = time.perf_counter()
        ingested = ingest_directory(repo_dir)
        ingested_paths = [f.rel_path for f in ingested]
        file_present = task["expected_file"] in ingested_paths

        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            timeout=15,
        )
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

        record = {
            "fixture_id": task["fixture_id"],
            "expected_file": task["expected_file"],
            "expected_symbol": task["expected_symbol"],
            "ingested_file_count": len(ingested),
            "expected_file_ingested": file_present,
            "baseline_tests_passed": proc.returncode == 0,
            "baseline_return_code": proc.returncode,
            "elapsed_ms": elapsed_ms,
        }
        records.append(record)

    with open(output_jsonl, "w", encoding="utf-8") as out:
        for rec in records:
            out.write(json.dumps(rec) + "\n")

    return records


def main():
    parser = argparse.ArgumentParser(description="Run baseline evaluation on RepoFix fixtures.")
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        default=Path("datasets/curated/fixtures"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("evaluation/reports/baseline_fixtures.jsonl"),
    )
    args = parser.parse_args()

    results = run_fixture_baseline(args.fixtures_dir, args.output)
    print(f"Wrote {len(results)} baseline records to {args.output}")
    for row in results:
        print(json.dumps(row))


if __name__ == "__main__":
    main()
