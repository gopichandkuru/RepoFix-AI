from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field

from retrieval.bm25 import BM25RepoIndex
from retrieval.graph_expand import expand_candidates_with_graph
from repo_engine.graph_builder import RepoGraphBuilder


class FindingItem(BaseModel):
    file: str
    symbol: Optional[str] = None
    line_hint: Optional[int] = None
    severity: str = "medium"
    evidence: str
    recommendation: str


class DiagnosisReport(BaseModel):
    task: str = "bug_diagnosis"
    summary: str
    confidence: float = Field(ge=0.0, le=1.0)
    findings: List[FindingItem] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    patch: str = ""


def run_retrieval_diagnosis(
    repo_dir: Path,
    issue_text: str,
    use_graph: bool = True,
    top_k: int = 5,
) -> DiagnosisReport:
    """Build a structured bug diagnosis report from retrieved code & graph evidence."""
    repo_path = Path(repo_dir).resolve()
    bm25 = BM25RepoIndex()
    bm25.index_repository(repo_path)

    candidates = bm25.search(issue_text, top_k=top_k)
    if use_graph:
        graph = RepoGraphBuilder().build_from_repo(repo_path)
        candidates = expand_candidates_with_graph(graph, candidates, max_neighbors=top_k)[:top_k]

    if not candidates:
        return DiagnosisReport(
            summary="No matching files or symbols found for the reported issue.",
            confidence=0.1,
            findings=[],
            missing_information=["Provide a stack trace, symbol name, or test failure output."],
        )

    findings: List[FindingItem] = []
    for idx, cand in enumerate(candidates[:3]):
        sev = "high" if idx == 0 else "medium"
        sym_label = cand.symbol_name or "(module level)"
        findings.append(
            FindingItem(
                file=cand.file_path,
                symbol=cand.symbol_name,
                line_hint=cand.start_line,
                severity=sev,
                evidence=f"Matched query terms with retrieval score {cand.score} in {cand.file_path} ({sym_label}).",
                recommendation=f"Inspect {cand.file_path} around line {cand.start_line or 1} and verify boundary/logic handling against tests.",
            )
        )

    top_cand = candidates[0]
    top_conf = round(min(0.9, max(0.25, top_cand.score / 10.0)), 2)
    missing = [] if len(issue_text.strip()) >= 25 else ["Add fuller stack trace or expected vs. actual behavior."]

    return DiagnosisReport(
        summary=f"Top candidate defect location is {top_cand.file_path} ({top_cand.symbol_name or 'file'}) based on {'BM25 + Graph-RAG' if use_graph else 'BM25'} retrieval.",
        confidence=top_conf,
        findings=findings,
        missing_information=missing,
    )
