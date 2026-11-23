from pathlib import Path
import pytest

from agent.patch_validator import PatchValidationError, validate_unified_diff
from sandbox.docker_runner import verify_patch_in_isolated_worktree


def test_patch_rejects_traversal_path(tmp_path: Path):
    evil_diff = """--- a/../../outside.py
+++ b/../../outside.py
@@ -1 +1 @@
-x = 1
+x = 2
"""
    with pytest.raises(PatchValidationError):
        validate_unified_diff(evil_diff, tmp_path)


def test_patch_fixes_discount_fixture_in_isolated_worktree():
    repo_dir = Path("datasets/curated/fixtures/fix_01_discount/repo")
    fix_diff = """--- a/shop/pricing.py
+++ b/shop/pricing.py
@@ -1,5 +1,5 @@
 def apply_discount(price: float, percent: float) -> float:
     if percent < 0 or percent > 100:
         raise ValueError("percent must be between 0 and 100")
     # Bug: applies percent as raw multiplier instead of percentage fraction
-    return round(price - percent, 2)
+    return round(price * (1.0 - percent / 100.0), 2)
"""
    result = verify_patch_in_isolated_worktree(repo_dir, fix_diff)
    assert result.diff_valid is True
    assert result.syntax_ok is True
    assert result.tests_passed is True
