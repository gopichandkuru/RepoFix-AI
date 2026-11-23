import json
from pathlib import Path

from retrieval.bm25 import BM25RepoIndex, recall_at_k


def test_bm25_localizes_all_three_fixtures():
    fixtures_root = Path("datasets/curated/fixtures")
    hits_at_1 = 0
    total = 0

    for task_file in sorted(fixtures_root.glob("*/task.json")):
        task = json.loads(task_file.read_text(encoding="utf-8"))
        repo_dir = task_file.parent / "repo"

        idx = BM25RepoIndex()
        idx.index_repository(repo_dir)

        top_files = idx.top_files(task["issue"], top_k=3)
        hits_at_1 += recall_at_k(top_files, task["expected_file"], k=1)
        total += 1

    assert total == 3
    assert hits_at_1 == 3


def test_bm25_boosts_exact_symbol_match():
    fixtures_root = Path("datasets/curated/fixtures")
    repo_dir = fixtures_root / "fix_02_pagination" / "repo"

    idx = BM25RepoIndex()
    idx.index_repository(repo_dir)

    results = idx.search("Bug inside paginate function", top_k=3)
    assert results[0].symbol_name == "paginate"
    assert results[0].exact_symbol_hit is True
