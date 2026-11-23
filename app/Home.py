import streamlit as st

st.set_page_config(
    page_title="RepoFix AI — Repository Intelligence & Repair",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .stApp {
            background-color: #0e1117;
            color: #e6edf3;
        }
        [data-testid="stSidebar"] {
            background-color: #161b22;
            border-right: 1px solid #262c36;
        }
        code, pre, .stCodeBlock {
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace !important;
        }
        .status-pill {
            display: inline-block;
            padding: 2px 10px;
            border-radius: 999px;
            background-color: rgba(45, 212, 191, 0.12);
            color: #2dd4bf;
            border: 1px solid rgba(45, 212, 191, 0.35);
            font-size: 0.8rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.session_state.setdefault("repo_path", None)
st.session_state.setdefault("index_status", "NOT_INDEXED")
st.session_state.setdefault("model_status", "UNLOADED")

col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
with col1:
    st.markdown("### RepoFix AI")
with col2:
    st.caption(f"Repo: `{st.session_state['repo_path'] or 'None selected'}`")
with col3:
    st.caption(f"Index: `{st.session_state['index_status']}`")
with col4:
    st.markdown(
        f'<span class="status-pill">Model: {st.session_state["model_status"]}</span>',
        unsafe_allow_html=True,
    )

st.divider()
st.subheader("Overview")
st.info(
    "v0.0.1 Foundation: Safe repository ingestion, fixture benchmarks, and baseline evaluation "
    "before AST indexing, retrieval, or QLoRA fine-tuning."
)
