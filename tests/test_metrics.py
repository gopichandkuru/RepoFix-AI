from pathlib import Path
from evaluation.metrics import evaluate_retrieval_suite


def test_evaluate_retrieval_suite_on_fixtures():
    res = evaluate_retrieval_suite(Path("datasets/curated/fixtures"), use_graph=True, top_k=5)
    assert res["total_tasks"] == 3
    assert res["recall_at_1"] == 1.0
    assert len(res["rows"]) == 3
