---
language:
  - en
library_name: peft
base_model: Qwen/Qwen2.5-Coder-1.5B-Instruct
tags:
  - qlora
  - quantized
  - code-repair
  - repofix-ai
---

# RepoFix AI — QLoRA Adapter (`repofix-qwen25-coder-1.5b-qlora-v0`)

## Model Overview
`repofix-qwen25-coder-1.5b-qlora-v0` is a 4-bit NF4 QLoRA adapter fine-tuned on top of `Qwen/Qwen2.5-Coder-1.5B-Instruct` for repository-aware bug diagnosis and unified diff patch synthesis inside **RepoFix AI**.

## Training Configuration

- **Base Model:** `Qwen/Qwen2.5-Coder-1.5B-Instruct` (1.54B total parameters)
- **Fine-Tuning Method:** 4-bit NF4 QLoRA
- **Hardware:** NVIDIA RTX 3050 (4GB VRAM)
- **LoRA Settings:** `r = 16`, `lora_alpha = 32`, `learning_rate = 2e-4`, `seed = 42`
- **Training Loss:** `1.8565`

### Benchmarks: Base Normal Mode vs. RepoFix-AI Model

![Benchmark Comparison — Accuracy, Speed & Token Generation](assets/benchmark_comparison.png)

| Metric | Base Model (Normal Mode) | RepoFix-AI Model (Fine-Tuned & Quantized) |
| :--- | :---: | :---: |
| **Accuracy** | 100.0% | **100.0%** |
| **Speed** | 1.62 tok/s (21025.9 ms) | **3.07 tok/s** (22178.3 ms) |
| **Token Generation** | 34 tokens | **68 tokens** |
