import json
from pathlib import Path
import pandas as pd
import streamlit as st

import model.train_qlora as tq
from app.ui_theme import apply_repofix_theme, render_error_with_fix
from model.inference import generate_with_qlora_adapter

st.set_page_config(page_title="Model Lab", layout="wide")
apply_repofix_theme()

st.markdown(
    """
    <div class="rf-header">
      <div>
        <div style="font-size: 19px; font-weight: 700;">Model Lab</div>
        <div style="font-size: 13px; color: #9ab8a8;">4-bit NF4 QLoRA training config, visual scaling & live inference</div>
      </div>
      <span class="rf-pill">RTX 3050 4GB</span>
    </div>
    """,
    unsafe_allow_html=True,
)

adapter_dir = Path("model/adapters/repofix-qwen25-coder-1.5b-qlora-v0")
if adapter_dir.exists():
    st.success(f"Fine-tuned QLoRA adapter ready at `{adapter_dir}`")
else:
    st.info("Adapter not found yet under `model/adapters/`.")

c1, c2 = st.columns(2)
with c1:
    base_model = st.text_input("Base Model ID", value="Qwen/Qwen2.5-Coder-1.5B-Instruct")
    lora_r = st.selectbox("LoRA Rank (r)", [8, 16, 32, 64], index=1)
    lr = st.number_input("Learning Rate", min_value=1e-6, max_value=1e-2, value=2e-4, format="%.6f")
with c2:
    max_seq_len = st.slider("Max Sequence Length", min_value=256, max_value=4096, value=1024, step=256)
    lora_alpha = st.selectbox("LoRA Alpha", [16, 32, 64, 128], index=1)
    seed = st.number_input("Random Seed", min_value=0, max_value=999999, value=42, step=1)

st.markdown("**QLoRA Parameter Profile Chart**")
st.bar_chart(
    pd.DataFrame(
        {"Value": [int(max_seq_len), int(lora_r), int(lora_alpha)]},
        index=["Max Seq Len", "LoRA Rank (r)", "LoRA Alpha"],
    ),
    height=180,
)

if st.button("Validate & Save QLoRA Config →", type="primary"):
    try:
        payload = {
            "base_model": base_model.strip(),
            "max_seq_length": int(max_seq_len),
            "lora_r": int(lora_r),
            "lora_alpha": int(lora_alpha),
            "learning_rate": float(lr),
            "seed": int(seed),
            "output_dir": str(adapter_dir),
        }
        cfg_cls = getattr(tq, "QLoRAConfig", None)
        if cfg_cls is not None:
            try:
                cfg_obj = cfg_cls(**payload)
                payload = getattr(cfg_obj, "model_dump", lambda: getattr(cfg_obj, "__dict__", payload))()
            except Exception:
                pass
        out_path = Path("configs/qlora_v0.json")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        st.success(f"Saved QLoRA config to `{out_path}`")
        st.json(payload)
    except Exception as exc:
        render_error_with_fix(exc, context_hint=base_model)

st.divider()
st.subheader("Live QLoRA Adapter Test")
prompt_txt = st.text_area(
    "Repair Prompt",
    value=(
        "Task: repair\n"
        "Repository: local/fix_01_discount\n"
        "Target File: shop/pricing.py\n"
        "Issue / Description:\n"
        "apply_discount(200.0, 20.0) should return 160.0."
    ),
    height=120,
)
if st.button("Run QLoRA Inference →"):
    try:
        with st.spinner("Generating patch with QLoRA adapter..."):
            out = generate_with_qlora_adapter(
                user_prompt=prompt_txt,
                base_model=base_model.strip(),
                adapter_dir=str(adapter_dir) if adapter_dir.exists() else None,
                max_new_tokens=180,
            )
        st.code(out, language="diff")
    except Exception as exc:
        render_error_with_fix(exc, context_hint=base_model)
