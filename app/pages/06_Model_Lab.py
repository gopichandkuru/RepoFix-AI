import json
from pathlib import Path
import streamlit as st

from model.train_qlora import QLoRAConfig, validate_training_recipe, write_run_config

st.title("Model Lab")
st.caption("Configure, validate, and export reproducible QLoRA fine-tuning recipes.")

base_model = st.text_input("Base Model ID", value="Qwen/Qwen2.5-Coder-7B-Instruct")
max_seq_len = st.number_input("Max Sequence Length", min_value=512, max_value=32768, value=4096, step=512)
lora_r = st.selectbox("LoRA Rank (r)", options=[8, 16, 32, 64], index=1)
lora_alpha = st.selectbox("LoRA Alpha", options=[16, 32, 64, 128], index=1)
lr = st.number_input("Learning Rate", min_value=1e-6, max_value=1e-2, value=2e-4, format="%.6f")
seed = st.number_input("Random Seed", min_value=0, max_value=999999, value=42)

cfg = QLoRAConfig(
    base_model=base_model,
    max_seq_length=int(max_seq_len),
    lora_r=int(lora_r),
    lora_alpha=int(lora_alpha),
    learning_rate=float(lr),
    seed=int(seed),
)

if st.button("Validate & Save QLoRA Config"):
    check = validate_training_recipe(cfg)
    st.write(f"- **Recipe Valid:** `{check['valid']}`")
    st.write(f"- **Dataset Manifest Found:** `{check['manifest_exists']}`")
    for err in check["errors"]:
        st.error(err)
    saved = write_run_config(cfg, Path("configs/qlora_v0.json"))
    st.success(f"Saved training recipe to `{saved}`")
    st.json(json.loads(saved.read_text(encoding="utf-8")))
