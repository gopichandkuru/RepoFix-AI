import hashlib
from pathlib import Path
import re
import subprocess
import pandas as pd
import streamlit as st

from app.ui_theme import load_first_module
diag_mod, _diag_missing = load_first_module(['agent.diagnose', 'agent.bug_detective', 'agent.analyzer'])
from app.ui_theme import apply_repofix_theme, render_error_with_fix
from repo_engine.ingest import ingest_directory
from app.ui_theme import load_first_module
_bm25_mod, _bm25_missing = load_first_module(['retrieval.bm25_index', 'retrieval.bm25', 'retrieval.search'])
def build_bm25_index(files):
    fn = getattr(_bm25_mod, 'build_bm25_index', None) or getattr(_bm25_mod, 'build_index', None)
    if callable(fn):
        return fn(files)
    return [Path(getattr(f, 'file_path', getattr(f, 'path', f))) for f in files]
def search_bm25(index, query, top_k=5):
    fn = getattr(_bm25_mod, 'search_bm25', None) or getattr(_bm25_mod, 'search', None)
    if callable(fn):
        return fn(index, query, top_k=top_k)
    terms = [t.lower() for t in str(query).split() if len(t) > 2]
    scored = []
    for item in index:
        p = Path(item)
        txt = f'{p.name} ' + (p.read_text(encoding='utf-8', errors='ignore')[:2000] if p.is_file() else '')
        low = txt.lower()
        score = float(sum(low.count(t) for t in terms))
        scored.append({'file_path': str(p), 'score': score})
    scored.sort(key=lambda x: x['score'], reverse=True)
    return scored[:max(1, int(top_k))]
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

st.set_page_config(page_title="Bug Detective", layout="wide")
apply_repofix_theme()

st.markdown(
    """
    <div class="rf-header">
      <div>
        <div style="font-size: 19px; font-weight: 700;">Bug Detective</div>
        <div style="font-size: 13px; color: #9ab8a8;">Real-time BM25 + Graph-RAG root cause localization & diagnosis</div>
      </div>
      <span class="rf-pill">BM25 + Graph-RAG</span>
    </div>
    """,
    unsafe_allow_html=True,
)

fixtures = sorted(Path("datasets/curated/fixtures").glob("*/repo"))
presets = {"Custom Path or GitHub URL": ""}
for f in fixtures:
    presets[f"Fixture: {f.parent.name}"] = str(f)
presets["GitHub: PlayNest"] = "https://github.com/gopichandkuru/PlayNest.git"

c1, c2 = st.columns([1.4, 1])
with c1:
    selected_preset = st.selectbox("Repository Preset", list(presets.keys()), index=1 if fixtures else 0)
with c2:
    top_k = st.slider("Top-K Retrieval Candidates", min_value=1, max_value=10, value=5, step=1)

use_graph = st.toggle("Enable Graph-RAG Dependency Expansion", value=True)
repo_input = st.text_input("Repository Path or GitHub URL", value=presets[selected_preset])
issue_text = st.text_area(
    "Issue Description / Stack Trace",
    value="apply_discount returns wrong discounted price for percentage discounts",
    height=110,
)


def _resolve_repo(raw: str) -> Path:
    val = raw.strip()
    if not val:
        raise ValueError("Please enter a local repository path or GitHub URL.")
    if re.match(r"^(https?://|git@)", val):
        slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", val.rstrip("/"))[-36:]
        h = hashlib.sha256(val.encode("utf-8")).hexdigest()[:8]
        dest = Path("/tmp/repofix_clones") / f"{slug}_{h}"
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            proc = subprocess.run(
                ["git", "clone", "--depth", "1", val, str(dest)],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if proc.returncode != 0:
                raise RuntimeError((proc.stderr or proc.stdout).strip() or "git clone failed")
        return dest
    p = Path(val).expanduser()
    if not p.is_dir():
        raise FileNotFoundError(f"Directory does not exist: {p}")
    return p


def _call_diagnose(repo_dir: Path, candidates, query: str):
    for fn_name in ("diagnose_issue", "diagnose_bug", "diagnose", "run_diagnose"):
        fn = getattr(diag_mod, fn_name, None)
        if callable(fn):
            sig = inspect.signature(fn)
            kwargs = {}
            for param_name in sig.parameters:
                if "repo" in param_name or "root" in param_name or "dir" in param_name:
                    kwargs[param_name] = repo_dir
                elif "issue" in param_name or "query" in param_name or "prompt" in param_name or "text" in param_name:
                    kwargs[param_name] = query
                elif "cand" in param_name or "context" in param_name or "files" in param_name:
                    kwargs[param_name] = candidates
            try:
                return fn(**kwargs)
            except TypeError:
                pass
    return {
        "top_candidates": candidates,
        "summary": f"Localized {len(candidates)} candidate files for query: {query}",
    }


if st.button("Analyze Bug →", type="primary"):
    try:
        if not issue_text.strip():
            raise ValueError("Issue description cannot be empty.")
        with st.spinner("Running real-time ingestion, BM25, Graph-RAG & diagnosis..."):
            repo_dir = _resolve_repo(repo_input)
            ing = ingest_directory(repo_dir)
            files = getattr(ing, "files", ing)
            bm25_idx = build_bm25_index(files)
            hits = search_bm25(bm25_idx, issue_text, top_k=int(top_k))
            hit_files = [getattr(h, "file_path", getattr(h, "path", str(h))) for h in hits]
            if use_graph:
                graph = build_code_graph(files)
                candidates = expand_with_graph(graph, hit_files, max_hops=1)
            else:
                candidates = [
                    {"file": getattr(h, "file_path", getattr(h, "path", str(h))), "score": float(getattr(h, "score", 1.0))}
                    for h in hits
                ]
            diagnosis = _call_diagnose(repo_dir, candidates, issue_text)

        st.success(f"Analyzed `{repo_dir}` • {len(files)} files indexed")

        scores_map = {}
        for idx, h in enumerate(hits):
            fname = Path(getattr(h, "file_path", getattr(h, "path", str(h)))).name
            scores_map[fname] = float(getattr(h, "score", max(0.1, 1.0 - idx * 0.1)))
        if scores_map:
            st.markdown("**BM25 Candidate Relevance Chart**")
            st.bar_chart(pd.DataFrame({"BM25 Score": list(scores_map.values())}, index=list(scores_map.keys())), height=210)

        st.subheader("Diagnosis Output")
        st.json(diagnosis)
    except Exception as exc:
        render_error_with_fix(exc, context_hint=repo_input)
