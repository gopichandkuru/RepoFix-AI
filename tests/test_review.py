from agent.review import review_pr_diff


def test_pr_reviewer_flags_broad_except_and_todo():
    diff = """--- a/pkg/worker.py
+++ b/pkg/worker.py
@@ -1,2 +1,5 @@
 def run_job():
-    pass
+    # TODO: tighten handler
+    except Exception:
+        return None
"""
    report = review_pr_diff(diff)
    assert report.task == "pr_review"
    assert len(report.findings) >= 1
    assert any(f.severity == "medium" for f in report.findings)
