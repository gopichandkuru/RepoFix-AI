import difflib
from pathlib import Path
import streamlit as st

from agent.patch_validator import validate_unified_diff
from app.ui_theme import apply_repofix_theme, render_error_with_fix
from sandbox.docker_runner import verify_patch_in_isolated_worktree

st.set_page_config(page_title="Patch Lab", layout="wide")
apply_repofix_theme()

st.markdown(
    """
    <div class="rf-header">
      <div>
        <div style="font-size: 19px; font-weight: 700;">Patch Lab</div>
        <div style="font-size: 13px; color: #9ab8a8;">Isolated Git worktree patch validation, syntax check & pytest runner</div>
      </div>
      <span class="rf-pill">Sandbox Worktree</span>
    </div>
    """,
    unsafe_allow_html=True,
)

repo_path = st.text_input("Repository Path", value="datasets/curated/fixtures/fix_01_discount/repo")
timeout_sec = st.slider("Worktree Timeout (seconds)", min_value=5, max_value=60, value=15, step=5)

default_diff = """--- a/shop/pricing.py
+++ b/shop/pricing.py
@@ -2,4 +2,4 @@
     if percent < 0 or percent > 100:
         raise ValueError("percent must be between 0 and 100")
     # Bug: applies percent as raw multiplier instead of percentage fraction
-    return round(price - percent, 2)
+    return round(price * (1.0 - percent / 100.0), 2)
"""
diff_text = st.text_area("Unified Diff Patch", value=default_diff, height=210)

c1, c2 = st.columns(2)
with c1:
    run_isolated = st.button("Validate & Run Tests in Isolated Worktree →", type="primary")
with c2:
    auto_rebuild = st.button("Auto-Align Diff Against Target File")

repo_dir = Path(repo_path.strip()).expanduser()

if auto_rebuild:
    try:
        target_file = repo_dir / "shop/pricing.py"
        if not target_file.exists():
            raise FileNotFoundError(f"Target file not found: {target_file}")
        orig = target_file.read_text(encoding="utf-8")
        fixed = orig.replace("return round(price - percent, 2)", "return round(price * (1.0 - percent / 100.0), 2)")
        aligned = "".join(
            difflib.unified_diff(
                orig.splitlines(keepends=True),
                fixed.splitlines(keepends=True),
                fromfile="a/shop/pricing.py",
                tofile="b/shop/pricing.py",
            )
        )
        st.success("Generated exact line-aligned unified diff:")
        st.code(aligned, language="diff")
    except Exception as exc:
        render_error_with_fix(exc, context_hint=str(repo_dir))

if run_isolated:
    try:
        if not repo_dir.is_dir():
            raise FileNotFoundError(f"Repository directory does not exist: {repo_dir}")
        parsed = validate_unified_diff(diff_text, repo_dir)
        with st.spinner("Running isolated worktree verification..."):
            result = verify_patch_in_isolated_worktree(repo_dir, diff_text, timeout_sec=int(timeout_sec))

        m1, m2, m3 = st.columns(3)
        m1.metric("Diff Valid", "YES" if result.diff_valid else "NO")
        m2.metric("Syntax OK", "YES" if result.syntax_ok else "NO")
        m3.metric("Tests Passed", "PASS" if result.tests_passed else "FAIL")

        if result.tests_passed:
            st.success("Isolated worktree verification PASSED!")
        else:
            render_error_with_fix(RuntimeError(result.error or "Worktree tests failed"), context_hint=str(repo_dir))

        st.json(
            {
                "target_files": getattr(parsed, "target_files", []),
                "diff_valid": result.diff_valid,
                "syntax_ok": result.syntax_ok,
                "tests_passed": result.tests_passed,
                "return_code": result.return_code,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "error": result.error,
            }
        )
    except Exception as exc:
        render_error_with_fix(exc, context_hint=str(repo_dir))
