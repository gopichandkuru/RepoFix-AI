from dataclasses import dataclass
from pathlib import Path
import py_compile
import shutil
import subprocess
import sys
import tempfile

from agent.patch_validator import apply_unified_diff_to_text, validate_unified_diff
from repo_engine.ingest import is_ignored_file


@dataclass
class VerificationResult:
    diff_valid: bool
    syntax_ok: bool
    tests_passed: bool
    return_code: int
    stdout: str
    stderr: str
    error: str = ""


def _copy_clean_worktree(src_repo: Path, dst_repo: Path) -> None:
    for item in sorted(src_repo.rglob("*")):
        if item.is_symlink() or not item.is_file():
            continue
        rel = item.relative_to(src_repo)
        size_bytes = item.stat().st_size
        if is_ignored_file(rel, size_bytes):
            continue
        target = dst_repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)


def verify_patch_in_isolated_worktree(
    repo_dir: Path,
    raw_diff: str,
    timeout_sec: int = 15,
) -> VerificationResult:
    """Validate patch, apply in a clean temporary worktree, compile Python files, and run pytest."""
    repo_path = Path(repo_dir).resolve()
    try:
        parsed = validate_unified_diff(raw_diff, repo_path)
    except Exception as exc:
        return VerificationResult(
            diff_valid=False,
            syntax_ok=False,
            tests_passed=False,
            return_code=-1,
            stdout="",
            stderr="",
            error=str(exc),
        )

    with tempfile.TemporaryDirectory(prefix="repofix_worktree_") as tmp_dir:
        worktree = Path(tmp_dir) / "repo"
        _copy_clean_worktree(repo_path, worktree)

        try:
            for target_rel in parsed.target_files:
                target_path = worktree / target_rel
                if not target_path.exists():
                    raise FileNotFoundError(f"Target file not found in worktree: {target_rel}")
                original_text = target_path.read_text(encoding="utf-8")
                patched_text = apply_unified_diff_to_text(original_text, raw_diff)
                target_path.write_text(patched_text, encoding="utf-8")
        except Exception as exc:
            return VerificationResult(
                diff_valid=True,
                syntax_ok=False,
                tests_passed=False,
                return_code=-1,
                stdout="",
                stderr="",
                error=f"Patch apply failed: {exc}",
            )

        # Syntax check modified Python files
        try:
            for target_rel in parsed.target_files:
                if target_rel.endswith(".py"):
                    py_compile.compile(str(worktree / target_rel), doraise=True)
        except py_compile.PyCompileError as exc:
            return VerificationResult(
                diff_valid=True,
                syntax_ok=False,
                tests_passed=False,
                return_code=-1,
                stdout="",
                stderr=str(exc),
                error=f"Syntax check failed: {exc}",
            )

        try:
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", "-q"],
                cwd=str(worktree),
                capture_output=True,
                text=True,
                timeout=timeout_sec,
            )
            return VerificationResult(
                diff_valid=True,
                syntax_ok=True,
                tests_passed=(proc.returncode == 0),
                return_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
            )
        except subprocess.TimeoutExpired:
            return VerificationResult(
                diff_valid=True,
                syntax_ok=True,
                tests_passed=False,
                return_code=-1,
                stdout="",
                stderr="",
                error=f"Test execution timed out after {timeout_sec}s.",
            )
