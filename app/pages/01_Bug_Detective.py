import hashlib
from pathlib import Path
import re
import subprocess
import streamlit as st

from agent.bug_detective import diagnose_bug
from repo_engine.ingest import ingest_directory
from retrieval.bm25_index import build_bm25_index, search_bm25
from retrieval.graph_rag import build_code_graph, expand_with_graph

st.title("Bug Detective")
st.caption("Localize root causes with code-aware BM25 + Graph-RAG and generate structured diagnosis JSON.")

fixtures = sorted(Path("datasets/curated/fixtures").glob("*/repo"))
preset_options = ["Custom Path / GitHub URL"] + [str(p) for p in fixtures]
preset = st.selectbox("Quick Local Fixture Preset", preset_options, index=1 if fixtures else 0)

default_repo = "" if preset == "Custom Path / GitHub URL" else preset
repo_input = st.text_input("Repository Path or GitHub URL", value=default_repo)
use_graph = st.checkbox("Enable Graph-RAG Expansion", value=True)
issue_text = st.text_area(
    "Issue Description / Stack Trace",
    value="apply_discount returns wrong discounted price for percentage discounts",
    height=130,
)


def _resolve_repo_dir(raw_path: str) -> Path:
    cleaned = raw_path.strip()
    if not cleaned:
        raise ValueError("Please enter a local repository path or GitHub URL.")
    if re.match(r"^(https?://|git@)", cleaned):
        slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", cleaned.rstrip("/"))[-40:]
        digest = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()[:8]
        dest = Path("/tmp/repofix_clones") / f"{slug}_{digest}"
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            proc = subprocess.run(
                ["git", "clone", "--depth", "1", cleaned, str(dest)],
                capture_output=True,
                text=True,
                timeout=90,
            )
            if proc.returncode != 0:
                raise RuntimeError(f"Git clone failed: {proc.stderr.strip() or proc.stdout.strip()}")
        return dest
    p = Path(cleaned)
    if not p.is_dir():
        raise FileNotFoundError(f"Directory not found: {p}")
    return p


if st.button("Analyze Bug", type="primary"):
    if not issue_text.strip():
        st.error("Please enter an issue description or stack trace.")
    else:
        try:
            with st.spinner("Ingesting repository & retrieving context..."):
                repo_dir = _resolve_repo_dir(repo_input)
                ingest_res = ingest_directory(repo_dir)
                bm25_idx = build_bm25_index(ingest_res.files)
                hits = search_bm25(bm25_idx, issue_text, top_k=5)
                if use_graph:
                    graph = build_code_graph(ingest_res.files)
                    candidates = expand_with_graph(graph, [h.file_path for h in hits], max_hops=1)
                else:
                    candidates = [
                        {"file": h.file_path, "score": h.score, "source": "bm25"}
                        for h in hits
                    ]
                diagnosis = diagnose_bug(
                    repo_root=repo_dir,
                    issue_text=issue_text,
                    candidates=candidates,
                )
            st.success(f"Analyzed `{repo_dir}` ({len(ingest_res.files)} files indexed)")
            st.subheader("Top Candidate Files")
            st.json(candidates)
            st.subheader("Structured Diagnosis")
            st.json(diagnosis)
        except Exception as exc:
            st.error(str(exc))
