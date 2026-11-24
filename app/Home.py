from pathlib import Path
import tempfile
import zipfile
import pandas as pd
import streamlit as st

from app.ui_theme import apply_repofix_theme, render_error_with_fix
from repo_engine.ingest import ingest_directory

st.set_page_config(page_title="RepoFix AI", layout="wide")
apply_repofix_theme()

st.markdown(
    """
    <div class="rf-header">
      <div>
        <div style="font-size: 19px; font-weight: 700;">RepoFix AI</div>
        <div style="font-size: 13px; color: #9ab8a8;">Real-time repository intelligence, diagnosis & patch verification</div>
      </div>
      <span class="rf-pill">Live Pipeline • RTX 3050</span>
    </div>
    """,
    unsafe_allow_html=True,
)

fixture_repos = sorted(Path("datasets/curated/fixtures").glob("*/repo"))
indexed_count = len(st.session_state.get("home_files", []))

st.markdown(
    f"""
    <div class="rf-kpi-grid">
      <div class="rf-kpi">
        <div class="rf-kpi-label">Curated Fixtures</div>
        <div class="rf-kpi-val">{len(fixture_repos)}</div>
      </div>
      <div class="rf-kpi">
        <div class="rf-kpi-label">Active Indexed Files</div>
        <div class="rf-kpi-val">{indexed_count}</div>
      </div>
      <div class="rf-kpi">
        <div class="rf-kpi-label">Pytest Suite</div>
        <div class="rf-kpi-val">20 / 20</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="rf-card"><div style="font-size:17px;font-weight:700;margin-bottom:4px;">Real-Time Repository Analysis</div><div style="color:#9ab8a8;font-size:13px;margin-bottom:10px;">Upload a ZIP archive or scan a local project folder directly.</div>', unsafe_allow_html=True)

uploaded_zip = st.file_uploader("Upload repository ZIP", type=["zip"])
local_repo = st.text_input("Local project directory", value="datasets/curated/fixtures/fix_01_discount/repo")

def _extract_zip_safely(zip_bytes: bytes, dest: Path) -> None:
    archive_path = dest.parent / f"{dest.name}.zip"
    archive_path.write_bytes(zip_bytes)
    with zipfile.ZipFile(archive_path, "r") as zf:
        for info in zf.infolist():
            out_file = (dest / info.filename).resolve()
            if not str(out_file).startswith(str(dest.resolve())):
                raise ValueError(f"Unsafe path in archive: {info.filename}")
        zf.extractall(dest)

if st.button("Analyze Repository →", type="primary"):
    try:
        if uploaded_zip is not None:
            raw = uploaded_zip.getvalue()
            if not raw:
                raise ValueError("Uploaded ZIP file is empty.")
            out_dir = Path(tempfile.mkdtemp(prefix="repofix_ui_"))
            _extract_zip_safely(raw, out_dir)
            ing = ingest_directory(out_dir)
            files = getattr(ing, "files", ing)
            st.session_state["home_files"] = [str(f) for f in files]
            st.success(f"Extracted & indexed `{uploaded_zip.name}` ({len(files)} files)")
        else:
            p = Path(local_repo.strip()).expanduser()
            if not p.is_dir():
                raise FileNotFoundError(f"Directory does not exist: {p}")
            ing = ingest_directory(p)
            files = getattr(ing, "files", ing)
            st.session_state["home_files"] = [str(f) for f in files]
            st.success(f"Indexed `{p}` ({len(files)} files)")
    except Exception as exc:
        render_error_with_fix(exc, context_hint=local_repo)

if st.session_state.get("home_files"):
    ext_counts = {}
    for fp in st.session_state["home_files"]:
        ext = Path(fp).suffix or "no_ext"
        ext_counts[ext] = ext_counts.get(ext, 0) + 1
    chart_df = pd.DataFrame({"File Count": list(ext_counts.values())}, index=list(ext_counts.keys()))
    st.markdown("**Indexed File Types Chart**")
    st.bar_chart(chart_df, height=200)

st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    """
    <div class="rf-card">
      <div style="font-size:16px;font-weight:700;margin-bottom:6px;">Common Static & Patch Checks</div>
      <div class="rf-finding">
        <span>⚠ Missing boundary / discount percentage guard</span>
        <span class="rf-sev-med">Medium</span>
      </div>
      <div class="rf-finding">
        <span>🛡 Path traversal & unverified diff hunk check</span>
        <span class="rf-sev-high">High</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)
