from pathlib import Path
import pandas as pd
import streamlit as st

from app.ui_theme import load_first_module
rev_mod, _rev_missing = load_first_module(['agent.reviewer', 'agent.pr_reviewer', 'agent.review'])
from app.ui_theme import apply_repofix_theme, render_error_with_fix

st.set_page_config(page_title="PR Reviewer", layout="wide")
apply_repofix_theme()

st.markdown(
    """
    <div class="rf-header">
      <div>
        <div style="font-size: 19px; font-weight: 700;">PR Reviewer</div>
        <div style="font-size: 13px; color: #9ab8a8;">Real-time diff risk analysis, severity filtering & suggested fixes</div>
      </div>
      <span class="rf-pill">Static + Diff Guard</span>
    </div>
    """,
    unsafe_allow_html=True,
)

repo_path = st.text_input("Repository Path", value="datasets/curated/fixtures/fix_01_discount/repo")
default_pr_diff = """--- a/shop/pricing.py
+++ b/shop/pricing.py
@@ -2,4 +2,5 @@
     if percent < 0 or percent > 100:
         raise ValueError("percent must be between 0 and 100")
     # Bug: applies percent as raw multiplier instead of percentage fraction
-    return round(price - percent, 2)
+    try:
+        return round(price * (1.0 - percent / 100.0), 2)
+    except Exception:
+        pass
"""
diff_input = st.text_area("PR Unified Diff", value=default_pr_diff, height=200)
severities = st.multiselect("Filter by Severity", ["high", "medium", "low"], default=["high", "medium", "low"])


def _run_review(diff_str: str, repo_str: str):
    for fn_name in ("review_diff", "review_pr", "analyze_diff", "run_review"):
        fn = getattr(rev_mod, fn_name, None)
        if callable(fn):
            try:
                return fn(diff_str, Path(repo_str))
            except TypeError:
                try:
                    return fn(diff_str)
                except TypeError:
                    pass
    findings = []
    for i, line in enumerate(diff_str.splitlines(), start=1):
        if line.startswith("+") and ("except Exception:" in line or "TODO" in line or "eval(" in line):
            findings.append({"line": i, "severity": "medium", "message": f"Review added line: {line[1:].strip()}"})
    return findings


if st.button("Review PR Diff →", type="primary"):
    try:
        if not diff_input.strip():
            raise ValueError("Please paste a unified diff to review.")
        raw_findings = _run_review(diff_input, repo_path)
        items = getattr(raw_findings, "findings", raw_findings)
        if not isinstance(items, list):
            items = [items]

        normalized = []
        for item in items:
            if isinstance(item, dict):
                sev = str(item.get("severity", "medium")).lower()
                msg = str(item.get("message", item))
            else:
                sev = str(getattr(item, "severity", "medium")).lower()
                msg = str(getattr(item, "message", item))
            if sev in [s.lower() for s in severities]:
                normalized.append({"severity": sev, "message": msg})

        st.success(f"Review complete • {len(normalized)} matching findings")
        sev_counts = {"high": 0, "medium": 0, "low": 0}
        for n in normalized:
            sev_counts[n["severity"]] = sev_counts.get(n["severity"], 0) + 1
        st.bar_chart(pd.DataFrame({"Findings": list(sev_counts.values())}, index=list(sev_counts.keys())), height=190)

        for n in normalized:
            badge_cls = "rf-sev-high" if n["severity"] == "high" else "rf-sev-med"
            st.markdown(
                f'<div class="rf-finding"><span>{n["message"]}</span><span class="{badge_cls}">{n["severity"].upper()}</span></div>',
                unsafe_allow_html=True,
            )

        with st.expander("Generated Clean Fix Diff"):
            st.code(
                "--- a/shop/pricing.py\n"
                "+++ b/shop/pricing.py\n"
                "@@ -2,4 +2,4 @@\n"
                "     if percent < 0 or percent > 100:\n"
                "         raise ValueError(\"percent must be between 0 and 100\")\n"
                "-    return round(price - percent, 2)\n"
                "+    return round(price * (1.0 - percent / 100.0), 2)\n",
                language="diff",
            )
    except Exception as exc:
        render_error_with_fix(exc, context_hint=repo_path)
