import streamlit as st


def apply_repofix_theme():
    st.markdown(
        """
        <style>
        .stApp {
            background: radial-gradient(circle at 20% 0%, #0b2419 0%, #060b09 55%, #050807 100%);
            color: #e6f4ec;
        }
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2.5rem;
            max-width: 1040px;
        }
        .rf-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(12, 28, 21, 0.85);
            border: 1px solid rgba(52, 211, 153, 0.22);
            border-radius: 14px;
            padding: 14px 18px;
            margin-bottom: 16px;
        }
        .rf-pill {
            background: rgba(16, 185, 129, 0.16);
            border: 1px solid rgba(52, 211, 153, 0.35);
            color: #6ee7b7;
            padding: 4px 12px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 600;
        }
        .rf-card {
            background: rgba(11, 24, 18, 0.88);
            border: 1px solid rgba(110, 231, 183, 0.16);
            border-radius: 14px;
            padding: 18px 20px;
            margin-bottom: 16px;
        }
        .rf-kpi-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-bottom: 16px;
        }
        .rf-kpi {
            background: rgba(11, 24, 18, 0.88);
            border: 1px solid rgba(110, 231, 183, 0.16);
            border-radius: 12px;
            padding: 14px 16px;
        }
        .rf-kpi-label {
            font-size: 13px;
            color: #9ab8a8;
            margin-bottom: 6px;
        }
        .rf-kpi-val {
            font-size: 28px;
            font-weight: 700;
            color: #34d399;
            line-height: 1.1;
        }
        .rf-finding {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 12px;
            border-radius: 10px;
            background: rgba(7, 16, 12, 0.75);
            border: 1px solid rgba(110, 231, 183, 0.12);
            margin-top: 8px;
        }
        .rf-sev-med {
            background: rgba(245, 158, 11, 0.16);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.35);
            padding: 2px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 600;
        }
        .rf-sev-high {
            background: rgba(239, 68, 68, 0.16);
            color: #f87171;
            border: 1px solid rgba(239, 68, 68, 0.35);
            padding: 2px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 600;
        }
        div.stButton > button[kind="primary"] {
            width: 100%;
            background: rgba(16, 185, 129, 0.22);
            color: #6ee7b7;
            border: 1px solid rgba(52, 211, 153, 0.45);
            border-radius: 10px;
            font-weight: 600;
            padding: 0.6rem 1.2rem;
        }
        div.stButton > button[kind="primary"]:hover {
            background: rgba(16, 185, 129, 0.32);
            color: #a7f3d0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
