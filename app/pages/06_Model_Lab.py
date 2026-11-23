import json
from pathlib import Path
import streamlit as st

from model.inference import generate_with_qlora_adapter
from model.train_qlora import QLoRAConfig, export_qlora_config, validate_training_recipe

st.title("Model Lab")
st.caption("Configure, validate, and test 4-bit QLoRA fine-tuning recipes on your GPU.")

adapter_path = Path("model/adapters/repofix-qwen25-coder-1.5b-qlora-v0")
if adapter_path.exists():
    st.success(f"Local QLoRA adapter ready at `{adapter_path}`")
else:
    st.info("No local QLoRA adapter found yet under `model/adapters/`.")

base_model = st.text_input("Base Model ID", value="Qwen/Qwen2.5-Coder-1.5B-Instruct")
max_seq_len = st.number_input("Max Sequence Length", min_value=256, max_value=8192, value=1024, step=256)
lora_r = st.selectbox("LoRA Rank (r)", [8, 16, 32, 64], index=1)
lora_alpha = st.selectbox("LoRA Alpha", [16, 32, 64, 128], index=1)
lr = st.number_input("Learning Rate", min_value=1e-6, max_value=1e-2, value=2e-4, format="%.6f")
seed = st.number_input("Random Seed", min_value=0, max_value=999999, value=42, step=1)

if st.button("Validate & Save QLoRA Config", type="primary"):
    cfg = QLoRAConfig(
        base_model=base_model.strip(),
        max_seq_length=int(max_seq_len),
        lora_r=int(lora_r),
        lora_alpha=int(lora_alpha),
        learning_rate=float(lr),
        seed=int(seed),
        output_dir=str(adapter_path),
    )
    res = validate_training_recipe(cfg)
    if res["valid"]:
        out_file = export_qlora_config(cfg, Path("configs/qlora_v0.json"))
        st.success(f"Valid QLoRA recipe exported to `{out_file}`")
        st.json(res)
    else:
        st.error(f"Validation failed: {res['errors']}")

st.divider()
st.subheader("Quick Adapter Patch Smoke Test")
sample_prompt = st.text_area(
    "Test Prompt",
    value=(
        "Task: repair\n"
        "Repository: local/fix_01_discount\n"
        "Target File: shop/pricing.py\n"
        "Issue / Description:\n"
        "apply_discount(200.0, 20.0) should apply a 20% discount and return 160.0."
    ),
    height=130,
)
if st.button("Run Adapter Inference"):
    with st.spinner("Generating with QLoRA adapter..."):
        out = generate_with_qlora_adapter(
            user_prompt=sample_prompt,
            base_model=base_model.strip(),
            adapter_dir=str(adapter_path) if adapter_path.exists() else None,
            max_new_tokens=180,
        )
    st.code(out, language="diff")
