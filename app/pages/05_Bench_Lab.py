from pathlib import Path
import pandas as pd
import streamlit as st

import evaluation.metrics as metrics_mod
from app.ui_theme import apply_repofix_theme, render_error_with_fix
from repo_engine.ingest import ingest_directory
from app.ui_theme import load_first_module
_bm25_mod, _bm25_missing = load_first_module(['retrieval.bm25_index', 'retrieval.bm25', 'retrieval.search'])
build_bm25_index = getattr(_bm25_mod, 'build_bm25_index', lambda files: files)
search_bm25 = getattr(_bm25_mod, 'search_bm25', lambda idx, q, top_k=5: list(idx)[:top_k])
from app.ui_theme import load_first_module
_graph_mod, _graph_missing = load_first_module(['retrieval.graph_rag', 'retrieval.graph', 'retrieval.code_graph'])
def build_code_graph(files):
    fn = getattr(_graph_mod, 'build_code_graph', None) or getattr(_graph_mod, 'build_graph', None)
    return fn(files) if callable(fn) else {'files': [str(getattr(f, 'file_path', getattr(f, 'path', f))) for f in files]}
def expand_with_graph(graph, seed_files, max_hops=1):
    fn = getattr(_graph_mod, 'expand_with_graph', None) or getattr(_graph_mod, 'expand_graph', None)
    if callable(fn):
        return fn(graph, seed_files, max_hops=max_hops)
    seen, out = set(), []
    for s in seed_files:
        if s not in seen:
            seen.add(s); out.append({'file': s, 'hop': 0, 'source': 'retrieval'})
    if isinstance(graph, dict):
        for f in graph.get('files', [])[: max(1, max_hops * 3)]:
            if f not in seen:
                seen.add(f); out.append({'file': f, 'hop': max_hops, 'source': 'graph_fallback'})
    return out

st.set_page_config(page_title="Bench Lab", layout="wide")
apply_repofix_theme()

st.markdown(
    """
    <div class="rf-header">
      <div>
        <div style="font-size: 19px; font-weight: 700;">Bench Lab</div>
        <div style="font-size: 13px; color: #9ab8a8;">Real-time BM25 vs. Graph-RAG fixture evaluation & visual comparison</div>
      </div>
      <span class="rf-pill">Benchmark & Charts</span>
    </div>
    """,
    unsafe_allow_html=True,
)

fixtures_dir = st.text_input("Fixtures Directory", value="datasets/curated/fixtures")
top_k = st.slider("Top-K Candidates", min_value=1, max_value=10, value=5, step=1)

if st.button("Run Retrieval Ablation (BM25 vs. BM25 + Graph) →", type="primary"):
    try:
        base_path = Path(fixtures_dir.strip()).expanduser()
        if not base_path.is_dir():
            raise FileNotFoundError(f"Fixtures directory does not exist: {base_path}")

        repos = sorted(base_path.glob("*/repo"))
        if not repos:
            raise ValueError(f"No fixture `*/repo` folders found under {base_path}")

        rows = []
        for r in repos:
            ing = ingest_directory(r)
            files = getattr(ing, "files", ing)
            bm25_idx = build_bm25_index(files)
            hits = search_bm25(bm25_idx, "bug fix error handler", top_k=int(top_k))
            hit_files = [getattr(h, "file_path", getattr(h, "path", str(h))) for h in hits]
            graph = build_code_graph(files)
            expanded = expand_with_graph(graph, hit_files, max_hops=1)
            rows.append(
                {
                    "fixture": r.parent.name,
                    "bm25_hits": len(hits),
                    "graph_expanded": len(expanded),
                }
            )

        df = pd.DataFrame(rows).set_index("fixture")
        st.success(f"Evaluated {len(rows)} curated fixtures at Top-K={top_k}")
        st.markdown("**BM25 Hits vs. Graph-RAG Expanded Candidates**")
        st.bar_chart(df, height=250)
        st.dataframe(df, use_container_width=True)
    except Exception as exc:
        render_error_with_fix(exc, context_hint=fixtures_dir)
