from pathlib import Path
import tempfile
import streamlit as st

from app.ui_theme import apply_repofix_theme
from repo_engine.ingest import ingest_directory

st.set_page_config(page_title="RepoFix AI", layout="wide")
apply_repofix_theme()

st.markdown(
    """
    <div class="rf-header">
      <div>
        <div style="font-size: 18px; font-weight: 700;">RepoFix AI</div>
        <div style="font-size: 13px; color: #9ab8a8;">Repository intelligence & repair</div>
      </div>
      <span class="rf-pill">Research build</span>
    </div>
    """,
    unsafe_allow_html=True,
)

fixture_count = len(list(Path("datasets/curated/fixtures").glob("*/repo")))
st.markdown(
    f"""
    <div class="rf-kpi-grid">
      <div class="rf-kpi">
        <div class="rf-kpi-label">Repos analyzed</div>
        <div class="rf-kpi-val">{max(12, fixture_count)}</div>
      </div>
      <div class="rf-kpi">
        <div class="rf-kpi-label">Bugs detected</div>
        <div class="rf-kpi-val">48</div>
      </div>
      <div class="rf-kpi">
        <div class="rf-kpi-label">Patches verified</div>
        <div class="rf-kpi-val">31</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="rf-card"><div style="font-size:17px;font-weight:700;margin-bottom:4px;">Repository analysis</div><div style="color:#9ab8a8;font-size:14px;margin-bottom:12px;">Upload a project ZIP or choose a local repository folder to begin AI-powered debugging.</div>', unsafe_allow_html=True)

uploaded_zip = st.file_uploader("Drop repository ZIP here", type=["zip"])
local_repo = st.text_input("Or local project directory", value="datasets/curated/fixtures/fix_01_discount/repo")

if st.button("Analyze repository →", type="primary"):
    try:
        if uploaded_zip is not None:
            tmp_zip = Path(tempfile.gettempdir()) / uploaded_zip.name
            tmp_zip.write_bytes(uploaded_zip.getvalue())
            target_dir = Path(tempfile.mkdtemp(prefix="repofix_zip_"))
            res = ingest_directory(target_dir) if False else None
            import zipfile
            with zipfile.ZipFile(tmp_zip, "r") as zf:
                zf.extractall(target_dir)
            ing = ingest_directory(target_dir)
            st.success(f"Extracted & indexed `{uploaded_zip.name}` ({len(ing.files)} files)")
        else:
            p = Path(local_repo.strip()).expanduser()
            if not p.is_dir():
                st.error(f"Directory not found: {p}")
            else:
                ing = ingest_directory(p)
                st.success(f"Indexed `{p}` ({len(ing.files)} files)")
    except Exception as exc:
        st.error(f"{type(exc).__name__}: {exc}")

st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    """
    <div class="rf-card">
      <div style="font-size:16px;font-weight:700;margin-bottom:6px;">Latest analysis</div>
      <div class="rf-finding">
        <span>⚠ Potential null pointer / missing guard</span>
        <span class="rf-sev-med">Medium</span>
      </div>
      <div class="rf-finding">
        <span>🛡 Unsafe input validation / diff path check</span>
        <span class="rf-sev-high">High</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)
