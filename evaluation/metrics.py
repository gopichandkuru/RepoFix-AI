import json
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from agent.diagnosis import run_retrieval_diagnosis
from agent.patch_validator import apply_unified_diff_to_text
from retrieval.bm25 import BM25RepoIndex, recall_at_k
from repo_engine.graph_builder import RepoGraphBuilder
from retrieval.graph_expand import expand_candidates_with_graph
from sandbox.docker_runner import verify_patch_in_isolated_worktree


def build_fix_diff_for_fixture(fixture_dir: Path) -> Optional[str]:
    """Build a unified diff from a known fix reference if present in task.json."""
    task_file = Path(fixture_dir) / "task.json"
    if not task_file.exists():
        return None
    task = json.loads(task_file.read_text(encoding="utf-8"))
    fixed_file = task.get("fixed_file")
    target_rel = task.get("expected_file")
    if not fixed_file or not target_rel:
        return None

    orig_path = Path(fixture_dir) / "repo" / target_rel
    fixed_path = Path(fixture_dir) / fixed_file
    if not orig_path.exists() or not fixed_path.exists():
        return None

    orig_lines = orig_path.read_text(encoding="utf-8").splitlines(keepends=True)
    new_lines = fixed_path.read_text(encoding="utf-8").splitlines(keepends=True)

    import difflib
    diff_text = "".join(
        difflib.unified_diff(
            orig_lines,
            new_lines,
            fromfile=f"a/{target_rel}",
            tofile=f"b/{target_rel}",
        )
    )
    return diff_text if diff_text.strip() else None


def evaluate_retrieval_suite(
    fixtures_dir: Path,
    use_graph: bool = False,
    top_k: int = 5,
    candidate_diffs: Optional[Dict[str, str]] = None,
) -> Dict[str, object]:
    """Evaluate localization recall@1/@3/@5 and optional patch verification across fixtures."""
    fixtures_path = Path(fixtures_dir)
    task_files = sorted(fixtures_path.glob("*/task.json"))
    if not task_files:
        return {
            "mode": "bm25+graph" if use_graph else "bm25_only",
            "total_tasks": 0,
            "recall_at_1": 0.0,
            "recall_at_3": 0.0,
            "recall_at_5": 0.0,
            "patch_apply_rate": 0.0,
            "test_pass_rate": 0.0,
            "rows": [],
        }

    r1_hits = 0.0
    r3_hits = 0.0
    r5_hits = 0.0
    patch_attempted = 0
    patch_applied = 0
    tests_passed_count = 0
    rows: List[Dict[str, object]] = []

    for tf in task_files:
        task = json.loads(tf.read_text(encoding="utf-8"))
        repo_dir = tf.parent / "repo"
        fid = task["fixture_id"]
        expected_file = task["expected_file"]

        bm25 = BM25RepoIndex()
        bm25.index_repository(repo_dir)
        cands = bm25.search(task["issue"], top_k=top_k)

        if use_graph:
            graph = RepoGraphBuilder().build_from_repo(repo_dir)
            cands = expand_candidates_with_graph(graph, cands, max_neighbors=top_k)[:top_k]

        ranked_files: List[str] = []
        for c in cands:
            if c.file_path not in ranked_files:
                ranked_files.append(c.file_path)

        h1 = recall_at_k(ranked_files, expected_file, 1)
        h3 = recall_at_k(ranked_files, expected_file, 3)
        h5 = recall_at_k(ranked_files, expected_file, 5)
        r1_hits += h1
        r3_hits += h3
        r5_hits += h5

        diag = run_retrieval_diagnosis(repo_dir, task["issue"], use_graph=use_graph, top_k=top_k)

        applied = False
        passed = False
        diff_str = (candidate_diffs or {}).get(fid)
        if diff_str:
            patch_attempted += 1
            ver = verify_patch_in_isolated_worktree(repo_dir, diff_str)
            # Check if diff applied cleanly by checking syntax_ok or diff_valid + non-apply failure
            if ver.diff_valid and not ver.error.startswith("Patch apply failed"):
                applied = True
                patch_applied += 1
            if ver.tests_passed:
                passed = True
                tests_passed_count += 1

        rows.append(
            {
                "fixture_id": fid,
                "expected_file": expected_file,
                "top_files": ranked_files[:3],
                "recall@1": h1,
                "recall@3": h3,
                "recall@5": h5,
                "confidence": diag.confidence,
                "patch_applied": applied if diff_str else None,
                "tests_passed": passed if diff_str else None,
            }
        )

    n = len(task_files)
    return {
        "mode": "bm25+graph" if use_graph else "bm25_only",
        "total_tasks": n,
        "recall_at_1": round(r1_hits / n, 4),
        "recall_at_3": round(r3_hits / n, 4),
        "recall_at_5": round(r5_hits / n, 4),
        "patch_apply_rate": round(patch_applied / patch_attempted, 4) if patch_attempted else 0.0,
        "test_pass_rate": round(tests_passed_count / patch_attempted, 4) if patch_attempted else 0.0,
        "rows": rows,
    }
