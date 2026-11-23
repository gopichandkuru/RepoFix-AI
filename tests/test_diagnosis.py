from pathlib import Path
from agent.diagnosis import run_retrieval_diagnosis


def test_diagnosis_returns_valid_schema_on_fixture():
    repo_dir = Path("datasets/curated/fixtures/fix_01_discount/repo")
    report = run_retrieval_diagnosis(
        repo_dir=repo_dir,
        issue_text="apply_discount returns 180.0 instead of 160.0 for 20% off 200.0",
        use_graph=True,
    )
    assert report.task == "bug_diagnosis"
    assert 0.0 <= report.confidence <= 1.0
    assert len(report.findings) >= 1
    assert report.findings[0].file == "shop/pricing.py"
