from pathlib import Path
import pandas as pd
import streamlit as st

import repo_engine.parser as parser_mod
from app.ui_theme import apply_repofix_theme, render_error_with_fix
from repo_engine.ingest import ingest_directory

st.set_page_config(page_title="Repository Explorer", layout="wide")
apply_repofix_theme()

st.markdown(
    """
    <div class="rf-header">
      <div>
        <div style="font-size: 19px; font-weight: 700;">Repository Explorer</div>
        <div style="font-size: 13px; color: #9ab8a8;">Real-time file tree scan, AST symbol inspection & visual breakdown</div>
      </div>
      <span class="rf-pill">AST + File Scanner</span>
    </div>
    """,
    unsafe_allow_html=True,
)

local_candidates = [
    ".",
    "datasets/curated/fixtures/fix_01_discount/repo",
    "datasets/curated/fixtures/fix_02_auth/repo",
    "datasets/curated/fixtures/fix_03_pagination/repo",
]
existing_choices = [p for p in local_candidates if Path(p).is_dir()]
preset = st.selectbox("Quick Valid Paths", existing_choices or ["."], index=1 if len(existing_choices) > 1 else 0)
repo_input = st.text_input("Local Repository Path", value=preset)
max_preview = st.slider("Max Files to Preview", min_value=5, max_value=100, value=25, step=5)


def _extract_symbols(py_file: Path):
    for fn_name in ("parse_python_file", "parse_file_symbols", "parse_symbols", "extract_symbols"):
        fn = getattr(parser_mod, fn_name, None)
        if callable(fn):
            try:
                return fn(py_file)
            except Exception:
                pass
    import ast
    names = []
    try:
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names.append(node.name)
    except SyntaxError:
        pass
    return names


if st.button("Scan & Index Repository →", type="primary"):
    try:
        repo_dir = Path(repo_input.strip()).expanduser()
        if not repo_dir.is_dir():
            raise FileNotFoundError(f"Directory does not exist: {repo_dir}")

        ing = ingest_directory(repo_dir)
        files = [Path(getattr(f, "file_path", getattr(f, "path", f))) for f in getattr(ing, "files", ing)]

        ext_summary = {}
        py_symbol_rows = []
        for f in files:
            ext = f.suffix or "other"
            ext_summary[ext] = ext_summary.get(ext, 0) + 1
            if f.suffix == ".py" and f.exists():
                syms = _extract_symbols(f)
                py_symbol_rows.append({"file": str(f), "symbols": len(syms), "names": ", ".join(syms[:8])})

        st.success(f"Scanned `{repo_dir}` • Found {len(files)} files")
        if ext_summary:
            st.markdown("**Files by Extension Chart**")
            st.bar_chart(pd.DataFrame({"Count": list(ext_summary.values())}, index=list(ext_summary.keys())), height=210)

        st.markdown("**Indexed Files Preview**")
        st.dataframe(pd.DataFrame({"File Path": [str(f) for f in files[: int(max_preview)]]}), use_container_width=True)

        if py_symbol_rows:
            st.markdown("**Python AST Symbols**")
            st.dataframe(pd.DataFrame(py_symbol_rows[: int(max_preview)]), use_container_width=True)
    except Exception as exc:
        render_error_with_fix(exc, context_hint=repo_input)
