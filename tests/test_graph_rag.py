from pathlib import Path

from repo_engine.graph_builder import RepoGraphBuilder
from retrieval.bm25 import BM25RepoIndex
from retrieval.graph_expand import expand_candidates_with_graph


def test_graph_expansion_surfaces_imported_module(tmp_path: Path):
    repo = tmp_path / "service_repo"
    (repo / "pkg").mkdir(parents=True)
    (repo / "pkg" / "helper.py").write_text(
        "def compute_tax(amount):\n    return amount * 0.18\n",
        encoding="utf-8",
    )
    (repo / "pkg" / "billing.py").write_text(
        "from pkg.helper import compute_tax\n\ndef invoice_total(amount):\n    return amount + compute_tax(amount)\n",
        encoding="utf-8",
    )

    bm25 = BM25RepoIndex()
    bm25.index_repository(repo)
    seeds = bm25.search("invoice_total calculation", top_k=2)

    graph = RepoGraphBuilder().build_from_repo(repo)
    expanded = expand_candidates_with_graph(graph, seeds, max_neighbors=3)
    expanded_files = [c.file_path for c in expanded]

    assert "pkg/billing.py" in expanded_files
    assert "pkg/helper.py" in expanded_files
