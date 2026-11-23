from pathlib import Path

from datasets.prepare_data import (
    compute_repo_disjoint_split,
    normalize_fixture_tasks,
    normalize_swe_bench_rows,
    save_normalized_jsonl,
)


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
