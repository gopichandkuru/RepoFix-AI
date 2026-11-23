import importlib.util
from pathlib import Path
import sys

_spec = importlib.util.spec_from_file_location("local_prepare_data", "datasets/prepare_data.py")
_prep = importlib.util.module_from_spec(_spec)
sys.modules["local_prepare_data"] = _prep
_spec.loader.exec_module(_prep)

compute_repo_disjoint_split = _prep.compute_repo_disjoint_split
normalize_fixture_tasks = _prep.normalize_fixture_tasks
normalize_swe_bench_rows = _prep.normalize_swe_bench_rows
save_normalized_jsonl = _prep.save_normalized_jsonl


def test_normalize_fixtures_and_save_jsonl(tmp_path: Path):
    recs = normalize_fixture_tasks(Path("datasets/curated/fixtures"))
    assert len(recs) == 3
    out_file = save_normalized_jsonl(recs, tmp_path / "fixtures_norm.jsonl")
    assert len(out_file.read_text(encoding="utf-8").strip().splitlines()) == 3


def test_repo_disjoint_split_and_no_gold_leak():
    s1 = compute_repo_disjoint_split("scikit-learn/scikit-learn")
    s2 = compute_repo_disjoint_split("scikit-learn/scikit-learn")
    assert s1 == s2 and s1 in {"train", "val", "test"}

    rows = normalize_swe_bench_rows(
        [
            {
                "instance_id": "sklearn__sklearn-12345",
                "repo": "scikit-learn/scikit-learn",
                "base_commit": "deadbeef",
                "problem_statement": "Estimator fit fails on sparse input.",
                "patch": "diff --git ...",
            }
        ],
        include_gold_patch=False,
    )
    assert rows[0].diff == ""
    assert rows[0].split == s1
