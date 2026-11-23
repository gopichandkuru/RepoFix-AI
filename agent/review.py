from pathlib import Path
import re
from typing import List, Optional
from pydantic import BaseModel, Field

from retrieval.bm25 import BM25RepoIndex


class ReviewFinding(BaseModel):
    file: str
    line: Optional[int] = None
    severity: str = "medium"  # "low" | "medium" | "high"
    title: str
    explanation: str
    suggested_fix: str


class PRReviewReport(BaseModel):
    task: str = "pr_review"
    summary: str
    findings: List[ReviewFinding] = Field(default_factory=list)


def review_pr_diff(diff_text: str, repo_dir: Optional[Path] = None, top_k: int = 3) -> PRReviewReport:
    """Analyze a unified PR diff for common risks and cross-reference repository context."""
    if not diff_text or not diff_text.strip():
        return PRReviewReport(
            summary="Empty diff provided; no review findings generated.",
            findings=[],
        )

    findings: List[ReviewFinding] = []
    current_file = "unknown"
    line_num = 0

    bm25: Optional[BM25RepoIndex] = None
    if repo_dir and Path(repo_dir).exists() and Path(repo_dir).is_dir():
        bm25 = BM25RepoIndex()
        bm25.index_repository(Path(repo_dir))

    for raw_line in diff_text.splitlines():
        if raw_line.startswith("+++ "):
            m = re.match(r"^\+\+\+\s+(?:b/)?([^\t\n]+)", raw_line)
            if m:
                current_file = m.group(1).strip()
            continue
        hunk = re.match(r"^@@\s+-\d+(?:,\d+)?\s+\+(\d+)(?:,\d+)?\s+@@", raw_line)
        if hunk:
            line_num = int(hunk.group(1))
            continue

        if raw_line.startswith("+") and not raw_line.startswith("+++"):
            added_code = raw_line[1:]
            stripped = added_code.strip()

            if "except:" in stripped or re.search(r"\bexcept\s+Exception\s*:", stripped):
                findings.append(
                    ReviewFinding(
                        file=current_file,
                        line=line_num,
                        severity="medium",
                        title="Broad exception handler introduced",
                        explanation="Catching bare Exception or all exceptions can hide real bugs or mask system errors.",
                        suggested_fix="Catch specific expected exception types and log unexpected failures explicitly.",
                    )
                )

            if re.search(r"\b(eval|exec)\s*\(", stripped):
                findings.append(
                    ReviewFinding(
                        file=current_file,
                        line=line_num,
                        severity="high",
                        title="Dynamic code execution detected",
                        explanation="Use of eval() or exec() on untrusted inputs creates code-injection risks.",
                        suggested_fix="Replace dynamic evaluation with safe parsing or explicit dispatch mappings.",
                    )
                )

            if "TODO" in stripped or "FIXME" in stripped:
                findings.append(
                    ReviewFinding(
                        file=current_file,
                        line=line_num,
                        severity="low",
                        title="Unresolved TODO/FIXME marker in added code",
                        explanation="Incomplete logic or placeholders may ship unintentionally if left unresolved.",
                        suggested_fix="Complete the implementation or track a follow-up issue before merging.",
                    )
                )

            line_num += 1
        elif not raw_line.startswith("-"):
            line_num += 1

    related_info = ""
    if bm25 and current_file != "unknown":
        cands = bm25.search(current_file, top_k=top_k)
        if cands:
            related_info = f" Indexed repo context checked around `{current_file}`."

    summary = (
        f"Reviewed diff across `{current_file}`: found {len(findings)} potential finding(s)."
        + related_info
    )
    return PRReviewReport(task="pr_review", summary=summary, findings=findings)
