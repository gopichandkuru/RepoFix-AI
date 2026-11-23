from pathlib import Path
import streamlit as st

from agent.patch_validator import PatchValidationError, validate_unified_diff
from sandbox.docker_runner import verify_patch_in_isolated_worktree

st.title("Patch Lab")
st.caption("Patches are validated and tested in an isolated temporary worktree before any manual apply.")

default_repo = st.session_state.get("repo_path") or "datasets/curated/fixtures/fix_01_discount/repo"
repo_input = st.text_input("Repository Path", value=default_repo)

sample_diff = """--- a/shop/pricing.py
+++ b/shop/pricing.py
@@ -1,5 +1,5 @@
 def apply_discount(price: float, percent: float) -> float:
     if percent < 0 or percent > 100:
         raise ValueError("percent must be between 0 and 100")
     # Bug: applies percent as raw multiplier instead of percentage fraction
-    return round(price - percent, 2)
+    return round(price * (1.0 - percent / 100.0), 2)
"""

diff_text = st.text_area("Unified Diff Patch", value=sample_diff, height=220)

col1, col2 = st.columns(2)
with col1:
    if st.button("Validate & Run Tests in Isolated Worktree"):
        p = Path(repo_input)
        if not p.exists() or not p.is_dir():
            st.error("Invalid repository directory.")
        else:
            res = verify_patch_in_isolated_worktree(p, diff_text)
            st.write(f"- **Diff Valid:** `{res.diff_valid}`")
            st.write(f"- **Syntax OK:** `{res.syntax_ok}`")
            st.write(f"- **Tests Passed:** `{res.tests_passed}` (exit code `{res.return_code}`)")
            if res.error:
                st.error(res.error)
            if res.stdout:
                st.code(res.stdout, language="text")
            if res.stderr:
                st.code(res.stderr, language="text")

with col2:
    if st.button("Apply Patch to Target Repo"):
        p = Path(repo_input)
        try:
            parsed = validate_unified_diff(diff_text, p)
            for rel in parsed.target_files:
                target = p / rel
                updated = apply_text = None
                from agent.patch_validator import apply_unified_diff_to_text
                updated = apply_unified_diff_to_text(target.read_text(encoding="utf-8"), diff_text)
                target.write_text(updated, encoding="utf-8")
            st.success(f"Applied patch to: {', '.join(parsed.target_files)}")
        except (PatchValidationError, OSError) as exc:
            st.error(f"Could not apply patch: {exc}")
