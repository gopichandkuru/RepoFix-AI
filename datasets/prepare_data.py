from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional

DEFAULT_HF_DATASET = "SWE-bench/SWE-bench_Lite"


@dataclass
class NormalizedTaskRecord:
    example_id: str
    task_type: str  # "repair" | "review" | "localization"
    source_dataset: str
    source_url: str
    repo: str
    commit: str
    language: str
    issue: str
    files_context: List[str]
    diff: str
    tests: List[str]
    quality_checks: Dict[str, object]
    split: str  # "train" | "val" | "test"


def compute_repo_disjoint_split(
    repo_name: str, val_ratio: float = 0.15, test_ratio: float = 0.15
) -> str:
    """Deterministically assign a repository to train/val/test to prevent repo leakage."""
    digest = hashlib.sha256(repo_name.encode("utf-8")).hexdigest()
    bucket = int(digest[:8], 16) / 0xFFFFFFFF
    if bucket < test_ratio:
        return "test"
    if bucket < test_ratio + val_ratio:
        return "val"
    return "train"


def normalize_fixture_tasks(fixtures_dir: Path) -> List[NormalizedTaskRecord]:
    """Normalize local curated fixture tasks into the blueprint schema."""
    records: List[NormalizedTaskRecord] = []
    for task_file in sorted(Path(fixtures_dir).glob("*/task.json")):
        task = json.loads(task_file.read_text(encoding="utf-8"))
        fid = task["fixture_id"]
        expected_file = task.get("expected_file", "")
        test_file = task.get("test_file", "")

        records.append(
            NormalizedTaskRecord(
                example_id=f"fixture_{fid}",
                task_type="repair",
                source_dataset="curated_fixtures_v0",
                source_url="local://datasets/curated/fixtures",
                repo=f"local/{fid}",
                commit="working-tree",
                language="python",
                issue=task.get("issue", ""),
                files_context=[f for f in [expected_file, test_file] if f],
                diff="",
                tests=[test_file] if test_file else [],
                quality_checks={
                    "patch_applies": False,
                    "tests_run": True,
                    "license_reviewed": True,
                },
                split="test",
            )
        )
    return records


def normalize_swe_bench_rows(
    rows: Iterable[Dict[str, object]],
    source_dataset: str = DEFAULT_HF_DATASET,
    include_gold_patch: bool = False,
    limit: Optional[int] = None,
) -> List[NormalizedTaskRecord]:
    """Normalize SWE-bench rows while excluding gold patches by default."""
    records: List[NormalizedTaskRecord] = []
    for idx, row in enumerate(rows):
        if limit is not None and idx >= limit:
            break
        repo = str(row.get("repo", "unknown/repo"))
        instance_id = str(row.get("instance_id", f"row_{idx}"))
        base_commit = str(row.get("base_commit", ""))
        problem_statement = str(row.get("problem_statement", ""))
        patch_text = str(row.get("patch", "")) if include_gold_patch else ""

        records.append(
            NormalizedTaskRecord(
                example_id=instance_id,
                task_type="repair",
                source_dataset=source_dataset,
                source_url=f"https://huggingface.co/datasets/{source_dataset}",
                repo=repo,
                commit=base_commit,
                language="python",
                issue=problem_statement,
                files_context=[],
                diff=patch_text,
                tests=[],
                quality_checks={
                    "patch_applies": False,
                    "tests_run": False,
                    "license_reviewed": False,
                },
                split=compute_repo_disjoint_split(repo),
            )
        )
    return records


def save_normalized_jsonl(records: List[NormalizedTaskRecord], out_path: Path) -> Path:
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(asdict(r)) + "\n")
    return out_file
