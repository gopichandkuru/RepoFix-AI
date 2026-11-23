import json
from pathlib import Path
import streamlit as st

from evaluation.metrics import evaluate_retrieval_suite

st.title("Bench Lab")
st.caption("Compare retrieval configurations and record reproducible benchmark runs.")

fixtures_dir = Path(st.text_input("Fixtures Directory", value="datasets/curated/fixtures"))
top_k = st.slider("Top-K Candidates", min_value=1, max_value=10, value=5)

if st.button("Run Retrieval Ablation (BM25 vs. BM25 + Graph)"):
    if not fixtures_dir.exists():
        st.error("Fixtures directory not found.")
    else:
        bm25_res = evaluate_retrieval_suite(fixtures_dir, use_graph=False, top_k=top_k)
        graph_res = evaluate_retrieval_suite(fixtures_dir, use_graph=True, top_k=top_k)

        summary_rows = [
            {
                "Configuration": "BM25 Only",
                "Tasks": bm25_res["total_tasks"],
                "Recall@1": bm25_res["recall_at_1"],
                "Recall@3": bm25_res["recall_at_3"],
                "Recall@5": bm25_res["recall_at_5"],
            },
            {
                "Configuration": "BM25 + Graph-RAG",
                "Tasks": graph_res["total_tasks"],
                "Recall@1": graph_res["recall_at_1"],
                "Recall@3": graph_res["recall_at_3"],
                "Recall@5": graph_res["recall_at_5"],
            },
        ]
        st.table(summary_rows)

        report_path = Path("evaluation/reports/ablation_latest.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"bm25_only": bm25_res, "bm25_plus_graph": graph_res}
        report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        st.success(f"Saved benchmark report to `{report_path}`")
        st.json(payload)
