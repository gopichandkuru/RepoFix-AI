from pathlib import Path
import streamlit as st

from agent.review import review_pr_diff

st.title("PR Reviewer")
st.caption("Inspect a pull-request unified diff for risk findings, severity, and suggested fixes.")

default_repo = st.session_state.get("repo_path") or "datasets/curated/fixtures/fix_01_discount/repo"
repo_input = st.text_input("Optional Repository Path for Context", value=default_repo)

sample_pr_diff = """--- a/shop/pricing.py
+++ b/shop/pricing.py
@@ -1,5 +1,8 @@
 def apply_discount(price: float, percent: float) -> float:
-    if percent < 0 or percent > 100:
-        raise ValueError("percent must be between 0 and 100")
-    # Bug: applies percent as raw multiplier instead of percentage fraction
-    return round(price - percent, 2)
+    try:
+        # TODO: validate upper bound cleanly
+        return round(price * (1.0 - percent / 100.0), 2)
+    except Exception:
+        return price
"""

diff_input = st.text_area("PR Unified Diff", value=sample_pr_diff, height=220)
severity_filter = st.multiselect(
    "Filter by Severity",
    options=["high", "medium", "low"],
    default=["high", "medium", "low"],
)

if st.button("Review PR Diff"):
    repo_p = Path(repo_input) if repo_input.strip() else None
    report = review_pr_diff(diff_input, repo_dir=repo_p)
    st.subheader("Review Summary")
    st.write(report.summary)

    filtered = [f for f in report.findings if f.severity in severity_filter]
    st.subheader(f"Findings ({len(filtered)})")
    for item in filtered:
        with st.container(border=True):
            st.markdown(f"**{item.title}** — `{item.file}` line `{item.line}` | severity: `{item.severity}`")
            st.write(f"**Explanation:** {item.explanation}")
            st.write(f"**Suggested Fix:** {item.suggested_fix}")

    st.json(report.model_dump())
