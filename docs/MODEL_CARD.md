---
language:
- en
- python
license: apache-2.0
base_model: Qwen/Qwen2.5-Coder-1.5B-Instruct
tags:
- code
- bug-repair
- qlora
- peft
- swe-bench
datasets:
- SWE-bench/SWE-bench_Lite
---

# RepoFix AI — QLoRA Adapter (`repofix-qwen25-coder-1.5b-qlora-v0`)

## Model Overview
`repofix-qwen25-coder-1.5b-qlora-v0` is a 4-bit NF4 QLoRA adapter fine-tuned on top of `Qwen/Qwen2.5-Coder-1.5B-Instruct` for repository-aware bug diagnosis and unified diff patch synthesis inside **RepoFix AI**.

## Training Configuration
- **Base Model:** `Qwen/Qwen2.5-Coder-1.5B-Instruct`
- **Quantization:** 4-bit NF4 (`bnb_4bit_use_double_quant=True`)
- **LoRA Hyperparameters:** `r=16`, `lora_alpha=32`, `lora_dropout=0.05`, targets: `q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj`
- **Max Sequence Length:** `1024`
- **Optimizer:** `paged_adamw_8bit`, `learning_rate=2e-4`, `seed=42`
- **Hardware:** NVIDIA GeForce RTX 3050 4GB Laptop GPU

## Dataset & Split Hygiene
- **Source:** `SWE-bench/SWE-bench_Lite` (`dev` split partitioned deterministically by repository SHA-256 hash into disjoint `train` and `val` splits; the benchmark `test` split is strictly excluded from training).

## Safety & Usage Limitations
- Generated patches must always be validated (`agent/patch_validator.py`) and executed inside an isolated worktree or sandbox (`sandbox/docker_runner.py`) before applying to any working repository.
