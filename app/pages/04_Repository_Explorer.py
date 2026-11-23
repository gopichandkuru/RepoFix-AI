from pathlib import Path
import streamlit as st

from repo_engine.ingest import ingest_directory
from repo_engine.parser import parse_python_file

st.title("Repository Explorer")

default_repo = st.session_state.get("repo_path") or "datasets/curated/fixtures/fix_01_discount/repo"
repo_input = st.text_input("Local Repository Path", value=default_repo)

if st.button("Scan & Index Repository"):
    p = Path(repo_input)
    if p.exists() and p.is_dir():
        st.session_state["repo_path"] = str(p.resolve())
        st.session_state["index_status"] = "READY"
    else:
        st.session_state["index_status"] = "ERROR"
        st.error("Directory does not exist.")

active_repo = st.session_state.get("repo_path")
if active_repo and Path(active_repo).exists():
    files = ingest_directory(Path(active_repo))
    st.metric("Indexed Files", len(files))

    file_paths = [f.rel_path for f in files]
    selected_file = st.selectbox("Select File", options=file_paths) if file_paths else None

    if selected_file:
        full_file = Path(active_repo) / selected_file
        content = full_file.read_text(encoding="utf-8", errors="replace")
        st.code(content, language="python" if selected_file.endswith(".py") else None, line_numbers=True)

        if selected_file.endswith(".py"):
            parsed = parse_python_file(full_file, rel_path=selected_file)
            st.subheader("Extracted Symbols")
            for sym in parsed.symbols:
                st.write(f"`{sym.kind}` **{sym.name}** (lines {sym.start_line}–{sym.end_line}) — `{sym.signature}`")
else:
    st.info("Enter a valid local repository directory and click **Scan & Index Repository**.")
