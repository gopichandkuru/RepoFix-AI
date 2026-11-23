from pathlib import Path
import streamlit as st

from agent.diagnosis import run_retrieval_diagnosis

st.title("Bug Detective")

default_repo = st.session_state.get("repo_path") or "datasets/curated/fixtures/fix_01_discount/repo"
repo_path = st.text_input("Repository Path", value=default_repo)
use_graph = st.checkbox("Enable Graph-RAG Expansion", value=True)
issue_text = st.text_area(
    "Issue Description / Stack Trace",
    height=130,
    placeholder="Paste bug report, failing assertion, or stack trace...",
)

if st.button("Analyze Bug"):
    p = Path(repo_path)
    if not p.exists() or not p.is_dir():
        st.error("Please enter a valid repository directory.")
    elif not issue_text.strip():
        st.warning("Please enter an issue description or stack trace.")
    else:
        st.session_state["repo_path"] = str(p.resolve())
        report = run_retrieval_diagnosis(p, issue_text=issue_text, use_graph=use_graph, top_k=5)

        st.subheader("Diagnosis Summary")
        st.write(report.summary)
        st.caption(f"Confidence: `{report.confidence}`")

        st.subheader("Candidate Findings")
        for f in report.findings:
            with st.container(border=True):
                st.markdown(f"**{f.file}** (`{f.symbol or 'module'}`) — line `{f.line_hint}` | severity: `{f.severity}`")
                st.write(f"**Evidence:** {f.evidence}")
                st.write(f"**Recommendation:** {f.recommendation}")

        st.subheader("Structured JSON Output")
        st.json(report.model_dump())
