import importlib
import streamlit as st


def apply_repofix_theme():
    st.markdown(
        """
        <style>
        /* Main App Canvas */
        .stApp {
            background: radial-gradient(circle at 18% 0%, #0d2b1e 0%, #060b09 55%, #040706 100%);
            color: #e8f5ee;
        }
        header[data-testid="stHeader"] {
            background: rgba(6, 11, 9, 0.75);
            backdrop-filter: blur(8px);
        }
        .block-container {
            padding-top: 1.4rem;
            padding-bottom: 2.5rem;
            max-width: 1120px;
        }

        /* Professional Left Navigation Sidebar */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #081510 0%, #050c09 100%) !important;
            border-right: 1px solid rgba(52, 211, 153, 0.18) !important;
            width: 260px !important;
        }
        section[data-testid="stSidebar"] > div:first-child {
            padding-top: 1.1rem;
        }
        /* Sidebar Brand Header via ::before */
        [data-testid="stSidebarNav"]::before {
            content: "REPOFIX AI  •  v0.4";
            display: block;
            margin: 0 14px 14px 14px;
            padding: 10px 14px;
            border-radius: 10px;
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.18), rgba(6, 78, 59, 0.35));
            border: 1px solid rgba(52, 211, 153, 0.32);
            color: #6ee7b7;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.08em;
        }
        /* Sidebar Nav Links */
        [data-testid="stSidebarNav"] ul {
            padding: 0 10px;
        }
        [data-testid="stSidebarNav"] li {
            margin-bottom: 4px;
        }
        [data-testid="stSidebarNav"] a {
            border-radius: 10px !important;
            padding: 9px 14px !important;
            color: #9ab8a8 !important;
            font-weight: 500 !important;
            border: 1px solid transparent !important;
            transition: all 0.18s ease-in-out;
        }
        [data-testid="stSidebarNav"] a:hover {
            background: rgba(16, 185, 129, 0.10) !important;
            color: #ecfdf5 !important;
            border-color: rgba(52, 211, 153, 0.22) !important;
        }
        /* Active Sidebar Page Pill */
        [data-testid="stSidebarNav"] a[aria-current="page"] {
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.24), rgba(5, 150, 105, 0.16)) !important;
            color: #6ee7b7 !important;
            font-weight: 700 !important;
            border: 1px solid rgba(52, 211, 153, 0.45) !important;
            box-shadow: 0 4px 14px rgba(16, 185, 129, 0.12);
        }
        [data-testid="stSidebarNav"] a[aria-current="page"] span {
            color: #6ee7b7 !important;
        }

        /* Header Banner & Cards */
        .rf-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: linear-gradient(120deg, rgba(16, 185, 129, 0.14), rgba(10, 24, 18, 0.92));
            border: 1px solid rgba(52, 211, 153, 0.28);
            border-radius: 14px;
            padding: 14px 20px;
            margin-bottom: 16px;
        }
        .rf-pill {
            background: rgba(16, 185, 129, 0.18);
            border: 1px solid rgba(52, 211, 153, 0.45);
            color: #6ee7b7;
            padding: 4px 12px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 600;
        }
        .rf-card {
            background: rgba(11, 24, 18, 0.88);
            border: 1px solid rgba(110, 231, 183, 0.18);
            border-radius: 14px;
            padding: 16px 20px;
            margin-bottom: 16px;
        }
        .rf-kpi-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-bottom: 16px;
        }
        .rf-kpi {
            background: rgba(11, 24, 18, 0.9);
            border: 1px solid rgba(110, 231, 183, 0.2);
            border-radius: 12px;
            padding: 14px 16px;
        }
        .rf-kpi-label {
            font-size: 12px;
            color: #9ab8a8;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 4px;
        }
        .rf-kpi-val {
            font-size: 26px;
            font-weight: 700;
            color: #34d399;
        }
        .rf-finding {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 12px;
            border-radius: 10px;
            background: rgba(6, 15, 11, 0.82);
            border: 1px solid rgba(110, 231, 183, 0.14);
            margin-top: 8px;
        }
        .rf-sev-med {
            background: rgba(245, 158, 11, 0.18);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.4);
            padding: 2px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 600;
        }
        .rf-sev-high {
            background: rgba(239, 68, 68, 0.18);
            color: #f87171;
            border: 1px solid rgba(239, 68, 68, 0.4);
            padding: 2px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 600;
        }

        /* Range Slider Styling */
        [data-testid="stSlider"] [data-testid="stThumbValue"] {
            background: #10b981;
            color: #04120c;
            font-weight: 700;
            border-radius: 6px;
            padding: 2px 6px;
        }
        [data-testid="stSlider"] div[role="slider"] {
            background-color: #34d399 !important;
            border: 2px solid #ecfdf5 !important;
            box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.25) !important;
        }

        /* Primary Buttons */
        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #059669, #10b981);
            color: #03110b;
            border: none;
            border-radius: 10px;
            font-weight: 700;
            padding: 0.55rem 1.2rem;
        }
        div.stButton > button[kind="primary"]:hover {
            background: linear-gradient(135deg, #10b981, #34d399);
            color: #020c08;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    with st.sidebar:
        st.markdown(
            """
            <div style="margin: 14px 8px 0 8px; padding: 12px; border-radius: 10px;
                        background: rgba(11, 24, 18, 0.85); border: 1px solid rgba(52, 211, 153, 0.18);
                        font-size: 12px; color: #9ab8a8;">
              <div style="color: #6ee7b7; font-weight: 700; margin-bottom: 4px;">System Status</div>
              <div>GPU: RTX 3050 (4-bit NF4)</div>
              <div>Model: Qwen2.5-Coder-1.5B</div>
              <div>Tests: 20 / 20 Passing</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_error_with_fix(exc: Exception, context_hint: str = ""):
    err_type = type(exc).__name__
    err_msg = str(exc)
    st.error(f"Error Detected ({err_type}): {err_msg}")

    cause = "Invalid path, missing module/symbol, or malformed input reached the pipeline."
    how_to_fix = (
        "1. Verify the target path exists locally or pass a valid GitHub/ZIP input.\n"
        "2. Check imported module/function names against actual repo modules.\n"
        "3. Apply the generated fix snippet below and re-run."
    )
    fixed_code = (
        "from pathlib import Path\n"
        "from repo_engine.ingest import ingest_directory\n\n"
        "repo_dir = Path('datasets/curated/fixtures/fix_01_discount/repo')\n"
        "assert repo_dir.is_dir(), f'Missing repo dir: {repo_dir}'\n"
        "result = ingest_directory(repo_dir)\n"
        "print('Indexed files:', len(result.files))\n"
    )

    if "No module named" in err_msg or isinstance(exc, ModuleNotFoundError):
        missing_mod = err_msg.split("No module named")[-1].strip().strip("'\"")
        cause = f"Python could not import `{missing_mod}` because the module name or `PYTHONPATH=.` is missing."
        how_to_fix = (
            f"1. Replace missing import `{missing_mod}` with the existing module in this repo (e.g., `agent.diagnose`).\n"
            "2. Launch Streamlit with `PYTHONPATH=. streamlit run app/Home.py`."
        )
        fixed_code = (
            "import importlib\n\n"
            "for mod_name in ('agent.diagnose', 'agent.reviewer', 'repo_engine.ingest'):\n"
            "    try:\n"
            "        mod = importlib.import_module(mod_name)\n"
            "        print('Loaded:', mod.__name__)\n"
            "    except ModuleNotFoundError as e:\n"
            "        print('Skip missing:', e)\n"
        )
    elif isinstance(exc, (FileNotFoundError, NotADirectoryError)) or "Directory" in err_msg:
        cause = f"Target repository folder was not found on disk ({context_hint or err_msg})."
        how_to_fix = (
            "1. Use an existing local directory such as `datasets/curated/fixtures/fix_01_discount/repo` or `.`.\n"
            "2. Avoid Windows UNC/WSL paths that do not exist inside the active Linux shell."
        )
        fixed_code = (
            "from pathlib import Path\n\n"
            "def resolve_valid_repo(path_str: str) -> Path:\n"
            "    p = Path(path_str).expanduser()\n"
            "    if p.is_dir():\n"
            "        return p\n"
            "    fallback = Path('datasets/curated/fixtures/fix_01_discount/repo')\n"
            "    return fallback if fallback.is_dir() else Path('.')\n"
        )
    elif "Context mismatch" in err_msg or "diff" in err_msg.lower():
        cause = "Unified diff hunk line numbers/context did not match the target file contents."
        how_to_fix = (
            "1. Regenerate the unified diff using `difflib.unified_diff` against the current file lines.\n"
            "2. Verify hunk headers (`@@ -start,count +start,count @@`) match before applying."
        )
        fixed_code = (
            "import difflib\n\n"
            "def make_exact_diff(rel_path: str, old_text: str, new_text: str) -> str:\n"
            "    return ''.join(difflib.unified_diff(\n"
            "        old_text.splitlines(keepends=True),\n"
            "        new_text.splitlines(keepends=True),\n"
            "        fromfile=f'a/{rel_path}',\n"
            "        tofile=f'b/{rel_path}',\n"
            "    ))\n"
        )

    with st.expander("Error Analysis, How to Fix & Generated Code", expanded=True):
        st.markdown(f"**Root Cause:** {cause}")
        st.markdown(f"**How to Change / Fix:**\n{how_to_fix}")
        st.code(fixed_code, language="python")


def load_first_module(candidates):
    """Return (module, missing_list) for the first importable module name."""
    missing = []
    for name in candidates:
        try:
            return importlib.import_module(name), missing
        except ModuleNotFoundError:
            missing.append(name)
    return None, missing
